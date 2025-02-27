# src/core/parser.py
import json
import re

class OutputParser:
    @staticmethod
    async def parse_json(text):
        """Extract and parse JSON from the text"""
        try:
            # Try to find JSON in code blocks first
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find any JSON-like structure with curly braces
                json_match = re.search(r'({[\s\S]*})', text)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # If no JSON structure is found, use the entire text
                    json_str = text
            
            # Clean up potential issues
            json_str = json_str.strip()
            
            # Try to fix common JSON errors
            # Replace single quotes with double quotes
            json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
            # Add quotes around unquoted keys
            json_str = re.sub(r'(\s*)(\w+)(\s*):', r'\1"\2"\3:', json_str)
            
            # Parse the JSON
            action_data = json.loads(json_str)
            return action_data
        except Exception as e:
            print(f"JSON parsing error: {e}")
            print(f"Attempted to parse: {text}")
            
            # Last resort: Try to extract tool name and parameters manually
            tool_match = re.search(r'"tool"\s*:\s*"([^"]+)"', text)
            if tool_match:
                tool_name = tool_match.group(1)
                params = {}
                # Try to find parameters section
                params_match = re.search(r'"parameters"\s*:\s*{([^}]+)}', text)
                if params_match:
                    params_text = params_match.group(1)
                    # Extract key-value pairs
                    for kv_match in re.finditer(r'"([^"]+)"\s*:\s*("[^"]*"|[0-9]+)', params_text):
                        key = kv_match.group(1)
                        value = kv_match.group(2)
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]  # Remove quotes
                        elif value.isdigit():
                            value = int(value)
                        params[key] = value
                
                return {"tool": tool_name, "parameters": params}
            
            return {"error": f"Failed to parse output: {str(e)}", "original_text": text}