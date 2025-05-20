FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_ENV=production

# Install system dependencies
# Added libpq-dev for PostgreSQL client libraries (pg_config)
# Added python3.11-dev for Python C headers (Python.h)
# Added --no-install-recommends to potentially reduce image size
# Added apt-get clean and rm -rf /var/lib/apt/lists/* for cleanup
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    python3.11-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create user early and set up directory structure
RUN useradd -m -r appuser
RUN mkdir -p /app/logs /app/uploads && \
    chown -R appuser:appuser /app

# Copy requirements first (for better caching)
COPY --chown=appuser:appuser app/requirements.txt .

# Upgrade pip and install Python dependencies
# Note: Running pip install --upgrade pip inside the RUN command that also installs requirements
# ensures that the upgraded pip is used for installing the requirements.
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser ./app ./app
COPY --chown=appuser:appuser main.py .
# If you have other top-level files or directories like 'migrations' that are needed at runtime,
# ensure they are copied as well. For example:
# COPY --chown=appuser:appuser migrations ./migrations

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/v1/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "main:app"]
