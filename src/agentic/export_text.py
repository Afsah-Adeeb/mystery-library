"""
Export each book to a grep-friendly text file for the agentic retriever.

WHY THIS STAGE EXISTS
-----------------------
The semantic pipeline never needs the books as text on disk in any special
shape -- ingest.py reads, chunks, and embeds them in one pass, and after
that everything lives in the FAISS index. The agentic retriever
(agent_rag.py) works the opposite way: it has no index at all, and instead
searches the source text directly, the way a person would with Ctrl+F.

So this stage converts data/books/*.txt -> data/books_text/*.txt.

KEEPING THE COMPARISON FAIR
-----------------------------
This deliberately reuses ingest.py's reading, licence stripping and chapter
splitting rather than doing its own. If the agentic side searched raw
Gutenberg files (licence header and all) while the semantic side searched
cleaned text, any difference in the benchmark could just be preprocessing
quality rather than the retrieval strategy -- which is the thing we
actually want to measure.

Chapter markers are written into the text ("[chapter: Chapter 6:
Baskerville Hall]") for the same reason: the semantic pipeline cites a
chapter from chunk metadata, so the agentic side needs that information
too, or it would look worse at citation purely for lack of the data rather
than for lack of ability.

ONE SENTENCE PER LINE, AND WHY IT MATTERS
-------------------------------------------
Gutenberg hard-wraps every line at ~70 characters. Written out verbatim, a
phrase that spans a line break simply cannot be found by a line-based
search -- "speckled\nband" does not match "speckled band". The research-
paper version of this project measured exactly that failure: a paper was
invisible to a search for the term it coined, because the words landed on
different lines.

That is a line-wrapping artifact, not a real property of agentic
retrieval, and benchmarking against it would be a strawman. ingest.py
already re-joins wrapped lines into flowing paragraphs before chunking, so
this applies the same join, then re-splits the flowing text one sentence
per line. Both arms see identical *characters*; only where the newlines
fall differs, and newline placement matters to nothing except grep.

Sentences rather than paragraphs because a paragraph can run to thousands
of characters (a confession, a letter), which makes grep output unreadable
and blows the output budget on a single match. Sentences give short lines:
phrases still match, results stay readable, and line numbers mean something
when paging through a book with read_book.

    cd src
    ../.venv/Scripts/python.exe agentic/export_text.py
"""

import re

# This script lives in a subfolder but imports the pipeline modules that sit in
# src/ (config, retrieve, generate, telemetry). Running a script puts its OWN
# folder on the import path, not its parent, so the parent is added explicitly.
# Siblings inside this folder import normally.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import config
from ingest import book_paths, book_title, read_book_text, sections_to_paragraphs, split_chapters

# Split after sentence-ending punctuation (optionally followed by a closing
# quote) when the next thing starts a new sentence: a capital or an opening
# quote. Requiring the capital keeps "Mr. Holmes" and "Dr. Watson" mostly
# intact -- not perfectly, and it does not need to be: an occasional extra
# line break costs nothing here.
_SENTENCE_BOUNDARY = re.compile(
    r"(?<=[.!?])\s+(?=[A-Z“‘\"'(])"
    r"|(?<=[.!?][”’\"'])\s+(?=[A-Z“‘\"'(])"
)


def split_sentences(paragraph):
    """Break one flowing paragraph into sentence-sized lines."""
    return [s.strip() for s in _SENTENCE_BOUNDARY.split(paragraph) if s.strip()]


def book_to_text(path):
    """One book -> chapter-marked text, one sentence per line.

    Reuses ingest.py's reading and chapter splitting, so the agentic
    retriever searches the same text the semantic pipeline embedded.
    """
    sections = split_chapters(read_book_text(path), book=book_title(path.name))
    lines = []
    current = None
    for chapter, para in sections_to_paragraphs(sections):
        if chapter != current:
            lines.append(f"\n[chapter: {chapter}]")
            current = chapter
        lines.extend(split_sentences(para))
    return "\n".join(lines).strip() + "\n"


def main():
    paths = book_paths()
    if not paths:
        print(f"No books found in {config.BOOKS_DIR}. Run download_books.py first.")
        return

    config.BOOKS_TEXT_DIR.mkdir(parents=True, exist_ok=True)

    total_chars = 0
    for path in paths:
        text = book_to_text(path)
        out_path = config.BOOKS_TEXT_DIR / path.name
        out_path.write_text(text, encoding="utf-8")
        total_chars += len(text)
        print(f"  {len(text):>9,} chars  {out_path.name}")

    print(f"\nWrote {len(paths)} text files ({total_chars:,} chars total) "
          f"to {config.BOOKS_TEXT_DIR}")


if __name__ == "__main__":
    main()
