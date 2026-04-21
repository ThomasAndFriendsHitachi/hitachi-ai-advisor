import builtins
import json
import os
import types
from pathlib import Path

import pytest

from ingestor_core.extractors.base_extractor import BaseExtractor
from ingestor_core.extractors.csv_extractor import CsvExtractor
from ingestor_core.extractors.doc_extractor import DocExtractor
from ingestor_core.extractors.docx_extractor import DocxExtractor
from ingestor_core.extractors.excel_extractor import ExcelExtractor
from ingestor_core.extractors.json_extractor import JsonExtractor
from ingestor_core.extractors.pdf_extractor import PdfExtractor
from ingestor_core.extractors.text_extractor import TextExtractor
from ingestor_core.models import IngestionOptions


def _force_import_error(monkeypatch: pytest.MonkeyPatch, names: set[str]) -> None:
    original_import = builtins.__import__

    def _patched(name, globals=None, locals=None, fromlist=(), level=0):
        if name in names:
            raise ImportError(name)
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _patched)


def test_base_extractor_not_implemented() -> None:
    class Dummy(BaseExtractor):
        def extract(self, path: Path, options: IngestionOptions):
            return super().extract(path, options)

    with pytest.raises(NotImplementedError):
        Dummy().extract(Path("x"), IngestionOptions())


def test_text_json_csv_extractors(tmp_path: Path) -> None:
    txt = tmp_path / "f.txt"
    txt.write_text("# H\nX\n", encoding="utf-8")
    content_type, text, sections, tables, metadata = TextExtractor().extract(txt, IngestionOptions())
    assert content_type == "text"
    assert text == "# H\nX"
    assert sections is None
    assert tables is None
    assert metadata["line_count"] == 2

    j = tmp_path / "f.json"
    j.write_text(json.dumps({"a": 1}), encoding="utf-8")
    ctype, obj, _, _, m = JsonExtractor().extract(j, IngestionOptions())
    assert ctype == "json" and obj["a"] == 1 and m["top_level_type"] == "dict"

    csv_path = tmp_path / "f.csv"
    csv_path.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    ctype, rows, _, _, meta = CsvExtractor(max_rows_preview=1).extract(csv_path, IngestionOptions())
    assert ctype == "table" and len(rows) == 1 and meta["truncated"] is True


def test_excel_extractor_success_and_import_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeDf:
        def __init__(self, size: int):
            self._size = size

        def __len__(self):
            return self._size

        def head(self, n):
            return FakeDf(n)

        def notna(self):
            return self

        def where(self, _mask, _none):
            return self

        def to_dict(self, orient="records"):
            assert orient == "records"
            return [{"x": 1}]

    fake_pd = types.SimpleNamespace(
        ExcelFile=lambda _path: types.SimpleNamespace(sheet_names=["S1", "S2"]),
        read_excel=lambda _path, sheet_name: FakeDf(5 if sheet_name == "S1" else 1),
    )
    monkeypatch.setitem(__import__("sys").modules, "pandas", fake_pd)
    xls = tmp_path / "f.xlsx"
    xls.write_text("x", encoding="utf-8")
    ctype, workbook, _, _, metadata = ExcelExtractor(max_rows_preview=2).extract(xls, IngestionOptions())
    assert ctype == "workbook"
    assert set(workbook.keys()) == {"S1", "S2"}
    assert metadata["sheet_count"] == 2

    _force_import_error(monkeypatch, {"pandas"})
    with pytest.raises(RuntimeError):
        ExcelExtractor().extract(xls, IngestionOptions())


