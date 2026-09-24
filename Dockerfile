# syntax=docker/dockerfile:1

# ---- Stage 1: build the Next.js static export ----
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python backend serving the built frontend ----
FROM python:3.12-slim AS backend

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Install backend dependencies first for better layer caching.
# README.md must be copied too: pyproject.toml declares it as the package
# readme, and hatchling's build validation fails if it's missing.
COPY backend/pyproject.toml backend/uv.lock backend/README.md ./backend/
RUN cd backend && uv sync --frozen --no-dev

# Copy backend source
COPY backend/ ./backend/

# Copy the Next.js static export into the directory the backend serves
COPY --from=frontend-build /app/frontend/out ./backend/static

# Runtime volume mount point for the SQLite database
RUN mkdir -p /app/db

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
