# Model Storage Layout

This folder is the local model workspace for the AI Processing Layer.

## Structure

- primary_llm/: local files or references for the primary drafting model.
- secondary_llm/: local files or references for the secondary verifier model.
- embedding_models/: local files for semantic embedding retrievers.
- docs/: model-specific setup notes, prompts, or adapter instructions.

## Notes

1. The pipeline does not force a single provider.
2. You can use hosted providers or local providers.
3. For local providers (for example Ollama, vLLM, LM Studio, TGI), keep model notes/config in this folder and point runtime to the correct endpoint.

## Suggested files to add

- primary_llm/model_info.json
- secondary_llm/model_info.json
- embedding_models/bge-m3/model_info.json
- docs/provider_setup.md
- model_profiles.example.json

## Profile catalog

- model_profiles.json is the active runtime catalog consumed by CLI flags:
  - --model-profiles-file
  - --primary-profile
  - --secondary-profile
- model_profiles.example.json is a reference template.

## Hugging Face local quick start

1. Install local dependencies.

pip install -r requirements-hf-local.txt

1. Optional: enable direct GGUF runtime.

pip install -r requirements-hf-gguf.txt

1. Download recommended GGUF models.

python scripts/download_hf_models.py

1. Optional: download the recommended semantic embedding model.

python scripts/download_hf_models.py --with-embedding

1. Run pipeline with local profiles.

python main.py --primary-profile primary-hf-meta-llama31-8b --secondary-profile secondary-hf-mistral7b

1. Enable semantic retrieval with local embeddings.

python main.py --primary-profile primary-hf-meta-llama31-8b --secondary-profile secondary-hf-mistral7b --retrieval-strategy semantic --embedding-model models/embedding_models/bge-m3 --embedding-model-dir models/embedding_models/bge-m3

If local runtime installation fails, use local OpenAI-compatible profiles:

python main.py --primary-profile primary-hf-lmstudio --secondary-profile secondary-hf-lmstudio
