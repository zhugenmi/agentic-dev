# 模型路由配置说明

本文档说明多 Agent 系统中的模型路由原理、配置方法和调用流程。

## 目录

- [概述](#概述)
- [模型路由原理](#模型路由原理)
- [配置说明](#配置说明)
- [调用流程](#调用流程)
- [使用示例](#使用示例)
- [故障排查](#故障排查)

## 概述

本系统支持为 5 个不同的 Agent 配置不同的 LLM 模型：

| Agent | 职责 | 配置前缀 |
|-------|------|----------|
| Supervisor | 任务规划和分解 | `SUPERVISOR_` |
| RepoAnalyst | 代码库分析 | `REPO_ANALYST_` |
| Implementer | 代码生成和修复 | `IMPLEMENTER_` |
| Reviewer | 代码审查 | `REVIEWER_` |
| Tester | 测试生成和执行 | `TESTER_` |

## 模型路由原理

### 核心设计

模型路由的核心思想是**配置分离 + 自动回退**：

1. **配置分离**: 每个 Agent 可以独立配置模型名称、API Key 和 Base URL
2. **自动回退**: 如果 Agent 专用配置为空，自动使用默认配置

### 配置优先级

```
Agent 专用配置 > 默认配置 (DEFAULT_*)
```

具体来说：
- 如果 `IMPLEMENTER_MODEL` 为空 → 使用 `DEFAULT_MODEL`
- 如果 `IMPLEMENTER_MODEL_API_KEY` 为空 → 使用 `DEFAULT_MODEL_API_KEY`
- 如果 `IMPLEMENTER_MODEL_BASE_URL` 为空 → 使用 `DEFAULT_MODEL_BASE_URL`

### 回退逻辑示意

```
读取 IMPLEMENTER_MODEL
         │
         ▼
    是否为空？
    │      │
    是     否
    │      │
    ▼      ▼
使用    使用
DEFAULT  专用
MODEL    MODEL
```

## 配置说明

### .env 文件结构

```ini
# ============= 默认配置（所有 Agent 的回退源）=============
DEFAULT_MODEL=qwen3.5-flash-2026-02-23
DEFAULT_MODEL_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
DEFAULT_MODEL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# ============= Agent 专用配置（可选）=============

# Supervisor Agent
SUPERVISOR_MODEL=
SUPERVISOR_MODEL_API_KEY=
SUPERVISOR_MODEL_BASE_URL=

# Repo Analyst Agent
REPO_ANALYST_MODEL=
REPO_ANALYST_MODEL_API_KEY=
REPO_ANALYST_MODEL_BASE_URL=

# Implementer Agent
IMPLEMENTER_MODEL=
IMPLEMENTER_MODEL_API_KEY=
IMPLEMENTER_MODEL_BASE_URL=

# Reviewer Agent
REVIEWER_MODEL=
REVIEWER_MODEL_API_KEY=
REVIEWER_MODEL_BASE_URL=

# Tester Agent
TESTER_MODEL=
TESTER_MODEL_API_KEY=
TESTER_MODEL_BASE_URL=
```

### 配置场景示例

#### 场景 1: 所有 Agent 使用同一模型（最简单）

只配置默认配置，Agent 专用配置留空：

```ini
DEFAULT_MODEL=qwen3.5-flash-2026-02-23
DEFAULT_MODEL_API_KEY=sk-xxx
DEFAULT_MODEL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Agent 专用配置全部留空
SUPERVISOR_MODEL=
IMPLEMENTER_MODEL=
# ... 其他 Agent 同理
```

#### 场景 2: 不同 Agent 使用不同模型

```ini
# 默认配置（作为回退）
DEFAULT_MODEL=qwen3.5-flash-2026-02-23
DEFAULT_MODEL_API_KEY=sk-xxx
DEFAULT_MODEL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Supervisor 使用更高阶的模型
SUPERVISOR_MODEL=qwen-max
SUPERVISOR_MODEL_API_KEY=sk-xxx
SUPERVISOR_MODEL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Implementer 使用默认模型（留空回退）
IMPLEMENTER_MODEL=
IMPLEMENTER_MODEL_API_KEY=
IMPLEMENTER_MODEL_BASE_URL=

# Tester 使用低成本模型
TESTER_MODEL=qwen-turbo
TESTER_MODEL_API_KEY=sk-xxx
TESTER_MODEL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

#### 场景 3: 使用不同 API 提供商

```ini
# 默认使用阿里云
DEFAULT_MODEL=qwen3.5-flash-2026-02-23
DEFAULT_MODEL_API_KEY=sk-aliyun-xxx
DEFAULT_MODEL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Reviewer 使用智谱 AI
REVIEWER_MODEL=glm-4-flash
REVIEWER_MODEL_API_KEY=sk-zhipu-xxx
REVIEWER_MODEL_BASE_URL=https://open.bigmodel.cn/api/paas/v4
```

## 调用流程

### 1. Agent 初始化时的模型加载

```python
# 以 Implementer 为例
from src.llm.llm_model_client import get_agent_llm_client

class Implementer:
    def __init__(self):
        # 自动读取 IMPLEMENTER_*配置
        # 如果为空，回退到 DEFAULT_*配置
        self.client = get_agent_llm_client("implementer")
```

### 2. 配置读取流程

```
get_agent_llm_client("implementer")
           │
           ▼
┌─────────────────────────────┐
│  LlmModelClient(agent_name) │
└─────────────────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  get_agent_model_config()   │
│  - 读取 IMPLEMENTER_MODEL   │
│  - 读取 IMPLEMENTER_MODEL_  │
│    API_KEY                  │
│  - 读取 IMPLEMENTER_MODEL_  │
│    BASE_URL                 │
└─────────────────────────────┘
           │
           ▼
    ┌──────┴──────┐
    │  值是否为空？│
    └──────┬──────┘
     是    │    否
     │     │     │
     ▼     │     ▼
使用默认   │   使用专用
配置       │   配置
           │
           ▼
┌─────────────────────────────┐
│  创建 ChatOpenAI 实例        │
│  model=xxx                  │
│  api_key=xxx                │
│  base_url=xxx               │
└─────────────────────────────┘
```

### 3. 完整调用链路

```
User 请求
   │
   ▼
SupervisorAgent.plan()
   │
   └─→ get_agent_llm_client("supervisor")
          │
          └─→ 读取 SUPERVISOR_* 配置
                 │
                 └─→ 如果为空，回退 DEFAULT_*
                        │
                        └─→ ChatOpenAI.invoke(prompt)
```

## 使用示例

### 基础使用

```python
from src.agents.implementer import Implementer

# Implementer 会自动使用配置的模型
implementer = Implementer()
code = implementer.generate("写一个快速排序函数")
```

### 手动获取配置

```python
from src.llm.llm_model_client import get_agent_model_config

# 查看 Implementer 的模型配置
config = get_agent_model_config("implementer")
print(f"Model: {config['model']}")
print(f"API Key: {config['api_key']}")
print(f"Base URL: {config['base_url']}")

# 查看 Supervisor 的模型配置
config = get_agent_model_config("supervisor")
```

### 自定义 Temperature

```python
from src.llm.llm_model_client import get_agent_llm_client_with_temp

# 使用更高的 temperature 增加创造性
client = get_agent_llm_client_with_temp("implementer", temperature=0.8)
```

## 故障排查

### 问题 1: API Key 错误

**现象**: 调用模型时返回 401 错误

**排查步骤**:
```bash
# 检查 .env 文件
cat .env | grep DEFAULT_MODEL_API_KEY

# 检查 API Key 是否为空
# 如果为空，确保有 DEFAULT_MODEL_API_KEY 配置
```

### 问题 2: 模型名称错误

**现象**: 返回 "model not found" 错误

**排查步骤**:
```bash
# 检查模型名称拼写
cat .env | grep IMPLEMENTER_MODEL

# 确认模型在 API 提供商处可用
```

### 问题 3: Base URL 错误

**现象**: 连接超时或 404 错误

**排查步骤**:
```bash
# 检查 Base URL 格式
# 应该类似：https://dashscope.aliyuncs.com/compatible-mode/v1
cat .env | grep DEFAULT_MODEL_BASE_URL
```

### 调试代码

```python
from src.llm.llm_model_client import get_agent_model_config

# 打印所有 Agent 的配置
for agent in ["supervisor", "repo_analyst", "implementer", "reviewer", "tester"]:
    config = get_agent_model_config(agent)
    print(f"\n{agent}:")
    print(f"  Model: {config['model']}")
    print(f"  Base URL: {config['base_url']}")
    print(f"  API Key: {'*' * 10}")  # 不打印完整 API Key
```

## 支持的平台

本配置支持所有 OpenAI 兼容 API 的平台：

| 平台 | Base URL 示例 |
|------|---------------|
| 阿里云通义 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| 智谱 AI | `https://open.bigmodel.cn/api/paas/v4` |
| OpenAI | `https://api.openai.com/v1` |
| LocalAI | `http://localhost:8080/v1` |
| Ollama | `http://localhost:11434/v1` |
| vLLM | `http://localhost:8000/v1` |

## 最佳实践

1. **开发环境**: 使用默认配置即可，简化配置
2. **生产环境**: 为关键 Agent（如 Supervisor）配置更高阶的模型
3. **成本优化**: 为低频 Agent（如 Tester）配置成本更低的模型
4. **安全**: 不要在代码中硬编码 API Key，始终使用环境变量
