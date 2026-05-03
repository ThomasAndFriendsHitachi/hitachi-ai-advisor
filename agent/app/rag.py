from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import EvidenceChunk, EvidenceDocument, GenerationIssue, RAGDecision, RetrievalHit
from .utils import chunk_text, estimate_tokens, short_snippet, stable_id


_WORD_RE = re.compile(r"[a-zA-Z0-9_]+")

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
    "il",
    "lo",
    "la",
    "i",
    "gli",
    "le",
    "di",
    "del",
    "della",
    "delle",
    "dei",
    "da",
    "in",
    "su",
    "per",
    "con",
    "e",
    "o",
    "che",
    "un",
    "una",
    "sono",
    "html",
    "class",
    "div",
    "span",
    "href",
    "http",
    "https",
}


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in _WORD_RE.findall(text):
        token = raw.lower()
        if len(token) <= 2:
            continue
        if token in _STOPWORDS:
            continue
        if token.isdigit():
            continue
        tokens.append(token)
    return tokens


@dataclass
class ChunkBuilder:
    chunk_size: int
    overlap: int

    def build(self, documents: Iterable[EvidenceDocument]) -> list[EvidenceChunk]:
        chunks: list[EvidenceChunk] = []
        for doc in documents:
            for start, end, piece in chunk_text(doc.text, self.chunk_size, self.overlap):
                chunk_id = stable_id("chunk", f"{doc.document_id}:{start}:{end}")
                chunks.append(
                    EvidenceChunk(
                        chunk_id=chunk_id,
                        document_id=doc.document_id,
                        source_file=doc.relative_path,
                        text=piece,
                        start_char=start,
                        end_char=end,
                        metadata={"extension": doc.extension},
                    )
                )
        return chunks


class RAGDecisionEngine:
    def __init__(self, token_budget: int, doc_limit: int) -> None:
        self.token_budget = token_budget
        self.doc_limit = doc_limit

    def decide(self, documents: list[EvidenceDocument], field_count: int) -> RAGDecision:
        total_chars = sum(len(doc.text) for doc in documents)
        estimated_tokens = estimate_tokens("\n".join(doc.text for doc in documents))
        total_documents = len(documents)

        noisy_docs = 0
        for doc in documents:
            if doc.extension in {".html", ".xml"} and len(doc.text) > 8000:
                noisy_docs += 1

        oversized = estimated_tokens > int(self.token_budget * 0.9)
        too_many_docs = total_documents > self.doc_limit
        high_noise = noisy_docs > 0
        many_fields = field_count > 20 and estimated_tokens > int(self.token_budget * 0.65)

        use_rag = oversized or too_many_docs or high_noise or many_fields
        rationale_parts = [
            f"estimated_tokens={estimated_tokens}",
            f"token_budget={self.token_budget}",
            f"doc_count={total_documents}",
            f"doc_limit={self.doc_limit}",
            f"noisy_docs={noisy_docs}",
            f"field_count={field_count}",
        ]
        rationale = " ; ".join(rationale_parts)

        return RAGDecision(
            mode="rag" if use_rag else "direct",
            estimated_tokens=estimated_tokens,
            total_documents=total_documents,
            total_chars=total_chars,
            rationale=rationale,
        )


class BaseRetriever:
    def build(self, chunks: list[EvidenceChunk]) -> None:
        raise NotImplementedError

    def query(self, text: str, top_k: int) -> list[RetrievalHit]:
        raise NotImplementedError


