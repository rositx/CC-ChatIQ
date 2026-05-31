import pytest
from backend.utils.text import chunk_text, scrape_web_page

def test_chunk_text_boundaries_and_overlaps():
    """Verify that chunk_text returns segments with requested overlaps and limits."""
    words = [f"word{i}" for i in range(1000)]
    sample = " ".join(words)
    
    chunks = chunk_text(sample, chunk_size=512, overlap=64)
    
    assert len(chunks) > 1
    # Verify first chunk has 512 words
    assert len(chunks[0].split()) == 512
    # Verify second chunk has overlap
    words_first = chunks[0].split()
    words_second = chunks[1].split()
    # The last 64 words of first chunk should equal the first 64 words of second chunk
    assert words_first[-64:] == words_second[:64]

def test_scrape_web_page_strips_tags():
    """Verify HTML scraper strips scripting and returns normalized text."""
    html = """
    <html>
      <head><title>Test Title</title></head>
      <body>
        <nav>Navigation links here</nav>
        <script>alert('malicious')</script>
        <style>body { color: red; }</style>
        <h1>Main Heading</h1>
        <p>This is the core content paragraph.</p>
        <footer>Footer info</footer>
      </body>
    </html>
    """
    cleaned = scrape_web_page(html)
    assert "alert" not in cleaned
    assert "Navigation" not in cleaned
    assert "Footer" not in cleaned
    assert "Main Heading" in cleaned
    assert "core content paragraph." in cleaned
