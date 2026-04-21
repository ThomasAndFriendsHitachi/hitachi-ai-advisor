from pathlib import Path

from .base_extractor import BaseExtractor, ExtractedData
from ..models import IngestionOptions
from ..parsers import SectionParser
from ..utils import TextUtils


class TextExtractor(BaseExtractor):
    def extract(self, path: Path, options: IngestionOptions) -> ExtractedData:
        del options
        text = TextUtils.normalize_whitespace(TextUtils.read_text_with_fallback(path))
        sections = SectionParser.extract_sections_from_markdown_or_text(text)
        metadata = {
            "line_count": len(text.split("\n")) if text else 0,
            "char_count": len(text),
        }
        return "text", text, sections or None, None, metadata
