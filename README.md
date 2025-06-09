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

**Note:**
- Output is always Markdown for easy downstream use.
- The scraper does not check robots.txt and will attempt to fetch any URL provided.
- No REST API or MCP server is included; this is a pure stdio tool.
- All domains with available RSS feeds are now included in the test suite (fortune.com, techcrunch.com, wired.com, engadget.com, medium.com, dev.to, tomsguide.com, xda-developers.com, dmnews.com).
- Test cases use domain URLs for clear output.
- The scraper detects and handles Cloudflare challenge screens, returning a specific error status.

---

# Project Overview

This project is a Python-based web scraper that extracts primary text content from web pages, outputting Markdown via a simple stdio interface. It is designed for use in pipelines, containers, and AI toolchains.

## Technology Stack
- Python 3.9+
- Playwright
- BeautifulSoup
- Markdownify
- Docker

## Development
- Core scraping logic: `src/scraper.py`
- Stdio entrypoint: `src/stdio_server.py`
- Dockerfile: runs the stdio server by default
- All dependencies: `requirements.txt`

## Example: Run Locally (Python)

```
echo '{"url": "https://example.com"}' | python src/stdio_server.py
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
