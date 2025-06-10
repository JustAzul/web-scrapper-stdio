#!/usr/bin/env python3

import argparse
import asyncio
import json
import logging
import sys
from typing import List, Optional

from scraper import extract_text_from_url

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("scraper-cli")

async def scrape_urls(urls: List[str], output_file: Optional[str] = None, pretty: bool = False, 
                     remove_elements: Optional[List[str]] = None, timeout: Optional[int] = None) -> None:
    """
    Scrape content from a list of URLs and output results to stdout or a file.
    
    Args:
        urls: List of URLs to scrape
        output_file: Optional file path to save results
        pretty: Whether to format JSON output with indentation
        remove_elements: Optional list of HTML elements to remove
        timeout: Optional custom timeout in seconds
    """
    results = []
    
    for url in urls:
        logger.info(f"Scraping: {url}")
        result = await extract_text_from_url(url, custom_elements_to_remove=remove_elements, custom_timeout=timeout)
        
        # Add the URL to the result for reference
        result["url"] = url
        
        # Summarize the result
        status = result["status"]
        text_length = len(result["extracted_text"])
        
        if status == "success":
            logger.info(f"Successfully scraped {url} - Got {text_length} characters")
        else:
            logger.error(f"Failed to scrape {url} - {result['error_message']}")
        
        results.append(result)
    
    # Format the JSON output
    indent = 2 if pretty else None
    json_output = json.dumps(results, indent=indent)
    
    # Output to file or stdout
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_output)
        logger.info(f"Results saved to {output_file}")
    else:
        print(json_output)

def main():
    """Parse command line arguments and run the scraper."""
    parser = argparse.ArgumentParser(description="Web content scraper CLI")
    parser.add_argument("urls", nargs="+", help="One or more URLs to scrape")
    parser.add_argument("-o", "--output", help="Output file for results (JSON format)")
    parser.add_argument("-p", "--pretty", action="store_true", help="Pretty print JSON output")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("-t", "--timeout", type=int, help="Custom timeout in seconds")
    parser.add_argument("-r", "--remove", nargs="+", help="Additional HTML elements to remove (e.g., 'div.ads' 'section.comments')")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        asyncio.run(scrape_urls(args.urls, args.output, args.pretty, args.remove, args.timeout))
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Error running scraper: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 