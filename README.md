# The Mystery Library

**Live: <https://mystery-library.web.app>**

**The site** is a reader in the style of the Books app in EdgeChat: open any of the 23 books, read
it whole, chapter by chapter, and ask about it in a side chat. Answers come only from the book you
are reading, appear only in the chat (the page is never marked up), and when the book doesn't say,
the reply is simply "Not in this book." Read Aloud speaks from wherever you are and lights each word.
The Evaluation page shows every measured number with its 95% interval. The original minimal
interface is still at [/classic](https://mystery-library.web.app/classic).

The EdgeChat Otter is used with the permission of Biostate AI, given for this public demo. This is an
independent student project, not an official EdgeChat product.

Ask questions across **23 classic mystery books** — the complete Sherlock Holmes, Father
Brown, Poe's Dupin stories, *The Moonstone*, *The Mystery of the Yellow Room* and more —
and get answers grounded in the text, with the book and chapter they came from.

It is a **Corrective RAG** system: every retrieved passage is graded by a model *before*
it reaches the answer step. The system answers from what survives, searches deeper when
too little does, or declines instead of guessing. Every design choice is measured against
a hand-labelled test set, with 95% confidence intervals and honest baselines.

> This project began as a RAG system over research papers on sports-video event spotting.
> The approach is unchanged; the corpus is now books. What had to change — and what the
> change revealed — is described under [From papers to books](#from-papers-to-books).

---

## Quick start

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env          # then put your free Gemini key in .env
cd src
..\.venv\Scripts\python.exe download_books.py   # 23 books from Project Gutenberg (skips ones you have)
..\.venv\Scripts\python.exe ingest.py           # books -> 13,430 chapter-labelled chunks
..\.venv\Scripts\python.exe embed_store.py      # chunks -> FAISS index (~12 min on a laptop CPU)
..\.venv\Scripts\python.exe -m uvicorn api:app --port 8010   # open http://localhost:8010
```

The index is committed, so for a quick look you can skip straight to the last line.
A free Gemini key comes from <https://aistudio.google.com/apikey>.

---

## The shelf

All public domain, all from [Project Gutenberg](https://www.gutenberg.org), fetched by
`src/download_books.py` so the corpus can be rebuilt byte for byte.

| Books | Author |
|---|---|
| *A Study in Scarlet*, *The Sign of the Four*, *The Adventures*, *The Memoirs*, *The Hound of the Baskervilles*, *The Return*, *The Valley of Fear*, *His Last Bow*, *The Case-Book* | Arthur Conan Doyle |
| *The Innocence of Father Brown*, *The Wisdom of Father Brown* | G. K. Chesterton |
| *The Works of Edgar Allan Poe*, Volumes 1–2 (Dupin, *The Gold-Bug*, *The Tell-Tale Heart*) | Edgar Allan Poe |
| *The Moonstone* | Wilkie Collins |
| *The Mystery of Edwin Drood* (unfinished) | Charles Dickens |
| *The Leavenworth Case* | Anna Katharine Green |
| *The Big Bow Mystery* | Israel Zangwill |
| *The Amateur Cracksman* (Raffles) | E. W. Hornung |
| *The Mystery of the Yellow Room* | Gaston Leroux |
| *The Extraordinary Adventures of Arsène Lupin* | Maurice Leblanc |
| *The Thinking Machine* | Jacques Futrelle |
| *The Old Man in the Corner* | Baroness Orczy |
| *The Thirty-Nine Steps* | John Buchan |

**Why mysteries:** a detective story is full of small, checkable facts — who, where, which
weapon, which clue. "What killed Julia Stoner?" has one right answer that either is or is
not in the retrieved text, which is exactly what an evaluation needs.

**Why no Agatha Christie:** her early novels are public domain in the US, but she died in
1976, so they are still under copyright in India and the UK. Every author here died before
1950, so the whole shelf is public domain in all three.

---

## How it works

```
data/books/*.txt  (Project Gutenberg)
  -> ingest.py       strip licence, find chapters, chunk -> data/chunks.jsonl
  -> embed_store.py  all-MiniLM-L6-v2 embeddings -> FAISS index
  -> crag.py         retrieve -> grade -> answer / deepen / refuse   (LangGraph)
  -> api.py + web/   FastAPI, streams each step to the page as it happens
```

```
question -> retrieve -> grade -+-> generate        (enough passages are relevant)
                          ^    |
                          |    +-> deepen -> grade (too thin: look at top 15, grade the new 10)
                          |    |
                          |    +-> refuse          (nothing relevant: decline, skip the answer call)
                          +----+
```

- **Chunks** are ~1,000 characters, packed from whole paragraphs, with 200 characters of
  overlap, and they **never cross a chapter boundary** — so each one's citation is exact.
- **Every chunk starts with a label line** — `The Hound of the Baskervilles — Chapter 6:
  Baskerville Hall` — that both the search and the model see (see below for why).
- **The grader is a model reading each passage**, not a similarity cutoff, because a
  similarity score measures whether a passage is *about* the question, never whether it
  *answers* it. The numbers that prove this are below.

---

## From papers to books

Three things had to change, and each one is in `src/ingest.py` with its reasoning:

1. **Citations point at chapters, not pages.** Plain-text books have no pages. Chapters
   are found from the patterns novels use (`CHAPTER IV.`, `PART II.`) and, for story
   collections, from **the book's own table of contents** — a heading only counts if the
   contents list names it. The book says what its chapters are; the code does not guess.
   Getting this right took real data: *The Moonstone*'s contents list ends in a way the
   first version misread, turning 700 paragraphs into "chapters", and *The Problem of
   Cell 13* briefly lost its "13" to a page-number rule.
2. **The Gutenberg licence is cut off** before anything is indexed. It is identical in all
   23 books, so a question about "copyright" would otherwise match every one of them.
3. **Each chunk carries its book and chapter as a label line.** A research paper repeats
   its method name on every page; a Sherlock Holmes chapter just says "Holmes" and
   "Watson", like sixty other stories. Measured on the same chunks with and without it:

   | | without label | with label |
   |---|---|---|
   | Right book ranked first | 0.65 | **0.78** |
   | MRR | 0.74 | **0.84** |
   | Hit Rate@5 | 0.88 | **0.92** |

   The intervals overlap a little, so the direction is clear and the exact size is not.
   On the 12 reworded questions that name no story, the label slightly *hurt* (0.83 → 0.67).

---

## Evaluation

**93 hand-labelled questions** in `eval/test_questions.json`: 77 the books can answer
(48 simple, 12 reworded, 9 comparisons across two books, 8 needing several books) and
**16 traps** that sound on-topic but have no answer in the text — like *"Who is finally
revealed as the murderer of Edwin Drood?"* (Dickens died before writing it).

Every required fact was checked by script to appear in its book, and every trap was
checked not to leak into any book. `src/eval/verify_questions.py` re-runs both checks;
when the research-paper version grew from 9 to 30 papers, two traps quietly became
answerable, and this is the guard against that.

Proportions carry Wilson intervals, means a seeded bootstrap (`eval_core.py` explains why
the two differ).

### Retrieval (free to run, no API calls)

| Metric (n = 77) | Score [95% CI] |
|---|---|
| Hit Rate@5 — right book in the top 5 | **0.92** [0.84–0.96] |
| Right book ranked first | 0.78 [0.67–0.86] |
| MRR | 0.84 [0.77–0.91] |

| Against baselines | Hit Rate@5 |
|---|---|
| Semantic search (this system) | 0.92 [0.84–0.96] |
| BM25 keyword search | 0.94 [0.86–0.97] |
| Random chunks | 0.30 [0.21–0.41] |

**BM25 ties the embeddings on books.** That is a real result, stated plainly: book
questions are full of exact names ("Rouletabille", "Speckled Band") that keyword search
matches perfectly. On research papers the embeddings won clearly on reworded questions
(0.91 vs 0.55); on novels the reworded questions tie too (0.67 each). The two methods
fail on *different* questions (3 vs 4), which points at a hybrid as the next step.

| By type | Hit@5 | Books reached |
|---|---|---|
| simple (48) | 0.96 | 0.96 |
| paraphrase (12) | 0.67 | 0.67 |
| comparison (9) | 1.00 | 0.78 |
| multi-book (8) | 1.00 | **0.40** |

Hit Rate is meaningless for multi-book questions — five random chunks score 0.75 there —
so "books reached" is the number that counts: retrieval finds one book and stops.

**Robustness** (`robustness.py`): casual wording and keyword-only queries cost almost
nothing (0.91 and 0.92); **typos cost the most** (0.92 → 0.68).

### Why a similarity cutoff cannot replace the grader

| Top-1 similarity | mean |
|---|---|
| 77 answerable questions | 0.607 |
| 16 unanswerable traps | 0.586 |

The two groups overlap almost completely. The Edwin Drood trap scores **0.749 — higher
than 73 of the 77 answerable questions**. A cosine score measures whether a passage is
*about* the question; it cannot say whether the passage *answers* it. On books even
plainly off-topic questions leak through: "Write a poem about the ocean" scores 0.52,
because literature is full of the sea. (`config.LOW_CONFIDENCE_THRESHOLD = 0.46` is the
cut that gets the fewest wrong, 1 of 18, and the monitoring flag built on it is advisory.)

### Answers, and corrective vs plain RAG

<!-- FILLED IN FROM eval/summary.json AFTER THE RUN -->

### Still to run

`closed_book.py` (how much the model already knows *without* the books — the key question
for famous public-domain texts) and `judge.py` (an LLM judge cross-check) need ~370 more
free-tier calls, which is a second day of quota.

---

## Project layout

```
src/
  download_books.py   the 23 books, from a Project Gutenberg mirror
  ingest.py           licence stripping, chapter detection, chunking, label lines
  embed_store.py      embeddings + FAISS index
  retrieve.py         search
  generate.py         the answer prompt (only from the passages; never from memory)
  grader.py, crag.py  the corrective flow
  api.py, web/        FastAPI + a hand-written page (no framework, no build step)
  telemetry.py        what the live system did on real questions
  eval/               the evaluation suite (eval_core.py holds all the scoring)
  agentic/            a no-index comparison arm: the model greps the books itself
data/books/           the texts + catalog.json (author, year, source link)
data/vector_store/    the committed FAISS index
eval/                 test set, reports, summary.json (read by the Evaluation tab)
```

Every tunable number lives in `src/config.py`, with the measurement that justifies it.
