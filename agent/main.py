from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from app.config import ModelRuntimeConfig, PipelineConfig
from app.model_profiles import ModelProfile, load_selected_profiles
from app.pipeline import AIPipeline


def _flag_was_provided(flag_name: str, argv: list[str]) -> bool:
    for token in argv:
        if token == flag_name or token.startswith(f"{flag_name}="):
            return True
    return False


def _select_api_key(explicit_env_value: str | None, profile: ModelProfile | None) -> str | None:
    if explicit_env_value:
        return explicit_env_value
    if profile and profile.api_key_env:
        return os.getenv(profile.api_key_env)
    return None


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Processing Layer PoC pipeline")
    parser.add_argument("--inputs", default="inputs", help="Input directory for extracted JSON files")
    parser.add_argument("--template", default="templates/vdd_template.docx", help="VDD DOCX template path")
    parser.add_argument("--outputs", default="outputs", help="Output root directory")
    parser.add_argument("--model-catalog-dir", default="models", help="Model catalog directory")
    parser.add_argument(
        "--model-profiles-file",
        default=(os.getenv("MODEL_PROFILES_FILE") or "models/model_profiles.json"),
        help="Path to model profiles JSON file",
    )
    parser.add_argument(
        "--primary-profile",
        default=(os.getenv("PRIMARY_PROFILE") or ""),
        help="Primary model profile name from profiles file",
    )
    parser.add_argument(
        "--secondary-profile",
        default=(os.getenv("SECONDARY_PROFILE") or ""),
        help="Secondary model profile name from profiles file",
    )
    parser.add_argument("--primary-model-dir", default="models/primary_llm", help="Primary local model directory")
    parser.add_argument("--secondary-model-dir", default="models/secondary_llm", help="Secondary local model directory")
    parser.add_argument(
        "--embedding-model-dir",
        default="models/embedding_models/bge-m3",
        help="Embedding model directory for semantic retrieval",
    )
    parser.add_argument("--project", default="demo", help="Project key for versioned artifacts")
    parser.add_argument("--semver", default="0.1.0", help="Semantic version component")
    parser.add_argument(
        "--primary-provider",
        default="openai",
        help="Primary provider (openai, anthropic, openai_compatible, ollama, hf_local)",
    )
    parser.add_argument(
        "--secondary-provider",
        default="anthropic",
        help="Secondary provider (openai, anthropic, openai_compatible, ollama, hf_local)",
    )
    parser.add_argument("--primary-model", default="gpt-4.1-mini", help="Primary model identifier")
    parser.add_argument("--secondary-model", default="claude-3-5-sonnet-20241022", help="Secondary model identifier")
    parser.add_argument("--primary-base-url", default="", help="Primary provider base URL (for openai_compatible)")
    parser.add_argument("--secondary-base-url", default="", help="Secondary provider base URL (for openai_compatible)")
    parser.add_argument("--direct-budget", type=int, default=12000, help="Direct mode token budget")
    parser.add_argument("--direct-doc-limit", type=int, default=6, help="Document count threshold for direct mode")
    parser.add_argument("--chunk-size", type=int, default=1200, help="Chunk size for retrieval")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Chunk overlap for retrieval")
    parser.add_argument("--top-k", type=int, default=6, help="Top-K retrieval hits")
    parser.add_argument("--vector-dim", type=int, default=256, help="Hashed vector dimension for retriever")
    parser.add_argument(
        "--retrieval-strategy",
        default=(os.getenv("RAG_RETRIEVAL_STRATEGY") or "auto"),
        help="Retriever strategy (auto, lexical, hashed_faiss, semantic)",
    )
    parser.add_argument(
        "--embedding-model",
        default=(os.getenv("RAG_EMBEDDING_MODEL") or ""),
        help="Embedding model id/path for semantic retrieval (for example BAAI/bge-m3)",
    )
    parser.add_argument(
        "--embedding-device",
        default=(os.getenv("RAG_EMBEDDING_DEVICE") or "cpu"),
        help="Embedding runtime device (cpu, cuda, mps)",
    )
    parser.add_argument(
        "--language-priority",
        default="multilingual",
        help="Language policy hint (multilingual, english, italian, etc.)",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    argv = sys.argv[1:]
    args = parser.parse_args()

    primary_profile_name = args.primary_profile.strip() or None
    secondary_profile_name = args.secondary_profile.strip() or None
    profiles_path = Path(args.model_profiles_file)
    try:
        primary_profile, secondary_profile = load_selected_profiles(
            profiles_path=profiles_path,
            primary_profile_name=primary_profile_name,
            secondary_profile_name=secondary_profile_name,
        )
    except Exception as exc:
        parser.error(str(exc))

    primary_provider = args.primary_provider
    primary_model = args.primary_model
    primary_base_url = args.primary_base_url or os.getenv("PRIMARY_LLM_BASE_URL") or None
    primary_model_dir = Path(args.primary_model_dir)

    secondary_provider = args.secondary_provider
    secondary_model = args.secondary_model
    secondary_base_url = args.secondary_base_url or os.getenv("SECONDARY_LLM_BASE_URL") or None
    secondary_model_dir = Path(args.secondary_model_dir)

    if primary_profile:
        if not _flag_was_provided("--primary-provider", argv):
            primary_provider = primary_profile.provider
        if not _flag_was_provided("--primary-model", argv):
            primary_model = primary_profile.model
        if not _flag_was_provided("--primary-base-url", argv) and primary_profile.base_url:
            primary_base_url = primary_profile.base_url
        if not _flag_was_provided("--primary-model-dir", argv) and primary_profile.model_dir:
            primary_model_dir = Path(primary_profile.model_dir)

    if secondary_profile:
        if not _flag_was_provided("--secondary-provider", argv):
            secondary_provider = secondary_profile.provider
        if not _flag_was_provided("--secondary-model", argv):
            secondary_model = secondary_profile.model
        if not _flag_was_provided("--secondary-base-url", argv) and secondary_profile.base_url:
            secondary_base_url = secondary_profile.base_url
        if not _flag_was_provided("--secondary-model-dir", argv) and secondary_profile.model_dir:
            secondary_model_dir = Path(secondary_profile.model_dir)

    config = PipelineConfig(
        input_dir=Path(args.inputs),
        template_path=Path(args.template),
        output_dir=Path(args.outputs),
        model_catalog_dir=Path(args.model_catalog_dir),
        model_profiles_path=profiles_path,
        primary_model_dir=primary_model_dir,
        secondary_model_dir=secondary_model_dir,
        embedding_model_dir=Path(args.embedding_model_dir),
        project=args.project,
        semver=args.semver,
        direct_context_token_budget=args.direct_budget,
        direct_context_doc_limit=args.direct_doc_limit,
        rag_chunk_size=args.chunk_size,
        rag_chunk_overlap=args.chunk_overlap,
        rag_top_k=args.top_k,
        rag_vector_dim=args.vector_dim,
        rag_retrieval_strategy=args.retrieval_strategy,
        rag_embedding_model=(args.embedding_model.strip() or None),
        rag_embedding_device=args.embedding_device,
        language_priority=args.language_priority,
        primary_profile=primary_profile_name,
        secondary_profile=secondary_profile_name,
        primary_provider=primary_provider,
        secondary_provider=secondary_provider,
        primary_model=primary_model,
        secondary_model=secondary_model,
    )

    runtime = ModelRuntimeConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        primary_api_key=_select_api_key(os.getenv("PRIMARY_LLM_API_KEY"), primary_profile),
        secondary_api_key=_select_api_key(os.getenv("SECONDARY_LLM_API_KEY"), secondary_profile),
        primary_base_url=primary_base_url,
        secondary_base_url=secondary_base_url,
        ollama_host=os.getenv("OLLAMA_HOST") or "http://localhost:11434",
    )

    pipeline = AIPipeline(config=config, runtime=runtime)
    manifest = pipeline.run()

    print("Pipeline run completed.")
    print(f"Run ID: {manifest.run_id}")
    print(f"Version Key: {manifest.version_key}")
    print(f"RAG Mode: {manifest.rag_mode}")
    print(f"Artifacts: {manifest.artifacts}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