def test_docx_extractor_success_and_import_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class Para:
        def __init__(self, text, style_name=None):
            self.text = text
            self.style = types.SimpleNamespace(name=style_name) if style_name is not None else None

    class Cell:
        def __init__(self, text):
            self.text = text

    class Row:
        def __init__(self, cells):
            self.cells = [Cell(c) for c in cells]

    class Table:
        def __init__(self, rows):
            self.rows = [Row(r) for r in rows]

    class Doc:
        paragraphs = [
            Para("Heading One", "Heading 1"),
            Para("Paragraph A", "Normal"),
            Para("", "Normal"),
        ]
        tables = [Table([["H1", "H2"], ["v1", "v2"]])]

    fake_docx = types.SimpleNamespace(Document=lambda _path: Doc())
    monkeypatch.setitem(__import__("sys").modules, "docx", fake_docx)

    f = tmp_path / "f.docx"
    f.write_text("x", encoding="utf-8")
    ctype, content, sections, tables, metadata = DocxExtractor().extract(f, IngestionOptions())
    assert ctype == "text"
    assert "Paragraph A" in content
    assert sections and sections["Heading One"] == "Paragraph A"
    assert tables and tables[0]["table_index"] == 1
    assert metadata["table_count"] == 1

    _force_import_error(monkeypatch, {"docx"})
    with pytest.raises(RuntimeError):
        DocxExtractor().extract(f, IngestionOptions())


def test_doc_extractor_win32com_and_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    doc_file = tmp_path / "f.doc"
    doc_file.write_text("x", encoding="utf-8")

    class CellObj:
        def __init__(self, text):
            self.Range = types.SimpleNamespace(Text=text)

    class CellsCollection:
        def __init__(self, vals):
            self._vals = vals
            self.Count = len(vals)

        def __call__(self, idx):
            return CellObj(self._vals[idx - 1])

    class RowObj:
        def __init__(self, vals):
            self.Cells = CellsCollection(vals)

    class RowsCollection:
        def __init__(self, rows):
            self._rows = rows
            self.Count = len(rows)

        def __call__(self, idx):
            return RowObj(self._rows[idx - 1])

    class TableObj:
        def __init__(self, rows):
            self.Rows = RowsCollection(rows)

    class TablesCollection:
        def __init__(self, tables):
            self._tables = tables
            self.Count = len(tables)

        def __call__(self, idx):
            return TableObj(self._tables[idx - 1])

    class DocObj:
        def __init__(self):
            self.Paragraphs = [types.SimpleNamespace(Range=types.SimpleNamespace(Text="Title\r"))]
            self.Tables = TablesCollection([[['H1\r\x07', 'H2\r\x07'], ['a\r\x07', 'b\r\x07']]])
            self.closed = False

        def Close(self, _save):
            self.closed = True

    class WordObj:
        def __init__(self):
            self.Visible = True
            self._doc = DocObj()
            self.Documents = types.SimpleNamespace(Open=lambda _p: self._doc)
            self.quit_called = False

        def Quit(self):
            self.quit_called = True

    word = WordObj()
    client_mod = types.SimpleNamespace(Dispatch=lambda _name: word)
    win32_pkg = types.SimpleNamespace(client=client_mod)
    monkeypatch.setitem(__import__("sys").modules, "win32com", win32_pkg)
    monkeypatch.setitem(__import__("sys").modules, "win32com.client", client_mod)
    monkeypatch.setattr(os, "name", "nt", raising=False)

    ctype, text, sections, tables, metadata = DocExtractor().extract(doc_file, IngestionOptions())
    assert ctype == "text"
    assert text == "Title"
    assert sections is None
    assert tables and metadata["extractor"] == "win32com"
    assert word._doc.closed is True and word.quit_called is True

    def boom(_name):
        raise RuntimeError("boom")

    client_mod2 = types.SimpleNamespace(Dispatch=boom)
    monkeypatch.setitem(__import__("sys").modules, "win32com.client", client_mod2)
    win32_pkg.client = client_mod2
    monkeypatch.setitem(__import__("sys").modules, "textract", types.SimpleNamespace(process=lambda _p: b"A: aa\nB: bb"))
    ctype2, text2, sections2, tables2, metadata2 = DocExtractor().extract(doc_file, IngestionOptions())
    assert ctype2 == "text"
    assert tables2 is None
    assert sections2 is None or "__body__" in sections2
    assert metadata2["extractor"] == "textract"
    assert "A: aa" in text2

    _force_import_error(monkeypatch, {"textract"})
    with pytest.raises(RuntimeError):
        DocExtractor().extract(doc_file, IngestionOptions())


