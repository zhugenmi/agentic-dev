"""MCP Server process management and startup utilities"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from src.tools.mcp_config import MCPServerConfig, get_server_configs, get_enabled_configs

logger = logging.getLogger(__name__)


class MCPServerError(Exception):
    """Raised when MCP Server startup fails"""
    pass


def get_python_executable() -> str:
    """Get the Python executable (handles virtualenv)"""
    return sys.executable


def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).parent.parent.parent.absolute()


def _build_env(config: MCPServerConfig) -> Optional[Dict[str, str]]:
    """Build environment dict for subprocess"""
    import os
    env = dict(os.environ)
    project_root = str(get_project_root())
    env["PYTHONPATH"] = project_root

    if config.env:
        env.update(config.env)

    return env


class MCPServerRunner:
    """Manages MCP Server subprocesses"""

    def __init__(self):
        self._processes: Dict[str, subprocess.Popen] = {}

    @property
    def running_servers(self) -> List[str]:
        return [name for name, proc in self._processes.items() if proc.poll() is None]

    def start(self, server_name: str, config: Optional[MCPServerConfig] = None) -> subprocess.Popen:
        """Start an MCP Server subprocess"""
        if server_name in self._processes:
            proc = self._processes[server_name]
            if proc.poll() is None:
                logger.info("MCP Server '%s' is already running", server_name)
                return proc

        if config is None:
            config = get_server_configs().get(server_name)
        if not config:
            raise MCPServerError(f"No config found for MCP Server '{server_name}'")

        cmd = [config.command] + (config.args or [])
        env = _build_env(config)

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=str(get_project_root()),
            )
            self._processes[server_name] = proc
            logger.info("Started MCP Server '%s' (PID %s)", server_name, proc.pid)
            return proc
        except FileNotFoundError:
            raise MCPServerError(
                f"Command not found: {config.command}. "
                f"Make sure '{' '.join(cmd)}' is available."
            )

    def stop(self, server_name: str) -> bool:
        """Stop a running MCP Server"""
        proc = self._processes.pop(server_name, None)
        if proc is None:
            return False
        try:
            proc.terminate()
            proc.wait(timeout=10)
            logger.info("Stopped MCP Server '%s'", server_name)
            return True
        except Exception as e:
            logger.error("Failed to stop MCP Server '%s': %s", server_name, e)
            return False

    def stop_all(self) -> None:
        """Stop all running MCP Servers"""
        for name in list(self._processes.keys()):
            self.stop(name)

    def is_running(self, server_name: str) -> bool:
        """Check if an MCP Server is running"""
        proc = self._processes.get(server_name)
        return proc is not None and proc.poll() is None

    def get_output(self, server_name: str, last_lines: int = 20) -> str:
        """Get recent stderr output from an MCP Server"""
        proc = self._processes.get(server_name)
        if not proc:
            return ""
        return proc.stdout


# Singleton instance
_runner: Optional[MCPServerRunner] = None


def get_runner() -> MCPServerRunner:
    """Get or create the global MCPServerRunner"""
    global _runner
    if _runner is None:
        _runner = MCPServerRunner()
    return _runner


def reset_runner() -> None:
    """Reset the global runner"""
    global _runner
    _runner = None
