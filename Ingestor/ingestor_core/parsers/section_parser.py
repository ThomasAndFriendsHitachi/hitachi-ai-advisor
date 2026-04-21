import re
from typing import Dict, List, Optional, Set, Tuple

from ..utils import TextUtils


class SectionParser:
    @staticmethod
    def extract_sections_from_markdown_or_text(text: str) -> Dict[str, str]:
        sections: Dict[str, List[str]] = {}
        current = "__body__"
        sections[current] = []

        md_heading = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$")
        simple_heading = re.compile(r"^\s*([A-Z][A-Za-z0-9 _\-/]{1,100})\s*:?\s*$")

        for line in text.split("\n"):
            md_match = md_heading.match(line)
            if md_match:
                current = md_match.group(2).strip()
                sections.setdefault(current, [])
                continue

            if line.strip() and line.strip() == line.strip().upper() and len(line.strip()) <= 80:
                current = line.strip().title()
                sections.setdefault(current, [])
                continue

            if simple_heading.match(line) and len(line.strip().split()) <= 8:
                current = line.strip().rstrip(":")
                sections.setdefault(current, [])
                continue

            sections.setdefault(current, []).append(line)

        cleaned: Dict[str, str] = {}
        for heading, lines in sections.items():
            block = TextUtils.normalize_whitespace("\n".join(lines))
            if block:
                cleaned[heading] = block
        return cleaned

    @staticmethod
    def is_likely_pdf_heading(line_text: str, line_font_size: float, median_font_size: float) -> bool:
        text = TextUtils.normalize_whitespace(line_text)
        if not text:
            return False

        lower = text.lower().rstrip(":")
        if lower in {
            "what it covers",
            "assigned people",
            "guiding questions",
            "expected result",
            "actual result",
        }:
            return False

        if text.startswith("•"):
            return False

        if re.fullmatch(r"\d{1,3}", text):
            return False

        word_count = len(text.split())
        if word_count > 14 or len(text) > 120:
            return False

        if line_font_size >= (median_font_size * 1.2) and not text.endswith("."):
            return True

        if text.isupper() and word_count <= 10:
            return True

        if re.match(r"^\d+(\.\d+)*[\.)]\s+.+", text):
            return True

        return False

    @staticmethod
    def build_sections_from_pdf_lines(lines: List[Tuple[str, float]], fallback_text: str) -> Optional[Dict[str, str]]:
        if not lines:
            sections = SectionParser.extract_sections_from_markdown_or_text(fallback_text)
            return sections or None

        font_sizes = [size for _, size in lines if size > 0]
        median_font = sorted(font_sizes)[len(font_sizes) // 2] if font_sizes else 10.0

        heading_candidates: List[str] = []
        seen_headings: Set[str] = set()
        for line_text, line_font_size in lines:
            text = TextUtils.normalize_whitespace(line_text)
            if not text:
                continue

            if re.fullmatch(r"\d{1,3}", text):
                continue

            if SectionParser.is_likely_pdf_heading(text, line_font_size, median_font) and text not in seen_headings:
                seen_headings.add(text)
                heading_candidates.append(text)

        if not heading_candidates:
            sections = SectionParser.extract_sections_from_markdown_or_text(fallback_text)
            return sections or None

        heading_set = set(heading_candidates)
        section_lines: Dict[str, List[str]] = {"__body__": []}
        current_section = "__body__"

        for raw_line in fallback_text.split("\n"):
            text = TextUtils.normalize_whitespace(raw_line)
            if not text:
                continue

            if re.fullmatch(r"\d{1,3}", text):
                continue

            if text in heading_set:
                current_section = text
                section_lines.setdefault(current_section, [])
                continue

            section_lines.setdefault(current_section, []).append(text)

        cleaned: Dict[str, str] = {}
        for section, content_lines in section_lines.items():
            body = TextUtils.normalize_whitespace("\n".join(content_lines))
            if body:
                cleaned[section] = body

        if not cleaned:
            sections = SectionParser.extract_sections_from_markdown_or_text(fallback_text)
            return sections or None

        return cleaned
