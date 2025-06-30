# Stage 1: Builder
# Install all dependencies, including build-time dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

# Install system dependencies needed for Playwright and application
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libglib2.0-0 libgtk-3-0 libpango-1.0-0 libcairo2 \
    libatspi2.0-0 libx11-6 libxcb1 libxext6 libxcursor1 libxi6 libxtst6 \
    libpangocairo-1.0-0 libxss1 \
    curl ca-certificates fonts-liberation libappindicator3-1 \
    lsb-release xdg-utils git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt requirements.txt
COPY requirements-dev.txt requirements-dev.txt
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Install the project in editable mode to make its modules available
COPY . .
RUN pip install -e .

# Install Playwright and its browser dependencies
RUN playwright install --with-deps chromium


# Stage 2: Final Image
# A slim image with only the necessary artifacts
FROM python:3.11-slim AS final

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy Playwright browser files and their system dependencies
COPY --from=builder /opt/playwright /opt/playwright
COPY --from=builder /usr/lib/x86_64-linux-gnu /usr/lib/x86_64-linux-gnu
COPY --from=builder /lib/x86_64-linux-gnu /lib/x86_64-linux-gnu

# Set the path to use the virtual environment
ENV PATH="/opt/venv/bin:$PATH"
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/lib/x86_64-linux-gnu

# Copy source code and test configuration
COPY ./src /app/src
COPY ./tests /app/tests
COPY ./pytest.ini /app/pytest.ini
COPY ./requirements.txt /app/requirements.txt
COPY ./requirements-dev.txt /app/requirements-dev.txt
COPY ./ruff.toml /app/ruff.toml
COPY ./pyproject.toml /app/pyproject.toml

# Run the script when the container starts
CMD ["python", "src/main.py"] 
