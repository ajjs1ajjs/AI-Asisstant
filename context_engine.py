"""
Context Engine з використанням sentence-transformers для розумного пошуку
Забезпечує семантичний пошук по кодовій базі проекту
"""

import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np


class ContextEngine:
    """Розумний контекстний пошук на основі семантичних ембедингів"""

    def __init__(
        self,
        embedding_dim: int = 384,
        model_name: str = "all-MiniLM-L6-v2",
        cache_dir: str = None,
    ):
        self.embedding_dim = embedding_dim
        self.model_name = model_name
        self.cache_dir = cache_dir or os.path.join(
            Path.home(), ".ai-ide", "context_cache"
        )
        self.cache_file = os.path.join(self.cache_dir, "index_cache.json")

        # FAISS index
        self.index = None
        self.chunks: List[Dict] = []
        self.file_hashes: Dict[str, str] = {}
        self.chunk_embeddings: List[np.ndarray] = []

        # Model cache
        self._model = None
        self._model_loaded = False

        # Завантаження кешу
        self._load_cache()

    def _get_model(self):
        """Lazy loading моделі ембедингів"""
        if not self._model_loaded:
            try:
                from sentence_transformers import SentenceTransformer

                print(f"🧠 Завантаження моделі ембедингів: {self.model_name}...")
                self._model = SentenceTransformer(self.model_name)
                self._model_loaded = True
                print("✅ Модель ембедингів готова!")
            except ImportError:
                print(
                    "⚠️ sentence-transformers не встановлено. Використовую резервний режим."
                )
                self._model = None
                self._model_loaded = True
            except Exception as e:
                print(f"⚠️ Помилка завантаження моделі: {e}. Резервний режим.")
                self._model = None
                self._model_loaded = True

        return self._model

    def get_embedding(self, text: str) -> np.ndarray:
        """Отримати ембединг тексту"""
        model = self._get_model()

        if model is not None:
            try:
                embedding = model.encode([text], convert_to_numpy=True)[0]
                return embedding.reshape(1, -1).astype(np.float32)
            except Exception as e:
                print(f"⚠️ Помилка ембедингу: {e}")

        # Резервний режим: TF-IDF подібний підхід
        return self._fallback_embedding(text)

    def _fallback_embedding(self, text: str) -> np.ndarray:
        """Резервний метод ембедингу (TF-IDF + hash)"""
        # Tokenize
        tokens = text.lower().split()
        token_hash = {}

        for token in tokens:
            if len(token) > 2:
                h = hashlib.sha256(token.encode()).digest()
                token_hash[token] = np.frombuffer(h[:16], dtype=np.uint8).astype(
                    np.float32
                ) / 255.0

        # Average pooling
        if token_hash:
            embeddings = np.array(list(token_hash.values()))
            avg_embedding = np.mean(embeddings, axis=0)
            # Pad to embedding_dim
            if len(avg_embedding) < self.embedding_dim:
                avg_embedding = np.pad(
                    avg_embedding,
                    (0, self.embedding_dim - len(avg_embedding)),
                    mode="constant",
                )
            else:
                avg_embedding = avg_embedding[: self.embedding_dim]
        else:
            avg_embedding = np.zeros(self.embedding_dim, dtype=np.float32)

        return avg_embedding.reshape(1, -1)

    def chunk_file(
        self, content: str, chunk_size: int = 300, overlap: int = 50
    ) -> List[Tuple[str, int, int]]:
        """
        Розбити файл на розумні чанки

        Returns:
            List of (chunk_text, start_line, end_line)
        """
        chunks = []
        lines = content.split("\n")

        # Групуємо по функціях/класах
        current_chunk = []
        current_size = 0
        chunk_start = 0

        for i, line in enumerate(lines):
            # Чи починається нова функція/клас?
            is_definition = (
                line.strip().startswith(("def ", "class ", "function ", "async "))
                or ("{" in line and current_size > 100)
                or ("}" in line and current_size > 100)
            )

            if is_definition and current_chunk:
                # Зберегти поточний чанк
                chunk_text = "\n".join(current_chunk)
                if len(chunk_text.strip()) > 20:
                    chunks.append((chunk_text, chunk_start, i))

                # Почати новий з overlap
                overlap_lines = min(overlap, len(current_chunk))
                current_chunk = current_chunk[-overlap_lines:]
                current_size = sum(len(l) for l in current_chunk)
                chunk_start = i - overlap_lines

            current_chunk.append(line)
            current_size += len(line)

            # Якщо чанк занадто великий
            if current_size >= chunk_size:
                chunk_text = "\n".join(current_chunk)
                if len(chunk_text.strip()) > 20:
                    chunks.append((chunk_text, chunk_start, i))
                current_chunk = []
                current_size = 0
                chunk_start = i + 1

        # Останній чанк
        if current_chunk:
            chunk_text = "\n".join(current_chunk)
            if len(chunk_text.strip()) > 20:
                chunks.append((chunk_text, chunk_start, len(lines)))

        return chunks

    def add_file(self, filepath: str, content: str) -> int:
        """Додати файл до індексу"""
        if self.index is None:
            try:
                import faiss

                self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product
            except ImportError:
                print("⚠️ FAISS not installed. Context search disabled.")
                return 0

        file_hash = hashlib.md5(content.encode()).hexdigest()

        # Перевірка чи файл вже індексовано
        if self.file_hashes.get(filepath) == file_hash:
            return 0

        # Видалити старі чанки цього файлу
        self._remove_file_chunks(filepath)

        self.file_hashes[filepath] = file_hash

        # Розбити на чанки
        chunk_data = self.chunk_file(content)
        added = 0

        for chunk_text, start_line, end_line in chunk_data:
            if len(chunk_text.strip()) < 20:
                continue

            try:
                embedding = self.get_embedding(chunk_text)

                # Нормалізувати для cosine similarity
                from faiss import normalize_L2

                normalize_L2(embedding)

                self.index.add(embedding)
                self.chunk_embeddings.append(embedding[0])

                self.chunks.append(
                    {
                        "content": chunk_text,
                        "filepath": filepath,
                        "start_line": start_line,
                        "end_line": end_line,
                        "embedding_index": len(self.chunks),
                    }
                )
                added += 1
            except Exception as e:
                print(f"⚠️ Помилка додавання чанку: {e}")

        # Зберегти кеш
        self._save_cache()

        return added

    def _remove_file_chunks(self, filepath: str):
        """Видалити всі чанки файлу"""
        # Знайти індекси чанків для видалення
        to_remove = [
            i for i, chunk in enumerate(self.chunks) if chunk["filepath"] == filepath
        ]

        if not to_remove:
            return

        # Видалити чанки (з кінця, щоб індекси не змістилися)
        for i in sorted(to_remove, reverse=True):
            if i < len(self.chunks):
                self.chunks.pop(i)
            if i < len(self.chunk_embeddings):
                self.chunk_embeddings.pop(i)

        # Перестворити індекс
        if self.index is not None and self.chunk_embeddings:
            try:
                import faiss

                self.index = faiss.IndexFlatIP(self.embedding_dim)
                embeddings = np.array(self.chunk_embeddings)
                faiss.normalize_L2(embeddings)
                self.index.add(embeddings)
            except:
                pass

    def index_project(
        self, root_dir: str, extensions: List[str] = None, max_files: int = 500
    ) -> Dict:
        """Індексувати весь проект"""
        if extensions is None:
            extensions = [
                ".py",
                ".md",
                ".txt",
                ".js",
                ".ts",
                ".jsx",
                ".tsx",
                ".json",
                ".yaml",
                ".yml",
                ".cpp",
                ".c",
                ".h",
                ".java",
                ".cs",
                ".go",
                ".rs",
                ".php",
                ".rb",
                ".swift",
            ]

        stats = {
            "files_indexed": 0,
            "chunks_added": 0,
            "errors": [],
            "skipped": 0,
        }

        file_count = 0
        for root, dirs, files in os.walk(root_dir):
            # Пропустити службові директорії
            dirs[:] = [
                d
                for d in dirs
                if d not in [".git", "__pycache__", "node_modules", "venv", ".venv", "dist", "build"]
            ]

            for file in files:
                if file_count >= max_files:
                    stats["skipped"] += len(files) - (max_files - file_count)
                    break

                if any(file.endswith(ext) for ext in extensions):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()

                        added = self.add_file(filepath, content)
                        stats["files_indexed"] += 1
                        stats["chunks_added"] += added
                        file_count += 1

                    except Exception as e:
                        stats["errors"].append(f"{filepath}: {str(e)}")

        return stats

    def search(self, query: str, k: int = 5) -> List[Dict]:
        """Пошук схожих чанків"""
        if self.index is None or self.index.ntotal == 0:
            return []

        try:
            query_embedding = self.get_embedding(query)
            from faiss import normalize_L2

            normalize_L2(query_embedding)

            k = min(k, self.index.ntotal)
            if k == 0:
                return []

            # Cosine similarity через inner product (нормалізовані вектори)
            similarities, indices = self.index.search(query_embedding, k)

            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.chunks) and similarities[0][i] > 0.1:  # Поріг
                    chunk = self.chunks[idx]
                    results.append(
                        {
                            "content": chunk["content"],
                            "filepath": chunk["filepath"],
                            "start_line": chunk["start_line"],
                            "end_line": chunk["end_line"],
                            "similarity": float(similarities[0][i]),
                        }
                    )

            return sorted(results, key=lambda x: x["similarity"], reverse=True)

        except Exception as e:
            print(f"⚠️ Помилка пошуку: {e}")
            return []

    def get_context_for_query(self, query: str, k: int = 5, max_tokens: int = 1500) -> str:
        """Отримати контекст для запиту"""
        results = self.search(query, k)

        if not results:
            return ""

        context_parts = []
        current_tokens = 0

        for result in results:
            # Груба оцінка токенів
            tokens = len(result["content"].split()) * 1.3

            if current_tokens + tokens > max_tokens:
                break

            filepath = result["filepath"]
            lines = f"L{result['start_line']}-{result['end_line']}"

            context_parts.append(
                f"📄 Файл: {filepath} ({lines})\n"
                f"{'='*60}\n"
                f"{result['content']}\n"
                f"{'='*60}"
            )
            current_tokens += tokens

        return "\n\n".join(context_parts)

    def _save_cache(self):
        """Зберегти кеш індексу"""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)

            cache_data = {
                "file_hashes": self.file_hashes,
                "chunks": [
                    {k: v for k, v in c.items() if k != "embedding_index"}
                    for c in self.chunks
                ],
                "model_name": self.model_name,
            }

            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)

        except Exception as e:
            print(f"⚠️ Помилка збереження кешу: {e}")

    def _load_cache(self):
        """Завантажити кеш індексу"""
        if not os.path.exists(self.cache_file):
            return

        try:
            with open(self.cache_file, "r") as f:
                cache_data = json.load(f)

            # Перевірка чи та сама модель
            if cache_data.get("model_name") != self.model_name:
                print("🔄 Зміна моделі ембедингів - кеш недійсний")
                return

            self.file_hashes = cache_data.get("file_hashes", {})
            chunk_data = cache_data.get("chunks", [])

            # Відновити чанки (але не індекс - треба переіндексувати)
            for i, c in enumerate(chunk_data):
                c["embedding_index"] = i
                self.chunks.append(c)

            print(f"✅ Завантажено кеш: {len(self.chunks)} чанків")

        except Exception as e:
            print(f"⚠️ Помилка завантаження кешу: {e}")

    def clear_cache(self):
        """Очистити весь кеш"""
        self.chunks.clear()
        self.chunk_embeddings.clear()
        self.file_hashes.clear()

        if self.index is not None:
            self.index = None

        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

        print("🧹 Контекст очищено")

    def get_stats(self) -> Dict:
        """Отримати статистику індексу"""
        return {
            "total_chunks": len(self.chunks),
            "total_files": len(self.file_hashes),
            "index_size": self.index.ntotal if self.index else 0,
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "cache_file": self.cache_file,
        }

    async def index_project_async(
        self, root_dir: str, extensions: List[str] = None, max_files: int = 500
    ):
        """Асинхронне індексування проекту"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.index_project, root_dir, extensions, max_files
        )

    async def search_async(self, query: str, k: int = 5) -> List[Dict]:
        """Асинхронний пошук"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.search, query, k)
