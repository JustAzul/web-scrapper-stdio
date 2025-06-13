## Web Scrapper Service (MCP Stdin/Stdout, Markdown Output by Default)

This project is a Python-based web scrapper that extracts primary text content from web pages, outputting Markdown via a simple stdio/JSON-RPC interface. It is designed as an MCP (Model Context Protocol) server for seamless AI model interaction.

- **Core scraping logic:** `src/scraper/`
- **MCP server entrypoint:** `src/mcp_server.py`
- **Dockerfile:** for containerization and tests
- **All dependencies:** `requirements.txt`

## Technology Stack
- Python 3.11+
- Playwright (headless browser automation)
- BeautifulSoup (HTML parsing)
- Markdownify (HTML to Markdown)
- Docker
- MCP (Model Context Protocol)

## Usage

### MCP Server (Tool/Prompt)

This web scrapper is used as an MCP (Model Context Protocol) tool, allowing it to be used by AI models or other automation directly.

#### Tool: `scrape_web`

**Parameters:**
 - `url` (string, required): The URL to scrape
- `max_length` (integer, optional): Maximum length of returned content (default: 5000)
- `timeout_seconds` (integer, optional): Timeout in seconds for the page load (default: 30)
- `user_agent` (string, optional): Custom User-Agent string passed directly to the browser (defaults to a random agent)
- `wait_for_network_idle` (boolean, optional): Wait for network activity to settle before scraping (default: true)
- `custom_elements_to_remove` (list, optional): Additional HTML elements to remove
- `grace_period_seconds` (float, optional): Short grace period to allow JS to finish rendering (in seconds, default: 2.0)
- `output_format` (string, optional): Desired format of returned content. Options are `markdown`, `text`, or `html` (default: `markdown`)

**Returns:**
- Content extracted from the webpage in the selected format
- Errors are reported as strings starting with `[ERROR] ...`

#### Prompt: `scrape`

**Parameters:**
- `url` (string, required): The URL to scrape
- `output_format` (string, optional): Choose `markdown`, `text`, or `html` (default: `markdown`)

**Returns:**
- Content extracted from the webpage in the selected format

**Note:**
- Output format can be ``markdown`` (default), ``text`` or ``html``.
- The scrapper does not check robots.txt and will attempt to fetch any URL provided.
- No REST API or CLI tool is included; this is a pure MCP stdio/JSON-RPC tool.
- The scrapper always extracts the full `<body>` content of web pages, applying only essential noise removal (removing script, style, nav, footer, aside, header, and similar non-content tags). The scrapper detects and handles Cloudflare challenge screens, returning a specific error string.

## Environment Variables

You can override most configuration options using environment variables:

- `DEFAULT_TIMEOUT_SECONDS`: Timeout for page loads and navigation (default: 30)
- `DEFAULT_MIN_CONTENT_LENGTH`: Minimum content length for extracted text (default: 100)
- `DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS`: Minimum delay between requests to the same domain (default: 2)
- `DEBUG_LOGS_ENABLED`: Set to `true` to enable debug-level logs (default: `false`)

## Error Handling & Rate Limiting

- The scrapper detects and returns errors for navigation failures, timeouts, HTTP errors (including 404), and Cloudflare anti-bot challenges.
- Rate limiting is enforced per domain (default: 2 seconds between requests).
- Cloudflare and similar anti-bot screens are detected and reported as errors.

## Development & Testing

### Running Tests (Docker Compose)

All tests must be run using Docker Compose. Do **not** run tests outside Docker.

- **All tests:**
  ```sh
  docker compose up --build --abort-on-container-exit test
  ```
- **MCP server tests only:**
  ```sh
  docker compose up --build --abort-on-container-exit test_mcp
  ```
- **Scrapper tests only:**
  ```sh
  docker compose up --build --abort-on-container-exit test_scrapper
  ```

## Cursor IDE Integration

To use this web scrapper as a tool in Cursor IDE, add the following configuration to your `mcp.json`:

```json
"web-scrapper-stdio": {
  "command": "docker",
  "args": [
    "run",
    "-i",
    "--rm",
    "ghcr.io/justazul/web-scrapper-stdio"
  ]
}
```

This configuration allows Cursor IDE to invoke the web scrapper container directly for web content extraction via MCP stdio/JSON-RPC.
