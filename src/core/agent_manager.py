# src/core/agent_manager.py
import os
import json
from pathlib import Path
from .agent import Agent


class AgentManager:
    _agents = {}
    _cache_dir = Path(".agent_cache")

    @classmethod
    def get_agent(cls, session_id, model="gpt-4o-mini", custom_system_message=None):
        # Create cache directory if it doesn't exist
        if not cls._cache_dir.exists():
            cls._cache_dir.mkdir()

        # Check if agent already exists in memory
        if session_id in cls._agents:
            agent = cls._agents[session_id]
            # Update model if it changed
            if hasattr(agent, "model") and agent.model != model:
                agent.model = model
                agent.llm.model = model
            # If agent doesn't have model attribute, add it
            elif not hasattr(agent, "model"):
                agent.model = model
            return agent

        # Create new agent
        agent = Agent(model=model, custom_system_message=custom_system_message)

        # Check if conversation history exists on disk
        history_path = cls._cache_dir / f"{session_id}_history.json"
        if history_path.exists():
            try:
                with open(history_path, "r") as f:
                    history = json.load(f)
                    # Manually rebuild conversation memory
                    for msg in history:
                        if msg["role"] == "user":
                            agent.memory.add_user_message(msg["content"])
                        elif msg["role"] == "assistant":
                            agent.memory.add_assistant_message(msg["content"])
            except Exception as e:
                print(f"Error loading history: {e}")

        cls._agents[session_id] = agent
        return agent

    @classmethod
    def save_agent(cls, session_id):
        if session_id in cls._agents:
            agent = cls._agents[session_id]

            # Deduplicate messages before saving
            messages = agent.memory.get_conversation_history()
            unique_messages = []
            seen_messages = set()

            for msg in messages:
                # Create a hashable identifier for the message
                msg_identifier = (msg["role"], msg.get("content", "")[:100])

                if msg_identifier not in seen_messages:
                    seen_messages.add(msg_identifier)
                    unique_messages.append(msg)

            # Update the agent's memory with deduplicated messages
            agent.memory.messages = unique_messages

            # Save to file
            history_path = cls._cache_dir / f"{session_id}_history.json"
            with open(history_path, "w") as f:
                json.dump(agent.memory.messages, f)

    @classmethod
    def clear_agent(cls, session_id):
        if session_id in cls._agents:
            agent = cls._agents[session_id]
            agent.memory.clear()

            # Remove history file if it exists
            history_path = cls._cache_dir / f"{session_id}_history.json"
            if history_path.exists():
                history_path.unlink()
