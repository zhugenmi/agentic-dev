"""Tool Executor - unified dispatch layer for MCP and builtin tools"""

import asyncio
import json
import logging
import os
import subprocess
import time
import uuid
from typing import Any, Dict, Optional

from src.tools.tool_registry import ToolDefinition, ToolResult, get_registry
from src.tools.permissions import (
    check_permission_level,
    is_tool_allowed,
)
from src.tools.mcp_client import MCPClientManager, get_mcp_manager, MCPToolCallError

logger = logging.getLogger(__name__)


def _execute_command_handler(command: str, working_dir: str = ".", timeout: int = 60) -> Dict[str, Any]:
    """Execute a shell command safely"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s", "returncode": -1}
    except Exception as e:
        return {"error": str(e), "returncode": -1}


class ToolExecutor:
    """
    Unified tool execution layer.

    Flow:
        Agent → call_tool(name, args) → ToolExecutor.execute()
                                    → permission check
                                    → route to MCP / builtin
                                    → record trace + metrics
                                    → return ToolResult
    """

    def __init__(self, mcp_manager: Optional[MCPClientManager] = None):
        self._registry = get_registry()
        self._mcp = mcp_manager or get_mcp_manager()

    def check_permission(self, agent_name: str, tool_name: str) -> bool:
        """Check if an agent is allowed to call a tool"""
        tool_def = self._registry.get_tool(tool_name)
        if not tool_def:
            return False
        if not is_tool_allowed(agent_name, tool_name):
            return False
        if not check_permission_level(agent_name, tool_def.permission_level):
            return False
        return True

    def _route_and_execute(
        self, tool_def: ToolDefinition, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route a tool call to the correct backend (MCP or builtin)"""
        from src.tools.tool_registry import ToolSource

        if tool_def.source == ToolSource.BUILTIN:
            return self._execute_builtin(tool_def.name, arguments)
        elif tool_def.source in (ToolSource.MCP_GITHUB, ToolSource.MCP_FILESYSTEM,
                                 ToolSource.MCP_LOCAL):
            server = tool_def.server_name or tool_def.source.replace("mcp_", "")
            return self._mcp.sync_call_tool(
                server_name=server,
                tool_name=tool_def.name,
                arguments=arguments,
                timeout=tool_def.timeout,
            )
        else:
            raise ValueError(f"Unknown tool source: {tool_def.source}")

    def _execute_builtin(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a builtin (local Python) tool"""
        builtin_handlers = self._get_builtin_handlers()
        handler = builtin_handlers.get(tool_name)
        if not handler:
            return {"error": f"Builtin tool '{tool_name}' not found"}

        try:
            result = handler(**arguments)
            return {"content": [{"type": "text", "text": str(result)}]}
        except Exception as e:
            return {"error": f"Builtin tool '{tool_name}' failed: {e}"}

    @staticmethod
    def _get_builtin_handlers() -> Dict[str, Any]:
        """Map of builtin tool names to their handler functions"""
        from src.mcp_servers.repo_search_server import (
            search_code_snippet,
            read_symbol_context,
            collect_project_metadata,
            find_files,
            search_symbols,
            analyze_project_structure,
            get_dependencies,
        )

        return {
            "search_code_snippet": search_code_snippet,
            "read_symbol_context": read_symbol_context,
            "collect_project_metadata": collect_project_metadata,
            "find_files": find_files,
            "search_symbols": search_symbols,
            "analyze_project_structure": analyze_project_structure,
            "get_dependencies": get_dependencies,
            "execute_command": _execute_command_handler,
        }

    def execute(
        self,
        agent_name: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> ToolResult:
        """Execute a tool call (sync entry point).

        Args:
            agent_name: Name of the requesting agent
            tool_name: Tool to execute
            arguments: Tool arguments
            trace_id: Optional trace ID for tracking

        Returns:
            ToolResult with success/failure and output
        """
        if trace_id is None:
            trace_id = str(uuid.uuid4())[:8]

        tool_def = self._registry.get_tool(tool_name)
        if not tool_def:
            logger.warning("Agent '%s' called unknown tool '%s'", agent_name, tool_name)
            return ToolResult(
                success=False,
                error=f"Unknown tool: {tool_name}",
                trace_id=trace_id,
            )

        # Permission check
        if not self.check_permission(agent_name, tool_name):
            logger.warning(
                "Agent '%s' denied access to tool '%s'", agent_name, tool_name
            )
            return ToolResult(
                success=False,
                error=f"Permission denied for agent '{agent_name}' on tool '{tool_name}'",
                trace_id=trace_id,
            )

        # Execute
        start_ms = time.time()
        try:
            raw_result = self._route_and_execute(tool_def, arguments or {})
            duration = int((time.time() - start_ms) * 1000)

            output = self._extract_output(raw_result)
            is_error = raw_result.get("isError", False) or "error" in raw_result

            logger.info(
                "Tool '%s' executed by '%s' in %dms (trace=%s)",
                tool_name, agent_name, duration, trace_id,
            )

            return ToolResult(
                success=not is_error,
                output=output,
                error=raw_result.get("error") if is_error else None,
                trace_id=trace_id,
                duration_ms=duration,
            )

        except MCPToolCallError as e:
            duration = int((time.time() - start_ms) * 1000)
            logger.error("MCP tool call failed: %s", e)
            return ToolResult(
                success=False,
                error=str(e),
                trace_id=trace_id,
                duration_ms=duration,
            )
        except Exception as e:
            duration = int((time.time() - start_ms) * 1000)
            logger.error("Tool execution failed: %s", e)
            return ToolResult(
                success=False,
                error=str(e),
                trace_id=trace_id,
                duration_ms=duration,
            )

    def _extract_output(self, raw_result: Dict[str, Any]) -> Any:
        """Extract the primary output from a raw MCP result."""
        if "error" in raw_result:
            return raw_result["error"]

        content = raw_result.get("content", [])
        if isinstance(content, list) and content:
            first = content[0]
            if isinstance(first, dict):
                if "text" in first:
                    return first["text"]
                if "data" in first:
                    return first["data"]
            return content
        elif isinstance(content, str):
            return content

        return raw_result


# Module-level singleton
_executor_instance: Optional[ToolExecutor] = None


def get_executor() -> ToolExecutor:
    """Get a singleton ToolExecutor instance"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = ToolExecutor()
    return _executor_instance
