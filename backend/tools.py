from duckduckgo_search import DDGS

def search_internet(query: str):
    try:
        print(f"[TOOL] Searching DuckDuckGo for: {query}")
        with DDGS() as ddgs:
            # 'text' generates results based on the query
            results = list(ddgs.text(query, max_results=5))
        
        if not results:
            print("[TOOL] No results found.")
            return ""

        print(f"[TOOL] Found {len(results)} results.")
        
        formatted = []
        for r in results:
            # Safely get data
            title = r.get('title', 'No Title')
            body = r.get('body', 'No Content')
            href = r.get('href', '')
            formatted.append(f"Title: {title}\nSnippet: {body}\nLink: {href}")
        
        return "\n\n".join(formatted)
        
    except Exception as e:
        print(f"[TOOL ERROR] Search failed: {e}")
        return "Search failed due to an exception."