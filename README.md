# 🚀 基于 LangGraph + MCP + RAG 的多 Agent 编程助手

一个面向真实软件工程场景的多 Agent AI Coding System，采用状态机驱动工作流、多 Agent 协作、MCP 工具生态、RAG 代码检索与沙箱执行机制，实现代码生成、审查、测试、修复的自动化工程闭环。

# 📌 项目简介

随着大模型能力增强，AI Coding Agent 已经从简单代码补全逐渐发展为复杂任务执行系统。

但大量 AI Agent 项目仍存在明显问题：

- 无法理解真实代码仓库
- 缺乏任务拆解能力
- Tool 调用链路不可控
- 无法自动验证结果
- 缺乏失败修复机制
- 无法形成完整工程闭环

尤其在真实软件工程场景中，仅依赖 Prompt 与单轮生成远远不够。

因此，本项目尝试从“AI 软件工程系统”的角度出发，结合：

- LangGraph 状态机
- MCP Tool 生态
- 多 Agent 协作
- RAG 代码检索
- Docker 沙箱执行
- 自动测试反馈

构建一个具备真实工程执行能力的多 Agent 编程助手，通过 LangGraph 状态机实现任务调度与状态管理，让多个 Agent 在统一状态下协同完成复杂编程任务。

整个系统强调：

- 工程可控性
- Tool 调用标准化
- 自动测试验证
- 失败可回退
- 多 Agent 协同
- 可观测与可回放

# 🏗️ 系统整体架构

系统整体采用三层架构：

```text
Control Plane（控制层）
        ↓
Capability Plane（能力层）
        ↓
Execution Plane（执行层）

横切能力：
Observability / Logging / Security
```

整个系统围绕：

```text
Plan → Analyze → Implement → Review → Test → Fix → Deliver
```

闭环运行。

# 使用示例

