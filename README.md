# Web Scraper Service (Stdin/Stdout, Markdown Output)

## Usage (Stdin/Stdout)

Run the web scraper as a Docker container that reads JSON lines from stdin and outputs results as JSON lines to stdout:

```
echo '{"url": "https://example.com"}' | docker run -i --rm justazul/web-scrapper
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

---

# Project Overview

This project is a Python-based web scraper that extracts primary text content from web pages, outputting Markdown via a simple stdio interface. It is designed for use in pipelines, containers, and AI toolchains.

## Technology Stack
- Python 3.10+
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
docker build -t justazul/web-scrapper .
echo '{"url": "https://example.com"}' | docker run -i --rm justazul/web-scrapper
```

## Output Example

```
{"extracted_text": "Example Domain\nThis domain is for use in illustrative examples in documents...", "status": "success", "error_message": null, "final_url": "https://example.com/"}
```

## Testing
- Use the above commands to verify extraction and Markdown output.
- The tool is suitable for integration in any pipeline that can provide JSON lines to stdin and read JSON lines from stdout.

---

# Changelog
- Now stdio-only, Markdown output, no robots.txt compliance, no REST API/MCP. 