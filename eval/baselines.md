# Retrieval Baselines

Three retrievers over the same 77 answerable questions, the same chunks, and the same scoring code. The only thing that differs is how candidates are ranked.

| Arm | What it does |
|---|---|
| **semantic** | The real system. Embeds the question, returns the nearest chunks by cosine similarity. |
| **bm25** | Classical keyword search. Matches words, weighted by rarity and chunk length. No embeddings. |
| **random** | Picks chunks at random. The floor. |

## Results

| Metric | semantic | bm25 | random |
|---|---|---|---|
| Hit Rate@1 | 0.78 [0.67-0.86] | 0.79 [0.69-0.87] | 0.05 [0.02-0.13] |
| Hit Rate@5 | 0.92 [0.84-0.96] | 0.94 [0.86-0.97] | 0.30 [0.21-0.41] |
| MRR | 0.841 [0.767-0.908] | 0.856 [0.787-0.922] | 0.142 [0.088-0.205] |
| Precision@5 | 0.79 [0.71-0.86] | 0.78 [0.70-0.85] | 0.07 [0.04-0.10] |
| Book coverage | 0.83 [0.76-0.90] | 0.85 [0.78-0.92] | 0.21 [0.13-0.29] |

Semantic retrieval scores **+0.62** over random and **-0.01** over keyword search on Hit Rate@5.

**BM25 matches or beats the embeddings here.** That is a real result and worth stating plainly: at this corpus size, on these questions, the vector index is not earning its complexity. The place to look next is the per-type table below -- the advantage of embeddings is supposed to show up on reworded questions, not on ones that quote the book's own terminology.

## By question type

### Hit Rate@5

| Type | n | semantic | bm25 | random |
|---|---|---|---|---|
| simple | 48 | 0.96 [0.86-0.99] | 1.00 [0.93-1.00] | 0.19 [0.10-0.32] |
| paraphrase | 12 | 0.67 [0.39-0.86] | 0.67 [0.39-0.86] | 0.17 [0.05-0.45] |
| comparison | 9 | 1.00 [0.70-1.00] | 1.00 [0.70-1.00] | 0.67 [0.35-0.88] |
| multi_book | 8 | 1.00 [0.68-1.00] | 0.88 [0.53-0.98] | 0.75 [0.41-0.93] |

**The `paraphrase` row is the one that matters.** Those questions are deliberately worded so the book's own vocabulary never appears -- "a deadly creature sent through a hole between two bedrooms" instead of "swamp adder" and "ventilator". Keyword search has nothing to match on. If embeddings are worth having, this is the row where it shows.

### Book coverage (fraction of ALL correct books reached)

| Type | n | semantic | bm25 | random |
|---|---|---|---|---|
| simple | 48 | 0.96 [0.90-1.00] | 1.00 [1.00-1.00] | 0.19 [0.08-0.29] |
| paraphrase | 12 | 0.67 [0.42-0.92] | 0.67 [0.42-0.92] | 0.17 [0.00-0.42] |
| comparison | 9 | 0.78 [0.61-0.94] | 0.72 [0.56-0.89] | 0.33 [0.17-0.44] |
| multi_book | 8 | 0.40 [0.27-0.58] | 0.34 [0.21-0.48] | 0.23 [0.12-0.33] |

## Where they disagree

Questions one arm found and the other missed. More useful than the averages: it names the specific failure.

**Semantic found, BM25 missed (3):**
- `P05` *(paraphrase)* Which story has a large ape kill two women in Paris?
- `P11` *(paraphrase)* Which gentleman thief is also a celebrated sportsman with a bat and ball?
- `M07` *(multi_book)* Which gentleman thieves appear in this collection?

**BM25 found, semantic missed (4):**
- `S03` *(simple)* On which troopship did Watson return to England from Afghanistan?
- `S05` *(simple)* What was the name of the dog Holmes borrowed to follow the creosote trail?
- `P06` *(paraphrase)* In which case does the killer turn out to be a sea creature rather than a person?
- `P10` *(paraphrase)* What sleep-inducing drug was secretly given to the man who unknowingly removed the yellow gem?