```shell
(.venv) zhugenmi@myserver:~/work/agentic-dev$ python cli_entry.py 
Using file storage at: memory_store
Local ollama model ready: bge-m3 (base_url: http://localhost:11434)
Chunking files from /home/zhugenmi/work/agentic-dev...
Generating embeddings for 527 chunks...
  Embedded 100/527 chunks...
  Embedded 200/527 chunks...
  Embedded 300/527 chunks...
  Embedded 400/527 chunks...
  Embedded 500/527 chunks...
Index built successfully in 1810.65s
  Total chunks: 527
  Index size: 527
╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                              │
│ LangGraph 多Agent编程助手                                                                                                                                    │
│ CLI 多轮对话界面                                                                                                                                             │
│                                                                                                                                                              │
│ 可用命令:                                                                                                                                                    │
│   /help      - 显示帮助                                                                                                                                      │
│   /exit      - 退出程序                                                                                                                                      │
│   /clear     - 清除对话历史                                                                                                                                  │
│   /history   - 显示对话历史                                                                                                                                  │
│   /memory    - 显示记忆状态                                                                                                                                  │
│   /search    - 搜索代码库                                                                                                                                    │
│   /task      - 执行完整任务流程                                                                                                                              │
│                                                                                                                                                              │
│ 提示: 直接输入编程任务描述，助手会帮你完成代码生成。                                                                                                         │
│                                                                                                                                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
>>> 你好，介绍一下你自己
╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ 用户: 你好，介绍一下你自己                                                                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
正在思考...
╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ 助手: 你好！我是 **agentic-dev**，一个基于多 Agent 协作的 AI 编程助手，专门为真实软件工程场景设计。                                                          │
│                                                                                                                                                              │
│ 我不仅仅是一个代码补全工具，而是围绕 **Plan → Analyze → Implement → Review → Test → Fix → Deliver** 的完整工程闭环构建的智能系统。我的核心能力包括：         │
│                                                                                                                                                              │
│ - 🧠 **理解真实代码仓库**：通过 RAG 代码检索，我能深入理解项目结构和上下文。                                                                                 │
│ - 🧩 **任务拆解与调度**：借助 LangGraph 状态机，我可以把复杂任务拆分成可执行的子任务，并协调多个 Agent 有序协作。                                            │
│ - 🔧 **标准化 Tool 调用**：基于 MCP Tool 生态，我能安全、可控地调用各种工具，避免链路失控。                                                                  │
│ - 🧪 **自动测试与验证**：在 Docker 沙箱中执行代码并自动运行测试，确保结果正确。                                                                              │
│ - 🔄 **失败自动修复**：检测到错误后，我能回退并尝试其他方案，形成自愈能力。                                                                                  │
│ - 🪵 **可观测与可回放**：所有执行过程可追踪、可复现，方便调试与优化。                                                                                        │
│                                                                                                                                                              │
│ 我的架构分为三层：控制层（任务规划与决策）、能力层（工具与技能）、执行层（沙箱执行与反馈），并贯穿日志、安全等横切能力，保证整个开发过程工程可控。           │
│                                                                                                                                                              │
│ 简单来说，我是一个能真正帮你把想法变成可运行、经过验证的代码的 AI 软件工程伙伴。有什么任务需要我帮忙吗？😊                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
>>> /search mcp

🔍 搜索结果 for: mcp
╭───────────────────────────────────────────────────────────────────────────── #1 ─────────────────────────────────────────────────────────────────────────────╮
│ 文件: /home/zhugenmi/work/agentic-dev/src/tools/mcp_config.py                                                                                                │
│ 类型: class                                                                                                                                                  │
│ 相关度: 612.9605                                                                                                                                             │
│                                                                                                                                                              │
│ Class: MCPServerConfig                                                                                                                                       │
│ File: /home/zhugenmi/work/agentic-dev/src/tools/mcp_config.py                                                                                                │
│ Line: 12                                                                                                                                                     │
│                                                                                                                                                              │
│ Docstring:                                                                                                                                                   │
│ Configuration for a single MCP Server                                                                                                                        │
│                                                                                                                                                              │
│ Definition:                                                                                                                                                  │
│ class MCPServerConfig(BaseModel):                                                                                                                            │
│     """Co                                                                                                                                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭───────────────────────────────────────────────────────────────────────────── #2 ─────────────────────────────────────────────────────────────────────────────╮
│ 文件: /home/zhugenmi/work/agentic-dev/README.md                                                                                                              │
│ 类型: section                                                                                                                                                │
│ 相关度: 632.1557                                                                                                                                             │
│                                                                                                                                                              │
│ Section: 🧩 MCP Server 设计                                                                                                                                  │
│ File: /home/zhugenmi/work/agentic-dev/README.md                                                                                                              │
│                                                                                                                                                              │
│ ## 🧩 MCP Server 设计                                                                                                                                        │
│ 项目基于 MCP（Model Context Protocol）构建统一工具协议。                                                                                                     │
│                                                                                                                                                              │
│ MCP 的目标是：让 Agent 像操作系统一样调用工具，通过 MCP Server 将外部能力标准化。                                                                            │
│                                                                                                                                                              │
│ 项目当前主要接入了两                                                                                                                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭───────────────────────────────────────────────────────────────────────────── #3 ─────────────────────────────────────────────────────────────────────────────╮
│ 文件: /home/zhugenmi/work/agentic-dev/src/tools/mcp_client.py                                                                                                │
│ 类型: module                                                                                                                                                 │
│ 相关度: 640.1147                                                                                                                                             │
│                                                                                                                                                              │
│ Module: /home/zhugenmi/work/agentic-dev/src/tools/mcp_client.py                                                                                              │
│                                                                                                                                                              │
│ MCP Protocol Client - connects to MCP Servers via stdio transport                                                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭───────────────────────────────────────────────────────────────────────────── #4 ─────────────────────────────────────────────────────────────────────────────╮
│ 文件: /home/zhugenmi/work/agentic-dev/src/tools/mcp_client.py                                                                                                │
│ 类型: class                                                                                                                                                  │
│ 相关度: 644.3408                                                                                                                                             │
│                                                                                                                                                              │
│ Class: MCPConnectionError                                                                                                                                    │
│ File: /home/zhugenmi/work/agentic-dev/src/tools/mcp_client.py                                                                                                │
│ Line: 32                                                                                                                                                     │
│                                                                                                                                                              │
│ Docstring:                                                                                                                                                   │
│ Raised when an MCP Server connection fails                                                                                                                   │
│                                                                                                                                                              │
│ Definition:                                                                                                                                                  │
│ class MCPConnectionError(Exception)                                                                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭───────────────────────────────────────────────────────────────────────────── #5 ─────────────────────────────────────────────────────────────────────────────╮
│ 文件: /home/zhugenmi/work/agentic-dev/src/tools/tool_executor.py                                                                                             │
│ 类型: method                                                                                                                                                 │
│ 相关度: 648.1699                                                                                                                                             │
│                                                                                                                                                              │
│ Function: ToolExecutor.__init__                                                                                                                              │
│ File: /home/zhugenmi/work/agentic-dev/src/tools/tool_executor.py                                                                                             │
│ Line: 56                                                                                                                                                     │
│                                                                                                                                                              │
│ Signature: __init__(self, mcp_manager)                                                                                                                       │
│                                                                                                                                                              │
│ Code:                                                                                                                                                        │
│     def __init__(self, mcp_manager: Optional[MC                                                                                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
>>> 本项目中历史会话是如何实现的，存在什么问题？
╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ 用户: 本项目中历史会话是如何实现的，存在什么问题？                                                                                                           │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
正在思考...
╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ 助手: 基于你提供的代码片段，项目中历史会话的实现方式如下：                                                                                                   │
│                                                                                                                                                              │
│ - **存储层**：对话历史以字典列表形式存放在 `ShortTermMemory` 中，每个元素包含 `timestamp`、`role`、`content` 等字段。                                        │
│ - **访问接口**：`MemoryManager.get_conversation_history(limit)` 对外暴露获取历史的统一入口，内部调用 `ShortTermMemory.get_conversation_history(limit,        │
│ role_filter)`，支持按返回条数和角色过滤。                                                                                                                    │
│ - **展示层**：`OutputFormatter.print_history(history, limit=10)` 接收历史列表，取末尾 `limit` 条，使用 Rich 表格打印时间、角色和内容。                       │
│                                                                                                                                                              │
│ 存在的主要问题：                                                                                                                                             │
│                                                                                                                                                              │
│ 1. **无持久化，重启丢失**                                                                                                                                    │
│    `ShortTermMemory` 顾名思义是短期记忆，数据仅保存在内存中。程序退出或崩溃后所有历史会话消失，无法满足需要长期保留对话上下文的场景。                        │
│                                                                                                                                                              │
│ 2. **缺乏会话隔离**                                                                                                                                          │
│    所有对话历史混存在同一个列表中，没有 `session_id` 或类似标识。多用户、多会话并发时会相互干扰，取出的历史可能包含其他会话的记录。                          │
│                                                                                                                                                              │
│ 3. **默认值不一致，可能导致全量查询**                                                                                                                        │
│    `MemoryManager` 和 `ShortTermMemory` 的 `limit` 默认均为 `None`（返回全部），而 `OutputFormatter.print_history` 的 `limit` 默认为                         │
│ 10。如果调用链中没有显式传递 `limit`，会先取出全部历史，再由展示层截取最后 10 条，当历史较长时造成不必要的内存和性能开销。                                   │
│                                                                                                                                                              │
│ 4. **缺少容量上限与自动裁剪**                                                                                                                                │
│    历史列表无限增长，没有最大长度限制或淘汰策略（如固定窗口、FIFO），长时间运行会持续占用内存直至溢出。                                                      │
│                                                                                                                                                              │
│ 5. **接口能力未充分暴露**                                                                                                                                    │
│    `MemoryManager.get_conversation_history` 的签名中仅出现了 `limit`，未暴露 `ShortTermMemory` 已有的 `role_filter`                                          │
│ 参数，限制了上层仅获取用户或助手消息的灵活性。                                                                                                               │
│                                                                                                                                                              │
│ 6. **时间戳处理粗糙**                                                                                                                                        │
│    `print_history` 中直接使用 `turn.get("timestamp", "")`，如果某条历史缺少时间戳则显示空字符串，没有统一的生成或校验机制，可能导致展示混乱。                │
│                                                                                                                                                              │
│ 7. **缺少分页与倒序支持**                                                                                                                                    │
│    只能获取“最近 N 条”，无法按时间倒序、分页或基于游标拉取更早的历史，对长对话的浏览不友好。                                                                 │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
>>> 请帮我修改对应的代码
╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ 用户: 请帮我修改对应的代码                                                                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
正在思考...
根据你的需求，我分析了历史会话模块现有实现的问题，并针对性地设计了改进方案。以下是对 ShortTermMemory、MemoryManager 和 OutputFormatter                          
的修改建议及示例代码，你可以根据项目实际情况进行调整。                                                                                                          

----------------------------------------------------------------------------------------------------------------------------------------------------------------

1. 增加会话隔离（session_id）                                                                                                                                   

为每个会话分配唯一标识，所有历史记录按 session_id 隔离存储。                                                                                                    

修改点：                                                                                                                                                        

 • ShortTermMemory 内部使用字典 {session_id: [messages]} 替代原先的单一列表。                                                                                   
 • 所有方法增加 session_id 参数。                                                                                                                               

                                                                                                                                                                
 class ShortTermMemory:                                                                                                                                         
     def __init__(self):                                                                                                                                        
         self._storage: Dict[str, List[Dict[str, Any]]] = {}  # session_id -> history list                                                                      
                                                                                                                                                                
     def add_message(self, session_id: str, role: str, content: str):                                                                                           
         if session_id not in self._storage:                                                                                                                    
             self._storage[session_id] = []                                                                                                                     
         self._storage[session_id].append({                                                                                                                     
             "timestamp": datetime.now().isoformat(),                                                                                                           
             "role": role,                                                                                                                                      
             "content": content                                                                                                                                 
         })                                                                                                                                                     
                                                                                                                                                                
     def get_conversation_history(self, session_id: str, limit: int = 10,                                                                                       
                                  role_filter: Optional[str] = None) -> List[Dict[str, Any]]:                                                                   
         history = self._storage.get(session_id, [])                                                                                                            
         if role_filter:                                                                                                                                        
             history = [h for h in history if h.get("role") == role_filter]                                                                                     
         # 返回最近 limit 条（正序）                                                                                                                            
         return history[-limit:] if limit else history                                                                                                          
                                                                                                                                                                

----------------------------------------------------------------------------------------------------------------------------------------------------------------

2. 持久化存储（防止重启丢失）                                                                                                                                   

引入 SQLite 或 JSON 文件实现持久化，同时保留内存缓存以提升性能。示例使用 SQLite：                                                                               

                                                                                                                                                                
 import sqlite3                                                                                                                                                 
 import json                                                                                                                                                    
                                                                                                                                                                
 class PersistentMemory(ShortTermMemory):                                                                                                                       
     def __init__(self, db_path: str = "chat_history.db"):                                                                                                      
         super().__init__()                                                                                                                                     
         self.db_path = db_path                                                                                                                                 
         self._init_db()                                                                                                                                        
                                                                                                                                                                
     def _init_db(self):                                                                                                                                        
         with sqlite3.connect(self.db_path) as conn:                                                                                                            
             conn.execute("""                                                                                                                                   
                 CREATE TABLE IF NOT EXISTS history (                                                                                                           
                     session_id TEXT,                                                                                                                           
                     timestamp TEXT,                                                                                                                            
                     role TEXT,                                                                                                                                 
                     content TEXT                                                                                                                               
                 )                                                                                                                                              
             """)                                                                                                                                               
             conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON history(session_id, timestamp)")                                                           
                                                                                                                                                                
     def add_message(self, session_id: str, role: str, content: str):                                                                                           
         super().add_message(session_id, role, content)                                                                                                         
         with sqlite3.connect(self.db_path) as conn:                                                                                                            
             conn.execute(                                                                                                                                      
                 "INSERT INTO history VALUES (?, ?, ?, ?)",                                                                                                     
                 (session_id, datetime.now().isoformat(), role, content)                                                                                        
             )                                                                                                                                                  
                                                                                                                                                                
     def get_conversation_history(self, session_id: str, limit: int = 10,                                                                                       
                                  role_filter: Optional[str] = None,                                                                                            
                                  before_timestamp: Optional[str] = None) -> List[Dict[str, Any]]:                                                              
         # 优先从内存取，若未命中则从数据库加载并缓存                                                                                                           
         if session_id not in self._storage:                                                                                                                    
             self._load_from_db(session_id)                                                                                                                     
         return super().get_conversation_history(session_id, limit, role_filter)                                                                                
                                                                                                                                                                
     def _load_from_db(self, session_id: str):                                                                                                                  
         with sqlite3.connect(self.db_path) as conn:                                                                                                            
             rows = conn.execute(                                                                                                                               
                 "SELECT timestamp, role, content FROM history WHERE session_id=? ORDER BY timestamp",                                                          
                 (session_id,)                                                                                                                                  
             ).fetchall()                                                                                                                                       
         self._storage[session_id] = [                                                                                                                          
             {"timestamp": ts, "role": role, "content": content}                                                                                                
             for ts, role, content in rows                                                                                                                      
         ]                                                                                                                                                      
                                                                                                                                                                

----------------------------------------------------------------------------------------------------------------------------------------------------------------

```

