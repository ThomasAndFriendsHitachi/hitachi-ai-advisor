from __future__ import annotations

from pathlib import Path
from typing import Any

from .composers import DecisionJournalComposer, RiskRadarComposer, StakeholderInsightComposer, TraceMapComposer
from .config import ModelRuntimeConfig, PipelineConfig
from .ingestion import EvidenceIngestionService
from .llm_clients import BaseJSONLLMClient, build_llm_client
from .models import (
    EvidenceDocument,
    GenerationIssue,
    PipelineRunManifest,
    RAGDecision,
    TraceLink,
    VddCitation,
    VddFieldSpec,
    VddFieldValue,
    dataclass_to_dict,
)
from .prompt_library import (
    build_primary_system_prompt,
    build_primary_user_prompt,
    build_secondary_system_prompt,
    build_secondary_user_prompt,
)
from .rag import ChunkBuilder, build_retriever, summarize_hits, RAGDecisionEngine
from .template_parser import VddTemplateParser
from .utils import ensure_dir, estimate_tokens, short_snippet, slugify, stable_id, utc_now_iso, utc_today_ymd, write_json


class AIPipeline:
    def __init__(self, config: PipelineConfig, runtime: ModelRuntimeConfig) -> None:
        self.config = config
        self.runtime = runtime

    def run(self) -> PipelineRunManifest:
        issues: list[GenerationIssue] = []

        # Keep local model artifact folders available for offline/local providers.
        ensure_dir(self.config.model_catalog_dir)
        ensure_dir(self.config.primary_model_dir)
        ensure_dir(self.config.secondary_model_dir)
        ensure_dir(self.config.embedding_model_dir)

        ingestion = EvidenceIngestionService(self.config.input_dir)
        documents, ingest_issues = ingestion.ingest()
        issues.extend(ingest_issues)

        template_result = VddTemplateParser(self.config.template_path).parse()
        field_specs = template_result.fields
        issues.extend(template_result.issues)

        chunks = ChunkBuilder(
            chunk_size=self.config.rag_chunk_size,
            overlap=self.config.rag_chunk_overlap,
        ).build(documents)

        decision = RAGDecisionEngine(
            token_budget=self.config.direct_context_token_budget,
            doc_limit=self.config.direct_context_doc_limit,
        ).decide(documents, field_count=len(field_specs))

        retriever, retriever_issues = build_retriever(
            chunks=chunks,
            prefer_faiss=(decision.mode == "rag"),
            vector_dim=self.config.rag_vector_dim,
            retrieval_strategy=self.config.rag_retrieval_strategy,
            embedding_model=self.config.rag_embedding_model,
            embedding_model_dir=str(self.config.embedding_model_dir),
            embedding_device=self.config.rag_embedding_device,
        )
        issues.extend(retriever_issues)

        primary_client = build_llm_client(
            provider=self.config.primary_provider,
            model=self.config.primary_model,
            openai_api_key=self.runtime.openai_api_key,
            anthropic_api_key=self.runtime.anthropic_api_key,
            role_api_key=self.runtime.primary_api_key,
            role_base_url=self.runtime.primary_base_url,
            role_model_dir=str(self.config.primary_model_dir),
            ollama_host=self.runtime.ollama_host,
        )
        secondary_client = build_llm_client(
            provider=self.config.secondary_provider,
            model=self.config.secondary_model,
            openai_api_key=self.runtime.openai_api_key,
            anthropic_api_key=self.runtime.anthropic_api_key,
            role_api_key=self.runtime.secondary_api_key,
            role_base_url=self.runtime.secondary_base_url,
            role_model_dir=str(self.config.secondary_model_dir),
            ollama_host=self.runtime.ollama_host,
        )

        primary_fields, primary_issues, primary_raw = self._generate_primary_fields(
            field_specs=field_specs,
            documents=documents,
            retriever=retriever,
            rag_decision=decision,
            primary_client=primary_client,
        )
        issues.extend(primary_issues)

        verifier_notes: list[str] = []
        verify_issues, secondary_raw, verifier_notes = self._verify_secondary(
            fields=primary_fields,
            documents=documents,
            retriever=retriever,
            secondary_client=secondary_client,
        )
        issues.extend(verify_issues)

        trace_links: list[TraceLink] = TraceMapComposer().compose(primary_fields)
        risk_items = RiskRadarComposer().compose(issues, primary_fields, rag_mode=decision.mode)
        stakeholder_insights = StakeholderInsightComposer().compose(
            evidence_texts=[doc.text for doc in documents],
            fields=primary_fields,
            risk_items=risk_items,
            verifier_notes=verifier_notes,
        )

        degraded_mode = (not primary_client.is_available()) or (not secondary_client.is_available())
        model_status = {
            "primary_provider": self.config.primary_provider,
            "primary_model": self.config.primary_model,
            "primary_profile": self.config.primary_profile,
            "primary_available": primary_client.is_available(),
            "secondary_provider": self.config.secondary_provider,
            "secondary_model": self.config.secondary_model,
            "secondary_profile": self.config.secondary_profile,
            "secondary_available": secondary_client.is_available(),
            "degraded_mode": degraded_mode,
            "primary_model_dir": str(self.config.primary_model_dir),
            "secondary_model_dir": str(self.config.secondary_model_dir),
            "model_catalog_dir": str(self.config.model_catalog_dir),
            "model_profiles_path": (str(self.config.model_profiles_path) if self.config.model_profiles_path else None),
            "embedding_model": self.config.rag_embedding_model,
            "embedding_model_dir": str(self.config.embedding_model_dir),
            "retrieval_strategy": self.config.rag_retrieval_strategy,
        }

        decision_journal = DecisionJournalComposer().compose(
            rag_decision=decision,
            model_status=model_status,
            fields=primary_fields,
            issues=issues,
            risks=risk_items,
            stakeholder_insights=stakeholder_insights,
        )

        artifact_dir, version_key = self._prepare_output_dir()

        vdd_payload = {
            "version_key": version_key,
            "generated_at": utc_now_iso(),
            "project": self.config.project,
            "fields": [dataclass_to_dict(field) for field in primary_fields],
        }
        tracemap_payload = {
            "version_key": version_key,
            "links": [dataclass_to_dict(link) for link in trace_links],
        }
        issues_payload = {
            "version_key": version_key,
            "issues": [dataclass_to_dict(issue) for issue in issues],
        }
        risk_payload = {
            "version_key": version_key,
            "risks": [dataclass_to_dict(item) for item in risk_items],
        }
        insights_payload = {
            "version_key": version_key,
            "stakeholder_insights": [dataclass_to_dict(item) for item in stakeholder_insights],
        }

        artifacts = {
            "vdd": artifact_dir / "vdd.json",
            "tracemap": artifact_dir / "tracemap.json",
            "generation_issues": artifact_dir / "generation_issues.json",
            "risk_radar": artifact_dir / "risk_radar.json",
            "stakeholder_insights": artifact_dir / "stakeholder_insights.json",
            "decision_journal": artifact_dir / "decision_journal.json",
            "primary_raw": artifact_dir / "primary_raw.json",
            "secondary_raw": artifact_dir / "secondary_raw.json",
            "run_manifest": artifact_dir / "run_manifest.json",
        }

        write_json(artifacts["vdd"], vdd_payload)
        write_json(artifacts["tracemap"], tracemap_payload)
        write_json(artifacts["generation_issues"], issues_payload)
        write_json(artifacts["risk_radar"], risk_payload)
        write_json(artifacts["stakeholder_insights"], insights_payload)
        write_json(artifacts["decision_journal"], decision_journal)
        write_json(artifacts["primary_raw"], primary_raw)
        write_json(artifacts["secondary_raw"], secondary_raw)

        run_manifest = PipelineRunManifest(
            run_id=stable_id("run", f"{version_key}:{utc_now_iso()}"),
            version_key=version_key,
            timestamp_utc=utc_now_iso(),
            project=self.config.project,
            semver=self.config.semver,
            rag_mode=decision.mode,
            rag_rationale=decision.rationale,
            inputs_processed=len(documents),
            fields_detected=len(field_specs),
            fields_generated=len(primary_fields),
            issues_count=len(issues),
            degraded_mode=degraded_mode,
            model_status=model_status,
            artifacts={name: str(path) for name, path in artifacts.items()},
        )

        write_json(artifacts["run_manifest"], dataclass_to_dict(run_manifest))
        return run_manifest

    def _prepare_output_dir(self) -> tuple[Path, str]:
        ensure_dir(self.config.output_dir)
        base = f"{utc_today_ymd()}-{slugify(self.config.project)}-{self.config.semver}"
        candidate = self.config.output_dir / base
        if not candidate.exists():
            candidate.mkdir(parents=True, exist_ok=False)
            return candidate, base

        counter = 2
        while True:
            version_key = f"{base}-r{counter:02d}"
            path = self.config.output_dir / version_key
            if not path.exists():
                path.mkdir(parents=True, exist_ok=False)
                return path, version_key
            counter += 1

    def _generate_primary_fields(
        self,
        field_specs: list[VddFieldSpec],
        documents: list[EvidenceDocument],
        retriever,
        rag_decision: RAGDecision,
        primary_client: BaseJSONLLMClient,
    ) -> tuple[list[VddFieldValue], list[GenerationIssue], dict[str, Any]]:
        issues: list[GenerationIssue] = []

        if not primary_client.is_available():
            issues.append(
                GenerationIssue(
                    issue_id=stable_id("issue", "primary_unavailable"),
                    severity="critical",
                    category="llm",
                    message="Primary LLM unavailable; drafting could not be performed.",
                    recommendation="Configure primary provider credentials and endpoint, then rerun.",
                )
            )
            mapped_fields, map_issues = self._map_primary_payload_to_fields({"fields": []}, field_specs)
            issues.extend(map_issues)
            return mapped_fields, issues, {
                "mode": "error",
                "provider": self.config.primary_provider,
                "model": self.config.primary_model,
                "error": "Primary LLM unavailable",
            }

        # Online primary generation using compressed evidence context.
        try:
            evidence_context = self._build_evidence_context(field_specs, retriever)
            system_prompt = build_primary_system_prompt(self.config.language_priority)
            user_prompt = build_primary_user_prompt(field_specs, evidence_context, rag_decision.mode)
            result = primary_client.generate_json(system_prompt=system_prompt, user_prompt=user_prompt)
            mapped_fields, map_issues = self._map_primary_payload_to_fields(result.payload, field_specs)
            issues.extend(map_issues)
            return mapped_fields, issues, {
                "mode": "online",
                "provider": result.provider,
                "model": result.model,
                "payload": result.payload,
            }
        except Exception as exc:
            issues.append(
                GenerationIssue(
                    issue_id=stable_id("issue", f"primary_generation_failed:{exc}"),
                    severity="high",
                    category="llm",
                    message=f"Primary generation failed with invalid/unusable response. Error: {exc}",
                    recommendation="Inspect primary model output formatting and retry.",
                )
            )
            mapped_fields, map_issues = self._map_primary_payload_to_fields({"fields": []}, field_specs)
            issues.extend(map_issues)
            return mapped_fields, issues, {
                "mode": "error",
                "provider": self.config.primary_provider,
                "model": self.config.primary_model,
                "error": str(exc),
            }

    def _build_evidence_context(self, field_specs: list[VddFieldSpec], retriever) -> str:
        lines: list[str] = []
        max_context_tokens = 5200
        for field in field_specs:
            hits = retriever.query(f"{field.label} {field.hint or ''}", top_k=self.config.rag_top_k)
            if not hits:
                continue
            block = [
                f"Field: {field.field_id} | {field.label}",
                summarize_hits(hits, max_lines=3),
                "",
            ]
            candidate = "\n".join(lines + block)
            if estimate_tokens(candidate) > max_context_tokens:
                break
            lines.extend(block)
        return "\n".join(lines)

    def _map_primary_payload_to_fields(
        self,
        payload: dict[str, Any],
        specs: list[VddFieldSpec],
    ) -> tuple[list[VddFieldValue], list[GenerationIssue]]:
        issues: list[GenerationIssue] = []
        rows = payload.get("fields")
        if not isinstance(rows, list):
            issues.append(
                GenerationIssue(
                    issue_id=stable_id("issue", "primary_payload_shape"),
                    severity="medium",
                    category="llm",
                    message="Primary payload missing 'fields' list; switched to empty mapping.",
                    recommendation="Adjust prompt to enforce expected JSON structure.",
                )
            )
            rows = []

        by_id: dict[str, dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            field_id = str(row.get("field_id") or "").strip()
            if not field_id:
                continue
            by_id[field_id] = row

        mapped: list[VddFieldValue] = []
        for spec in specs:
            row = by_id.get(spec.field_id, {})
            citations: list[VddCitation] = []
            for citation in row.get("citations", []) if isinstance(row.get("citations"), list) else []:
                if not isinstance(citation, dict):
                    continue
                citations.append(
                    VddCitation(
                        document_id=str(citation.get("document_id") or "unknown"),
                        source_file=str(citation.get("source_file") or "unknown"),
                        chunk_id=str(citation.get("chunk_id") or "") or None,
                        snippet=str(citation.get("snippet") or ""),
                        score=float(citation.get("score") or 0.0),
                    )
                )

            status = str(row.get("status") or "missing")
            if status not in {"filled", "missing", "needs_review"}:
                status = "needs_review"

            confidence = row.get("confidence")
            try:
                confidence_float = float(confidence)
            except Exception:
                confidence_float = 0.0

            mapped.append(
                VddFieldValue(
                    field_id=spec.field_id,
                    label=spec.label,
                    value=(str(row.get("value")) if row.get("value") is not None else None),
                    status=status,
                    confidence=max(0.0, min(1.0, confidence_float)),
                    citations=citations,
                    notes=(str(row.get("notes")) if row.get("notes") else None),
                )
            )
        return mapped, issues

    def _verify_secondary(
        self,
        fields: list[VddFieldValue],
        documents: list[EvidenceDocument],
        retriever,
        secondary_client: BaseJSONLLMClient,
    ) -> tuple[list[GenerationIssue], dict[str, Any], list[str]]:
        issues: list[GenerationIssue] = []
        verifier_notes: list[str] = []

        if not secondary_client.is_available():
            issues.append(
                GenerationIssue(
                    issue_id=stable_id("issue", "secondary_unavailable"),
                    severity="high",
                    category="llm",
                    message="Secondary LLM unavailable; verification was skipped.",
                    recommendation="Configure secondary provider credentials and endpoint, then rerun.",
                )
            )
            return issues, {
                "mode": "error",
                "provider": self.config.secondary_provider,
                "model": self.config.secondary_model,
                "error": "Secondary LLM unavailable",
            }, verifier_notes

        try:
            evidence_context = self._build_secondary_context(fields, retriever)
            system_prompt = build_secondary_system_prompt(self.config.language_priority)
            user_prompt = build_secondary_user_prompt(
                primary_payload=self._build_secondary_primary_payload(fields),
                evidence_context=evidence_context,
            )
            result = secondary_client.generate_json(system_prompt=system_prompt, user_prompt=user_prompt)
            self._apply_secondary_payload(result.payload, fields, issues, verifier_notes)
            return issues, {
                "mode": "online",
                "provider": result.provider,
                "model": result.model,
                "payload": result.payload,
            }, verifier_notes
        except Exception as exc:
            issues.append(
                GenerationIssue(
                    issue_id=stable_id("issue", f"secondary_verification_failed:{exc}"),
                    severity="high",
                    category="llm",
                    message=f"Secondary verification failed with invalid/unusable response. Error: {exc}",
                    recommendation="Inspect secondary model output formatting and retry.",
                )
            )
            return issues, {
                "mode": "error",
                "provider": self.config.secondary_provider,
                "model": self.config.secondary_model,
                "error": str(exc),
            }, verifier_notes

    def _build_secondary_context(self, fields: list[VddFieldValue], retriever) -> str:
        lines: list[str] = []
        max_fields = 10
        max_context_tokens = 2200

        for field in fields[:max_fields]:
            value_hint = short_snippet(field.value or "", max_len=160)
            query = f"{field.label} {value_hint}"
            hits = retriever.query(query, top_k=2)
            if not hits:
                continue
            block = [
                f"Field: {field.field_id}",
                summarize_hits(hits, max_lines=1),
                "",
            ]
            candidate = "\n".join(lines + block)
            if estimate_tokens(candidate) > max_context_tokens:
                break
            lines.extend(block)
        return "\n".join(lines)

    def _build_secondary_primary_payload(self, fields: list[VddFieldValue]) -> dict[str, Any]:
        compact_fields: list[dict[str, Any]] = []
        for field in fields:
            compact_citations: list[dict[str, Any]] = []
            for citation in field.citations[:1]:
                compact_citations.append(
                    {
                        "source_file": citation.source_file,
                        "chunk_id": citation.chunk_id,
                        "snippet": short_snippet(citation.snippet, max_len=120),
                        "score": round(float(citation.score), 4),
                    }
                )

            compact_fields.append(
                {
                    "field_id": field.field_id,
                    "label": field.label,
                    "value": short_snippet(field.value, max_len=280) if field.value else None,
                    "status": field.status,
                    "confidence": round(float(field.confidence), 4),
                    "citations": compact_citations,
                }
            )

        return {"fields": compact_fields}

    def _apply_secondary_payload(
        self,
        payload: dict[str, Any],
        fields: list[VddFieldValue],
        issues: list[GenerationIssue],
        verifier_notes: list[str],
    ) -> None:
        by_id = {field.field_id: field for field in fields}

        verdicts = payload.get("verdicts") if isinstance(payload.get("verdicts"), list) else []
        for row in verdicts:
            if not isinstance(row, dict):
                continue
            field_id = str(row.get("field_id") or "").strip()
            field = by_id.get(field_id)
            if not field:
                continue

            verdict = str(row.get("verdict") or "").lower()
            adjustment = row.get("confidence_adjustment")
            try:
                adj = float(adjustment)
            except Exception:
                adj = 0.0
            comment = str(row.get("comment") or "").strip() or None

            field.confidence = max(0.0, min(1.0, field.confidence + adj))
            field.verifier_comment = comment

            if verdict == "accept":
                field.verified = True
            elif verdict in {"contested", "insufficient_evidence"}:
                field.verified = False
                field.status = "needs_review" if field.value else "missing"
                issues.append(
                    GenerationIssue(
                        issue_id=stable_id("issue", f"secondary_verdict:{field.field_id}:{verdict}"),
                        severity="high" if verdict == "insufficient_evidence" else "medium",
                        category="verification",
                        message=f"Secondary verifier marked field {field.field_id} as {verdict}.",
                        recommendation=comment or "Review source evidence and adjust the generated value.",
                        field_id=field.field_id,
                    )
                )

        for note in payload.get("risk_notes", []) if isinstance(payload.get("risk_notes"), list) else []:
            if isinstance(note, str) and note.strip():
                verifier_notes.append(note.strip())

        for note in payload.get("stakeholder_insights", []) if isinstance(payload.get("stakeholder_insights"), list) else []:
            if isinstance(note, str) and note.strip():
                verifier_notes.append(note.strip())
