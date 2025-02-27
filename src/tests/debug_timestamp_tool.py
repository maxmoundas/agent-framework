# src/tests/debug_timestamp_tool.py

# to run this, run: ~ python3 -m src.tests.debug_timestamp_tool

import asyncio
import os
from dotenv import load_dotenv
from ..core.agent import Agent
from ..core.llm_provider import LLMProvider

# Import the timestamp tool to ensure it's registered
from ..tools.implementations.timestamp import TimestampTool

# Load environment variables
load_dotenv()

# Set your API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

async def debug_test():
    # First, let's test the direct LLM response
    llm = LLMProvider(model="gpt-4o-mini")

    system_message = """You are a helpful assistant that can use tools.
    
Available tools:
- TimestampTool: Get the current date and time
  Parameters:
    - format: string (optional)

IMPORTANT: You MUST respond using ONLY the following JSON format:
```json
{
  "tool": "TimestampTool",
  "parameters": {
    "format": "default"
  }
}
```
Do not include any explanations or text outside the JSON structure.
"""
    print("Testing direct LLM response...")
    response = await llm.generate(
        prompt="What time is it now?", system_message=system_message
    )

    print("\nRaw LLM response:")
    print("-" * 40)
    print(response)
    print("-" * 40)

    # Now test with the agent
    print("\nTesting with Agent...")
    agent = Agent(model="gpt-4o-mini")

    result = await agent.run("What's the current time?")
    print("\nAgent result:")
    print("-" * 40)
    print(result)
    print("-" * 40)

if __name__ == "__main__":
    asyncio.run(debug_test())
