"""Implementer agent for both code generation and fixing"""

from typing import Dict, Any, Optional
from src.llm.llm_model_client import get_agent_llm_client


class Implementer:
    """Agent responsible for both generating and fixing code"""

    def __init__(self):
        self.client = get_agent_llm_client("implementer")
        self.model = "bigmodel"

    def generate(self, task_description: str, task_plan: Optional[Dict[str, Any]] = None, repo_analysis: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate code based on task description and plan.

        Args:
            task_description: The coding task description
            task_plan: Optional task plan with sub-tasks
            repo_analysis: Optional repository analysis context

        Returns:
            Generated code as string
        """
        plan_info = ""
        if task_plan:
            plan_info = f"""
任务规划：
主任务：{task_plan.get('task', '未知')}

子任务分解：
"""
            for sub in task_plan.get('sub_tasks', []):
                plan_info += f"- {sub.get('description', '')}\n"

        repo_info = ""
        if repo_analysis:
            main_files = repo_analysis.get('main_files', [])[:3]  # Limit to first 3 files
            if main_files:
                repo_info = f"""
代码库分析：
主要相关文件：
- {'\\n'.join(main_files)}

关键接口：
{'\\n'.join(repo_analysis.get('key_patterns', {}).get('imports', [])[:5])}
"""

        prompt = f"""你是一个专业的Python程序员。请根据用户需求和代码库上下文生成高质量的Python代码。

{plan_info}
{repo_info}

用户需求：{task_description}

要求：
1. 代码必须是完整可运行的Python代码
2. 必须用中文写好代码注释
3. 必须用中文给函数和类写docstring说明
4. 代码要遵循PEP8规范
5. 要有适当的错误处理
6. 只需要生成代码，不需要解释

请只输出代码，用```python代码块包裹，不要输出任何其他内容："""

        try:
            response = self.client.invoke(prompt)

            if hasattr(response, 'content') and response.content:
                return response.content
            elif hasattr(response, 'text') and response.text:
                return response.text
            elif isinstance(response, str):
                return response
            elif hasattr(response, 'lc_content') and response.lc_content:
                return response.lc_content
            else:
                content = getattr(response, 'content', None)
                if content:
                    return content
                return str(response)

        except Exception as e:
            raise RuntimeError(f"代码生成失败: {str(e)}")

    def fix(self, original_code: str, review_result: Dict[str, Any]) -> str:
        """
        Fix code issues based on review feedback.

        Args:
            original_code: The original generated code
            review_result: The review result containing issues

        Returns:
            Fixed code as string
        """
        issues_text = ""
        if review_result.get("issues"):
            issues_text = "\n审查发现的问题：\n"
            for i, issue in enumerate(review_result["issues"], 1):
                issues_text += f"{i}. [{issue.get('severity', 'warning')}] {issue.get('description', '')}\n"
                if issue.get('suggestion'):
                    issues_text += f"   建议：{issue['suggestion']}\n"

        prompt = f"""你是一个专业的Python程序员。请根据审查意见修复代码中的问题。

原始代码：
```python
{original_code}
```

{issues_text}

要求：
1. 只输出修复后的完整代码
2. 必须用中文写好代码注释
3. 必须用中文给函数和类写docstring说明
4. 修复所有审查发现的问题
5. 保持代码的功能不变
6. 只需要输出代码，不需要解释

请只输出代码，用```python代码块包裹："""

        try:
            response = self.client.invoke(prompt)

            if hasattr(response, 'content'):
                code_response = response.content
            elif hasattr(response, 'text'):
                code_response = response.text
            elif isinstance(response, str):
                code_response = response
            else:
                code_response = str(response)

            import re
            code_match = re.search(r'```python\s*(.*?)\s*```', code_response, re.DOTALL)
            if code_match:
                return code_match.group(1).strip()
            return code_response.strip() if code_response.strip() else original_code

        except Exception as e:
            return original_code