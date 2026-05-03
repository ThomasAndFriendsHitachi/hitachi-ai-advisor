from __future__ import annotations

import argparse
from pathlib import Path


def download_model_transformers(repo_id: str, target_dir: Path) -> None:
    from huggingface_hub import snapshot_download  # type: ignore

    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {repo_id} -> {target_dir}")
    snapshot_download(
        repo_id=repo_id,
        local_dir=str(target_dir),
    )


def download_model_gguf(repo_id: str, filename: str, target_dir: Path) -> Path:
    from huggingface_hub import hf_hub_download  # type: ignore

    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {repo_id}:{filename} -> {target_dir}")
    downloaded = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=str(target_dir),
    )
    return Path(downloaded)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download Hugging Face models for local offline pipeline usage")
    parser.add_argument(
        "--format",
        choices=["gguf", "transformers"],
        default="gguf",
        help="Download format: gguf (recommended) or full transformers model folders",
    )
    parser.add_argument(
        "--primary-repo",
        default="bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        help="Primary role HF repo ID",
    )
    parser.add_argument(
        "--secondary-repo",
        default="bartowski/Mistral-7B-Instruct-v0.3-GGUF",
        help="Secondary role HF repo ID",
    )
    parser.add_argument(
        "--primary-file",
        default="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        help="Primary GGUF filename",
    )
    parser.add_argument(
        "--secondary-file",
        default="Mistral-7B-Instruct-v0.3-Q4_K_M.gguf",
        help="Secondary GGUF filename",
    )
    parser.add_argument("--primary-dir", default="models/primary_llm", help="Primary model directory")
    parser.add_argument("--secondary-dir", default="models/secondary_llm", help="Secondary model directory")
    parser.add_argument(
        "--with-embedding",
        action="store_true",
        help="Also download embedding model for semantic retrieval",
    )
    parser.add_argument(
        "--embedding-repo",
        default="BAAI/bge-m3",
        help="Embedding model HF repo ID",
    )
    parser.add_argument(
        "--embedding-dir",
        default="models/embedding_models/bge-m3",
        help="Embedding model directory",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    primary_root = Path(args.primary_dir)
    secondary_root = Path(args.secondary_dir)
    embedding_root = Path(args.embedding_dir)

    if args.format == "gguf":
        primary_file = download_model_gguf(
            repo_id=args.primary_repo,
            filename=args.primary_file,
            target_dir=primary_root,
        )
        secondary_file = download_model_gguf(
            repo_id=args.secondary_repo,
            filename=args.secondary_file,
            target_dir=secondary_root,
        )

        print("Download complete.")
        print(f"Primary GGUF path: {primary_file}")
        print(f"Secondary GGUF path: {secondary_file}")

        if args.with_embedding:
            download_model_transformers(args.embedding_repo, embedding_root)
            print(f"Embedding model path: {embedding_root}")
        return 0

    primary_target = primary_root / args.primary_repo.split("/")[-1]
    secondary_target = secondary_root / args.secondary_repo.split("/")[-1]
    download_model_transformers(args.primary_repo, primary_target)
    download_model_transformers(args.secondary_repo, secondary_target)

    print("Download complete.")
    print(f"Primary model path: {primary_target}")
    print(f"Secondary model path: {secondary_target}")

    if args.with_embedding:
        download_model_transformers(args.embedding_repo, embedding_root)
        print(f"Embedding model path: {embedding_root}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
