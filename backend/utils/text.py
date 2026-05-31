import logging
from bs4 import BeautifulSoup
import pypdf
from typing import List, BinaryIO

logger = logging.getLogger("text_utils")

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    """Chunks text into word/token blocks with a specified overlap size."""
    words = text.strip().split()
    if not words:
        return []
        
    chunks = []
    step = chunk_size - overlap
    if step <= 0:
        step = chunk_size
        
    for i in range(0, len(words), step):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        # If we have reached the end of the text, stop
        if i + chunk_size >= len(words):
            break
            
    return chunks

def scrape_web_page(html_content: str) -> str:
    """Parses raw HTML, stripping script, style, nav, header, and footer tags."""
    soup = BeautifulSoup(html_content, "html.parser")
    # Decompose irrelevant nodes
    for element in soup(["script", "style", "nav", "header", "footer"]):
        element.decompose()
        
    # Return normalized text content
    return " ".join(soup.get_text().split())

def extract_text_from_pdf(pdf_file: BinaryIO) -> str:
    """Extracts raw text page by page from a binary PDF buffer."""
    try:
        reader = pypdf.PdfReader(pdf_file)
        text_content = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
        return " ".join(" ".join(text_content).split())
    except Exception as e:
        logger.error(f"Failed to parse PDF document: {str(e)}")
        raise ValueError(f"Corrupt or invalid PDF: {str(e)}")
