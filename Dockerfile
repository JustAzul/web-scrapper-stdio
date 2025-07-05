# ---- Builder Stage ----
# Installs all dependencies, including playwright browsers
FROM python:3.11-slim AS builder

# Set env vars
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright browser dependencies
    libnss3 libnspr4 libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libglib2.0-0 libgtk-3-0 libpango-1.0-0 libcairo2 \
    libatspi2.0-0 libx11-6 libxcb1 libxext6 libxcursor1 libxi6 libxtst6 \
    # Other dependencies
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create and activate virtual environment
RUN python -m venv /opt/venv

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright browsers
RUN playwright install --with-deps

# ---- Final Stage ----
# The actual production image
FROM python:3.11-slim AS final

WORKDIR /app

# Set env vars
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Set the python path to ensure modules are found correctly from the root
ENV PYTHONPATH /app

# Install runtime dependencies for Playwright (same as builder stage)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright browser dependencies
    libnss3 libnspr4 libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libglib2.0-0 libgtk-3-0 libpango-1.0-0 libcairo2 \
    libatspi2.0-0 libx11-6 libxcb1 libxext6 libxcursor1 libxi6 libxtst6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy playwright browser binaries from builder
# Note: The location may vary based on playwright version, /root/.cache/ms-playwright is common
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Copy application source
COPY src/ ./src/

# Expose the port (optional, for reference)
EXPOSE 8000

# Default command to run the MCP server
CMD ["python", "src/mcp_server.py"] 