# 🧠 Control Plane：基于 LangGraph 的状态机工作流

控制层基于 LangGraph 构建状态机式工作流。

相比传统 Chain，LangGraph 更适合复杂 Agent 系统，因为它支持：

- 条件分支
- 循环
- 状态持久化
- 中断恢复
- Human-in-the-loop

系统中每个 Agent 都对应一个独立节点：

```text
Supervisor
    ↓
RepoAnalyst
    ↓
Implementer
    ↓
Reviewer
    ↓
Tester
```

节点之间通过条件边进行流转。

例如：

- Review 未通过 → 回到 Implementer
- 测试失败 → 回到 RepoAnalyst
- 超过最大修复轮次 → 中止任务

整个工作流并不是“自由生成”，而是一个受控的软件工程状态机。

---

# 🤖 多 Agent 协作设计

系统包含 5 个核心 Agent。

Supervisor 不直接编写代码，而是负责需求解析、任务拆解、工作流调度与验收标准定义。

RepoAnalyst 负责代码仓库分析与上下文构建。系统会结合代码检索、文件结构分析与依赖关系定位最相关代码片段，为后续 Agent 提供上下文。

Implementer 只负责生成最小 patch，而不是整文件重写。系统要求 patch 以 diff 格式输出，从而降低破坏性修改，提高自动修复稳定性。

