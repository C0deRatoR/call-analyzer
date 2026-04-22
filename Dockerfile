# ============================================================
# Call Analyzer — Production Docker Image
# ============================================================
# Multi-stage build for smaller final image
# Base: Python 3.12 slim | Runtime: gunicorn
# ============================================================

# ---------- Stage 1: Builder ----------
FROM python:3.12-slim AS builder

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Install only build-time dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy and install Python deps in a virtual-env so we can copy it cleanly
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Stage 2: Runtime ----------
FROM python:3.12-slim AS runtime

LABEL maintainer="c0derator"
LABEL org.opencontainers.image.source="https://github.com/C0deRatoR/call-analyzer"
LABEL org.opencontainers.image.description="AI-Powered Audio Intelligence & Mentoring Guidance"

# Runtime system deps: ffmpeg is required by openai-whisper
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual-env from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create a non-root user for security
RUN groupadd -r analyzer && useradd -r -g analyzer -m analyzer

# Set working directory
WORKDIR /app

# Copy application source code
COPY src/ ./src/
COPY web/ ./web/
COPY .env.example ./.env.example

# Create uploads directory with correct permissions
RUN mkdir -p /tmp/uploads && chown -R analyzer:analyzer /app /tmp/uploads

# Switch to non-root user
USER analyzer

# Environment configuration
ENV FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5000

# Expose the application port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Run with gunicorn for production
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--threads", "4", \
     "--timeout", "300", \
     "--chdir", "src", \
     "app:app"]
