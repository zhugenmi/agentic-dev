"""Project scaffold skill for generating new project structures"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from .skill_registry import BaseSkill, SkillMetadata, SkillType, SkillRiskLevel


class ProjectScaffoldSkill(BaseSkill):
    """Skill for generating project scaffolds"""

    def __init__(self):
        metadata = SkillMetadata(
            name="project_scaffold",
            description="Generate project scaffold/boilerplate for different project types",
            skill_type=SkillType.TOOL,
            risk_level=SkillRiskLevel.MEDIUM,
            tags=["project", "scaffold", "boilerplate", "template"],
            execution_timeout=120
        )
        super().__init__(metadata)

        # Project templates
        self.templates = {
            "python_package": self._python_package_template,
            "fastapi_project": self._fastapi_project_template,
            "flask_project": self._flask_project_template,
            "cli_tool": self._cli_tool_template,
            "data_science": self._data_science_template,
            "langgraph_agent": self._langgraph_agent_template,
        }

    def execute(
        self,
        project_name: str,
        project_type: str = "python_package",
        base_directory: str = ".",
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate project scaffold

        Args:
            project_name: Name of the project
            project_type: Type of project template to use
            base_directory: Base directory to create project in
            custom_config: Custom configuration for the template

        Returns:
            Dictionary with scaffold result
        """
        import time
        start_time = time.time()

        try:
            base_dir = Path(base_directory).resolve()
            project_dir = base_dir / project_name

            # Get template function
            template_func = self.templates.get(project_type, self._generic_template)

            # Generate project structure
            files_created = template_func(project_dir, project_name, custom_config or {})

            duration = time.time() - start_time
            self.record_execution(True, duration, {
                "project": project_name,
                "type": project_type,
                "files": len(files_created)
            })

            return {
                "success": True,
                "project_name": project_name,
                "project_type": project_type,
                "project_path": str(project_dir),
                "files_created": files_created,
                "total_files": len(files_created),
                "duration": duration
            }

        except Exception as e:
            duration = time.time() - start_time
            self.record_execution(False, duration, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "project_name": project_name
            }

    def list_templates(self) -> List[str]:
        """List available project templates"""
        return list(self.templates.keys())

    def _create_file(self, file_path: Path, content: str) -> bool:
        """Helper to create a file"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    def _python_package_template(
        self,
        project_dir: Path,
        project_name: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """Standard Python package template"""
        files_created = []

        # Core structure
        files = {
            project_dir / project_name / "__init__.py": f'"""{project_name} package"""\n\n__version__ = "0.1.0"\n',
            project_dir / project_name / "main.py": f'"""Main module for {project_name}"""\n\nfrom . import __version__\n\ndef main():\n    """Entry point"""\n    print(f"{project_name} v{__version__}")\n\nif __name__ == "__main__":\n    main()\n',
            project_dir / "tests" / "__init__.py": '"""Tests for ' + project_name + '"""',
            project_dir / "tests" / f"test_{project_name.replace('-', '_')}.py": f'"""Tests for {project_name}"""\n\nimport pytest\nfrom {project_name} import __version__\n\ndef test_version():\n    assert __version__ == "0.1.0"\n',
            project_dir / "README.md": f"# {project_name}\n\n## Description\n\n{config.get('description', 'A Python package')}\n\n## Installation\n\n```bash\npip install -e .\n```\n\n## Usage\n\n```python\nfrom {project_name} import main\nmain()\n```\n",
            project_dir / "requirements.txt": "# Dependencies\n",
            project_dir / "setup.py": f'"""Setup script for {project_name}"""\n\nfrom setuptools import setup, find_packages\n\nsetup(\n    name="{project_name}",\n    version="0.1.0",\n    packages=find_packages(),\n    python_requires=">=3.8",\n)\n',
            project_dir / ".gitignore": "__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\n*.egg-info/\ndist/\nbuild/\n.pytest_cache/\n.coverage\n",
        }

        for file_path, content in files.items():
            self._create_file(file_path, content)
            files_created.append(str(file_path.relative_to(project_dir.parent)))

        return files_created

    def _fastapi_project_template(
        self,
        project_dir: Path,
        project_name: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """FastAPI project template"""
        files_created = []

        files = {
            project_dir / "app" / "__init__.py": '"""FastAPI application"""',
            project_dir / "app" / "main.py": f'"""FastAPI main application"""\n\nfrom fastapi import FastAPI\n\napp = FastAPI(\n    title="{project_name}",\n    description="{config.get("description", "A FastAPI project")}",\n    version="0.1.0"\n)\n\n@app.get("/")\nasync def root():\n    return {{"message": "Welcome to ' + project_name + '"}}\n\n@app.get("/health")\nasync def health():\n    return {{"status": "ok"}}\n',
            project_dir / "app" / "routers" / "__init__.py": '"""API routers"""',
            project_dir / "app" / "routers" / "items.py": '"""Items router"""\n\nfrom fastapi import APIRouter\n\nrouter = APIRouter(prefix="/items", tags=["items"])\n\n@router.get("/")\nasync def list_items():\n    return []\n',
            project_dir / "app" / "models" / "__init__.py": '"""Data models"""',
            project_dir / "app" / "schemas" / "__init__.py": '"""Pydantic schemas"""',
            project_dir / "tests" / "__init__.py": '"""Tests"""',
            project_dir / "tests" / "test_main.py": '"""Test main endpoints"""\n\nfrom fastapi.testclient import TestClient\nfrom app.main import app\n\nclient = TestClient(app)\n\ndef test_root():\n    response = client.get("/")\n    assert response.status_code == 200\n\ndef test_health():\n    response = client.get("/health")\n    assert response.json() == {"status": "ok"}\n',
            project_dir / "requirements.txt": "fastapi==0.109.0\nuvicorn[standard]==0.27.0\npydantic==2.5.0\npytest==7.4.0\nhttpx==0.26.0\n",
            project_dir / "README.md": f"# {project_name}\n\nA FastAPI project\n\n## Quick Start\n\n```bash\npip install -r requirements.txt\nuvicorn app.main:app --reload\n```\n\n## API Docs\n\n- Swagger UI: http://localhost:8000/docs\n- ReDoc: http://localhost:8000/redoc\n",
            project_dir / ".gitignore": "__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\n*.egg-info/\ndist/\nbuild/\n.pytest_cache/\n.coverage\n",
        }

        for file_path, content in files.items():
            self._create_file(file_path, content)
            files_created.append(str(file_path.relative_to(project_dir.parent)))

        return files_created

    def _flask_project_template(
        self,
        project_dir: Path,
        project_name: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """Flask project template"""
        files_created = []

        files = {
            project_dir / "app" / "__init__.py": f'"""Flask application"""',
            project_dir / "app" / "__init__.py": f'"""Flask application factory"""',
            project_dir / "app" / "routes.py": f'"""Application routes"""',
            project_dir / "app" / "routes.py": f'"""Routes"""',
            project_dir / "app" / "routes.py": f'"""Application routes"""\n\nfrom flask import Blueprint, jsonify\n\nbp = Blueprint("main", __name__)\n\n@bp.route("/")\ndef index():\n    return jsonify({{"message": "Welcome to {project_name}"}})\n\n@bp.route("/health")\ndef health():\n    return jsonify({{"status": "ok"}})\n',
            project_dir / "app" / "templates" / "base.html": '<!DOCTYPE html>\n<html>\n<head>\n    <title>{% block title %}{% endblock %}</title>\n</head>\n<body>\n    {% block content %}{% endblock %}\n</body>\n</html>\n',
            project_dir / "tests" / "__init__.py": '"""Tests"""',
            project_dir / "tests" / "test_routes.py": '"""Test routes"""\n\nimport pytest\nfrom app import create_app\n\nclass TestRoutes:\n    def test_index(self):\n        app = create_app()\n        with app.test_client() as client:\n            response = client.get("/")\n            assert response.status_code == 200\n',
            project_dir / "requirements.txt": "Flask==3.0.0\npytest==7.4.0\n",
            project_dir / "README.md": f"# {project_name}\n\nA Flask project\n\n## Quick Start\n\n```bash\npip install -r requirements.txt\nexport FLASK_APP=app\nflask run\n```\n",
            project_dir / ".gitignore": "__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\n*.egg-info/\ndist/\nbuild/\n.pytest_cache/\n.coverage\ninstance/\n",
        }

        for file_path, content in files.items():
            self._create_file(file_path, content)
            files_created.append(str(file_path.relative_to(project_dir.parent)))

        return files_created

    def _cli_tool_template(
        self,
        project_dir: Path,
        project_name: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """CLI tool template"""
        files_created = []

        files = {
            project_dir / project_name / "__init__.py": f'"""{project_name} CLI tool"""',
            project_dir / project_name / "__init__.py": f'"""{project_name} CLI tool"""\n\n__version__ = "0.1.0"\n',
            project_dir / project_name / "cli.py": f'"""CLI entry point"""\n\nimport argparse\nimport sys\n\n\ndef main():\n    parser = argparse.ArgumentParser(description="{config.get("description", "CLI tool")}")\n    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")\n    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")\n    \n    args = parser.parse_args()\n    \n    if args.verbose:\n        print(f"Running {project_name} v0.1.0")\n    else:\n        print("Use --help for usage information")\n    \n    return 0\n\n\nif __name__ == "__main__":\n    sys.exit(main())\n',
            project_dir / "tests" / "__init__.py": '"""Tests"""',
            project_dir / "tests" / "test_cli.py": f'"""Test CLI"""\n\nimport subprocess\nimport sys\n\ndef test_help():\n    result = subprocess.run([sys.executable, "-m", "{project_name}.cli", "--help"], capture_output=True, text=True)\n    assert result.returncode == 0\n',
            project_dir / "pyproject.toml": f'[project]\nname = "{project_name}"\nversion = "0.1.0"\ndescription = "{config.get("description", "A CLI tool")}"\nrequires-python = ">=3.8"\n\n[project.scripts]\n{project_name} = "{project_name}.cli:main"\n\n[build-system]\nrequires = ["setuptools>=61.0"]\nbuild-backend = "setuptools.build_meta"\n',
            project_dir / "README.md": f"# {project_name}\n\nA CLI tool\n\n## Installation\n\n```bash\npip install -e .\n```\n\n## Usage\n\n```bash\n{project_name} --help\n{project_name} --version\n```\n",
            project_dir / ".gitignore": "__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\n*.egg-info/\ndist/\nbuild/\n.pytest_cache/\n.coverage\n",
        }

        for file_path, content in files.items():
            self._create_file(file_path, content)
            files_created.append(str(file_path.relative_to(project_dir.parent)))

        return files_created

    def _data_science_template(
        self,
        project_dir: Path,
        project_name: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """Data science project template"""
        files_created = []

        files = {
            project_dir / "src" / "__init__.py": '"""Data science project"""',
            project_dir / "src" / "data.py": '"""Data loading and preprocessing"""\n\nimport pandas as pd\nfrom pathlib import Path\n\ndef load_data(data_dir: str = "data"):\n    """Load data from data directory"""\n    data_path = Path(data_dir)\n    # TODO: Implement data loading\n    return None\n',
            project_dir / "src" / "features.py": '"""Feature engineering"""\n\nimport pandas as pd\n\ndef create_features(df):\n    """Create features from raw data"""\n    # TODO: Implement feature engineering\n    return df\n',
            project_dir / "src" / "models.py": '"""Model training"""\n\nfrom sklearn.base import BaseEstimator\n\ndef train_model(X, y):\n    """Train a model"""\n    # TODO: Implement model training\n    return None\n',
            project_dir / "notebooks" / "01-exploration.ipynb": '{"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}',
            project_dir / "notebooks" / "02-modeling.ipynb": '{"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}',
            project_dir / "data" / "raw" / ".gitkeep": "",
            project_dir / "data" / "processed" / ".gitkeep": "",
            project_dir / "models" / ".gitkeep": "",
            project_dir / "tests" / "__init__.py": '"""Tests"""',
            project_dir / "tests" / "test_features.py": '"""Test feature engineering"""\n\nimport pandas as pd\nfrom src.features import create_features\n\ndef test_create_features():\n    df = pd.DataFrame({"a": [1, 2, 3]})\n    result = create_features(df)\n    assert result is not None\n',
            project_dir / "requirements.txt": "pandas==2.1.0\nnumpy==1.24.0\nscikit-learn==1.3.0\nmatplotlib==3.8.0\nseaborn==0.13.0\njupyter==1.0.0\npytest==7.4.0\n",
            project_dir / "README.md": f"# {project_name}\n\nA data science project\n\n## Project Structure\n\n```\n{project_name}/\n├── data/\n│   ├── raw/         # Raw data\n│   └── processed/   # Processed data\n├── notebooks/       # Jupyter notebooks\n├── src/             # Source code\n│   ├── data.py      # Data loading\n│   ├── features.py  # Feature engineering\n│   └── models.py    # Model training\n├── models/          # Trained models\n└── tests/           # Tests\n```\n\n## Quick Start\n\n```bash\npip install -r requirements.txt\n```\n",
            project_dir / ".gitignore": "__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\n*.egg-info/\ndist/\nbuild/\n.pytest_cache/\n.coverage\n*.ipynb_checkpoints\ndata/*\n!data/.gitkeep\nmodels/*\n!models/.gitkeep\n",
        }

        for file_path, content in files.items():
            self._create_file(file_path, content)
            files_created.append(str(file_path.relative_to(project_dir.parent)))

        return files_created

    def _langgraph_agent_template(
        self,
        project_dir: Path,
        project_name: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """LangGraph multi-agent project template"""
        files_created = []

        files = {
            project_dir / project_name / "__init__.py": f'"""{project_name} - LangGraph Agent Project"""',
            project_dir / project_name / "__init__.py": f'"""{project_name}"""\n\n__version__ = "0.1.0"\n',
            project_dir / project_name / "graph" / "__init__.py": '"""LangGraph workflow"""',
            project_dir / project_name / "graph" / "workflow.py": f'"""LangGraph workflow definition"""\n\nfrom typing import TypedDict, Optional\nfrom langgraph.graph import StateGraph, END\n\n\nclass AgentState(TypedDict):\n    """State for the agent workflow"""\n    task: str\n    result: Optional[str]\n    error: Optional[str]\n\n\ndef create_workflow():\n    """Create the LangGraph workflow"""\n    workflow = StateGraph(AgentState)\n    \n    # Add nodes\n    workflow.add_node("agent", lambda state: state)\n    workflow.set_entry_point("agent")\n    workflow.add_edge("agent", END)\n    \n    return workflow.compile()\n',
            project_dir / project_name / "agents" / "__init__.py": '"""Agent implementations"""',
            project_dir / project_name / "agents" / "base.py": f'"""Base agent class"""\n\nfrom abc import ABC, abstractmethod\n\n\nclass BaseAgent(ABC):\n    """Base class for all agents"""\n    \n    @abstractmethod\n    def execute(self, task: str) -> dict:\n        """Execute the agent task"""\n        pass\n',
            project_dir / project_name / "skills" / "__init__.py": '"""Skills registry"""',
            project_dir / "tests" / "__init__.py": '"""Tests"""',
            project_dir / "tests" / "test_workflow.py": f'"""Test workflow"""\n\nimport pytest\nfrom {project_name}.graph.workflow import create_workflow\n\ndef test_workflow():\n    workflow = create_workflow()\n    assert workflow is not None\n',
            project_dir / "requirements.txt": "langgraph==0.0.1\nlangchain==0.1.0\nlangchain-core==0.1.0\npytest==7.4.0\n",
            project_dir / "README.md": f"# {project_name}\n\nA LangGraph multi-agent project\n\n## Project Structure\n\n```\n{project_name}/\n├── {project_name}/\n│   ├── graph/\n│   │   └── workflow.py  # LangGraph workflow\n│   ├── agents/        # Agent implementations\n│   └── skills/        # Skills registry\n└── tests/\n```\n\n## Quick Start\n\n```bash\npip install -r requirements.txt\n```\n\n## Running\n\n```bash\npython -m {project_name}\n```\n",
            project_dir / ".gitignore": "__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\n*.egg-info/\ndist/\nbuild/\n.pytest_cache/\n.coverage\n",
        }

        for file_path, content in files.items():
            self._create_file(file_path, content)
            files_created.append(str(file_path.relative_to(project_dir.parent)))

        return files_created

    def _generic_template(
        self,
        project_dir: Path,
        project_name: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """Generic project template"""
        files_created = []

        files = {
            project_dir / project_name / "__init__.py": f'"""{project_name} package"""',
            project_dir / "tests" / "__init__.py": '"""Tests"""',
            project_dir / "README.md": f"# {project_name}\n\n{config.get('description', 'A new project')}",
            project_dir / "requirements.txt": "# Dependencies\n",
            project_dir / ".gitignore": "__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\n*.egg-info/\ndist/\nbuild/\n.pytest_cache/\n.coverage\n",
        }

        for file_path, content in files.items():
            self._create_file(file_path, content)
            files_created.append(str(file_path.relative_to(project_dir.parent)))

        return files_created
