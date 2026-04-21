import re
from typing import Any, Dict, List, Tuple

from ..utils import TextUtils


class TableParser:
    @staticmethod
    def to_unique_headers(header_row: List[str]) -> List[str]:
        used: Dict[str, int] = {}
        headers: List[str] = []

        for idx, raw_header in enumerate(header_row, start=1):
            base = TextUtils.normalize_whitespace(raw_header)
            if not base:
                base = f"column_{idx}"

            candidate = base
            count = used.get(base, 0)
            if count > 0:
                candidate = f"{base}_{count + 1}"
            used[base] = count + 1
            headers.append(candidate)

        return headers

    @staticmethod
    def rows_to_entries(rows: List[List[Any]]) -> List[Dict[str, str]]:
        cleaned_rows: List[List[str]] = []
        for row in rows:
            cleaned_row = [TextUtils.normalize_whitespace("" if cell is None else str(cell)) for cell in row]
            if any(cleaned_row):
                cleaned_rows.append(cleaned_row)

        if len(cleaned_rows) < 2:
            return []

        max_cols = max(len(row) for row in cleaned_rows)
        header_source = cleaned_rows[0] + [""] * (max_cols - len(cleaned_rows[0]))
        headers = TableParser.to_unique_headers(header_source)

        entries: List[Dict[str, str]] = []
        for row in cleaned_rows[1:]:
            padded = row + [""] * (max_cols - len(row))
            entries.append({headers[i]: padded[i] for i in range(max_cols)})

        return entries

    @staticmethod
    def cleanup_fragmented_text(text: str, aggressive: bool = False) -> str:
        cleaned = TextUtils.normalize_whitespace(text)
        if not cleaned:
            return cleaned

        cleaned = re.sub(r"\b([A-Za-z])\s+([A-Za-z]{2,})\b", r"\1\2", cleaned)
        cleaned = re.sub(r"\b([A-Za-z]{2,})\s+([a-z])\b(?!\s+[A-Za-z])", r"\1\2", cleaned)

        if aggressive:
            cleaned = re.sub(
                r"\b([A-Za-z]{2,})\s+([A-Za-z])([A-Z][a-z]+)\b",
                r"\1\2 \3",
                cleaned,
            )
            cleaned = re.sub(
                r"\b([a-z])([A-Z][a-z]{2,})\b",
                r"\1 \2",
                cleaned,
            )
            cleaned = re.sub(
                r"\b([A-Z]{1,4}/[A-Z])\s+([A-Z])([a-z]{4,})\b",
                r"\1 \2 \3",
                cleaned,
            )

        return cleaned

    @staticmethod
    def merge_entry_columns(
        entries: List[Dict[str, str]],
        groups: List[List[int]],
        aggressive_cleanup: bool = False,
    ) -> Tuple[List[str], List[Dict[str, str]]]:
        if not entries:
            return [], []

        original_columns = list(entries[0].keys())
        merged_headers: List[str] = []
        for group in groups:
            header_parts: List[str] = []
            for idx in group:
                if idx >= len(original_columns):
                    continue
                part = TextUtils.normalize_whitespace(original_columns[idx])
                if not part.lower().startswith("column_"):
                    header_parts.append(part)

            header = TableParser.cleanup_fragmented_text(" ".join(header_parts), aggressive=aggressive_cleanup)
            if not header:
                header = f"column_{len(merged_headers) + 1}"
            merged_headers.append(header)

        merged_headers = TableParser.to_unique_headers(merged_headers)
        merged_entries: List[Dict[str, str]] = []
        for row in entries:
            merged_row: Dict[str, str] = {}
            for header_idx, group in enumerate(groups):
                value_parts: List[str] = []
                for idx in group:
                    if idx >= len(original_columns):
                        continue
                    value = TextUtils.normalize_whitespace(row.get(original_columns[idx], ""))
                    if value:
                        value_parts.append(value)
                merged_row[merged_headers[header_idx]] = TableParser.cleanup_fragmented_text(
                    " ".join(value_parts),
                    aggressive=aggressive_cleanup,
                )
            merged_entries.append(merged_row)

        return merged_headers, merged_entries

    @staticmethod
    def coalesce_pdf_table_entries(
        entries: List[Dict[str, str]],
        aggressive_cleanup: bool = False,
    ) -> List[Dict[str, str]]:
        if not entries:
            return entries

        columns = list(entries[0].keys())
        if len(columns) <= 3:
            return entries

        def is_placeholder(name: str) -> bool:
            return TextUtils.normalize_whitespace(name).lower().startswith("column_")

        groups: List[List[int]] = []
        for idx, column_name in enumerate(columns):
            normalized = TextUtils.normalize_whitespace(column_name)
            starts_lower = bool(normalized) and normalized[0].islower()
            very_short_fragment = len(normalized) <= 2 and bool(normalized)

            if idx > 0 and groups and (is_placeholder(normalized) or starts_lower or very_short_fragment):
                groups[-1].append(idx)
            else:
                groups.append([idx])

        def group_header(group: List[int]) -> str:
            names = [TextUtils.normalize_whitespace(columns[i]) for i in group if i < len(columns)]
            names = [name for name in names if name and not is_placeholder(name)]
            return TextUtils.normalize_whitespace(" ".join(names)).lower()

        def group_values(group: List[int], row: Dict[str, str]) -> str:
            parts: List[str] = []
            for i in group:
                if i < len(columns):
                    value = TextUtils.normalize_whitespace(row.get(columns[i], ""))
                    if value:
                        parts.append(value)
            return TextUtils.normalize_whitespace(" ".join(parts))

        first_group_numeric = True
        for row in entries:
            value = group_values(groups[0], row)
            if value and not re.fullmatch(r"\d+[A-Za-z]?", value):
                first_group_numeric = False
                break

        assignee_group_idx = -1
        for idx, group in enumerate(groups):
            header = group_header(group)
            if any(token in header for token in ("assignee", "assigned", "owner", "people", "person")):
                assignee_group_idx = idx
                break

        if first_group_numeric and assignee_group_idx >= 2:
            merged_groups: List[List[int]] = []
            merged_groups.append(groups[0])

            middle: List[int] = []
            for group in groups[1:assignee_group_idx]:
                middle.extend(group)
            if middle:
                merged_groups.append(middle)

            tail: List[int] = []
            for group in groups[assignee_group_idx:]:
                tail.extend(group)
            if tail:
                merged_groups.append(tail)

            _, merged_entries = TableParser.merge_entry_columns(
                entries,
                merged_groups,
                aggressive_cleanup=aggressive_cleanup,
            )
            return merged_entries

        _, merged_entries = TableParser.merge_entry_columns(
            entries,
            groups,
            aggressive_cleanup=aggressive_cleanup,
        )
        return merged_entries

    @staticmethod
    def normalize_document_tables(raw_tables: List[List[List[str]]]) -> List[Dict[str, Any]]:
        tables: List[Dict[str, Any]] = []

        for idx, raw_table in enumerate(raw_tables, start=1):
            entries = TableParser.rows_to_entries(raw_table)
            if not entries:
                continue

            tables.append(
                {
                    "table_index": idx,
                    "columns": list(entries[0].keys()),
                    "entries": entries,
                }
            )

        return tables

    @staticmethod
    def is_probable_table_columns(columns: List[str]) -> bool:
        if len(columns) < 2:
            return False

        first_col = TextUtils.normalize_whitespace(columns[0]).lower().rstrip(":")
        if re.match(r"^\d+[\.)]?\s*", first_col):
            return False

        blocked_labels = {
            "what it covers",
            "assigned people",
            "guiding questions",
        }
        if first_col in blocked_labels:
            return False

        alpha_cols = sum(1 for col in columns if re.search(r"[A-Za-z]", col))
        if alpha_cols < max(1, len(columns) // 2):
            return False

        placeholder_cols = sum(1 for col in columns if TextUtils.normalize_whitespace(col).lower().startswith("column_"))
        if placeholder_cols > (len(columns) // 2):
            return False

        return True