Reviewer 不生成代码，只负责代码审查。其核心目标是判断 patch 是否满足需求、是否引入副作用以及是否符合仓库风格。

Tester 负责运行测试、执行 lint、收集失败日志，并将测试结果反馈给上游 Agent，形成自动修复闭环。

整个系统更像一个“小型研发团队”，而不是单一大模型。

---


# 🧰 2. 能力层（Capability Plane）

能力层是整个系统的核心。

这一层主要由：

- MCP Tool Ecosystem
- Tool Calling
- RAG 检索
- Memory
- Model Router

组成。

## 🧩 MCP Server 设计
项目基于 MCP（Model Context Protocol）构建统一工具协议。

MCP 的目标是：让 Agent 像操作系统一样调用工具，通过 MCP Server 将外部能力标准化。

项目当前主要接入了两个官方 MCP Server：

- GitHub 官方 MCP Server
- Filesystem MCP Server

GitHub MCP Server 主要用于：

- 仓库信息获取
- Commit 分析
- PR 查询
- Issue 上下文获取

Filesystem MCP Server 主要用于：

- 文件读取
- 目录遍历
- Patch 写入
- 本地仓库分析

RepoAnalyst 会通过 Filesystem MCP Server 获取仓库上下文，而 Implementer 会基于文件内容生成 patch。

