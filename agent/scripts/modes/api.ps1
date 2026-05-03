param(
    [string]$Project = "ssms",
    [string]$Semver = "v0.1.0",
    [string]$PrimaryModel = "gpt-4.1-mini",
    [string]$SecondaryModel = "claude-3-5-sonnet-20241022"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\\.venv\\Scripts\\python.exe")) {
    throw "Missing .venv Python interpreter. Create the venv first."
}

if ([string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY)) {
    throw "OPENAI_API_KEY is not set in this shell."
}

if ([string]::IsNullOrWhiteSpace($env:ANTHROPIC_API_KEY)) {
    throw "ANTHROPIC_API_KEY is not set in this shell."
}

& .\.venv\Scripts\python.exe main.py `
    --project $Project `
    --semver $Semver `
    --primary-provider openai `
    --secondary-provider anthropic `
    --primary-model $PrimaryModel `
    --secondary-model $SecondaryModel
