import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
# Use webdriver_manager only for local development/testing if needed.
# In Docker, we install ChromeDriver directly.
# from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import os
import re # Import regex for class matching
from urllib.parse import urlparse # Import urlparse to get domain

# Mapping of known domains to their primary content selectors
KNOWN_SITE_SELECTORS = {
    "forbes.com": ["div.article-body", "article"], # Forbes has specific body, fallback to article
    "fortune.com": ["div.content-wrapper", "article"], # Fortune specific wrapper
    "search.app": ["article"], # search.app redirects, but target often uses article. Fallback handles this.
    "dmnews.com": ["div.story-content", "div.single-post", "article"], # dmnews specific selectors
    "tomsguide.com": ["article"],                 # Tomsguide uses article
    "dev.to": ["article"],                         # Dev.to uses article
    "xda-developers.com": ["div.article-body", "article"] # XDA specific body
}

def fetch_url_content(url: str) -> str:
    """Fetches the text content of a given URL using headless Chrome."""
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu") # Often needed in headless environments
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # In Docker, ChromeDriver should be in the PATH
    # For local, uncomment the webdriver_manager import and line below
    # service = ChromeService(ChromeDriverManager().install())
    # When running in Docker, ensure chromedriver is in PATH
    service = ChromeService()
    driver = None

    try:
        print(f"Attempting to fetch content from: {url}", file=sys.stderr)
        driver = webdriver.Chrome(service=service, options=options)
        # Increase page load timeout slightly
        driver.set_page_load_timeout(30)
        driver.get(url)

        # Wait for page elements to load with a smarter strategy
        print("Waiting for page to load...", file=sys.stderr)
        
        # Wait for document to be ready - this is a baseline wait
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Get the final URL after potential redirects
        final_url = driver.current_url
        print(f"Final URL after potential redirects: {final_url}", file=sys.stderr)

        page_source = driver.page_source
        print("Page source fetched.", file=sys.stderr)
        soup = BeautifulSoup(page_source, 'html.parser')

        # Always extract the full <body> content
        content_container = soup.body
        if not content_container:
            print("Could not find <body> tag in HTML.", file=sys.stderr)
            return ""

        # Essential noise removal
        noise_selectors = ['script', 'style', 'header', 'footer', 'nav', 'aside', 'form', 'button', 'input', 'select', 'textarea', 'label', 'iframe', 'figure', 'figcaption']
        for noise_selector in noise_selectors:
            try:
                for element in content_container.select(noise_selector):
                    if element:
                        element.decompose()
            except Exception as noise_e:
                print(f"Warning: Error removing noise with selector '{noise_selector}': {noise_e}", file=sys.stderr)

        text_parts = [t.strip() for t in content_container.stripped_strings]
        text = ' '.join(filter(None, text_parts))
        print("Text extracted.", file=sys.stderr)
        
        # Check if content is too short for non-search.app URLs
        if not text:
            print("No text content extracted.", file=sys.stderr)
            return ""
            
        # For search.app URLs, accept shorter content
        original_domain = urlparse(url).netloc.lower()
        min_length = 30 if 'search.app' in original_domain else 100
        
        if len(text) < min_length and 'search.app' not in original_domain:
            print(f"Extracted content too short (< {min_length} characters).", file=sys.stderr)
            return ""
            
        return text

    except Exception as e:
        print(f"An error occurred during scraping: {e}", file=sys.stderr)
        return ""
    finally:
        if driver:
            print("Closing browser.", file=sys.stderr)
            driver.quit()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python src/main.py <url>", file=sys.stderr)
        sys.exit(1)

    target_url = sys.argv[1]
    content = fetch_url_content(target_url)

    if content:
        print(content)
    else:
        print("Failed to retrieve content.", file=sys.stderr)
        sys.exit(1) 