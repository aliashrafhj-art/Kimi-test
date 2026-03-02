# Video Automation Tool - Dockerfile
# Multi-stage build for optimization

FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fontconfig \
    wget \
    curl \
    git \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Bengali fonts
RUN mkdir -p /usr/share/fonts/bengali && \
    cd /usr/share/fonts/bengali && \
    wget -q "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansBengali/NotoSansBengali-Regular.ttf" && \
    wget -q "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansBengali/NotoSansBengali-Bold.ttf" && \
    fc-cache -fv

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY fonts/ ./fonts/

# Create necessary directories
RUN mkdir -p /tmp/video-automation/downloads /app/fonts

# Set environment variables
ENV PYTHONPATH=/app
ENV TEMP_DIR=/tmp/video-automation
ENV DOWNLOAD_DIR=/tmp/video-automation/downloads
ENV FONT_DIR=/app/fonts
ENV PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start command
CMD ["python", "backend/main.py"]