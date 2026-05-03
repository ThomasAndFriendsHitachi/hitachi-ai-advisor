# HitachiAI - AI Processing Layer PoC

## Overview

This repository implements the AI Processing Layer and downstream drafting flow from your architecture.

The app starts from already-extracted evidence JSON files in inputs, then:

1. Ingests and normalizes evidence from multiple document types.
2. Infers VDD fields from a DOCX template.
3. Decides whether Retrieval-Augmented Generation (RAG) is needed.
4. Runs primary drafting and secondary verification using configurable providers.
5. Produces VDD output JSON plus reporting artifacts (trace map, issues, risk radar, stakeholder insights, decision journal).
6. Versions outputs with date-project-semver format.

This is an offline-capable PoC with degraded-mode behavior when one or both model providers are unavailable.

## Architecture Diagram

```mermaid
flowchart LR
      A[Extracted JSON Inputs] --> B[Evidence Ingestion and Normalization]
      B --> C[VDD Template Parser]
      B --> D[RAG Decision Engine]
      C --> E[Field Specs]
      D --> F[Retriever Builder]\n(FAISS or Lexical)
      E --> G[Primary LLM Drafting]
      F --> G
      G --> H[Secondary LLM Verification]
      F --> H
      H --> I[Trace Map Composer]
      H --> J[Risk Radar Composer]
      H --> K[Stakeholder Insight Composer]
      I --> L[Decision Journal Composer]
      J --> L
      K --> L
      L --> M[Versioned Artifacts Output]
```

## Model Storage and Offline Assets

Local model workspace is in models:

- models/primary_llm: primary model local files, metadata, or provider-specific notes.
- models/secondary_llm: secondary model local files, metadata, or provider-specific notes.
- models/embedding_models: embedding model local files for semantic retrieval.
- models/docs: setup docs for local/remote provider adapters.
- models/model_profiles.json: active profile catalog used by CLI profile selectors.
- models/model_profiles.example.json: example model profile definitions.

Important: the pipeline does not directly load raw model weights from these folders. These folders are the project-owned location to keep model references, metadata, and docs. Runtime model execution is done through selected providers/endpoints.

Examples of local/offline-capable execution:

- Ollama local server
- OpenAI-compatible local endpoint (for example vLLM, LM Studio OpenAI server)

## Provider and Model Selection (Not Restricted to Two Models)

You can choose providers/models independently for primary and secondary roles.

Supported provider keys:

- openai
- anthropic
- openai_compatible
- ollama
- hf_local

This allows many models beyond ChatGPT/Claude when routed through openai_compatible or ollama.
It also supports direct local Hugging Face execution via hf_local.

### Role split

- Primary LLM: drafts field values.
- Secondary LLM: verifies/fact-checks the draft.

Both roles are configurable from CLI and env vars.

## Project Structure

```text
HitachiAI/
   app/
      __init__.py
      config.py
      models.py
      utils.py
      ingestion.py
      template_parser.py
      rag.py
      prompt_library.py
      llm_clients.py
      composers.py
      pipeline.py
   inputs/
      *.json
   templates/
      vdd_template.docx
   models/
      primary_llm/
      secondary_llm/
      embedding_models/
      docs/
      model_profiles.json
      model_profiles.example.json
      README.md
   docs/
      modes/
         README.md
         local-hf.md
         lmstudio-server.md
         api-cloud.md
         container.md
   outputs/
      <versioned-runs>/
   scripts/
      download_hf_models.py
      modes/
         local-hf.ps1
         lmstudio.ps1
         api.ps1
         container.ps1
   Dockerfile
   docker-compose.yml
   .dockerignore
   main.py
   .env.example
   requirements.txt
   README.md
```

## Runtime Modes (Choose One)

Pick one mode first, then follow only that mode.

| Mode | Best runtime | Python | Requirements files | Script |
| --- | --- | --- | --- | --- |
| Local HF (direct GGUF) | Local runtime on one machine, fully offline after model download | 3.12.x | requirements.txt + requirements-hf-local.txt + requirements-hf-gguf.txt | scripts/modes/local-hf.ps1 |
| LM Studio server | Local server runtime (OpenAI-compatible endpoint) | 3.12.x | requirements.txt | scripts/modes/lmstudio.ps1 |
| Hosted API | Server runtime with managed APIs | 3.12.x | requirements.txt | scripts/modes/api.ps1 |
| Container | Container runtime (deployment and CI/CD) | Docker image includes Python 3.12 | Image installs requirements-hf-local.txt | scripts/modes/container.ps1 |

Mode guides:

- docs/modes/README.md
- docs/modes/local-hf.md
- docs/modes/lmstudio-server.md
- docs/modes/api-cloud.md
- docs/modes/container.md

## Common One-Time Setup

Create environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Use the mode-specific requirements after this step.

## Mode A: Local HF (Direct GGUF)

Use this when you want true local offline inference in Python.

Install:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-hf-local.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-hf-gguf.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-hf-transformers.txt
```

Download models:

```powershell
.\.venv\Scripts\python.exe scripts/download_hf_models.py
.\.venv\Scripts\python.exe scripts/download_hf_models.py --with-embedding
```

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/modes/local-hf.ps1 -Project ssms -Semver v0.1.0

# Optional semantic retrieval mode
.\.venv\Scripts\python.exe main.py --primary-profile primary-hf-meta-llama31-8b --secondary-profile secondary-hf-mistral7b --retrieval-strategy semantic --embedding-model models/embedding_models/bge-m3 --embedding-model-dir models/embedding_models/bge-m3
```

