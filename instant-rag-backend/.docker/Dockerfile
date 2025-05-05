FROM ubuntu:24.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    postgresql-client \
    libpq-dev \
    tesseract-ocr \
    poppler-utils \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for uploads and data if they don't exist
RUN mkdir -p uploads data/emails logs

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["python3", "run.py"]

# Default command
CMD ["--host", "0.0.0.0", "--port", "8000"]
