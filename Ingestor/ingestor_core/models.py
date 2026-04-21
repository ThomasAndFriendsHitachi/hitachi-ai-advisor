from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class FileIngestionResult:
    file_path: str
    relative_path: str
    extension: str
    size_bytes: int
    status: str
    content_type: str
    content: Any
    sections: Optional[Dict[str, str]]
    tables: Optional[List[Dict[str, Any]]]
    metadata: Dict[str, Any]
    error: Optional[str] = None
    structured_sections: Optional[Dict[str, Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "file_path": self.file_path,
            "relative_path": self.relative_path,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "status": self.status,
            "content_type": self.content_type,
            "content": self.content,
            "metadata": self.metadata,
        }
        if self.sections:
            result["sections"] = self.sections
        if self.structured_sections:
            result["structured_sections"] = self.structured_sections
        if self.tables:
            result["tables"] = self.tables
        if self.error:
            result["error"] = self.error
        return result


@dataclass
class IngestionOptions:
    aggressive_pdf_cleanup: bool = False
