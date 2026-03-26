import asyncio
import hashlib
import os
from typing import Dict, List, Optional

import numpy as np


class ContextEngine:
    def __init__(self, embedding_dim: int = 768):
        self.embedding_dim = embedding_dim
        self.index = None
        self.chunks: List[Dict] = []
        self.file_hashes: Dict[str, str] = {}

        try:
            import faiss

            self.index = faiss.IndexFlatL2(embedding_dim)
        except ImportError:
            print("FAISS not installed. Context search disabled.")
            self.index = None

    def get_embedding(self, text: str) -> np.ndarray:
        # Simple hash-based embedding (replace with real model in production)
        hash_bytes = hashlib.md5(text.encode()).digest()
        embedding = np.array([b / 255.0 for b in hash_bytes], dtype=np.float32)
        embedding = np.tile(embedding, self.embedding_dim // 16 + 1)[
            : self.embedding_dim
        ]
        return embedding.reshape(1, -1)

    def chunk_file(
        self, content: str, chunk_size: int = 500, overlap: int = 50
    ) -> List[str]:
        chunks = []
        start = 0
        while start < len(content):
            end = start + chunk_size
            chunk = content[start:end]

            if end < len(content):
                last_newline = chunk.rfind("\n")
                if last_newline > chunk_size // 2:
                    chunk = chunk[:last_newline]
                    end = start + last_newline

            chunks.append(chunk.strip())
            start = end - overlap

        return chunks

    def add_file(self, filepath: str, content: str):
        if self.index is None:
            return

        file_hash = hashlib.md5(content.encode()).hexdigest()

        if self.file_hashes.get(filepath) == file_hash:
            return

        self.file_hashes[filepath] = file_hash

        chunks = self.chunk_file(content)

        for chunk in chunks:
            if len(chunk) < 20:
                continue

            embedding = self.get_embedding(chunk)
            self.index.add(embedding)

            self.chunks.append(
                {
                    "content": chunk,
                    "filepath": filepath,
                    "embedding_index": len(self.chunks),
                }
            )

    def index_project(self, root_dir: str, extensions: List[str] = None):
        if extensions is None:
            extensions = [".py", ".md", ".txt", ".js", ".ts", ".json"]

        for root, dirs, files in os.walk(root_dir):
            if ".git" in root or "__pycache__" in root or "node_modules" in root:
                continue

            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                        self.add_file(filepath, content)
                    except Exception as e:
                        print(f"Error indexing {filepath}: {e}")

    def search(self, query: str, k: int = 5) -> List[Dict]:
        if self.index is None or self.index.ntotal == 0:
            return []

        query_embedding = self.get_embedding(query)

        k = min(k, self.index.ntotal)
        if k == 0:
            return []

        distances, indices = self.index.search(query_embedding, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.chunks):
                results.append(
                    {
                        "content": self.chunks[idx]["content"],
                        "filepath": self.chunks[idx]["filepath"],
                        "distance": float(distances[0][i]),
                    }
                )

        return results

    def get_context_for_query(self, query: str, k: int = 5) -> str:
        results = self.search(query, k)

        if not results:
            return ""

        context_parts = []
        for result in results:
            context_parts.append(f"From {result['filepath']}:\n{result['content']}")

        return "\n\n---\n\n".join(context_parts)

    async def index_project_async(self, root_dir: str, extensions: List[str] = None):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.index_project, root_dir, extensions)

    async def search_async(self, query: str, k: int = 5) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.search, query, k)
