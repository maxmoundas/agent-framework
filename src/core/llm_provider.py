# src/core/llm_provider.py - update the class
from litellm import acompletion
import asyncio


class LLMProvider:
    def __init__(self, model="gpt-3.5-turbo", api_key=None):
        self.model = model
        self.api_key = api_key

    async def generate(
        self,
        prompt=None,
        system_message=None,
        conversation_history=None,
        temperature=0.7,
    ):
        messages = []

        # Add system message if provided
        if system_message:
            messages.append({"role": "system", "content": system_message})

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add the current prompt if provided (and not already in history)
        if prompt and (
            not conversation_history
            or conversation_history[-1]["role"] != "user"
            or conversation_history[-1]["content"] != prompt
        ):
            messages.append({"role": "user", "content": prompt})

        try:
            response = await acompletion(
                model=self.model, messages=messages, temperature=temperature
            )

            # Ensure any pending tasks from LiteLLM are handled
            pending = [
                task
                for task in asyncio.all_tasks()
                if task is not asyncio.current_task() and "litellm" in str(task)
            ]

            if pending:
                await asyncio.gather(*pending, return_exceptions=True)

            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in LLM request: {e}")
            raise e
