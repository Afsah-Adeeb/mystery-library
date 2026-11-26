"""
Check the labelled test set against the books themselves. No API calls.

WHY THIS EXISTS
-----------------
Every evaluation number is only as good as its labels, and labels rot.
The research-paper version of this project learned that the hard way:
when the corpus grew from 9 to 30 papers, two "unanswerable" trap
questions quietly became answerable, because the new papers contained the
answers. The system was right to answer them; the labels were wrong, and
nothing flagged it until the refusal rate looked odd.

So the two kinds of label are checked against the actual text:

  answerable questions  -- every required fact (any accepted spelling)
                           must appear in at least one of the books marked
                           correct. A fact the book never states is a fact
                           no answer can be fairly scored on.

  unanswerable questions-- every giveaway phrase listed in `must_not_appear`
                           must appear in NO book. If one turns up, the trap
                           may have stopped being a trap.

Run it after adding books, and after editing eval/test_questions.json:

    cd src
    ../.venv/Scripts/python.exe eval/verify_questions.py

It cannot prove a trap is unanswerable -- absence of a phrase is not
absence of an answer -- but it catches the cheap, common way they break.
"""

import re

# This script lives in a subfolder but imports the pipeline modules that sit in
# src/ (config, ingest). Running a script puts its OWN folder on the import
# path, not its parent, so the parent is added explicitly.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import eval_core as ec
from ingest import book_paths, read_book_text


def load_book_texts():
    """{file name: lower-cased text with whitespace collapsed}.

    Collapsing whitespace matters: the files are hard-wrapped, so a two-word
    fact can be split across a line break in the raw text.
    """
    return {p.name: " ".join(read_book_text(p).lower().split()) for p in book_paths()}


def check(questions, texts):
    """Return a list of human-readable problems. Empty means the set is clean."""
    problems = []
    everything = " ".join(texts.values())

    for q in questions:
        if q.get("answerable", True):
            missing = [b for b in q.get("correct_books", []) if b not in texts]
            if missing:
                problems.append(f"{q['id']}: correct book not in corpus: {missing}")
                continue
            pool = " ".join(texts[b] for b in q.get("correct_books", []))
            for fact in q.get("must_mention", []):
                if not any(spelling.lower() in pool for spelling in fact):
                    problems.append(f"{q['id']}: required fact not found in its book(s): {fact}")
        else:
            for phrase in q.get("must_not_appear", []):
                if re.search(r"\b" + re.escape(phrase.lower()) + r"\b", everything):
                    problems.append(f"{q['id']}: trap may be stale -- '{phrase}' now appears in the corpus")
    return problems


def main():
    questions = ec.load_questions()
    texts = load_book_texts()
    problems = check(questions, texts)

    answerable = sum(1 for q in questions if q.get("answerable", True))
    print(f"Checked {len(questions)} questions ({answerable} answerable, "
          f"{len(questions) - answerable} traps) against {len(texts)} books.")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        raise SystemExit(1)
    print("All required facts found in their books; no trap giveaways found anywhere.")


if __name__ == "__main__":
    main()
