# src/core/agent.py
import json
from .llm_provider import LLMProvider
from .parser import OutputParser
from .memory import ConversationMemory
from .router import QueryRouter
from ..tools.registry import ToolRegistry
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Agent")


class Agent:

    def __init__(
        self, model="gpt-3.5-turbo", custom_system_message=None, memory_turns=10
    ):
        self.model = model
        self.llm = LLMProvider(model=model)
        self.parser = OutputParser()
        self.memory = ConversationMemory(max_turns=memory_turns)
        self.custom_system_message = custom_system_message
        self.system_message = self._build_system_message()
        self.router = QueryRouter(model=model)

    def _build_system_message(self):
        """Dynamically build system message with all registered tools"""
        tool_specs = ToolRegistry.get_tool_specs()

        # Format tools for display in the system message
        tools_description = []
        for name, spec in tool_specs.items():
            param_desc = []
            for param_name, param_details in spec.get("parameters", {}).items():
                required = param_details.get("required", True)
                param_type = param_details.get("type", "string")
                param_desc.append(
                    f"    - {param_name}: {param_type}{' (optional)' if not required else ''}"
                )

            tools_description.append(
                f"- {name}: {spec.get('description', '')}\n  Parameters:\n"
                + "\n".join(param_desc)
            )

        tools_str = "\n".join(tools_description)

        # Use custom system message if provided, otherwise use default
        base_message = (
            self.custom_system_message.replace("{tools}", tools_str)
            if self.custom_system_message
            else f"""You are a helpful AI assistant with access to specialized tools. {tools_str}

    WHEN TO USE TOOLS:
    - Use tools ONLY when the user's question specifically requires their functionality
    - For general conversation, questions, or advice, DO NOT use tools
    - For time and date queries, use the TimestampTool
    - For news and current events, use the NewsTool
    - For all other queries, respond conversationally without using tools

    TOOL USAGE FORMAT:
    When you need to use a tool, respond using the following JSON format:
    ```json
    {{
    "tool": "tool_name",
    "parameters": {{
        "param1": "value1",
        "param2": "value2"
    }}
    }}
    ```
    """
        )
        return base_message

    def __getstate__(self):
        """Make sure agent can be pickled"""
        state = self.__dict__.copy()
        # Don't pickle the LLM provider (will be recreated on load)
        state.pop("llm", None)
        return state

    def __setstate__(self, state):
        """Restore state when unpickled"""
        self.__dict__.update(state)
        # Recreate the LLM provider
        self.llm = LLMProvider(model=self.model)

    async def run(self, user_input):
        """Main entry point for processing user input"""
        # Add user input to memory
        self.memory.add_user_message(user_input)

        # Check if we should use tools for this query
        use_tool, suggested_tool = await self.router.should_use_tools(user_input)

        # If tool execution is recommended and we have a specific tool
        if use_tool and suggested_tool:
            # Process with tools, which now includes LLM response to tool output
            return await self._process_with_tools(user_input, suggested_tool)
        elif use_tool:
            # Generic tool execution needed
            return await self._process_with_tools(user_input)
        else:
            # Process as conversation, but include recent tool results for context
            return await self._process_conversation(user_input)

    # src/core/agent.py - update the _process_conversation method


    async def _process_conversation(self, user_input):
        """Process user input as a normal conversation, but include relevant tool results"""
        # Get conversation history
        conversation_history = self.memory.get_conversation_history()

        # Get recent tool results for context
        recent_tools = self.memory.get_recent_tool_results(limit=2)

        # Build a conversational system message
        conv_system_message = """You are a helpful, friendly AI assistant. Provide informative, 
        thoughtful responses to the user's questions."""

        # If we have recent tool results, include them in the prompt
        tool_context = ""
        if recent_tools:
            tool_context = "\n\nRecent information from tools that may be relevant:\n"
            for tool_info in recent_tools:
                tool_context += (
                    f"- From {tool_info['tool']}: {tool_info['result'][:200]}...\n"
                )

            conv_system_message += tool_context

        # Get response from LLM using conversation history and any tool context
        response = await self.llm.generate(
            system_message=conv_system_message, conversation_history=conversation_history
        )

        # Add response to memory
        self.memory.add_assistant_message(response)
        return response

    async def _process_with_tools(self, user_input, suggested_tool=None):
        """Process user input using tools and then have the LLM respond with the tool results"""
        # Get conversation history
        conversation_history = self.memory.get_conversation_history()

        # Create a strongly directive prompt for tool usage if needed
        tool_directive = ""
        if suggested_tool:
            tool_specs = ToolRegistry.get_tool_specs()
            if suggested_tool in tool_specs:
                tool_info = tool_specs[suggested_tool]
                params = tool_info.get("parameters", {})
                param_names = list(params.keys())

                # Create parameter examples
                param_examples = {}
                for param, details in params.items():
                    if param == "format" and suggested_tool == "TimestampTool":
                        param_examples[param] = "default"
                    elif param == "query" and suggested_tool == "MockNewsTool":
                        param_examples[param] = "technology"
                    elif param == "category" and suggested_tool == "MockNewsTool":
                        param_examples[param] = "technology"
                    elif param == "limit":
                        param_examples[param] = 5
                    else:
                        param_examples[param] = ""

                # Create directive
                tool_directive = f"""
IMPORTANT: The user's query requires using the {suggested_tool}.
You MUST respond ONLY with the following JSON format to use this tool:

```json
{{
"tool": "{suggested_tool}",
"parameters": {json.dumps(param_examples)}
}}
```
Do not include any other text or explanations. Only return the JSON.
"""
        # Add the directive to the system message
        enhanced_system_message = self.system_message
        if tool_directive:
            enhanced_system_message = tool_directive + "\n\n" + self.system_message

        # Get response from LLM using conversation history and enhanced system message
        tool_response = await self.llm.generate(
            system_message=enhanced_system_message,
            prompt=user_input,
            temperature=0.2,  # Lower temperature for more consistent tool usage
        )

        # Parse the response
        action = await self.parser.parse_json(tool_response)

        # If we have a valid action, execute the tool
        tool_result = None
        if "tool" in action and "parameters" in action:
            tool_name = action["tool"]
            params = action["parameters"]

            # Get the tool class and instantiate it
            tool_class = ToolRegistry.get_tool(tool_name)
            if not tool_class:
                error_msg = f"Error: Tool '{tool_name}' not found"
                self.memory.add_assistant_message(error_msg)
                return error_msg

            # Execute the tool
            tool = tool_class()
            tool_result = await tool.execute(**params)

            # Store the tool execution in memory (but don't add to assistant message yet)
            self.memory.add_tool_result(tool_name, tool_result)

        # If direct execution of suggested tool is needed
        if not tool_result and suggested_tool:
            tool_class = ToolRegistry.get_tool(suggested_tool)
            if tool_class:
                tool = tool_class()

                # Execute with appropriate defaults based on tool type
                if suggested_tool == "TimestampTool":
                    tool_result = await tool.execute()
                elif "NewsTool" in suggested_tool:
                    # Extract potential category from user input
                    category = None
                    if (
                        "technology" in user_input.lower()
                        or "tech" in user_input.lower()
                    ):
                        category = "technology"
                    elif "business" in user_input.lower():
                        category = "business"
                    elif "sports" in user_input.lower():
                        category = "sports"

                    tool_result = await tool.execute(category=category)

        # If we got a tool result, have the LLM provide a response that incorporates it
        if tool_result:
            # Create a prompt for the LLM to respond to the tool result
            followup_prompt = f"""The user asked: "{user_input}"
I've retrieved the following information:
{tool_result}

Please provide a helpful response to the user's query using this information."""

            final_response = await self.llm.generate(
                prompt=followup_prompt, conversation_history=conversation_history
            )

            # Store the final response in memory
            self.memory.add_assistant_message(final_response)
            return final_response

        # If no tool result, just return the original LLM response
        self.memory.add_assistant_message(tool_response)
        return tool_response