def test_pdf_extractor_pdfplumber_and_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pdf_file = tmp_path / "f.pdf"
    pdf_file.write_text("x", encoding="utf-8")

    class FakePage:
        def extract_text(self):
            return "Main Heading\nBody line"

        def extract_words(self, extra_attrs=None):
            assert extra_attrs == ["size"]
            return [
                {"top": 1.0, "x0": 1.0, "text": "Main", "size": 20.0},
                {"top": 1.0, "x0": 2.0, "text": "Heading", "size": 20.0},
                {"top": 2.0, "x0": 1.0, "text": "Body", "size": 9.0},
            ]

        def extract_tables(self, table_settings=None):
            if table_settings is None:
                return [[['Name', 'Value'], ['A', '1']]]
            return [[['Name', 'Value'], ['A', '1']]]

    class FakePdf:
        def __init__(self):
            self.pages = [FakePage()]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    fake_pdfplumber = types.SimpleNamespace(open=lambda _p: FakePdf())
    monkeypatch.setitem(__import__("sys").modules, "pdfplumber", fake_pdfplumber)

    ctype, text, sections, tables, metadata = PdfExtractor().extract(
        pdf_file,
        IngestionOptions(aggressive_pdf_cleanup=True),
    )
    assert ctype == "text"
    assert "Body line" in text
    assert sections is None or "Main Heading" in sections
    assert tables and len(tables) == 1
    assert metadata["extractor"] == "pdfplumber"

    _force_import_error(monkeypatch, {"pdfplumber"})

    class FakePdfReader:
        def __init__(self, _path):
            self.pages = [types.SimpleNamespace(extract_text=lambda: "# A\nB")]

    monkeypatch.setitem(__import__("sys").modules, "pypdf", types.SimpleNamespace(PdfReader=FakePdfReader))
    ctype2, text2, sections2, tables2, metadata2 = PdfExtractor().extract(pdf_file, IngestionOptions())
    assert ctype2 == "text"
    assert sections2 is None or sections2 == {"A": "B"}
    assert tables2 is None
    assert metadata2["extractor"] == "pypdf"

    _force_import_error(monkeypatch, {"pdfplumber", "pypdf"})
    with pytest.raises(RuntimeError):
        PdfExtractor().extract(pdf_file, IngestionOptions())


def test_pdf_extractor_table_filter_continues(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pdf_file = tmp_path / "edge.pdf"
    pdf_file.write_text("x", encoding="utf-8")

    class FakePage:
        def extract_text(self):
            return "T"

        def extract_words(self, extra_attrs=None):
            return []

        def extract_tables(self, table_settings=None):
            return [[['h', 'v'], ['1', '2']]]

    class FakePdf:
        def __init__(self):
            self.pages = [FakePage()]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setitem(__import__("sys").modules, "pdfplumber", types.SimpleNamespace(open=lambda _p: FakePdf()))

    from ingestor_core.extractors import pdf_extractor as mod

    monkeypatch.setattr(mod.TableParser, "rows_to_entries", lambda _raw: [])
    c1 = PdfExtractor().extract(pdf_file, IngestionOptions())
    assert c1[4]["table_count"] == 0

    monkeypatch.setattr(mod.TableParser, "rows_to_entries", lambda _raw: [{"A": "1"}])
    monkeypatch.setattr(mod.TableParser, "coalesce_pdf_table_entries", lambda _e, aggressive_cleanup=False: [])
    c2 = PdfExtractor().extract(pdf_file, IngestionOptions())
    assert c2[4]["table_count"] == 0

    monkeypatch.setattr(mod.TableParser, "coalesce_pdf_table_entries", lambda _e, aggressive_cleanup=False: [{"A": "1"}])
    monkeypatch.setattr(mod.TableParser, "is_probable_table_columns", lambda _c: False)
    c3 = PdfExtractor().extract(pdf_file, IngestionOptions())
    assert c3[4]["table_count"] == 0
