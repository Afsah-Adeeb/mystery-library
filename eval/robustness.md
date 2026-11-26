# Robustness: retrieval under badly-typed questions

Every answerable question re-asked in four forms and re-scored at top-k=5. All variants are generated deterministically from the original, so nothing here was hand-picked.

| Variant | What it does to the question |
|---|---|
| `original` | unchanged -- careful, complete English |
| `typo` | one character-level typo per ~12 characters, inside words only |
| `casual` | lowercased, punctuation removed, polite question frame stripped |
| `keywords` | stopwords removed -- a bag of content words, search-box style |

## Results

| Variant | Hit Rate@5 | MRR | Same top book as original | Mean confidence |
|---|---|---|---|---|
| `original` | 0.92 [0.84-0.96] | 0.841 [0.767-0.908] | - | 0.607 [0.584-0.628] |
| `typo` | 0.68 [0.56-0.77] | 0.586 [0.484-0.682] | 0.51 [0.40-0.62] | 0.497 [0.477-0.516] |
| `casual` | 0.91 [0.82-0.96] | 0.852 [0.777-0.923] | 0.87 [0.78-0.93] | 0.596 [0.573-0.619] |
| `keywords` | 0.92 [0.84-0.96] | 0.863 [0.790-0.926] | 0.81 [0.70-0.88] | 0.565 [0.542-0.587] |

**Accuracy and stability are different questions.** Hit Rate can hold steady while the *same top book* column falls, because several books may be acceptable for one question. That combination means the system is landing on a different-but-still-correct source -- fine today, fragile once the corpus grows and near-duplicate books start competing.

- **`typo`**: Hit Rate +0.25 vs original (a real drop, outside the intervals); kept the same top book on 51% of questions.
- **`casual`**: Hit Rate +0.01 vs original (within measurement error); kept the same top book on 87% of questions.
- **`keywords`**: Hit Rate +0.00 vs original (within measurement error); kept the same top book on 81% of questions.

## Per-type

| Type | `original` | `typo` | `casual` | `keywords` |
|---|---|---|---|---|
| comparison (9) | 1.00 | 0.78 | 1.00 | 1.00 |
| multi_book (8) | 1.00 | 0.62 | 0.88 | 0.88 |
| paraphrase (12) | 0.67 | 0.67 | 0.67 | 0.75 |
| simple (48) | 0.96 | 0.67 | 0.96 | 0.96 |

## Questions that broke

Questions the original form got right and a degraded form got wrong. These name the actual failure rather than averaging it away.

**`S01`** (simple) -- broke under: `typo`
- original: What word was written in blood on the wall at Lauriston Gardens?
- typo: What word was written in blod on the wall at Lurisotn aGredns?

**`S09`** (simple) -- broke under: `typo`
- original: In Silver Blaze, what was the curious incident of the dog in the night-time?
- typo: In Silver Bllaze, what was the crious incidet of the odg in the ngiht-itme?

**`S10`** (simple) -- broke under: `typo`
- original: Where did Holmes and Moriarty have their final struggle in The Final Problem?
- typo: Where did Hooles and Morarty have their final srugge in The Final Problem?

**`S14`** (simple) -- broke under: `typo`
- original: What weapon did Colonel Moran use in The Adventure of the Empty House?
- typo: What weapon did Coolnoel Mran use in The Adventue of the Empty oHuse?

**`S15`** (simple) -- broke under: `typo`
- original: What did the stick figures in The Adventure of the Dancing Men turn out to be?
- typo: What did the stick fgures in The Addventrue of thhe Daancig Men turn out to be?

**`S16`** (simple) -- broke under: `typo`
- original: What was hidden inside one of the busts in The Six Napoleons?
- typo: Wht was hidden insiide oe of the buusts in The Six Npoleons?

**`S21`** (simple) -- broke under: `typo`
- original: How did Maria Gibson die in The Problem of Thor Bridge?
- typo: Hw did Maria Gibsn de in The Problem of Thor Brige?

**`S25`** (simple) -- broke under: `typo`
- original: Whose family curse was supposedly hidden under the purple wig?
- typo: Whose faimly curse was supposedly hidden unedr thhe purrple iwg?

**`S27`** (simple) -- broke under: `typo`
- original: What did the coded message in The Gold-Bug lead to?
- typo: What did the coedd meessage in The oGld-uBg lead to?

**`S31`** (simple) -- broke under: `typo`
- original: Which book does Gabriel Betteredge keep re-reading for guidance?
- typo: hWiich book does Gabriel Betteeredge keeep re-redaing for guidance?

**`S34`** (simple) -- broke under: `typo`
- original: Who is the police detective in The Leavenworth Case?
- typo: Who is the polce detective in The eLavenoth Case?

**`S35`** (simple) -- broke under: `typo`
- original: How was Horatio Leavenworth killed?
- typo: How was Hoartio Leavneworth killed?

**`S37`** (simple) -- broke under: `typo`
- original: Who turns out to be the murderer in The Big Bow Mystery?
- typo: Who turns out to be the murderer in The Biig Boow Myssery?

**`S39`** (simple) -- broke under: `typo`
- original: Who narrates the Raffles stories?
- typo: Who narrates the Rafles stories?

**`P01`** (paraphrase) -- broke under: `typo`
- original: In which story does a stepfather kill using a venomous creature sent through a small opening into the next bedroom?
- typo: In which story does a steepfather kill suing a veenomous creautre sent throough a msall openinng into the neext bedoom?

**`C05`** (comparison) -- broke under: `typo`
- original: Compare the motive for murder in A Study in Scarlet with the motive in The Valley of Fear.
- typo: Copmare the motve for murder in A Suy in Sccarlet with the motiive in The Valley of eFar.

**`C07`** (comparison) -- broke under: `typo`
- original: In The Final Problem Watson believes Holmes died at the Reichenbach Falls. How does Holmes explain his survival in The Empty House?
- typo: In The Final Poblem Watsn beliees Hoolmes died at the Reihcennbach Falls. How does Holmees explain his suvvrival in The Emty House?

**`M04`** (multi_book) -- broke under: `typo`, `casual`, `keywords`
- original: Which books in this collection have part of their story set in America?
- typo: Which books in thiis collectioon havve part of their sotry set in Ameriica?
- casual: books in this collection have part of their story set in america
- keywords: books collection part story set America

**`M06`** (multi_book) -- broke under: `typo`
- original: Which books in this collection have plots connected to India?
- typo: Whhich books in ths collection hvae plots connecetd to Idia?

**`M07`** (multi_book) -- broke under: `typo`
- original: Which gentleman thieves appear in this collection?
- typo: Which genteman thieves apear in this collecciton?
