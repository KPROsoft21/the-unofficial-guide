"""Central configuration for The Unofficial Guide RAG system.

Keeping every tunable knob in one place means the pipeline stages stay in sync
(ingest, embed, retrieve, generate all import from here) and the values in this
file are exactly the ones documented in planning.md / README.md.
"""

from pathlib import Path

# --- Paths ---
ROOT = Path(__file__).parent
DOCS_DIR = ROOT / "documents"
CHROMA_DIR = ROOT / "chroma_store"

# --- Chunking (see planning.md "Chunking Strategy") ---
# Documents are review/comment threads: many short, self-contained opinions.
# We chunk paragraph-/comment-aware, targeting ~600 chars with ~100 char overlap.
CHUNK_TARGET_CHARS = 600   # ~150 tokens, well under MiniLM's 256-token limit
CHUNK_MAX_CHARS = 900      # hard cap before we force a split
CHUNK_OVERLAP_CHARS = 100  # carried between forced splits to preserve context

# --- Embedding / vector store ---
EMBED_MODEL = "all-MiniLM-L6-v2"   # local, no API key, 384-dim
COLLECTION_NAME = "unofficial_guide"

# --- Retrieval ---
TOP_K = 4                  # chunks returned per query

# --- Generation (Anthropic Claude) ---
LLM_MODEL = "claude-opus-4-8"
