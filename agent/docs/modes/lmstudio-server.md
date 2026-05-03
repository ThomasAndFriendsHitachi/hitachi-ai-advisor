# Mode: LM Studio Server (OpenAI-Compatible)

Best runtime

- Server runtime on a local workstation.
- Good when direct GGUF runtime inside Python is unstable.
- Works with local models served by LM Studio.

Python and system requirements

- Python 3.12.x
- LM Studio installed
- LM Studio OpenAI-compatible server enabled (default <http://localhost:1234/v1>)

Install requirements

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

LM Studio requirements

- Load a Meta model for primary role.
- Load a Mistral model for secondary role.
- Start the local server and keep it running.

Run

```powershell
powershell -ExecutionPolicy Bypass -File scripts/modes/lmstudio.ps1 -Project ssms -Semver v0.1.0
```

Expected run manifest signals

- model_status.primary_provider = openai_compatible
- model_status.secondary_provider = openai_compatible
- model_status.primary_available = true
- model_status.secondary_available = true

If it fails

- Check that <http://localhost:1234/v1/models> is reachable.
- Confirm model names in models/model_profiles.json match the loaded LM Studio models.
