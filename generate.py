"""Stage 5 — Grounded generation.

Takes retrieved chunks and a question, and asks Claude (Anthropic API) to answer
USING ONLY those chunks. Grounding is enforced two ways:

  1. A strict system prompt that forbids outside knowledge and requires an explicit
     "I don't have enough information on that." when the context is insufficient.
  2. Source attribution is added PROGRAMMATICALLY from the retrieved chunks'
     metadata (not left to the model), so every answer is traceable to real sources.

Requires ANTHROPIC_API_KEY in .env (get a key from https://console.anthropic.com).
Uses claude-opus-4-8. Note: Opus 4.8 removes temperature/top_p/top_k (sending them
400s), so we steer purely with the prompt; we also tell it to return only the final
answer, since with thinking off Opus 4.8 can otherwise narrate its reasoning.
"""

import os

import anthropic
from dotenv import load_dotenv

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
- Keep answers concise and specific to what students actually said.
- Respond with only the final answer — no preamble, no description of your \
reasoning or process."""


def _format_context(chunks: list[dict]) -> str:
    blocks = []
    for i, c in enumerate(chunks, 1):
        blocks.append(f"[{i}] (source: {c['source']})\n{c['text']}")
    return "\n\n".join(blocks)


def generate_answer(query: str, chunks: list[dict]) -> str:
    """Return a grounded answer string for the given query + retrieved chunks."""
    if not chunks:
        return "I don't have enough information on that."

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    user_msg = (
        f"Context passages:\n\n{_format_context(chunks)}\n\n"
        f"Question: {query}\n\n"
        "Answer using only the passages above."
    )
    response = client.messages.create(
        model=LLM_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    # response.content is a list of content blocks; collect the text blocks.
    return "".join(b.text for b in response.content if b.type == "text").strip()
