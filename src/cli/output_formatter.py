"""Output formatter for CLI application"""

import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.live import Live
    from rich.layout import Layout
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: rich not installed, using basic output")


class OutputFormatter:
    """Format and display output for CLI"""

    def __init__(self, use_rich: bool = True):
        """Initialize formatter

        Args:
            use_rich: Whether to use rich library for enhanced output
        """
        self.use_rich = use_rich and RICH_AVAILABLE

        if self.use_rich:
            self._console = Console()
        else:
            self._console = None

    def print(self, message: str, style: Optional[str] = None):
        """Print message

        Args:
            message: Message to print
            style: Style for rich output (info, success, error, warning)
        """
        if self.use_rich:
            if style == "error":
                self._console.print(f"[red]{message}[/red]")
            elif style == "success":
                self._console.print(f"[green]{message}[/green]")
            elif style == "warning":
                self._console.print(f"[yellow]{message}[/yellow]")
            elif style == "info":
                self._console.print(f"[blue]{message}[/blue]")
            else:
                self._console.print(message)
        else:
            prefix = ""
            if style == "error":
                prefix = "❌ "
            elif style == "success":
                prefix = "✅ "
            elif style == "warning":
                prefix = "⚠️ "
            elif style == "info":
                prefix = "ℹ️ "
            print(f"{prefix}{message}")

    def print_header(self, title: str, subtitle: Optional[str] = None):
        """Print header panel"""
        if self.use_rich:
            content = title
            if subtitle:
                content = f"{title}\n[dim]{subtitle}[/dim]"
            panel = Panel(content, style="bold blue", border_style="blue")
            self._console.print(panel)
        else:
            print(f"\n{'='*50}")
            print(f"  {title}")
            if subtitle:
                print(f"  {subtitle}")
            print(f"{'='*50}\n")

    def print_user_message(self, content: str):
        """Print user message"""
        if self.use_rich:
            panel = Panel(f"[bold]用户[/bold]: {content}", style="cyan", border_style="cyan")
            self._console.print(panel)
        else:
            print(f"\n>>> 用户: {content}\n")

    def print_assistant_message(self, content: str):
        """Print assistant message"""
        if self.use_rich:
            # Check for code blocks
            if "```" in content:
                self._print_markdown(content)
            else:
                panel = Panel(f"[bold]助手[/bold]: {content}", style="green", border_style="green")
                self._console.print(panel)
        else:
            print(f"\n<<< 助手: {content}\n")

    def _print_markdown(self, content: str):
        """Print markdown content with code highlighting"""
        if self.use_rich:
            markdown = Markdown(content)
            self._console.print(markdown)
        else:
            print(content)

    def print_code(self, code: str, language: str = "python"):
        """Print code block"""
        if self.use_rich:
            syntax = Syntax(code, language, theme="monokai", line_numbers=True)
            self._console.print(syntax)
        else:
            print(f"\n```{language}")
            print(code)
            print("```\n")

    def print_task_plan(self, task_plan: Dict[str, Any]):
        """Print task plan"""
        if self.use_rich:
            table = Table(title="📋 任务规划")
            table.add_column("ID", style="cyan")
            table.add_column("描述", style="white")
            table.add_column("复杂度", style="yellow")

            main_task = task_plan.get("task", "未知任务")
            self._console.print(f"\n[bold cyan]主任务: {main_task}[/bold cyan]")

            sub_tasks = task_plan.get("sub_tasks", [])
            for sub in sub_tasks:
                table.add_row(
                    str(sub.get("id", "?")),
                    sub.get("description", ""),
                    sub.get("complexity", "medium")
                )

            self._console.print(table)
        else:
            print(f"\n📋 任务规划:")
            print(f"  主任务: {task_plan.get('task', '未知任务')}")
            for sub in task_plan.get("sub_tasks", []):
                print(f"  #{sub.get('id', '?')}: {sub.get('description', '')}")

    def print_review_result(self, review_result: Dict[str, Any]):
        """Print review result"""
        score = review_result.get("score", "N/A")
        needs_revision = review_result.get("needs_revision", False)

        if self.use_rich:
            status = "[red]需要修改[/red]" if needs_revision else "[green]通过[/green]"
            self._console.print(f"\n🔍 代码审查结果: 评分 {score}/10 - {status}")

            issues = review_result.get("issues", [])
            if issues:
                table = Table(title="问题列表")
                table.add_column("严重性", style="yellow")
                table.add_column("描述", style="white")
                table.add_column("建议", style="cyan")

                for issue in issues:
                    table.add_row(
                        issue.get("severity", "warning"),
                        issue.get("description", ""),
                        issue.get("suggestion", "")
                    )
                self._console.print(table)
        else:
            status = "需要修改" if needs_revision else "通过"
            print(f"\n🔍 代码审查: 评分 {score}/10 - {status}")
            for issue in review_result.get("issues", []):
                print(f"  [{issue.get('severity', 'warning')}] {issue.get('description', '')}")

    def print_test_result(self, test_result: Dict[str, Any]):
        """Print test result"""
        execution = test_result.get("execution", {})

        passed = execution.get("passed", 0)
        failed = execution.get("failed", 0)
        total = execution.get("total", 0)

        if self.use_rich:
            status = "[green]全部通过[/green]" if failed == 0 else "[red]有失败[/red]"
            self._console.print(f"\n🧪 测试结果: {passed}/{total} 通过 - {status}")

            if failed > 0:
                output = execution.get("output", "")
                if output:
                    self._console.print(f"\n[red]失败日志:[/red]")
                    self._console.print(output[:500])
        else:
            status = "全部通过" if failed == 0 else "有失败"
            print(f"\n🧪 测试结果: {passed}/{total} 通过 - {status}")
            if failed > 0:
                print(f"  失败日志: {execution.get('output', '')[:200]}")

    def print_history(self, history: List[Dict[str, Any]], limit: int = 10):
        """Print conversation history"""
        if self.use_rich:
            table = Table(title="📜 对话历史")
            table.add_column("时间", style="cyan")
            table.add_column("角色", style="yellow")
            table.add_column("内容", style="white")

            for turn in history[-limit:]:
                timestamp = turn.get("timestamp", "")
                role = turn.get("role", "unknown")
                content = turn.get("content", "")[:50] + "..." if len(turn.get("content", "")) > 50 else turn.get("content", "")

                table.add_row(timestamp.split("T")[1][:8] if "T" in timestamp else timestamp, role, content)

            self._console.print(table)
        else:
            print(f"\n📜 对话历史 (最近{limit}条):")
            for turn in history[-limit:]:
                role = "用户" if turn.get("role") == "user" else "助手"
                content = turn.get("content", "")[:50]
                print(f"  [{role}] {content}")

    def print_memory_summary(self, summary: Dict[str, Any]):
        """Print memory summary"""
        if self.use_rich:
            table = Table(title="🧠 记忆状态")
            table.add_column("组件", style="cyan")
            table.add_column("状态", style="white")

            st = summary.get("short_term", {})
            lt = summary.get("long_term", {})

            table.add_row("会话ID", summary.get("session_id", ""))
            table.add_row("对话轮次", str(st.get("conversation_turns", 0)))
            table.add_row("任务状态", str(st.get("task_states", 0)))
            table.add_row("向量索引", str(lt.get("vector_index_size", 0)))
            table.add_row("历史任务", str(lt.get("historical_tasks_count", 0)))

            self._console.print(table)
        else:
            print(f"\n🧠 记忆状态:")
            print(f"  会话ID: {summary.get('session_id', '')}")
            print(f"  对话轮次: {summary.get('short_term', {}).get('conversation_turns', 0)}")
            print(f"  向量索引: {summary.get('long_term', {}).get('vector_index_size', 0)}")

    def print_rag_results(self, results: List[Dict[str, Any]], query: str):
        """Print RAG search results"""
        if self.use_rich:
            self._console.print(f"\n🔍 搜索结果 for: [bold]{query}[/bold]")

            for i, result in enumerate(results[:5]):
                metadata = result.get("metadata", {})
                score = result.get("score", 0)

                panel_content = f"文件: {metadata.get('file_path', 'unknown')}\n"
                panel_content += f"类型: {metadata.get('type', 'unknown')}\n"
                panel_content += f"相关度: {score:.4f}\n\n"
                panel_content += result.get("content", "")[:200]

                panel = Panel(panel_content, title=f"#{i+1}", style="green")
                self._console.print(panel)
        else:
            print(f"\n🔍 搜索结果 for: {query}")
            for i, result in enumerate(results[:5]):
                metadata = result.get("metadata", {})
                print(f"  #{i+1} {metadata.get('file_path', '')} (score: {result.get('score', 0):.4f})")

    def print_error(self, error: str):
        """Print error message"""
        self.print(error, style="error")

    def print_success(self, message: str):
        """Print success message"""
        self.print(message, style="success")

    def print_warning(self, message: str):
        """Print warning message"""
        self.print(message, style="warning")

    def print_info(self, message: str):
        """Print info message"""
        self.print(message, style="info")

    def clear_screen(self):
        """Clear terminal screen"""
        if self.use_rich:
            self._console.clear()
        else:
            os.system('clear' if os.name == 'posix' else 'cls')

    def show_progress(self, message: str, total: int = 100):
        """Show progress bar"""
        if self.use_rich:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                transient=True
            )
            task = progress.add_task(message, total=total)
            return progress, task
        return None, None

    def print_welcome(self):
        """Print welcome message"""
        if self.use_rich:
            welcome_text = """
[bold cyan]LangGraph 多Agent编程助手[/bold cyan]
[dim]CLI 多轮对话界面[/dim]

可用命令:
  /help      - 显示帮助
  /exit      - 退出程序
  /clear     - 清除对话历史
  /history   - 显示对话历史
  /memory    - 显示记忆状态
  /search    - 搜索代码库
  /task      - 执行完整任务流程

提示: 直接输入编程任务描述，助手会帮你完成代码生成。
"""
            panel = Panel(welcome_text, style="bold blue", border_style="blue")
            self._console.print(panel)
        else:
            print("\n" + "="*50)
            print("  LangGraph 多Agent编程助手 - CLI界面")
            print("="*50)
            print("\n可用命令: /help, /exit, /clear, /history, /memory, /search, /task")
            print("提示: 直接输入编程任务描述\n")