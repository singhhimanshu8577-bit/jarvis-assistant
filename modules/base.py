"""
Base module and tool registry for JARVIS.
Provides the @tool decorator and automatic JSON Schema generation for LLM tool calling.
"""

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, get_type_hints


@dataclass
class ToolResult:
    """Standardized response from tool execution."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    requires_confirmation: bool = False
    confirmation_prompt: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        res = {
            "success": self.success,
            "message": self.message,
        }
        if self.data:
            res["data"] = self.data
        if self.requires_confirmation:
            res["requires_confirmation"] = True
            res["confirmation_prompt"] = self.confirmation_prompt
        return res


@dataclass
class ToolDefinition:
    """Metadata and execution pointer for a registered tool."""
    name: str
    description: str
    func: Callable
    parameters_schema: Dict[str, Any]
    requires_confirmation: bool = False
    module_name: str = "general"


class ToolRegistry:
    """Global registry holding all registered tools and their schemas."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance.tools: Dict[str, ToolDefinition] = {}
        return cls._instance

    def register(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        requires_confirmation: bool = False,
        module_name: str = "general",
    ) -> Callable:
        """Register a function as an LLM tool."""
        tool_name = name or func.__name__
        tool_desc = description or inspect.getdoc(func) or f"Execute {tool_name}"
        # Extract first paragraph of docstring if multi-line
        tool_desc = tool_desc.strip().split("\n\n")[0].replace("\n", " ").strip()

        schema = self._generate_json_schema(func)

        tool_def = ToolDefinition(
            name=tool_name,
            description=tool_desc,
            func=func,
            parameters_schema=schema,
            requires_confirmation=requires_confirmation,
            module_name=module_name,
        )

        self.tools[tool_name] = tool_def
        return func

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self.tools.get(name)

    def get_all(self) -> Dict[str, ToolDefinition]:
        return self.tools

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """Export tools formatted for OpenAI / Ollama tool calling format."""
        openai_tools = []
        for name, tool in self.tools.items():
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool.description,
                    "parameters": tool.parameters_schema,
                },
            })
        return openai_tools

    def get_gemini_tools(self) -> List[Dict[str, Any]]:
        """Export tools formatted for Gemini function calling."""
        declarations = []
        for name, tool in self.tools.items():
            declarations.append({
                "name": name,
                "description": tool.description,
                "parameters": tool.parameters_schema,
            })
        return declarations

    def _generate_json_schema(self, func: Callable) -> Dict[str, Any]:
        """Generate JSON Schema from function signature and type hints."""
        sig = inspect.signature(func)
        try:
            hints = get_type_hints(func)
        except Exception:
            hints = {}

        properties = {}
        required = []

        type_mapping = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            param_type = hints.get(param_name, str)
            # Unwrap Optional[T] if present
            origin = getattr(param_type, "__origin__", None)
            args = getattr(param_type, "__args__", ())
            if origin is not None and type(None) in args:
                # Optional type
                non_none_types = [t for t in args if t is not type(None)]
                param_type = non_none_types[0] if non_none_types else str

            json_type = type_mapping.get(param_type, "string")
            param_schema = {"type": json_type}

            # If default is not inspect._empty, it's optional
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
            else:
                param_schema["default"] = param.default

            properties[param_name] = param_schema

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }


# Singleton instance
registry = ToolRegistry()


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    requires_confirmation: bool = False,
    module_name: str = "general",
):
    """Decorator to register any function as an LLM tool."""
    def decorator(func: Callable):
        registry.register(
            func=func,
            name=name,
            description=description,
            requires_confirmation=requires_confirmation,
            module_name=module_name,
        )
        return func
    return decorator
