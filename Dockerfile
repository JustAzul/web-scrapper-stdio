# Use Python 3.11 slim as the base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables to prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libglib2.0-0 libgtk-3-0 libpango-1.0-0 libcairo2 libasound2 \
    libatspi2.0-0 libx11-6 libxcb1 libxext6 libxcursor1 libxi6 libxtst6 \
    libpangocairo-1.0-0 libxss1 \
    wget gnupg curl ca-certificates fonts-liberation libappindicator3-1 \
    lsb-release xdg-utils git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy source code
COPY ./src /app/src

# Run the script when the container starts
CMD ["python", "src/mcp_server.py"] 