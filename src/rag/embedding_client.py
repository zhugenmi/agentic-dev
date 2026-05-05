"""Embedding client for generating text embeddings"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class EmbeddingClient:
    """Client for generating text embeddings

    Supports:
    - OpenAI-compatible embedding APIs
    - Local embedding models (sentence-transformers)
    - Multiple embedding models
    """

    DEFAULT_MODEL = "text-embedding-ada-002"
    DEFAULT_DIMENSION = 1536

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        dimension: Optional[int] = None,
        use_local: bool = False,
        local_model: Optional[str] = None
    ):
        """Initialize embedding client

        Args:
            model: Embedding model name
            api_key: API key for remote embedding service
            base_url: Base URL for embedding API
            dimension: Embedding dimension
            use_local: Whether to use local embedding model
            local_model: Local model name (sentence-transformers)
        """
        self.model = model or os.getenv("EMBEDDING_MODEL", self.DEFAULT_MODEL)
        self.api_key = api_key or os.getenv("EMBEDDING_MODEL_API_KEY", os.getenv("DEFAULT_MODEL_API_KEY", ""))
        self.base_url = base_url or os.getenv("EMBEDDING_MODEL_BASE_URL", os.getenv("DEFAULT_MODEL_BASE_URL", ""))
        self.dimension = dimension or int(os.getenv("EMBEDDING_DIMENSION", str(self.DEFAULT_DIMENSION)))
        self.use_local = use_local

        # Local model
        self._local_model = None
        self._local_model_name = local_model or os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

        if use_local:
            self._init_local_model()

    def _init_local_model(self):
        """Initialize local embedding model"""
        try:
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer(self._local_model_name)
            # Update dimension based on model
            self.dimension = self._local_model.get_sentence_embedding_dimension()
            print(f"Local embedding model initialized: {self._local_model_name} (dimension: {self.dimension})")
        except ImportError:
            print("Warning: sentence-transformers not installed, falling back to API")
            self.use_local = False
        except Exception as e:
            print(f"Warning: Failed to load local model: {e}, falling back to API")
            self.use_local = False

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if self.use_local and self._local_model:
            return self._embed_local([text])[0]

        return self._embed_api(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if self.use_local and self._local_model:
            return self._embed_local(texts)

        return [self._embed_api(text) for text in texts]

    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local model"""
        if self._local_model is None:
            raise RuntimeError("Local model not initialized")

        embeddings = self._local_model.encode(texts)
        return [emb.tolist() for emb in embeddings]

    def _embed_api(self, text: str) -> List[float]:
        """Generate embedding using API"""
        if not self.api_key:
            # Fallback to simple hash-based embedding for demo
            return self._fallback_embedding(text)

        try:
            import requests

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # OpenAI-compatible API format
            endpoint = f"{self.base_url}/embeddings"
            payload = {
                "input": text,
                "model": self.model
            }

            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                return result["data"][0]["embedding"]
            else:
                print(f"Embedding API error: {response.status_code}")
                return self._fallback_embedding(text)

        except Exception as e:
            print(f"Embedding API request failed: {e}")
            return self._fallback_embedding(text)

    def _fallback_embedding(self, text: str) -> List[float]:
        """Fallback embedding using simple hash-based method

        This is a simple deterministic embedding for demonstration
        when no API is available. Not suitable for real semantic search.
        """
        import hashlib

        # Generate deterministic embedding from text hash
        text_hash = hashlib.sha256(text.encode()).hexdigest()

        # Convert hash to float vector
        embedding = []
        for i in range(0, min(len(text_hash), self.dimension * 2), 2):
            hex_pair = text_hash[i:i+2]
            value = int(hex_pair, 16) / 255.0  # Normalize to [0, 1]
            embedding.append(value)

        # Pad to dimension
        while len(embedding) < self.dimension:
            embedding.append(0.0)

        # Normalize
        norm = sum(x**2 for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]

        return embedding[:self.dimension]

    def embed_with_metadata(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate embedding with metadata

        Args:
            text: Text to embed
            metadata: Additional metadata

        Returns:
            Dictionary with embedding and metadata
        """
        embedding = self.embed_text(text)

        return {
            "text": text,
            "embedding": embedding,
            "dimension": len(embedding),
            "model": self.model,
            "metadata": metadata
        }

    def batch_embed(
        self,
        texts_with_metadata: List[Dict[str, Any]],
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """Batch embed texts with metadata

        Args:
            texts_with_metadata: List of dicts with 'text' and 'metadata' keys
            batch_size: Batch size for API calls

        Returns:
            List of embedding results with metadata
        """
        results = []

        for i in range(0, len(texts_with_metadata), batch_size):
            batch = texts_with_metadata[i:i+batch_size]
            texts = [item["text"] for item in batch]

            embeddings = self.embed_texts(texts)

            for j, item in enumerate(batch):
                results.append({
                    "text": item["text"],
                    "embedding": embeddings[j],
                    "dimension": len(embeddings[j]),
                    "model": self.model,
                    "metadata": item.get("metadata", {})
                })

        return results

    def get_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def get_config(self) -> Dict[str, Any]:
        """Get client configuration"""
        return {
            "model": self.model,
            "dimension": self.dimension,
            "use_local": self.use_local,
            "local_model": self._local_model_name if self.use_local else None,
            "base_url": self.base_url if not self.use_local else None
        }


def get_embedding_client(
    use_local: bool = False,
    model: Optional[str] = None
) -> EmbeddingClient:
    """Get embedding client instance

    Args:
        use_local: Whether to use local model
        model: Model name

    Returns:
        EmbeddingClient instance
    """
    return EmbeddingClient(use_local=use_local, model=model)