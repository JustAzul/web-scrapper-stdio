# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required by Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright browser dependencies
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 \
    libdrm2 libexpat1 libgbm1 libgcc1 libglib2.0-0 libpango-1.0-0 \
    libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxdamage1 libxext6 \
    libxfixes3 libxrandr2 libxrender1 libxtst6 ca-certificates \
    fonts-liberation libappindicator3-1 libasound2 xdg-utils wget \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
# This command downloads the browser binaries into the image
RUN playwright install --with-deps chromium

# Copy the rest of the application code into the container
COPY ./src /app/src

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using uvicorn
# Use --host 0.0.0.0 to make it accessible from outside the container
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"] 