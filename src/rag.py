import json
from pathlib import Path
import numpy as np
from typing import List, Dict, Set, Optional
from src.config import is_vector_search_enabled, client


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    if chunk_size <= 0:
        return []
    if overlap >= chunk_size:
        overlap = max(1, chunk_size // 2)

    words = text.split()
    if not words:
        return []

    step = max(1, chunk_size - overlap)
    chunks = []

    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size]).strip()
        if chunk:
            chunks.append(chunk)

    return chunks


# --- PIPELINE LAYER: VECTOR ENGINE ---
class SimpleVectorStore:
    def __init__(self):
        self.entries = []

    def save(self, path: Path):
        print(" -> Saving vector index.")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.entries, f)

    def load(self, path: Path):
        print(" -> Loading vector index.")
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                self.entries = json.load(f)

    def build_indices(self, chunks: List[Dict]):
        print(" -> Building vector indices.")
        print(f" -> Found {len(chunks)} chunks to index.")
        self.entries = []
        if not is_vector_search_enabled:
            return
        for chunk in chunks:
            embedding = get_embedding(chunk["text"])
            if embedding:
                self.entries.append({**chunk, "embedding": embedding})

    def search(self, query: str, top_k: int = 2, min_similarity: float = 0.20) -> List[Dict]:
        if not is_vector_search_enabled or not self.entries:
            return []

        query_vector = get_embedding(query)
        if not query_vector:
            return []

        scored = []
        for entry in self.entries:
            sim = cosine_similarity(query_vector, entry["embedding"])
            if sim >= min_similarity:
                scored.append((sim, entry))

        scored.sort(reverse=True, key=lambda x: x[0])
        return [
            {
                "source": item[1]["metadata"].get("source", "Unknown"),
                "snippet": item[1]["text"],
                "score": round(item[0], 3)
            }
            for item in scored[:top_k]
        ]


    # --- PIPELINE LAYER: CORE UTILITIES ---


def get_embedding(text: str) -> List[float]:
    if not is_vector_search_enabled:
        return []

    cleaned = " ".join(str(text).split())
    if not cleaned:
        return []

    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=cleaned
        )
        return response.data[0].embedding
    except Exception as e:
        print(f" -> Embedding generation failed: {e}")
        return []


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2:
        return 0.0
    a, b = np.array(v1), np.array(v2)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / norm) if norm > 0 else 0.0
