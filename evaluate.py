"""Evaluation harness.

Runs the system on the 5 test questions from planning.md (plus one out-of-scope
question to verify refusal behavior), printing for each: the expected answer, the
retrieved chunks with distances, and the system's actual response. The human
accuracy judgments (accurate / partially accurate / inaccurate) are recorded in
README.md based on these runs.

    python evaluate.py            # full run (needs ANTHROPIC_API_KEY)
    python evaluate.py --retrieval-only   # just retrieval, no LLM
"""

import sys

from query import ask
from retrieve import retrieve

EVAL = [
    {
        "q": "Does Professor Hilfinger base CS61B exams on the lecture slides, and what do students say about the autograder?",
        "expected": "Exams are NOT based directly on lecture slides; they test applying data structures to unseen problems / reasoning from first principles. The autograder is brutal, gives little/no partial credit and sparse feedback, so start projects early.",
    },
    {
        "q": "Is the housing lottery actually random?",
        "expected": "Yes, the lottery NUMBER is random, but only within your on-time pool. Applying earlier does not improve your number; missing the priority deadline drops you to a worse pool. Accommodations and themed-program housing are assigned outside the lottery.",
    },
    {
        "q": "Which CS class gives the most useful feedback?",
        "expected": "CS70 for proofs (graders leave detailed, paragraph-long written comments). For code, CS61B's optional TA code-review sessions. Large classes like CS61A give little individual feedback (just the autograder).",
    },
    {
        "q": "Which dining hall do students recommend and why?",
        "expected": "Foothill has the best food quality (a walk). Crossroads is the all-rounder: most variety, best/latest hours, but very crowded 12-1pm. Cafe 3 is consistent with shorter lines (good for Units 1/2/3). Clark Kerr is convenient but boring.",
    },
    {
        "q": "How much cheaper is a co-op than the dorms per month, in dollars?",
        "expected": "(Hard case) Students say co-ops are significantly cheaper than dorms because you do ~5 hrs/week of labor, but the documents give NO dollar figures. A grounded system should give the relative comparison and decline to state exact dollars.",
    },
]

OUT_OF_SCOPE = "What is the best gym on campus and what are its hours?"


def main():
    retrieval_only = "--retrieval-only" in sys.argv

    for i, item in enumerate(EVAL, 1):
        print("=" * 80)
        print(f"Q{i}: {item['q']}")
        print(f"\nEXPECTED: {item['expected']}\n")

        hits = retrieve(item["q"])
        print("RETRIEVED CHUNKS:")
        for j, h in enumerate(hits, 1):
            print(f"  {j}. [{h['source']}] distance={h['distance']}")
            print(f"     {h['text'][:140].replace(chr(10), ' ')}...")

        if not retrieval_only:
            result = ask(item["q"])
            print(f"\nSYSTEM ANSWER:\n{result['answer']}")
            print(f"\nSOURCES: {', '.join(result['sources'])}")
        print()

    print("=" * 80)
    print(f"OUT-OF-SCOPE CHECK: {OUT_OF_SCOPE}")
    hits = retrieve(OUT_OF_SCOPE)
    print("RETRIEVED:", ", ".join(f"{h['source']}({h['distance']})" for h in hits))
    if not retrieval_only:
        print("SYSTEM ANSWER:", ask(OUT_OF_SCOPE)["answer"])


if __name__ == "__main__":
    main()
