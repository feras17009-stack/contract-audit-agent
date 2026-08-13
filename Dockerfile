# Production Dockerfile for Contract Audit Agent API Service
FROM python:3.11-slim

# Install system dependencies (curl for healthchecks, tesseract for OCR fallback)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirement files and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and default data files
COPY src/ ./src/
COPY data/ ./data/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV API_HOST=0.0.0.0
ENV API_PORT=8080

EXPOSE 8080

# Run FastAPI app with uvicorn server
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
