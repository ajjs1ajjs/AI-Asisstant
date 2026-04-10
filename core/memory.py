# 🧠 Global Memory Engine
# Singleton for cross-project semantic search.

import os
import json
import faiss
import numpy as np
from datetime import datetime

class GlobalMemoryEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalMemoryEngine, cls).__new__(cls)
            cls._instance._init_engine()
        return cls._instance

    def _init_engine(self):
        self.memory_path = os.path.expanduser("~/.ai-ide/global_memory")
        os.makedirs(self.memory_path, exist_ok=True)
        self.index_file = os.path.join(self.memory_path, "global_faiss.index")
        self.meta_file = os.path.join(self.memory_path, "metadata.json")
        
        self.dimension = 384 # Default for all-MiniLM-L6-v2
        if os.path.exists(self.index_file):
            self.index = faiss.read_index(self.index_file)
            with open(self.meta_file, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []

    def add_entry(self, project_name, file_path, content, embedding):
        """Adds a code snippet to global memory"""
        vector = np.array([embedding]).astype('float32')
        self.index.add(vector)
        self.metadata.append({
            "project": project_name,
            "path": file_path,
            "snippet": content[:500],
            "timestamp": datetime.now().isoformat()
        })
        self._save()

    def search(self, embedding, top_k=5):
        """Search global memory for similar snippets"""
        if self.index.ntotal == 0:
            return []
        
        vector = np.array([embedding]).astype('float32')
        distances, indices = self.index.search(vector, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):
                results.append(self.metadata[idx])
        return results

    def _save(self):
        faiss.write_index(self.index, self.index_file)
        with open(self.meta_file, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
