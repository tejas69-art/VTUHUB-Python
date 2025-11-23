# Dockerfile.cpu
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# system deps for pillow / general image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
    libjpeg-dev libpng-dev && rm -rf /var/lib/apt/lists/*

# copy requirements then install (better layer caching)
# Using requirements-docker.txt which excludes Windows-only packages (pywinpty) and Jupyter
COPY requirements-docker.txt /app/requirements-docker.txt

# Upgrade pip first
RUN pip install --upgrade pip setuptools wheel

# Install all requirements
# Note: On Linux systems, PyPI torch is CPU-only by default (no CUDA)
# This is the most reliable method for deployment platforms
RUN pip install --no-cache-dir -r /app/requirements-docker.txt

# copy source
COPY . /app

# expose
EXPOSE 8000

# run uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
