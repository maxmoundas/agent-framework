# src/tools/implementations/news.py
import aiohttp
import os
import ssl
import certifi
from ..base import BaseTool
from ..registry import ToolRegistry


@ToolRegistry.register()
class NewsTool(BaseTool):
    description = "Get today's top news headlines by category or keyword"
    parameters = {
        "query": {
            "type": "string",
            "description": "Optional: Search term or keywords to find specific news",
            "required": False,
        },
        "category": {
            "type": "string",
            "description": "Optional: News category (business, entertainment, general, health, science, sports, technology)",
            "required": False,
        },
        "limit": {
            "type": "integer",
            "description": "Optional: Number of news items to return (default: 5, max: 10)",
            "required": False,
        },
    }

    async def execute(self, query=None, category=None, limit=5):
        # Set a reasonable limit
        if limit > 10:
            limit = 10

        # Get API key from environment
        api_key = os.getenv("NEWS_API_KEY")
        if not api_key:
            return "Error: NEWS_API_KEY not found in environment variables"

        # Build the API URL
        base_url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": api_key,
            "pageSize": limit,
            "language": "en",  # English news
        }

        # Add optional parameters if provided
        if query:
            params["q"] = query
        if category:
            params["category"] = category
        else:
            # Default to general news if no category specified
            params["country"] = "us"  # Use US as default region when no specific query

        try:
            # Create a custom SSL context using certifi's certificates
            ssl_context = ssl.create_default_context(cafile=certifi.where())

            # Create a ClientSession with the SSL context
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=ssl_context)
            ) as session:
                async with session.get(base_url, params=params) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        return f"Error fetching news: {error_data.get('message', 'Unknown error')}"

                    data = await response.json()

                    if data["status"] != "ok":
                        return f"API Error: {data.get('message', 'Unknown error')}"

                    articles = data["articles"]
                    if not articles:
                        return "No news articles found for the given criteria"

                    # Format the results
                    formatted_news = []
                    for i, article in enumerate(articles[:limit], 1):
                        source = article.get("source", {}).get("name", "Unknown Source")
                        title = article.get("title", "No title")
                        url = article.get("url", "#")
                        published = article.get("publishedAt", "Unknown date")

                        # Format each news item
                        news_item = f"{i}. {title}\n   Source: {source} | Published: {published}\n   URL: {url}\n"
                        formatted_news.append(news_item)

                    # Join all formatted news items
                    return "Today's Headlines:\n\n" + "\n".join(formatted_news)

        except Exception as e:
            return f"Error fetching news: {str(e)}"
