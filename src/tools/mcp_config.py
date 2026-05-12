"""MCP Server configuration management"""

import os
import sys
from typing import Dict, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP Server"""
    name: str
    transport: str = "stdio"  # "stdio" | "sse"
    command: Optional[str] = None
    args: Optional[List[str]] = Field(default_factory=list)
    url: Optional[str] = None
    env: Optional[Dict[str, str]] = Field(default_factory=dict)
    enabled: bool = True
    timeout: int = 60


def _get_python_executable() -> str:
    """Get the current Python interpreter path"""
    return sys.executable


def _build_default_configs() -> Dict[str, MCPServerConfig]:
    """Build default MCP Server configurations"""
    github_token = os.getenv("GITHUB_TOKEN", "")

    return {
        "github": MCPServerConfig(
            name="github",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": github_token} if github_token else {},
            enabled=bool(github_token),
            timeout=60,
        ),
        "filesystem": MCPServerConfig(
            name="filesystem",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", str(PROJECT_ROOT)],
            enabled=True,
            timeout=60,
        ),
        "repo_search": MCPServerConfig(
            name="repo_search",
            transport="stdio",
            command=_get_python_executable(),
            args=["-m", "src.mcp_servers.repo_search_server"],
            env={"PYTHONPATH": str(PROJECT_ROOT)},
            enabled=True,
            timeout=30,
        ),
    }


# Default server configurations (lazily loaded)
DEFAULT_SERVER_CONFIGS: Optional[Dict[str, MCPServerConfig]] = None


def get_server_configs() -> Dict[str, MCPServerConfig]:
    """Get all MCP Server configurations"""
    global DEFAULT_SERVER_CONFIGS
    if DEFAULT_SERVER_CONFIGS is None:
        DEFAULT_SERVER_CONFIGS = _build_default_configs()
    return DEFAULT_SERVER_CONFIGS


def get_server_config(name: str) -> Optional[MCPServerConfig]:
    """Get a specific MCP Server configuration"""
    configs = get_server_configs()
    return configs.get(name)


def register_server_config(config: MCPServerConfig) -> None:
    """Register or override a server configuration"""
    configs = get_server_configs()
    configs[config.name] = config


def get_enabled_configs() -> Dict[str, MCPServerConfig]:
    """Get only enabled server configurations"""
    return {k: v for k, v in get_server_configs().items() if v.enabled}


def reset_configs() -> None:
    """Reset to default configurations"""
    global DEFAULT_SERVER_CONFIGS
    DEFAULT_SERVER_CONFIGS = None
