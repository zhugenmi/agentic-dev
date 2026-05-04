"""Tester agent for test generation and execution"""

import subprocess
import tempfile
import os
from typing import Dict, Any, Optional
from src.llm.llm_model_client import get_agent_llm_client


class Tester:
    """Agent responsible for generating tests and running them"""

    def __init__(self):
        self.client = get_agent_llm_client("tester")
        self.model = "bigmodel"

    def generate_tests(self, code: str, task_description: str) -> Dict[str, Any]:
        """
        Generate test cases for the given code.

        Args:
            code: The code to generate tests for
            task_description: Original task description

        Returns:
            Dict containing generated tests
        """
        prompt = f"""你是一个专业的测试工程师。请为以下Python代码生成全面的单元测试。

原始需求：{task_description}

代码：
```python
{code}
```

请生成以下格式的测试代码（只输出测试代码，不要其他内容）：
```python
import unittest
import pytest

class Test{self._extract_class_name(code)}(unittest.TestCase):
    def setUp(self):
        # Setup code
        pass

    def test_{self._get_function_name(code)}_happy_path(self):
        # Test happy path
        pass

    def test_{self._get_function_name(code)}_edge_cases(self):
        # Test edge cases
        pass

if __name__ == '__main__':
    unittest.main()
```

要求：
1. 测试覆盖率至少80%
2. 包含正常情况和边界情况
3. 使用unittest或pytest框架
4. 测试代码必须可直接运行"""

        try:
            response = self.client.invoke(prompt)

            if hasattr(response, 'content'):
                test_code = response.content
            elif hasattr(response, 'text'):
                test_code = response.text
            elif isinstance(response, str):
                test_code = response
            else:
                test_code = str(response)

            import re
            test_match = re.search(r'```python\s*(.*?)\s*```', test_code, re.DOTALL)
            if test_match:
                test_code = test_match.group(1).strip()

            return {
                "success": True,
                "test_code": test_code,
                "test_framework": "unittest",
                "coverage": self._estimate_coverage(code, test_code)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "test_code": "",
                "test_framework": "unittest"
            }

    def run_tests(self, code: str, test_code: str = None) -> Dict[str, Any]:
        """
        Run tests on the given code.

        Args:
            code: The code to test
            test_code: Optional test code to run

        Returns:
            Dict containing test results
        """
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write the main code
                main_file = os.path.join(temp_dir, "main.py")
                with open(main_file, 'w', encoding='utf-8') as f:
                    f.write(code)

                # If no test code provided, generate it
                if not test_code:
                    test_result = self.generate_tests(code, "Test code")
                    if not test_result["success"]:
                        return test_result
                    test_code = test_result["test_code"]

                # Write test code
                test_file = os.path.join(temp_dir, "test_main.py")
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(test_code)

                # Run tests
                os.chdir(temp_dir)
                result = subprocess.run(
                    ["python", "-m", "pytest", "test_main.py", "-v"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                # Parse results
                output = result.stdout + result.stderr
                passed = len([line for line in output.split('\n') if ' PASSED' in line])
                failed = len([line for line in output.split('\n') if ' FAILED' in line])
                error = result.returncode != 0

                return {
                    "success": not error,
                    "passed": passed,
                    "failed": failed,
                    "total": passed + failed,
                    "output": output,
                    "error": output if error else None,
                    "duration": 0  # TODO: capture actual duration
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test execution timed out",
                "output": "",
                "passed": 0,
                "failed": 0,
                "total": 0
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "passed": 0,
                "failed": 0,
                "total": 0
            }

    def _extract_class_name(self, code: str) -> str:
        """Extract main class name from code"""
        import re
        match = re.search(r'class\s+(\w+)', code)
        return match.group(1) if match else "Code"

    def _get_function_name(self, code: str) -> str:
        """Extract main function name from code"""
        import re
        matches = re.findall(r'def\s+(\w+)', code)
        return matches[0] if matches else "main"

    def _estimate_coverage(self, code: str, test_code: str) -> float:
        """Estimate test coverage (simplified)"""
        # Simple heuristic based on number of lines
        code_lines = len([line for line in code.split('\n') if line.strip() and not line.strip().startswith('#')])
        test_lines = len([line for line in test_code.split('\n') if line.strip() and not line.strip().startswith('#')])

        if code_lines == 0:
            return 0.0

        # Very rough estimate
        return min(0.8, test_lines / code_lines * 2)

    def analyze_test_results(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze test results and provide feedback.

        Args:
            test_results: Results from test execution

        Returns:
            Dict with analysis and recommendations
        """
        if not test_results.get("success"):
            return {
                "status": "failed",
                "message": "测试执行失败",
                "recommendations": [
                    "检查代码是否有语法错误",
                    "确保所有依赖已安装",
                    "查看详细的错误日志"
                ]
            }

        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)
        total = test_results.get("total", 0)

        if total == 0:
            return {
                "status": "warning",
                "message": "没有执行任何测试",
                "recommendations": ["检查测试代码是否正确"]
            }

        pass_rate = passed / total

        if pass_rate == 1.0:
            return {
                "status": "success",
                "message": "所有测试通过",
                "pass_rate": pass_rate,
                "recommendations": []
            }
        else:
            return {
                "status": "partial",
                "message": f"部分测试通过 ({passed}/{total})",
                "pass_rate": pass_rate,
                "failed_count": failed,
                "recommendations": [
                    "检查失败的测试用例",
                    "考虑添加边界测试",
                    "提高异常处理覆盖率"
                ]
            }