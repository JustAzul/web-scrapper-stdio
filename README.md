# Web Scraper MCP Tool

A service designed to be invoked by AI models via a Model Context Protocol (MCP) server. It fetches and extracts primary text content from web URLs using headless browsing (Playwright).

## Setup and Running

This service is containerized using Docker and managed with Docker Compose.

1.  **Prerequisites**:
    *   Docker
    *   Docker Compose

2.  **Build the Service**:
    ```bash
    docker compose build
    ```

3.  **Run the Service**:
    ```bash
    docker compose up webscraper
    ```
    *   Replace `webscraper` with the actual service name defined in your `docker-compose.yml` if different (it is `webscraper` in the provided example).
    *   The service will typically be available on `http://localhost:8000` (or the port mapped in `docker-compose.yml`).

4.  **Environment Variables**:
    *   Configuration options (timeouts, user agent, viewport) can be set via environment variables.
    *   Copy `.env.example` to `.env` and modify the values as needed.
    ```bash
    cp .env.example .env
    # Edit .env file with your custom values
    ```
    *   Docker Compose will automatically load variables from the `.env` file.

## API Usage

The service exposes a single endpoint `/extract` via POST request.

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

## Testing

Integration tests using `pytest` are included.

1.  **Run Tests**:
    *   Ensure the service containers are not running (`docker compose down`).
    *   Run the tests using the `test` service defined in `docker-compose.yml`:
    ```bash
    docker compose run test
    ```
    *   This command builds the necessary images, starts the main service, runs the tests against it, and then tears down the test-specific containers.

## Development

*   Core logic is in `src/scraper.py`.
*   API endpoint definition is in `src/api.py`.
*   Configuration is managed in `src/config.py` (loaded from environment variables).
*   Tests are in the `tests/` directory.
*   Dependencies are in `requirements.txt`. 