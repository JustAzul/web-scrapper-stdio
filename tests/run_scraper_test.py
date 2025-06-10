#!/usr/bin/env python3
"""
Script to test the scraper in isolation without Docker.
This allows for quick iteration and debugging of the core scraping logic.

Usage:
    python tests/run_scraper_test.py [urls...]
    
Example:
    python tests/run_scraper_test.py https://example.com https://wikipedia.org
"""

import asyncio
import sys
import logging
import time
import os
import argparse

# Add the src directory to the path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.scraper import extract_text_from_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("scraper-test")

TEST_URLS = [
    "https://example.com",
    "https://en.wikipedia.org/wiki/Web_scraping",
    "https://httpstat.us/404",  # Should fail with 404
    "https://this-domain-does-not-exist-12345.com",  # Should fail with DNS error
]

# Helper function, not a test
async def _scrape_url_helper(url, remove_elements=None, custom_timeout=None):
    """Test scraping a single URL and print results."""
    start_time = time.time()
    try:
        logger.info(f"Testing URL: {url}")
        logger.info(f"  Custom elements to remove: {remove_elements}")
        logger.info(f"  Custom timeout: {custom_timeout}")
        
        result = await extract_text_from_url(
            url,
            custom_elements_to_remove=remove_elements,
            custom_timeout=custom_timeout
        )
        
        # Calculate time taken
        time_taken = time.time() - start_time
        
        # Print results
        status = result["status"]
        if status == "success":
            logger.info(f"✅ Success: {url} ({time_taken:.2f}s)")
            text_sample = result["extracted_text"][:100].replace("\n", " ")
            logger.info(f"Text sample: {text_sample}...")
            logger.info(f"Text length: {len(result['extracted_text'])} characters")
        else:
            logger.error(f"❌ Failed: {url} ({time_taken:.2f}s)")
            logger.error(f"Error: {result['error_message']}")
        
        return result
    except Exception as e:
        time_taken = time.time() - start_time
        logger.exception(f"❌ Exception testing {url} ({time_taken:.2f}s): {str(e)}")
        return {"status": "exception", "error_message": str(e), "extracted_text": "", "final_url": url}

# Helper function, not a test
async def _customization_demo():
    """Test custom parameters and show differences in results."""
    url = "https://en.wikipedia.org/wiki/Main_Page"
    
    logger.info("=== Testing customization options ===")
    
    # Test 1: Normal extraction
    logger.info("Test 1: Normal extraction")
    result1 = await _scrape_url_helper(url)
    text_len1 = len(result1["extracted_text"])
    
    # Test 2: With custom elements to remove
    logger.info("Test 2: Removing additional elements")
    # Remove paragraphs, which should reduce the text
    result2 = await _scrape_url_helper(url, remove_elements=['p', 'h1', 'h2'])
    text_len2 = len(result2["extracted_text"])
    
    # Test 3: With shorter timeout
    logger.info("Test 3: Short timeout (1 second)")
    result3 = await _scrape_url_helper(url, custom_timeout=1)
    text_len3 = len(result3["extracted_text"])
    
    # Compare results
    logger.info("\n=== Comparison Results ===")
    logger.info(f"Normal extraction: {text_len1} characters")
    logger.info(f"With extra elements removed: {text_len2} characters ({text_len2/text_len1:.2%} of normal)")
    logger.info(f"With short timeout: {text_len3} characters")
    
    if result3["status"] == "error_timeout":
        logger.info("Short timeout test correctly timed out")
    
    if text_len2 < text_len1:
        logger.info("Element removal successfully reduced content length")
    else:
        logger.warning("Element removal did not reduce content length as expected")

async def main():
    """Main test function that runs the scraper on test URLs."""
    parser = argparse.ArgumentParser(description="Test web scraper in isolation")
    parser.add_argument("urls", nargs="*", help="URLs to test (optional)")
    parser.add_argument("--custom", action="store_true", help="Run customization tests")
    parser.add_argument("-r", "--remove", nargs="+", help="HTML elements to remove")
    parser.add_argument("-t", "--timeout", type=int, help="Custom timeout in seconds")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run customization tests if requested
    if args.custom:
        await _customization_demo()
        return
    
    # Use URLs from command line if provided, otherwise use default test URLs
    urls_to_test = args.urls if args.urls else TEST_URLS
    
    if not urls_to_test:
        logger.error("No URLs provided to test")
        sys.exit(1)
    
    logger.info(f"Starting test with {len(urls_to_test)} URLs")
    
    results = []
    for url in urls_to_test:
        result = await _scrape_url_helper(url, args.remove, args.timeout)
        results.append(result)
    
    # Print summary
    success_count = sum(1 for r in results if r["status"] == "success")
    logger.info(f"Test complete: {success_count}/{len(results)} URLs successfully scraped")
    
    # List failures
    failures = [(i+1, url) for i, (url, result) in enumerate(zip(urls_to_test, results)) if result["status"] != "success"]
    if failures:
        logger.info("Failed URLs:")
        for idx, url in failures:
            logger.info(f"  {idx}. {url}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1) 