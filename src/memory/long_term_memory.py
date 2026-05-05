"""Long-term memory for persistent knowledge and vector-based retrieval"""

import os
import json
import pickle
import hashlib
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not available, vector search will be disabled")


class LongTermMemory:
    """Long-term memory with vector-based semantic retrieval

    Features:
    - User preferences storage
    - Project knowledge base
    - Historical tasks and solutions
    - FAISS-based vector index for semantic search
    - Persistent storage on disk
    """

    DEFAULT_INDEX_DIMENSION = 768  # Typical embedding dimension
    DEFAULT_STORAGE_DIR = "memory_store"

    def __init__(
        self,
        user_id: str = "default",
        project_id: str = "default",
        storage_dir: Optional[str] = None,
        embedding_dimension: int = None
    ):
        """Initialize long-term memory

        Args:
            user_id: User identifier
            project_id: Project identifier
            storage_dir: Directory for persistent storage
            embedding_dimension: Dimension of embedding vectors
        """
        self.user_id = user_id
        self.project_id = project_id
        self.storage_dir = Path(storage_dir or self.DEFAULT_STORAGE_DIR)
        self.embedding_dimension = embedding_dimension or self.DEFAULT_INDEX_DIMENSION

        # Create storage directory
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Knowledge stores
        self._user_preferences: Dict[str, Any] = {}
        self._project_knowledge: Dict[str, Any] = {}
        self._historical_tasks: List[Dict[str, Any]] = []
        self._code_patterns: List[Dict[str, Any]] = []

        # Vector index (FAISS)
        self._index = None
        self._index_metadata: List[Dict[str, Any]] = []  # Maps index position to content

        # Initialize or load
        self._initialize()

    def _initialize(self):
        """Initialize or load from storage"""
        self._load_user_preferences()
        self._load_project_knowledge()
        self._load_historical_tasks()
        self._initialize_vector_index()

    def _get_user_pref_file(self) -> Path:
        """Get user preferences file path"""
        return self.storage_dir / f"user_{self.user_id}_preferences.json"

    def _get_project_kb_file(self) -> Path:
        """Get project knowledge base file path"""
        return self.storage_dir / f"project_{self.project_id}_kb.json"

    def _get_tasks_file(self) -> Path:
        """Get historical tasks file path"""
        return self.storage_dir / f"tasks_{self.user_id}_{self.project_id}.json"

    def _get_index_file(self) -> Path:
        """Get FAISS index file path"""
        return self.storage_dir / f"index_{self.project_id}.faiss"

    def _get_index_meta_file(self) -> Path:
        """Get index metadata file path"""
        return self.storage_dir / f"index_meta_{self.project_id}.pkl"

    def _load_user_preferences(self):
        """Load user preferences from disk"""
        pref_file = self._get_user_pref_file()
        if pref_file.exists():
            try:
                with open(pref_file, 'r', encoding='utf-8') as f:
                    self._user_preferences = json.load(f)
            except Exception as e:
                print(f"Failed to load user preferences: {e}")
                self._user_preferences = {}

    def _load_project_knowledge(self):
        """Load project knowledge base from disk"""
        kb_file = self._get_project_kb_file()
        if kb_file.exists():
            try:
                with open(kb_file, 'r', encoding='utf-8') as f:
                    self._project_knowledge = json.load(f)
            except Exception as e:
                print(f"Failed to load project knowledge: {e}")
                self._project_knowledge = {}

    def _load_historical_tasks(self):
        """Load historical tasks from disk"""
        tasks_file = self._get_tasks_file()
        if tasks_file.exists():
            try:
                with open(tasks_file, 'r', encoding='utf-8') as f:
                    self._historical_tasks = json.load(f)
            except Exception as e:
                print(f"Failed to load historical tasks: {e}")
                self._historical_tasks = []

    def _initialize_vector_index(self):
        """Initialize FAISS vector index"""
        if not FAISS_AVAILABLE:
            return

        index_file = self._get_index_file()
        meta_file = self._get_index_meta_file()

        if index_file.exists() and meta_file.exists():
            try:
                self._index = faiss.read_index(str(index_file))
                with open(meta_file, 'rb') as f:
                    self._index_metadata = pickle.load(f)
            except Exception as e:
                print(f"Failed to load vector index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self):
        """Create a new FAISS index"""
        if not FAISS_AVAILABLE:
            return

        # Use L2 distance index (most common for semantic search)
        self._index = faiss.IndexFlatL2(self.embedding_dimension)
        self._index_metadata = []

    def _save_user_preferences(self):
        """Save user preferences to disk"""
        pref_file = self._get_user_pref_file()
        try:
            with open(pref_file, 'w', encoding='utf-8') as f:
                json.dump(self._user_preferences, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save user preferences: {e}")

    def _save_project_knowledge(self):
        """Save project knowledge base to disk"""
        kb_file = self._get_project_kb_file()
        try:
            with open(kb_file, 'w', encoding='utf-8') as f:
                json.dump(self._project_knowledge, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save project knowledge: {e}")

    def _save_historical_tasks(self):
        """Save historical tasks to disk"""
        tasks_file = self._get_tasks_file()
        try:
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self._historical_tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save historical tasks: {e}")

    def _save_vector_index(self):
        """Save vector index to disk"""
        if not FAISS_AVAILABLE or self._index is None:
            return

        index_file = self._get_index_file()
        meta_file = self._get_index_meta_file()

        try:
            faiss.write_index(self._index, str(index_file))
            with open(meta_file, 'wb') as f:
                pickle.dump(self._index_metadata, f)
        except Exception as e:
            print(f"Failed to save vector index: {e}")

    # ==================== User Preferences ====================

    def set_preference(self, key: str, value: Any):
        """Set a user preference

        Args:
            key: Preference key
            value: Preference value
        """
        self._user_preferences[key] = {
            "value": value,
            "updated_at": datetime.now().isoformat()
        }
        self._save_user_preferences()

    def get_preference(self, key: str) -> Optional[Any]:
        """Get a user preference

        Args:
            key: Preference key

        Returns:
            Preference value or None
        """
        pref = self._user_preferences.get(key)
        if pref:
            return pref["value"]
        return None

    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all user preferences"""
        return {k: v["value"] for k, v in self._user_preferences.items()}

    # ==================== Project Knowledge ====================

    def add_project_knowledge(
        self,
        category: str,
        key: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add project knowledge

        Args:
            category: Knowledge category (structure, pattern, dependency, etc.)
            key: Knowledge key
            content: Knowledge content
            metadata: Optional metadata
        """
        if category not in self._project_knowledge:
            self._project_knowledge[category] = {}

        self._project_knowledge[category][key] = {
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }
        self._save_project_knowledge()

    def get_project_knowledge(
        self,
        category: Optional[str] = None,
        key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get project knowledge

        Args:
            category: Optional category filter
            key: Optional key filter

        Returns:
            Project knowledge dictionary
        """
        if category and key:
            cat_dict = self._project_knowledge.get(category, {})
            return cat_dict.get(key, {})
        elif category:
            return self._project_knowledge.get(category, {})
        else:
            return dict(self._project_knowledge)

    # ==================== Historical Tasks ====================

    def add_historical_task(
        self,
        task_description: str,
        result: Dict[str, Any],
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a historical task

        Args:
            task_description: Task description
            result: Task result
            success: Whether the task succeeded
            metadata: Optional metadata
        """
        task_record = {
            "id": hashlib.md5(f"{task_description}{datetime.now().isoformat()}".encode()).hexdigest()[:12],
            "task_description": task_description,
            "result": result,
            "success": success,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }

        self._historical_tasks.append(task_record)
        self._save_historical_tasks()

        return task_record["id"]

    def get_similar_tasks(
        self,
        task_description: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get similar historical tasks (keyword matching)

        Args:
            task_description: Task description to match
            limit: Maximum number of results

        Returns:
            List of similar tasks
        """
        # Simple keyword matching for now
        # Can be enhanced with vector similarity later
        keywords = task_description.lower().split()

        similar = []
        for task in self._historical_tasks:
            desc = task["task_description"].lower()
            match_score = sum(1 for kw in keywords if kw in desc)
            if match_score > 0:
                similar.append({
                    **task,
                    "match_score": match_score
                })

        # Sort by match score
        similar.sort(key=lambda x: x["match_score"], reverse=True)

        return similar[:limit]

    def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent historical tasks

        Args:
            limit: Maximum number of results

        Returns:
            List of recent tasks
        """
        return self._historical_tasks[-limit:]

    # ==================== Vector Index ====================

    def add_to_vector_index(
        self,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ):
        """Add content to vector index

        Args:
            content: Content string
            embedding: Embedding vector
            metadata: Metadata associated with the content
        """
        if not FAISS_AVAILABLE or self._index is None:
            return

        if len(embedding) != self.embedding_dimension:
            print(f"Warning: Embedding dimension mismatch. Expected {self.embedding_dimension}, got {len(embedding)}")
            return

        # Add to FAISS index
        vector = np.array([embedding], dtype=np.float32)
        self._index.add(vector)

        # Store metadata
        self._index_metadata.append({
            "content": content,
            "metadata": metadata,
            "added_at": datetime.now().isoformat()
        })

        # Save periodically
        if len(self._index_metadata) % 10 == 0:
            self._save_vector_index()

    def search_vector_index(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search vector index

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return

        Returns:
            List of search results with scores
        """
        if not FAISS_AVAILABLE or self._index is None:
            return []

        if len(self._index_metadata) == 0:
            return []

        if len(query_embedding) != self.embedding_dimension:
            print(f"Warning: Query embedding dimension mismatch")
            return []

        # Search
        query_vector = np.array([query_embedding], dtype=np.float32)
        distances, indices = self._index.search(query_vector, min(top_k, len(self._index_metadata)))

        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self._index_metadata):  # Valid index
                results.append({
                    "content": self._index_metadata[idx]["content"],
                    "metadata": self._index_metadata[idx]["metadata"],
                    "score": float(distances[0][i]),
                    "index": int(idx)
                })

        return results

    def get_index_size(self) -> int:
        """Get number of items in vector index"""
        if self._index is None:
            return 0
        return self._index.ntotal

    # ==================== Code Patterns ====================

    def add_code_pattern(
        self,
        pattern_type: str,
        pattern_code: str,
        description: str,
        usage_context: Optional[str] = None
    ):
        """Add a code pattern

        Args:
            pattern_type: Pattern type (function, class, algorithm, etc.)
            pattern_code: Pattern code
            description: Pattern description
            usage_context: Usage context
        """
        pattern = {
            "id": hashlib.md5(pattern_code.encode()).hexdigest()[:12],
            "type": pattern_type,
            "code": pattern_code,
            "description": description,
            "usage_context": usage_context,
            "created_at": datetime.now().isoformat()
        }

        self._code_patterns.append(pattern)
        self._save_project_knowledge()

    def get_code_patterns(
        self,
        pattern_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get code patterns

        Args:
            pattern_type: Optional pattern type filter
            limit: Maximum number of results

        Returns:
            List of code patterns
        """
        patterns = self._code_patterns

        if pattern_type:
            patterns = [p for p in patterns if p["type"] == pattern_type]

        return patterns[:limit]

    # ==================== Summary & Export ====================

    def get_summary(self) -> Dict[str, Any]:
        """Get memory summary"""
        return {
            "user_id": self.user_id,
            "project_id": self.project_id,
            "preferences_count": len(self._user_preferences),
            "knowledge_categories": len(self._project_knowledge),
            "historical_tasks_count": len(self._historical_tasks),
            "code_patterns_count": len(self._code_patterns),
            "vector_index_size": self.get_index_size(),
            "storage_dir": str(self.storage_dir),
            "faiss_available": FAISS_AVAILABLE
        }

    def clear_all(self):
        """Clear all long-term memory"""
        self._user_preferences.clear()
        self._project_knowledge.clear()
        self._historical_tasks.clear()
        self._code_patterns.clear()

        if FAISS_AVAILABLE:
            self._create_new_index()

        # Delete files
        for file_path in [
            self._get_user_pref_file(),
            self._get_project_kb_file(),
            self._get_tasks_file(),
            self._get_index_file(),
            self._get_index_meta_file()
        ]:
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception:
                    pass