# Getting Started - Multi-Agent Programming Assistant

## 快速开始

### 1. 环境准备

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.template .env

# 编辑配置文件，填入你的API密钥
vim .env
```

### 3. 运行测试

```bash
# 运行测试脚本
python test_agents.py
```

### 4. 启动应用

```bash
# 启动Web应用
python main.py
```

访问 http://localhost:8000 查看界面。

## 项目结构

```
agentic-dev/
├── src/
│   ├── agents/                 # Agents
│   │   ├── supervisor.py      # Supervisor Agent
│   │   ├── repo_analyst_agent.py # RepoAnalyst Agent
│   │   ├── implementer_agent.py  # Implementer Agent
│   │   ├── reviewer.py         # Reviewer Agent
│   │   ├── implementer.py      # Implementer Agent (for fixing)
│   │   └── base_agent.py       # Base Agent class
│   ├── graph/
│   │   └── workflow.py        # LangGraph workflow
│   ├── mcp_servers/            # MCP Servers
│   │   ├── git_server.py      # Git operations
│   │   └── repo_search_server.py # Repository search
│   ├── skills/                # Skill system
│   │   ├── skill_registry.py  # Skill registry
│   │   ├── file_search_skill.py
│   │   ├── code_analysis_skill.py
│   │   ├── model_router.py
│   │   └── skill_initializer.py
│   ├── llm/
│   │   └── llm_model_client.py
│   ├── sandbox/
│   │   └── code_executor.py
│   ├── utils/
│   │   └── logger.py
│   └── memory/
│       └── session_manager.py
├── main.py                    # Entry point
├── test_agents.py            # Test script
├── .env.template             # Environment template
└── requirements.txt           # Dependencies
```

## 核心概念

### 1. Agents (五个核心角色)

- **Supervisor**: 任务规划和全局调度
- **RepoAnalyst**: 代码库上下文分析
- **Implementer**: 代码生成和修复
- **Reviewer**: 代码审查
- **Tester**: 测试生成和执行

### 2. Skill 系统

- 可复用的能力模块
- 权限管理
- 执行统计
- 成本估算

### 3. MCP 服务器

- Git Server: 版本控制操作
- Repo Search Server: 代码库检索

### 4. 工作流流程

```
用户输入
    ↓
Supervisor (任务规划)
    ↓
RepoAnalyst (代码库分析)
    ↓
Implementer (代码生成)
    ↓
Reviewer (代码审查) → 失败 → Implementer (修复)
    ↓
Tester (测试执行) → 失败 → Implementer (修复)
    ↓
Supervisor (最终汇总)
```

## 使用示例

### 1. 编程任务

```python
# 在Python代码中直接使用
from src.graph.workflow import create_workflow

workflow = create_workflow()
result = workflow.invoke({
    "task_description": "创建一个REST API，支持用户注册和登录",
    "session_id": "session-123",
    "iteration_count": 0,
    "max_iterations": 3
    # ... 其他必需字段
})
```

### 2. Web API

启动Web应用后，可以通过HTTP API调用：

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"task": "创建一个计算器类"}'
```

### 3. 扩展新Agent

```python
from src.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__("custom_agent")
    
    def execute_task(self, task):
        # 实现你的逻辑
        pass
```

## 配置说明

### 模型配置

项目支持多种模型路由：

- **主模型**: GLM-4.7（云端）
- **本地模型**: Qwen2.5-Coder-7B-Instruct
- **备用模型**: Gemini Free Tier

在 `.env` 中可以配置默认模型：

```env
DEFAULT_MODEL=glm-4.7
MAX_ITERATIONS=3
TEMPERATURE=0.7
```

### Skill 配置

Skills通过 `skill_registry` 注册：

```python
from src.skills.skill_registry import skill_registry

# 注册新技能
skill_registry.register_skill(my_skill, ["supervisor", "repo_analyst"])
```

## 测试和调试

### 1. 单元测试

```bash
# 运行特定Agent的测试
python -m pytest tests/test_supervisor.py

# 运行所有测试
python -m pytest tests/
```

### 2. 日志查看

```bash
# 查看日志
tail -f logs/agents.log

# 查看错误日志
grep ERROR logs/agents.log
```

### 3. 调试模式

设置 `DEBUG=true` 环境变量启用详细日志：

```bash
export DEBUG=true
python main.py
```

## 常见问题

### 1. API密钥错误

确保 `BIGMODEL_API_KEY` 已正确设置。

### 2. 模型连接失败

检查网络连接和API密钥是否有效。

### 3. 代码生成失败

确保RepoAnalyst能正确分析代码库。

### 4. 循环次数过多

调整 `MAX_ITERATIONS` 参数（默认3次）。

## 下一步

1. 实现Docker沙箱执行
2. 添加更多的MCP服务器
3. 实现评测系统
4. 添加Web UI界面
5. 集成更多编程语言支持