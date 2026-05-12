"""
Tool layer - unified tool calling, MCP integration, permission isolation.

Usage:
    from src.tools import register_all_tools, get_registry, get_executor
    register_all_tools()
"""

import logging
from typing import List

from src.tools.tool_registry import (
    ToolDefinition,
    ToolResult,
    get_registry,
    reset_registry,
    ToolSource,
    PermissionLevel,
)
from src.tools.tool_executor import ToolExecutor, get_executor
from src.tools.mcp_client import MCPClientManager, get_mcp_manager
from src.tools.mcp_config import get_server_configs, get_enabled_configs

logger = logging.getLogger(__name__)

# Flag to prevent double-registration
_initialized = False


def register_all_tools() -> None:
    """
    Register all tools from all MCP Servers and builtin handlers.

    This is the single entry point for bootstrapping the tool layer.
    Call it once at application startup.
    """
    global _initialized
    if _initialized:
        return

    registry = get_registry()
    reset_registry()
    registry = get_registry()

    # Register builtin tools (local Python implementations)
    builtin_tools = _build_builtin_tools()
    for tool, agents in builtin_tools:
        registry.register(tool)
    logger.info("Registered %d builtin tools", len(builtin_tools))

    # Attempt to discover tools from MCP Servers
    try:
        mcp_tools = _discover_mcp_tools()
        for tool, agents in mcp_tools:
            registry.register(tool)
        logger.info("Registered %d MCP tools", len(mcp_tools))
    except Exception as e:
        logger.warning("MCP tool discovery skipped: %s", e)

    _initialized = True
    logger.info(
        "Tool layer initialized with %d total tools",
        len(registry.tools),
    )


def _build_builtin_tools() -> List[tuple]:
    """Build builtin tool definitions (local Python handlers)"""
    tools = [
        (
            ToolDefinition(
                name="search_code_snippet",
                description=(
                    "Search for code snippets by keyword. "
                    "Supports filtering by programming language."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Keyword to search for",
                        },
                        "language": {
                            "type": "string",
                            "enum": ["python", "javascript", "all"],
                            "description": "Filter by language",
                            "default": "python",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Max number of results",
                            "default": 10,
                        },
                    },
                    "required": ["query"],
                },
                permission_level=PermissionLevel.READ_ONLY,
                source=ToolSource.BUILTIN,
                timeout=15,
            ),
            ["repo_analyst", "implementer", "reviewer", "tester"],
        ),
        (
            ToolDefinition(
                name="read_symbol_context",
                description=(
                    "Read a function/class definition and its surrounding context. "
                    "Useful for understanding how a symbol is implemented."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Symbol name to find",
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Optional file to search in",
                        },
                        "context_lines": {
                            "type": "integer",
                            "description": "Number of surrounding lines",
                            "default": 10,
                        },
                    },
                    "required": ["symbol"],
                },
                permission_level=PermissionLevel.READ_ONLY,
                source=ToolSource.BUILTIN,
                timeout=15,
            ),
            ["repo_analyst", "implementer", "reviewer"],
        ),
        (
            ToolDefinition(
                name="collect_project_metadata",
                description=(
                    "Collect project metadata: language, framework, directory "
                    "structure, dependencies."
                ),
                input_schema={"type": "object", "properties": {}},
                permission_level=PermissionLevel.READ_ONLY,
                source=ToolSource.BUILTIN,
                timeout=15,
            ),
            ["supervisor", "repo_analyst", "reviewer"],
        ),
        (
            ToolDefinition(
                name="find_files",
                description="Find files matching a name pattern",
                input_schema={
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Pattern to match file names",
                        },
                        "file_type": {
                            "type": "string",
                            "enum": ["python", "javascript", "all"],
                            "default": "all",
                        },
                    },
                    "required": ["pattern"],
                },
                permission_level=PermissionLevel.READ_ONLY,
                source=ToolSource.BUILTIN,
                timeout=10,
            ),
            ["repo_analyst"],
        ),
        (
            ToolDefinition(
                name="search_symbols",
                description="Search for classes and functions across the codebase",
                input_schema={
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Symbol name pattern",
                        },
                        "symbol_type": {
                            "type": "string",
                            "enum": ["class", "function", "all"],
                            "default": "all",
                        },
                    },
                    "required": ["symbol"],
                },
                permission_level=PermissionLevel.READ_ONLY,
                source=ToolSource.BUILTIN,
                timeout=15,
            ),
            ["repo_analyst", "reviewer"],
        ),
        (
            ToolDefinition(
                name="analyze_project_structure",
                description="Analyze overall project structure and layout",
                input_schema={"type": "object", "properties": {}},
                permission_level=PermissionLevel.READ_ONLY,
                source=ToolSource.BUILTIN,
                timeout=15,
            ),
            ["repo_analyst"],
        ),
        (
            ToolDefinition(
                name="get_dependencies",
                description="Get project dependencies (requirements.txt / package.json)",
                input_schema={"type": "object", "properties": {}},
                permission_level=PermissionLevel.READ_ONLY,
                source=ToolSource.BUILTIN,
                timeout=10,
            ),
            ["repo_analyst"],
        ),
        (
            ToolDefinition(
                name="execute_command",
                description=(
                    "Execute a shell command in a sandboxed environment. "
                    "Use for running tests, linters, and build commands."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Shell command to execute",
                        },
                        "working_dir": {
                            "type": "string",
                            "description": "Working directory for the command",
                            "default": ".",
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds",
                            "default": 60,
                        },
                    },
                    "required": ["command"],
                },
                permission_level=PermissionLevel.EXECUTE,
                source=ToolSource.BUILTIN,
                timeout=120,
            ),
            ["tester"],
        ),
    ]

    return tools


