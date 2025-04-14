# Web Scraper Service (API + MCP Tool)

A versatile application designed to fetch and extract primary text content from web URLs. It provides this functionality through two interfaces: a direct **REST API endpoint (`/extract`)** for general integrations and a **Model Context Protocol (MCP) server** hosting a `WEBPAGE_TEXT_EXTRACTOR` tool specifically for AI model consumption. The service uses headless browsing (Playwright) for dynamic content and is containerized using Docker.

## Setup and Running

This service is containerized using Docker and managed with Docker Compose.

1.  **Prerequisites**:
    *   Docker
    *   Docker Compose

2.  **Build the Service**:
    ```bash
    docker compose build
    ```

3.  **Run the Services**:
    ```bash
    docker compose up
    ```
    *   This command starts both the API service (`webscraper`) and the MCP server (`mcp_server`).
    *   The API service will typically be available on `http://localhost:8000` (or the port mapped in `docker-compose.yml`). The MCP server runs internally within the Docker network.

4.  **Environment Variables**:
    *   Configuration options (timeouts, user agent, viewport) can be set via environment variables.
    *   Copy `.env.example` to `.env` and modify the values as needed.
    ```bash
    cp .env.example .env
    # Edit .env file with your custom values
    ```
    *   Docker Compose will automatically load variables from the `.env` file.

## API Usage (`/extract` Endpoint)

The service exposes a single endpoint `/extract` via POST request for direct integration.

*   **URL**: `http://localhost:8000/extract` (adjust host/port if needed)
*   **Method**: `POST`
*   **Headers**: `Content-Type: application/json`
*   **Body (JSON)**:
    ```json
    {
      "url": "<URL_TO_SCRAPE>"
    }
    ```
    *   Replace `<URL_TO_SCRAPE>` with the fully qualified URL you want to process.

**Example API Call (using curl)**:

```bash
cURL -X POST http://localhost:8000/extract \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
```

**Example Success Response (JSON)**:

```json
{
  "extracted_text": "Example Domain\nThis domain is for use in illustrative examples in documents...",
  "status": "success",
  "error_message": null,
  "final_url": "https://example.com/"
}
```

**Example Error Response (JSON)**:

```json
{
  "extracted_text": "",
  "status": "error_fetching",
  "error_message": "Navigation failed: net::ERR_NAME_NOT_RESOLVED at https://nonexistent-domain-for-testing-12345.com/somepage",
  "final_url": "https://nonexistent-domain-for-testing-12345.com/somepage"
}
```

## MCP Tool Usage (`WEBPAGE_TEXT_EXTRACTOR`)

The service also hosts an MCP server exposing the `WEBPAGE_TEXT_EXTRACTOR` tool for consumption by MCP-compatible clients (e.g., AI models).

*   **Tool Name**: `WEBPAGE_TEXT_EXTRACTOR`
*   **Description**: Fetches the primary text content from a given public web URL. Uses headless browsing to handle JavaScript-heavy pages. Ideal for extracting articles, blog posts, or documentation.
*   **Arguments**:
    *   `url` (str, required): The fully qualified URL of the web page to scrape.
*   **Returns (JSON object)**:
    *   `extracted_text` (str): The main textual content extracted from the page. Returns an empty string if no significant content is found or if an error occurs during extraction.
    *   `status` (str): Indicates the outcome. Possible values: "success", "error_fetching", "error_parsing", "error_timeout", "error_invalid_url", "error_unknown".
    *   `error_message` (str | None): A brief description of the error if the status is not "success". Otherwise, null.
    *   `final_url` (str): The URL the browser ended up on after any redirects. Same as input `url` if no redirects occurred.

**Conceptual Example MCP Tool Call**:

*(Note: Requires an MCP client library or tool)*

```python
# Hypothetical MCP client usage
# client = MCPClient(server_address="mcp_tool_server") # Connect to the server (name resolution depends on client context)
# result = client.call_tool(
#     tool_name="WEBPAGE_TEXT_EXTRACTOR",
#     arguments={"url": "https://example.com"}
# )
# print(result) # Expected output would be the JSON object described above
```

## Testing

Integration tests using `pytest` are included in `tests/test_integration.py`.

1.  **Run Tests**:
    *   Ensure the service containers are not running (`docker compose down`).
    *   Run the tests using the `test` service defined in `docker-compose.yml`:
    ```bash
    docker compose run test
    ```
    *   This command builds the necessary images, starts the main service, runs the tests against it, and then tears down the test-specific containers.

## Development

*   Core scraping logic is in `src/scraper.py`.
*   API endpoint definition is in `src/api.py`.
*   MCP server and tool definition is in `src/mcp_server.py`.
*   Configuration is managed in `src/config.py` (loaded from environment variables).
*   Integration tests (API and simulated MCP) are in `tests/test_integration.py`.
*   Dependencies are in `requirements.txt`. 