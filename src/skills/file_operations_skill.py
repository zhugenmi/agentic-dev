"""File operations skill for creating and modifying files"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from .skill_registry import BaseSkill, SkillMetadata, SkillType, SkillRiskLevel


class FileOperationsSkill(BaseSkill):
    """Skill for file operations: create, write, append, delete"""

    def __init__(self):
        metadata = SkillMetadata(
            name="file_operations",
            description="Create, write, and modify files in the repository",
            skill_type=SkillType.TOOL,
            risk_level=SkillRiskLevel.MEDIUM,
            tags=["file", "write", "create", "modify"],
            execution_timeout=60
        )
        super().__init__(metadata)

    def execute(
        self,
        operation: str,
        file_path: str,
        content: Optional[str] = None,
        mode: str = "w",
        create_dirs: bool = True
    ) -> Dict[str, Any]:
        """
        Execute file operation

        Args:
            operation: Operation type (create, write, append, delete, read)
            file_path: Path to the file
            content: Content to write (for create/write/append)
            mode: File mode (default: "w")
            create_dirs: Whether to create parent directories (default: True)

        Returns:
            Dictionary with operation result
        """
        import time
        start_time = time.time()

        try:
            file_path = Path(file_path)

            if operation == "create" or operation == "write":
                return self._write_file(file_path, content, create_dirs, start_time)
            elif operation == "append":
                return self._append_file(file_path, content, create_dirs, start_time)
            elif operation == "read":
                return self._read_file(file_path, start_time)
            elif operation == "delete":
                return self._delete_file(file_path, start_time)
            elif operation == "exists":
                return self._check_exists(file_path, start_time)
            else:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }

        except Exception as e:
            duration = time.time() - start_time
            self.record_execution(False, duration, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "operation": operation
            }

    def _write_file(
        self,
        file_path: Path,
        content: str,
        create_dirs: bool,
        start_time: float
    ) -> Dict[str, Any]:
        """Write content to file"""
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        duration = time.time() - start_time
        self.record_execution(True, duration, {"file": str(file_path), "size": len(content)})

        return {
            "success": True,
            "operation": "write",
            "file_path": str(file_path),
            "bytes_written": len(content),
            "duration": duration
        }

    def _append_file(
        self,
        file_path: Path,
        content: str,
        create_dirs: bool,
        start_time: float
    ) -> Dict[str, Any]:
        """Append content to file"""
        if create_dirs and not file_path.parent.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)

        duration = time.time() - start_time
        self.record_execution(True, duration, {"file": str(file_path), "size": len(content)})

        return {
            "success": True,
            "operation": "append",
            "file_path": str(file_path),
            "bytes_appended": len(content),
            "duration": duration
        }

    def _read_file(self, file_path: Path, start_time: float) -> Dict[str, Any]:
        """Read file content"""
        if not file_path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "content": None
            }

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        duration = time.time() - start_time
        self.record_execution(True, duration, {"file": str(file_path), "size": len(content)})

        return {
            "success": True,
            "operation": "read",
            "file_path": str(file_path),
            "content": content,
            "size": len(content),
            "duration": duration
        }

    def _delete_file(self, file_path: Path, start_time: float) -> Dict[str, Any]:
        """Delete file"""
        if not file_path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }

        os.remove(file_path)

        duration = time.time() - start_time
        self.record_execution(True, duration, {"file": str(file_path)})

        return {
            "success": True,
            "operation": "delete",
            "file_path": str(file_path),
            "duration": duration
        }

    def _check_exists(self, file_path: Path, start_time: float) -> Dict[str, Any]:
        """Check if file exists"""
        exists = file_path.exists()
        is_file = file_path.is_file() if exists else False
        is_dir = file_path.is_dir() if exists else False

        duration = time.time() - start_time
        self.record_execution(True, duration, {"file": str(file_path), "exists": exists})

        return {
            "success": True,
            "operation": "exists",
            "file_path": str(file_path),
            "exists": exists,
            "is_file": is_file,
            "is_dir": is_dir,
            "duration": duration
        }


class DirectoryOperationsSkill(BaseSkill):
    """Skill for directory operations: create, list, delete"""

    def __init__(self):
        metadata = SkillMetadata(
            name="directory_operations",
            description="Create, list, and manage directories",
            skill_type=SkillType.TOOL,
            risk_level=SkillRiskLevel.MEDIUM,
            tags=["directory", "folder", "create", "list"],
            execution_timeout=60
        )
        super().__init__(metadata)

    def execute(
        self,
        operation: str,
        directory: str,
        recursive: bool = False,
        pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute directory operation

        Args:
            operation: Operation type (create, list, delete, exists)
            directory: Path to the directory
            recursive: Whether to operate recursively (for list/delete)
            pattern: File pattern filter (for list)

        Returns:
            Dictionary with operation result
        """
        import time
        start_time = time.time()

        try:
            directory = Path(directory)

            if operation == "create":
                return self._create_directory(directory, start_time)
            elif operation == "list":
                return self._list_directory(directory, recursive, pattern, start_time)
            elif operation == "delete":
                return self._delete_directory(directory, recursive, start_time)
            elif operation == "exists":
                return self._check_exists(directory, start_time)
            else:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }

        except Exception as e:
            duration = time.time() - start_time
            self.record_execution(False, duration, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "operation": operation
            }

    def _create_directory(self, directory: Path, start_time: float) -> Dict[str, Any]:
        """Create directory"""
        if directory.exists():
            return {
                "success": False,
                "error": f"Directory already exists: {directory}"
            }

        directory.mkdir(parents=True, exist_ok=True)

        duration = time.time() - start_time
        self.record_execution(True, duration, {"directory": str(directory)})

        return {
            "success": True,
            "operation": "create",
            "directory": str(directory),
            "duration": duration
        }

    def _list_directory(
        self,
        directory: Path,
        recursive: bool,
        pattern: Optional[str],
        start_time: float
    ) -> Dict[str, Any]:
        """List directory contents"""
        if not directory.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory}"
            }

        if not directory.is_dir():
            return {
                "success": False,
                "error": f"Not a directory: {directory}"
            }

        results = {
            "directories": [],
            "files": []
        }

        if recursive:
            for root, dirs, files in os.walk(directory):
                rel_root = Path(root).relative_to(directory)
                for d in dirs:
                    dir_path = Path(root) / d
                    rel_path = str(dir_path.relative_to(directory))
                    if pattern is None or pattern in rel_path:
                        results["directories"].append(rel_path)
                for f in files:
                    file_path = Path(root) / f
                    rel_path = str(file_path.relative_to(directory))
                    if pattern is None or pattern in rel_path:
                        results["files"].append(rel_path)
        else:
            for item in directory.iterdir():
                rel_path = str(item.relative_to(directory))
                if pattern and pattern not in rel_path:
                    continue
                if item.is_dir():
                    results["directories"].append(rel_path)
                else:
                    results["files"].append(rel_path)

        duration = time.time() - start_time
        self.record_execution(True, duration, {"directory": str(directory), "recursive": recursive})

        return {
            "success": True,
            "operation": "list",
            "directory": str(directory),
            "recursive": recursive,
            "contents": results,
            "total_dirs": len(results["directories"]),
            "total_files": len(results["files"]),
            "duration": duration
        }

    def _delete_directory(self, directory: Path, recursive: bool, start_time: float) -> Dict[str, Any]:
        """Delete directory"""
        if not directory.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory}"
            }

        import shutil
        if recursive:
            shutil.rmtree(directory)
        else:
            directory.rmdir()

        duration = time.time() - start_time
        self.record_execution(True, duration, {"directory": str(directory)})

        return {
            "success": True,
            "operation": "delete",
            "directory": str(directory),
            "recursive": recursive,
            "duration": duration
        }

    def _check_exists(self, directory: Path, start_time: float) -> Dict[str, Any]:
        """Check if directory exists"""
        exists = directory.exists()
        is_dir = directory.is_dir() if exists else False

        duration = time.time() - start_time
        self.record_execution(True, duration, {"directory": str(directory), "exists": exists})

        return {
            "success": True,
            "operation": "exists",
            "directory": str(directory),
            "exists": exists,
            "is_dir": is_dir,
            "duration": duration
        }
