import json
from pathlib import Path

from .base_extractor import BaseExtractor, ExtractedData
from ..models import IngestionOptions


class JsonExtractor(BaseExtractor):
    def extract(self, path: Path, options: IngestionOptions) -> ExtractedData:
        del options
        with path.open("r", encoding="utf-8", errors="replace") as f:
            obj = json.load(f)

        metadata = {"top_level_type": type(obj).__name__}
        return "json", obj, None, None, metadata
