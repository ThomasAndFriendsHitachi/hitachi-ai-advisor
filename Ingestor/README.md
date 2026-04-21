# DATA INGESTION

A multi-format ingestion CLI that reads textual documents, office files, spreadsheets, PDFs, and code/text files, then exports a single consolidated JSON payload.

Primary script: `Ingestor.py`

## Architecture

The codebase is now modularized under `ingestor_core/`:

- `models.py`: result and option dataclasses
- `utils.py`: shared text utilities
- `parsers/`: section, subsection, and table parsing logic
- `extractors/`: format-specific extractors (`docx`, `doc`, `pdf`, `csv`, `excel`, `json`, `text`)
- `engine/`: extractor registry + ingestion orchestration
- `cli.py`: CLI argument parsing and output writer

## What It Does

- Ingests a single file or an entire folder recursively.
- Normalizes extracted content into one JSON output.
- Builds `sections` for text-like documents.
- Extracts tables into row objects (`entries`) with column headers.
- Adds `structured_sections` by parsing inline labels like:
  - `What it covers:`
  - `Assigned people:`
  - `Guiding questions:`

## Supported Formats

### Textual / Code / Script (section parsing)

- `.txt`, `.md`, `.rst`, `.log`
- `.ini`, `.cfg`, `.conf`, `.yaml`, `.yml`
- `.xml`, `.html`, `.htm`, `.sql`
- `.sh`, `.bash`, `.zsh`, `.bat`, `.cmd`, `.ps1`
- `.py`, `.js`, `.ts`, `.java`, `.c`, `.cpp`, etc.
- Unknown extensions fallback to text best-effort

### Office / Document

- `.docx`
  - Heading-aware sections
  - Native table extraction
- `.doc`
  - Windows COM path (best quality on Windows + Word)
  - Fallback via textract
  - Table extraction available on COM path
- `.pdf`
  - Header/section heuristics
  - Table extraction via pdfplumber (including text-strategy fallback)

### Structured Data

- `.csv` -> array of row objects
- `.xls`, `.xlsx` -> workbook with sheet-wise row objects
- `.json` -> loaded as-is

## Output Structure

Top-level JSON:

- `source`
- `generated_at`
- `summary`
  - `total_files`
  - `success_count`
  - `error_count`
- `files` (array)

Per-file fields include:

- `file_path`, `relative_path`, `extension`, `size_bytes`
- `status`, `content_type`, `content`
- optional `sections`
- optional `structured_sections`
- optional `tables`
- `metadata`
- optional `error`

## Requirements

From `requirements.txt`:

- `python-docx>=1.1.0`
- `pypdf>=4.2.0`
- `pdfplumber>=0.11.0`
- `pandas>=2.2.0`
- `openpyxl>=3.1.0`
- `xlrd>=2.0.1`
- `pywin32>=306` (Windows only)
- `textract>=1.6.5` (non-Windows fallback for `.doc`)

## Setup

### 1. Create and activate virtual environment (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

## Usage

### Preferred entrypoint

```powershell
python Ingestor.py --input "file.pdf" --output "file.json"
```

### Folder ingestion

```powershell
python Ingestor.py --input "./data" --output "./ingested.json"
```

## CLI Flags

- `--input` (required): input file or directory
- `--output` (required): output JSON path
- `--pretty`: force pretty JSON output
- `--compact`: compact/minified JSON output
- `--aggressive-pdf-cleanup`: stronger PDF table text cleanup (can over-normalize in some files)

Notes:

- Default output is pretty JSON.
- `--pretty` and `--compact` are mutually exclusive.

## Examples

Pretty output (default):

```powershell
python Ingestor.py --input "file.pdf" --output "file.pretty.json"
```

Compact output:

```powershell
python Ingestor.py --input "file.pdf" --output "file.compact.json" --compact
```

Aggressive PDF cleanup:

```powershell
python Ingestor.py --input "file.pdf" --output "file.json" --aggressive-pdf-cleanup
```

## Testing

Install test dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

Run unit tests with coverage:

```powershell
python -m pytest
```


Notes:

- Test inputs are mocked/stubbed and use neutral sample names (for example `file.pdf`, `file.json`).
- Coverage is configured in `pytest.ini` with `--cov-fail-under=100`.

## Practical Guidance

- For LLM pipelines where factual fidelity matters, prefer default mode (no aggressive cleanup).
- For readability-oriented workflows, test `--aggressive-pdf-cleanup` and compare outputs.
- Scanned/image-only PDFs may still require OCR for best results.

## Troubleshooting

- If `.docx` parsing fails, verify `python-docx` is installed.
- If `.pdf` table extraction is weak, ensure `pdfplumber` is installed.
- If `.doc` fails on Windows, ensure Microsoft Word and `pywin32` are available.
- If `.xls/.xlsx` fails, verify `pandas`, `openpyxl`, and `xlrd` installation.
