"""
Measure where to set config.LOW_CONFIDENCE_THRESHOLD.

The monitoring layer (telemetry.py) flags an answer as "hallucination risk"
when retrieval scored badly but the model answered confidently anyway. That
needs a number for "scored badly" -- and picking one by vibe is exactly the
kind of unexplainable magic constant worth avoiding.

So we measure it. Run a batch of questions the corpus *should* answer and a
batch it clearly should not, then look at the top-1 similarity each produces.
If the two groups separate cleanly, the threshold belongs in the gap between
them; the midpoint maximizes the margin on both sides.

This is corpus- and model-specific: change the books or the embedding model
and the distributions shift, so re-run this and update config.py.

    cd src
    ../.venv/Scripts/python.exe measure_threshold.py
"""

import statistics

# This script lives in a subfolder but imports the pipeline modules that sit in
# src/ (config, retrieve, generate, telemetry). Running a script puts its OWN
# folder on the import path, not its parent, so the parent is added explicitly.
# Siblings inside this folder import normally.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import config
from retrieve import retrieve

# Questions the corpus genuinely covers -- spread across different books, so
# the minimum is not just "how well does it know Sherlock Holmes".
ON_TOPIC = [
    "What killed Julia Stoner in The Speckled Band?",
    "Who is Irene Adler?",
    "What is the legend of the hound that haunts the Baskerville family?",
    "How did Father Brown leave a trail for the police in The Blue Cross?",
    "Who took the Moonstone from Rachel Verinder's cabinet?",
    "Who committed the murders in the Rue Morgue?",
    "What happened between Holmes and Moriarty at the Reichenbach Falls?",
    "How does Raffles try to steal the pearl in The Gift of the Emperor?",
    "What are the thirty-nine steps?",
    "How did the Thinking Machine escape from Cell 13?",
]

# Questions the corpus clearly does not cover. Deliberately spread across
# unrelated domains so a single odd match can't skew the maximum.
OFF_TOPIC = [
    "What houses exist at Hogwarts?",
    "How do I bake sourdough bread?",
    "What is the capital of Brazil?",
    "Explain quantum entanglement to a child.",
    "Who won the 2018 FIFA World Cup final?",
    "What are the side effects of ibuprofen?",
    "How do I file my income tax return?",
    "Write a poem about the ocean.",
]


def probe(label, questions):
    """Retrieve for each question and report the top-1 similarity spread."""
    print(f"\n=== {label} ===")
    top_scores = []
    for question in questions:
        chunks = retrieve(question, top_k=config.DEFAULT_TOP_K)
        top = chunks[0]["score"] if chunks else 0.0
        top_scores.append(top)
        print(f"  top1={top:.3f}  {question}")
    print(f"  --> min={min(top_scores):.3f}  "
          f"median={statistics.median(top_scores):.3f}  max={max(top_scores):.3f}")
    return top_scores


def best_cut(on, off):
    """The threshold that misclassifies the fewest questions: (threshold, errors).

    Tries the midpoint between every pair of neighbouring scores. An on-topic
    question below the cut, or an off-topic one at or above it, is an error.
    Ties go to the LOWER cut: the flag asks a human to review an answer, and
    a dashboard that keeps flagging real readers' real questions stops being
    read. Missing an off-topic poem request is the cheaper mistake.
    """
    scores = sorted(on + off)
    candidates = [(a + b) / 2 for a, b in zip(scores, scores[1:])]
    best = None
    for cut in candidates:
        errors = sum(1 for s in on if s < cut) + sum(1 for s in off if s >= cut)
        if best is None or errors < best[1]:
            best = (cut, errors)
    return best


def main():
    on = probe("ON-TOPIC (corpus should answer these)", ON_TOPIC)
    off = probe("OFF-TOPIC (corpus should not answer these)", OFF_TOPIC)

    lowest_on, highest_off = min(on), max(off)
    print("\n=== SEPARATION ===")
    print(f"  lowest on-topic top-1  : {lowest_on:.3f}")
    print(f"  highest off-topic top-1: {highest_off:.3f}")

    if lowest_on <= highest_off:
        print("\n  The two groups OVERLAP -- no threshold separates them cleanly.")
        print("  A single similarity cutoff will misclassify some questions here.")
        # Still pick a number, but an honest one: the cut that gets the fewest
        # of these questions wrong, with the error count printed next to it.
        # On the research papers the groups never overlapped. On novels they
        # do -- ordinary words ("ocean", "houses") appear in literature, so an
        # off-topic question can find a passage that sounds close.
        threshold, errors = best_cut(on, off)
        print(f"\n  Fewest mistakes at LOW_CONFIDENCE_THRESHOLD = {threshold:.2f} "
              f"({errors} of {len(on) + len(off)} questions on the wrong side)")
        print(f"  (config.py currently has {config.LOW_CONFIDENCE_THRESHOLD})")
        print("  Treat the hallucination flag built on it as advisory only.")
        return

    midpoint = (lowest_on + highest_off) / 2
    print(f"  gap                    : {lowest_on - highest_off:+.3f} (clean separation)")
    print(f"\n  Suggested LOW_CONFIDENCE_THRESHOLD = {midpoint:.2f}")
    print(f"  (config.py currently has {config.LOW_CONFIDENCE_THRESHOLD})")


if __name__ == "__main__":
    main()
