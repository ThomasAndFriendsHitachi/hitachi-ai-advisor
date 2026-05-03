# Mode: Hosted API (OpenAI + Anthropic)

Best runtime

- Server runtime with managed APIs.
- Best for high reliability and no local model hosting.
- Requires internet and paid/free API credentials.

Python and system requirements

- Python 3.12.x
- Internet access

Install requirements

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Credentials

Set environment variables before running:

```powershell
$env:OPENAI_API_KEY = "<openai_key>"
$env:ANTHROPIC_API_KEY = "<anthropic_key>"
```

Run

```powershell
powershell -ExecutionPolicy Bypass -File scripts/modes/api.ps1 -Project ssms -Semver v0.1.0
```

Expected run manifest signals

- model_status.primary_provider = openai
- model_status.secondary_provider = anthropic
- model_status.primary_available = true
- model_status.secondary_available = true

If it fails

- Verify keys are set in the same terminal session.
- Verify account/model access for selected models.
