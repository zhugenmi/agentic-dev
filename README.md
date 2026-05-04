# 🚀 基于 LangGraph + MCP + Skill 的多 Agent 编程助手

 一个可控、可回放、可评测、可扩展的多 Agent 软件工程系统

---

## 📌 项目简介

本项目实现了一个面向真实软件工程场景的多 Agent 编程助手，系统采用**状态机驱动 + 工具标准化 + 沙箱执行 + 闭环反馈**的工程化设计，能够自动完成：
- 需求理解
- 任务拆解
- 代码库分析
- 代码 patch 生成
- 代码审查
- 测试生成与执行
- 失败修复
- 最终交付
---
## 🛠️ 快速开始
### 环境准备
```shell
git clone <repo>
cd project

# Python 环境
pip install -r requirements.txt

# 启动 Docker
docker compose up -d
```

### 启动 MCP Servers
```shell
python mcp/git_server.py
python mcp/repo_server.py
python mcp/test_server.py
python mcp/sandbox_server.py
```
### 运行 Agent 系统
```shell
python run_agent.py --task "修复登录接口 bug"
```

## 🧠 项目背景

传统 AI Agent 项目存在明显不足：
- 无法处理真实代码库上下文
- 缺乏测试验证机制
- 工具调用不可控
- 没有评测体系
- 无法形成工程闭环

本项目的目标是构建一个：**贴近真实软件开发流程的 AI 编程系统**

---

## 🎯 项目目标

系统可以接收任务，例如：
- “实现一个xxx系统”
- “为项目增加 JWT 登录功能”
- “修复接口边界 bug”
- “为模块补充单元测试”

并自动执行完整流程：

Plan → Analyze → Implement → Review → Test → Fix → Loop → Deliver

---

## 🏗️ 总体架构

### 三层控制 + 一条闭环

```text
Control Plane（控制层）
        ↓
Capability Plane（能力层）
        ↓
Execution Plane（执行层）

横切能力：Observability / Logging / Security

核心闭环：
Plan → Analyze → Implement → Review → Test → Fix → Loop → Deliver
```

---

## 🧩 系统分层设计

---

### 🧠 1. 控制层（Control Plane）

基于 **LangGraph**

#### 实际实现：

- 使用 `StateGraph` 构建状态机
- 使用 `Pydantic` 定义全局 State
- 每个 Agent 对应一个 Node
- 使用 Edge 控制流程跳转
- 使用 checkpoint 持久化执行状态
- 使用 interrupt 支持人工审批

#### 状态结构（核心字段）：

```python
class AgentState(BaseModel):
    task: dict
    plan: dict
    repo_context: dict
    patch: str
    review_result: dict
    test_result: dict
    iteration_count: int
    max_iterations: int = 5
    status: str
```
### 🧰 2. 能力层（Capability Plane）

由 MCP + Skill + RAG + Memory 组成

#### 2.1 MCP 工具层

##### Git MCP Server

提供：
- git_status
- git_diff
- apply_patch
- checkout_branch
- commit_changes

##### Repo Search MCP Server

提供：
- search_file
- search_symbol
- read_file
- list_directory
- analyze_imports

##### Test Runner MCP Server

提供：
- run_tests
- run_pytest
- run_lint
- collect_coverage

##### andbox Executor MCP Server

提供：
- exec_command
- install_dependencies
- run_in_container
- collect_logs
#### 2.2 Skill 层）

当前项目内 Skill：
- repo_search_skill
- file_read_skill
- patch_generate_skill
- patch_apply_skill
- diff_review_skill
- test_generate_skill
- test_run_skill
- lint_check_skill
- security_scan_skill

每个 Skill 包含：
- Prompt 模板
- 可调用 MCP tools
- 输入输出 schema
- 风险等级标记
#### 2.3 RAG（代码检索）

实现方式：基于代码库建立索引（文件级 + 符号级）
支持：
- -文件检索
- 函数检索
- 相似代码片段检索

RepoAnalyst 使用 RAG 获取上下文
#### 2.4 Memory（记忆系统）
短期记忆（LangGraph State）
- 当前任务状态
- 中间输出
- 错误日志
- patch 记录

长期记忆（存储）
- 历史任务记录
- 常见 bug 模式
- 代码片段库
### ⚙️ 3. 执行层（Execution Plane）
实际实现：
- Git Worktree
- 每个任务创建独立 worktree
- 避免污染主分支
- 支持快速回滚
- Docker Sandbox
- 容器隔离执行
- 禁止访问宿主机
- 默认禁网
- 限制 CPU / 内存
- 测试执行环境
- 安装依赖
- 执行 pytest
- 收集失败日志
- 输出覆盖率
### 🔍 4. 横切能力（Cross-cutting）
可观测性（Observability）
- trace_id（每个任务唯一）
- Agent 执行日志
- token 使用统计
- 每步耗时

日志系统
- 工具调用日志
- 测试日志
- patch 记录
- 错误堆栈

安全控制
- MCP 工具权限控制
- 危险操作审批
- 执行命令审计

🔁 核心闭环流程
1. Plan（Supervisor）
2. Analyze（RepoAnalyst）
3. Implement（Implementer）
4. Review（Reviewer）
5. Test（Tester）
6. Fix（回到 Implementer）
7. Loop（最多 5 次）
8. Deliver（Supervisor）

## 🤖 多 Agent 设计
### 1️⃣ Supervisor
负责：
- 需求解析
- 任务拆解
- 调度 Agent
- 定义验收标准
### 2️⃣ RepoAnalyst

负责：

- 代码检索
- 文件定位
- 接口分析
- 依赖分析
### 3️⃣ Implementer

负责：
- 生成 patch（diff 格式）
- 最小修改原则
- 保持代码一致性
4️⃣ Reviewer

输出结构：
```python
{
  "status": "pass | needs_revision | reject",
  "issues": [],
  "suggestions": []
}
```
### 5️⃣ Tester

负责：

- 生成测试代码
- 执行测试
- 收集日志
- 判断失败原因
## 🧠 模型路由（Model Router）

实现统一路由：
```text
router:
  supervisor:
    primary: glm-4.7
    fallback:
      - gemini-free
      - glm-4.7-flash

  repo_analyst:
    primary: qwen-coder-local
    fallback:
      - glm-4.7-flash

  implementer:
    primary: glm-4.7
    fallback:
      - qwen-coder-local

  reviewer:
    primary: glm-4.7
    fallback:
      - gemini-free

  tester:
    primary: qwen-coder-local
    fallback:
      - glm-4.7-flash
```
## 🧪 评测体系
指标：
- 任务成功率
- 平均修复轮数
- 测试通过率
- patch 质量
- token 消耗
- 平均延迟
- Benchmark

采用：SWE-bench 风格评测

特点：

- 真实 GitHub issue
- Docker 执行测试
- 自动验证 patch 是否生效

## 📊 项目亮点
✅ 可控性
- 状态机驱动
- 支持回放
- 支持人工介入
✅ 标准化
- MCP 工具协议
- Skill 能力封装
✅ 工程真实性
- Git + Docker
- 测试驱动验证
✅ 可扩展性
- Agent 可扩展
- Skill 可复用
- MCP 可新增
✅ 可展示性
- 执行流程
- patch diff
- 测试日志
- trace 轨迹
-成功率统计