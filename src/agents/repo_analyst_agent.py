"""Repository analysis agent"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import ast
from src.llm.llm_model_client import get_agent_llm_client
from src.skills.skill_registry import skill_registry


class RepoAnalystAgent:
    """Agent responsible for analyzing codebase context and locating relevant files"""

    def __init__(self):
        self.client = get_agent_llm_client("repo_analyst")
        self.model = "bigmodel"
        self.project_root = Path(__file__).parent.parent.parent
        self.skills = skill_registry.get_skills_for_agent("repo_analyst")

    def use_skill(self, skill_name: str, *args, **kwargs) -> Any:
        """Use a skill available to this agent"""
        skill = skill_registry.get_skill(skill_name)
        if skill:
            return skill.execute(*args, **kwargs)
        else:
            raise ValueError(f"Skill '{skill_name}' not available")

    def analyze(self, task_description: str) -> Dict[str, Any]:
        """
        Analyze the codebase to understand context and identify relevant files.

        Args:
            task_description: The coding task description

        Returns:
            Dict containing repository analysis results
        """
        # Use skills to enhance analysis
        try:
            # Use file search skill to find relevant files
            search_result = self.use_skill("file_search", task_description, ".", "python")
            if search_result["success"]:
                relevant_files = [r["path"] for r in search_result["results"][:10]]
            else:
                relevant_files = []
        except Exception:
            relevant_files = []
        # First analyze project structure
        project_structure = self._analyze_project_structure()

        # Identify programming language and framework
        language_info = self._identify_language()

        # Find relevant files based on task
        relevant_files = self._find_relevant_files(task_description, project_structure)

        # Analyze dependencies
        dependencies = self._analyze_dependencies()

        # Find test-related information
        test_info = self._find_test_information()

        # Extract key patterns and interfaces
        patterns = self._extract_key_patterns()

        prompt = f"""你是一个资深的代码库分析师。基于以下项目信息和任务，请进行深入分析。

项目信息：
- 项目结构：{json.dumps(project_structure, ensure_ascii=False, indent=2)}
- 编程语言：{language_info['language']} ({language_info['framework'] or '无框架'})
- 主要依赖：{dependencies}
- 测试信息：{test_info}

任务描述：{task_description}

请按以下JSON格式输出分析结果（只输出JSON，不要其他内容）：
{{
    "main_files": ["文件路径1", "文件路径2"],
    "related_files": ["相关文件路径1", "相关文件路径2"],
    "dependencies": ["依赖项1", "依赖项2"],
    "test_files": ["测试文件1", "测试文件2"],
    "key_patterns": {{
        "imports": ["import语句1", "import语句2"],
        "class_patterns": ["类名1", "类名2"],
        "function_patterns": ["函数名1", "函数名2"]
    }},
    "interface_contracts": {{
        "inputs": ["输入接口1"],
        "outputs": ["输出接口1"]
    }},
    "risk_points": ["风险点1", "风险点2"],
    "suggestions": ["建议1", "建议2"],
    "complexity_assessment": "low/medium/high",
    "estimated_hours": 数字
}}

