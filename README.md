# 🎓 The Unofficial Guide

A Retrieval-Augmented Generation (RAG) system that makes **student-generated campus
knowledge** searchable and answerable. Ask a plain-language question — *"Is the
housing lottery actually random?"* — and get a grounded, **cited** answer drawn from
real student reviews, Reddit threads, and Discord advice.

Domain: **the unofficial student guide to UC Berkeley** (courses & professors,
dining, housing).

```
You ──▶ retrieve top-4 chunks (MiniLM + ChromaDB) ──▶ Groq LLM answers from
        those chunks only ──▶ answer + source citations 
```

---

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then paste your free Groq key (console.groq.com)
python embed_store.py         # build the vector index (one time)
python app.py                 # open http://localhost:7860
```
CLI alternative: `python query.py "is the housing lottery random?"`
Evaluation: `python evaluate.py`  (retrieval only: `python evaluate.py --retrieval-only`)

---

## Domain and document sources

The official channels (course catalog, housing handbook, dining site) describe
*policy*; they never tell you a dining hall is mobbed 12–1pm or which buildings have
mold. That lived knowledge is scattered across Reddit, Rate My Professors, and
Discord. This system consolidates it.

**13 source documents** spanning courses/professors, dining, and housing — see the
table in [`planning.md`](planning.md#documents). Source types: Rate My
Professors-style review pages, r/berkeley threads, and a CS Discord advice channel.

> **Note on the corpus:** Reddit and Rate My Professors block automated scraping
> (JS-rendered, 403 to bots — confirmed in this build), so the files in
> `documents/` are **realistic sample data** that mirror the structure of real
> threads, enabling a full end-to-end run today. The pipeline auto-loads any
> `.txt`/`.pdf` dropped into `documents/`, so swapping in real copy-pasted threads
> is a drop-in step — see [`documents/README_DOCUMENTS.md`](documents/README_DOCUMENTS.md).

## Chunking strategy and reasoning

**~600-char target, 900 hard cap, 100-char overlap (on force-split only),
paragraph/comment-aware.** Each document is a thread of short self-contained
opinions, so the natural retrieval unit is *one comment/review*. The chunker splits
on blank lines, merges small comments up to the target, and only sentence-splits a
block if it exceeds the cap. Full rationale (why not smaller / larger, failure
signatures) is in [`planning.md`](planning.md#chunking-strategy).

Result on the actual corpus: **39 chunks**, lengths min 128 / avg 395 / max 594
chars.

## Sample chunks (5 labeled, with source)

1. **`reddit_dining_halls.txt::chunk_1`** (594 chars)
   > [Reply, 188 upvotes] Cafe 3 is underrated. Smaller menu than Crossroads but the food quality is more consistent and the lines are shorter. If you live in Units 1/2/3 it's the obvious choice... [Reply, 95 upvotes] Foothill is the best food quality hands down, but it's a hike... [Reply, 60 upvotes] Clark Kerr is isolated so almost nobody complains about lines, but the food is the most boring.

2. **`reddit_housing_lottery.txt::chunk_1`** (random number block)
   > [Reply, 130 upvotes] Confirming: the lottery number is random, but your *preferences* and *contract type* (academic year vs. semester) filter what you're even eligible for. Continuing students and new freshmen are in different pools. So "random" is true but only within your pool.

3. **`rmp_cs61b_hilfinger.txt::chunk_0`**
   > --- Review 1 --- Quality: 3.5 / Difficulty: 4.5 ... His exams are NOT based on the lecture slides directly — they test whether you can apply data structures to problems you have never seen... The autograder for projects is brutal and gives almost no partial credit, so start early.

4. **`reddit_meal_plan_worth_it.txt::chunk_1`** (532 chars)
   > [Reply, 88 upvotes] Math: the unlimited plan is roughly the break-even point if you eat about 2 meals a day in the dining halls. If you routinely skip breakfast... a smaller block plan saves money. [Reply, 51 upvotes] If you have an apartment with a kitchen, cooking is dramatically cheaper — like half the cost.

5. **`reddit_safety_neighborhoods.txt::chunk_2`** (214 chars)
   > [Reply, 25 upvotes] Honestly most areas are fine if you use basic city common sense. The biggest practical risk is bike and package theft, not anything dramatic. Get renters insurance — it's cheap and covers theft.

Each chunk is self-contained: you can answer a question from it without reading the
rest of the thread.

## Embedding model + production tradeoffs

**Model used: `all-MiniLM-L6-v2`** (sentence-transformers, 384-dim, local, cosine
distance in ChromaDB). Chosen because it runs with no API key or rate limits and is
fast enough for interactive use.

**If I were choosing for production (cost aside):** I'd weigh **accuracy on
domain-specific text** (course codes, campus slang — a larger model like
`text-embedding-3-large` or Voyage retrieves jargon better), **context length**
(MiniLM truncates at 256 tokens — fine for comments, too short for a long housing
handbook PDF), **multilingual** coverage if the community posts in several
languages, and **latency vs. privacy** — local MiniLM keeps anonymous, sometimes
sensitive student posts off third-party APIs, which is a real reason to *not* reach
for a hosted model even when budget allows.

## Retrieval test results

Run with `python evaluate.py --retrieval-only`. Top hits below; distance = cosine
(lower is closer). Top results land **0.23–0.38** (strong); rank-4 hits drift toward
0.5+, which is why **top-k=4** is the cutoff.

**Query 1 — "Is the housing lottery actually random?"**
| rank | source | distance |
|---|---|---|
| 1 | `reddit_housing_lottery.txt` | **0.232** |
| 2 | `reddit_housing_lottery.txt` | 0.359 |
| 3 | `reddit_housing_lottery.txt` | 0.514 |
| 4 | `reddit_safety_neighborhoods.txt` | 0.757 |

*Why relevant:* the top-3 are all from the housing-lottery thread and directly state
the lottery number is random within your pool — exactly the asked fact. The rank-4
safety chunk is correctly far away (0.76), showing the metric separates signal from
noise.

**Query 2 — "Which CS class gives the most useful feedback?"**
| rank | source | distance |
|---|---|---|
| 1 | `reddit_cs_professor_feedback.txt` | **0.275** |
| 2 | `reddit_cs_professor_feedback.txt` | 0.369 |
| 3 | `reddit_cs_professor_feedback.txt` | 0.450 |
| 4 | `rmp_cs70_reviews.txt` | 0.476 |

*Why relevant:* ranks 1–3 are the exact thread debating CS70 vs 61B feedback; rank-4
pulls the CS70 review file that independently corroborates the "detailed written
proof feedback" point — useful cross-source support, not noise.

**Query 3 — "Does Professor Hilfinger base CS61B exams on the slides / autograder?"**
| rank | source | distance |
|---|---|---|
| 1–3 | `rmp_cs61b_hilfinger.txt` | 0.313 / 0.338 / 0.372 |
| 4 | `reddit_data8_vs_data100.txt` | 0.461 |

The top-3 are all Hilfinger reviews (correct source); rank-4 is a Data 100 chunk
about exams "rewarding reasoning" — topically adjacent but the wrong class, an early
sign of the cross-document conflation risk noted in planning.md.

## How grounded generation is enforced

Two mechanisms (see `generate.py`):

1. **Strict system prompt** — the model is told to use *only* the numbered context
   passages, to never use outside knowledge, and to reply **exactly** `"I don't have
   enough information on that."` when context is insufficient. Temperature is 0.1.
