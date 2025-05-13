FROM python:3.10.4-slim-buster

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    python3-pip \
    ffmpeg \
    wget \
    bash \
    neofetch \
    software-properties-common \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -U wheel
RUN pip3 install --no-cache-dir -U -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p downloads

# Expose port for web server
EXPOSE 5000

# Environment variables will be set in Render dashboard

# Start both the Flask web server and the Telegram bot
CMD python3 app.py & python3 main.py
