# src/tools/implementations/timestamp.py
from ..base import BaseTool
from ..registry import ToolRegistry
import datetime


@ToolRegistry.register()
class TimestampTool(BaseTool):
    description = "Get the current date and time"
    parameters = {
        "format": {
            "type": "string",
            "description": "Optional: The format for the timestamp (default, iso, unix)",
            "required": False,
        }
    }

    async def execute(self, format="default"):
        now = datetime.datetime.now()

        if format.lower() == "iso":
            return now.isoformat()
        elif format.lower() == "unix":
            return str(int(now.timestamp()))
        else:  # default format
            return now.strftime("%Y-%m-%d %H:%M:%S")
