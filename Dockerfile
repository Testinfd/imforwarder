FROM python:3.10.4-slim-buster

# Install dependencies - optimized to reduce layer size
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ffmpeg \
    wget \
    bash \
    procps \
    software-properties-common \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -U wheel \
    && pip3 install --no-cache-dir -U -r requirements.txt \
    && pip3 cache purge

# Create log directory
RUN mkdir -p logs

# Copy application code
COPY . .

# Make the start script executable
RUN chmod +x start.sh

# Create a healthcheck for the container
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Expose port for web server
EXPOSE 5000

# Set environment validation and startup
CMD bash -c "\
  echo 'Validating environment...' && \
  python -c \"import os, sys; required = ['API_ID', 'API_HASH', 'BOT_TOKEN']; missing = [v for v in required if not os.getenv(v)]; sys.exit(1) if missing else None\" || { echo 'Missing required environment variables!'; exit 1; } && \
  echo 'Environment validation passed. Starting services...' && \
  ./start.sh \
"
