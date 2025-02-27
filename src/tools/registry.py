# src/tools/registry.py
class ToolRegistry:
    _tools = {}
    
    @classmethod
    def register(cls, name=None):
        def decorator(tool_class):
            tool_name = name or tool_class.__name__
            cls._tools[tool_name] = tool_class
            return tool_class
        return decorator
    
    @classmethod
    def get_tool(cls, name):
        return cls._tools.get(name)
    
    @classmethod
    def list_tools(cls):
        return list(cls._tools.keys())
    
    @classmethod
    def get_tool_specs(cls):
        specs = {}
        for name, tool_class in cls._tools.items():
            specs[name] = {
                "description": tool_class.description,
                "parameters": {}
            }
            
            # Extract parameter descriptions and details
            for param_name, param_details in tool_class.parameters.items():
                specs[name]["parameters"][param_name] = param_details
                
        return specs