class LexicalRetriever(BaseRetriever):
    def __init__(self) -> None:
        self._chunks: list[EvidenceChunk] = []
        self._chunk_tokens: list[set[str]] = []

    def build(self, chunks: list[EvidenceChunk]) -> None:
        self._chunks = chunks
        self._chunk_tokens = [set(_tokenize(chunk.text)) for chunk in chunks]

    def query(self, text: str, top_k: int) -> list[RetrievalHit]:
        if not self._chunks:
            return []

        query_tokens = set(_tokenize(text))
        if not query_tokens:
            return []

        scored: list[tuple[int, float]] = []
        for index, tokens in enumerate(self._chunk_tokens):
            overlap = len(query_tokens.intersection(tokens))
            if overlap == 0:
                continue
            recall = overlap / max(1, len(query_tokens))
            precision = overlap / max(1, len(tokens))
            # Emphasize query coverage while still penalizing overly broad chunks.
            score = (0.85 * recall) + (0.15 * precision)
            scored.append((index, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return [
            RetrievalHit(chunk=self._chunks[index], score=score)
            for index, score in scored[: max(1, top_k)]
        ]


class FaissRetriever(BaseRetriever):
    def __init__(self, dim: int) -> None:
        self.dim = dim
        self._chunks: list[EvidenceChunk] = []
        self._index = None
        self._np = None

        try:
            import numpy as np  # type: ignore
            import faiss  # type: ignore

            self._np = np
            self._faiss = faiss
        except Exception as exc:  # pragma: no cover - optional dependency branch
            raise RuntimeError(f"FAISS dependencies not available: {exc}")

    def _vectorize(self, text: str):
        np = self._np
        vec = np.zeros(self.dim, dtype="float32")
        for token in _tokenize(text):
            slot = hash(token) % self.dim
            vec[slot] += 1.0

        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec

    def build(self, chunks: list[EvidenceChunk]) -> None:
        np = self._np
        self._chunks = chunks
        if not chunks:
            self._index = None
            return

        matrix = np.vstack([self._vectorize(chunk.text) for chunk in chunks]).astype("float32")
        self._index = self._faiss.IndexFlatIP(self.dim)
        self._index.add(matrix)

    def query(self, text: str, top_k: int) -> list[RetrievalHit]:
        if self._index is None or not self._chunks:
            return []

        np = self._np
        qvec = self._vectorize(text).reshape(1, self.dim).astype("float32")
        scores, indices = self._index.search(qvec, max(1, top_k))

        hits: list[RetrievalHit] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._chunks):
                continue
            hits.append(RetrievalHit(chunk=self._chunks[idx], score=float(score)))
        return hits


class SemanticEmbeddingRetriever(BaseRetriever):
    def __init__(
        self,
        model_name_or_path: str,
        model_dir: str | None = None,
        device: str = "cpu",
        batch_size: int = 16,
    ) -> None:
        self.model_name_or_path = model_name_or_path
        self.model_dir = model_dir
        self.device = device
        self.batch_size = max(1, batch_size)
        self._chunks: list[EvidenceChunk] = []
        self._model = None
        self._matrix = None
        self._np = None

    def _resolve_model_source(self) -> tuple[str, bool]:
        direct = Path(self.model_name_or_path)
        if direct.exists():
            return str(direct), True

        if self.model_dir:
            model_root = Path(self.model_dir)
            if model_root.exists():
                nested = model_root / self.model_name_or_path.split("/")[-1]
                if nested.exists():
                    return str(nested), True

                if (model_root / "config.json").exists() and (model_root / "tokenizer_config.json").exists():
                    return str(model_root), True

        return self.model_name_or_path, False

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return

        import numpy as np  # type: ignore
        from sentence_transformers import SentenceTransformer  # type: ignore

        self._np = np
        source, local_files_only = self._resolve_model_source()

        try:
            self._model = SentenceTransformer(
                source,
                device=self.device,
                trust_remote_code=True,
                local_files_only=local_files_only,
            )
        except TypeError:
            # Compatibility fallback for older sentence-transformers versions.
            self._model = SentenceTransformer(source, device=self.device)

    def build(self, chunks: list[EvidenceChunk]) -> None:
        self._chunks = chunks
        if not chunks:
            self._matrix = None
            return

        self._ensure_loaded()
        texts = [chunk.text for chunk in chunks]
        matrix = self._model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        self._matrix = matrix.astype("float32")

    def query(self, text: str, top_k: int) -> list[RetrievalHit]:
        if self._matrix is None or not self._chunks:
            return []

        qvec = self._model.encode(
            [text],
            batch_size=1,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )[0].astype("float32")

        scores = self._matrix @ qvec
        k = max(1, min(top_k, len(self._chunks)))
        if k == len(self._chunks):
            ranked_idx = scores.argsort()[::-1]
        else:
            candidate_idx = self._np.argpartition(scores, -k)[-k:]
            ranked_idx = candidate_idx[self._np.argsort(scores[candidate_idx])[::-1]]

        hits: list[RetrievalHit] = []
        for idx in ranked_idx:
            hits.append(RetrievalHit(chunk=self._chunks[int(idx)], score=float(scores[int(idx)])))
        return hits


def build_retriever(
    chunks: list[EvidenceChunk],
    prefer_faiss: bool,
    vector_dim: int,
    retrieval_strategy: str = "auto",
    embedding_model: str | None = None,
    embedding_model_dir: str | None = None,
    embedding_device: str = "cpu",
) -> tuple[BaseRetriever, list[GenerationIssue]]:
    issues: list[GenerationIssue] = []

    strategy = retrieval_strategy.strip().lower()
    if strategy not in {"auto", "lexical", "hashed_faiss", "semantic"}:
        issues.append(
            GenerationIssue(
                issue_id=stable_id("issue", f"retrieval_strategy_invalid:{strategy}"),
                severity="low",
                category="retrieval",
                message=f"Unknown retrieval strategy '{retrieval_strategy}'; falling back to auto.",
                recommendation="Use one of: auto, lexical, hashed_faiss, semantic.",
            )
        )
        strategy = "auto"

    if strategy == "lexical":
        retriever = LexicalRetriever()
        retriever.build(chunks)
        return retriever, issues

    if strategy == "semantic" or (strategy == "auto" and prefer_faiss and embedding_model):
        if not embedding_model:
            issues.append(
                GenerationIssue(
                    issue_id=stable_id("issue", "semantic_missing_model"),
                    severity="low",
                    category="retrieval",
                    message="Semantic retriever requested without embedding model; fallback retriever activated.",
                    recommendation=(
                        "Set --embedding-model to a Hugging Face embedding model id or local model directory."
                    ),
                )
            )
        else:
            try:
                retriever = SemanticEmbeddingRetriever(
                    model_name_or_path=embedding_model,
                    model_dir=embedding_model_dir,
                    device=embedding_device,
                )
                retriever.build(chunks)
                return retriever, issues
            except Exception as exc:
                issues.append(
                    GenerationIssue(
                        issue_id=stable_id("issue", f"semantic_fallback:{exc}"),
                        severity="low",
                        category="retrieval",
                        message="Semantic embedding retriever unavailable; fallback retriever activated.",
                        recommendation=(
                            "Install requirements-hf-transformers.txt and download the embedding model locally."
                        ),
                    )
                )

    if strategy == "hashed_faiss" or (strategy == "auto" and prefer_faiss):
        try:
            retriever: BaseRetriever = FaissRetriever(dim=vector_dim)
            retriever.build(chunks)
            return retriever, issues
        except Exception as exc:
            issues.append(
                GenerationIssue(
                    issue_id=stable_id("issue", f"faiss_fallback:{exc}"),
                    severity="low",
                    category="retrieval",
                    message="FAISS unavailable; fallback lexical retriever activated.",
                    recommendation="Install faiss-cpu and numpy for vector retrieval performance.",
                )
            )

    retriever = LexicalRetriever()
    retriever.build(chunks)
    return retriever, issues


def summarize_hits(hits: list[RetrievalHit], max_lines: int = 5) -> str:
    lines: list[str] = []
    for hit in hits[:max_lines]:
        lines.append(
            f"[{hit.chunk.source_file}#{hit.chunk.chunk_id} score={round(hit.score, 4)}] {short_snippet(hit.chunk.text, 220)}"
        )
    return "\n".join(lines)
