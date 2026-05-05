"""Command handler for CLI application"""

import json
import re
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path


class CommandHandler:
    """Handle CLI commands"""

    def __init__(self):
        """Initialize command handler"""
        self._commands: Dict[str, Callable] = {}
        self._aliases: Dict[str, str] = {}
        self._help_text: Dict[str, str] = {}

        # Register default commands
        self._register_default_commands()

    def _register_default_commands(self):
        """Register default commands"""
        self.register_command("help", self._cmd_help, "显示帮助信息")
        self.register_command("exit", self._cmd_exit, "退出程序")
        self.register_command("quit", self._cmd_exit, "退出程序", alias="exit")
        self.register_command("clear", self._cmd_clear, "清除对话历史")
        self.register_command("history", self._cmd_history, "显示对话历史")
        self.register_command("memory", self._cmd_memory, "显示记忆状态")
        self.register_command("search", self._cmd_search, "搜索代码库 (用法: /search <查询>)")
        self.register_command("task", self._cmd_task, "执行完整任务流程")
        self.register_command("session", self._cmd_session, "管理会话 (用法: /session new|id|list)")
        self.register_command("config", self._cmd_config, "显示配置信息")
        self.register_command("rag", self._cmd_rag, "RAG索引管理 (用法: /rag build|stats|clear)")
        self.register_command("save", self._cmd_save, "保存当前会话到文件")
        self.register_command("load", self._cmd_load, "加载会话文件 (用法: /load <文件路径>)")

    def register_command(
        self,
        name: str,
        handler: Callable,
        help_text: str,
        alias: Optional[str] = None
    ):
        """Register a command

        Args:
            name: Command name
            handler: Command handler function
            help_text: Help text for the command
            alias: Optional alias for the command
        """
        self._commands[name] = handler
        self._help_text[name] = help_text

        if alias:
            self._aliases[alias] = name

    def handle(self, input_str: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user input

        Args:
            input_str: User input string
            context: Context dictionary with memory, rag, etc.

        Returns:
            Response dictionary
        """
        # Check if it's a command
        if input_str.startswith("/"):
            return self._handle_command(input_str, context)

        # Otherwise, treat as a message
        return self._handle_message(input_str, context)

    def _handle_command(self, input_str: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle slash command"""
        # Parse command
        parts = input_str.strip().split(maxsplit=1)
        cmd_name = parts[0].lower().lstrip("/")
        cmd_args = parts[1] if len(parts) > 1 else ""

        # Resolve alias
        if cmd_name in self._aliases:
            cmd_name = self._aliases[cmd_name]

        # Check if command exists
        if cmd_name not in self._commands:
            return {
                "type": "error",
                "message": f"未知命令: /{cmd_name}\n使用 /help 查看可用命令"
            }

        # Execute command
        try:
            handler = self._commands[cmd_name]
            result = handler(cmd_args, context)
            return result
        except Exception as e:
            return {
                "type": "error",
                "message": f"命令执行错误: {str(e)}"
            }

    def _handle_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle regular message"""
        return {
            "type": "message",
            "message": message
        }

    # ==================== Default Command Handlers ====================

    def _cmd_help(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Help command"""
        help_lines = ["可用命令列表:\n"]

        for name, text in self._help_text.items():
            aliases = [k for k, v in self._aliases.items() if v == name]
            alias_str = f" (别名: /{', /'.join(aliases)})" if aliases else ""
            help_lines.append(f"  /{name} - {text}{alias_str}")

        return {
            "type": "info",
            "message": "\n".join(help_lines)
        }

    def _cmd_exit(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Exit command"""
        return {
            "type": "exit",
            "message": "再见！感谢使用 LangGraph 多Agent编程助手。"
        }

    def _cmd_clear(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Clear history command"""
        memory = context.get("memory")
        if memory:
            memory.clear_session()

        return {
            "type": "success",
            "message": "对话历史已清除。"
        }

    def _cmd_history(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Show history command"""
        memory = context.get("memory")
        if not memory:
            return {"type": "error", "message": "记忆系统未初始化"}

        history = memory.get_conversation_history(limit=20)

        if not history:
            return {"type": "info", "message": "对话历史为空"}

        return {
            "type": "history",
            "message": history
        }

    def _cmd_memory(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Show memory status"""
        memory = context.get("memory")
        if not memory:
            return {"type": "error", "message": "记忆系统未初始化"}

        summary = memory.get_summary()

        return {
            "type": "memory_summary",
            "message": summary
        }

    def _cmd_search(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search code command"""
        rag = context.get("rag")
        if not rag:
            return {"type": "error", "message": "RAG系统未初始化"}

        if not args:
            return {"type": "error", "message": "请提供搜索查询，用法: /search <查询内容>"}

        results = rag.search(args, top_k=5)

        return {
            "type": "rag_results",
            "message": results,
            "query": args
        }

    def _cmd_task(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute full task workflow"""
        if not args:
            return {"type": "error", "message": "请提供任务描述，用法: /task <任务描述>"}

        return {
            "type": "full_task",
            "message": args
        }

    def _cmd_session(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Session management"""
        args = args.strip().lower()

        if args == "new":
            new_session_id = f"session_{int(time.time() * 1000)}"
            memory = context.get("memory")
            if memory:
                memory.new_session(new_session_id)
            return {
                "type": "success",
                "message": f"新会话已创建: {new_session_id}"
            }

        elif args == "id":
            memory = context.get("memory")
            if memory:
                return {
                    "type": "info",
                    "message": f"当前会话ID: {memory.session_id}"
                }
            return {"type": "error", "message": "记忆系统未初始化"}

        elif args == "list":
            # Would need session storage to list
            return {
                "type": "info",
                "message": "会话列表功能尚未实现"
            }

        else:
            return {
                "type": "error",
                "message": "用法: /session new|id|list"
            }

    def _cmd_config(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Show configuration"""
        config_info = {
            "session_id": context.get("memory", {}).session_id if context.get("memory") else "unknown",
            "user_id": context.get("memory", {}).user_id if context.get("memory") else "unknown",
            "project_id": context.get("memory", {}).project_id if context.get("memory") else "unknown"
        }

        rag = context.get("rag")
        if rag:
            config_info["rag_stats"] = rag.get_stats()

        return {
            "type": "config",
            "message": json.dumps(config_info, indent=2)
        }

    def _cmd_rag(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """RAG management"""
        rag = context.get("rag")
        if not rag:
            return {"type": "error", "message": "RAG系统未初始化"}

        args = args.strip().lower()

        if args == "build":
            return {
                "type": "rag_build",
                "message": "开始重建索引..."
            }

        elif args == "stats":
            stats = rag.get_stats()
            return {
                "type": "info",
                "message": json.dumps(stats, indent=2)
            }

        elif args == "clear":
            rag.clear_index()
            return {
                "type": "success",
                "message": "RAG索引已清除"
            }

        else:
            return {
                "type": "error",
                "message": "用法: /rag build|stats|clear"
            }

    def _cmd_save(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Save session"""
        memory = context.get("memory")
        if not memory:
            return {"type": "error", "message": "记忆系统未初始化"}

        # Generate filename
        import time
        filename = args or f"session_{memory.session_id}_{int(time.time())}.json"
        filepath = Path("saved_sessions") / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Save memory state
        data = memory._short_term.to_dict()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {
            "type": "success",
            "message": f"会话已保存到: {filepath}"
        }

    def _cmd_load(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Load session"""
        if not args:
            return {"type": "error", "message": "用法: /load <文件路径>"}

        filepath = Path(args)
        if not filepath.exists():
            filepath = Path("saved_sessions") / args

        if not filepath.exists():
            return {"type": "error", "message": f"文件不存在: {args}"}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                "type": "load_session",
                "message": data,
                "filepath": str(filepath)
            }
        except Exception as e:
            return {"type": "error", "message": f"加载失败: {str(e)}"}

    def get_command_names(self) -> List[str]:
        """Get all command names"""
        return list(self._commands.keys())

    def get_help(self, command_name: str) -> Optional[str]:
        """Get help text for a command"""
        return self._help_text.get(command_name)