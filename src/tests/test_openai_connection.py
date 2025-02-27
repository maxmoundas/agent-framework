# src/tests/test_openai_connection.py

# to run this, run: ~ python3 -m src.tests.test_openai_connection

import asyncio
import os
from dotenv import load_dotenv
from ..core.llm_provider import LLMProvider

# Load environment variables (assuming you store your API key in a .env file)
load_dotenv()

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


async def test_connection():
    # Initialize LLM provider with gpt-4o-mini model
    llm = LLMProvider(model="gpt-4o-mini")

    # Custom system message
    system_message = "You are a helpful assistant. Please respond with a simple 'Hello, I am GPT-4o-mini!' so we can verify the connection."

    # Generate response
    print("Sending request to OpenAI via LiteLLM...")
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
