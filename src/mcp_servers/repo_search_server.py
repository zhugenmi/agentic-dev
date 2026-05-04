"""Repository Search MCP Server for code analysis"""

import os
import re
import json
from typing import Any, Dict, List, Optional
from pathlib import Path
import ast


class RepoSearchServer:
    """MCP Server for repository search and analysis"""

    def __init__(self, repo_path: str = "."):
        """
        Initialize RepoSearchServer with repository path

        Args:
            repo_path: Path to the repository
        """
        self.repo_path = Path(repo_path).absolute()

    def find_files(self, pattern: str, file_type: Optional[str] = None) -> Dict[str, Any]:
        """Find files matching pattern"""
        try:
            matches = []
            for root, dirs, files in os.walk(self.repo_path):
                # Skip common directories
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', '.env']]

                for file in files:
                    file_path = Path(root) / file
                    rel_path = str(file_path.relative_to(self.repo_path))

                    # Check file type filter
                    if file_type:
                        if file_type == "python" and not file.endswith('.py'):
                            continue
                        elif file_type == "javascript" and not file.endswith(('.js', '.ts', '.jsx', '.tsx')):
                            continue
                        elif file_type == "markdown" and not file.endswith(('.md', '.mdown', '.markdown')):
                            continue

                    # Check pattern match
                    if pattern.lower() in file.lower() or pattern in rel_path:
                        matches.append(str(rel_path))

            return {
                "success": True,
                "files": matches[:50],  # Limit to 50 results
                "total": len(matches)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_symbols(self, symbol: str, symbol_type: Optional[str] = None) -> Dict[str, Any]:
        """Search for symbols (classes, functions, variables) in the codebase"""
        try:
            results = []

            # Determine file types based on symbol type
            file_types = []
            if symbol_type in ["function", "method", "class"]:
                file_types = ["python", "javascript"]
            elif symbol_type == "variable":
                file_types = ["python", "javascript"]
            else:
                file_types = ["python", "javascript"]

            for file_type in file_types:
                if file_type == "python":
                    for root, dirs, files in os.walk(self.repo_path):
                        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules']]
                        for file in files:
                            if file.endswith('.py'):
                                self._search_python_symbols(Path(root) / file, symbol, symbol_type, results)
                elif file_type == "javascript":
                    for root, dirs, files in os.walk(self.repo_path):
                        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules']]
                        for file in files:
                            if file.endswith(('.js', '.ts', '.jsx', '.tsx')):
                                self._search_js_symbols(Path(root) / file, symbol, symbol_type, results)

            return {
                "success": True,
                "symbols": results[:20],  # Limit to 20 results
                "total": len(results)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _search_python_symbols(self, file_path: Path, symbol: str, symbol_type: str, results: List[Dict]):
        """Search for symbols in Python files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Use AST for accurate symbol detection
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and (symbol_type in [None, "class"] and symbol.lower() in node.name.lower()):
                        results.append({
                            "file": str(file_path.relative_to(self.repo_path)),
                            "symbol": node.name,
                            "type": "class",
                            "line": node.lineno,
                            "docstring": ast.get_docstring(node)
                        })
                    elif isinstance(node, ast.FunctionDef) and (symbol_type in [None, "function", "method"] and symbol.lower() in node.name.lower()):
                        results.append({
                            "file": str(file_path.relative_to(self.repo_path)),
                            "symbol": node.name,
                            "type": "function",
                            "line": node.lineno,
                            "docstring": ast.get_docstring(node)
                        })
            except SyntaxError:
                # Fallback to regex if AST fails
                if symbol_type in [None, "class"]:
                    class_matches = re.findall(r'class\s+(\w+)', content)
                    for match in class_matches:
                        if symbol.lower() in match.lower():
                            line_num = content[:content.find(match)].count('\n') + 1
                            results.append({
                                "file": str(file_path.relative_to(self.repo_path)),
                                "symbol": match,
                                "type": "class",
                                "line": line_num,
                                "docstring": None
                            })

                if symbol_type in [None, "function"]:
                    func_matches = re.findall(r'def\s+(\w+)', content)
                    for match in func_matches:
                        if symbol.lower() in match.lower():
                            line_num = content[:content.find(f"def {match}")].count('\n') + 1
                            results.append({
                                "file": str(file_path.relative_to(self.repo_path)),
                                "symbol": match,
                                "type": "function",
                                "line": line_num,
                                "docstring": None
                            })
        except Exception:
            pass

    def _search_js_symbols(self, file_path: Path, symbol: str, symbol_type: str, results: List[Dict]):
        """Search for symbols in JavaScript files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if symbol_type in [None, "function"]:
                # Find function declarations
                func_matches = re.findall(r'(?:function|const|let|var)\s+(\w+)[\s\(]', content)
                for match in func_matches:
                    if symbol.lower() in match.lower():
                        line_num = content[:content.find(match)].count('\n') + 1
                        results.append({
                            "file": str(file_path.relative_to(self.repo_path)),
                            "symbol": match,
                            "type": "function",
                            "line": line_num,
                            "docstring": None
                        })

            if symbol_type in [None, "class"]:
                # Find class declarations
                class_matches = re.findall(r'class\s+(\w+)', content)
                for match in class_matches:
                    if symbol.lower() in match.lower():
                        line_num = content[:content.find(match)].count('\n') + 1
                        results.append({
                            "file": str(file_path.relative_to(self.repo_path)),
                            "symbol": match,
                            "type": "class",
                            "line": line_num,
                            "docstring": None
                        })
        except Exception:
            pass

    def analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze overall project structure"""
        try:
            structure = {
                "language": self._detect_language(),
                "framework": self._detect_framework(),
                "directories": [],
                "key_files": [],
                "total_files": 0,
                "estimated_size": 0
            }

            for root, dirs, files in os.walk(self.repo_path):
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv']]

                rel_root = Path(root).relative_to(self.repo_path)
                if rel_root != Path('.'):
                    structure["directories"].append(str(rel_root))

                structure["total_files"] += len(files)
                structure["estimated_size"] += sum(os.path.getsize(os.path.join(root, f)) for f in files)

                # Identify key files
                for file in files:
                    file_path = Path(root) / file
                    if file in ['requirements.txt', 'package.json', 'pyproject.toml', 'setup.py', 'pom.xml']:
                        structure["key_files"].append(str(file_path.relative_to(self.repo_path)))

            structure["estimated_size_mb"] = round(structure["estimated_size"] / 1024 / 1024, 2)
            return {"success": True, "structure": structure}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _detect_language(self) -> str:
        """Detect programming language"""
        if (self.repo_path / "requirements.txt").exists() or \
           (self.repo_path / "setup.py").exists() or \
           (self.repo_path / "pyproject.toml").exists():
            return "Python"
        elif (self.repo_path / "package.json").exists():
            return "JavaScript/TypeScript"
        elif (self.repo_path / "pom.xml").exists() or \
             (self.repo_path / "build.gradle").exists():
            return "Java"
        elif (self.repo_path / "Cargo.toml").exists():
            return "Rust"
        elif (self.repo_path / "go.mod").exists():
            return "Go"
        return "Unknown"

    def _detect_framework(self) -> str:
        """Detect framework"""
        if self._detect_language() == "Python":
            if (self.repo_path / "requirements.txt").exists():
                content = (self.repo_path / "requirements.txt").read_text()
                if "django" in content.lower():
                    return "Django"
                elif "flask" in content.lower():
                    return "Flask"
                elif "fastapi" in content.lower():
                    return "FastAPI"
        elif self._detect_language() == "JavaScript/TypeScript":
            if (self.repo_path / "package.json").exists():
                try:
                    import json
                    package_json = json.loads((self.repo_path / "package.json").read_text())
                    deps = str(package_json.get("dependencies", {}))
                    if "react" in deps.lower():
                        return "React"
                    elif "vue" in deps.lower():
                        return "Vue"
                    elif "angular" in deps.lower():
                        return "Angular"
                except:
                    pass
        return "Unknown"

    def get_dependencies(self) -> Dict[str, Any]:
        """Get project dependencies"""
        try:
            dependencies = {
                "language": self._detect_language(),
                "dependencies": []
            }

            if self._detect_language() == "Python":
                if (self.repo_path / "requirements.txt").exists():
                    with open(self.repo_path / "requirements.txt", 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                dependencies["dependencies"].append(line)

            elif self._detect_language() == "JavaScript/TypeScript":
                if (self.repo_path / "package.json").exists():
                    try:
                        import json
                        package_json = json.loads((self.repo_path / "package.json").read_text())
                        dependencies["dependencies"] = list(package_json.get("dependencies", {}).keys())
                    except:
                        pass

            return {"success": True, "dependencies": dependencies}
        except Exception as e:
            return {"success": False, "error": str(e)}


# MCP Tool definitions
def get_repo_search_tools():
    """Get repository search MCP tools"""
    server = RepoSearchServer()

    return [
        {
            "name": "find_files",
            "description": "Find files matching pattern",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Pattern to search for in file names"
                    },
                    "file_type": {
                        "type": "string",
                        "enum": ["python", "javascript", "markdown", "all"],
                        "description": "Optional: filter by file type"
                    }
                },
                "required": ["pattern"]
            }
        },
        {
            "name": "search_symbols",
            "description": "Search for symbols (classes, functions) in code",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Symbol name to search for"
                    },
                    "symbol_type": {
                        "type": "string",
                        "enum": ["class", "function", "variable", "all"],
                        "description": "Optional: filter by symbol type"
                    }
                },
                "required": ["symbol"]
            }
        },
        {
            "name": "analyze_project_structure",
            "description": "Analyze overall project structure",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "get_dependencies",
            "description": "Get project dependencies",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    ]


# MCP Tool handlers
async def handle_repo_search_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle repository search tool calls"""
    server = RepoSearchServer()

    if name == "find_files":
        pattern = arguments.get("pattern", "")
        file_type = arguments.get("file_type")
        result = server.find_files(pattern, file_type)
    elif name == "search_symbols":
        symbol = arguments.get("symbol", "")
        symbol_type = arguments.get("symbol_type")
        result = server.search_symbols(symbol, symbol_type)
    elif name == "analyze_project_structure":
        result = server.analyze_project_structure()
    elif name == "get_dependencies":
        result = server.get_dependencies()
    else:
        return {"success": False, "error": f"Unknown tool: {name}"}

    return result