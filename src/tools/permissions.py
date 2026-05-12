"""Agent permission definitions and validation"""

from enum import Enum
from typing import Set


class PermissionLevel(str, Enum):
    READ_ONLY = "read_only"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


# Permission hierarchy: each level includes all levels below it
PERMISSION_HIERARCHY = {
    PermissionLevel.READ_ONLY: {PermissionLevel.READ_ONLY},
    PermissionLevel.WRITE: {PermissionLevel.READ_ONLY, PermissionLevel.WRITE},
    PermissionLevel.EXECUTE: {PermissionLevel.READ_ONLY, PermissionLevel.EXECUTE},
    PermissionLevel.ADMIN: {PermissionLevel.READ_ONLY, PermissionLevel.WRITE,
                            PermissionLevel.EXECUTE, PermissionLevel.ADMIN},
}

# Agent → allowed permission levels
AGENT_PERMISSIONS: dict[str, Set[PermissionLevel]] = {
    "supervisor": {PermissionLevel.READ_ONLY},
    "repo_analyst": {PermissionLevel.READ_ONLY},
    "implementer": {PermissionLevel.READ_ONLY, PermissionLevel.WRITE},
    "reviewer": {PermissionLevel.READ_ONLY},
    "tester": {PermissionLevel.READ_ONLY, PermissionLevel.EXECUTE},
}

# Agent → allowed tool name whitelist
AGENT_TOOL_WHITELISTS: dict[str, set[str]] = {
    "supervisor": {
        "get_repo_info",
        "list_directory",
        "read_file",
        "collect_project_metadata",
    },
    "repo_analyst": {
        "search_code_snippet",
        "read_symbol_context",
        "collect_project_metadata",
        "get_repo_info",
        "list_directory",
        "read_file",
        "search_symbols",
        "find_files",
    },
    "implementer": {
        "search_code_snippet",
        "read_symbol_context",
        "collect_project_metadata",
        "read_file",
        "write_file",
        "create_or_update_file",
        "create_pull_request",
        "search_issues",
    },
    "reviewer": {
        "read_file",
        "search_code_snippet",
        "read_symbol_context",
        "search_symbols",
        "get_repo_info",
        "collect_project_metadata",
    },
    "tester": {
        "read_file",
        "write_file",
        "execute_command",
        "search_code_snippet",
    },
}


def check_permission_level(agent_name: str, required_level: PermissionLevel) -> bool:
    """Check if an agent has at least the required permission level."""
    agent_levels = AGENT_PERMISSIONS.get(agent_name, set())
    allowed_levels = PERMISSION_HIERARCHY.get(required_level, {required_level})
    return bool(agent_levels & allowed_levels)


def is_tool_allowed(agent_name: str, tool_name: str) -> bool:
    """Check if a tool is in the agent's whitelist."""
    whitelist = AGENT_TOOL_WHITELISTS.get(agent_name, set())
    return tool_name in whitelist


def get_agent_permissions(agent_name: str) -> Set[PermissionLevel]:
    """Get all permission levels for an agent."""
    return AGENT_PERMISSIONS.get(agent_name, set())


def get_agent_whitelist(agent_name: str) -> set[str]:
    """Get all whitelisted tools for an agent."""
    return AGENT_TOOL_WHITELISTS.get(agent_name, set())
