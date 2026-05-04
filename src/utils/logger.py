"""Logging module for debugging and monitoring agent execution"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def setup_logger(name: str = "multi_agents_coder", level: int = logging.DEBUG) -> logging.Logger:
    """Setup and return a logger instance"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    file_handler = logging.FileHandler(
        Path(__file__).parent.parent.parent / "logs" / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()


def get_model_name_from_env(agent_name: str) -> str:
    """从环境变量获取 Agent 使用的模型名称

    Args:
        agent_name: Agent 名称 (supervisor, repo_analyst, implementer, reviewer, tester)

    Returns:
        模型名称，如果未配置则返回 'default'
    """
    prefix_map = {
        "supervisor": "SUPERVISOR",
        "repo_analyst": "REPO_ANALYST",
        "implementer": "IMPLEMENTER",
        "reviewer": "REVIEWER",
        "tester": "TESTER"
    }

    prefix = prefix_map.get(agent_name, "DEFAULT")
    model_name = (
        os.getenv(f"{prefix}_MODEL")
        if prefix != "DEFAULT"
        else os.getenv("DEFAULT_MODEL")
    )

    return model_name or "default"


class AgentLogger:
    """Logger for tracking agent execution"""

    def __init__(self, agent_name: str, model_name: str = None):
        self.agent_name = agent_name
        # 如果没有传入 model_name，从环境变量读取 Agent 专用配置
        self.model_name = model_name or get_model_name_from_env(agent_name)
        self.logger = logger

    def _get_prefixed_agent_name(self) -> str:
        """获取带模型名称的 Agent 名称，例如：Supervisor-deepseek-v4-pro"""
        return f"{self.agent_name}-{self.model_name}"

    def info(self, message: str):
        self.logger.info(f"[{self._get_prefixed_agent_name()}] {message}")

    def debug(self, message: str):
        self.logger.debug(f"[{self._get_prefixed_agent_name()}] {message}")

    def warning(self, message: str):
        self.logger.warning(f"[{self._get_prefixed_agent_name()}] {message}")

    def error(self, message: str):
        self.logger.error(f"[{self._get_prefixed_agent_name()}] {message}")

    def start(self, task: str = ""):
        self.info(f"🚀 开始执行 {task}")

    def complete(self, result_summary: str = ""):
        self.info(f"✅ 执行完成 {result_summary}")

    def fail(self, error: str):
        self.error(f"❌ 执行失败: {error}")

    def step(self, step_name: str, message: str = ""):
        prefix = f"[{step_name}]" if step_name else ""
        self.debug(f"{prefix} {message}")
