"""Repository Search MCP Server - built on FastMCP for code analysis"""

import os
import re
import json
import sys
import ast
from typing import Any, Dict, List, Optional
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

REPO_PATH = Path(__file__).parent.parent.parent.absolute()


if MCP_AVAILABLE:
    mcp = FastMCP(
        "repo_search",
        instructions="Repository search and code analysis MCP server"
    )
else:
    mcp = None


def _safe_walk(repo: Path):
    """Walk directory tree, skipping common noise dirs."""
    skip = {".git", "__pycache__", "node_modules", "venv", ".venv", ".env",
            "build", "dist", ".cache", "rag_index", "memory_store", "logs"}
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in skip]
        yield root, dirs, files


def _python_ext(s: str) -> bool:
    return s.endswith(".py")


def _js_ext(s: str) -> bool:
    return s.endswith((".js", ".ts", ".jsx", ".tsx"))


# ── Tool: search_code_snippet ──────────────────────────────────────

def search_code_snippet(query: str, language: str = "python", max_results: int = 10) -> Dict[str, Any]:
    """搜索代码片段，支持按关键词和语言过滤

    Args:
        query: 搜索关键词
        language: 过滤语言 (python / javascript / all)
        max_results: 最大返回条数
    """
    try:
        results = []
        q_lower = query.lower()

        for root, _, files in _safe_walk(REPO_PATH):
            for fname in files:
                # Language filter
                if language == "python" and not _python_ext(fname):
                    continue
                if language == "javascript" and not _js_ext(fname):
                    continue

                fpath = Path(root) / fname
                try:
                    content = fpath.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    if q_lower in line.lower():
                        start = max(0, i - 4)
                        end = min(len(lines), i + 4)
                        context = "\n".join(lines[start:end])
                        results.append({
                            "file": str(fpath.relative_to(REPO_PATH)),
                            "line": i,
                            "match": line.strip(),
                            "context": context,
                        })
                        if len(results) >= max_results:
                            return {"success": True, "results": results, "total": len(results)}

        return {"success": True, "results": results, "total": len(results)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Tool: read_symbol_context ──────────────────────────────────────

def read_symbol_context(symbol: str, file_path: str = "", context_lines: int = 10) -> Dict[str, Any]:
    """读取符号（函数/类）定义及其周围上下文

    Args:
        symbol: 符号名称
        file_path: 可选，限定在某个文件中搜索
        context_lines: 前后上下文行数
    """
    try:
        found = []

        if file_path:
            targets = [REPO_PATH / file_path]
            if not targets[0].exists():
                return {"success": False, "error": f"File not found: {file_path}"}
        else:
            targets = []
            for p in REPO_PATH.rglob("*.py"):
                if _python_ext(str(p)):
                    targets.append(p)
            for p in REPO_PATH.rglob("*.{js,ts,jsx,tsx}"):
                targets.append(p)

        for fpath in targets:
            if len(found) >= 10:
                break
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            if _python_ext(str(fpath)):
                found.extend(_find_python_symbols(fpath, content, symbol, context_lines))
            elif _js_ext(str(fpath)):
                found.extend(_find_js_symbols(fpath, content, symbol, context_lines))

        return {"success": True, "symbols": found, "total": len(found)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _find_python_symbols(fpath: Path, content: str, symbol: str, ctx: int) -> List[Dict]:
    results = []
    try:
        tree = ast.parse(content)
        lines = content.split("\n")
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and symbol.lower() in node.name.lower():
                start = max(0, node.lineno - 1 - ctx)
                end = min(len(lines), node.lineno + ctx)
                results.append({
                    "file": str(fpath.relative_to(REPO_PATH)),
                    "symbol": node.name,
                    "type": "class" if isinstance(node, ast.ClassDef) else "function",
                    "line": node.lineno,
                    "docstring": ast.get_docstring(node),
                    "context": "\n".join(lines[start:end]),
                })
    except SyntaxError:
        pass
    return results


def _find_js_symbols(fpath: Path, content: str, symbol: str, ctx: int) -> List[Dict]:
    results = []
    lines = content.split("\n")
    patterns = [
        (r"(?:function|const|let|var)\s+(\w+)[\s(]", "function"),
        (r"class\s+(\w+)", "class"),
    ]
    for pattern, stype in patterns:
        for i, line in enumerate(lines, 1):
            m = re.search(pattern, line)
            if m and symbol.lower() in m.group(1).lower():
                start = max(0, i - 1 - ctx)
                end = min(len(lines), i + ctx)
                results.append({
                    "file": str(fpath.relative_to(REPO_PATH)),
                    "symbol": m.group(1),
                    "type": stype,
                    "line": i,
                    "context": "\n".join(lines[start:end]),
                })
    return results


# ── Tool: collect_project_metadata ─────────────────────────────────

def collect_project_metadata() -> Dict[str, Any]:
    """收集项目元数据（语言、框架、目录结构、依赖）"""
    try:
        language = _detect_language()
        framework = _detect_framework()
        total_files = 0
        total_size = 0
        dirs_list: List[str] = []
        key_files: List[str] = []

        for root, dirs, files in _safe_walk(REPO_PATH):
            rel_root = Path(root).relative_to(REPO_PATH)
            if rel_root != Path("."):
                dirs_list.append(str(rel_root))
            total_files += len(files)
            for f in files:
                try:
                    total_size += (Path(root) / f).stat().st_size
                except OSError:
                    pass
                if f in ("requirements.txt", "package.json", "pyproject.toml",
                         "setup.py", "pom.xml", "Cargo.toml", "go.mod"):
                    key_files.append(str((Path(root) / f).relative_to(REPO_PATH)))

        dependencies = _get_dependencies(language)

        return {
            "success": True,
            "language": language,
            "framework": framework,
            "directories": dirs_list,
            "key_files": key_files,
            "total_files": total_files,
            "estimated_size_mb": round(total_size / 1024 / 1024, 2),
            "dependencies": dependencies,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _detect_language() -> str:
    for marker, lang in [
        (("requirements.txt", "setup.py", "pyproject.toml"), "Python"),
        (("package.json",), "JavaScript/TypeScript"),
        (("pom.xml", "build.gradle"), "Java"),
        (("Cargo.toml",), "Rust"),
        (("go.mod",), "Go"),
    ]:
        if any((REPO_PATH / m).exists() for m in marker):
            return lang
    return "Unknown"


def _detect_framework() -> str:
    lang = _detect_language()
    if lang == "Python":
        req = (REPO_PATH / "requirements.txt").read_text() if (REPO_PATH / "requirements.txt").exists() else ""
        req_lower = req.lower()
        if "django" in req_lower:
            return "Django"
        if "flask" in req_lower:
            return "Flask"
        if "fastapi" in req_lower:
            return "FastAPI"
        if "langgraph" in req_lower:
            return "LangGraph"
    elif lang == "JavaScript/TypeScript":
        pkg = {}
        p = REPO_PATH / "package.json"
        if p.exists():
            try:
                pkg = json.loads(p.read_text())
            except Exception:
                pass
        deps = str(pkg.get("dependencies", {})).lower()
        if "react" in deps:
            return "React"
        if "vue" in deps:
            return "Vue"
    return "Unknown"


def _get_dependencies(lang: str) -> List[str]:
    if lang == "Python" and (REPO_PATH / "requirements.txt").exists():
        return [l.strip() for l in (REPO_PATH / "requirements.txt").read_text().splitlines()
                if l.strip() and not l.startswith("#")]
    if lang == "JavaScript/TypeScript" and (REPO_PATH / "package.json").exists():
        try:
            pkg = json.loads((REPO_PATH / "package.json").read_text())
            return list(pkg.get("dependencies", {}).keys())
        except Exception:
            pass
    return []


# ── Tool: find_files (legacy compatibility) ────────────────────────

def find_files(pattern: str, file_type: str = "all") -> Dict[str, Any]:
    """Find files matching a pattern"""
    try:
        matches = []
        for root, _, files in _safe_walk(REPO_PATH):
            for f in files:
                if file_type == "python" and not _python_ext(f):
                    continue
                if file_type == "javascript" and not _js_ext(f):
                    continue
                if pattern.lower() in f.lower():
                    matches.append(str((Path(root) / f).relative_to(REPO_PATH)))
                    if len(matches) >= 50:
                        return {"success": True, "files": matches, "total": len(matches)}
        return {"success": True, "files": matches, "total": len(matches)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Tool: search_symbols (legacy compatibility) ────────────────────

def search_symbols(symbol: str, symbol_type: str = "all") -> Dict[str, Any]:
    """Search for symbols (classes, functions) across the codebase"""
    return read_symbol_context(symbol, file_path="", context_lines=2)


# ── Tool: analyze_project_structure (legacy compatibility) ─────────

def analyze_project_structure() -> Dict[str, Any]:
    """Analyze overall project structure"""
    meta = collect_project_metadata()
    return {**meta, "success": True}


# ── Tool: get_dependencies (legacy compatibility) ──────────────────

def get_dependencies() -> Dict[str, Any]:
    """Get project dependencies"""
    lang = _detect_language()
    deps = _get_dependencies(lang)
    return {"success": True, "language": lang, "dependencies": deps}


# ── Register tools with FastMCP if available ────────────────────────

if MCP_AVAILABLE and mcp:
    mcp.add_tool(search_code_snippet)
    mcp.add_tool(read_symbol_context)
    mcp.add_tool(collect_project_metadata)
    mcp.add_tool(find_files)
    mcp.add_tool(search_symbols)
    mcp.add_tool(analyze_project_structure)
    mcp.add_tool(get_dependencies)


# ── Legacy: standalone class for non-MCP usage ─────────────────────

class RepoSearchServer:
    """Compatibility wrapper - delegates to the tool functions above"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).absolute()
        # Monkey-patch the global for legacy calls
        global REPO_PATH
        old = REPO_PATH
        REPO_PATH = self.repo_path

    def find_files(self, pattern: str, file_type: str = "all") -> Dict[str, Any]:
        return find_files(pattern, file_type)

    def search_symbols(self, symbol: str, symbol_type: str = "all") -> Dict[str, Any]:
        return search_symbols(symbol, symbol_type)

    def analyze_project_structure(self) -> Dict[str, Any]:
        return analyze_project_structure()

    def get_dependencies(self) -> Dict[str, Any]:
        return get_dependencies()


# ── Entry point for stdio transport ─────────────────────────────────

if __name__ == "__main__":
    if MCP_AVAILABLE and mcp:
        mcp.run(transport="stdio")
    else:
        print("Error: 'mcp' package not available. Install with: pip install mcp")
        sys.exit(1)
