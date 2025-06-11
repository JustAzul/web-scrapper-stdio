# Web Scraper Service (MCP Stdin/Stdout, Markdown Output)

## Usage (MCP Stdin/Stdout)

Run the web scraper as a Docker container that reads JSON-RPC lines from stdin and outputs results as formatted strings (Markdown with metadata):

```
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "scrape_web", "arguments": {"url": "https://example.com"}}}' | docker run -i --rm ghcr.io/justazul/web-scrapper-stdio:latest
```

- Each input line must be a JSON-RPC 2.0 object with a `url` field in `arguments`.
- The output is a JSON-RPC response with:
  - `status` (success/error)
  - `extracted_text` (Markdown content)
  - `final_url` (the resolved URL)
  - Errors are reported as strings starting with `[ERROR] ...` in the `extracted_text` field or as an `error` object.

**Example Output:**
```
{"jsonrpc": "2.0", "id": 1, "result": {"status": "success", "extracted_text": "Title: Example Domain\n\nURL Source: https://example.com/\n\nMarkdown Content:\n# Example Domain\n\nThis domain is for use in illustrative examples in documents...", "final_url": "https://example.com"}}
```

## Usage (Docker)

Build and run the Docker image (if not using the published image):

```
docker build -t web-scrapper-stdio:latest .
```

Run the container with a JSON-RPC request:

```
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "scrape_web", "arguments": {"url": "https://example.com"}}}' | docker run -i --rm ghcr.io/justazul/web-scrapper-stdio:latest
```

## Usage (MCP Server)

This web scraper is used as an MCP (Model Context Protocol) tool, allowing it to be used by AI models or other automation directly.

### Tool Name: scrape_web

**Parameters:**
- `url` (string, required): The URL to scrape
- `max_length` (integer, optional): Maximum length of returned content (default: 5000)
- `timeout_seconds` (integer, optional): Timeout in seconds for the page load (default: 30)
- `user_agent` (string, optional): Custom User-Agent string
- `wait_for_network_idle` (boolean, optional): Whether to wait for network activity to settle (default: true)
- `custom_elements_to_remove` (list, optional): Additional HTML elements to remove

**Returns:**
- Markdown formatted content extracted from the webpage, as a string (see example above)
- Errors are reported as strings starting with `[ERROR] ...`

### Example:

```
{"jsonrpc": "2.0", "id": 1, "result": {"status": "success", "extracted_text": "Title: Example Domain\n\nURL Source: https://example.com/\n\nMarkdown Content:\n# Example Domain\n\nThis domain is for use in illustrative examples in documents...", "final_url": "https://example.com"}}
```

### Prompt Name: scrape

**Parameters:**
- `url` (string, required): The URL to scrape

**Returns:**
- Markdown formatted content extracted from the webpage, as a string

**Note:**
- Output is always Markdown for easy downstream use.
- The scraper does not check robots.txt and will attempt to fetch any URL provided.
- No REST API or CLI tool is included; this is a pure MCP stdio/JSON-RPC tool.
- The scraper always extracts the full <body> content of web pages, applying only essential noise removal (removing script, style, nav, footer, aside, header, and similar non-content tags). Domain-specific selectors are no longer used. The scraper detects and handles Cloudflare challenge screens, returning a specific error string.

## Project Overview

This project is a Python-based web scraper that extracts primary text content from web pages, outputting Markdown via a simple stdio/JSON-RPC interface. It is designed for use in pipelines, containers, and AI toolchains, with a focus on MCP (Model Context Protocol) integration for seamless AI model interaction.

## Technology Stack
- Python 3.11+
- Playwright
- BeautifulSoup
- Markdownify
- Docker
- MCP (Model Context Protocol)

## Development
- Core scraping logic: `src/scraper/`
- MCP server entrypoint: `src/mcp_server.py`
- Dockerfile: for tests
- All dependencies: `requirements.txt`

## Cursor IDE Integration

To use this web scraper as a tool in Cursor IDE, add the following configuration to your `mcp.json`:

```json
"web-scrapper-stdio": {
  "command": "docker",
  "args": [
    "run",
    "-i",
    "--rm",
    "ghcr.io/justazul/web-scrapper-stdio:latest"
  ]
}
```

This configuration allows Cursor IDE to invoke the web scraper container directly for web content extraction via MCP stdio/JSON-RPC.
