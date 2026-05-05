"""Repository analysis agent"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import ast
from src.llm.llm_model_client import get_agent_llm_client
from src.skills.skill_registry import skill_registry


class TaskType:
    """Task types"""
    MODIFY_EXISTING = "modify_existing"  # Modify existing code
    CREATE_NEW = "create_new"  # Create new project/files
    MIXED = "mixed"  # Both modify and create


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

    def classify_task(self, task_description: str) -> Dict[str, Any]:
        """
        Classify the task type based on the description.

        Args:
            task_description: The task description

        Returns:
            Dict containing task classification
        """
        prompt = f"""你是一个专业的任务分类器。请分析以下任务描述，判断任务类型。

任务描述：{task_description}

请判断这是哪种类型的任务：
1. modify_existing - 修改已有的代码/文件
2. create_new - 创建新的项目或全新文件
3. mixed - 既需要修改已有代码，也需要创建新文件

关键指标：
- 如果是"修改"、"修复"、"优化"、"添加功能到已有文件" -> modify_existing
- 如果是"创建新项目"、"从头开始"、"新建一个" -> create_new
- 如果两者都有 -> mixed

请按以下 JSON 格式输出（只输出 JSON）：
{{
    "task_type": "modify_existing|create_new|mixed",
    "confidence": 0.0-1.0,
    "reasoning": "判断理由",
    "existing_files_mentioned": ["可能涉及的文件"],
    "new_files_needed": ["可能需要创建的新文件"],
    "suggested_project_type": "如果是新项目，建议的项目类型（python_package/fastapi_project 等）"
}}
"""
        try:
            response = self.client.invoke(prompt)

            if hasattr(response, 'content'):
                content = response.content
            elif hasattr(response, 'text'):
                content = response.text
            else:
                content = str(response)

            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"Task classification error: {e}")

        # Default to modify_existing
        return {
            "task_type": TaskType.MODIFY_EXISTING,
            "confidence": 0.5,
            "reasoning": "Default classification due to parsing error",
            "existing_files_mentioned": [],
            "new_files_needed": [],
            "suggested_project_type": "python_package"
        }

    def analyze(self, task_description: str) -> Dict[str, Any]:
        """
        Analyze the codebase to understand context and identify relevant files.
        Routes to different analysis methods based on task type.

        Args:
            task_description: The coding task description

        Returns:
            Dict containing repository analysis results
        """
        # First, classify the task type
        task_classification = self.classify_task(task_description)
        task_type = task_classification.get("task_type", TaskType.MODIFY_EXISTING)

        # Route to appropriate analysis method
        if task_type == TaskType.CREATE_NEW:
            return self._analyze_new_project_task(task_description, task_classification)
        elif task_type == TaskType.MODIFY_EXISTING:
            return self._analyze_modification_task(task_description, task_classification)
        else:  # mixed
            return self._analyze_mixed_task(task_description, task_classification)

    def _analyze_new_project_task(
        self,
        task_description: str,
        task_classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a task that requires creating a new project.

        Args:
            task_description: The task description
            task_classification: The task classification result

        Returns:
            Dict containing new project analysis
        """
        project_type = task_classification.get("suggested_project_type", "python_package")

        # Use LLM to generate detailed project plan
        prompt = f"""你是一个资深的项目架构师。用户需要创建一个新项目，请根据任务描述生成详细的项目规划。

任务描述：{task_description}
建议的项目类型：{project_type}

请按以下 JSON 格式输出（只输出 JSON）：
{{
    "project_name": "建议的项目名称",
    "project_type": "python_package|fastapi_project|flask_project|cli_tool|data_science|langgraph_agent",
    "description": "项目描述",
    "directory_structure": {{
        "project_name/": "主目录",
        "project_name/__init__.py": "包初始化",
        "project_name/main.py": "入口文件",
        "tests/": "测试目录"
    }},
    "core_files": [
        {{
            "path": "文件路径",
            "purpose": "文件用途",
            "key_components": ["主要组件 1", "主要组件 2"]
        }}
    ],
    "dependencies": ["依赖 1", "依赖 2"],
    "setup_steps": ["步骤 1", "步骤 2"],
    "test_strategy": "测试策略",
    "estimated_complexity": "low/medium/high",
    "estimated_hours": 数字
}}
"""
        try:
            response = self.client.invoke(prompt)

            if hasattr(response, 'content'):
                content = response.content
            elif hasattr(response, 'text'):
                content = response.text
            else:
                content = str(response)

            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                project_plan = json.loads(json_match.group())

                # Use scaffold skill to create the project
                scaffold_result = self._create_project_scaffold(
                    project_plan.get("project_name", "new_project"),
                    project_plan.get("project_type", "python_package"),
                    task_description
                )

                project_plan["scaffold_result"] = scaffold_result
                project_plan["task_type"] = TaskType.CREATE_NEW
                return project_plan
        except Exception as e:
            print(f"New project analysis error: {e}")

        # Default response
        return {
            "task_type": TaskType.CREATE_NEW,
            "project_name": "new_project",
            "project_type": project_type,
            "description": task_description,
            "core_files": [],
            "dependencies": [],
            "setup_steps": ["Create project directory", "Add source files", "Add tests"],
            "estimated_complexity": "medium",
            "estimated_hours": 4
        }

    def _analyze_modification_task(
        self,
        task_description: str,
        task_classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a task that requires modifying existing code.

        Args:
            task_description: The task description
            task_classification: The task classification result

        Returns:
            Dict containing modification analysis
        """
        # Analyze current project structure
        project_structure = self._analyze_project_structure()
        language_info = self._identify_language()
        dependencies = self._analyze_dependencies()
        test_info = self._find_test_information()

        # Use file search skill to find relevant files
        relevant_files = []
        try:
            search_result = self.use_skill("file_search", task_description, ".", "python")
            if search_result.get("success"):
                relevant_files = [r["path"] for r in search_result.get("results", [])[:10]]
        except Exception as e:
            print(f"File search error: {e}")

        # Use LLM to generate modification plan
        prompt = f"""你是一个资深的代码分析师。基于以下项目信息和任务，请分析需要修改的文件和修改方案。

项目信息：
- 项目结构：{json.dumps(project_structure, ensure_ascii=False, indent=2)}
- 编程语言：{language_info['language']} ({language_info['framework'] or '无框架'})
- 主要依赖：{dependencies}
- 测试信息：{test_info}
- 相关文件：{relevant_files}

任务描述：{task_description}

请按以下 JSON 格式输出分析结果（只输出 JSON）：
{{
    "task_type": "modify_existing",
    "main_files_to_modify": ["需要修改的主要文件路径"],
    "related_files": ["相关文件路径"],
    "modification_plan": [
        {{
            "file": "文件路径",
            "changes": ["变更 1", "变更 2"],
            "risk_level": "low/medium/high"
        }}
    ],
    "dependencies_to_update": ["需要更新的依赖"],
    "test_files_to_update": ["需要更新的测试文件"],
    "key_patterns": {{
        "imports": ["需要导入的模块"],
        "classes_to_modify": ["需要修改的类"],
        "functions_to_modify": ["需要修改的函数"]
    }},
    "risk_points": ["风险点 1", "风险点 2"],
    "suggestions": ["建议 1", "建议 2"],
    "complexity_assessment": "low/medium/high",
    "estimated_hours": 数字
}}

分析要点：
1. 找出需要修改的核心文件
2. 评估修改的影响范围
3. 识别潜在风险点
4. 评估任务复杂度"""

        try:
            response = self.client.invoke(prompt)

            if hasattr(response, 'content'):
                return self._parse_analysis_response(response.content, project_structure)
            elif hasattr(response, 'text'):
                return self._parse_analysis_response(response.text, project_structure)
            elif isinstance(response, str):
                return self._parse_analysis_response(response, project_structure)
            else:
                return self._create_default_analysis(project_structure, TaskType.MODIFY_EXISTING)

        except Exception as e:
            print(f"Modification analysis error: {e}")
            return self._create_default_analysis(project_structure, TaskType.MODIFY_EXISTING)

    def _analyze_mixed_task(
        self,
        task_description: str,
        task_classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a task that requires both modification and creation.

        Args:
            task_description: The task description
            task_classification: The task classification result

        Returns:
            Dict containing mixed task analysis
        """
        # Combine both analyses
        modification_analysis = self._analyze_modification_task(
            task_description,
            task_classification
        )

        # Add creation-specific information
        new_files = task_classification.get("new_files_needed", [])

        modification_analysis["task_type"] = TaskType.MIXED
        modification_analysis["new_files_to_create"] = new_files
        modification_analysis["creation_plan"] = [
            {
                "file": f,
                "purpose": "New file for extended functionality",
                "template": "standard"
            }
            for f in new_files
        ]

        return modification_analysis

    def _create_project_scaffold(
        self,
        project_name: str,
        project_type: str,
        task_description: str
    ) -> Dict[str, Any]:
        """
        Create project scaffold using the scaffold skill.

        Args:
            project_name: Name of the project
            project_type: Type of project
            task_description: Task description for custom config

        Returns:
            Result from scaffold execution
        """
        try:
            scaffold_skill = skill_registry.get_skill("project_scaffold")
            if scaffold_skill:
                return scaffold_skill.execute(
                    project_name=project_name,
                    project_type=project_type,
                    base_directory=".",
                    custom_config={"description": task_description}
                )
        except Exception as e:
            print(f"Scaffold creation error: {e}")
            return {"success": False, "error": str(e)}

        return {"success": False, "error": "Scaffold skill not found"}

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
                    continue
                elif item.name in ['requirements.txt', 'package.json', 'pom.xml', 'setup.py']:
                    structure["config_files"].append(str(item))
                elif item.suffix in ['.md', '.txt', '.rst', '.doc']:
                    structure["documentation"].append(str(item))

        return structure

    def _identify_language(self) -> Dict[str, str]:
        """Identify programming language and framework"""
        if (self.project_root / "requirements.txt").exists() or \
           (self.project_root / "setup.py").exists() or \
           (self.project_root / "pyproject.toml").exists():
            return {"language": "Python", "framework": self._detect_python_framework()}

        if (self.project_root / "package.json").exists():
            return {"language": "JavaScript/TypeScript", "framework": self._detect_js_framework()}

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

        if os.path.exists("src"):
            for root, dirs, files in os.walk("src"):
                for file in files:
                    if file.endswith(".py"):
                        relevant_files.append(os.path.join(root, file))

        for file in os.listdir("."):
            if file.endswith(".py") and not file.startswith("__"):
                relevant_files.append(file)

        return relevant_files[:10]

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

        test_dirs = ["test", "tests", "spec"]
        for test_dir in test_dirs:
            if os.path.exists(test_dir):
                for root, dirs, files in os.walk(test_dir):
                    for file in files:
                        if file.endswith((".py", "_test.py", "test_*.py")):
                            test_info["test_files"].append(os.path.join(root, file))

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

        relevant_files = self._find_relevant_files("", {})
        for file_path in relevant_files[:5]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                imports = re.findall(r'from\s+([^\s]+)\s+import|import\s+([^\s]+)', content)
                for imp in imports:
                    if imp[0]:
                        patterns["imports"].append(imp[0])
                    elif imp[1]:
                        patterns["imports"].append(imp[1])

                classes = re.findall(r'class\s+(\w+)', content)
                patterns["class_patterns"].extend(classes)

                functions = re.findall(r'def\s+(\w+)', content)
                patterns["function_patterns"].extend(functions)

            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue

        for key in patterns:
            patterns[key] = list(set(patterns[key]))

        return patterns

    def _parse_analysis_response(self, response: str, project_structure: Dict) -> Dict[str, Any]:
        """Parse LLM response into structured analysis"""
        import json
        import re

        response = response.strip()

        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                analysis = json.loads(json_match.group())
                return self._ensure_required_fields(analysis)
            except json.JSONDecodeError:
                pass

        return self._create_default_analysis(project_structure, TaskType.MODIFY_EXISTING)

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
                for sub_field in required_fields[field]:
                    if sub_field not in analysis[field]:
                        analysis[field][sub_field] = required_fields[field][sub_field]

        return analysis

    def _create_default_analysis(
        self,
        project_structure: Dict,
        task_type: str = TaskType.MODIFY_EXISTING
    ) -> Dict[str, Any]:
        """Create default analysis if parsing fails"""
        return {
            "task_type": task_type,
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
