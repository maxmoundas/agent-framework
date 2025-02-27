# Agent Framework

A flexible, extensible framework for building LLM-powered AI agents with tool integration capabilities.

## Overview

This agent framework allows you to:

- Connect to multiple LLM providers (OpenAI, Anthropic) through a unified API
- Create and register custom tools for your agent to use
- Intelligently route queries between direct LLM responses and tool execution
- Maintain conversation context across multiple interactions
- Deploy a user-friendly chat interface with Streamlit

The framework intelligently determines whether to process a query through direct LLM conversation or to use specialized tools, combining the benefits of both approaches.

## Key Features

- **Provider Abstraction**: Uses LiteLLM to support multiple LLM providers
- **Dynamic Tool Registry**: Easily create and register new agent tools
- **Smart Query Routing**: Automatically determines if tools are needed for a query
- **Conversation Memory**: Maintains context across multiple interactions
- **Streamlit UI**: User-friendly chat interface
- **Modular Architecture**: Easily extensible with new capabilities

## Installation

1. Clone the repository:

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your API keys:
```
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
NEWS_API_KEY=your_news_api_key  # for the news tool (optional), key from https://newsapi.org/docs/get-started
```

## Project Structure

```
agent-framework/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py          # Main agent class
│   │   ├── llm_provider.py   # LiteLLM integration
│   │   ├── parser.py         # Response parsing logic
│   │   ├── memory.py         # Conversation memory
│   │   ├── router.py         # Query routing logic
│   │   └── agent_manager.py  # Agent persistence
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py       # Tool registration & discovery
│   │   ├── base.py           # Base tool class 
│   │   └── implementations/  # Individual tools
│   │       ├── __init__.py
│   │       ├── timestamp.py
│   │       └── news.py
│   └── tests/
│       ├── __init__.py
│       ├── test_openai_connection.py
│       ├── test_anthropic_connection.py
│       ├── test_conversation_memory.py
│       ├── test_news_tool.py
│       └── test_timestamp_tool.py
├── app.py                    # Streamlit app
├── tool_test.py              # Tool testing interface
├── .env                      # Environment variables
├── requirements.txt
└── README.md                 # You are here!
```

## Available Tools

The framework comes with two pre-built tools:

1. **TimestampTool**: Provides the current date and time in various formats
2. **NewsTool**: Fetches real news headlines using the NewsAPI (requires API key)

## Usage

### Running the Chat Interface

```bash
streamlit run app.py
```

This launches a Streamlit web interface where you can interact with your agent.

### Testing Tools Directly

```bash
streamlit run tool_test.py
```

This launches a simplified interface specifically for testing tool execution.

### Adding a New Tool

To add a new tool to your agent framework:

1. Create a new Python file in `src/tools/implementations/`
2. Define your tool class inheriting from `BaseTool`
3. Register it using the `@ToolRegistry.register()` decorator

Example:

```python
# src/tools/implementations/calculator.py
from ..base import BaseTool
from ..registry import ToolRegistry
import math

@ToolRegistry.register()
class CalculatorTool(BaseTool):
    description = "Perform mathematical calculations"
    parameters = {
        "expression": {
            "type": "string",
            "description": "The mathematical expression to evaluate"
        }
    }
    
    async def execute(self, expression):
        # A simple calculator with safety measures
        allowed_names = {
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'sqrt': math.sqrt, 'pi': math.pi, 'e': math.e
        }
        
        try:
            # Safe evaluation of math expressions
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return f"The result of {expression} is {result}"
        except Exception as e:
            return f"Error calculating {expression}: {str(e)}"
```

## API Reference

### Agent Class

The main class that processes user queries and manages tool execution.

```python
agent = Agent(model="gpt-4o-mini", custom_system_message=None, memory_turns=10)
response = await agent.run("What time is it?")
```

### ToolRegistry

Handles registration and discovery of available tools.

```python
@ToolRegistry.register()
class MyCustomTool(BaseTool):
    # Tool implementation
    pass

# Get all registered tools
tools = ToolRegistry.list_tools()
```

### BaseTool

Base class for all tools, providing the standard interface.

```python
class MyTool(BaseTool):
    description = "Tool description"
    parameters = {
        "param1": {
            "type": "string",
            "description": "Parameter description",
            "required": True
        }
    }
    
    async def execute(self, param1):
        # Implementation
        return result
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| OPENAI_API_KEY | OpenAI API key | Yes (for OpenAI models) |
| ANTHROPIC_API_KEY | Anthropic API key | Yes (for Claude models) |
| NEWS_API_KEY | NewsAPI key | Optional (for news tool) |

## Dependencies

- litellm: Unified interface for multiple LLM providers
- streamlit: Web interface
- python-dotenv: Environment variable management
- aiohttp: Async HTTP requests
- certifi: SSL certificate verification
