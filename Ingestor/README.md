# Ingestor

Multi-format data ingestion service that converts files into a single structured JSON payload.

Primary entrypoint: Ingestor.py

## Table of Contents

1. Overview
2. Code Structure
3. Supported File Types
4. Output JSON Schema
5. Prerequisites
6. Local Setup
7. Docker Setup in This Monorepo
8. CLI Usage
9. Redis Worker Usage
10. Redis Message Contracts
11. Worker Failure and Retry Behavior
12. Environment Variables
13. End-to-End Redis Test
14. Testing and Quality Checks
15. Troubleshooting
16. Integration Notes for This Repository

## 1) Overview

Ingestor can run in two modes:

- CLI mode: ingest a local file or directory and write one JSON output file.
- Worker mode: consume ingestion jobs from a Redis list and publish results to another Redis list.

Core capabilities:

- Recursively ingest directories.
- Normalize multi-format data into one JSON payload.
- Parse text sections and label-based structured sections.
- Extract tables from supported formats.

## 2) Code Structure

- Ingestor.py: top-level entrypoint. Uses CLI mode by default, worker mode with --worker.
- ingestor_core/cli.py: argument parsing and JSON output writing for CLI mode.
- ingestor_core/worker.py: Redis queue worker, retries, DLQ, processing queue recovery.
- ingestor_core/engine/: ingestion orchestration and extractor registry.
- ingestor_core/extractors/: format-specific extraction logic.
- ingestor_core/parsers/: section, subsection, and table parsing.
- ingestor_core/models.py: dataclasses and ingestion options.
- ingestor_core/utils.py: shared text and helper utilities.

## 3) Supported File Types

### Text and Code Files

- .txt, .md, .rst, .log
- .ini, .cfg, .conf, .yaml, .yml, .toml, .env
- .xml, .html, .htm, .sql
- .sh, .bash, .zsh, .bat, .cmd, .ps1
- .py, .ipynb, .js, .jsx, .ts, .tsx, .java, .c, .h, .cpp, .hpp, .cs, .go, .rs, .php, .rb, .swift, .kt, .scala, .r, .m, .pl, .lua
- Unknown extensions are processed with text best-effort fallback.

### Office and Document Files

- .docx: heading-aware section parsing and native table extraction.
- .doc: Word COM path on Windows (best quality), fallback via textract.
- .pdf: section heuristics and table extraction via pdfplumber.

### Structured Data Files

- .csv: extracted as arrays of row objects.
- .xls and .xlsx: extracted sheet-by-sheet as row objects.
- .json: loaded as-is.

## 4) Output JSON Schema

Top-level fields:

- source
- generated_at
- summary
- files

Summary fields:

- total_files
- success_count
- error_count

Per-file fields include:

- file_path
- relative_path
- extension
- size_bytes
- status
- content_type
- content
- sections (optional)
- structured_sections (optional)
- tables (optional)
- metadata
- error (optional)

## 5) Prerequisites

- Python 3.11+ recommended.
- pip
- Redis (for worker mode)

Dependencies from requirements.txt:

- python-docx>=1.1.0
- pypdf>=4.2.0
- pdfplumber>=0.11.0
- pandas>=2.2.0
- openpyxl>=3.1.0
- xlrd>=2.0.1
- redis>=5.0.0
- pywin32>=306 (Windows only)
- textract>=1.6.5 (non-Windows fallback for .doc)

## 6) Local Setup

Run from the Ingestor directory.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 7) Docker Setup in This Monorepo

From the repository root:

```bash
docker compose up -d redis_broker
docker compose --profile ingestor up -d ingestor
```

Notes:

- The ingestor service Docker command runs: python Ingestor.py --worker
- Redis service is named redis_broker in docker-compose.yaml.

## 8) CLI Usage

CLI mode is for ingesting local files and writing one output JSON file.

### Required arguments

- --input: input file or folder path
- --output: output JSON file path

### Optional arguments

- --pretty: pretty JSON output (default behavior)
- --compact: minified JSON output
- --aggressive-pdf-cleanup: stronger PDF table text normalization

### Important rules

- Do not pass --pretty and --compact together.
- If input path does not exist, command exits with status code 1.

### CLI examples

```powershell
python Ingestor.py --input "file.pdf" --output "file.json"
python Ingestor.py --input "./data" --output "./ingested.json"
python Ingestor.py --input "file.pdf" --output "file.compact.json" --compact
python Ingestor.py --input "file.pdf" --output "file.json" --aggressive-pdf-cleanup
```

## 9) Redis Worker Usage

Worker mode is enabled with --worker and reads jobs continuously from Redis.

### Start worker locally

