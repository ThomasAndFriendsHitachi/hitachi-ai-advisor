# Provider Setup Notes

This project supports multiple providers through a provider selector.

Supported provider keys:

- openai
- anthropic
- openai_compatible
- ollama
- hf_local

## openai_compatible

Use this for any endpoint exposing OpenAI-compatible APIs (for example vLLM, LM Studio OpenAI server, some managed gateways).

Set:

- PRIMARY_LLM_BASE_URL or SECONDARY_LLM_BASE_URL
- PRIMARY_LLM_API_KEY or SECONDARY_LLM_API_KEY (if required)

## ollama

- Install Ollama locally.
- Pull your model.
- Ensure server is reachable at OLLAMA_HOST (default: <http://localhost:11434>).

## hf_local

Use this for direct local Hugging Face model execution with no paid API key.

1. Install optional local dependencies.

pip install -r requirements-hf-local.txt

1. Install optional semantic embedding dependencies.

pip install -r requirements-hf-transformers.txt

1. Optional: enable direct GGUF runtime.

pip install -r requirements-hf-gguf.txt

1. Download recommended models.

python scripts/download_hf_models.py

1. Optional: download the recommended embedding model for semantic retrieval.

python scripts/download_hf_models.py --with-embedding

1. Run with profile-based selection.

python main.py --primary-profile primary-hf-meta-llama31-8b --secondary-profile secondary-hf-mistral7b

1. Run with semantic embedding retrieval enabled.

python main.py --primary-profile primary-hf-meta-llama31-8b --secondary-profile secondary-hf-mistral7b --retrieval-strategy semantic --embedding-model models/embedding_models/bge-m3 --embedding-model-dir models/embedding_models/bge-m3

Notes:

- Profile entries point to local GGUF files under models/primary_llm and models/secondary_llm.
- Embedding profile entry points to models/embedding_models/bge-m3.
- You can replace profile model paths with any local GGUF file or transformers model folder.
- If llama-cpp installation fails on your machine, use profiles primary-hf-lmstudio and secondary-hf-lmstudio with a local OpenAI-compatible server.
