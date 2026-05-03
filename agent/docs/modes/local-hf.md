# Mode: Local HF (Direct GGUF)

Best runtime

- Local runtime on one machine.
- Works fully offline after models are downloaded.
- Recommended when you want no server dependency.

Python and system requirements

- Python 3.12.x
- Windows PowerShell
- Enough RAM for loaded GGUF models

Install requirements

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-hf-local.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-hf-gguf.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-hf-transformers.txt
```

Download models

```powershell
.\.venv\Scripts\python.exe scripts/download_hf_models.py
.\.venv\Scripts\python.exe scripts/download_hf_models.py --with-embedding
```

Run

```powershell
powershell -ExecutionPolicy Bypass -File scripts/modes/local-hf.ps1 -Project ssms -Semver v0.1.0

# Optional semantic retrieval switch:
.\.venv\Scripts\python.exe main.py --primary-profile primary-hf-meta-llama31-8b --secondary-profile secondary-hf-mistral7b --retrieval-strategy semantic --embedding-model models/embedding_models/bge-m3 --embedding-model-dir models/embedding_models/bge-m3
```

Expected run manifest signals

- model_status.primary_provider = hf_local
- model_status.secondary_provider = hf_local
- model_status.primary_available = true
- model_status.secondary_available = true
- degraded_mode = false

If it fails

- If llama-cpp build/runtime fails, switch to LM Studio mode.