2. **Programmatic source attribution** — the `sources` list returned to the user is
   built in code from the retrieved chunks' metadata (`query.py`), *not* parsed from
   the LLM's prose. Attribution is therefore guaranteed even if the model forgets to
   cite inline (it's also prompted to cite inline as a bonus).

This is structural grounding: the answer can only draw on what retrieval put in
front of it, and the citations reflect what was actually retrieved.

## Example responses

> ⏳ **Pending GROQ_API_KEY.** Retrieval is fully verified above; generation needs a
> free Groq key (`console.groq.com`) in `.env`. After adding it, run
> `python evaluate.py` and these sections (example responses, full evaluation
> answers, failure-case write-up) will be filled with the real model output.
> *(See "What you need to do" at the bottom.)*

_To be filled:_ 2 grounded responses with visible source attribution + 1
out-of-scope query ("best gym on campus?") showing the refusal.

## Query interface

**Gradio web UI** (`app.py`, `http://localhost:7860`).
- **Input:** a single text box for a plain-language question; an optional "Hybrid
  search" checkbox (semantic + BM25).
- **Outputs:** *Answer* (grounded, with inline citations), *Retrieved from* (the
  source files the answer may draw on), and *Retrieved chunks* (the raw passages +
  distances, so a viewer can see exactly what grounded the answer).

_Sample interaction transcript:_ ⏳ pending GROQ_API_KEY (see above).

## Evaluation report

All 5 test questions and expected answers are in
[`planning.md`](planning.md#evaluation-plan). **Retrieval** for every question is
verified (above / via `evaluate.py --retrieval-only`):

| # | Question | Retrieval accuracy | Response accuracy |
|---|---|---|---|
| 1 | Hilfinger CS61B exams / autograder | ✅ accurate (top-3 correct source) | ⏳ pending key |
| 2 | Housing lottery random? | ✅ accurate (top-3 correct source) | ⏳ pending key |
| 3 | Most useful CS feedback | ✅ accurate | ⏳ pending key |
| 4 | Dining hall recommendation | ✅ accurate | ⏳ pending key |
| 5 | Co-op vs dorm cost *in dollars* | ⚠️ partial — correct source, but no $ figures exist | ⏳ pending key |

**Predicted failure case (Q5)** — to be confirmed with real output: the documents
say co-ops are "significantly cheaper" but contain **no dollar amounts**. Retrieval
correctly surfaces the co-op cost chunks (distances 0.23–0.27), so this is *not* a
retrieval failure — it's a **corpus-coverage limit**: the question asks for a
quantitative answer the source material only addresses qualitatively. A correctly
grounded system should give the relative comparison and decline to invent dollar
figures; an *incorrectly* grounded one would hallucinate a number. This is the value
of the test — it probes whether grounding holds when the honest answer is "the
documents don't say." *(Final judgment + any observed hallucination recorded after
the generation run.)*

## Spec reflection

⏳ Drafted after the full run. *(One way the spec helped: writing the chunking
section first forced the comment-aware decision before any code, which is why
retrieval precision is high. One divergence: I added an empty-chunk safety net and a
`CHUNK_MAX_CHARS` force-split that weren't in the original spec, after seeing real
block sizes — planning.md was updated to match.)*

## AI usage

Two concrete instances (more in [`planning.md`](planning.md#ai-tool-plan)):

1. **Chunker generation.** I gave Claude the Chunking Strategy section and asked for
   paragraph-aware merge-then-split logic. The first version split purely on fixed
   character count; I **overrode** it to split on blank-line comment boundaries
   first (and only sentence-split oversized blocks), because fixed-width splitting
   would slice opinions in half — the exact failure the strategy was designed to
   avoid.
2. **Grounding prompt.** I asked Claude to wire up generation; the initial system
   prompt *suggested* using the context. I **tightened** it to forbid outside
   knowledge outright and require a verbatim refusal string, and moved source
   attribution out of the LLM's hands into `query.py` so citations are
   programmatically guaranteed rather than model-dependent.

## Stretch feature: hybrid search

`retrieve.retrieve_hybrid()` blends normalized semantic similarity with BM25 keyword
scores (toggle in the UI). Rationale and a semantic-only comparison: see
[`planning.md`](planning.md#stretch-features).
