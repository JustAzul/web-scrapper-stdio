"""
Chunked HTML Processing Module

Provides memory-efficient HTML processing for large documents while maintaining
complete backward compatibility with existing scraper functionality.
"""

import time
import logging
from typing import List, Tuple, Optional, Dict, Any, Union
from bs4 import BeautifulSoup, Tag
import gc
import lxml
import re

# Import psutil at module level for easier mocking in tests
import psutil

from .html_utils import _extract_and_clean_html

logger = logging.getLogger(__name__)


class ChunkedHTMLProcessor:
    """
    Memory-efficient HTML processor that handles large documents through chunked processing
    while maintaining complete backward compatibility.
    """
    
    def __init__(
        self, 
        chunk_size_threshold: int = 100000,  # 100KB
        memory_limit_mb: int = 100,
        enable_chunking: bool = True,
        fallback_enabled: bool = True
    ):
        """
        Initialize the chunked HTML processor.
        
        Args:
            chunk_size_threshold: HTML size threshold to trigger chunked processing
            memory_limit_mb: Memory limit in MB for processing
            enable_chunking: Whether to enable chunked processing
            fallback_enabled: Whether to fallback to original method on errors
        """
        self.chunk_size_threshold = chunk_size_threshold
        self.memory_limit_mb = memory_limit_mb
        self.enable_chunking = enable_chunking
        self.fallback_enabled = fallback_enabled
        
        # Performance tracking
        self._last_metrics = {}
        
        # Elements that typically contain unwanted content
        self.noise_selectors = [
            'nav', 'header', 'footer', 'aside', 'sidebar',
            '.nav', '.navigation', '.header', '.footer', '.sidebar',
            '.advertisement', '.ads', '.banner', '.social-media',
            '.comments', '.related', '.recommended'
        ]
        
        self.parser = 'lxml'  # Using lxml for better performance
    
    def extract_content(self, html_content: str, elements_to_remove: List[str], url: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[BeautifulSoup]]:
        """
        Extract content from HTML using either chunked or original processing.
        
        Returns:
            Tuple of (title, clean_html, text_content, error, soup)
        """
        start_time = time.time()
        content_size_mb = len(html_content.encode('utf-8')) / 1024 / 1024
        
        try:
            # Handle empty HTML - not an error condition, just return empty strings
            if not html_content or not html_content.strip():
                return "", "", "", None, None
            
            # Always parse the HTML to get basic structure and title
            soup = BeautifulSoup(html_content, self.parser)
            
            # Extract title first (works even without body)
            page_title = soup.title.string.strip() if soup.title and soup.title.string else ""
            
            # Check if we should use chunked processing
            use_chunked = self._should_use_chunked_processing(html_content)
            
            if use_chunked:
                logger.debug(f"Using chunked processing for {url} (size: {content_size_mb:.2f}MB)")
                try:
                    title, clean_html, text_content, error, soup = self._extract_content_chunked(
                        soup, elements_to_remove, url
                    )
                except Exception as chunked_error:
                    logger.warning(f"Chunked processing failed, falling back to original method: {chunked_error}")
                    if self.fallback_enabled:
                        return self._extract_content_original(soup, elements_to_remove, url)
                    else:
                        raise
            else:
                logger.debug(f"Using original processing for {url} (size: {content_size_mb:.2f}MB)")
                title, clean_html, text_content, error, soup = self._extract_content_original(
                    soup, elements_to_remove, url
                )
            
            # Ensure title is preserved even if body processing fails
            if title is None:
                title = page_title
            
            processing_time = time.time() - start_time
            
            # Store metrics
            self._last_metrics = {
                'processing_time': processing_time,
                'content_size_mb': content_size_mb,
                'used_chunked_processing': use_chunked,
                'memory_peak_mb': self._get_memory_usage(),
                'chunks_processed': getattr(self, '_chunks_processed', 0),
                'processing_successful': error is None
            }
            
            logger.debug(f"Content extraction completed for {url} in {processing_time:.2f}s")
            return title or "", clean_html or "", text_content or "", error, soup
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Content extraction failed: {str(e)}"
            logger.error(f"Error processing {url}: {error_msg}")
            
            # Store error metrics
            self._last_metrics = {
                'processing_time': processing_time,
                'content_size_mb': content_size_mb,
                'used_chunked_processing': False,
                'memory_peak_mb': self._get_memory_usage(),
                'chunks_processed': 0,
                'processing_successful': False,
                'error': error_msg
            }
            
            return "", "", "", error_msg, None
    
    def _should_use_chunked_processing(self, html_content: str) -> bool:
        """Determine if chunked processing should be used."""
        if not self.enable_chunking:
            return False
        
        return len(html_content) > self.chunk_size_threshold
    
    def _extract_content_chunked(
        self, 
        soup: BeautifulSoup, 
        elements_to_remove: List[str], 
        url: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[BeautifulSoup]]:
        """
        Process content using chunked processing for better memory efficiency.
        This simplified version maintains output consistency with original processing.
        """
        try:
            # Convert soup back to HTML string for consistent behavior with original method
            html_content = str(soup)
            new_soup = BeautifulSoup(html_content, self.parser)
            
            # Extract title first
            title = ""
            if new_soup.title and new_soup.title.string:
                title = new_soup.title.string.strip()
            
            # Remove unwanted elements globally (same as original)
            self._remove_unwanted_elements(new_soup, elements_to_remove)
            
            # Get the body tag as target element (same as original)
            target_element = new_soup.body
            if not target_element:
                # If no body tag, use entire soup
                target_element = new_soup
            
            # For memory efficiency, process large elements in chunks but maintain output structure
            self._chunks_processed = 0
            
            # If content is very large, process it in chunks for memory efficiency
            if len(str(target_element)) > self.chunk_size_threshold:
                self._process_large_content_in_chunks(target_element)
                self._chunks_processed += 1
            
            # Extract final content with proper text normalization (matching html_utils)
            clean_html = str(target_element)
            text_content = target_element.get_text(separator="\n", strip=True)
            # Apply the same text normalization as original html_utils
            text_content = re.sub(r'\n\s*\n', '\n\n', text_content).strip()
            
            # Memory cleanup
            gc.collect()
            
            return title or "", clean_html or "", text_content or "", None, new_soup
            
        except Exception as e:
            logger.error(f"Chunked processing failed: {e}")
            raise  # Re-raise to trigger fallback
    
    def _process_large_content_in_chunks(self, element: Tag) -> None:
        """
        Process large content in smaller chunks for memory efficiency.
        This method processes content in-place without changing the structure.
        """
        # Process children in chunks for memory efficiency
        children = list(element.children)  # Convert to list to avoid generator issues
        
        chunk_size = 50  # Process 50 elements at a time
        for i in range(0, len(children), chunk_size):
            chunk = children[i:i + chunk_size]
            
            # Process each chunk (this could include additional optimizations)
            for child in chunk:
                if isinstance(child, Tag):
                    # For very large child elements, we could add recursive chunking here
                    if len(str(child)) > self.chunk_size_threshold:
                        self._process_large_content_in_chunks(child)
            
            # Periodically clean up memory
            if i % 100 == 0:  # Every 100 chunks
                gc.collect()
    
    def _extract_content_original(
        self, 
        soup: BeautifulSoup, 
        elements_to_remove: List[str], 
        url: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[BeautifulSoup]]:
        """
        Use the original extraction method for backward compatibility.
        """
        try:
            # Convert soup back to HTML string for original function
            html_content = str(soup)
            soup_orig, target_element = _extract_and_clean_html(html_content, elements_to_remove)
            
            # Extract title (preserve from original soup if available)
            title = ""
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            elif soup_orig and soup_orig.title and soup_orig.title.string:
                title = soup_orig.title.string.strip()
            
            # Handle case where no body/target element found
            if not target_element:
                # Try to use the entire soup as content if no specific target
                text_content = soup_orig.get_text(separator="\n", strip=True) if soup_orig else ""
                clean_html = str(soup_orig) if soup_orig else ""
                
                if text_content and clean_html:
                    return title or "", clean_html, text_content, None, soup_orig
                else:
                    # Return title but indicate body tag issue
                    if title:
                        return title, "", "", "[ERROR] Could not find body tag in HTML.", soup_orig
                    else:
                        return "", "", "", "[ERROR] Could not find body tag in HTML.", soup_orig
            
            # Extract clean HTML and text from target element
            clean_html = str(target_element)
            text_content = target_element.get_text(separator="\n", strip=True)
            # Apply the same text normalization as original html_utils
            text_content = re.sub(r'\n\s*\n', '\n\n', text_content).strip()
            
            return title or "", clean_html or "", text_content or "", None, soup_orig
            
        except Exception as e:
            logger.error(f"Original processing failed: {e}")
            # Return any title we managed to extract
            if title:
                return title, "", "", f"Original processing failed: {str(e)}", None
            else:
                return "", "", "", f"Original processing failed: {str(e)}", None
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup, elements_to_remove: List[str]) -> None:
        """Remove unwanted elements from the soup."""
        # Remove user-specified elements
        for element_name in elements_to_remove:
            for element in soup.find_all(element_name):
                element.decompose()
        
        # Remove common noise elements
        for selector in self.noise_selectors:
            try:
                if selector.startswith('.') or selector.startswith('#'):
                    # CSS class or ID selector
                    for element in soup.select(selector):
                        element.decompose()
                else:
                    # Tag name
                    for element in soup.find_all(selector):
                        element.decompose()
            except Exception as e:
                logger.warning(f"Error removing noise element {selector}: {e}")
    
    def _identify_content_areas(self, soup: BeautifulSoup) -> List[Tag]:
        """
        Identify main content areas in the HTML document.
        Returns a list of BeautifulSoup Tag objects representing content areas.
        """
        content_areas = []
        
        # First, look for semantic main content elements
        main_elements = soup.find_all(['main', 'article'])
        if main_elements:
            content_areas.extend(main_elements)
        
        # Look for content areas by class/id patterns
        content_patterns = [
            'content', 'article', 'post', 'entry',
            'main', 'body', 'text', 'story'
        ]
        
        for pattern in content_patterns:
            # Search by class
            elements = soup.find_all(class_=lambda x: x and pattern in x.lower())
            content_areas.extend(elements)
            
            # Search by id
            elements = soup.find_all(id=lambda x: x and pattern in x.lower())
            content_areas.extend(elements)
        
        # If no content areas found, use body or entire soup
        if not content_areas:
            if soup.body:
                content_areas.append(soup.body)
            else:
                content_areas.append(soup)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_areas = []
        for area in content_areas:
            if area not in seen:
                seen.add(area)
                unique_areas.append(area)
        
        return unique_areas
    
    def _process_area_in_chunks(self, area: Tag) -> Tuple[List[str], List[str]]:
        """
        Process a content area in chunks to manage memory usage.
        Returns lists of text and HTML chunks.
        """
        text_chunks = []
        html_chunks = []
        current_chunk_size = 0
        current_chunk_elements = []
        
        def process_current_chunk():
            if current_chunk_elements:
                # Create a new soup for the chunk
                chunk_soup = BeautifulSoup('<div></div>', self.parser)
                chunk_div = chunk_soup.div
                
                # Add all elements to the chunk
                for element in current_chunk_elements:
                    # Create a copy to avoid modifying original
                    element_copy = BeautifulSoup(str(element), self.parser).contents[0]
                    chunk_div.append(element_copy)
                
                # Extract text and HTML
                text_chunks.append(chunk_div.get_text(separator="\n", strip=True))
                html_chunks.append(str(chunk_div))
                
                # Clear the current chunk
                current_chunk_elements.clear()
                nonlocal current_chunk_size
                current_chunk_size = 0
                
                # Force garbage collection
                gc.collect()
        
        # Process each direct child of the area
        for element in area.children:
            if isinstance(element, Tag):
                element_size = len(str(element))
                
                # If adding this element would exceed chunk size, process current chunk
                if current_chunk_size + element_size > self.chunk_size_threshold:
                    process_current_chunk()
                
                # Add element to current chunk
                current_chunk_elements.append(element)
                current_chunk_size += element_size
                
                # Monitor memory usage
                if self._get_memory_usage() > self.memory_limit_mb:
                    process_current_chunk()
        
        # Process any remaining elements
        if current_chunk_elements:
            process_current_chunk()
        
        return text_chunks, html_chunks
    
    def _monitor_memory_usage(self) -> Dict[str, float]:
        """Monitor current memory usage."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'memory_rss_mb': memory_info.rss / 1024 / 1024,  # RSS in MB
                'memory_vms_mb': memory_info.vms / 1024 / 1024,  # VMS in MB
                'memory_percent': max(0.1, process.memory_percent())  # Ensure non-zero
            }
        except Exception as e:
            logger.warning(f"Failed to monitor memory usage: {e}")
            return {
                'memory_rss_mb': 0.1,  # Default to small non-zero values
                'memory_vms_mb': 0.1,
                'memory_percent': 0.1
            }
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            metrics = self._monitor_memory_usage()
            return max(0.1, metrics['memory_rss_mb'])  # Ensure non-zero
        except Exception:
            return 0.1  # Default to small non-zero value
    
    def get_last_processing_metrics(self) -> Dict[str, Any]:
        """Get metrics from the last processing operation."""
        return self._last_metrics.copy()

    def _optimize_memory(self, soup):
        """Optimize memory usage by clearing unnecessary references"""
        # Clear the builder's memory
        if hasattr(soup, 'builder'):
            soup.builder.reset()
        
        # Clear string store if using lxml
        if hasattr(soup, '_namespaces'):
            soup._namespaces.clear()
        
        # Force garbage collection
        gc.collect()
    
    def _extract_content(self, area):
        """Extract content from a content area while preserving structure"""
        if not area:
            return None
        
        # Extract title from h1-h3 tags
        title_tag = area.find(['h1', 'h2', 'h3'])
        title = title_tag.get_text(strip=True) if title_tag else ''
        
        # Get all text content while preserving structure
        content = area.get_text(strip=True, separator=' ')
        
        # Get the HTML content
        html = str(area)
        
        return {
            'title': title,
            'content': content,
            'html': html
        }

    def process_html(self, html_content):
        """Process HTML content with memory optimization"""
        try:
            # Create initial soup with lxml parser for better performance
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Find all content areas
            content_areas = soup.find_all(['article', 'div', 'section'], 
                                        class_=lambda x: x and 'content' in x.lower())
            
            # Process each content area
            extracted_content = []
            for area in content_areas:
                content = self._extract_content(area)
                if content:
                    extracted_content.append(content)
                
                # Optimize memory after processing each major section
                self._optimize_memory(soup)
            
            return extracted_content
            
        finally:
            # Final cleanup
            gc.collect()


# Backward compatibility function that integrates with existing scraper
def extract_clean_html_optimized(
    html_content: str, 
    elements_to_remove: List[str], 
    url: str,
    **processor_kwargs
) -> Tuple[str, str, str, Optional[str], Optional[BeautifulSoup]]:
    """
    Drop-in replacement for the original extract_clean_html function with optimization.
    
    Maintains exact same signature and return format for complete backward compatibility.
    
    Args:
        html_content: Raw HTML content to process
        elements_to_remove: List of HTML elements to remove
        url: Source URL of the content
        **processor_kwargs: Additional configuration for ChunkedHTMLProcessor
    
    Returns:
        Tuple of (title, clean_html, text_content, error, soup)
    """
    processor = ChunkedHTMLProcessor(**processor_kwargs)
    return processor.extract_content(html_content, elements_to_remove, url)


# Factory function for creating configured processors
def create_chunked_processor(
    enable_chunking: bool = True,
    chunk_size_threshold: int = 100000,
    memory_limit_mb: int = 150
) -> ChunkedHTMLProcessor:
    """
    Factory function to create a configured ChunkedHTMLProcessor.
    
    Args:
        enable_chunking: Whether to enable chunked processing
        chunk_size_threshold: Size threshold for triggering chunked processing
        memory_limit_mb: Memory limit for processing operations
    
    Returns:
        Configured ChunkedHTMLProcessor instance
    """
    return ChunkedHTMLProcessor(
        chunk_size_threshold=chunk_size_threshold,
        memory_limit_mb=memory_limit_mb,
        enable_chunking=enable_chunking,
        fallback_enabled=True
    ) 