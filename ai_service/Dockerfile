# Multi-stage build for SchemaSculpt AI Service
# Stage 1: Base image with dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime image
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 fastapi && chown -R fastapi:fastapi /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/fastapi/.local

# Copy application code
COPY --chown=fastapi:fastapi . .

# Create data directory for RAG vector store
RUN mkdir -p data/vector_store && chown -R fastapi:fastapi data

USER fastapi

# Add local Python packages to PATH
ENV PATH=/home/fastapi/.local/bin:$PATH

# Expose AI Service port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
