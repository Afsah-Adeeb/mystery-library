# Settings Sweep: chunk size and top-k

Every combination of chunk size [500, 1000, 1500] and top-k [3, 5, 10], scored on the same labelled questions. The corpus is re-chunked and re-embedded from the book texts for each chunk size.

**Currently committed:** `CHUNK_SIZE = 1000`, `DEFAULT_TOP_K = 5`.

Free to run -- retrieval scoring makes no API calls. Overlap is held at a constant fraction of chunk size (20%), so this measures chunk size rather than chunk size and redundancy together. Nothing under `data/vector_store/` is modified: every candidate index is built in memory and discarded.

## Corpus shape at each chunk size

| Chunk size | Overlap | Chunks | Mean chars | Build time |
|---|---|---|---|---|
| 500 | 100 | 28954 | 531 | 886.0s |
| 1000 | 200 | 13430 | 1018 | 571.2s |
| 1500 | 300 | 8444 | 1539 | 360.5s |

## Hit Rate@k

| chunk size \ top-k | 3 | 5 | 10 |
|---|---|---|---|
| **500** | 0.86 [0.76-0.92] | 0.87 [0.78-0.93] | 0.91 [0.82-0.96] |
| **1000** | 0.91 [0.82-0.96] | 0.92 [0.84-0.96] | 0.95 [0.87-0.98] |
| **1500** | 0.87 [0.78-0.93] | 0.87 [0.78-0.93] | 0.90 [0.81-0.95] |

## MRR

| chunk size \ top-k | 3 | 5 | 10 |
|---|---|---|---|
| **500** | 0.838 [0.753-0.916] | 0.841 [0.760-0.916] | 0.847 [0.769-0.920] |
| **1000** | 0.838 [0.764-0.907] | 0.841 [0.767-0.908] | 0.845 [0.772-0.911] |
| **1500** | 0.788 [0.703-0.866] | 0.788 [0.703-0.866] | 0.792 [0.709-0.867] |

## Book coverage

| chunk size \ top-k | 3 | 5 | 10 |
|---|---|---|---|
| **500** | 0.77 [0.68-0.85] | 0.79 [0.71-0.87] | 0.83 [0.75-0.90] |
| **1000** | 0.81 [0.73-0.88] | 0.83 [0.76-0.90] | 0.87 [0.80-0.93] |
| **1500** | 0.79 [0.71-0.87] | 0.80 [0.72-0.88] | 0.83 [0.75-0.90] |

## Precision@k

| chunk size \ top-k | 3 | 5 | 10 |
|---|---|---|---|
| **500** | 0.80 [0.71-0.88] | 0.79 [0.71-0.88] | 0.79 [0.71-0.86] |
| **1000** | 0.80 [0.72-0.87] | 0.79 [0.71-0.86] | 0.76 [0.69-0.84] |
| **1500** | 0.76 [0.67-0.84] | 0.74 [0.66-0.82] | 0.71 [0.63-0.79] |

## What the sweep says

- Best Hit Rate: **chunk 1000, top-k 10** at 0.95 [0.87-0.98] -- but note this will almost always pick the largest k in the grid, because Hit Rate cannot fall as k rises. It is not evidence that k=10 is the right choice.
- Best MRR: **chunk 500, top-k 10** at 0.847 [0.769-0.920]
- Currently committed (1000/5): Hit Rate 0.92 [0.84-0.96], MRR 0.841 [0.767-0.908]

The best cell beats the committed one by +0.03 on Hit Rate, but the confidence intervals overlap, so this grid **cannot establish** that the difference is real. The honest conclusion is that retrieval quality is not very sensitive to these two knobs on this corpus -- which is itself the answer to "why 1000?": within measurement error, it does not matter much.

**Reading the top-k columns.** Hit Rate can only rise with larger k -- more slots cannot lose a book that a smaller k already found -- so a higher Hit Rate at k=10 is not evidence that k=10 is better. MRR and precision are the columns that can genuinely fall, and every extra chunk is paid for in prompt tokens on every single query. Pick the smallest k whose MRR has stopped improving.

**This table is corpus-specific.** Re-run it after adding books; the best chunk size for 23 books is not necessarily the best for 200.
