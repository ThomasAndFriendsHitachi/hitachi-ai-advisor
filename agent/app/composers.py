from __future__ import annotations

import re
from collections import Counter

from .models import (
    GenerationIssue,
    RAGDecision,
    RiskItem,
    StakeholderInsight,
    TraceLink,
    VddFieldValue,
)
from .utils import short_snippet, stable_id


class TraceMapComposer:
    def compose(self, fields: list[VddFieldValue]) -> list[TraceLink]:
        links: list[TraceLink] = []
        for field in fields:
            for citation in field.citations:
                links.append(
                    TraceLink(
                        field_id=field.field_id,
                        document_id=citation.document_id,
                        source_file=citation.source_file,
                        chunk_id=citation.chunk_id,
                        score=citation.score,
                        snippet=short_snippet(citation.snippet, max_len=250),
                    )
                )
        return links


class RiskRadarComposer:
    def compose(
        self,
        issues: list[GenerationIssue],
        fields: list[VddFieldValue],
        rag_mode: str,
    ) -> list[RiskItem]:
        risks: list[RiskItem] = []

        for issue in issues:
            risks.append(
                RiskItem(
                    risk_id=stable_id("risk", issue.issue_id),
                    severity=issue.severity,
                    category=issue.category,
                    title=f"{issue.category.title()} Issue",
                    description=issue.message,
                    evidence_refs=[x for x in [issue.document_id, issue.field_id] if x],
                    mitigation=issue.recommendation,
                    status="open",
                )
            )

        for field in fields:
            if field.status == "missing":
                risks.append(
                    RiskItem(
                        risk_id=stable_id("risk", f"missing:{field.field_id}"),
                        severity="high",
                        category="coverage",
                        title=f"Missing required information: {field.label}",
                        description="Required data for this field was not found in evidence.",
                        evidence_refs=[field.field_id],
                        mitigation="Collect additional evidence or mark for manual review.",
                    )
                )
            elif field.status == "needs_review":
                risks.append(
                    RiskItem(
                        risk_id=stable_id("risk", f"review:{field.field_id}"),
                        severity="medium",
                        category="quality",
                        title=f"Field needs review: {field.label}",
                        description=(
                            field.verifier_comment
                            or "Field confidence is low or evidence support is contested."
                        ),
                        evidence_refs=[field.field_id],
                        mitigation="Human reviewer should validate evidence and update the draft.",
                    )
                )

        if rag_mode == "direct":
            risks.append(
                RiskItem(
                    risk_id=stable_id("risk", "direct_mode_context_limit"),
                    severity="low",
                    category="operational",
                    title="Direct-context mode selected",
                    description="No retrieval index used for this run. Consider RAG if evidence volume grows.",
                    mitigation="Switch threshold settings when new documents are ingested.",
                    status="accepted",
                )
            )

        # Deduplicate by title and description.
        deduped: list[RiskItem] = []
        seen: set[tuple[str, str]] = set()
        for risk in risks:
            key = (risk.title, risk.description)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(risk)
        return deduped


