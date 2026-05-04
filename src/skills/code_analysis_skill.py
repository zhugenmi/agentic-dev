"""Code analysis skill for analyzing Python code"""

import ast
import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional
from .skill_registry import BaseSkill, SkillMetadata, SkillType, SkillRiskLevel


class CodeAnalysisSkill(BaseSkill):
    """Skill for analyzing Python code"""

    def __init__(self):
        metadata = SkillMetadata(
            name="code_analysis",
            description="Analyze Python code for complexity, dependencies, and patterns",
            skill_type=SkillType.RESOURCE,
            risk_level=SkillRiskLevel.LOW,
            tags=["python", "analysis", "code"],
            execution_timeout=60
        )
        super().__init__(metadata)

    def execute(self, file_path: str, analysis_type: str = "basic") -> Dict[str, Any]:
        """
        Analyze Python code file

        Args:
            file_path: Path to the Python file to analyze
            analysis_type: Type of analysis (basic, detailed, complexity)

        Returns:
            Dictionary with analysis results
        """
        import time
        start_time = time.time()

        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "analysis": {}
                }

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if analysis_type == "basic":
                analysis = self._basic_analysis(content)
            elif analysis_type == "detailed":
                analysis = self._detailed_analysis(content)
            elif analysis_type == "complexity":
                analysis = self._complexity_analysis(content)
            else:
                analysis = self._basic_analysis(content)

            duration = time.time() - start_time
            self.record_execution(True, duration, {"file": str(file_path), "type": analysis_type})

            return {
                "success": True,
                "file_path": str(file_path),
                "analysis_type": analysis_type,
                "analysis": analysis,
                "duration": duration
            }

        except Exception as e:
            duration = time.time() - start_time
            self.record_execution(False, duration, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "analysis": {}
            }

    def _basic_analysis(self, content: str) -> Dict[str, Any]:
        """Perform basic code analysis"""
        try:
            tree = ast.parse(content)
            lines = content.split('\n')

            classes = []
            functions = []
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "docstring": ast.get_docstring(node),
                        "methods": len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                    })
                elif isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "docstring": ast.get_docstring(node),
                        "args": len(node.args.args)
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(f"from {node.module} import")

            return {
                "total_lines": len(lines),
                "classes": classes,
                "functions": functions,
                "imports": imports,
                "summary": {
                    "class_count": len(classes),
                    "function_count": len(functions),
                    "import_count": len(imports)
                }
            }
        except SyntaxError:
            return {
                "error": "Invalid Python syntax",
                "total_lines": len(content.split('\n'))
            }

    def _detailed_analysis(self, content: str) -> Dict[str, Any]:
        """Perform detailed code analysis"""
        basic = self._basic_analysis(content)

        # Add more detailed metrics
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        comment_lines = [line for line in lines if line.strip().startswith('#') or line.strip().startswith('"""')]

        # Calculate cyclomatic complexity (simplified)
        complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'with', 'and', 'or']
        complexity_count = sum(sum(1 for keyword in keywords if keyword in line)
                             for line in lines
                             for keyword in complexity_keywords)

        return {
            **basic,
            "metrics": {
                "total_lines": len(lines),
                "non_empty_lines": len(non_empty_lines),
                "comment_lines": len(comment_lines),
                "blank_lines": len(lines) - len(non_empty_lines),
                "code_comments_ratio": len(comment_lines) / max(len(non_empty_lines), 1),
                "cyclomatic_complexity": complexity_count
            },
            "code_quality": {
                "has_docstrings": any(item.get("docstring") for item in basic.get("classes", []) + basic.get("functions", [])),
                "has_comments": len(comment_lines) > 0,
                "complexity_level": "low" if complexity_count < 10 else "medium" if complexity_count < 20 else "high"
            }
        }

    def _complexity_analysis(self, content: str) -> Dict[str, Any]:
        """Perform complexity-focused analysis"""
        detailed = self._detailed_analysis(content)

        # Calculate function complexity
        function_complexities = []
        for func in detailed.get("functions", []):
            func_complexity = self._calculate_function_complexity(func, content)
            function_complexities.append({
                "name": func["name"],
                "complexity": func_complexity,
                "level": "low" if func_complexity < 5 else "medium" if func_complexity < 10 else "high"
            })

        return {
            **detailed,
            "function_complexities": function_complexities,
            "overall_complexity": sum(f["complexity"] for f in function_complexities),
            "recommendations": self._generate_recommendations(detailed, function_complexities)
        }

    def _calculate_function_complexity(self, func: Dict[str, Any], content: str) -> int:
        """Calculate cyclomatic complexity for a function"""
        lines = content.split('\n')
        start_line = func["line"] - 1
        func_lines = []

        # Find function body
        indent = len(lines[start_line]) - len(lines[start_line].lstrip())
        for i in range(start_line, len(lines)):
            if i == start_line:
                func_lines.append(lines[i])
            elif len(lines[i]) - len(lines[i].lstrip()) > indent:
                func_lines.append(lines[i])
            elif lines[i].strip():
                break

        # Count complexity factors
        complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'with', 'and', 'or']
        return sum(sum(1 for keyword in keywords if keyword in line)
                  for line in func_lines
                  for keyword in keywords)

    def _generate_recommendations(self, detailed: Dict[str, Any], function_complexities: List[Dict]) -> List[str]:
        """Generate code improvement recommendations"""
        recommendations = []

        if detailed.get("metrics", {}).get("code_comments_ratio", 0) < 0.1:
            recommendations.append("Consider adding more comments to improve code readability")

        if any(f["level"] == "high" for f in function_complexities):
            recommendations.append("Some functions have high complexity - consider breaking them down")

        if not detailed.get("code_quality", {}).get("has_docstrings", False):
            recommendations.append("Add docstrings to classes and functions")

        return recommendations