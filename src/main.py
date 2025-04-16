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
        
        # Try to identify the domain and wait for domain-specific elements
        parsed_url = urlparse(driver.current_url)
        domain = parsed_url.netloc.replace('www.', '')
        
        # Define a default fallback selector
        main_content_selector = 'body'
        
        # If it's a known domain, use the first selector as indicator of ready content
        if domain in KNOWN_SITE_SELECTORS:
            selectors = KNOWN_SITE_SELECTORS[domain]
            if selectors:
                # Use the first selector as an indicator - try to wait for it
                try:
                    css_selector = selectors[0]
                    # Convert from simple selector to CSS selector if needed
                    if css_selector.startswith("div.") or css_selector.startswith("article"):
                        # Already CSS format
                        pass
                    else:
                        # Assume it's a tag name
                        css_selector = f"{css_selector}"
                    
                    print(f"Waiting for main content element: {css_selector}", file=sys.stderr)
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
                    )
                    print(f"Main content element found: {css_selector}", file=sys.stderr)
                except TimeoutException:
                    print(f"Timed out waiting for main content element: {css_selector}. Continuing anyway.", file=sys.stderr)
        else:
            # For unknown domains, wait for any potential content containers
            generic_content_selectors = ["article", "main", ".content", ".article", "#content", "#main-content"]
            print("Unknown domain. Trying to wait for common content elements...", file=sys.stderr)
            
            for selector in generic_content_selectors:
                try:
                    WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"Found content element: {selector}", file=sys.stderr)
                    break
                except TimeoutException:
                    # Continue to next selector
                    pass

        # Get the final URL after potential redirects
        final_url = driver.current_url
        print(f"Final URL after potential redirects: {final_url}", file=sys.stderr)

        page_source = driver.page_source
        print("Page source fetched.", file=sys.stderr)
        soup = BeautifulSoup(page_source, 'html.parser')

        # --- Targeted Extraction based on Final Domain ---
        # Use the final URL's domain to determine the strategy
        parsed_url = urlparse(final_url)
        domain = parsed_url.netloc
        # Handle cases where domain might have www. prefix
        if domain.startswith('www.'):
             domain = domain[4:]

        content_container = None
        specific_selectors_tried = False

        if domain in KNOWN_SITE_SELECTORS:
            specific_selectors_tried = True
            selectors = KNOWN_SITE_SELECTORS[domain]
            print(f"Known domain '{domain}'. Trying specific selectors: {selectors}", file=sys.stderr)
            for selector in selectors:
                content_container = soup.select_one(selector)
                if content_container:
                    print(f"Found container with selector: {selector}", file=sys.stderr)
                    break
            if not content_container:
                print(f"Specific selectors failed for known domain '{domain}'. Falling back to body.", file=sys.stderr)
                content_container = soup.body # Fallback for known site if specific fails
        else:
            # Check if the original domain was search.app, even if redirected elsewhere
            original_parsed_url = urlparse(url)
            original_domain = original_parsed_url.netloc
            if original_domain == "search.app":
                 print(f"Original domain was search.app, but redirected to unknown domain '{domain}'. Applying article selector as fallback.", file=sys.stderr)
                 content_container = soup.select_one('article')
                 if content_container:
                      specific_selectors_tried = True # Treat this as a specific attempt
                      print("Found container with selector: article (search.app fallback)", file=sys.stderr)

            # If still no container, use body for truly unknown domains
            if not content_container:
                 print(f"Unknown domain '{domain}'. Extracting from body.", file=sys.stderr)
                 content_container = soup.body

        if not content_container:
             print("Could not find a suitable content container (body or specific). Unable to extract text.", file=sys.stderr)
             return ""

        # --- Noise Removal ---
        # More aggressive removal for specific containers, less for generic body
        if specific_selectors_tried and content_container != soup.body:
             # Assume the specific container is mostly article, remove more aggressively
            noise_selectors = [
                'script', 'style', 'header', 'footer', 'nav', 'aside',
                '.ad', '.ads', '.advertisement', '.sidebar', '.related-posts',
                '.comments', '.comment-section', '.footer', '.header', '.nav',
                '.menu', '.meta', '.metadata', '.share', '.social', '.pagination',
                'form', 'button', '[role="navigation"]', '[role="banner"]',
                '[role="complementary"]', '[aria-hidden="true"]',
                '.ad-container', '.promo', '.promoted', '.related', '.newsletter'
            ]
            print("Applying aggressive noise removal for specific container.", file=sys.stderr)
        else:
            # For generic body or fallback, remove only essential clutter
            noise_selectors = ['script', 'style', 'header', 'footer', 'nav', 'aside']
            print("Applying basic noise removal for body/fallback.", file=sys.stderr)

        for noise_selector in noise_selectors:
            try:
                for element in content_container.select(noise_selector):
                     if element: # Check if element exists before decomposing
                         element.decompose()
            except Exception as noise_e:
                 # Catch potential errors during noise removal (e.g., invalid selector)
                 print(f"Warning: Error removing noise with selector '{noise_selector}': {noise_e}", file=sys.stderr)


        # --- Final Text Extraction ---
        text_parts = [t.strip() for t in content_container.stripped_strings]
        text = ' '.join(filter(None, text_parts)) # Join non-empty strings

        print("Text extracted.", file=sys.stderr)
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