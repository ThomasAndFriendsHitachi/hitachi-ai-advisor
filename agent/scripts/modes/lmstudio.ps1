param(
    [string]$Project = "ssms",
    [string]$Semver = "v0.1.0",
    [string]$BaseUrl = "http://localhost:1234/v1",
    [string]$ApiKey = "local-key",
    [string]$ModelProfilesFile = "models/model_profiles.json",
    [string]$PrimaryProfile = "primary-hf-lmstudio",
    [string]$SecondaryProfile = "secondary-hf-lmstudio"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\\.venv\\Scripts\\python.exe")) {
    throw "Missing .venv Python interpreter. Create the venv first."
}

$env:PRIMARY_LLM_BASE_URL = $BaseUrl
$env:SECONDARY_LLM_BASE_URL = $BaseUrl
$env:PRIMARY_LLM_API_KEY = $ApiKey
$env:SECONDARY_LLM_API_KEY = $ApiKey

& .\.venv\Scripts\python.exe main.py `
    --project $Project `
    --semver $Semver `
    --model-profiles-file $ModelProfilesFile `
    --primary-profile $PrimaryProfile `
    --secondary-profile $SecondaryProfile
