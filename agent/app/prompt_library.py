from __future__ import annotations

import json

from .models import VddFieldSpec


def build_primary_system_prompt(language_priority: str) -> str:
    return (
        "You are the Primary LLM for structured release drafting. "
        "Return strictly valid RFC-8259 JSON with no markdown. "
        "Use only provided evidence snippets and never invent facts. "
        f"Language policy: {language_priority}. Favor English and Italian quality when possible."
    )


def build_primary_user_prompt(
    fields: list[VddFieldSpec],
    evidence_context: str,
    rag_mode: str,
) -> str:
    schema = {
        "fields": [
            {
                "field_id": "string",
                "value": "string or null",
                "status": "filled|missing|needs_review",
                "confidence": "0-1 float",
                "citations": [
                    {
                        "source_file": "string",
                        "chunk_id": "string or null",
                        "snippet": "string",
                        "score": "float",
                    }
                ],
                "notes": "string optional",
            }
        ]
    }

    field_lines = [
        f"- {field.field_id} | label={field.label} | required={field.required} | type={field.value_type}"
        for field in fields
    ]

    return (
        "Generate draft values for the requested fields using only the provided evidence.\n"
        f"RAG mode: {rag_mode}\n"
        "Fields:\n"
        + "\n".join(field_lines)
        + "\n\n"
        + "Output JSON schema example:\n"
        + json.dumps(schema, ensure_ascii=False, indent=2)
        + "\n\nEvidence context:\n"
        + evidence_context
    )


def build_secondary_system_prompt(language_priority: str) -> str:
    return (
        "You are the Secondary LLM verifier. "
        "You receive evidence and the primary draft. "
        "Fact-check each field, detect unsupported claims, and return strictly valid RFC-8259 JSON only. "
        f"Language policy: {language_priority}."
    )


def build_secondary_user_prompt(primary_payload: dict, evidence_context: str) -> str:
    schema = {
        "verdicts": [
            {
                "field_id": "string",
                "verdict": "accept|contested|insufficient_evidence",
                "confidence_adjustment": "-1.0 to +1.0 float",
                "comment": "string",
            }
        ],
        "risk_notes": ["string"],
        "stakeholder_insights": ["string"],
    }

    return (
        "Validate the primary output against evidence.\n"
        "Return JSON with verdicts and observations.\n"
        "Schema example:\n"
        + json.dumps(schema, ensure_ascii=False, indent=2)
        + "\n\nPrimary payload:\n"
        + json.dumps(primary_payload, ensure_ascii=False, indent=2)
        + "\n\nEvidence context:\n"
        + evidence_context
    )
