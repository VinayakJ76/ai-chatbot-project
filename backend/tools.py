from duckduckgo_search import DDGS

def search_internet(query: str):
    try:
        # DDGS context manager
        with DDGS() as ddgs:
            # Use .text() method instead of calling ddgs() directly
            results = list(ddgs.text(query, max_results=3))
        
        formatted = []
        for r in results:
            # Structure: {'title': '...', 'href': '...', 'body': '...'}
            formatted.append(f"Source: {r['title']}\nSnippet: {r['body']}")
        
        return "\n\n".join(formatted)
    except Exception as e:
        print(f"Search error: {e}")
        return "Search failed or timed out."