# Mode: Container Runtime (Docker)

Best runtime

- Container runtime for deployment and reproducible builds.
- Best for CI/CD and server deployments.
- Default compose profile is LM Studio-style OpenAI-compatible endpoint on the host.

Requirements

- Docker Desktop (or Docker Engine + Compose)
- If using host model server: LM Studio or compatible endpoint reachable from container

Build and run

```powershell
docker build -t hitachiai-pipeline:latest .
docker compose up --build
```

Default compose behavior

- Uses profile pair: primary-hf-lmstudio + secondary-hf-lmstudio
- Uses host endpoint: <http://host.docker.internal:1234/v1>
- Mounts inputs, outputs, models, templates into container

Run via script

```powershell
powershell -ExecutionPolicy Bypass -File scripts/modes/container.ps1
```

Direct GGUF in container

- Not the default path.
- Requires llama-cpp-python toolchain support inside image.
- Prefer host model server for simpler container operations.