除了官方 MCP Server 之外，项目中还本地实现了一个简单的自定义 MCP Server，主要用于学习 MCP 协议与 Tool Calling 流程。

这个自定义 MCP Server 主要提供：

```text
search_code_snippet
read_symbol_context
collect_project_metadata
```

等能力。

其目的并不是实现复杂业务，而是完整跑通：

```text
Agent
→ Tool Calling
→ MCP Client
→ MCP Server
→ Tool Execution
→ Result Return
```

整个调用链路。

通过这个过程，可以更深入理解 MCP 的：

- Tool Schema
- Tool Discovery
- Tool Invocation
- Client/Server 通信机制

以及 MCP 在 AI Agent 工程化中的作用。

---

## 🛠️ Tool Calling 与权限控制

系统内部构建了统一 Tool Registry。

每个 Tool 都包含：

- Tool Name
- Description
- JSON Schema
- Timeout
- Permission Level

所有 Tool 调用都通过：

```text
Tool Calling
→ Tool Executor
→ MCP Server
```

统一执行。

同时，不同 Agent 拥有不同 Tool 权限。

例如：

- Supervisor 只能读取状态
- RepoAnalyst 只能读取仓库
- Implementer 只能生成 patch
- Tester 才能执行测试命令

这种设计可以降低：

