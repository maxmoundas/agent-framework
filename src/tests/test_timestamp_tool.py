# src/tests/test_timestamp_tool.py

# to run this, run: ~ python3 -m src.tests.test_timestamp_tool

import asyncio
import os
from dotenv import load_dotenv
from ..core.agent import Agent

# Import the timestamp tool to ensure it's registered
from src.tools.implementations.timestamp import TimestampTool

# Load environment variables
load_dotenv()

# Set your API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


async def test_timestamp_tool():
    # No need to define tools in the system message - they're automatically included
    # You can still provide a custom message if you want additional instructions
    custom_message = """You are a helpful assistant with access to useful tools. {tools}
    
    When a user asks about the current time or date, always use the TimestampTool.
    Use the appropriate format based on their request.
    """

    # Initialize agent with your preferred model and optional custom message
    agent = Agent(model="gpt-4o-mini", custom_system_message=custom_message)

    print("Testing TimestampTool with the agent...")

    # Test with a simple query
    result1 = await agent.run("What's the current time?")
    print("\nResult (default format):")
    print("-" * 40)
    print(result1)
    print("-" * 40)

    # Test with a specific format
    result2 = await agent.run("Tell me the current time in ISO format")
    print("\nResult (ISO format):")
    print("-" * 40)
    print(result2)
    print("-" * 40)

    print("\nTimestamp tool test complete!")


if __name__ == "__main__":
    asyncio.run(test_timestamp_tool())
