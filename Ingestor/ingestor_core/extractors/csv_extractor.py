import csv
from pathlib import Path
from typing import Any, Dict, List

from .base_extractor import BaseExtractor, ExtractedData
from ..models import IngestionOptions


class CsvExtractor(BaseExtractor):
    def __init__(self, max_rows_preview: int = 2000) -> None:
        self.max_rows_preview = max_rows_preview

    def extract(self, path: Path, options: IngestionOptions) -> ExtractedData:
        del options
        with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.DictReader(f)
            rows: List[Dict[str, Any]] = []
            for idx, row in enumerate(reader):
                rows.append(dict(row))
                if idx + 1 >= self.max_rows_preview:
                    break

        metadata = {
            "rows": len(rows),
            "columns": list(rows[0].keys()) if rows else [],
            "truncated": len(rows) >= self.max_rows_preview,
        }
        return "table", rows, None, None, metadata
