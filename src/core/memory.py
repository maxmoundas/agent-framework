# src/core/memory.py
import datetime


class ConversationMemory:
    def __init__(self, max_turns=10):
        self.messages = []
        self.tool_results = []  # Store tool results separately
        self.router_decisions = []  # Store router decisions separately
        self.max_turns = max_turns

    def add_user_message(self, message):
        # Check if this exact message is already the most recent user message
        if (
            self.messages
            and self.messages[-1]["role"] == "user"
            and self.messages[-1]["content"] == message
        ):
            return  # Skip adding duplicate

        self.messages.append({"role": "user", "content": message})
        self._trim_if_needed()

    def add_assistant_message(self, message):
        # Check if this exact message is already the most recent assistant message
        if (
            len(self.messages) >= 2
            and self.messages[-1]["role"] == "assistant"
            and self.messages[-1]["content"] == message
        ):
            return  # Skip adding duplicate

        self.messages.append({"role": "assistant", "content": message})
        self._trim_if_needed()

    def add_tool_result(self, tool_name, result):
        """Store tool execution result for context"""
        self.tool_results.append(
            {
                "tool": tool_name,
                "result": result,
                "timestamp": datetime.datetime.now().isoformat(),
            }
        )

        # Only keep recent tool results
        if len(self.tool_results) > self.max_turns * 2:
            self.tool_results = self.tool_results[-self.max_turns * 2 :]

    def add_router_decision(self, use_tool, tool_name, reasoning):
        """Store router decision for context"""
        self.router_decisions.append(
            {
                "use_tool": use_tool,
                "tool_name": tool_name,
                "reasoning": reasoning,
                "timestamp": datetime.datetime.now().isoformat(),
            }
        )

        # Only keep recent router decisions
        if len(self.router_decisions) > self.max_turns * 2:
            self.router_decisions = self.router_decisions[-self.max_turns * 2 :]

    def get_conversation_history(self):
        return self.messages.copy()

    def get_recent_tool_results(self, limit=3):
        """Get the most recent tool results for context"""
        return self.tool_results[-limit:] if self.tool_results else []

    def get_recent_router_decisions(self, limit=3):
        """Get the most recent router decisions for context"""
        return self.router_decisions[-limit:] if self.router_decisions else []

    def clear(self):
        self.messages = []
        self.tool_results = []
        self.router_decisions = []

    def _trim_if_needed(self):
        """Keep only the most recent messages if we exceed max_turns"""
        if len(self.messages) > self.max_turns * 2:
            self.messages = self.messages[-self.max_turns * 2 :]
