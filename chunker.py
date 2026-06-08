"""Stage 2 — Chunking.

Strategy (see planning.md): our documents are threads of short, self-contained
opinions (reviews / comments) separated by blank lines. The natural retrieval
unit is one comment, so we chunk paragraph-aware:

  1. Split on blank lines into blocks (one review/comment ~ one block).
  2. Greedily merge consecutive small blocks until we approach CHUNK_TARGET_CHARS,
     so a two-sentence review isn't stranded as a tiny, low-signal embedding.
  3. If a single block exceeds CHUNK_MAX_CHARS, split it on sentence boundaries
     with CHUNK_OVERLAP_CHARS of overlap so a fact spanning the split is still
     recoverable from at least one chunk.

Each chunk keeps its source filename and position for attribution.
"""

import re

from config import CHUNK_TARGET_CHARS, CHUNK_MAX_CHARS, CHUNK_OVERLAP_CHARS


def _split_large_block(block: str) -> list[str]:
    """Sentence-split an oversized block into <=MAX pieces with char overlap."""
    sentences = re.split(r"(?<=[.!?])\s+", block)
    pieces, current = [], ""
    for sent in sentences:
        if current and len(current) + len(sent) + 1 > CHUNK_MAX_CHARS:
            pieces.append(current.strip())
            # start next piece with the tail of the previous one (overlap)
            current = current[-CHUNK_OVERLAP_CHARS:] + " " + sent
        else:
            current = f"{current} {sent}".strip()
    if current.strip():
        pieces.append(current.strip())
    return pieces


def chunk_document(text: str) -> list[str]:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]

    chunks, buffer = [], ""
    for block in blocks:
        if len(block) > CHUNK_MAX_CHARS:
            # flush whatever we've accumulated, then split the big block on its own
            if buffer:
                chunks.append(buffer.strip())
                buffer = ""
            chunks.extend(_split_large_block(block))
            continue

        if buffer and len(buffer) + len(block) + 2 > CHUNK_TARGET_CHARS:
            chunks.append(buffer.strip())
            buffer = block
        else:
            buffer = f"{buffer}\n\n{block}".strip()

    if buffer.strip():
        chunks.append(buffer.strip())

    # final safety net: never emit an empty chunk
    return [c for c in chunks if c.strip()]


def chunk_corpus(docs: list[dict]) -> list[dict]:
    """Turn loaded docs into chunk records ready for embedding."""
    records = []
    for doc in docs:
        for i, chunk in enumerate(chunk_document(doc["text"])):
            records.append({
                "id": f"{doc['source']}::chunk_{i}",
                "text": chunk,
                "source": doc["source"],
                "position": i,
            })
    return records


if __name__ == "__main__":
    import random
    from ingest import load_documents

    records = chunk_corpus(load_documents())
    print(f"Total chunks: {len(records)}\n")
    lengths = [len(r["text"]) for r in records]
    print(f"Chunk char length — min {min(lengths)}, "
          f"avg {sum(lengths)//len(lengths)}, max {max(lengths)}\n")
    print("=== 5 random chunks ===")
    for r in random.sample(records, 5):
        print(f"\n[{r['id']}] ({len(r['text'])} chars)\n{r['text']}")
