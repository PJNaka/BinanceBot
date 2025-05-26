# backend/tools/web_tools.py
import asyncio
import httpx # For asynchronous HTTP requests
from bs4 import BeautifulSoup # For HTML parsing and cleaning
# lxml is used by BeautifulSoup as a parser, ensure it's installed
from typing import Optional, Dict, Tuple

# Standard User-Agent to mimic a common browser
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
DEFAULT_TIMEOUT = 10  # seconds for HTTP requests

async def fetch_url_content(url: str, timeout: int = DEFAULT_TIMEOUT) -> Tuple[Optional[str], Optional[str]]:
    """
    Asynchronously fetches content from a given URL.
    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.
    Returns:
        A tuple (content, error_message). 
        'content' is the page content if successful and HTML/text, None otherwise.
        'error_message' is a string description of the error if one occurred, None otherwise.
    """
    try:
        async with httpx.AsyncClient(headers={"User-Agent": DEFAULT_USER_AGENT}, follow_redirects=True) as client:
            response = await client.get(url, timeout=timeout)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

            content_type = response.headers.get("content-type", "").lower()
            if "text/html" in content_type or "text/plain" in content_type or "application/json" in content_type or "application/xml" in content_type:
                # It's important to decode using the correct encoding if available,
                # or fall back to a common one like UTF-8.
                # response.text handles this reasonably well.
                return response.text, None
            else:
                return None, f"Unsupported content type: {content_type}. Only HTML, plain text, JSON, or XML are processed."
                
    except httpx.HTTPStatusError as e:
        return None, f"HTTP error occurred: {e.response.status_code} - {e.response.reason_phrase} for URL: {url}"
    except httpx.RequestError as e: # Covers network errors, timeout errors, etc.
        return None, f"Request error occurred: {type(e).__name__} - {str(e)} for URL: {url}"
    except Exception as e: # Catch-all for other unexpected errors
        return None, f"An unexpected error occurred while fetching URL {url}: {str(e)}"

def clean_html_to_text(html_content: str) -> str:
    """
    Cleans HTML content by removing script and style tags, and then extracts readable text.
    Args:
        html_content: The HTML content string.
    Returns:
        A string containing the cleaned text.
    """
    try:
        # Use lxml parser for speed and robustness if available (it's a dependency)
        soup = BeautifulSoup(html_content, 'lxml') 
        
        # Remove script and style tags
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose() # Remove the tag and its content

        # Get text, but try to preserve some structure with separators
        # .get_text(separator=" ", strip=True) is good for general text extraction
        # For more structured text, iterating over elements might be needed.
        text = soup.get_text(separator="\n", strip=True) # Use newline as separator for better readability
        
        # Further cleanups:
        # - Reduce multiple newlines to a single newline
        # - Reduce multiple spaces to a single space (after newlines are handled)
        lines = [line.strip() for line in text.splitlines()]
        cleaned_lines = []
        for line in lines:
            if line: # Only add non-empty lines
                # Replace multiple spaces within a line with a single space
                cleaned_line = ' '.join(line.split())
                cleaned_lines.append(cleaned_line)
        
        return "\n".join(cleaned_lines)
    except Exception as e:
        print(f"Error cleaning HTML: {e}")
        return "" # Return empty string or original content based on desired error handling

async def fetch_and_clean_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetches content from a URL and, if it's HTML, cleans it to extract readable text.
    Args:
        url: The URL to fetch and clean.
        timeout: Request timeout for fetching.
    Returns:
        A tuple (cleaned_text, error_message).
        'cleaned_text' is the extracted text if successful, None otherwise.
        'error_message' describes any error that occurred.
    """
    content, error = await fetch_url_content(url, timeout=timeout)
    if error:
        return None, error
    if content is None: # Should not happen if error is None, but as a safeguard
        return None, "No content fetched, but no explicit error reported."

    # Heuristic: If it looks like HTML (even if content-type was just text/plain sometimes)
    # A more robust check would be to always try parsing and catch errors,
    # or rely strictly on content-type from fetch_url_content.
    # For this implementation, we assume fetch_url_content correctly identifies processable types.
    content_type = "" # We don't have direct access to content-type here unless fetch_url_content returns it
    # Simplification: if it has html tags, assume it's HTML.
    if content.strip().lower().startswith("<html") or content.strip().lower().startswith("<!doctype html"):
        cleaned_text = clean_html_to_text(content)
        return cleaned_text, None
    else:
        # If not HTML (e.g., plain text, JSON, XML), return as is.
        # The agent might want to process these differently.
        return content, None 


# Example usage (for testing, can be run with `python -m backend.tools.web_tools`)
async def main_test():
    print("Testing Web Tools...")

    test_urls = [
        "https://www.google.com/robots.txt", # Plain text
        "https://example.com/", # Simple HTML
        "https://httpstat.us/404", # HTTP error
        "https://nonexistentdomainthatshouldfailresolution.com/", # Network error
        "https://www.python.org/static/img/python-logo.png" # Non-text content
    ]

    for url in test_urls:
        print(f"\n--- Testing URL: {url} ---")
        
        # Test fetch_url_content
        # print("Fetching raw content...")
        # content, error = await fetch_url_content(url)
        # if error:
        #     print(f"  Fetch Error: {error}")
        # elif content:
        #     print(f"  Fetched Content (first 300 chars): {content[:300]}...")
        # else:
        #     print("  No content and no error (should not happen).")

        # Test fetch_and_clean_url
        print("Fetching and cleaning content...")
        cleaned_text, clean_error = await fetch_and_clean_url(url)
        if clean_error:
            print(f"  Fetch/Clean Error: {clean_error}")
        elif cleaned_text:
            print(f"  Cleaned Text (first 300 chars): {cleaned_text[:300]}...")
        else:
            print("  No cleaned text and no error (e.g. unsupported content type not returning error explicitly from fetch_and_clean_url but handled in fetch_url_content).")
    
    # Test clean_html_to_text directly
    print("\n--- Testing clean_html_to_text directly ---")
    sample_html = """
    <html><head><title>Test Page</title><script>alert('hello');</script><style>body{color:red}</style></head>
    <body><h1>Main Title</h1><p>This is a paragraph with a <a href="#">link</a>.</p><div>Some more text.</div></body></html>
    """
    cleaned_sample = clean_html_to_text(sample_html)
    print(f"Original HTML:\n{sample_html}")
    print(f"Cleaned Text:\n{cleaned_sample}")


if __name__ == "__main__":
    asyncio.run(main_test())
