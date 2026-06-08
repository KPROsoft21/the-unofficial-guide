# The Unofficial Guide — Planning / Spec

## Domain

**Unofficial student guide to UC Berkeley** — the practical, lived knowledge
students trade about *courses & professors, dining, and housing*. Things like
which professor's exams actually reward understanding, whether the housing lottery
is really random, which dining hall is worth the walk, and what to inspect before
signing a southside lease.

This knowledge is valuable and hard to find through official channels because the
university's own materials (course catalog, housing handbook, dining website)
describe *policy and logistics*, not *experience*. They won't tell you that
Crossroads is mobbed 12–1pm, that a professor's autograder gives no partial
credit, or which buildings have chronic mold. That information lives in Reddit
threads, Rate My Professors reviews, and Discord servers — scattered, anonymous,
and unsearchable across sources.

## Documents

13 documents, chosen for *coverage across subtopics* rather than redundancy.
(These are realistic **sample** files because Reddit/RMP block scraping — see
`documents/README_DOCUMENTS.md` for how to swap in real collected threads.)

| Source type | File | Subtopic |
|---|---|---|
| RMP-style reviews | `rmp_cs61b_hilfinger.txt` | CS61B exams / autograder / curve |
| RMP-style reviews | `rmp_cs70_reviews.txt` | CS70 difficulty / proof feedback |
| Reddit thread | `reddit_dining_halls.txt` | Dining hall comparison + wait times |
| Reddit thread | `reddit_housing_lottery.txt` | Is the housing lottery random |
| Reddit thread | `reddit_offcampus_southside.txt` | Apartment mold / deposits / landlords |
| Reddit thread | `reddit_cs_professor_feedback.txt` | Which CS class gives useful feedback |
| Reddit thread | `reddit_data8_vs_data100.txt` | Data 8 → Data 100 jump / prereqs |
| Discord channel | `discord_finals_tips.txt` | Finals prep, study spots, curves |
| Reddit thread | `reddit_meal_plan_worth_it.txt` | Meal plan vs cooking economics |
| Reddit thread | `reddit_enrollment_calcentral.txt` | Getting into full classes / waitlists |
| Reddit thread | `reddit_safety_neighborhoods.txt` | Neighborhood safety northside/southside |
| Reddit thread | `reddit_math1a_vs_16a.txt` | Math 1A vs 16A course choice |
| Reddit thread | `reddit_coops_vs_dorms.txt` | Co-op vs dorm vs apartment cost/vibe |

## Chunking Strategy

**Chunk size: ~600 characters target, 900 hard cap. Overlap: 100 characters (only
applied when a single block must be force-split).**

*Why these numbers fit these documents:* Every document is a **thread of short,
self-contained opinions** — one Reddit comment or one RMP review is one complete
thought ("Crossroads has the best hours but is crowded 12–1"). The natural
retrieval unit is therefore *the comment*, not a fixed character window that would
slice mid-opinion. So the chunker is **paragraph/comment-aware**:

1. Split on blank lines into blocks (≈ one comment/review per block).
2. Greedily merge consecutive *small* blocks up to the ~600-char target, so a
   two-sentence review isn't stranded as a tiny, low-signal embedding.
3. Only if one block exceeds 900 chars, sentence-split it with 100-char overlap so
   a fact spanning the split is still recoverable from at least one chunk.

- **Why not smaller (e.g. 200 chars)?** A 200-char chunk often captures only half
  an opinion ("Foothill is the best food quality hands down") and loses the
  qualifier ("...but it's a hike"). Queries about tradeoffs would retrieve a
  one-sided fragment.
- **Why not larger (e.g. 1500 chars)?** Merging four unrelated comments into one
  embedding dilutes the vector — a query about *wait times* would match a chunk
  that's mostly about *food quality*, lowering precision.
- **How I'd know it's wrong:** too small → top hits are sentence fragments with
  high distance; too large → the right document is retrieved but the specific
  sub-point is buried and the LLM answers vaguely.

Result on the actual corpus: **39 chunks**, min 128 / avg 395 / max 594 chars.
(39 is below the brief's "≥50" rule of thumb, but that heuristic assumes 10 *long*
documents — our sources are short threads, so 39 self-contained chunks is the
right granularity, confirmed by the chunk inspection.)

## Retrieval Approach

