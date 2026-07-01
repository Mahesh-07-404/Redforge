# Production Dockerfile for RedForge Security Engine
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

# Install system dependencies (including tools needed for pentesting scans)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nmap \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY pyproject.toml README.md ./
# Install project using pip directly
RUN pip install --no-cache-dir .

# Copy codebase
COPY src/ ./src/

# Expose API gateway port
EXPOSE 8000

# Set entry point to run unified API Gateway
CMD ["uvicorn", "redforge.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
