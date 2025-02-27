# src/tests/test_news_tool.py

# to run this, run: ~ python3 -m src.tests.test_news_tool

import asyncio
import os
from dotenv import load_dotenv
from ..core.agent import Agent

# Import tools to register them
from ..tools.implementations.news import NewsTool

# Load environment variables
load_dotenv()

# Set your API keys
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["NEWS_API_KEY"] = os.getenv("NEWS_API_KEY")


async def test_news_tool():
    # Initialize agent with a custom system message
    custom_message = """You are a helpful assistant that can fetch the latest news. {tools}
    
    When asked about news or current events, use the NewsTool to get up-to-date information.
    Make sure to use any specific categories or keywords the user mentions.
    """

    agent = Agent(model="gpt-4o-mini", custom_system_message=custom_message)

    print("Testing news tool...\n")

    # Test general news
    print("USER: What's in the news today?")
    result1 = await agent.run("What's in the news today?")
    print(f"AGENT: {result1}")

    # Test category-specific news
    print("\nUSER: Tell me the latest technology news")
    result2 = await agent.run("Tell me the latest technology news")
    print(f"AGENT: {result2}")

    # Test keyword search
    print("\nUSER: Any news about weather?")
    result3 = await agent.run("Any news about weather?")
    print(f"AGENT: {result3}")

    print("\nNews tool test complete!")


if __name__ == "__main__":
    asyncio.run(test_news_tool())
