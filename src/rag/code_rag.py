"""RAG-based code retrieval system"""

import os
import json
import pickle
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not available, using simple similarity search")

from .code_chunker import CodeChunker
from .embedding_client import EmbeddingClient, get_embedding_client


class CodeRAG:
    """RAG system for code semantic retrieval

    Features:
    - Index code files into vector database
    - Semantic search for code snippets
    - Function/class level retrieval
    - Persistent index storage
    """

    DEFAULT_INDEX_DIR = "rag_index"

    def __init__(
        self,
        repo_path: str = ".",
        index_dir: Optional[str] = None,
        embedding_client: Optional[EmbeddingClient] = None,
        chunk_size: int = 500,
        use_local_embedding: bool = False
    ):
        """Initialize CodeRAG

        Args:
            repo_path: Path to the code repository
            index_dir: Directory for storing index files
            embedding_client: Custom embedding client
            chunk_size: Size of code chunks
            use_local_embedding: Whether to use local embedding model
        """
        self.repo_path = Path(repo_path).absolute()
        self.index_dir = Path(index_dir or self.DEFAULT_INDEX_DIR)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.chunker = CodeChunker(chunk_size=chunk_size)
        self.embedding_client = embedding_client or get_embedding_client(use_local=use_local_embedding)

        # Index storage
        self._index = None
        self._chunks: List[Dict[str, Any]] = []
        self._embeddings: List[List[float]] = []
        self._index_metadata: List[Dict[str, Any]] = []

        # Index file paths
        self._index_file = self.index_dir / "code_index.faiss"
        self._chunks_file = self.index_dir / "chunks.pkl"
        self._metadata_file = self.index_dir / "metadata.pkl"

        # Load existing index if available
        self._load_index()

    def _load_index(self):
        """Load existing index from disk"""
        if FAISS_AVAILABLE and self._index_file.exists():
            try:
                self._index = faiss.read_index(str(self._index_file))
                print(f"Loaded FAISS index with {self._index.ntotal} vectors")
            except Exception as e:
                print(f"Failed to load FAISS index: {e}")
                self._index = None

        if self._chunks_file.exists():
            try:
                with open(self._chunks_file, 'rb') as f:
                    self._chunks = pickle.load(f)
                print(f"Loaded {len(self._chunks)} chunks")
            except Exception as e:
                print(f"Failed to load chunks: {e}")
                self._chunks = []

        if self._metadata_file.exists():
            try:
                with open(self._metadata_file, 'rb') as f:
                    self._index_metadata = pickle.load(f)
            except Exception as e:
                print(f"Failed to load metadata: {e}")
                self._index_metadata = []

    def _save_index(self):
        """Save index to disk"""
        if FAISS_AVAILABLE and self._index is not None:
            try:
                faiss.write_index(self._index, str(self._index_file))
            except Exception as e:
                print(f"Failed to save FAISS index: {e}")

        with open(self._chunks_file, 'wb') as f:
            pickle.dump(self._chunks, f)

        with open(self._metadata_file, 'wb') as f:
            pickle.dump(self._index_metadata, f)

    def build_index(
        self,
        extensions: Optional[List[str]] = None,
        exclude_dirs: Optional[List[str]] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """Build index from repository

        Args:
            extensions: File extensions to include
            exclude_dirs: Directories to exclude
            show_progress: Show progress messages

        Returns:
            Build statistics
        """
        start_time = time.time()

        # Chunk all files
        if show_progress:
            print(f"Chunking files from {self.repo_path}...")

        chunks = self.chunker.chunk_directory(
            str(self.repo_path),
            extensions=extensions,
            exclude_dirs=exclude_dirs
        )

        if not chunks:
            return {
                "success": False,
                "error": "No chunks generated",
                "duration": time.time() - start_time
            }

        # Generate embeddings
        if show_progress:
            print(f"Generating embeddings for {len(chunks)} chunks...")

        texts = [chunk["content"] for chunk in chunks]
        embeddings = []

        # Batch embedding for efficiency
        batch_size = 20
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_embeddings = self.embedding_client.embed_texts(batch_texts)
            embeddings.extend(batch_embeddings)

            if show_progress and (i + batch_size) % 100 == 0:
                print(f"  Embedded {i + batch_size}/{len(texts)} chunks...")

        # Create FAISS index
        if FAISS_AVAILABLE:
            dimension = len(embeddings[0]) if embeddings else self.embedding_client.dimension
            self._index = faiss.IndexFlatL2(dimension)

            # Add vectors to index
            vectors = np.array(embeddings, dtype=np.float32)
            self._index.add(vectors)

        # Store chunks and metadata
        self._chunks = chunks
        self._embeddings = embeddings
        self._index_metadata = [
            {
                "chunk_id": i,
                "file_path": chunk["metadata"].get("file_path", ""),
                "type": chunk["metadata"].get("type", ""),
                "name": chunk["metadata"].get("name", ""),
                "language": chunk["metadata"].get("language", "")
            }
            for i, chunk in enumerate(chunks)
        ]

        # Save to disk
        self._save_index()

        duration = time.time() - start_time

        result = {
            "success": True,
            "total_chunks": len(chunks),
            "total_embeddings": len(embeddings),
            "index_size": self._index.ntotal if FAISS_AVAILABLE and self._index else len(embeddings),
            "duration": round(duration, 2),
            "chunk_summary": self.chunker.get_chunk_summary(chunks)
        }

        if show_progress:
            print(f"Index built successfully in {duration:.2f}s")
            print(f"  Total chunks: {len(chunks)}")
            print(f"  Index size: {result['index_size']}")

        return result

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_type: Optional[str] = None,
        filter_file: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant code chunks

        Args:
            query: Search query
            top_k: Number of results to return
            filter_type: Filter by chunk type (function, class, etc.)
            filter_file: Filter by file path

        Returns:
            List of search results
        """
        if not self._chunks:
            return []

        # Generate query embedding
        query_embedding = self.embedding_client.embed_text(query)

        if FAISS_AVAILABLE and self._index is not None:
            # Use FAISS for search
            query_vector = np.array([query_embedding], dtype=np.float32)
            distances, indices = self._index.search(query_vector, min(top_k * 3, len(self._chunks)))

            results = []
            for i, idx in enumerate(indices[0]):
                if idx < 0 or idx >= len(self._chunks):
                    continue

                chunk = self._chunks[idx]
                metadata = chunk.get("metadata", {})

                # Apply filters
                if filter_type and metadata.get("type") != filter_type:
                    continue
                if filter_file and filter_file not in metadata.get("file_path", ""):
                    continue

                results.append({
                    "content": chunk["content"],
                    "metadata": metadata,
                    "score": float(distances[0][i]),
                    "chunk_id": int(idx)
                })

                if len(results) >= top_k:
                    break

            return results

        else:
            # Simple similarity search without FAISS
            similarities = []
            for i, embedding in enumerate(self._embeddings):
                similarity = self.embedding_client.get_similarity(query_embedding, embedding)
                similarities.append((i, similarity))

            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)

            results = []
            for idx, sim in similarities[:top_k * 3]:
                chunk = self._chunks[idx]
                metadata = chunk.get("metadata", {})

                # Apply filters
                if filter_type and metadata.get("type") != filter_type:
                    continue
                if filter_file and filter_file not in metadata.get("file_path", ""):
                    continue

                results.append({
                    "content": chunk["content"],
                    "metadata": metadata,
                    "score": sim,
                    "chunk_id": idx
                })

                if len(results) >= top_k:
                    break

            return results

    def search_by_function_name(
        self,
        function_name: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for functions by name

        Args:
            function_name: Function name to search
            top_k: Number of results

        Returns:
            List of matching functions
        """
        return self.search(
            query=f"function {function_name}",
            top_k=top_k,
            filter_type="function"
        )

    def search_by_class_name(
        self,
        class_name: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for classes by name

        Args:
            class_name: Class name to search
            top_k: Number of results

        Returns:
            List of matching classes
        """
        return self.search(
            query=f"class {class_name}",
            top_k=top_k,
            filter_type="class"
        )

    def search_in_file(
        self,
        query: str,
        file_path: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search within a specific file

        Args:
            query: Search query
            file_path: File path to search in
            top_k: Number of results

        Returns:
            List of results from the file
        """
        return self.search(
            query=query,
            top_k=top_k,
            filter_file=file_path
        )

    def get_context_for_query(
        self,
        query: str,
        max_tokens: int = 2000,
        top_k: int = 10
    ) -> str:
        """Get formatted context for LLM prompt

        Args:
            query: Query string
            max_tokens: Maximum tokens for context
            top_k: Number of chunks to retrieve

        Returns:
            Formatted context string
        """
        results = self.search(query, top_k=top_k)

        if not results:
            return ""

        context_parts = ["相关代码片段:\n"]
        estimated_tokens = 0

        for i, result in enumerate(results):
            chunk_text = f"\n--- 代码片段 {i+1} ---\n"
            chunk_text += f"文件: {result['metadata'].get('file_path', 'unknown')}\n"
            chunk_text += f"类型: {result['metadata'].get('type', 'unknown')}\n"
            chunk_text += f"相关度: {result['score']:.4f}\n\n"
            chunk_text += result['content']

            chunk_tokens = len(chunk_text) // 4

            if estimated_tokens + chunk_tokens > max_tokens:
                break

            context_parts.append(chunk_text)
            estimated_tokens += chunk_tokens

        return "\n".join(context_parts)

    def add_chunk(
        self,
        content: str,
        metadata: Dict[str, Any]
    ):
        """Add a single chunk to the index

        Args:
            content: Chunk content
            metadata: Chunk metadata
        """
        chunk = {
            "content": content,
            "metadata": metadata
        }

        embedding = self.embedding_client.embed_text(content)

        if FAISS_AVAILABLE and self._index is not None:
            vector = np.array([embedding], dtype=np.float32)
            self._index.add(vector)

        self._chunks.append(chunk)
        self._embeddings.append(embedding)
        self._index_metadata.append({
            "chunk_id": len(self._chunks) - 1,
            "file_path": metadata.get("file_path", ""),
            "type": metadata.get("type", ""),
            "name": metadata.get("name", ""),
            "language": metadata.get("language", "")
        })

    def remove_chunk(self, chunk_id: int):
        """Remove a chunk from index (requires rebuild)"""
        if chunk_id < 0 or chunk_id >= len(self._chunks):
            return

        # Note: FAISS doesn't support removal, so we mark and rebuild on save
        self._chunks[chunk_id] = None
        self._embeddings[chunk_id] = None

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            "total_chunks": len(self._chunks),
            "active_chunks": sum(1 for c in self._chunks if c is not None),
            "index_size": self._index.ntotal if FAISS_AVAILABLE and self._index else len(self._embeddings),
            "embedding_dimension": self.embedding_client.dimension,
            "embedding_model": self.embedding_client.model,
            "faiss_available": FAISS_AVAILABLE,
            "repo_path": str(self.repo_path),
            "index_dir": str(self.index_dir)
        }

    def clear_index(self):
        """Clear the index"""
        self._chunks = []
        self._embeddings = []
        self._index_metadata = []

        if FAISS_AVAILABLE:
            dimension = self.embedding_client.dimension
            self._index = faiss.IndexFlatL2(dimension)

        # Remove files
        for file_path in [self._index_file, self._chunks_file, self._metadata_file]:
            if file_path.exists():
                file_path.unlink()


def create_code_rag(
    repo_path: str = ".",
    use_local_embedding: bool = True,
    rebuild_index: bool = False
) -> CodeRAG:
    """Create or load CodeRAG instance

    Args:
        repo_path: Repository path
        use_local_embedding: Use local embedding model
        rebuild_index: Force rebuild index

    Returns:
        CodeRAG instance
    """
    rag = CodeRAG(
        repo_path=repo_path,
        use_local_embedding=use_local_embedding
    )

    if rebuild_index or len(rag._chunks) == 0:
        rag.build_index(show_progress=True)

    return rag