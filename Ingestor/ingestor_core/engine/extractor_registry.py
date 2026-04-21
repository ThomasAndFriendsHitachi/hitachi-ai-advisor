from pathlib import Path

from ..config import TEXT_LIKE_EXTENSIONS
from ..extractors import (
    BaseExtractor,
    CsvExtractor,
    DocExtractor,
    DocxExtractor,
    ExcelExtractor,
    JsonExtractor,
    PdfExtractor,
    TextExtractor,
)


class ExtractorRegistry:
    def __init__(self) -> None:
        self.text_extractor = TextExtractor()
        self._by_extension: dict[str, BaseExtractor] = {
            ".docx": DocxExtractor(),
            ".doc": DocExtractor(),
            ".pdf": PdfExtractor(),
            ".csv": CsvExtractor(),
            ".xls": ExcelExtractor(),
            ".xlsx": ExcelExtractor(),
            ".json": JsonExtractor(),
        }

    def resolve(self, file_path: Path) -> tuple[BaseExtractor, bool]:
        ext = file_path.suffix.lower()
        if ext in self._by_extension:
            return self._by_extension[ext], False

        if ext in TEXT_LIKE_EXTENSIONS or not ext:
            return self.text_extractor, False

        return self.text_extractor, True