- **Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers` — 384-dim,
  runs locally, no API key, no rate limits. Embeddings are normalized and the
  Chroma collection uses **cosine** distance.
- **top-k = 4.** Each chunk is one opinion; 3–4 chunks give the LLM enough
  cross-commenter consensus to synthesize ("most students say X, though one notes
  Y") without dragging in loosely-related material. Too few (k=1–2) risks missing
  the relevant opinion entirely; too many (k=8+) pulls in off-topic chunks that can
  steer the answer (visible in our eval: rank-4 hits already creep toward 0.5+
  distance).
- **Why semantic search beats keyword here:** a student asking "is the housing
  lottery rigged?" should match a comment that says "the number is *random*" —
  zero shared keywords, but near-identical meaning. MiniLM captures that.
- **If cost weren't a constraint (production):** I'd weigh (a) a larger/better
  model like OpenAI `text-embedding-3-large` or Voyage for higher accuracy on
  domain jargon (course codes, slang); (b) **context length** — MiniLM truncates
  at 256 tokens, fine for comments but a long-form housing handbook PDF would need
  a longer-context embedder; (c) **multilingual** support if the campus community
  posts in multiple languages; (d) **latency & privacy** — local MiniLM is fast and
  keeps anonymous student posts off third-party APIs, a real consideration for
  potentially sensitive content. Tradeoff: API models cost per token and add
  network latency but lift retrieval accuracy.

## Evaluation Plan

| # | Test question | Expected (verifiable) answer |
|---|---|---|
| 1 | Does Professor Hilfinger base CS61B exams on the lecture slides, and what do students say about the autograder? | Exams are **not** based directly on slides; they test applying data structures to unseen problems. Autograder is brutal, little/no partial credit, sparse feedback — start early. |
| 2 | Is the housing lottery actually random? | The lottery **number** is random, but only within your on-time pool. Applying earlier doesn't help; missing the priority deadline drops you to a worse pool; accommodations/themed housing are assigned outside the lottery. |
| 3 | Which CS class gives the most useful feedback? | **CS70** for proofs (detailed written grader comments); **CS61B** optional TA code-review for code. Big classes (CS61A) give little individual feedback. |
| 4 | Which dining hall do students recommend and why? | **Foothill** best food (a walk); **Crossroads** all-rounder, best hours, crowded 12–1; **Cafe 3** consistent + short lines; **Clark Kerr** convenient but boring. |
| 5 | *(hard)* How much cheaper is a co-op than the dorms per month, in dollars? | Co-ops are "significantly cheaper" (you do ~5 hrs/wk labor), but the documents give **no dollar figures** — a grounded system should give the relative comparison and decline to invent numbers. |

Plus an **out-of-scope** check ("best gym on campus?") to confirm the system
refuses rather than hallucinates.

## Anticipated Challenges

1. **Cross-document conflation.** "Useful feedback" and "the curve" appear in
   multiple class docs; semantic search may pull a CS70 chunk for a CS61B question
   and the LLM could attribute one class's feature to another. *(Risk: wrong-source
   attribution.)*
2. **Quantitative questions over qualitative sources.** Our docs say co-ops are
   "cheaper" but give no dollars; a "how much in dollars" question can tempt the LLM
   to fabricate a figure. *(Risk: hallucinated specifics — Q5 tests exactly this.)*
3. **Noisy formatting.** Upvote tags (`[Reply, 88 upvotes]`) and review headers
   are kept as light structure but could leak into answers; the prompt must focus
   on substance.
4. **Out-of-domain queries.** Questions the corpus never covers (gyms, parking
   permits) must trigger refusal, not a plausible-sounding guess.

## AI Tool Plan

Specific components I delegated to an AI tool (Claude), with inputs/expected output:

- **Ingestion + cleaning (`ingest.py`):** input = the Documents section + a
  description of the `SOURCE:`/`COLLECTED:` header format; expected = a loader that
  strips that header, decodes HTML entities, and skips empty/scanned files.
- **Chunker (`chunker.py`):** input = the Chunking Strategy section above;
  expected = paragraph-aware merge-then-split logic honoring the 600/900/100
  numbers, with a `chunk_corpus()` that attaches source + position metadata.
- **Embedding + store (`embed_store.py`):** input = Retrieval Approach section +
  architecture diagram; expected = MiniLM encode + persistent Chroma collection
  with cosine space and source metadata.
- **Grounded generation (`generate.py`):** input = the grounding requirement
  (context-only, explicit refusal string) + desired output format; expected = a
  strict system prompt + programmatic source attribution.
- **Gradio UI (`app.py`):** input = the skeleton from the brief + "show retrieved
  chunks so grounding is visible"; expected = a runnable 3-output interface.

I review each output against the spec, fix anything that drifts (e.g. tightening
the grounding prompt, adding the empty-chunk safety net), and make sure I can
explain every line.

## Architecture

```
┌──────────────────┐   ┌──────────────┐   ┌────────────────────────┐
│ 1. INGESTION     │   │ 2. CHUNKING  │   │ 3. EMBED + VECTOR STORE │
│ documents/*.txt  │──▶│ paragraph-   │──▶│ all-MiniLM-L6-v2        │
│ .pdf (pdfplumber)│   │ aware split  │   │  → ChromaDB (cosine,    │
│ clean boilerplate│   │ ~600c / 100c │   │     source metadata)    │
│ (ingest.py)      │   │ (chunker.py) │   │ (embed_store.py)        │
└──────────────────┘   └──────────────┘   └───────────┬─────────────┘
                                                       │
                  ┌────────────────────────────────────┘
                  ▼
        ┌────────────────────┐      ┌──────────────────────────────┐
        │ 4. RETRIEVAL       │      │ 5. GENERATION                │
        │ embed query, top-k=4│─────▶│ Groq llama-3.3-70b-versatile │
        │ cosine search      │      │ grounded prompt (context     │
        │ (+ optional hybrid │      │ only) + programmatic source  │
        │  BM25) retrieve.py │      │ attribution (generate.py)    │
        └────────────────────┘      └──────────────┬───────────────┘
                                                    ▼
                                       Gradio UI (app.py) / CLI (query.py)
                                       answer + sources + retrieved chunks
```

## Stretch Features (update before starting each)

- **Hybrid search (BM25 + semantic):** implemented in `retrieve.retrieve_hybrid()`
  and toggleable in the Gradio UI. Rationale: queries hinging on a rare exact token
  (a course number like "16A", a professor name) can be blurred by pure semantic
  similarity; BM25 reweights exact-term overlap. Comparison vs semantic-only to be
  recorded in README.
