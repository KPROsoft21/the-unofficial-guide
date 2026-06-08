"""End-to-end query entry point: retrieve -> generate -> attribute.

This is the single function the UI, the evaluator, and the CLI all call, so the
behavior demoed in the video is exactly the behavior under test.

    python query.py "which dining hall do students recommend?"
"""

from config import TOP_K
from retrieve import retrieve, retrieve_hybrid
from generate import generate_answer


def ask(question: str, k: int = TOP_K, hybrid: bool = False) -> dict:
    """Answer a question. Returns {answer, sources, chunks}.

    `sources` is the de-duplicated list of source files the answer can draw from
    (programmatic attribution). `chunks` is the full retrieval result for
    transparency / evaluation.
    """
    chunks = retrieve_hybrid(question, k=k) if hybrid else retrieve(question, k=k)
    answer = generate_answer(question, chunks)

    # programmatic source attribution — guaranteed, not left to the LLM
    sources = []
    for c in chunks:
        if c["source"] not in sources:
            sources.append(c["source"])

    return {"answer": answer, "sources": sources, "chunks": chunks}


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "which dining hall do students recommend and why?"
    result = ask(q)
    print(f"Q: {q}\n")
    print(f"A: {result['answer']}\n")
    print("Retrieved from:")
    for s in result["sources"]:
        print(f"  • {s}")
