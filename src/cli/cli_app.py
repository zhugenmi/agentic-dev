"""CLI application for multi-turn conversation"""

import os
import sys
import time
import json
import signal
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load environment
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

from src.memory.memory_manager import MemoryManager
from src.rag.code_rag import CodeRAG, create_code_rag
from src.llm.llm_model_client import get_llm_client
from src.graph.workflow import create_workflow, format_workflow_result
from .command_handler import CommandHandler
from .output_formatter import OutputFormatter


class CLIApp:
    """CLI application for multi-turn conversation with Agent workflow"""

    def __init__(
        self,
        session_id: Optional[str] = None,
        user_id: str = "default",
        project_id: str = "default",
        use_rich: bool = True,
        use_local_embedding: bool = True
    ):
        """Initialize CLI application

        Args:
            session_id: Session identifier
            user_id: User identifier
            project_id: Project identifier
            use_rich: Use rich library for enhanced output
            use_local_embedding: Use local embedding model for RAG
        """
        self.session_id = session_id or f"session_{int(time.time() * 1000)}"
        self.user_id = user_id
        self.project_id = project_id
        self.running = True

        # Initialize components
        self._init_components(use_rich, use_local_embedding)

        # Context for command handler
        self._context = {
            "memory": self._memory,
            "rag": self._rag,
            "llm": self._llm,
            "workflow": self._workflow
        }

        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_interrupt)

    def _init_components(self, use_rich: bool, use_local_embedding: bool):
        """Initialize all components"""
        # Output formatter
        self._formatter = OutputFormatter(use_rich=use_rich)

        # Memory manager
        self._memory = MemoryManager(
            session_id=self.session_id,
            user_id=self.user_id,
            project_id=self.project_id
        )

        # RAG system
        try:
            self._rag = create_code_rag(
                repo_path=str(PROJECT_ROOT),
                use_local_embedding=use_local_embedding
            )
        except Exception as e:
            self._formatter.print_warning(f"RAG初始化失败: {e}")
            self._rag = None

        # LLM client
        try:
            self._llm = get_llm_client()
        except Exception as e:
            self._formatter.print_warning(f"LLM初始化失败: {e}")
            self._llm = None

        # Workflow
        try:
            self._workflow = create_workflow()
        except Exception as e:
            self._formatter.print_warning(f"Workflow初始化失败: {e}")
            self._workflow = None

        # Command handler
        self._command_handler = CommandHandler()

    def _handle_interrupt(self, signum, frame):
        """Handle Ctrl+C interrupt"""
        self._formatter.print_info("\n按 Ctrl+C 再次退出，或输入 /exit")
        self.running = False

    def run(self):
        """Run the CLI application"""
        self._formatter.print_welcome()

        while self.running:
            try:
                # Get user input
                user_input = self._get_input()

                if not user_input.strip():
                    continue

                # Handle input
                response = self._command_handler.handle(user_input, self._context)

                # Process response
                self._process_response(response, user_input)

            except KeyboardInterrupt:
                self._formatter.print_info("\n退出程序...")
                break
            except Exception as e:
                self._formatter.print_error(f"错误: {str(e)}")

    def _get_input(self) -> str:
        """Get user input"""
        try:
            # Use prompt_toolkit if available
            from prompt_toolkit import prompt
            from prompt_toolkit.history import FileHistory

            history_file = PROJECT_ROOT / "cli_history.txt"
            return prompt(
                ">>> ",
                history=FileHistory(str(history_file))
            )
        except ImportError:
            return input(">>> ")

    def _process_response(self, response: Dict[str, Any], original_input: str):
        """Process and display response"""
        response_type = response.get("type", "unknown")
        message = response.get("message")

        if response_type == "exit":
            self._formatter.print_success(message)
            self.running = False

        elif response_type == "error":
            self._formatter.print_error(message)

        elif response_type == "success":
            self._formatter.print_success(message)

        elif response_type == "info":
            self._formatter.print_info(message)

        elif response_type == "warning":
            self._formatter.print_warning(message)

        elif response_type == "history":
            self._formatter.print_history(message)

        elif response_type == "memory_summary":
            self._formatter.print_memory_summary(message)

        elif response_type == "rag_results":
            self._formatter.print_rag_results(message, response.get("query", ""))

        elif response_type == "rag_build":
            self._rebuild_rag_index()

        elif response_type == "load_session":
            self._load_session(message)

        elif response_type == "config":
            self._formatter.print(message)

        elif response_type == "message":
            # Regular message - process through workflow
            self._process_user_message(message)

        elif response_type == "full_task":
            # Full task workflow
            self._execute_full_workflow(message)

        else:
            self._formatter.print(str(message))

    def _process_user_message(self, message: str):
        """Process user message through conversation"""
        # Add to memory
        self._memory.add_user_message(message)

        # Display user message
        self._formatter.print_user_message(message)

        # Get context from memory and RAG
        context_text = ""
        if self._rag:
            rag_context = self._rag.get_context_for_query(message, max_tokens=500)
            context_text += rag_context

        memory_context = self._memory.get_context_for_prompt(max_tokens=500)
        context_text += memory_context

        # Generate response using LLM
        if self._llm:
            self._formatter.print_info("正在思考...")

            # Build prompt with context
            prompt = f"{context_text}\n\n用户问题: {message}\n\n请回答用户问题:"

            try:
                response = self._llm.invoke(prompt)
                content = response.content if hasattr(response, 'content') else str(response)

                # Add to memory
                self._memory.add_assistant_message(content)

                # Display response
                self._formatter.print_assistant_message(content)

            except Exception as e:
                self._formatter.print_error(f"LLM响应失败: {str(e)}")
                self._formatter.print_assistant_message("抱歉，我暂时无法响应。请稍后再试。")

        else:
            self._formatter.print_warning("LLM未初始化，无法生成响应")

    def _execute_full_workflow(self, task_description: str):
        """Execute full Agent workflow"""
        if not self._workflow:
            self._formatter.print_error("Workflow未初始化")
            return

        # Add to memory
        self._memory.add_user_message(f"[TASK] {task_description}")
        self._formatter.print_user_message(task_description)

        self._formatter.print_info("启动多Agent工作流...")
        self._formatter.print_info("="*50)

        # Get context
        context_text = ""
        if self._rag:
            context_text = self._rag.get_context_for_query(task_description, max_tokens=1000)

        memory_context = self._memory.get_context_for_prompt(max_tokens=500)

        # Set task state
        task_id = f"task_{int(time.time() * 1000)}"
        self._memory.set_current_task(task_id, {
            "description": task_description,
            "status": "running",
            "started_at": datetime.now().isoformat()
        })

        try:
            # Invoke workflow
            result = self._workflow.invoke({
                "task_description": task_description,
                "session_id": self.session_id,
                "iteration_count": 0,
                "max_iterations": 3
            })

            # Format result
            formatted = format_workflow_result(result)

            # Display results
            self._display_workflow_result(formatted)

            # Save to memory
            self._memory.save_task_result(
                task_description=task_description,
                result=formatted,
                success=not formatted.get("error")
            )

            # Update task state
            self._memory.set_current_task(task_id, {
                "description": task_description,
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "success": not formatted.get("error")
            })

        except Exception as e:
            self._formatter.print_error(f"Workflow执行失败: {str(e)}")

            self._memory.set_current_task(task_id, {
                "description": task_description,
                "status": "failed",
                "failed_at": datetime.now().isoformat(),
                "error": str(e)
            })

    def _display_workflow_result(self, result: Dict[str, Any]):
        """Display workflow result"""
        self._formatter.print_info("\n" + "="*50)
        self._formatter.print_success("工作流执行完成")

        # Task plan
        if result.get("task_plan"):
            self._formatter.print_task_plan(result["task_plan"])

        # Generated code
        if result.get("generated_code"):
            self._formatter.print_info("\n生成的代码:")
            self._formatter.print_code(result["generated_code"])

        # Review result
        if result.get("review_result"):
            self._formatter.print_review_result(result["review_result"])

        # Test result
        if result.get("test_result"):
            self._formatter.print_test_result(result["test_result"])

        # Final code
        final_code = result.get("final_code")
        if final_code and final_code != result.get("generated_code"):
            self._formatter.print_info("\n最终代码:")
            self._formatter.print_code(final_code)

        # Error
        if result.get("error"):
            self._formatter.print_error(f"\n错误: {result['error']}")

        self._formatter.print_info(f"\n迭代次数: {result.get('iterations', 0)}")

    def _rebuild_rag_index(self):
        """Rebuild RAG index"""
        if not self._rag:
            self._formatter.print_error("RAG未初始化")
            return

        self._formatter.print_info("重建RAG索引...")
        result = self._rag.build_index(show_progress=True)
        self._formatter.print_success(f"索引构建完成: {result['total_chunks']} chunks")

    def _load_session(self, data: Dict[str, Any]):
        """Load saved session"""
        try:
            from src.memory.short_term_memory import ShortTermMemory
            stm = ShortTermMemory.from_dict(data)
            self._memory._short_term = stm
            self.session_id = stm.session_id
            self._context["memory"] = self._memory
            self._formatter.print_success(f"会话已加载: {stm.session_id}")
        except Exception as e:
            self._formatter.print_error(f"加载会话失败: {str(e)}")


def main():
    """Main entry point for CLI"""
    import argparse

    parser = argparse.ArgumentParser(description="LangGraph Multi-Agent CLI")
    parser.add_argument("--session", help="Session ID", default=None)
    parser.add_argument("--user", help="User ID", default="default")
    parser.add_argument("--project", help="Project ID", default="default")
    parser.add_argument("--no-rich", help="Disable rich output", action="store_true")
    parser.add_argument("--local-embedding", help="Use local embedding", action="store_true", default=True)

    args = parser.parse_args()

    app = CLIApp(
        session_id=args.session,
        user_id=args.user,
        project_id=args.project,
        use_rich=not args.no_rich,
        use_local_embedding=args.local_embedding
    )

    app.run()


if __name__ == "__main__":
    main()