分析要点：
1. 找出与任务最相关的核心文件
2. 识别需要关注的依赖关系
3. 分析现有测试结构
4. 提取关键代码模式
5. 识别潜在风险点
6. 评估任务复杂度"""

        try:
            response = self.client.invoke(prompt)

            if hasattr(response, 'content'):
                return self._parse_analysis_response(response.content, project_structure)
            elif hasattr(response, 'text'):
                return self._parse_analysis_response(response.text, project_structure)
            elif isinstance(response, str):
                return self._parse_analysis_response(response, project_structure)
            else:
                return self._create_default_analysis(project_structure)

        except Exception as e:
            print(f"Analysis failed: {e}")
            return self._create_default_analysis(project_structure)

    def _analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze the project structure"""
        structure = {
            "root": str(self.project_root),
            "main_dirs": [],
            "source_dirs": [],
            "test_dirs": [],
            "config_files": [],
            "documentation": []
        }

        for item in self.project_root.iterdir():
            if item.is_dir():
                if item.name in ['src', 'source', 'lib']:
                    structure["source_dirs"].append(str(item))
                elif item.name in ['test', 'tests', 'spec']:
                    structure["test_dirs"].append(str(item))
                else:
                    structure["main_dirs"].append(str(item))
            elif item.is_file():
                if item.suffix in ['.py', '.js', '.ts', '.java', '.cpp', '.h']:
                    continue  # Skip source files, we'll list them separately
                elif item.name in ['requirements.txt', 'package.json', 'pom.xml', 'setup.py']:
                    structure["config_files"].append(str(item))
                elif item.suffix in ['.md', '.txt', '.rst', '.doc']:
                    structure["documentation"].append(str(item))

        return structure

    def _identify_language(self) -> Dict[str, str]:
        """Identify programming language and framework"""
        # Check for Python
        if (self.project_root / "requirements.txt").exists() or \
           (self.project_root / "setup.py").exists() or \
           (self.project_root / "pyproject.toml").exists():
            return {"language": "Python", "framework": self._detect_python_framework()}

        # Check for JavaScript/TypeScript
        if (self.project_root / "package.json").exists():
            return {"language": "JavaScript/TypeScript", "framework": self._detect_js_framework()}

        # Check for Java
        if (self.project_root / "pom.xml").exists() or \
           (self.project_root / "build.gradle").exists():
            return {"language": "Java", "framework": self._detect_java_framework()}

        return {"language": "Unknown", "framework": "Unknown"}

    def _detect_python_framework(self) -> str:
        """Detect Python framework"""
        requirements = (self.project_root / "requirements.txt").read_text() if \
                       (self.project_root / "requirements.txt").exists() else ""

        if "django" in requirements.lower():
            return "Django"
        elif "flask" in requirements.lower():
            return "Flask"
        elif "fastapi" in requirements.lower():
            return "FastAPI"
        return "Standard Python"

    def _detect_js_framework(self) -> str:
        """Detect JavaScript framework"""
        package_json = {}
        if (self.project_root / "package.json").exists():
            try:
                import json
                package_json = json.loads((self.project_root / "package.json").read_text())
            except:
                pass

        if "react" in str(package_json.get("dependencies", {})).lower():
            return "React"
        elif "vue" in str(package_json.get("dependencies", {})).lower():
            return "Vue"
        elif "angular" in str(package_json.get("dependencies", {})).lower():
            return "Angular"
        return "Vanilla JS"

    def _detect_java_framework(self) -> str:
        """Detect Java framework"""
        pom_xml = ""
        if (self.project_root / "pom.xml").exists():
            pom_xml = (self.project_root / "pom.xml").read_text()

        if "spring-boot" in pom_xml.lower():
            return "Spring Boot"
        elif "spring" in pom_xml.lower():
            return "Spring"
        return "Java SE"

    def _find_relevant_files(self, task_description: str, project_structure: Dict) -> List[str]:
        """Find files relevant to the task"""
        relevant_files = []

        # Search for Python files in src directory
        if os.path.exists("src"):
            for root, dirs, files in os.walk("src"):
                for file in files:
                    if file.endswith(".py"):
                        relevant_files.append(os.path.join(root, file))

        # Also check root directory
        for file in os.listdir("."):
            if file.endswith(".py") and not file.startswith("__"):
                relevant_files.append(file)

        return relevant_files[:10]  # Limit to first 10 files

    def _analyze_dependencies(self) -> List[str]:
        """Analyze project dependencies"""
        dependencies = []

        if os.path.exists("requirements.txt"):
            with open("requirements.txt", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        dependencies.append(line)

        return dependencies

    def _find_test_information(self) -> Dict[str, Any]:
        """Find test-related information"""
        test_info = {
            "test_framework": "unknown",
            "test_files": [],
            "test_commands": []
        }

        # Find test directories
        test_dirs = ["test", "tests", "spec"]
        for test_dir in test_dirs:
            if os.path.exists(test_dir):
                for root, dirs, files in os.walk(test_dir):
                    for file in files:
                        if file.endswith((".py", "_test.py", "test_*.py")):
                            test_info["test_files"].append(os.path.join(root, file))

        # Check common testing frameworks
        if any("pytest" in dep for dep in self._analyze_dependencies()):
            test_info["test_framework"] = "pytest"
            test_info["test_commands"].append("pytest")
        elif any("unittest" in dep for dep in self._analyze_dependencies()):
            test_info["test_framework"] = "unittest"
            test_info["test_commands"].append("python -m unittest")

        return test_info

    def _extract_key_patterns(self) -> Dict[str, List[str]]:
        """Extract key patterns from the codebase"""
        patterns = {
            "imports": [],
            "class_patterns": [],
            "function_patterns": []
        }

        # Sample a few files to extract patterns
        relevant_files = self._find_relevant_files("", {})
        for file_path in relevant_files[:5]:  # Limit to first 5 files
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract imports
                imports = re.findall(r'from\s+([^\s]+)\s+import|import\s+([^\s]+)', content)
                for imp in imports:
                    if imp[0]:
                        patterns["imports"].append(imp[0])
                    elif imp[1]:
                        patterns["imports"].append(imp[1])

                # Extract class names
                classes = re.findall(r'class\s+(\w+)', content)
                patterns["class_patterns"].extend(classes)

                # Extract function names
                functions = re.findall(r'def\s+(\w+)', content)
                patterns["function_patterns"].extend(functions)

            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue

        # Remove duplicates
        for key in patterns:
            patterns[key] = list(set(patterns[key]))

        return patterns

    def _parse_analysis_response(self, response: str, project_structure: Dict) -> Dict[str, Any]:
        """Parse LLM response into structured analysis"""
        import json
        import re

        response = response.strip()

        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                analysis = json.loads(json_match.group())
                # Ensure all required fields exist
                return self._ensure_required_fields(analysis)
            except json.JSONDecodeError:
                pass

        return self._create_default_analysis(project_structure)

    def _ensure_required_fields(self, analysis: Dict) -> Dict[str, Any]:
        """Ensure all required fields exist in analysis"""
        required_fields = {
            "main_files": [],
            "related_files": [],
            "dependencies": [],
            "test_files": [],
            "key_patterns": {"imports": [], "class_patterns": [], "function_patterns": []},
            "interface_contracts": {"inputs": [], "outputs": []},
            "risk_points": [],
            "suggestions": [],
            "complexity_assessment": "medium",
            "estimated_hours": 2
        }

        for field in required_fields:
            if field not in analysis:
                analysis[field] = required_fields[field]
            elif isinstance(required_fields[field], dict) and isinstance(analysis[field], dict):
                # Handle nested dictionaries
                for sub_field in required_fields[field]:
                    if sub_field not in analysis[field]:
                        analysis[field][sub_field] = required_fields[field][sub_field]

        return analysis

    def _create_default_analysis(self, project_structure: Dict) -> Dict[str, Any]:
        """Create default analysis if parsing fails"""
        return {
            "main_files": [],
            "related_files": [],
            "dependencies": [],
            "test_files": [],
            "key_patterns": {"imports": [], "class_patterns": [], "function_patterns": []},
            "interface_contracts": {"inputs": [], "outputs": []},
            "risk_points": [],
            "suggestions": [],
            "complexity_assessment": "medium",
            "estimated_hours": 2
        }