import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .base_extractor import BaseExtractor, ExtractedData
from ..models import IngestionOptions
from ..parsers import SectionParser, TableParser
from ..utils import TextUtils


class PdfExtractor(BaseExtractor):
    def extract(self, path: Path, options: IngestionOptions) -> ExtractedData:
        aggressive_cleanup = options.aggressive_pdf_cleanup

        try:
            import pdfplumber  # type: ignore
        except ImportError:
            pdfplumber = None

        if pdfplumber is not None:
            with pdfplumber.open(str(path)) as pdf:
                pages_text: List[str] = []
                line_candidates: List[Tuple[str, float]] = []
                tables: List[Dict[str, Any]] = []
                table_index = 0
                seen_table_signatures = set()

                def add_page_tables(raw_tables: List[List[List[Any]]], page_idx: int) -> None:
                    nonlocal table_index
                    for raw_table in raw_tables:
                        entries = TableParser.rows_to_entries(raw_table)
                        if not entries:
                            continue

                        entries = TableParser.coalesce_pdf_table_entries(
                            entries,
                            aggressive_cleanup=aggressive_cleanup,
                        )
                        if not entries:
                            continue

                        columns = list(entries[0].keys())
                        if not TableParser.is_probable_table_columns(columns):
                            continue

                        signature = json.dumps(entries, ensure_ascii=False, sort_keys=True)
                        if signature in seen_table_signatures:
                            continue
                        seen_table_signatures.add(signature)

                        table_index += 1
                        tables.append(
                            {
                                "table_index": table_index,
                                "page": page_idx,
                                "columns": columns,
                                "entries": entries,
                            }
                        )

                for page_idx, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text() or ""
                    pages_text.append(page_text)

                    words = page.extract_words(extra_attrs=["size"])
                    line_buckets: Dict[float, List[Dict[str, Any]]] = {}
                    for word in words:
                        top = float(word.get("top", 0.0))
                        line_key = round(top, 1)
                        line_buckets.setdefault(line_key, []).append(word)

                    for line_top in sorted(line_buckets.keys()):
                        line_words = line_buckets[line_top]
                        sorted_words = sorted(line_words, key=lambda item: float(item.get("x0", 0.0)))
                        line_text = " ".join(str(item.get("text", "")) for item in sorted_words)
                        font_size = max(float(item.get("size", 0.0)) for item in sorted_words) if sorted_words else 0.0
                        if TextUtils.normalize_whitespace(line_text):
                            line_candidates.append((line_text, font_size))

                    default_tables = page.extract_tables() or []
                    add_page_tables(default_tables, page_idx)

                    text_strategy_settings = {
                        "vertical_strategy": "text",
                        "horizontal_strategy": "text",
                        "snap_tolerance": 3,
                        "join_tolerance": 3,
                        "intersection_tolerance": 3,
                        "text_x_tolerance": 2,
                        "text_y_tolerance": 2,
                    }
                    text_tables = page.extract_tables(table_settings=text_strategy_settings) or []
                    add_page_tables(text_tables, page_idx)

                text = TextUtils.normalize_whitespace("\n\n".join(pages_text))
                sections = SectionParser.build_sections_from_pdf_lines(line_candidates, text)
                metadata = {
                    "extractor": "pdfplumber",
                    "aggressive_pdf_cleanup": aggressive_cleanup,
                    "page_count": len(pdf.pages),
                    "section_count": len(sections or {}),
                    "table_count": len(tables),
                    "table_row_count": sum(len(table["entries"]) for table in tables),
                }
                return "text", text, sections, tables or None, metadata

        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "PDF parsing requires pdfplumber or pypdf. Install with: pip install pdfplumber pypdf"
            ) from exc

        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")

        text = TextUtils.normalize_whitespace("\n\n".join(pages))
        sections = SectionParser.extract_sections_from_markdown_or_text(text) or None
        metadata = {
            "extractor": "pypdf",
            "aggressive_pdf_cleanup": aggressive_cleanup,
            "page_count": len(reader.pages),
            "table_extraction": "not_supported_without_pdfplumber",
        }
        return "text", text, sections, None, metadata
