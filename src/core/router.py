# src/core/router.py
import json
from .llm_provider import LLMProvider
from ..tools.registry import ToolRegistry


class QueryRouter:
    def __init__(self, model="gpt-4o-mini"):
        self.llm = LLMProvider(model=model)
        self.tools_info = self._get_tools_info()

    def _get_tools_info(self):
        """Get information about available tools for routing decisions"""
        tool_specs = ToolRegistry.get_tool_specs()
        tools_info = []

        for name, spec in tool_specs.items():
            tools_info.append(
                {
                    "name": name,
                    "description": spec.get("description", ""),
                    "capabilities": self._derive_capabilities(spec),
                }
            )

        return tools_info

    def _derive_capabilities(self, tool_spec):
        """Derive tool capabilities from its description and parameters"""
        capabilities = []
        description = tool_spec.get("description", "").lower()

        # Add keyword-based capabilities
        if "time" in description or "date" in description:
            capabilities.extend(["current time", "current date", "timestamp"])

        if "news" in description:
            capabilities.extend(["news", "headlines", "current events"])

        # Add more tool-specific capability detection logic here

        return capabilities

    async def should_use_tools(self, query):
        """Determine if the query should use tools"""
        if not self.tools_info:
            return False, None
        
        # Create a prompt for the router decision with examples
        tool_descriptions = "\n".join([
            f"- {tool['name']}: {tool['description']}" 
            for tool in self.tools_info
        ])
        
        router_prompt = f"""You are a query router that determines if a user query should be handled using specialized tools.

Available tools:
{tool_descriptions}

EXAMPLES:
1. User query: "What time is it now?"
Decision: {{"use_tool": true, "tool_name": "TimestampTool", "reasoning": "This query is asking for the current time."}}

2. User query: "Tell me about the history of Rome."
Decision: {{"use_tool": false, "tool_name": null, "reasoning": "This is a general knowledge question that doesn't require real-time data or specialized tools."}}

3. User query: "What's in the news today?"
Decision: {{"use_tool": true, "tool_name": "NewsTool", "reasoning": "This query is asking for current news which requires the news tool."}}

4. User query: "I'm feeling sad today."
Decision: {{"use_tool": false, "tool_name": null, "reasoning": "This is a conversational statement that requires empathy, not a tool."}}

5. User query: "Can you show me the latest technology news?"
Decision: {{"use_tool": true, "tool_name": "NewsTool", "reasoning": "This query is asking for specific news about technology."}}

User query: "{query}"

Should this query be handled using one of the available tools? If so, which tool is most appropriate?
Respond with a JSON object with the following format:
{{
"use_tool": true/false,
"tool_name": "ToolName or null if no tool needed",
"reasoning": "Brief explanation of your decision"
}}
"""
        
        # Get router decision
        response = await self.llm.generate(prompt=router_prompt)
        
        try:
            # Parse the JSON response
            decision = json.loads(response)
            return decision.get("use_tool", False), decision.get("tool_name")
        except:
            # If JSON parsing fails, default to not using tools
            return False, None
