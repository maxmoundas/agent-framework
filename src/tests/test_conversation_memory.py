# src/tests/test_conversation_memory.py

# to run this, run: ~ python3 -m src.tests.test_conversation_memory

import asyncio
import os
from dotenv import load_dotenv
from src.core.agent import Agent

# Import tools to register them
from src.tools.implementations.timestamp import TimestampTool

# Load environment variables
load_dotenv()

# Set your API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


async def test_conversation():
    # Initialize agent with a custom system message
    custom_message = """You are a helpful assistant with access to time and date tools. {tools}
    
    When asked about time or date, please use the appropriate tool.
    """

    agent = Agent(model="gpt-4o-mini", custom_system_message=custom_message)

    print("Testing conversation with memory...\n")

    # First query
    print("USER: What time is it now?")
    result1 = await agent.run("What time is it now?")
    print(f"AGENT: {result1}")

    # Follow-up query
    print("\nUSER: Can you show it in ISO format?")
    result2 = await agent.run("Can you show it in ISO format?")
    print(f"AGENT: {result2}")

    print("\nConversation memory test complete!")


if __name__ == "__main__":
    asyncio.run(test_conversation())
