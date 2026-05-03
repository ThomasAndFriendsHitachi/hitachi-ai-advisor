param(
    [switch]$Build
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($Build) {
    docker build -t hitachiai-pipeline:latest .
}

docker compose up --build