def _discover_mcp_tools() -> List[tuple]:
    """
    Attempt to discover tools from enabled MCP Servers.

    If an MCP Server is not reachable (e.g., npx not installed),
    falls back to pre-defined schemas.
    """
    manager = get_mcp_manager()
    discovered = []

    for name, config in get_enabled_configs().items():
        try:
            tools_list = manager.sync_list_tools(name)
            for t in tools_list:
                source = ToolSource.MCP_GITHUB if name == "github" else \
                         ToolSource.MCP_FILESYSTEM if name == "filesystem" else \
                         ToolSource.MCP_LOCAL

                plevel = PermissionLevel.READ_ONLY
                if t["name"] in ("write_file", "create_or_update_file"):
                    plevel = PermissionLevel.WRITE
                elif t["name"] in ("execute_command",):
                    plevel = PermissionLevel.EXECUTE

                tool_def = ToolDefinition(
                    name=t["name"],
                    description=t["description"],
                    input_schema=t["inputSchema"],
                    source=source,
                    server_name=name,
                    permission_level=plevel,
                    timeout=config.timeout,
                )

                agents = _resolve_mcp_tool_agents(name, t["name"], plevel)
                discovered.append((tool_def, agents))

        except Exception as e:
            logger.warning("MCP Server '%s' discovery failed: %s", name, e)
            discovered.extend(_fallback_mcp_tools(name, config))

    return discovered


def _resolve_mcp_tool_agents(
    server_name: str, tool_name: str, level: PermissionLevel
) -> List[str]:
    """Map an MCP tool to allowed agents"""
    from src.tools.permissions import AGENT_PERMISSIONS, PERMISSION_HIERARCHY

    allowed = []
    for agent_name, levels in AGENT_PERMISSIONS.items():
        tool_levels = PERMISSION_HIERARCHY.get(level, {level})
        if levels & tool_levels:
            allowed.append(agent_name)

    return allowed


def _fallback_mcp_tools(server_name: str, config) -> List[tuple]:
    """
    Fallback tool definitions when MCP Server discovery fails
    (e.g., npx not available or server not running).
    """
    from src.tools.tool_registry import ToolSource

    if server_name == "github":
        source = ToolSource.MCP_GITHUB
        tools = [
            ToolDefinition(
                name="get_repo_info",
                description="Get repository metadata (owner, default branch, description)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string", "description": "Repo owner"},
                        "repo": {"type": "string", "description": "Repo name"},
                    },
                    "required": ["owner", "repo"],
                },
                source=source,
                server_name=server_name,
                permission_level=PermissionLevel.READ_ONLY,
            ),
            ToolDefinition(
                name="search_issues",
                description="Search GitHub issues",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "query": {"type": "string"},
                    },
                    "required": ["query"],
                },
                source=source,
                server_name=server_name,
                permission_level=PermissionLevel.READ_ONLY,
            ),
            ToolDefinition(
                name="create_or_update_file",
                description="Create or update a file in a GitHub repository",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                        "message": {"type": "string"},
                    },
                    "required": ["owner", "repo", "path", "content"],
                },
                source=source,
                server_name=server_name,
                permission_level=PermissionLevel.WRITE,
            ),
            ToolDefinition(
                name="create_pull_request",
                description="Create a GitHub pull request",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "title": {"type": "string"},
                        "head": {"type": "string"},
                        "base": {"type": "string"},
                    },
                    "required": ["owner", "repo", "title", "head", "base"],
                },
                source=source,
                server_name=server_name,
                permission_level=PermissionLevel.WRITE,
            ),
        ]
    elif server_name == "filesystem":
        source = ToolSource.MCP_FILESYSTEM
        tools = [
            ToolDefinition(
                name="read_file",
                description="Read the contents of a file",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                    },
                    "required": ["path"],
                },
                source=source,
                server_name=server_name,
                permission_level=PermissionLevel.READ_ONLY,
            ),
            ToolDefinition(
                name="write_file",
                description="Write content to a file",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "content": {"type": "string", "description": "File content"},
                    },
                    "required": ["path", "content"],
                },
                source=source,
                server_name=server_name,
                permission_level=PermissionLevel.WRITE,
            ),
            ToolDefinition(
                name="list_directory",
                description="List files and directories in a path",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path"},
                    },
                    "required": ["path"],
                },
                source=source,
                server_name=server_name,
                permission_level=PermissionLevel.READ_ONLY,
            ),
        ]
    else:
        return []

    result = []
    for tool in tools:
        agents = _resolve_mcp_tool_agents(server_name, tool.name, tool.permission_level)
        result.append((tool, agents))
    return result


__all__ = [
    "register_all_tools",
    "get_registry",
    "get_executor",
    "get_mcp_manager",
    "ToolDefinition",
    "ToolResult",
    "ToolSource",
    "PermissionLevel",
    "MCPClientManager",
    "ToolExecutor",
]