```powershell
$env:REDIS_URL="redis://localhost:6379/0"
$env:INGESTOR_INPUT_QUEUE="queue:ai_tasks"
$env:INGESTOR_OUTPUT_QUEUE="queue:ingestor_results"
$env:INGESTOR_DLQ_QUEUE="queue:ingestor_dlq"
python Ingestor.py --worker
```

### Worker flags

- --max-jobs N: process at most N jobs then exit. 0 means infinite loop.
- --aggressive-pdf-cleanup: same cleanup behavior as CLI mode.

Example:

```powershell
python Ingestor.py --worker --max-jobs 10
```

## 10) Redis Message Contracts

### Input queue message shape

Minimum valid envelope:

```json
{
  "id": "job-123",
  "source": "github_webhook",
  "payload": {
    "project_name": "org/repo",
    "files": [
      {
        "path": "src/main.py",
        "content": "print('hello')",
        "encoding": "utf-8"
      },
      {
        "path": "assets/blob.bin",
        "content_base64": "QUJDRA=="
      }
    ]
  }
}
```

Validation rules:

- payload.files must be a non-empty list.
- Each files item must be an object.
- Each file must include path or name.
- Each file must include content (text) or content_base64 (binary).
- Absolute paths are rejected.
- Path traversal using .. is rejected.

### Output queue message shape

On success, worker pushes:

- id
- source
- type (ingestion_result)
- timestamp
- status (completed)
- project_name
- summary
- ingestion (full ingestion payload)
- attempt

## 11) Worker Failure and Retry Behavior

- Worker reserves jobs from input queue into processing queue using BRPOPLPUSH.
- On success, result is pushed to output queue.
- On failure, worker increments _attempt and adds _last_error and _last_failed_at.
- If _attempt is less than or equal to INGESTOR_MAX_RETRIES, message is re-queued to input queue.
- If retries are exceeded, message is pushed to DLQ queue.
- On startup, if INGESTOR_RECOVER_INFLIGHT is true, worker moves items from processing queue back to input queue.

## 12) Environment Variables

### Worker variables

- REDIS_URL: default redis://localhost:6379/0
- INGESTOR_INPUT_QUEUE: fallback to REDIS_QUEUE_NAME, default queue:ai_tasks
- INGESTOR_PROCESSING_QUEUE: default <input_queue>:processing
- INGESTOR_OUTPUT_QUEUE: default queue:ingestor_results
- INGESTOR_DLQ_QUEUE: default queue:ingestor_dlq
- INGESTOR_POP_TIMEOUT: default 5
- INGESTOR_MAX_RETRIES: default 3
- INGESTOR_RECOVER_INFLIGHT: default true

### CLI-related

- No required environment variables for CLI mode.

## 13) End-to-End Redis Test

Example manual test from repository root using Docker Redis container.

1. Start Redis and ingestor.
2. Push a valid input envelope.
3. Read one output message.

```powershell
# Start services
docker compose up -d redis_broker
docker compose --profile ingestor up -d ingestor

# Push one test job
$job = @'
{
  "id": "job-local-1",
  "source": "manual",
  "payload": {
    "project_name": "demo/project",
    "files": [
      { "path": "docs/readme.txt", "content": "hello from ingestor" }
    ]
  }
}
'@
$job | docker exec -i advisor_redis redis-cli -x LPUSH queue:ai_tasks

# Read output
docker exec -it advisor_redis redis-cli BRPOP queue:ingestor_results 10
```

If a job fails repeatedly, inspect DLQ:

```powershell
docker exec -it advisor_redis redis-cli LRANGE queue:ingestor_dlq 0 -1
```

## 14) Testing and Quality Checks

Install test dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

Run tests:

```powershell
python -m pytest
```

Coverage is configured in pytest.ini with a fail-under target of 100.

## 15) Troubleshooting

- .docx issues: verify python-docx installation.
- .pdf table quality issues: verify pdfplumber installation; compare default vs aggressive cleanup.
- .doc issues on Windows: ensure Microsoft Word and pywin32 are available.
- .xls/.xlsx issues: verify pandas, openpyxl, and xlrd.
- Worker appears idle: verify input queue name and Redis URL.
- Messages moved to DLQ: check _last_error and _attempt fields in DLQ message.

## 16) Integration Notes for This Repository

- In this monorepo, webhook-manager publishes to REDIS_QUEUE_NAME.
- The mock agent also consumes REDIS_QUEUE_NAME.
- Ingestor input queue defaults to queue:ai_tasks if not overridden.

Recommendation:

- Use a dedicated ingestion queue for INGESTOR_INPUT_QUEUE to avoid contention with non-ingestion consumers.
- Ensure producer payloads for ingestor include payload.files in the required shape.
