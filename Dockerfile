# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
# wget and unzip are needed for downloading Chrome/ChromeDriver
# fonts-liberation helps render pages correctly
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    fonts-liberation \
    libu2f-udev \
    curl \
    jq \
    # Add any other system dependencies required by Chrome or your app
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome Stable
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    # Use apt-get install -f to install dependencies if needed
    && apt-get install -y ./google-chrome-stable_current_amd64.deb --fix-missing --no-install-recommends \
    && rm google-chrome-stable_current_amd64.deb

# Install ChromeDriver using the new JSON endpoints
RUN CHROME_MAJOR_VERSION=$(google-chrome --version | cut -d ' ' -f 3 | cut -d '.' -f 1) \
    && echo "Detected Chrome major version: $CHROME_MAJOR_VERSION" \
    # Get the latest stable chromedriver version URL for the major Chrome version
    # Note the careful quoting for jq and shell variable expansion
    && CHROME_DRIVER_URL=$(curl -sS https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json | jq -r --arg major_version "$CHROME_MAJOR_VERSION" '.versions[] | select(.version | startswith($major_version + ".")) | .downloads.chromedriver // [] | .[] | select(.platform=="linux64") | .url' | tail -n 1) \
    && echo "Using ChromeDriver URL: ${CHROME_DRIVER_URL}" \
    # Download and install ChromeDriver
    && wget -q "${CHROME_DRIVER_URL}" -O chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip -d /app/chromedriver_temp \
    # The unzipped structure might be like chromedriver-linux64/chromedriver
    && mv /app/chromedriver_temp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && rm chromedriver_linux64.zip \
    && rm -rf /app/chromedriver_temp \
    && chmod +x /usr/local/bin/chromedriver

# Verify installations
RUN google-chrome --version
RUN chromedriver --version

# Install Python dependencies
COPY requirements.txt .
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source code into the container
COPY ./src /app/src

# Make port 80 available to the world outside this container (if needed for web apps later)
# EXPOSE 80

# Define the command to run the application
ENTRYPOINT ["python", "src/main.py"]
# CMD will be appended to ENTRYPOINT, providing the default URL if needed, or can be overridden
# CMD ["https://example.com"] # Example default URL 