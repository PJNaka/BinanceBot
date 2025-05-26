# backend/tools/search_tool.py
import asyncio
import os
from typing import List, Dict, Any, Optional

# Attempt to import TavilyClient and config
try:
    from tavily import TavilyClient
    from ..config import TAVILY_API_KEY # Relative import from parent package
except ImportError:
    # This allows the file to be run standalone for testing without full package structure,
    # or if tavily-python is not installed yet in some environments.
    print("Warning: TavilyClient or TAVILY_API_KEY could not be imported. Search tool will not function.")
    TavilyClient = None
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "mock_tavily_api_key_for_testing_if_not_set") # Fallback for standalone


# Initialize TavilyClient
# It's better to initialize it once if the API key is available.
# If TAVILY_API_KEY is None or empty, the client might raise an error or not work.
tavily_client: Optional[TavilyClient] = None
if TavilyClient and TAVILY_API_KEY and TAVILY_API_KEY != "your_tavily_api_key_here" and TAVILY_API_KEY != "mock_tavily_api_key_for_testing_if_not_set":
    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        # print("TavilyClient initialized successfully.")
    except Exception as e:
        print(f"Error initializing TavilyClient: {e}")
        tavily_client = None
else:
    if TAVILY_API_KEY == "your_tavily_api_key_here" or TAVILY_API_KEY == "mock_tavily_api_key_for_testing_if_not_set":
        print("Info: TavilyClient not initialized because TAVILY_API_KEY is a placeholder or mock value.")
    elif not TavilyClient:
        pass # Warning already printed
    else:
        print("Warning: TavilyClient not initialized. TAVILY_API_KEY might be missing or empty.")


async def tavily_search(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """
    Performs a web search using the Tavily API.
    Args:
        query: The search query string.
        max_results: The maximum number of search results to return.
    Returns:
        A list of search result dictionaries, each containing 'title', 'url', and 'content'.
        Returns an empty list if an error occurs or no results are found.
    """
    if not tavily_client:
        print("Error: TavilyClient is not initialized. Cannot perform search.")
        # Optionally, could return a specific error structure or raise an exception.
        return [{"error": "TavilyClient not initialized. API key may be missing or invalid.", "title": "Search Error", "url": "", "content": ""}]

    try:
        # Use asyncio.to_thread to run the synchronous Tavily client call in a separate thread,
        # making it non-blocking for the asyncio event loop.
        # print(f"Performing Tavily search for: '{query}', max_results={max_results}")
        # The Tavily client's search method might return various structures.
        # We are interested in 'results' which is typically a list of dicts.
        # Common keys in results: 'title', 'url', 'content', 'score', 'raw_content', etc.
        response = await asyncio.to_thread(
            tavily_client.search,
            query=query,
            search_depth="basic",  # Or "advanced" for more detailed results (consumes more credits)
            max_results=max_results,
            # include_domains = [], # Optional: to limit search to specific domains
            # exclude_domains = [], # Optional: to exclude domains
        )
        
        # Ensure 'results' key exists and is a list
        search_results = response.get("results", []) if isinstance(response, dict) else []
        
        # Format results to include only title, url, and content (or snippet)
        formatted_results: List[Dict[str, Any]] = []
        if isinstance(search_results, list):
            for result in search_results:
                if isinstance(result, dict):
                    formatted_results.append({
                        "title": result.get("title", "No title"),
                        "url": result.get("url", "#"),
                        "content": result.get("content", result.get("raw_content", "No content snippet available")) # Prioritize 'content'
                    })
        
        # print(f"Tavily search returned {len(formatted_results)} formatted results.")
        return formatted_results

    except Exception as e:
        print(f"Error during Tavily search for query '{query}': {e}")
        # Return a list with a single error entry, or an empty list based on desired error handling
        return [{"error": str(e), "title": "Search API Error", "url": "", "content": ""}]


# Example usage (for testing, can be run with `python -m backend.tools.search_tool`)
async def main_test():
    print("Testing Tavily Search Tool...")
    if not tavily_client:
        print("Tavily client not initialized. Ensure TAVILY_API_KEY is set in config or environment for testing.")
        print("If TAVILY_API_KEY is set and this message appears, there might have been an init error.")
        # For local testing without a real key, you might mock the client or expect empty/error results.
        # This test will proceed assuming the client *might* be mocked or a placeholder key is being used,
        # leading to an expected error or empty result from the search function.
    
    test_query = "What is the capital of France?"
    print(f"Searching for: '{test_query}'")
    results = await tavily_search(test_query, max_results=2)
    
    if results and "error" not in results[0]:
        print(f"\nFound {len(results)} results:")
        for i, result in enumerate(results):
            print(f"Result {i+1}:")
            print(f"  Title: {result.get('title')}")
            print(f"  URL: {result.get('url')}")
            print(f"  Content Snippet: {result.get('content', '')[:200]}...") # Print first 200 chars of content
            print("-" * 20)
    elif results and "error" in results[0]:
        print(f"Search failed with error: {results[0]['error']}")
    else:
        print("Search returned no results or an unhandled error structure.")

    # Test with a query that might not have many direct results or uses advanced features (conceptually)
    test_query_complex = "latest advancements in quantum computing QML"
    print(f"\nSearching for: '{test_query_complex}'")
    results_complex = await tavily_search(test_query_complex, max_results=1)
    if results_complex and "error" not in results_complex[0]:
        print(f"\nFound {len(results_complex)} results for complex query:")
        for result in results_complex:
            print(f"  Title: {result.get('title')}, URL: {result.get('url')}")
    elif results_complex and "error" in results_complex[0]:
         print(f"Search failed with error: {results_complex[0]['error']}")
    else:
        print("Search for complex query returned no results or an unhandled error structure.")

if __name__ == "__main__":
    # This allows running `python -m backend.tools.search_tool` to test the functions.
    # Ensure you have a Tavily API key set in your environment or .env file for this test to work.
    # (Or it will use the mock key and the client won't be truly initialized)
    asyncio.run(main_test())
