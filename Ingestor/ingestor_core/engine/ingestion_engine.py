from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import FileIngestionResult, IngestionOptions
from ..parsers import SubsectionParser
from .extractor_registry import ExtractorRegistry


class IngestionEngine:
    def __init__(self, options: Optional[IngestionOptions] = None) -> None:
        self.options = options or IngestionOptions()
        self.registry = ExtractorRegistry()

    @staticmethod
    def gather_files(input_path: Path) -> List[Path]:
        if input_path.is_file():
            return [input_path]
        return [p for p in input_path.rglob("*") if p.is_file()]

    @staticmethod
    def _enrich_with_structured_sections(
        sections: Optional[Dict[str, str]],
        metadata: Dict[str, Any],
    ) -> Optional[Dict[str, Dict[str, Any]]]:
        structured_sections = SubsectionParser.extract_structured_sections(sections)
        if structured_sections:
            metadata["structured_section_count"] = len(structured_sections)
        return structured_sections

    @classmethod
    def _make_result(
        cls,
        *,
        file_path: Path,
        relative_path: str,
        extension: str,
        size_bytes: int,
        status: str,
        content_type: str,
        content: Any,
        sections: Optional[Dict[str, str]],
        tables: Optional[List[Dict[str, Any]]],
        metadata: Dict[str, Any],
        error: Optional[str] = None,
        with_structured_sections: bool = False,
    ) -> FileIngestionResult:
        structured_sections: Optional[Dict[str, Dict[str, Any]]] = None
        if with_structured_sections:
            structured_sections = cls._enrich_with_structured_sections(sections, metadata)

        return FileIngestionResult(
            file_path=str(file_path),
            relative_path=relative_path,
            extension=extension,
            size_bytes=size_bytes,
            status=status,
            content_type=content_type,
            content=content,
            sections=sections,
            tables=tables,
            metadata=metadata,
            error=error,
            structured_sections=structured_sections,
        )

    def ingest_file(self, file_path: Path, root_path: Path) -> FileIngestionResult:
        ext = file_path.suffix.lower()
        relative = str(file_path.relative_to(root_path)) if file_path.is_relative_to(root_path) else file_path.name
        size = file_path.stat().st_size if file_path.exists() else 0

        extractor, unknown_as_text = self.registry.resolve(file_path)

        try:
            content_type, content, sections, tables, metadata = extractor.extract(file_path, self.options)
            if unknown_as_text:
                metadata["fallback"] = "unknown_extension_as_text"

            return self._make_result(
                file_path=file_path,
                relative_path=relative,
                extension=ext,
                size_bytes=size,
                status="success",
                content_type=content_type,
                content=content,
                sections=sections,
                tables=tables,
                metadata=metadata,
                with_structured_sections=(content_type == "text"),
            )

        except Exception as exc:
            return self._make_result(
                file_path=file_path,
                relative_path=relative,
                extension=ext,
                size_bytes=size,
                status="error",
                content_type="unknown",
                content=None,
                sections=None,
                tables=None,
                metadata={},
                error=str(exc),
            )

    def ingest_path(self, input_path: Path) -> Dict[str, Any]:
        files = self.gather_files(input_path)
        root = input_path if input_path.is_dir() else input_path.parent

        results = [self.ingest_file(p, root) for p in files]
        success_count = sum(1 for r in results if r.status == "success")
        error_count = sum(1 for r in results if r.status == "error")

        return {
            "source": str(input_path),
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "summary": {
                "total_files": len(results),
                "success_count": success_count,
                "error_count": error_count,
            },
            "files": [r.to_dict() for r in results],
        }
