"""Base agent class with Tool Calling support"""

import json
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.llm.llm_model_client import get_agent_llm_client
from src.tools import (
    get_executor,
    get_registry,
)
from src.tools.tool_registry import ToolResult


class BaseAgent:
    """
    Base class for all agents with Tool Calling support.

    Replaces the old skill-based system with MCP-backed tool calling.
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.client = get_agent_llm_client(agent_name)
        self._executor = get_executor()
        self._registry = get_registry()
        self._trace_id: Optional[str] = None

    @property
    def trace_id(self) -> Optional[str]:
        return self._trace_id

    @trace_id.setter
    def trace_id(self, value: str) -> None:
        self._trace_id = value

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available tools for this agent in OpenAI format.

        Used for LLM bind_tools() / function calling.
        """
        return self._registry.get_tools_as_openai_functions(self.agent_name)

    def get_tool_descriptions(self) -> str:
        """
        Get a human-readable description of available tools for prompt context.
        """
        tools = self._registry.get_tools_for_agent(self.agent_name)
        if not tools:
            return "No tools available."

        lines = ["Available tools:"]
        for t in tools:
            lines.append(f"  - {t.name}: {t.description}")
        return "\n".join(lines)

    def check_permission(self, tool_name: str) -> bool:
        """Check if this agent is allowed to call a tool."""
        return self._executor.check_permission(self.agent_name, tool_name)

    def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """
        Call a tool with permission checking and tracing.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            ToolResult with success/failure and output
        """
        return self._executor.execute(
            agent_name=self.agent_name,
            tool_name=tool_name,
            arguments=arguments or {},
            trace_id=self._trace_id,
        )

    def invoke_with_tools(
        self,
        prompt: str,
        max_tool_turns: int = 3,
    ) -> tuple[Any, List[Dict[str, Any]]]:
        """
        Invoke LLM with tool calling capability.

        Handles the multi-turn loop:
          1. LLM returns tool calls → execute tools
          2. Send results back to LLM
          3. Repeat until no more tool calls or max turns reached

        Args:
            prompt: User/system prompt
            max_tool_turns: Maximum rounds of tool execution

        Returns:
            (final_response, tool_call_history)
        """
        messages = [HumanMessage(content=prompt)]
        tool_history: List[Dict[str, Any]] = []

        # Bind tools to the underlying ChatOpenAI client
        tools = self.get_available_tools()
        llm_with_tools = self.client._client.bind_tools(tools)

        for turn in range(max_tool_turns + 1):
            response = llm_with_tools.invoke(messages)

            if hasattr(response, "tool_calls") and response.tool_calls:
                # Execute each tool call
                for tc in response.tool_calls:
                    tool_name = tc["name"]
                    args_str = tc.get("args", {})
                    if isinstance(args_str, str):
                        try:
                            args = json.loads(args_str)
                        except json.JSONDecodeError:
                            args = {"input": args_str}
                    else:
                        args = args_str

                    result = self.call_tool(tool_name, args)
                    tool_history.append({
                        "tool": tool_name,
                        "args": args,
                        "result": result.to_content(),
                        "success": result.success,
                    })

                    # Add tool response to conversation
                    messages.append(AIMessage(tool_calls=[tc]))
                    messages.append(ToolMessage(
                        content=result.to_content(),
                        name=tool_name,
                    ))
            else:
                # No more tool calls, return final response
                return response, tool_history

        # Max turns exceeded, return last response
        return response, tool_history

    def invoke_simple(self, prompt: str) -> Any:
        """
        Simple LLM invocation without tool calling (for pure generation tasks).
        """
        return self.client.invoke(prompt)
