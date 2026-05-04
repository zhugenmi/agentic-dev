"""通用 LLM 客户端，支持从 .env 配置文件读取 API 设置"""

import os
from typing import Optional, Any, Dict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 加载环境变量
load_dotenv()

# Agent 到配置项前缀的映射
AGENT_CONFIG_PREFIX = {
    "supervisor": "SUPERVISOR",
    "repo_analyst": "REPO_ANALYST",
    "implementer": "IMPLEMENTER",
    "reviewer": "REVIEWER",
    "tester": "TESTER"
}

# 默认配置项
DEFAULT_CONFIG = {
    "MODEL": os.getenv("DEFAULT_MODEL", ""),
    "MODEL_API_KEY": os.getenv("DEFAULT_MODEL_API_KEY", ""),
    "MODEL_BASE_URL": os.getenv("DEFAULT_MODEL_BASE_URL", "")
}


def get_agent_model_config(agent_name: str) -> Dict[str, str]:
    """获取指定 Agent 的模型配置（模型名称、API Key、Base URL）

    从 .env 文件中读取配置，支持以下规则：
    1. 优先读取 Agent 专用配置（如 IMPLEMENTER_MODEL）
    2. 如果某项配置为空，则使用 DEFAULT 配置作为回退

    Args:
        agent_name: Agent 名称 (supervisor, repo_analyst, implementer, reviewer, tester)

    Returns:
        包含 model, api_key, base_url 的字典
    """
    prefix = AGENT_CONFIG_PREFIX.get(agent_name)

    if not prefix:
        # 未知 Agent 使用默认配置
        return {
            "model": DEFAULT_CONFIG["MODEL"],
            "api_key": DEFAULT_CONFIG["MODEL_API_KEY"],
            "base_url": DEFAULT_CONFIG["MODEL_BASE_URL"]
        }

    # 读取 Agent 专用配置
    agent_model = os.getenv(f"{prefix}_MODEL", "")
    agent_api_key = os.getenv(f"{prefix}_MODEL_API_KEY", "")
    agent_base_url = os.getenv(f"{prefix}_MODEL_BASE_URL", "")

    # 如果配置项为空，使用默认配置回退
    model = agent_model if agent_model else DEFAULT_CONFIG["MODEL"]
    api_key = agent_api_key if agent_api_key else DEFAULT_CONFIG["MODEL_API_KEY"]
    base_url = agent_base_url if agent_base_url else DEFAULT_CONFIG["MODEL_BASE_URL"]

    return {
        "model": model,
        "api_key": api_key,
        "base_url": base_url
    }


class LlmModelClient:
    """通用 LLM 客户端，兼容 OpenAI API 格式"""

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.7,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        agent_name: Optional[str] = None
    ):
        """初始化 LLM 客户端

        Args:
            model: 模型名称，如果未提供则从环境变量读取
            temperature: 采样温度 (默认：0.7)
            api_key: API 密钥，如果未提供则从环境变量读取
            base_url: API 基础 URL，如果未提供则从环境变量读取
            agent_name: Agent 名称，如果提供则从该 Agent 的专用配置读取
        """
        # 如果指定了 agent_name，优先使用 Agent 专用配置
        if agent_name:
            config = get_agent_model_config(agent_name)
            self.model = model or config["model"]
            self.api_key = api_key or config["api_key"]
            self.base_url = base_url or config["base_url"]
        else:
            # 获取模型配置
            self.model = model or os.getenv("LLM_MODEL", DEFAULT_CONFIG["MODEL"])
            self.api_key = api_key or os.getenv("MODEL_API_KEY", DEFAULT_CONFIG["MODEL_API_KEY"])
            self.base_url = base_url or os.getenv("MODEL_BASE_URL", DEFAULT_CONFIG["MODEL_BASE_URL"])

        self.temperature = temperature

        # 验证 API 密钥
        if not self.api_key:
            raise ValueError(
                "MODEL_API_KEY environment variable is not set or is empty. "
                "Please check your .env file or set it manually:\n"
                "export MODEL_API_KEY=your_actual_api_key"
            )

        # 初始化 OpenAI 兼容客户端
        self._client = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            api_key=self.api_key,
            base_url=self.base_url
        )

    def invoke(self, prompt: str) -> Any:
        """调用 LLM 生成单个响应

        Args:
            prompt: 输入提示

        Returns:
            LLM 响应对象
        """
        return self._client.invoke(prompt)

    def generate(self, prompts: list) -> Any:
        """批量生成响应

        Args:
            prompts: 提示列表

        Returns:
            批量响应结果
        """
        return self._client.generate(prompts)

    def stream(self, prompt: str):
        """流式调用 LLM

        Args:
            prompt: 输入提示

        Returns:
            流式响应迭代器
        """
        return self._client.stream(prompt)


def get_llm_client(
    model: Optional[str] = None,
    temperature: float = 0.7
) -> LlmModelClient:
    """获取 LLM 客户端实例（向后兼容）

    Args:
        model: 模型名称，如果未提供则从环境变量读取
        temperature: 采样温度 (默认：0.7)

    Returns:
        LlmModelClient 实例
    """
    return LlmModelClient(
        model=model,
        temperature=temperature
    )


def get_default_llm_client() -> LlmModelClient:
    """获取默认的 LLM 客户端实例

    Returns:
        LlmModelClient 实例
    """
    return LlmModelClient()


# ==================== Agent 专用 LLM 配置 ====================

def get_agent_llm_client(agent_name: str) -> LlmModelClient:
    """获取指定 Agent 的 LLM 客户端

    从 .env 文件读取 Agent 专用的模型配置：

    环境变量配置格式:
        DEFAULT_MODEL=qwen3.5-flash-2026-02-23
        DEFAULT_MODEL_API_KEY=sk-xxx
        DEFAULT_MODEL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

        # Agent 专用配置（可选，覆盖默认配置）
        SUPERVISOR_MODEL=
        SUPERVISOR_MODEL_API_KEY=
        SUPERVISOR_MODEL_BASE_URL=

        IMPLEMENTER_MODEL=
        IMPLEMENTER_MODEL_API_KEY=
        IMPLEMENTER_MODEL_BASE_URL=

        ... (其他 Agent)

    回退规则:
        - 如果 Agent 专用配置为空，自动回退到 DEFAULT 配置
        - 例如：IMPLEMENTER_MODEL 为空时，使用 DEFAULT_MODEL

    Args:
        agent_name: Agent 名称 (supervisor, repo_analyst, implementer, reviewer, tester)

    Returns:
        LlmModelClient 实例
    """
    return LlmModelClient(
        agent_name=agent_name,
        temperature=0.7
    )


def get_agent_llm_client_with_temp(agent_name: str, temperature: float) -> LlmModelClient:
    """获取指定 Agent 的 LLM 客户端（自定义 temperature）

    Args:
        agent_name: Agent 名称
        temperature: 采样温度

    Returns:
        LlmModelClient 实例
    """
    return LlmModelClient(
        agent_name=agent_name,
        temperature=temperature
    )
