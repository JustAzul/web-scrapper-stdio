#!/usr/bin/env python3
"""Debug script to compare chunked and original processing outputs."""

from src.scraper.helpers.chunked_processor import ChunkedHTMLProcessor
from bs4 import BeautifulSoup

def create_large_html():
    """Create the same large HTML as used in the test - exact match."""
    content_blocks = []
    for i in range(100):  # Reduced from 500 to 100 articles for faster tests
        content_blocks.append(f"""
            <article class="content-block">
                <h2>Article {i}</h2>
                <p>{'Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' * 20}</p>
                <div class="metadata">
                    <span class="author">Author {i}</span>
                    <span class="date">2024-01-{i:02d}</span>
                </div>
                <div class="comments">
                    {'<div class="comment">User comment here...</div>' * 5}
                </div>
            </article>
        """)
    
    return f"""
        <html>
            <head>
                <title>Large Page with Many Articles</title>
                <script>{'// Large script block ' + 'x' * 2000}</script>
                <style>{'/* Large CSS block */ ' + 'a' * 2000}</style>
            </head>
            <body>
                <nav>Navigation that should be removed</nav>
                <header>Header that should be removed</header>
                <main class="content">
                    {''.join(content_blocks)}
                </main>
                <aside>Sidebar that should be removed</aside>
                <footer>Footer that should be removed</footer>
                <script>alert('Should be removed');</script>
            </body>
        </html>
        """

def normalize_text(text):
    """Normalize text for comparison by removing extra whitespace."""
    return ' '.join(text.split())

def compare_outputs():
    """Compare chunked and original processing outputs."""
    processor = ChunkedHTMLProcessor()
    elements_to_remove = ['script', 'style', 'nav', 'header', 'aside', 'footer']
    url = "http://test.com"
    
    large_html = create_large_html()
    
    print("Creating large HTML content...")
    print(f"HTML size: {len(large_html)} characters")
    
    # Get output from original processing
    print("\nRunning original processing...")
    processor.enable_chunking = False
    title_orig, clean_html_orig, text_orig, error_orig, soup_orig = processor.extract_content(
        large_html, elements_to_remove, url
    )
    
    # Get output from chunked processing
    print("Running chunked processing...")
    processor.enable_chunking = True
    title_chunk, clean_html_chunk, text_chunk, error_chunk, soup_chunk = processor.extract_content(
        large_html, elements_to_remove, url
    )
    
    print(f"\nResults:")
    print(f"Original - Title: '{title_orig}', Text length: {len(text_orig)}, Error: {error_orig}")
    print(f"Chunked  - Title: '{title_chunk}', Text length: {len(text_chunk)}, Error: {error_chunk}")
    
    # Write outputs to files for comparison
    with open('original_text.txt', 'w') as f:
        f.write(text_orig)
    
    with open('chunked_text.txt', 'w') as f:
        f.write(text_chunk)
        
    with open('original_html.html', 'w') as f:
        f.write(clean_html_orig)
    
    with open('chunked_html.html', 'w') as f:
        f.write(clean_html_chunk)
    
    # Compare normalized text content
    norm_text_orig = normalize_text(text_orig)
    norm_text_chunk = normalize_text(text_chunk)
    
    print(f"\nNormalized text lengths: Original={len(norm_text_orig)}, Chunked={len(norm_text_chunk)}")
    
    if norm_text_orig == norm_text_chunk:
        print("✅ Text content matches!")
    else:
        print("❌ Text content differs!")
        
        # Find first difference
        min_len = min(len(norm_text_orig), len(norm_text_chunk))
        for i in range(min_len):
            if norm_text_orig[i] != norm_text_chunk[i]:
                print(f"First difference at position {i}:")
                print(f"Original: '{norm_text_orig[max(0, i-20):i+20]}'")
                print(f"Chunked:  '{norm_text_chunk[max(0, i-20):i+20]}'")
                break
        
        # Show article counts
        orig_articles = [i for i in range(100) if f"Article {i}" in text_orig]
        chunk_articles = [i for i in range(100) if f"Article {i}" in text_chunk]
        
        print(f"\nOriginal found articles: {len(orig_articles)} (first 10: {orig_articles[:10]})")
        print(f"Chunked found articles: {len(chunk_articles)} (first 10: {chunk_articles[:10]})")
        
        if len(orig_articles) != len(chunk_articles):
            missing_in_chunk = set(orig_articles) - set(chunk_articles)
            missing_in_orig = set(chunk_articles) - set(orig_articles)
            if missing_in_chunk:
                print(f"Missing in chunked: {sorted(missing_in_chunk)}")
            if missing_in_orig:
                print(f"Missing in original: {sorted(missing_in_orig)}")
    
    print("\nFiles written: original_text.txt, chunked_text.txt, original_html.html, chunked_html.html")

if __name__ == '__main__':
    compare_outputs() 