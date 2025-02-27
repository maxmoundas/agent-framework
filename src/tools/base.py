# base.py
from abc import ABC, abstractmethod


class BaseTool(ABC):
    description = "Base tool description"
    parameters = {}

    @abstractmethod
    async def execute(self, **kwargs):
        """Execute the tool with the given parameters"""
        pass
