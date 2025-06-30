# Web Scrapper Service (MCP Stdin/Stdout)

<!-- Badges: auto-generated, update workflow and Gist as needed -->
![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/JustAzul/d3ad29ac6775300b8475b9cedd434ae2/raw/50de0495daf2711a203fb68dfb148a20547e910e/gistfile1.txt)
![Build](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/JustAzul/d2497a7eb6d0d1a57a4faea9df7c78a1/raw/310de0cdeb3dc76aca880247297f871d9a0ee957/gistfile1.txt)
![Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/JustAzul/15392260e0e9be9f6f72ae5cf3182743/raw/6c05ef50ac0e4c04e748f04ef899324e7f44e04d/gistfile1.txt)
![Version](https://img.shields.io/github/v/release/JustAzul/web-scrapper-stdio)
![License](https://img.shields.io/github/license/JustAzul/web-scrapper-stdio)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Repo Size](https://img.shields.io/github/repo-size/JustAzul/web-scrapper-stdio)
![Last Commit](https://img.shields.io/github/last-commit/JustAzul/web-scrapper-stdio)
![Issues](https://img.shields.io/github/issues/JustAzul/web-scrapper-stdio)
![PRs](https://img.shields.io/github/issues-pr/JustAzul/web-scrapper-stdio)
![linting: Ruff](https://img.shields.io/badge/linting-Ruff-black?logo=ruff&logoColor=black)
![GHCR](https://img.shields.io/badge/ghcr.io-JustAzul%2Fweb--scrapper--stdio-blue?logo=github)

**A Python-based MCP server for robust, headless web scraping—extracts main text content from web pages and outputs Markdown, text, or HTML for seamless AI and automation integration.**

## Key Features
- Headless browser scraping (Playwright, BeautifulSoup, Markdownify)
- Outputs Markdown, text, or HTML
- Designed for MCP (Model Context Protocol) stdio/JSON-RPC integration
- Dockerized, with pre-built images
- Configurable via environment variables
- Robust error handling (timeouts, HTTP errors, Cloudflare, etc.)
- Per-domain rate limiting
- Easy integration with AI tools and IDEs (Cursor, Claude Desktop, Continue, JetBrains, Zed, etc.)
- One-click install for Cursor, interactive installer for Claude
- Enforced code quality with **Ruff** and **Bandit**.
- Automated dependency checking with **Deptry**.

---

## Quick Start

### Run with Docker
```sh
docker run -i --rm ghcr.io/justazul/web-scrapper-stdio
```

### One-Click Installation (Cursor IDE)
[![Add to Cursor](https://docs.cursor.com/add-to-cursor.svg)](https://docs.cursor.com/add-to-cursor?server=web-scrapper-stdio)

Or, use the [Cursor MCP Installer](https://www.npmjs.com/package/cursor-mcp-installer-free) for interactive installation of any MCP server:
```json
{
  "mcpServers": {
    "cursor-mcp-installer": {
      "command": "npx",
      "args": ["cursor-mcp-installer-free"]
    }
  }
}
```

---

## Integration with AI Tools & IDEs

This service supports integration with a wide range of AI tools and IDEs that implement the Model Context Protocol (MCP). Below are ready-to-use configuration examples for the most popular environments. Replace the image/tag as needed for custom builds.

### Cursor IDE
Add to your `.cursor/mcp.json` (project-level) or `~/.cursor/mcp.json` (global):
```json
{
  "mcpServers": {
    "web-scrapper-stdio": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "ghcr.io/justazul/web-scrapper-stdio"
      ]
    }
  }
}
```

### Claude Desktop
Add to your Claude Desktop MCP config (typically `claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "web-scrapper-stdio": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "ghcr.io/justazul/web-scrapper-stdio"
      ]
    }
  }
}
```
Or, use the [MCP Installer](https://github.com/anaisbetts/mcp-installer) for interactive installation:
```json
{
  "mcpServers": {
    "mcp-installer": {
      "command": "npx",
      "args": ["@anaisbetts/mcp-installer"]
    }
  }
}
```

### Continue (VSCode/JetBrains Plugin)
Add to your `continue.config.json` or via the Continue plugin MCP settings:
```json
{
  "mcpServers": {
    "web-scrapper-stdio": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "ghcr.io/justazul/web-scrapper-stdio"
      ]
    }
  }
}
```

### IntelliJ IDEA (JetBrains AI Assistant)
Go to **Settings > Tools > AI Assistant > Model Context Protocol (MCP)** and add a new server. Use:
```json
{
  "command": "docker",
  "args": [
    "run",
    "-i",
    "--rm",
    "ghcr.io/justazul/web-scrapper-stdio"
  ]
}
```

### Zed Editor
Add to your Zed MCP config (see Zed docs for the exact path):
```json
{
  "mcpServers": {
    "web-scrapper-stdio": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "ghcr.io/justazul/web-scrapper-stdio"
      ]
    }
  }
}
```

---

## Usage

### MCP Server (Tool/Prompt)
This web scrapper is used as an MCP (Model Context Protocol) tool, allowing it to be used by AI models or other automation directly.

#### Tool: `scrape_web`
**Parameters:**
- `url` (string, required): The URL to scrape
- `max_length` (integer, optional): Maximum length of returned content (default: unlimited)
- `timeout_seconds` (integer, optional): Timeout in seconds for the page load (default: 30)
- `user_agent` (string, optional): Custom User-Agent string passed directly to the browser (defaults to a random agent)
- `wait_for_network_idle` (boolean, optional): Wait for network activity to settle before scraping (default: true)
- `custom_elements_to_remove` (list of strings, optional): Additional HTML elements (CSS selectors) to remove before extraction
- `grace_period_seconds` (float, optional): Short grace period to allow JS to finish rendering (in seconds, default: 2.0)
- `output_format` (string, optional): `markdown`, `text`, or `html` (default: `markdown`)
- `click_selector` (string, optional): If provided, click the element matching this selector after navigation and before extraction

**Returns:**
- Markdown formatted content extracted from the webpage, as a string
- Errors are reported as strings starting with `[ERROR] ...`

**Example: Using `click_selector` and `custom_elements_to_remove`**
```json
{
  "url": "http://uitestingplayground.com/clientdelay",
  "click_selector": "#ajaxButton",
  "grace_period_seconds": 10,
  "custom_elements_to_remove": [".ads-banner", "#popup"],
  "output_format": "markdown"
}
```

#### Prompt: `scrape`
**Parameters:**
- `url` (string, required): The URL to scrape
- `output_format` (string, optional): `markdown`, `text`, or `html` (default: `markdown`)

**Returns:**
- Content extracted from the webpage in the chosen format

**Note:**
- Markdown is returned by default but text or HTML can be requested via `output_format`.
- The scrapper does not check robots.txt and will attempt to fetch any URL provided.
- No REST API or CLI tool is included; this is a pure MCP stdio/JSON-RPC tool.
- The scrapper always extracts the full `<body>` content of web pages, applying only essential noise removal (removing script, style, nav, footer, aside, header, and similar non-content tags). The scrapper detects and handles Cloudflare challenge screens, returning a specific error string.

---

## Configuration

You can override most configuration options using environment variables:
- `DEFAULT_TIMEOUT_SECONDS`: Timeout for page loads and navigation (default: 30)
- `DEFAULT_MIN_CONTENT_LENGTH`: Minimum content length for extracted text (default: 100)
- `DEFAULT_MIN_CONTENT_LENGTH_SEARCH_APP`: Minimum content length for search.app domains (default: 30)
- `DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS`: Minimum delay between requests to the same domain (default: 2)
- `DEFAULT_TEST_REQUEST_TIMEOUT`: Timeout for test requests (default: 10)
- `DEFAULT_TEST_NO_DELAY_THRESHOLD`: Threshold for skipping artificial delays in tests (default: 0.5)
- `DEBUG_LOGS_ENABLED`: Set to `true` to enable debug-level logs (default: `false`)

### Chunked HTML Processor Tuning  
The scraper now includes a **memory-aware, chunked HTML processor**.  Default behaviour preserves backward-compatibility, but you can fine-tune processing via environment variables:

| Variable | Default | Description |
| :-- | :-- | :-- |
| `CHUNK_ENABLE` | `true` | Set `false` to disable chunked processing globally. |
| `CHUNK_SIZE_THRESHOLD` | `100000` (bytes) | Minimum HTML size before chunk mode triggers. |
| `CHUNK_MEMORY_LIMIT_MB` | `100` | Soft RSS limit; processor enters *auto* chunk mode when current RSS > `0.8 * limit` and aborts when RSS > `1.2 * limit`. |
| `CHUNK_PARSER` | `html.parser` | Parser used by **both** processing paths (`html.parser`, `lxml`, etc.). |
| `CHUNK_EXTRA_NOISE_CLEANUP` | `false` | When `true`, removes additional noise selectors (`nav`, `.ads`, `.sidebar`, …).  Disabled by default for output parity. |

These map directly to the new `ChunkedHTMLProcessor` constructor parameters for library users.

---

## Error Handling & Limitations

- The scrapper detects and returns errors for navigation failures, timeouts, HTTP errors (including 404), and Cloudflare anti-bot challenges.
- Rate limiting is enforced per domain (default: 2 seconds between requests).
- Cloudflare and similar anti-bot screens are detected and reported as errors.
- **Limitations:**
  - No REST API or CLI tool (MCP stdio/JSON-RPC only)
  - No support for non-HTML content (PDF, images, etc.)
  - May not bypass advanced anti-bot protections
  - No authentication or session management for protected pages
  - Not intended for scraping at scale or violating site terms

---

## Code Quality

This project uses modern tooling to ensure high code quality, consistency, and security:

- **[Ruff](https://github.com/astral-sh/ruff)**: An extremely fast Python linter and code formatter, used to enforce a consistent code style (compatible with Black) and catch common errors.
- **[Bandit](https://github.com/PyCQA/bandit)**: A tool designed to find common security issues in Python code.
- **[Deptry](https://github.com/fpgmaas/deptry)**: A command-line tool to check for issues with dependencies, such as unused or missing dependencies.

## Development & Testing

### Local Development Setup

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/JustAzul/python-web-mcp-scrapper.git
    cd python-web-mcp-scrapper
    ```

2.  **Create a virtual environment and install dependencies:**
    ```sh
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt -r requirements-dev.txt
    ```

3.  **Install Playwright browsers:**
    ```sh
    playwright install --with-deps chromium
    ```

### Running Tests (Docker Compose)

All tests **must** be run using Docker Compose to ensure a consistent and clean environment. Do **not** run `pytest` directly on your local machine.

The project is configured with different test services in `docker-compose.yml` for flexibility:

-   **Run all fast tests (unit and integration, excluding slow):**
    This is the default command and is recommended for most development workflows.
    ```sh
    docker compose up --build --abort-on-container-exit test
    ```

-   **Run only unit tests:**
    This is the fastest way to get feedback on core logic changes.
    ```sh
    docker compose up --build --abort-on-container-exit test-unit
    ```

-   **Run all integration tests (excluding slow):**
    ```sh
    docker compose up --build --abort-on-container-exit test-integration
    ```

-   **Run the complete test suite (including slow external tests):**
    This command runs all tests, including those marked as `@pytest.mark.slow`, which make requests to external websites and can be slow or unreliable.
    ```sh
    docker compose up --build --abort-on-container-exit test-all
    ```

### Linting and Formatting

To automatically format the code and check for linting errors, run:

```sh
ruff format .
ruff check .
```

---

## Contributing

Contributions are welcome! Please open issues or pull requests for bug fixes, features, or improvements. If you plan to make significant changes, open an issue first to discuss your proposal.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Contact & Support

For questions, support, or feedback, please open an issue on GitHub or contact the maintainer.