- 越权调用
- Prompt Injection
- 危险命令执行

带来的风险。

---

## 📚 RAG：代码检索系统

为了让 Agent 能够理解真实代码仓库，项目实现了基于 FAISS 的代码向量检索系统。

系统会对代码仓库建立：

- 文件级索引
- 函数级索引
- Symbol 索引

RepoAnalyst 会结合：

- 文件结构
- Import Graph
- 向量检索

定位最相关代码上下文。

相比简单全文搜索，这种方式更适合复杂仓库分析。

---

## 🧠 Memory：上下文记忆机制

系统同时实现了短期记忆与长期记忆。

短期记忆基于 LangGraph State，主要保存：

- 当前任务状态
- patch 历史
- Review 结果
- 测试日志

长期记忆则保存：

- 历史任务
- 常见修复模式
- 高质量 patch
- 常见 bug 案例

用于提升复杂任务中的连续推理能力。

---

# ⚙️ Execution Plane：执行层

执行层负责真正执行代码，而不仅仅是“生成代码”。

系统使用 Git Worktree 为每个任务创建独立工作目录，从而避免污染主分支，并支持快速回滚。

所有危险操作都运行在 Docker Sandbox 中，包括：

- 安装依赖
- 执行 pytest
- shell command
- build

系统默认：

- 禁止访问宿主机
- 默认禁网
- 限制 CPU / 内存
- 限制目录权限

从而保证执行安全性。

---

# 🧪 评测体系

核心指标：

- 任务成功率
- 平均修复轮数
- 测试通过率
- Patch 质量
- Token 消耗
- 平均响应时间

基于 HumanEval 验证代码生成能力。