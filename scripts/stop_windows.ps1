# Stop and remove the FinAlly container. Does NOT remove the data volume.
# Idempotent: safe to run multiple times.
$ErrorActionPreference = "Stop"

$ContainerName = "finally"

$existing = docker ps -aq -f "name=^$ContainerName`$"
if ($existing) {
    Write-Host "Stopping FinAlly..."
    docker rm -f $ContainerName | Out-Null
    Write-Host "Stopped and removed container '$ContainerName'. Data volume preserved."
} else {
    Write-Host "No running FinAlly container found."
}
