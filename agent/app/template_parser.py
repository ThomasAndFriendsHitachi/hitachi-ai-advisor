from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .models import GenerationIssue, TemplateParseResult, VddFieldSpec
from .utils import slugify, stable_id


class VddTemplateParser:
    PLACEHOLDER_RE = re.compile(r"\{\{([^{}]+)\}\}|<<([^<>]+)>>|\[\[([^\[\]]+)\]\]")

    def __init__(self, template_path: Path) -> None:
        self.template_path = template_path

    def parse(self) -> TemplateParseResult:
        if not self.template_path.exists():
            issue = GenerationIssue(
                issue_id=stable_id("issue", f"template_missing:{self.template_path}"),
                severity="critical",
                category="template",
                message=f"Template file not found: {self.template_path}",
                recommendation="Add the DOCX template at templates/vdd_template.docx.",
            )
            return TemplateParseResult(fields=self._default_fields(), issues=[issue])

        try:
            paragraphs = self._extract_paragraphs(self.template_path)
        except Exception as exc:  # pragma: no cover - defensive parser guard
            issue = GenerationIssue(
                issue_id=stable_id("issue", f"template_parse_error:{self.template_path.name}"),
                severity="high",
                category="template",
                message=f"Failed to parse DOCX template: {exc}",
                recommendation="Check DOCX validity and OpenXML structure.",
            )
            return TemplateParseResult(fields=self._default_fields(), issues=[issue])

        placeholder_specs = self._extract_placeholder_specs(paragraphs)
        if placeholder_specs:
            return TemplateParseResult(fields=placeholder_specs, issues=[])

        inferred_specs = self._infer_fields_from_structure(paragraphs)
        issues = [
            GenerationIssue(
                issue_id=stable_id("issue", "template_no_placeholders"),
                severity="medium",
                category="template",
                message="No explicit placeholders were found in template; inferred fields from section structure.",
                recommendation="Add placeholders like {{FIELD_NAME}} to improve deterministic field mapping.",
            )
        ]
        if not inferred_specs:
            inferred_specs = self._default_fields()
            issues.append(
                GenerationIssue(
                    issue_id=stable_id("issue", "template_fallback_defaults"),
                    severity="medium",
                    category="template",
                    message="Template inference yielded no fields; default field set applied.",
                    recommendation="Update template headings or placeholders to align with required VDD sections.",
                )
            )

        return TemplateParseResult(fields=inferred_specs, issues=issues)

    def _extract_paragraphs(self, path: Path) -> list[str]:
        with zipfile.ZipFile(path, "r") as archive:
            xml_bytes = archive.read("word/document.xml")

        root = ET.fromstring(xml_bytes)
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

        paragraphs: list[str] = []
        for paragraph in root.findall(".//w:p", namespace):
            text_parts: list[str] = []
            for text_node in paragraph.findall(".//w:t", namespace):
                if text_node.text:
                    text_parts.append(text_node.text)
            merged = "".join(text_parts).strip()
            if merged:
                paragraphs.append(merged)
        return paragraphs

    def _extract_placeholder_specs(self, paragraphs: list[str]) -> list[VddFieldSpec]:
        ordered: list[VddFieldSpec] = []
        seen: set[str] = set()

        for line in paragraphs:
            for match in self.PLACEHOLDER_RE.finditer(line):
                raw = next(group for group in match.groups() if group)
                label = raw.strip().replace("_", " ").replace("-", " ")
                field_id = slugify(raw)
                if field_id in seen:
                    continue
                seen.add(field_id)
                ordered.append(
                    VddFieldSpec(
                        field_id=field_id,
                        label=label.title(),
                        required=True,
                        value_type="text",
                        hint=f"Inferred from template placeholder: {match.group(0)}",
                        confidence=0.98,
                    )
                )

        return ordered

    def _infer_fields_from_structure(self, paragraphs: list[str]) -> list[VddFieldSpec]:
        candidates: list[str] = []
        for line in paragraphs:
            clean = line.strip(" :-\t")
            if len(clean) < 4 or len(clean) > 90:
                continue

            is_numbered = bool(re.match(r"^\d+[\.)]\s+", clean))
            is_heading_like = clean.isupper() or clean.endswith(":")
            has_keywords = bool(
                re.search(
                    r"requirement|validation|verification|risk|scope|summary|approval|trace|stakeholder|issue",
                    clean,
                    flags=re.IGNORECASE,
                )
            )
            if is_numbered or is_heading_like or has_keywords:
                candidates.append(clean)

        # Keep insertion order and remove duplicates.
        unique_candidates: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            key = slugify(candidate)
            if key in seen:
                continue
            seen.add(key)
            unique_candidates.append(candidate)

        specs: list[VddFieldSpec] = []
        for candidate in unique_candidates[:30]:
            field_id = slugify(candidate)
            required = bool(
                re.search(
                    r"requirement|verification|validation|approval|risk|trace",
                    candidate,
                    flags=re.IGNORECASE,
                )
            )
            specs.append(
                VddFieldSpec(
                    field_id=field_id,
                    label=candidate,
                    required=required,
                    value_type="text",
                    hint="Inferred from template heading",
                    confidence=0.7,
                )
            )
        return specs

    def _default_fields(self) -> list[VddFieldSpec]:
        defaults = [
            ("release_summary", "Release Summary", True),
            ("scope_of_change", "Scope Of Change", True),
            ("requirements_coverage", "Requirements Coverage", True),
            ("verification_validation", "Verification And Validation", True),
            ("traceability_overview", "Traceability Overview", True),
            ("risk_radar_summary", "Risk Radar Summary", True),
            ("stakeholder_insights", "Stakeholder Insights", False),
            ("open_issues", "Open Issues", True),
            ("approval_recommendation", "Approval Recommendation", True),
        ]
        return [
            VddFieldSpec(field_id=field_id, label=label, required=required, value_type="text", confidence=0.5)
            for field_id, label, required in defaults
        ]
