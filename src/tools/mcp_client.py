"""MCP Protocol Client - connects to MCP Servers via stdio transport"""

import asyncio
import json
import logging
import os
import sys
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.tools.mcp_config import MCPServerConfig, get_server_config, get_enabled_configs

logger = logging.getLogger(__name__)


@contextmanager
def _suppress_asyncgen_cleanup():
    """Suppress asyncgen cleanup noise from MCP stdio teardown."""
    old_stderr = sys.stderr
    try:
        sys.stderr = open(os.devnull, 'w')
        yield
    finally:
        sys.stderr.close()
        sys.stderr = old_stderr


class MCPConnectionError(Exception):
    """Raised when an MCP Server connection fails"""
    pass


class MCPToolCallError(Exception):
    """Raised when a tool call to an MCP Server fails"""
    pass


class MCPClientManager:
    """
    Manages connections to multiple MCP Servers.

    Lifecycle:
        1. connect(server_name)  → starts stdio subprocess + initializes session
        2. call_tool(...)         → invokes a tool on the connected server
        3. list_tools(...)        → discovers available tools
        4. disconnect(...)        → tears down the connection

    Each server runs as a separate stdio subprocess. Connections are lazy
    (opened on first call, closed after use).
    """

    def __init__(self):
        self._sessions: Dict[str, Tuple[ClientSession, Any]] = {}
        self._tool_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._connected: set[str] = set()

    @property
    def connected_servers(self) -> set[str]:
        return self._connected.copy()

    async def connect(self, config: MCPServerConfig) -> ClientSession:
        """Connect to an MCP Server and initialize the session.

        Returns the ClientSession instance.
        """
        name = config.name

        # Reuse existing connection
        if name in self._sessions:
            return self._sessions[name][0]

        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env or {},
        )

        transport = stdio_client(server_params)
        streams = await transport.__aenter__()
        read_stream, write_stream = streams

        session = ClientSession(read_stream, write_stream)
        try:
            await session.__aenter__()
        except Exception as e:
            logger.warning("Session init failed for %s: %s", name, e)
            await transport.__aexit__(None, None, None)
            raise MCPConnectionError(f"Failed to initialize session for '{name}': {e}")

        self._sessions[name] = (session, transport)
        self._connected.add(name)
        logger.info("MCP connection opened: %s", name)

        return session

    async def _ensure_connected(self, server_name: str) -> ClientSession:
        """Get or create a connection for the given server name."""
        if server_name in self._connected:
            return self._sessions[server_name][0]

        config = get_server_config(server_name)
        if not config:
            raise MCPConnectionError(f"Unknown MCP Server: {server_name}")
        if not config.enabled:
            raise MCPConnectionError(f"MCP Server '{server_name}' is disabled")

        return await self.connect(config)

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Call a tool on an MCP Server.

        Returns a dict with 'content' and 'isError' keys.
        """
        session = await self._ensure_connected(server_name)

        try:
            result = await asyncio.wait_for(
                session.call_tool(tool_name, arguments or {}),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            raise MCPToolCallError(
                f"Tool '{tool_name}' on '{server_name}' timed out after {timeout}s"
            )
        except Exception as e:
            raise MCPToolCallError(f"Tool '{tool_name}' failed: {e}")

        return self._parse_call_result(result)

    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """List all tools exposed by an MCP Server."""
        if server_name in self._tool_cache:
            return self._tool_cache[server_name]

        session = await self._ensure_connected(server_name)

        try:
            result = await asyncio.wait_for(session.list_tools(), timeout=15)
        except Exception:
            return []

        tools = []
        for t in result.tools:
            tools.append({
                "name": t.name,
                "description": t.description or "",
                "inputSchema": t.inputSchema or {},
            })

        self._tool_cache[server_name] = tools
        return tools

    async def discover_all_tools(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Discover tools from all enabled MCP Servers.

        Returns list of (server_name, tool_info) tuples.
        """
        all_tools = []
        for name, config in get_enabled_configs().items():
            try:
                tools = await self.list_tools(name)
                for t in tools:
                    all_tools.append((name, t))
            except Exception as e:
                logger.warning("Failed to discover tools from %s: %s", name, e)

        return all_tools

    async def disconnect(self, server_name: str) -> None:
        """Disconnect from a specific MCP Server."""
        if server_name in self._sessions:
            session, transport = self._sessions[server_name]
            try:
                await session.__aexit__(None, None, None)
            except Exception:
                pass
            try:
                await transport.__aexit__(None, None, None)
            except Exception:
                pass
            del self._sessions[server_name]
            self._connected.discard(server_name)
            self._tool_cache.pop(server_name, None)
            logger.info("MCP connection closed: %s", server_name)

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP Servers."""
        names = list(self._connected)
        for name in names:
            await self.disconnect(name)

    def _parse_call_result(self, result) -> Dict[str, Any]:
        """Parse an MCP CallToolResult into a serializable dict."""
        content = []
        for item in result.content:
            if hasattr(item, "text"):
                content.append({"type": "text", "text": item.text})
            elif hasattr(item, "data"):
                content.append({"type": "resource", "data": item.data})
            else:
                content.append({"type": "unknown", "raw": str(item)})

        return {
            "content": content,
            "isError": getattr(result, "isError", False),
        }

    def sync_call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Synchronous wrapper for call_tool (for use from sync code paths)."""
        with _suppress_asyncgen_cleanup():
            return asyncio.run(self.call_tool(server_name, tool_name, arguments, timeout))

    def sync_list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """Synchronous wrapper for list_tools."""
        with _suppress_asyncgen_cleanup():
            return asyncio.run(self.list_tools(server_name))


# Module-level singleton
_mcp_manager_instance: Optional[MCPClientManager] = None


def get_mcp_manager() -> "MCPClientManager":
    """Get a singleton MCPClientManager instance."""
    global _mcp_manager_instance
    if _mcp_manager_instance is None:
        _mcp_manager_instance = MCPClientManager()
    return _mcp_manager_instance
