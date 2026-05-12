"""Unified Tool Registry with permission-aware tool discovery"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from src.tools.permissions import (
    PermissionLevel,
    check_permission_level,
    is_tool_allowed,
)


class ToolSource(str, Enum):
    MCP_GITHUB = "mcp_github"
    MCP_FILESYSTEM = "mcp_filesystem"
    MCP_LOCAL = "mcp_local"
    BUILTIN = "builtin"


class ToolDefinition(BaseModel):
    """Structured tool definition with metadata"""
    name: str
    description: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Optional[Dict[str, Any]] = None
    timeout: int = 30
    permission_level: PermissionLevel = PermissionLevel.READ_ONLY
    source: ToolSource = ToolSource.BUILTIN
    server_name: Optional[str] = None

    def to_openai_tool_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI-compatible function calling schema"""
        schema = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }
        return schema


class ToolResult(BaseModel):
    """Structured tool execution result"""
    success: bool
    output: Any = None
    error: Optional[str] = None
    trace_id: str = ""
    duration_ms: int = 0

    def to_content(self) -> str:
        """Convert output to string for LLM tool response"""
        if not self.success:
            return f"Error: {self.error}"
        if isinstance(self.output, str):
            return self.output
        if isinstance(self.output, dict):
            import json
            return json.dumps(self.output, ensure_ascii=False, indent=2)[:4000]
        return str(self.output)


class ToolRegistry:
    """Centralized tool registry with agent-level permission isolation"""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    @property
    def tools(self) -> Dict[str, ToolDefinition]:
        return self._tools

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool definition"""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def register_many(self, tools: List[ToolDefinition]) -> None:
        """Register multiple tool definitions"""
        for tool in tools:
            self.register(tool)

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool definition by name"""
        return self._tools.get(name)

    def get_tools_for_agent(self, agent_name: str) -> List[ToolDefinition]:
        """Get all tools available to an agent (filtered by permission + whitelist)"""
        result = []
        for tool in self._tools.values():
            if not is_tool_allowed(agent_name, tool.name):
                continue
            if not check_permission_level(agent_name, tool.permission_level):
                continue
            result.append(tool)
        return result

    def get_tools_as_openai_functions(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get tool schemas in OpenAI function calling format for LLM binding"""
        tools = self.get_tools_for_agent(agent_name)
        return [t.to_openai_tool_schema() for t in tools]

    def list_all(self) -> List[Dict[str, Any]]:
        """List all registered tools with metadata"""
        return [
            {
                "name": t.name,
                "description": t.description,
                "source": t.source.value,
                "permission_level": t.permission_level.value,
                "timeout": t.timeout,
                "server_name": t.server_name,
            }
            for t in self._tools.values()
        ]

    def unregister(self, name: str) -> bool:
        """Unregister a tool by name"""
        if name in self._tools:
            del self._tools[name]
            return True
        return False


# Global singleton
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get or create the global ToolRegistry singleton"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def reset_registry() -> None:
    """Reset the global registry (mainly for testing)"""
    global _registry
    _registry = None
