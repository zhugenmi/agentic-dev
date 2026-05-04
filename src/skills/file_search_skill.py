"""File search skill for locating files in the repository"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from .skill_registry import BaseSkill, SkillMetadata, SkillType, SkillRiskLevel


class FileSearchSkill(BaseSkill):
    """Skill for searching files in the repository"""

    def __init__(self):
        metadata = SkillMetadata(
            name="file_search",
            description="Search for files in the repository by pattern",
            skill_type=SkillType.RESOURCE,
            risk_level=SkillRiskLevel.LOW,
            tags=["repository", "file", "search"],
            execution_timeout=30
        )
        super().__init__(metadata)

    def execute(self, pattern: str, directory: str = ".", file_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for files matching pattern

        Args:
            pattern: Pattern to search for in file names
            directory: Directory to search in (default: current directory)
            file_type: Optional file type filter (python, javascript, etc.)

        Returns:
            Dictionary with search results
        """
        import time
        start_time = time.time()

        try:
            results = []
            search_dir = Path(directory).resolve()

            if not search_dir.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {directory}",
                    "results": []
                }

            for root, dirs, files in os.walk(search_dir):
                # Skip common directories
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv']]

                for file in files:
                    file_path = Path(root) / file
                    rel_path = str(file_path.relative_to(search_dir))

                    # Apply file type filter
                    if file_type:
                        if file_type == "python" and not file.endswith('.py'):
                            continue
                        elif file_type == "javascript" and not file.endswith(('.js', '.ts', '.jsx', '.tsx')):
                            continue
                        elif file_type == "markdown" and not file.endswith(('.md', '.mdown', '.markdown')):
                            continue

                    # Check pattern match
                    if pattern.lower() in file.lower() or pattern in rel_path:
                        results.append({
                            "path": rel_path,
                            "full_path": str(file_path),
                            "size": file_path.stat().st_size,
                            "modified": file_path.stat().st_mtime
                        })

            duration = time.time() - start_time
            self.record_execution(True, duration, {"count": len(results)})

            return {
                "success": True,
                "pattern": pattern,
                "directory": directory,
                "file_type": file_type,
                "results": results[:100],  # Limit results
                "total": len(results),
                "duration": duration
            }

        except Exception as e:
            duration = time.time() - start_time
            self.record_execution(False, duration, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "results": []
            }