Guide: docs/modes/local-hf.md

## Mode B: LM Studio Server (OpenAI-Compatible)

Use this when you want local models served by LM Studio.

Install:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Prerequisite:

- Start LM Studio server.
- Ensure endpoint is reachable at <http://localhost:1234/v1>.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/modes/lmstudio.ps1 -Project ssms -Semver v0.1.0
```

Guide: docs/modes/lmstudio-server.md

## Mode C: Hosted API (OpenAI + Anthropic)

Use this when you want managed cloud models.

Install:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Set keys:

```powershell
$env:OPENAI_API_KEY = "<openai_key>"
$env:ANTHROPIC_API_KEY = "<anthropic_key>"
```

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/modes/api.ps1 -Project ssms -Semver v0.1.0
```

Guide: docs/modes/api-cloud.md

## Mode D: Container Runtime (Docker)

Use this for deployment/CI and reproducible runtime.

Build and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/modes/container.ps1
```

or directly:

```powershell
docker build -t hitachiai-pipeline:latest .
docker compose up --build
```

Default compose profile uses LM Studio-style openai_compatible endpoint on host:

- PRIMARY_PROFILE=primary-hf-lmstudio
- SECONDARY_PROFILE=secondary-hf-lmstudio
- PRIMARY_LLM_BASE_URL=<http://host.docker.internal:1234/v1>
- SECONDARY_LLM_BASE_URL=<http://host.docker.internal:1234/v1>

Guide: docs/modes/container.md

## Mode Validation

After each run, verify outputs/{version}/run_manifest.json:

- For Local HF: provider should be hf_local and available=true for both roles.
- For LM Studio: provider should be openai_compatible and available=true for both roles.
- For Hosted API: provider should be openai and anthropic with available=true.

If available=false, that mode runtime is not reachable or not configured.

## Configuration Summary

Main environment variables:

- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- PRIMARY_LLM_API_KEY
- SECONDARY_LLM_API_KEY
- PRIMARY_LLM_BASE_URL
- SECONDARY_LLM_BASE_URL
- OLLAMA_HOST
- RAG_RETRIEVAL_STRATEGY
- RAG_EMBEDDING_MODEL
- RAG_EMBEDDING_DEVICE
- PRIMARY_PROFILE
- SECONDARY_PROFILE
- MODEL_PROFILES_FILE

Model profile catalog:

- models/model_profiles.json

CLI precedence rule:

- Explicit CLI flags override profile values.

## Inputs Contract

The pipeline expects extraction outputs similar to current inputs files.

Each file should contain a root object with a files array. Each element may include:

- relative_path
- extension
- status
- content_type
- content (string or structured object)
- sections (object)
- tables (array)
- metadata (object)

The ingestion layer flattens content, sections, and tables into normalized text + metadata.

## Outputs Contract

Each run creates a versioned output folder:

- outputs/YYYY-MM-DD-project-semver
- If already exists, suffix is added: -r02, -r03, ...

Generated artifacts:

1. vdd.json
2. tracemap.json
3. generation_issues.json
4. risk_radar.json
5. stakeholder_insights.json
6. decision_journal.json
7. primary_raw.json
8. secondary_raw.json
9. run_manifest.json

run_manifest.json includes selected providers/models and availability status.

## Decision Logic Highlights

### RAG decision

RAG is selected when context pressure/noise is high (token estimate, document count, noisy large HTML/XML, or broad field count).

### LLM-only execution behavior

If a provider call fails or returns invalid JSON, the pipeline records a clear error in raw artifacts and generation issues without switching to non-LLM fallback generation.

### Secondary verification

Secondary role validates draft values and raises missing/low-confidence concerns.

## Troubleshooting

### Online mode not used

- Verify provider key/env variables are set in the active shell.
- Check run_manifest.json model_status section.

### FAISS fallback warning

- Install numpy and faiss-cpu.
- Lexical fallback remains available automatically.

### Semantic retriever fallback warning

- Install requirements-hf-transformers.txt.
- Verify models/embedding_models/bge-m3 exists, or set --embedding-model to a valid HF repo id/path.
- The pipeline will automatically fallback to hashed_faiss or lexical strategy if semantic loading fails.

### Many fields marked missing

- Add explicit placeholders in DOCX template (for example {{FIELD_NAME}}).
- Improve upstream extraction quality/coverage.

### Provider endpoint issues

- For openai_compatible, verify base URL includes /v1.
- For ollama, verify host and model availability on local server.

## Security Notes

- Keep API keys in environment variables.
- Do not commit sensitive generated outputs.
- Keep provider-specific credentials out of model_profiles.example.json copies.

## Quick Start Checklist

1. Put extraction JSON files in inputs.
2. Ensure templates/vdd_template.docx exists.
3. Ensure models/primary_llm and models/secondary_llm contain your local model metadata/docs if needed.
4. Install dependencies.
5. Run main.py with your provider/model choices.
6. Review outputs/VERSION_KEY/run_manifest.json and decision_journal.json first.
