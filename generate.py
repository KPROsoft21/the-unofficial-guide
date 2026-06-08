"""Stage 5 — Grounded generation.

Takes retrieved chunks and a question, and asks Groq's llama-3.3-70b-versatile to
answer USING ONLY those chunks. Grounding is enforced two ways:

  1. A strict system prompt that forbids outside knowledge and requires an explicit
     "I don't have enough information on that." when the context is insufficient.
  2. Source attribution is added PROGRAMMATICALLY from the retrieved chunks'
     metadata (not left to the LLM), so every answer is traceable to real sources.

Requires GROQ_API_KEY in .env (free key from https://console.groq.com).
"""

import os

from dotenv import load_dotenv
from groq import Groq

from config import LLM_MODEL

load_dotenv()

SYSTEM_PROMPT = """You are The Unofficial Guide, a question-answering assistant for \
student-generated campus knowledge. You answer ONLY using the numbered context \
passages provided in the user message.

Rules:
- Use ONLY information found in the context passages. Do NOT use any outside or \
prior knowledge, even if you are confident.
- If the context does not contain enough information to answer, reply EXACTLY: \
"I don't have enough information on that."
- Do not speculate, generalize, or fill gaps with what is "usually" true.
- Cite the passages you used inline by their bracketed source name, e.g. \
[reddit_dining_halls.txt].
- Keep answers concise and specific to what students actually said."""


def _format_context(chunks: list[dict]) -> str:
    blocks = []
    for i, c in enumerate(chunks, 1):
        blocks.append(f"[{i}] (source: {c['source']})\n{c['text']}")
    return "\n\n".join(blocks)


def generate_answer(query: str, chunks: list[dict]) -> str:
    """Return a grounded answer string for the given query + retrieved chunks."""
    if not chunks:
        return "I don't have enough information on that."

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    user_msg = (
        f"Context passages:\n\n{_format_context(chunks)}\n\n"
        f"Question: {query}\n\n"
        "Answer using only the passages above."
    )
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.1,  # low temperature keeps the model anchored to the context
    )
    return resp.choices[0].message.content.strip()