class StakeholderInsightComposer:
    KEYWORDS = [
        "stakeholder",
        "assumption",
        "decision",
        "constraint",
        "approval",
        "risk",
        "security",
    ]

    def compose(
        self,
        evidence_texts: list[str],
        fields: list[VddFieldValue],
        risk_items: list[RiskItem],
        verifier_notes: list[str],
    ) -> list[StakeholderInsight]:
        insights: list[StakeholderInsight] = []

        joined = "\n".join(evidence_texts)
        lines = [line.strip() for line in joined.splitlines() if line.strip()]
        for line in lines:
            lowered = line.lower()
            if any(keyword in lowered for keyword in self.KEYWORDS):
                insights.append(
                    StakeholderInsight(
                        insight_id=stable_id("insight", line),
                        title="Evidence-derived stakeholder signal",
                        detail=short_snippet(line, max_len=300),
                        priority="medium",
                        source_refs=[],
                    )
                )
            if len(insights) >= 6:
                break

        unresolved = [field for field in fields if field.status in {"missing", "needs_review"}]
        for field in unresolved[:6]:
            insights.append(
                StakeholderInsight(
                    insight_id=stable_id("insight", f"field:{field.field_id}"),
                    title=f"Unresolved field: {field.label}",
                    detail=(
                        "This field still requires stakeholder confirmation or additional evidence. "
                        + (field.verifier_comment or "")
                    ).strip(),
                    priority="high" if field.status == "missing" else "medium",
                    source_refs=[field.field_id],
                )
            )

        high_risks = [risk for risk in risk_items if risk.severity in {"high", "critical"}]
        if high_risks:
            category_counts = Counter(risk.category for risk in high_risks)
            summary = ", ".join(f"{category}: {count}" for category, count in category_counts.items())
            insights.append(
                StakeholderInsight(
                    insight_id=stable_id("insight", "risk_summary"),
                    title="High-severity risk concentration",
                    detail=f"High-risk categories observed in this run: {summary}.",
                    priority="high",
                    source_refs=[risk.risk_id for risk in high_risks[:6]],
                )
            )

        for note in verifier_notes[:5]:
            if not note.strip():
                continue
            insights.append(
                StakeholderInsight(
                    insight_id=stable_id("insight", f"verifier:{note}"),
                    title="Verifier note",
                    detail=short_snippet(note, max_len=320),
                    priority="medium",
                    source_refs=[],
                )
            )

        # Remove duplicated details.
        deduped: list[StakeholderInsight] = []
        seen_details: set[str] = set()
        for item in insights:
            key = re.sub(r"\s+", " ", item.detail.strip().lower())
            if key in seen_details:
                continue
            seen_details.add(key)
            deduped.append(item)

        return deduped[:12]


class DecisionJournalComposer:
    def compose(
        self,
        rag_decision: RAGDecision,
        model_status: dict,
        fields: list[VddFieldValue],
        issues: list[GenerationIssue],
        risks: list[RiskItem],
        stakeholder_insights: list[StakeholderInsight],
    ) -> dict:
        total_fields = len(fields)
        filled_fields = len([field for field in fields if field.status == "filled"])
        unresolved_fields = len([field for field in fields if field.status != "filled"])

        open_actions: list[str] = []
        for field in fields:
            if field.status in {"missing", "needs_review"}:
                action = f"Resolve field '{field.label}' ({field.field_id}) before final approval."
                open_actions.append(action)

        high_risks = [risk for risk in risks if risk.severity in {"high", "critical"}]
        if high_risks:
            open_actions.append("Address high-severity risks before Nulla Osta decision.")

        if model_status.get("degraded_mode"):
            open_actions.append("Re-run verification with both LLMs online to improve confidence.")

        return {
            "run_summary": {
                "rag_mode": rag_decision.mode,
                "rag_rationale": rag_decision.rationale,
                "fields_total": total_fields,
                "fields_filled": filled_fields,
                "fields_unresolved": unresolved_fields,
                "issues_count": len(issues),
                "risk_count": len(risks),
            },
            "model_status": model_status,
            "stakeholder_insights": [
                {
                    "insight_id": insight.insight_id,
                    "title": insight.title,
                    "detail": insight.detail,
                    "priority": insight.priority,
                    "source_refs": insight.source_refs,
                }
                for insight in stakeholder_insights
            ],
            "risk_radar": [
                {
                    "risk_id": risk.risk_id,
                    "severity": risk.severity,
                    "category": risk.category,
                    "title": risk.title,
                    "description": risk.description,
                    "evidence_refs": risk.evidence_refs,
                    "mitigation": risk.mitigation,
                    "status": risk.status,
                }
                for risk in risks
            ],
            "open_actions": open_actions,
        }
