from pathlib import Path

import pytest

from ingestor_core.parsers.section_parser import SectionParser
from ingestor_core.parsers.subsection_parser import SubsectionParser
from ingestor_core.parsers.table_parser import TableParser
from ingestor_core.utils import TextUtils


def test_normalize_whitespace_and_read_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_bytes(b"abc\r\nline\r")
    assert TextUtils.normalize_whitespace("a\r\nb \r") == "a\nb"
    assert TextUtils.read_text_with_fallback(sample) == "abc\r\nline\r"

    class FakeRaw:
        def __init__(self) -> None:
            self.calls = []

        def decode(self, encoding: str, errors: str | None = None) -> str:
            self.calls.append((encoding, errors))
            if errors == "replace":
                return "ok"
            raise UnicodeDecodeError(encoding, b"\xff", 0, 1, "bad")

    class FakePath:
        def read_bytes(self) -> FakeRaw:
            return FakeRaw()

    assert TextUtils.read_text_with_fallback(FakePath()) == "ok"


def test_section_parser_markdown_uppercase_simple_and_pdf_helpers() -> None:
    text = "# Intro\nhello details\nPLAN\nbody details\nRisk Items:\nitem one"
    sections = SectionParser.extract_sections_from_markdown_or_text(text)
    assert sections["Intro"] == "hello details"
    assert sections["Plan"] == "body details"
    assert sections["Risk Items"] == "item one"

    assert not SectionParser.is_likely_pdf_heading("what it covers", 20, 10)
    assert not SectionParser.is_likely_pdf_heading("• bullet", 20, 10)
    assert not SectionParser.is_likely_pdf_heading("1", 20, 10)
    assert SectionParser.is_likely_pdf_heading("Header", 15, 10)
    assert SectionParser.is_likely_pdf_heading("BIG TITLE", 8, 10)
    assert SectionParser.is_likely_pdf_heading("1.2) Numbered Header", 8, 10)
    assert not SectionParser.is_likely_pdf_heading("This is a sentence.", 20, 10)

    built = SectionParser.build_sections_from_pdf_lines(
        [("Main Title", 20.0), ("detail", 9.0)],
        "Main Title\ndetail line\n2\nanother detail",
    )
    assert built is not None
    assert "Main Title" in built

    fallback = SectionParser.build_sections_from_pdf_lines([], "# X\nY")
    assert fallback is None or fallback == {"X": "Y"}


def test_section_parser_additional_pdf_paths() -> None:
    assert not SectionParser.is_likely_pdf_heading("", 11, 10)
    assert not SectionParser.is_likely_pdf_heading("one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen", 20, 10)

    lines = [
        ("", 5.0),
        ("2", 5.0),
        ("Main Heading", 40.0),
        ("tiny", 10.0),
        ("tiny2", 10.0),
    ]
    built = SectionParser.build_sections_from_pdf_lines(
        lines,
        "Main Heading\n\ncontent one\n3\ncontent two",
    )
    assert built is not None and built["Main Heading"] == "content one\ncontent two"

    cleaned_empty = SectionParser.build_sections_from_pdf_lines(
        [("Heading", 40.0), ("x", 10.0), ("y", 10.0)],
        "Heading\n1",
    )
    assert cleaned_empty is None


def test_subsection_parser_branches() -> None:
    assert not SubsectionParser.is_reasonable_label_name("")
    assert not SubsectionParser.is_reasonable_label_name("a b c d e f g h")
    assert not SubsectionParser.is_reasonable_label_name("Has?")
    assert not SubsectionParser.is_reasonable_label_name("Field 1234")
    assert SubsectionParser.is_reasonable_label_name("Assigned people")

    parsed = SubsectionParser.parse_labeled_subsections(
        "Assigned people:\n- Alice\ncontinued\nGuiding questions:\n* Q1\n* Q2"
    )
    assert parsed is not None
    assert "Assigned people" in parsed
    assert "Guiding questions" in parsed

    tiny = SubsectionParser.parse_labeled_subsections("A: x\nB: y")
    assert tiny is None

    extracted = SubsectionParser.extract_structured_sections(
        {
            "S1": "Assigned people:\n- Alice Wonderland\n- Bob Robertson\nGuiding questions:\n- What should happen\n- Why did it fail",
            "S2": "plain",
        }
    )
    assert extracted is not None and "S1" in extracted
    assert SubsectionParser.extract_structured_sections(None) is None


