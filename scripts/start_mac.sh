#!/usr/bin/env bash
# Build (if needed) and run the FinAlly Docker container.
# Idempotent: safe to run multiple times. Pass --build to force a rebuild.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

IMAGE_NAME="finally"
CONTAINER_NAME="finally"
PORT="8000"
VOLUME_NAME="finally-data"
FORCE_BUILD=false

for arg in "$@"; do
  case "$arg" in
    --build) FORCE_BUILD=true ;;
  esac
done

if [ ! -f .env ]; then
  echo "No .env file found. Copying .env.example to .env — add your OPENROUTER_API_KEY before using AI chat."
  cp .env.example .env
fi

if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1 || [ "$FORCE_BUILD" = true ]; then
  echo "Building Docker image '$IMAGE_NAME'..."
  docker build -t "$IMAGE_NAME" .
else
  echo "Docker image '$IMAGE_NAME' already exists (use --build to rebuild)."
fi

docker volume create "$VOLUME_NAME" >/dev/null

if [ "$(docker ps -aq -f name="^${CONTAINER_NAME}\$")" ]; then
  echo "Removing existing container '$CONTAINER_NAME'..."
  docker rm -f "$CONTAINER_NAME" >/dev/null
fi

echo "Starting FinAlly..."
docker run -d \
  --name "$CONTAINER_NAME" \
  -v "$VOLUME_NAME:/app/db" \
  -p "$PORT:8000" \
  --env-file .env \
  "$IMAGE_NAME" >/dev/null

URL="http://localhost:$PORT"
echo "FinAlly is running at $URL"

if command -v open >/dev/null 2>&1; then
  open "$URL" || true
fi
