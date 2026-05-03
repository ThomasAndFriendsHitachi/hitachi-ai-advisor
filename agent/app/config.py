from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    input_dir: Path
    template_path: Path
    output_dir: Path
    model_catalog_dir: Path = Path("models")
    model_profiles_path: Path | None = None
    primary_model_dir: Path = Path("models/primary_llm")
    secondary_model_dir: Path = Path("models/secondary_llm")
    embedding_model_dir: Path = Path("models/embedding_models/bge-m3")
    project: str = "demo"
    semver: str = "0.1.0"
    direct_context_token_budget: int = 12000
    direct_context_doc_limit: int = 6
    rag_chunk_size: int = 1200
    rag_chunk_overlap: int = 200
    rag_top_k: int = 6
    rag_vector_dim: int = 256
    rag_retrieval_strategy: str = "auto"
    rag_embedding_model: str | None = None
    rag_embedding_device: str = "cpu"
    language_priority: str = "multilingual"
    primary_profile: str | None = None
    secondary_profile: str | None = None
    primary_provider: str = "openai"
    secondary_provider: str = "anthropic"
    primary_model: str = "gpt-4.1-mini"
    secondary_model: str = "claude-3-5-sonnet-20241022"


@dataclass(frozen=True)
class ModelRuntimeConfig:
    openai_api_key: str | None
    anthropic_api_key: str | None
    primary_api_key: str | None
    secondary_api_key: str | None
    primary_base_url: str | None
    secondary_base_url: str | None
    ollama_host: str | None
