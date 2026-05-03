from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class GenerationIssue:
    issue_id: str
    severity: str
    category: str
    message: str
    recommendation: str | None = None
    field_id: str | None = None
    document_id: str | None = None


@dataclass
class EvidenceDocument:
    document_id: str
    source_file: str
    relative_path: str
    extension: str
    content_type: str
    text: str
    sections: dict[str, str] = field(default_factory=dict)
    tables: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "success"


@dataclass
class EvidenceChunk:
    chunk_id: str
    document_id: str
    source_file: str
    text: str
    start_char: int
    end_char: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VddFieldSpec:
    field_id: str
    label: str
    required: bool
    value_type: str = "text"
    hint: str | None = None
    confidence: float = 1.0


@dataclass
class VddCitation:
    document_id: str
    source_file: str
    chunk_id: str | None
    snippet: str
    score: float


@dataclass
class VddFieldValue:
    field_id: str
    label: str
    value: str | None
    status: str
    confidence: float
    citations: list[VddCitation] = field(default_factory=list)
    notes: str | None = None
    verified: bool = False
    verifier_comment: str | None = None


@dataclass
class RetrievalHit:
    chunk: EvidenceChunk
    score: float


@dataclass
class TraceLink:
    field_id: str
    document_id: str
    source_file: str
    chunk_id: str | None
    score: float
    snippet: str


@dataclass
class RiskItem:
    risk_id: str
    severity: str
    category: str
    title: str
    description: str
    evidence_refs: list[str] = field(default_factory=list)
    mitigation: str | None = None
    status: str = "open"


@dataclass
class StakeholderInsight:
    insight_id: str
    title: str
    detail: str
    priority: str
    source_refs: list[str] = field(default_factory=list)


@dataclass
class RAGDecision:
    mode: str
    estimated_tokens: int
    total_documents: int
    total_chars: int
    rationale: str


@dataclass
class PipelineRunManifest:
    run_id: str
    version_key: str
    timestamp_utc: str
    project: str
    semver: str
    rag_mode: str
    rag_rationale: str
    inputs_processed: int
    fields_detected: int
    fields_generated: int
    issues_count: int
    degraded_mode: bool
    model_status: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)


@dataclass
class TemplateParseResult:
    fields: list[VddFieldSpec]
    issues: list[GenerationIssue] = field(default_factory=list)


def dataclass_to_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, list):
        return [dataclass_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {k: dataclass_to_dict(v) for k, v in value.items()}
    return value
