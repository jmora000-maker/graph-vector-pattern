# SimpleVectorStore, embedding, and cosine similarity

import json
import numpy as np
from pathlib import Path
from typing import List, Dict
from openai import OpenAI
from src.config import API_KEY

# Initialize client locally in the module
client = OpenAI(api_key=API_KEY)
IS_ENABLED = API_KEY != "mock-key-for-local-ui-safety"

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    """Splits long text into manageable chunks for embedding."""
    if chunk_size <= 0: return []
    words = text.split()
    step = max(1, chunk_size - overlap)
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), step)]

def get_embedding(text: str) -> List[float]:
    """Generates OpenAI embeddings."""
    if not IS_ENABLED: return []
    try:
        response = client.embeddings.create(model="text-embedding-3-small", input=text)
        return response.data[0].embedding
    except Exception:
        return []

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates similarity between two vectors."""
    if not v1 or not v2: return 0.0
    a, b = np.array(v1), np.array(v2)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / norm) if norm > 0 else 0.0

class SimpleVectorStore:
    def __init__(self):
        self.entries = []

    def save(self, path: Path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.entries, f)

    def load(self, path: Path):
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                self.entries = json.load(f)

    def build_indices(self, chunks: List[Dict]):
        self.entries = []
        for chunk in chunks:
            embedding = get_embedding(chunk["text"])
            if embedding:
                self.entries.append({**chunk, "embedding": embedding})

    def search(self, query: str, top_k: int = 2, min_similarity: float = 0.20) -> List[Dict]:
        if not IS_ENABLED or not self.entries: return []
        query_vector = get_embedding(query)
        if not query_vector: return []

        scored = []
        for entry in self.entries:
            sim = cosine_similarity(query_vector, entry["embedding"])
            if sim >= min_similarity:
                scored.append((sim, entry))

        scored.sort(reverse=True, key=lambda x: x[0])
        return [{"source": item[1]["metadata"].get("source"), "snippet": item[1]["text"], "score": round(item[0], 3)}
                for item in scored[:top_k]]