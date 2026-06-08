"""Stage 3 — Embedding + vector store.

Embeds every chunk with all-MiniLM-L6-v2 (local sentence-transformers model) and
stores them in a persistent ChromaDB collection with source metadata for later
attribution. Re-running rebuilds the collection from scratch so the index always
matches the current documents/.

    python embed_store.py
"""

import chromadb
from sentence_transformers import SentenceTransformer

from config import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL
from ingest import load_documents
from chunker import chunk_corpus

_model = None


def get_model() -> SentenceTransformer:
    """Lazy singleton so we load the ~80MB model only once per process."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def get_collection():
    """Return the persistent Chroma collection (creating it if needed)."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # cosine distance for normalized text embeddings
    )


def build_index() -> int:
    """(Re)build the vector store from documents/. Returns the chunk count."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    # start clean so deleted/edited documents don't linger in the index
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )

    records = chunk_corpus(load_documents())
    model = get_model()
    embeddings = model.encode(
        [r["text"] for r in records], show_progress_bar=True, normalize_embeddings=True
    )

    collection.add(
        ids=[r["id"] for r in records],
        documents=[r["text"] for r in records],
        embeddings=[e.tolist() for e in embeddings],
        metadatas=[{"source": r["source"], "position": r["position"]} for r in records],
    )
    return len(records)


if __name__ == "__main__":
    n = build_index()
    print(f"\nIndexed {n} chunks into ChromaDB at {CHROMA_DIR}")
