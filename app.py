"""Gradio query interface for The Unofficial Guide.

Run:  python app.py   ->   http://localhost:7860

Input:  a plain-language question.
Output: a grounded answer (with inline source citations) + the list of source
documents it was allowed to draw from + the raw retrieved chunks with distances,
so a viewer can see exactly what the answer was grounded in.
"""

import gradio as gr

from query import ask


def handle_query(question, use_hybrid):
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", "", ""

    result = ask(question, hybrid=use_hybrid)
    sources = "\n".join(f"• {s}" for s in result["sources"])
    retrieved = "\n\n".join(
        f"[{c['source']}] (distance {c['distance']})\n{c['text']}"
        for c in result["chunks"]
    )
    return result["answer"], sources, retrieved


with gr.Blocks(title="The Unofficial Guide") as demo:
    gr.Markdown(
        "# 🎓 The Unofficial Guide\n"
        "Ask about UC Berkeley courses, professors, dining, and housing — answered "
        "from real student-generated knowledge, with sources."
    )
    with gr.Row():
        inp = gr.Textbox(
            label="Your question",
            placeholder="e.g. Is the housing lottery actually random?",
            scale=4,
        )
        hybrid = gr.Checkbox(label="Hybrid search (semantic + keyword)", value=False)
    btn = gr.Button("Ask", variant="primary")

    answer = gr.Textbox(label="Answer", lines=6)
    sources = gr.Textbox(label="Retrieved from (sources)", lines=3)
    retrieved = gr.Textbox(label="Retrieved chunks (what the answer is grounded in)", lines=12)

    gr.Examples(
        examples=[
            ["Is the housing lottery actually random?"],
            ["Which CS professor gives the most useful feedback?"],
            ["Which dining hall do students recommend and why?"],
            ["What should I check for before signing a southside apartment lease?"],
        ],
        inputs=inp,
    )

    btn.click(handle_query, inputs=[inp, hybrid], outputs=[answer, sources, retrieved])
    inp.submit(handle_query, inputs=[inp, hybrid], outputs=[answer, sources, retrieved])


if __name__ == "__main__":
    demo.launch()
