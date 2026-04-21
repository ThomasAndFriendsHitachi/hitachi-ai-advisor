import re
from typing import Any, Dict, List, Optional

from ..utils import TextUtils


class SubsectionParser:
    @staticmethod
    def is_reasonable_label_name(label: str) -> bool:
        name = TextUtils.normalize_whitespace(label)
        if not name:
            return False

        if len(name.split()) > 7 or len(name) > 60:
            return False

        if name.endswith(".") or "?" in name:
            return False

        if re.search(r"\d{4,}", name):
            return False

        return True

    @staticmethod
    def parse_labeled_subsections(text: str) -> Optional[Dict[str, Any]]:
        label_pattern = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 /&()'._-]{1,60})\s*:\s*(.*)\s*$")
        collected: Dict[str, List[str]] = {}
        current_label: Optional[str] = None

        for raw_line in text.split("\n"):
            line = TextUtils.normalize_whitespace(raw_line)
            if not line:
                continue

            match = label_pattern.match(line)
            if match and SubsectionParser.is_reasonable_label_name(match.group(1)):
                label = TextUtils.normalize_whitespace(match.group(1))
                current_label = label
                collected.setdefault(label, [])
                inline_value = TextUtils.normalize_whitespace(match.group(2))
                if inline_value:
                    collected[label].append(inline_value)
                continue

            if current_label:
                collected[current_label].append(line)

        structured: Dict[str, Any] = {}
        for label, lines in collected.items():
            if not lines:
                continue

            bullets: List[str] = []
            plain: List[str] = []
            last_was_bullet = False
            for line in lines:
                bullet_match = re.match(r"^[•*\-]\s*(.+)$", line)
                if bullet_match:
                    bullets.append(TextUtils.normalize_whitespace(bullet_match.group(1)))
                    last_was_bullet = True
                else:
                    if bullets and last_was_bullet and not re.match(r"^[A-Za-z][A-Za-z0-9 /&()'._-]{1,60}:$", line):
                        bullets[-1] = TextUtils.normalize_whitespace(bullets[-1] + " " + line)
                    else:
                        plain.append(line)
                    last_was_bullet = False

            if bullets and (len(bullets) >= 2 or not plain):
                if plain:
                    structured[label] = {
                        "text": TextUtils.normalize_whitespace(" ".join(plain)),
                        "items": bullets,
                    }
                else:
                    structured[label] = bullets
            else:
                structured[label] = TextUtils.normalize_whitespace("\n".join(lines))

        if len(structured) < 2:
            return None

        captured_chars = sum(len(str(value)) for value in structured.values())
        if captured_chars < 30:
            return None

        return structured

    @staticmethod
    def extract_structured_sections(sections: Optional[Dict[str, str]]) -> Optional[Dict[str, Dict[str, Any]]]:
        if not sections:
            return None

        structured_by_section: Dict[str, Dict[str, Any]] = {}
        for section_name, section_text in sections.items():
            parsed = SubsectionParser.parse_labeled_subsections(section_text)
            if parsed:
                structured_by_section[section_name] = parsed

        return structured_by_section or None
