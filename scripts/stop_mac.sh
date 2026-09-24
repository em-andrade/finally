#!/usr/bin/env bash
# Stop and remove the FinAlly container. Does NOT remove the data volume.
# Idempotent: safe to run multiple times.
set -euo pipefail

CONTAINER_NAME="finally"

if [ "$(docker ps -aq -f name="^${CONTAINER_NAME}\$")" ]; then
  echo "Stopping FinAlly..."
  docker rm -f "$CONTAINER_NAME" >/dev/null
  echo "Stopped and removed container '$CONTAINER_NAME'. Data volume preserved."
else
  echo "No running FinAlly container found."
fi
