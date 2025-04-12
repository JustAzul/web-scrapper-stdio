# Python Web Content Fetcher

This application fetches text content from a given URL using headless Chrome (via Selenium) within a Docker container and prints the extracted text to the terminal.

## Prerequisites

- Docker Engine and Docker Compose installed.

## Project Structure

```
.
├── Dockerfile           # Defines the Docker image
├── docker-compose.yml   # Configures the Docker service
├── prd.md               # Product Requirements Document
├── README.md            # This file
├── requirements.txt     # Python dependencies
└── src/
    └── main.py          # The main Python script
```

## Setup and Usage (Docker Recommended)

1.  **Build the Docker Image:**
    Open your terminal in the project's root directory and run:
    ```bash
    docker compose build
    ```
    This command builds the Docker image based on the `Dockerfile`, installing Python, Chrome, ChromeDriver, and Python dependencies.

2.  **Run the Application:**
    To fetch content from a specific URL, use the `docker compose run` command. Replace `<url>` with the actual URL you want to fetch.
    ```bash
    docker compose run --rm app "<url>"
    ```
    *   `--rm`: Automatically removes the container once the script finishes execution.
    *   `app`: The name of the service defined in `docker-compose.yml`.
    *   `"<url>"`: The URL passed as a command-line argument to the `src/main.py` script inside the container.

    **Example:**
    ```bash
    docker compose run --rm app "https://example.com"
    ```
    The extracted text content from the URL will be printed to your terminal.

## How it Works

-   **`Dockerfile`**: Sets up a Python 3.10 environment, installs Google Chrome and the matching ChromeDriver, copies the application code, and installs Python dependencies (`selenium`, `beautifulsoup4`).
-   **`docker-compose.yml`**: Defines a service named `app` that uses the built Docker image. It specifies `shm_size` for Chrome performance and allows passing the target URL via the run command.
-   **`src/main.py`**: The script receives a URL, initializes a headless Selenium WebDriver for Chrome, navigates to the URL, waits briefly for dynamic content loading, extracts the page source, uses BeautifulSoup to parse and clean the HTML (removing scripts/styles), and prints the resulting text.

## Local Development (Alternative)

While Docker is recommended for consistency, you can run the script locally:

1.  **Install Prerequisites:** Ensure you have Python 3.10+, pip, and Git installed.
2.  **Install Chrome/ChromeDriver:** You need Google Chrome and the corresponding ChromeDriver installed and accessible in your system's PATH.
3.  **Set up Environment:**
    ```bash
    git clone <your-repo-url> # If not already cloned
    cd python-web-mcp-scrapper
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
4.  **Run:**
    *Modify `src/main.py` to use `webdriver_manager`*: Uncomment the `webdriver_manager` import and the line `service = ChromeService(ChromeDriverManager().install())`, and comment out `service = ChromeService()`.
    ```bash
    python src/main.py "<url>"
    ```

## Future Improvements

-   Implement robust waiting strategies (e.g., waiting for specific elements) instead of `time.sleep()`.
-   Enhance text extraction logic (e.g., targeting specific HTML containers like `<article>`, `<main>`).
-   Add more comprehensive error handling (network issues, timeouts, invalid URLs).
-   Allow configuration of browser options (user agent, timeouts) via environment variables or arguments.
-   Support different output formats (JSON, saving to file). 