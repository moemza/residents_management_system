# syntax=docker/dockerfile:1

# ── Frontend build ────────────────────────────────────────────────────────────
FROM node:22-slim AS frontend-build

WORKDIR /frontend

# package-lock.json is tracked so the image installs the reviewed dependency
# graph exactly. npm ci fails if the lockfile and package.json disagree.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ── Runtime ───────────────────────────────────────────────────────────────────
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RESIDENTS_DB_PATH=/data/residents.db \
    RESIDENTS_BACKUP_DIR=/data/backups \
    RESIDENTS_FRONTEND_DIR=/app/frontend/dist

WORKDIR /app

RUN groupadd --system app \
    && useradd --system --gid app --create-home app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
COPY --from=frontend-build /frontend/dist ./frontend/dist

RUN mkdir -p /data \
    && chown -R app:app /app /data

USER app

EXPOSE 8000
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
