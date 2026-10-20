# syntax=docker/dockerfile:1

# ---- build stage: compile/install dependencies into a virtualenv ----
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
# Copy only the requirement files first so this layer is cached until dependencies change
COPY requirements.txt requirements-chroma.txt ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install -r requirements.txt \
    && /opt/venv/bin/pip install --no-deps -r requirements-chroma.txt

# ---- runtime stage: no compilers, no pip cache, non-root user ----
FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 app
WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app app ./app
RUN mkdir -p data logs && chown app:app data logs

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=2)"

# One worker per container: scale by adding replicas, not processes.
# Secrets (OPENAI_API_KEY, JWT_SECRET) come from the environment at runtime, never the image.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--timeout-graceful-shutdown", "20"]
