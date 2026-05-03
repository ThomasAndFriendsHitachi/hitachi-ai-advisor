from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def utc_today_ymd() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def stable_id(prefix: str, raw: str) -> str:
    digest = hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:10]
    return f"{prefix}_{digest}"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "field"


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def estimate_tokens(text: str) -> int:
    # Rule-of-thumb token estimate for mixed-language text.
    return max(1, int(len(text) / 4))


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def is_nan(value: Any) -> bool:
    return isinstance(value, float) and math.isnan(value)


def sanitize_json_compat(value: Any) -> Any:
    if is_nan(value):
        return None
    if isinstance(value, dict):
        return {str(k): sanitize_json_compat(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_json_compat(v) for v in value]
    return value


def write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(sanitize_json_compat(payload), handle, ensure_ascii=False, indent=2)


def _extract_braced_candidates(text: str) -> list[str]:
    candidates: list[str] = []
    start_index: int | None = None
    depth = 0
    in_string = False
    escaped = False

    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == "{":
            if depth == 0:
                start_index = index
            depth += 1
            continue

        if char == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start_index is not None:
                candidates.append(text[start_index : index + 1])
                start_index = None

    candidates.sort(key=len, reverse=True)
    return candidates


def _remove_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)


def _repair_missing_commas(text: str, max_repairs: int = 6) -> str:
    repaired = text
    for _ in range(max_repairs):
        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError as exc:
            if "Expecting ',' delimiter" not in exc.msg:
                return repaired

            position = exc.pos
            if position <= 0 or position >= len(repaired):
                return repaired

            prev_index = position - 1
            while prev_index >= 0 and repaired[prev_index].isspace():
                prev_index -= 1
            next_index = position
            while next_index < len(repaired) and repaired[next_index].isspace():
                next_index += 1

            if prev_index < 0 or next_index >= len(repaired):
                return repaired

            prev_char = repaired[prev_index]
            next_char = repaired[next_index]

            value_end = prev_char in {'"', "}", "]"} or prev_char.isalnum()
            value_start = next_char in {'"', "{", "[", "-"} or next_char.isalnum()
            if not (value_end and value_start):
                return repaired

            repaired = repaired[:position] + "," + repaired[position:]

    return repaired


def _repair_unterminated_json(text: str) -> str:
    repaired = text.rstrip()
    stack: list[str] = []
    in_string = False
    escaped = False

    for char in repaired:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char in {"{", "["}:
            stack.append(char)
            continue

        if char == "}" and stack and stack[-1] == "{":
            stack.pop()
            continue

        if char == "]" and stack and stack[-1] == "[":
            stack.pop()

    if in_string:
        repaired += '"'

    closers = "".join("}" if token == "{" else "]" for token in reversed(stack))
    repaired += closers
    return _remove_trailing_commas(repaired)


def _candidate_payloads(text: str) -> list[str]:
    raw = text.strip()
    candidates: list[str] = []

    if raw:
        candidates.append(raw)

    fenced = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, flags=re.IGNORECASE)
    for block in fenced:
        block_text = block.strip()
        if block_text:
            candidates.append(block_text)

    for source in list(candidates):
        candidates.extend(_extract_braced_candidates(source))

    # Preserve order while removing duplicates.
    seen: set[str] = set()
    unique: list[str] = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        unique.append(candidate)
    return unique


def extract_json_from_text(text: str) -> Any:
    parse_errors: list[json.JSONDecodeError] = []

    for candidate in _candidate_payloads(text):
        attempts = [
            candidate,
            _remove_trailing_commas(candidate),
            _repair_missing_commas(candidate),
            _repair_missing_commas(_remove_trailing_commas(candidate)),
            _repair_unterminated_json(candidate),
            _repair_missing_commas(_repair_unterminated_json(candidate)),
        ]

        seen_attempts: set[str] = set()
        for attempt in attempts:
            if attempt in seen_attempts:
                continue
            seen_attempts.add(attempt)
            try:
                return json.loads(attempt)
            except json.JSONDecodeError as exc:
                parse_errors.append(exc)

    if parse_errors:
        last_error = parse_errors[-1]
        raise ValueError(str(last_error)) from last_error
    raise ValueError("No JSON object found in model response")


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[tuple[int, int, str]]:
    normalized = normalize_whitespace(text)
    if not normalized:
        return []

    if chunk_size <= 0:
        return [(0, len(normalized), normalized)]

    overlap = max(0, min(overlap, chunk_size // 2))
    step = max(1, chunk_size - overlap)

    chunks: list[tuple[int, int, str]] = []
    start = 0
    length = len(normalized)
    while start < length:
        end = min(length, start + chunk_size)
        piece = normalized[start:end]
        chunks.append((start, end, piece))
        if end >= length:
            break
        start += step
    return chunks


def short_snippet(text: str, max_len: int = 200) -> str:
    clean = normalize_whitespace(text)
    if len(clean) <= max_len:
        return clean
    return clean[: max_len - 3].rstrip() + "..."
