import os
import subprocess
from pathlib import Path

from .base_extractor import BaseExtractor, ExtractedData
from ..models import IngestionOptions
from ..parsers import SectionParser, TableParser
from ..utils import TextUtils


class DocExtractor(BaseExtractor):
    def extract(self, path: Path, options: IngestionOptions) -> ExtractedData:
        del options
        
        if os.name == "nt":
            try:
                import win32com.client  # type: ignore

                word = win32com.client.Dispatch("Word.Application")
                word.Visible = False
                doc = None
                try:
                    doc = word.Documents.Open(str(path.resolve()))

                    paragraphs = []
                    for para in doc.Paragraphs:
                        text = str(para.Range.Text or "")
                        text = text.replace("\r", "").replace("\x07", "")
                        text = TextUtils.normalize_whitespace(text)
                        if text:
                            paragraphs.append(text)

                    raw_tables = []
                    for table_idx in range(1, int(doc.Tables.Count) + 1):
                        table = doc.Tables(table_idx)
                        table_rows = []
                        for row_idx in range(1, int(table.Rows.Count) + 1):
                            word_row = table.Rows(row_idx)
                            cells = []
                            for cell_idx in range(1, int(word_row.Cells.Count) + 1):
                                cell = word_row.Cells(cell_idx)
                                cell_text = str(cell.Range.Text or "")
                                cell_text = cell_text.replace("\r\x07", "").replace("\r", "").replace("\x07", "")
                                cells.append(TextUtils.normalize_whitespace(cell_text))
                            table_rows.append(cells)
                        raw_tables.append(table_rows)

                    tables = TableParser.normalize_document_tables(raw_tables)
                    full_text = TextUtils.normalize_whitespace("\n".join(paragraphs))

                    return (
                        "text",
                        full_text,
                        SectionParser.extract_sections_from_markdown_or_text(full_text) or None,
                        tables or None,
                        {
                            "extractor": "win32com",
                            "table_count": len(tables),
                            "table_row_count": sum(len(table["entries"]) for table in tables),
                        },
                    )
                finally:
                    if doc is not None:
                        doc.Close(False)
                    word.Quit()
            except Exception:
                pass

        try:
            result = subprocess.run(
                ['antiword', str(path)], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            text = TextUtils.normalize_whitespace(result.stdout)
            
            return (
                "text",
                text,
                SectionParser.extract_sections_from_markdown_or_text(text) or None,
                None,
                {
                    "extractor": "antiword_subprocess",
                    "table_extraction": "not_supported",
                },
            )
        except Exception as exc:
            raise RuntimeError(
                "Could not extract .doc file. Ensure 'antiword' is installed on Linux/Docker, or 'pywin32' on Windows."
            ) from exc