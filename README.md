# Web Scraper Service (Stdin/Stdout, Markdown Output)

## Usage (Stdin/Stdout)

Run the web scraper as a Docker container that reads JSON lines from stdin and outputs results as JSON lines to stdout:

```
echo '{"url": "https://example.com"}' | docker run -i --rm ghcr.io/justazul/web-scrapper-stdio:latest
```

- Each input line must be a JSON object with a `url` field.
- The output is a JSON object per line, with:
  - `extracted_text` (Markdown)
  - `status` ("success", "error_fetching", etc.)
  - `error_message` (string or null)
  - `final_url` (string)

## Usage (CLI Tool)

For direct use without the MCP server, you can use the CLI tool:

```bash
# Run in Docker
docker run -i --rm ghcr.io/justazul/web-scrapper-stdio:latest python src/cli.py https://example.com

# Or with multiple URLs
docker run -i --rm ghcr.io/justazul/web-scrapper-stdio:latest python src/cli.py https://example.com https://wikipedia.org

# Save output to a file
docker run -i --rm -v $(pwd):/app/output ghcr.io/justazul/web-scrapper-stdio:latest python src/cli.py https://example.com -o /app/output/results.json -p

# Custom timeout and element removal
docker run -i --rm ghcr.io/justazul/web-scrapper-stdio:latest python src/cli.py https://example.com -t 60 -r div.ads section.comments
```

CLI options:
- `urls`: One or more URLs to scrape (required)
- `-o, --output`: Output file path for results (JSON format)
- `-p, --pretty`: Pretty print JSON output
- `-v, --verbose`: Enable verbose logging
- `-t, --timeout`: Custom timeout in seconds
- `-r, --remove`: Additional HTML elements to remove (e.g., 'div.ads' 'section.comments')

## Usage (MCP Server)

This web scraper can also be used as an MCP (Model Context Protocol) tool, allowing it to be used by AI models directly.

### Tool Name: scrape_web

**Parameters:**
- `url` (string, required): The URL to scrape
- `max_length` (integer, optional): Maximum length of returned content (default: 5000)
- `timeout_seconds` (integer, optional): Timeout in seconds for the page load (default: 30)
- `user_agent` (string, optional): Custom User-Agent string
- `wait_for_network_idle` (boolean, optional): Whether to wait for network activity to settle (default: true)

**Returns:**
- Markdown formatted content extracted from the webpage

### Example:

```json
{
  "name": "scrape_web",
  "arguments": {
    "url": "https://example.com",
    "max_length": 10000
  }
}
```

### Prompt Name: scrape

**Parameters:**
- `url` (string, required): The URL to scrape

**Returns:**
- Markdown formatted content extracted from the webpage

**Note:**
- Output is always Markdown for easy downstream use.
- The scraper does not check robots.txt and will attempt to fetch any URL provided.
- No REST API or MCP server is included; this is a pure stdio tool.
- All domains with available RSS feeds are now included in the test suite (fortune.com, techcrunch.com, wired.com, engadget.com, medium.com, dev.to, tomsguide.com, xda-developers.com, dmnews.com).
- Test cases use domain URLs for clear output.
- The scraper always extracts the full <body> content of web pages, applying only essential noise removal (removing script, style, nav, footer, aside, header, and similar non-content tags). Domain-specific selectors are no longer used. The scraper detects and handles Cloudflare challenge screens, returning a specific error status.

---

# Project Overview

This project is a Python-based web scraper that extracts primary text content from web pages, outputting Markdown via a simple stdio interface. It is designed for use in pipelines, containers, and AI toolchains.

## Technology Stack
- Python 3.9+
- Playwright
- BeautifulSoup
- Markdownify
- Docker
- MCP (Model Context Protocol)

## Development
- Core scraping logic: `src/scraper.py`
- Stdio entrypoint: `src/stdio_server.py`
- MCP server entrypoint: `src/mcp_server.py`
- CLI tool: `src/cli.py`
- Dockerfile: runs the MCP server by default
- All dependencies: `requirements.txt`

## Example: Run Locally (Python)

```
# Stdio version
echo '{"url": "https://example.com"}' | python src/stdio_server.py

# MCP version
python src/mcp_server.py

# CLI version
python src/cli.py https://example.com -o results.json -p
```

## Example: Run in Docker

```
docker build -t ghcr.io/justazul/web-scrapper-stdio:latest .
echo '{"url": "https://example.com"}' | docker run -i --rm ghcr.io/justazul/web-scrapper-stdio:latest
```

## Output Example

```
{"extracted_text": "Example Domain\nThis domain is for use in illustrative examples in documents...", "status": "success", "error_message": null, "final_url": "https://example.com/"}
```

## Testing
- Use the above commands to verify extraction and Markdown output.
- The tool is suitable for integration in any pipeline that can provide JSON lines to stdin and read JSON lines from stdout.
- MCP-specific tests are included in the test suite.
- Core scraping logic can be tested in isolation using the enhanced test suite:
```bash
# Run all tests
docker compose up --build --abort-on-container-exit test

# Run specific tests
docker compose run --rm test pytest -v tests/test_scraper.py
```