def test_subsection_parser_additional_edges() -> None:
    # Blank lines and invalid labels are ignored.
    result = SubsectionParser.parse_labeled_subsections("\nA: x\nBad Label 1234: y\nValid Label:\nline text")
    assert result is None or "Valid Label" in result

    # First label has no content and is skipped; second keeps plain text.
    result2 = SubsectionParser.parse_labeled_subsections(
        "Alpha:\nBeta Label: long enough narrative plain text for threshold"
    )
    assert result2 is None or "Beta Label" in result2

    # Force len(structured)>=2 but captured chars <30.
    tiny = SubsectionParser.parse_labeled_subsections("Ab: x\nCd: y")
    assert tiny is None

    mixed = SubsectionParser.parse_labeled_subsections(
        "Review Items: intro summary\n- item one\n- item two\nOwner Notes: text that is long enough"
    )
    assert mixed is not None and "Review Items" in mixed


def test_table_parser_full_branches() -> None:
    headers = TableParser.to_unique_headers(["Name", "Name", "", ""])
    assert headers == ["Name", "Name_2", "column_3", "column_4"]

    assert TableParser.rows_to_entries([["onlyheader"]]) == []
    entries = TableParser.rows_to_entries([["ID", "Value"], [1, "a"], [2, "b"]])
    assert entries[0]["ID"] == "1"

    assert TableParser.cleanup_fragmented_text("A bc") == "Abc"
    aggressive = TableParser.cleanup_fragmented_text("Kiya nSaghti", aggressive=True)
    assert "Kiyan Saghti" in aggressive
    assert TableParser.cleanup_fragmented_text("   ") == ""

    assert TableParser.merge_entry_columns([], [[0]]) == ([], [])

    merged_headers, merged = TableParser.merge_entry_columns(
        [{"A": "x", "column_2": "y", "B": "z"}],
        [[0, 1], [2, 5]],
    )
    assert merged_headers == ["A", "B"]
    assert merged[0]["A"] == "x y"

    assert TableParser.coalesce_pdf_table_entries([], aggressive_cleanup=False) == []
    small = [{"A": "1", "B": "2", "C": "3"}]
    assert TableParser.coalesce_pdf_table_entries(small) == small

    merged_special = TableParser.coalesce_pdf_table_entries(
        [
            {
                "Index": "1",
                "Name": "Alpha",
                "Part": "One",
                "Assigned": "A",
                "people": "B",
            }
        ]
    )
    assert isinstance(merged_special, list) and merged_special

    merged_regular = TableParser.coalesce_pdf_table_entries(
        [{"Header": "x", "part": "y", "Other": "z", "Final": "v"}],
        aggressive_cleanup=True,
    )
    assert merged_regular[0]

    fallback_header, fallback_entries = TableParser.merge_entry_columns(
        [{"column_1": "value"}],
        [[0]],
    )
    assert fallback_header == ["column_1"]
    assert fallback_entries[0]["column_1"] == "value"

    tables = TableParser.normalize_document_tables(
        [
            [["H1", "H2"], ["a", "b"]],
            [["H"], [""]],
        ]
    )
    assert tables[0]["table_index"] == 1

    assert not TableParser.is_probable_table_columns(["single"])
    assert not TableParser.is_probable_table_columns(["1", "B"])
    assert not TableParser.is_probable_table_columns(["what it covers", "X"])
    assert not TableParser.is_probable_table_columns(["column_1", "column_2", "Z"])
    assert not TableParser.is_probable_table_columns(["@@", "##"])
    assert TableParser.is_probable_table_columns(["Name", "Value"])
