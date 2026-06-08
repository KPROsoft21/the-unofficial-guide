"""Stage 4 — Retrieval.

Embeds the query with the same model used for indexing and returns the top-k most
similar chunks from ChromaDB, each with its source and a cosine distance score
(lower = more similar).

Also offers an optional hybrid (semantic + BM25 keyword) mode — a stretch feature
documented in planning.md — which helps on queries that hinge on a rare exact term
(a professor's name, a course number) that pure semantic search can blur.

    python retrieve.py "is the housing lottery random?"
"""

from config import TOP_K
from embed_store import get_collection, get_model


def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """Pure semantic search. Returns [{text, source, position, distance}, ...]."""
    model = get_model()
    q_emb = model.encode([query], normalize_embeddings=True)[0].tolist()
    res = get_collection().query(query_embeddings=[q_emb], n_results=k)

    hits = []
    for text, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        hits.append({
            "text": text,
            "source": meta["source"],
            "position": meta["position"],
            "distance": round(float(dist), 4),
        })
    return hits


def retrieve_hybrid(query: str, k: int = TOP_K, alpha: float = 0.5) -> list[dict]:
    """Hybrid semantic + BM25 retrieval (stretch feature).

    Scores every chunk by both cosine similarity and BM25 keyword overlap, min-max
    normalizes each to [0,1], and blends them with `alpha` (1.0 = pure semantic,
    0.0 = pure keyword). Returns the top-k by blended score.
    """
    from rank_bm25 import BM25Okapi

    collection = get_collection()
    everything = collection.get(include=["documents", "metadatas"])
    docs = everything["documents"]
    metas = everything["metadatas"]

    # semantic similarity (1 - cosine distance) for all chunks
    model = get_model()
    q_emb = model.encode([query], normalize_embeddings=True)[0].tolist()
    sem = collection.query(query_embeddings=[q_emb], n_results=len(docs))
    sem_sim = {d: 1 - dist for d, dist in zip(sem["documents"][0], sem["distances"][0])}
    sem_scores = [sem_sim.get(d, 0.0) for d in docs]

    # BM25 keyword scores
    bm25 = BM25Okapi([d.lower().split() for d in docs])
    kw_scores = bm25.get_scores(query.lower().split())

    def norm(xs):
        lo, hi = min(xs), max(xs)
        return [(x - lo) / (hi - lo) if hi > lo else 0.0 for x in xs]

    sem_n, kw_n = norm(sem_scores), norm(list(kw_scores))
    blended = [alpha * s + (1 - alpha) * k_ for s, k_ in zip(sem_n, kw_n)]

    ranked = sorted(range(len(docs)), key=lambda i: blended[i], reverse=True)[:k]
    return [{
        "text": docs[i],
        "source": metas[i]["source"],
        "position": metas[i]["position"],
        "distance": round(1 - sem_scores[i], 4),  # report semantic distance for comparability
        "blended_score": round(blended[i], 4),
    } for i in ranked]


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "is the housing lottery actually random?"
    print(f"Query: {q}\n")
    for i, hit in enumerate(retrieve(q), 1):
        print(f"{i}. [{hit['source']}] distance={hit['distance']}")
        print(f"   {hit['text'][:160]}...\n")
