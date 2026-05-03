from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import EvidenceDocument, GenerationIssue
from .utils import normalize_whitespace, sanitize_json_compat, stable_id


class EvidenceIngestionService:
    def __init__(self, input_dir: Path) -> None:
        self.input_dir = input_dir

    def ingest(self) -> tuple[list[EvidenceDocument], list[GenerationIssue]]:
        documents: list[EvidenceDocument] = []
        issues: list[GenerationIssue] = []

        if not self.input_dir.exists():
            issues.append(
                GenerationIssue(
                    issue_id=stable_id("issue", f"missing:{self.input_dir}"),
                    severity="critical",
                    category="input",
                    message=f"Input directory not found: {self.input_dir}",
                    recommendation="Create the input directory and add extracted JSON files.",
                )
            )
            return documents, issues

        for json_path in sorted(self.input_dir.glob("*.json")):
            loaded, load_issues = self._load_source_file(json_path)
            issues.extend(load_issues)
            documents.extend(loaded)

        if not documents:
            issues.append(
                GenerationIssue(
                    issue_id=stable_id("issue", "empty_input"),
                    severity="high",
                    category="input",
                    message="No valid evidence documents were ingested.",
                    recommendation="Verify extraction outputs in inputs/*.json.",
                )
            )
        return documents, issues

    def _load_source_file(self, path: Path) -> tuple[list[EvidenceDocument], list[GenerationIssue]]:
        documents: list[EvidenceDocument] = []
        issues: list[GenerationIssue] = []

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload = sanitize_json_compat(payload)
        except Exception as exc:  # pragma: no cover - defensive parse guard
            issues.append(
                GenerationIssue(
                    issue_id=stable_id("issue", f"parse:{path.name}"),
                    severity="critical",
                    category="corruption",
                    message=f"Failed to parse {path.name}: {exc}",
                    recommendation="Re-run extraction for the corrupted source.",
                )
            )
            return documents, issues

        file_entries = payload.get("files")
        if not isinstance(file_entries, list):
            issues.append(
                GenerationIssue(
                    issue_id=stable_id("issue", f"schema:{path.name}"),
                    severity="high",
                    category="schema",
                    message=f"File {path.name} does not contain a valid 'files' list.",
                    recommendation="Ensure source follows ingestion microservice output schema.",
                )
            )
            return documents, issues

        for index, item in enumerate(file_entries):
            if not isinstance(item, dict):
                issues.append(
                    GenerationIssue(
                        issue_id=stable_id("issue", f"item:{path.name}:{index}"),
                        severity="medium",
                        category="schema",
                        message=f"Skipped malformed file entry at index {index} in {path.name}.",
                        recommendation="Inspect extraction output for malformed objects.",
                    )
                )
                continue

            relative_path = str(item.get("relative_path") or item.get("file_path") or f"{path.stem}:{index}")
            source_file = str(item.get("file_path") or relative_path)
            extension = str(item.get("extension") or "").lower()
            status = str(item.get("status") or "unknown").lower()
            content_type = str(item.get("content_type") or "unknown")
            sections = item.get("sections") if isinstance(item.get("sections"), dict) else {}
            tables = item.get("tables") if isinstance(item.get("tables"), list) else []
            metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}

            text = self._flatten_content(item.get("content"), sections, tables)
            if not text:
                issues.append(
                    GenerationIssue(
                        issue_id=stable_id("issue", f"empty:{path.name}:{relative_path}"),
                        severity="medium",
                        category="missing_information",
                        message=f"No textual content extracted for {relative_path}.",
                        recommendation="Check extractor coverage or source file quality.",
                        document_id=stable_id("doc", f"{path.name}:{relative_path}"),
                    )
                )

            document_id = stable_id("doc", f"{path.name}:{relative_path}")
            documents.append(
                EvidenceDocument(
                    document_id=document_id,
                    source_file=source_file,
                    relative_path=relative_path,
                    extension=extension,
                    content_type=content_type,
                    text=text,
                    sections={str(k): normalize_whitespace(str(v)) for k, v in sections.items()},
                    tables=tables,
                    metadata={**metadata, "container_file": path.name},
                    status=status,
                )
            )

            if status != "success":
                issues.append(
                    GenerationIssue(
                        issue_id=stable_id("issue", f"status:{path.name}:{relative_path}"),
                        severity="high",
                        category="corruption",
                        message=f"Document status is '{status}' for {relative_path}.",
                        recommendation="Validate source integrity before approval workflow.",
                        document_id=document_id,
                    )
                )

        return documents, issues

    def _flatten_content(
        self,
        content: Any,
        sections: dict[str, Any],
        tables: list[dict[str, Any]],
    ) -> str:
        parts: list[str] = []

        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, dict):
            for sheet_name, rows in content.items():
                parts.append(f"Sheet: {sheet_name}")
                if isinstance(rows, list):
                    for row in rows:
                        if isinstance(row, dict):
                            columns = [f"{k}: {row.get(k)}" for k in row.keys()]
                            parts.append(" | ".join(columns))
                        else:
                            parts.append(str(row))

        for section_name, section_text in sections.items():
            if section_name == "__body__":
                parts.append(str(section_text))
            else:
                parts.append(f"Section: {section_name}\n{section_text}")

        for table in tables:
            if not isinstance(table, dict):
                continue
            table_index = table.get("table_index")
            columns = table.get("columns") if isinstance(table.get("columns"), list) else []
            entries = table.get("entries") if isinstance(table.get("entries"), list) else []
            parts.append(f"Table {table_index} Columns: {', '.join(map(str, columns))}")
            for entry in entries:
                if isinstance(entry, dict):
                    row_str = " | ".join(f"{k}: {entry.get(k)}" for k in entry.keys())
                    parts.append(row_str)

        return normalize_whitespace("\n\n".join(parts))
