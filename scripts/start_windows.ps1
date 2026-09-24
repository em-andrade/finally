# Build (if needed) and run the FinAlly Docker container.
# Idempotent: safe to run multiple times. Pass -Build to force a rebuild.
param(
    [switch]$Build
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
Set-Location $RootDir

$ImageName = "finally"
$ContainerName = "finally"
$Port = "8000"
$VolumeName = "finally-data"

if (-not (Test-Path ".env")) {
    Write-Host "No .env file found. Copying .env.example to .env - add your OPENROUTER_API_KEY before using AI chat."
    Copy-Item ".env.example" ".env"
}

$imageExists = docker image inspect $ImageName 2>$null
if (-not $imageExists -or $Build) {
    Write-Host "Building Docker image '$ImageName'..."
    docker build -t $ImageName .
} else {
    Write-Host "Docker image '$ImageName' already exists (use -Build to rebuild)."
}

docker volume create $VolumeName | Out-Null

$existing = docker ps -aq -f "name=^$ContainerName`$"
if ($existing) {
    Write-Host "Removing existing container '$ContainerName'..."
    docker rm -f $ContainerName | Out-Null
}

Write-Host "Starting FinAlly..."
docker run -d `
    --name $ContainerName `
    -v "${VolumeName}:/app/db" `
    -p "${Port}:8000" `
    --env-file .env `
    $ImageName | Out-Null

$Url = "http://localhost:$Port"
Write-Host "FinAlly is running at $Url"

try {
    Start-Process $Url
} catch {
    # Browser launch is best-effort
}
