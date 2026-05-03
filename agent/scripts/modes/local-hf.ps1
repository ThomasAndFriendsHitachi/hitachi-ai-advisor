param(
    [string]$Project = "ssms",
    [string]$Semver = "v0.1.0",
    [string]$ModelProfilesFile = "models/model_profiles.json",
    [string]$PrimaryProfile = "primary-hf-meta-llama31-8b",
    [string]$SecondaryProfile = "secondary-hf-mistral7b",
    [string]$RetrievalStrategy = "auto",
    [string]$EmbeddingModel = "",
    [string]$EmbeddingModelDir = "models/embedding_models/bge-m3",
    [string]$EmbeddingDevice = "cpu"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\\.venv\\Scripts\\python.exe")) {
    throw "Missing .venv Python interpreter. Create the venv first."
}

& .\.venv\Scripts\python.exe main.py `
    --project $Project `
    --semver $Semver `
    --model-profiles-file $ModelProfilesFile `
    --primary-profile $PrimaryProfile `
    --secondary-profile $SecondaryProfile `
    --retrieval-strategy $RetrievalStrategy `
    --embedding-model $EmbeddingModel `
    --embedding-model-dir $EmbeddingModelDir `
    --embedding-device $EmbeddingDevice
