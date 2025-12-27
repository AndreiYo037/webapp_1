# Multi-stage build to reduce final image size
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# Use --no-cache-dir and pip cache cleanup to reduce size
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# Final stage - minimal runtime image
FROM python:3.12-slim

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # For PyMuPDF
    libmupdf-dev \
    # For pdf2image (poppler)
    poppler-utils \
    # For pytesseract (tesseract-ocr)
    tesseract-ocr \
    # For opencv-python-headless (no GUI dependencies needed)
    libglib2.0-0 \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Collect static files (if using Django)
RUN python manage.py collectstatic --noinput || true

# Expose port (PORT will be set by Railway at runtime)
EXPOSE ${PORT:-8000}

# Note: Railway uses Nixpacks, not Dockerfile, but if Docker is used, ensure PORT is used
# The start.sh script in the repo will be used, which handles PORT correctly

# Run startup script (which runs migrations then starts gunicorn)
CMD ["/app/start.sh"]

