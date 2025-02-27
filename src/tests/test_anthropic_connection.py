# src/tests/test_anthropic_connection.py

# to run this, run: ~ python3 -m src.tests.test_anthropic_connection

import asyncio
import os
from dotenv import load_dotenv
from ..core.llm_provider import LLMProvider

# Load environment variables
load_dotenv()

# Set your Anthropic API key
os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")


async def test_connection():
    # Initialize LLM provider with a Claude model
    # Common Claude models: "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"
    llm = LLMProvider(model="claude-3-haiku-20240307")

    # Custom system message
    system_message = "You are a helpful assistant. Please respond with a simple 'Hello, I am Claude!' so we can verify the connection."

    # Generate response
    print("Sending request to Anthropic via LiteLLM...")
    response = await llm.generate(
        prompt="Please introduce yourself briefly.",
        system_message=system_message,
        temperature=0.7,
    )

    print("\nResponse received:")
    print("-" * 40)
    print(response)
    print("-" * 40)
    print("\nConnection test complete!")


if __name__ == "__main__":
    asyncio.run(test_connection())
