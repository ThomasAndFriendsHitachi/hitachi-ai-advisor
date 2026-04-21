from pathlib import Path
from typing import Dict, List

from .base_extractor import BaseExtractor, ExtractedData
from ..models import IngestionOptions


class ExcelExtractor(BaseExtractor):
    def __init__(self, max_rows_preview: int = 2000) -> None:
        self.max_rows_preview = max_rows_preview

    def extract(self, path: Path, options: IngestionOptions) -> ExtractedData:
        del options
        try:
            import pandas as pd  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "pandas is required for xls/xlsx files. Install with: pip install pandas openpyxl xlrd"
            ) from exc

        workbook: Dict[str, List[Dict[str, object]]] = {}
        excel = pd.ExcelFile(path)
        for sheet in excel.sheet_names:
            df = pd.read_excel(path, sheet_name=sheet)
            if len(df) > self.max_rows_preview:
                df = df.head(self.max_rows_preview)
            workbook[sheet] = df.where(df.notna(), None).to_dict(orient="records")

        metadata = {
            "sheet_count": len(workbook),
            "sheets": list(workbook.keys()),
            "truncated_rows_per_sheet": self.max_rows_preview,
        }
        return "workbook", workbook, None, None, metadata
