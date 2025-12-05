# Dockerfile.cpu
FROM python:3.12-slim as builder

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libjpeg-dev libpng-dev python3-dev \
    && rm -rf /var/lib/apt/lists/*

# copy requirements then install (better layer caching)
# Using requirements-docker.txt which excludes Windows-only packages (pywinpty) and Jupyter
COPY requirements-docker.txt /app/requirements-docker.txt

# Upgrade pip first
RUN pip install --upgrade pip setuptools wheel

# Install all requirements
# Note: On Linux systems, PyPI torch is CPU-only by default (no CUDA)
# This is the most reliable method for deployment platforms
RUN pip install --no-cache-dir -r /app/requirements-docker.txt

# Final stage - minimal runtime image
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install only minimal runtime dependencies (no build tools)
# OpenCV headless needs libgl1 and libglib2.0-0, others may not be needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Clean up Python cache and unnecessary files
RUN find /usr/local/lib/python3.12/site-packages -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.12/site-packages -type f -name "*.pyc" -delete \
    && find /usr/local/lib/python3.12/site-packages -type f -name "*.pyo" -delete

# copy source
COPY . /app

# expose
EXPOSE 8080

# run uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
