# Evaluation Report

Test set: 77 answerable + 16 unanswerable questions. Retrieval at top-k=5.

All figures carry a 95% confidence interval in brackets. Proportions use a Wilson interval, means use a seeded bootstrap -- see `eval_core.py` for why the two differ.

## Retrieval

| Metric | Score [95% CI] |
|---|---|
| Hit Rate@1 | 0.78 [0.67-0.86] |
| Hit Rate@3 | 0.91 [0.82-0.96] |
| Hit Rate@5 | 0.92 [0.84-0.96] |
| Precision@1 | 0.78 [0.69-0.87] |
| Precision@3 | 0.80 [0.72-0.87] |
| Precision@5 | 0.79 [0.71-0.86] |
| MRR | 0.841 [0.767-0.908] |
| Book coverage | 0.83 [0.76-0.90] |

- **Hit Rate@k** -- did at least one of the top-k chunks come from a correct book? *Did we find it at all.*
- **Precision@k** -- what fraction of the top-k came from a correct book? *How much noise came with it.*
- **MRR** -- 1/(position of the first correct chunk). *Where we found it.* Hit Rate scores position 1 and position 5 identically; this does not.
- **Book coverage** -- fraction of ALL correct books reached, which matters for the multi-book questions that need three or four at once.

### Where the first correct chunk lands

| Rank | Questions |
|---|---|
| 1 | 60 |
| 2 | 7 |
| 3 | 3 |
| 4 | 1 |
| 5 | 0 |
| not in top-5 | 6 |

If most of the mass sits at rank 4-5, the system depends on every slot and lowering `DEFAULT_TOP_K` would break it. If it sits at rank 1, a smaller k is free.

## Confidence control: answerable vs unanswerable

The 16 unanswerable questions have no correct book to find, so they are not scored for accuracy. They serve as a control: retrieval confidence on questions the corpus *can* answer should sit clearly above confidence on questions it cannot.

| Group | Mean top-1 similarity [95% CI] |
|---|---|
| Answerable | 0.607 [0.584-0.628] |
| Unanswerable | 0.586 [0.539-0.629] |

The two groups **overlap** by 0.338. No single similarity threshold can separate 'found it' from 'found nothing' on this corpus, which means the hallucination flag in the monitoring dashboard cannot be fully trusted. Worth saying out loud rather than tuning the threshold until it looks clean.

## By question type

| Type | n | Hit@5 | MRR | Book coverage | Mean confidence |
|---|---|---|---|---|---|
| simple | 48 | 0.96 [0.86-0.99] | 0.906 [0.833-0.969] | 0.96 [0.90-1.00] | 0.627 [0.600-0.652] |
| paraphrase | 12 | 0.67 [0.39-0.86] | 0.528 [0.278-0.778] | 0.67 [0.42-0.92] | 0.540 [0.506-0.576] |
| comparison | 9 | 1.00 [0.70-1.00] | 1.000 [1.000-1.000] | 0.78 [0.61-0.94] | 0.664 [0.632-0.689] |
| multi_book | 8 | 1.00 [0.68-1.00] | 0.740 [0.479-0.917] | 0.40 [0.27-0.58] | 0.522 [0.477-0.564] |
| unanswerable | 16 | - | - | - | 0.586 [0.539-0.629] |

This table is where the findings are. A single average across all questions can be 100% on simple lookups and 0% on multi-book ones and still print as a healthy number.

## Answers

| Metric | Score [95% CI] |
|---|---|
| Fact coverage | 0.45 [0.34-0.55] |
| All required facts present | 0.39 [0.29-0.50] |
| Correct refusal (unanswerable) | 1.00 [0.81-1.00] |
| Over-refusal (answerable) | 0.44 [0.34-0.55] |

Refusal is reported in **both** directions on purpose. A system that declines everything scores 1.00 on correct refusal and 1.00 on over-refusal; neither number means anything alone.

## Per-question detail

### S01 (simple) -- What word was written in blood on the wall at Lauriston Gardens?
*Why this question is here: Single distinctive token. Baseline sanity check.*

**Correct book(s):** A Study in Scarlet.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] A Study in Scarlet.txt (Part I, Chapter III: The Lauriston Gardens Mystery, score=0.658)
2. [x] A Study in Scarlet.txt (Part I, Chapter III: The Lauriston Gardens Mystery, score=0.636)
3. [x] A Study in Scarlet.txt (Part I, Chapter IV: What John Rance Had to Tell, score=0.604)
4. [x] A Study in Scarlet.txt (Part I, Chapter III: The Lauriston Gardens Mystery, score=0.592)
5. [x] A Study in Scarlet.txt (Part I, Chapter III: The Lauriston Gardens Mystery, score=0.569)

**Answer:**

The provided text describes a word written in blood-red letters on the wall at Lauriston Gardens, but it does not specify what that word is.

**Required facts:** 0/1
**Missing:** RACHE
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S02 (simple) -- Who murdered Enoch Drebber in A Study in Scarlet?
*Why this question is here: The solution of the first Holmes novel.*

**Correct book(s):** A Study in Scarlet.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] A Study in Scarlet.txt (Part II, Chapter VI: A Continuation of the Reminiscences of John Watson, M.D, score=0.699)
2. [x] A Study in Scarlet.txt (Part I, Chapter V: Our Advertisement Brings a Visitor, score=0.665)
3. [x] A Study in Scarlet.txt (Part II, Chapter VII: The Conclusion, score=0.660)
4. [x] A Study in Scarlet.txt (Part II, Chapter VI: A Continuation of the Reminiscences of John Watson, M.D, score=0.635)
5. [x] A Study in Scarlet.txt (Part II, Chapter VI: A Continuation of the Reminiscences of John Watson, M.D, score=0.614)

**Answer:**

Jefferson Hope murdered Enoch Drebber. He pursued Drebber from Salt Lake City to St. Petersburg to exact vengeance for the life taken by Drebber long before, eventually killing him by offering him a choice of poisoned pills.

**Required facts:** 1/1

---

### S03 (simple) -- On which troopship did Watson return to England from Afghanistan?
*Why this question is here: One word in the first chapter; easy to miss in a 330-chunk book.*

**Correct book(s):** A Study in Scarlet.txt
**First correct chunk at rank:** not in top-5

**Retrieved:**
1. [ ] The Memoirs of Sherlock Holmes.txt (The Final Problem, score=0.534)
2. [ ] The Adventures of Sherlock Holmes.txt (The Boscombe Valley Mystery, score=0.514)
3. [ ] The Return of Sherlock Holmes.txt (The Adventure of the Abbey Grange, score=0.513)
4. [ ] His Last Bow.txt (His Last Bow: The War Service of Sherlock Holmes, score=0.513)
5. [ ] The Return of Sherlock Holmes.txt (The Adventure of the Priory School, score=0.509)

**Answer:**

The provided text does not contain information about which troopship Watson returned on. It only mentions that his experience of camp life in Afghanistan made him a prompt traveler.

**Required facts:** 0/1
**Missing:** Orontes
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S04 (simple) -- What treasure is at the centre of The Sign of the Four?
*Why this question is here: Named treasure; the novel's spine.*

**Correct book(s):** The Sign of the Four.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Sign of the Four.txt (Chapter XII: The Strange Story of Jonathan Small, score=0.709)
2. [x] The Sign of the Four.txt (Chapter IV: The Story of the Bald-Headed Man, score=0.682)
3. [x] The Sign of the Four.txt (Chapter XII: The Strange Story of Jonathan Small, score=0.669)
4. [x] The Sign of the Four.txt (Chapter VII: The Episode of the Barrel, score=0.658)
5. [x] The Sign of the Four.txt (Chapter XII: The Strange Story of Jonathan Small, score=0.644)

**Answer:**

The treasure at the center of *The Sign of the Four* is a chest filled with a vast collection of precious gems. According to Jonathan Small, the collection includes 143 diamonds of the first water—including the "Great Mogul"—97 emeralds, 170 rubies, 40 carbuncles, 210 sapphires, 61 agates, and a large quantity of other stones such as beryls, onyxes, cats’-eyes, and turquoises. The total value of these jewels is estimated to be no less than half a million sterling.

**Required facts:** 0/1
**Missing:** Agra

---

### S05 (simple) -- What was the name of the dog Holmes borrowed to follow the creosote trail?
*Why this question is here: Small named detail inside a long novel.*

**Correct book(s):** The Sign of the Four.txt
**First correct chunk at rank:** not in top-5

**Retrieved:**
1. [ ] The Return of Sherlock Holmes.txt (The Adventure of the Missing Three-Quarter, score=0.607)
2. [ ] The Return of Sherlock Holmes.txt (The Adventure of the Solitary Cyclist, score=0.607)
3. [ ] The Return of Sherlock Holmes.txt (The Adventure of the Solitary Cyclist, score=0.605)
4. [ ] The Adventures of Sherlock Holmes.txt (The Boscombe Valley Mystery, score=0.602)
5. [ ] The Adventures of Sherlock Holmes.txt (The Adventure of the Speckled Band, score=0.590)

**Answer:**

The provided text does not mention a dog named in relation to a creosote trail. In *The Adventure of the Missing Three-Quarter*, Holmes uses a dog named Pompey to follow a trail of aniseed, not creosote.

**Required facts:** 0/1
**Missing:** Toby
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S06 (simple) -- What killed Julia Stoner in The Speckled Band?
*Why this question is here: The best-known solution in the canon.*

**Correct book(s):** The Adventures of Sherlock Holmes.txt
**First correct chunk at rank:** 2

**Retrieved:**
1. [ ] The Moonstone.txt (First Narrative, Chapter VII, score=0.478)
2. [x] The Adventures of Sherlock Holmes.txt (The Adventure of the Speckled Band, score=0.473)
3. [ ] The Moonstone.txt (First Period, Chapter IV, score=0.469)
4. [ ] The Moonstone.txt (First Period, Chapter XIX, score=0.464)
5. [ ] The Moonstone.txt (First Period, Chapter XV, score=0.456)

**Answer:**

The provided text does not state what killed Julia Stoner; it only mentions that her sister believes she died from a sudden fright, a theory which Sherlock Holmes disputes in favor of a "more tangible cause."

**Required facts:** 0/1
**Missing:** swamp adder/swamp-adder/snake
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S07 (simple) -- What was the Red-Headed League really a cover for?
*Why this question is here: Two facts: the target and the method.*

**Correct book(s):** The Adventures of Sherlock Holmes.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Adventures of Sherlock Holmes.txt (The Red-Headed League, score=0.512)
2. [x] The Adventures of Sherlock Holmes.txt (The Red-Headed League, score=0.430)
3. [x] The Adventures of Sherlock Holmes.txt (The Red-Headed League, score=0.412)
4. [x] The Adventures of Sherlock Holmes.txt (The Red-Headed League, score=0.401)
5. [x] The Adventures of Sherlock Holmes.txt (The Red-Headed League, score=0.398)

**Answer:**

The Red-Headed League was a cover for a bank robbery. Its purpose was to lure the pawnbroker Jabez Wilson out of his shop for several hours every day, allowing the criminals to secure his absence to carry out their attempt at the robbery.

**Required facts:** 1/2
**Missing:** tunnel

---

### S08 (simple) -- Where was the blue carbuncle found?
*Why this question is here: Distinctive object, distinctive hiding place.*

**Correct book(s):** The Adventures of Sherlock Holmes.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Adventures of Sherlock Holmes.txt (The Adventure of the Blue Carbuncle, score=0.462)
2. [x] The Adventures of Sherlock Holmes.txt (The Adventure of the Blue Carbuncle, score=0.461)
3. [x] The Adventures of Sherlock Holmes.txt (The Adventure of the Blue Carbuncle, score=0.445)
4. [x] The Adventures of Sherlock Holmes.txt (The Adventure of the Blue Carbuncle, score=0.439)
5. [x] The Adventures of Sherlock Holmes.txt (The Adventure of the Blue Carbuncle, score=0.438)

**Answer:**

The blue carbuncle was found in the banks of the Amoy River in southern China.

**Required facts:** 0/1
**Missing:** goose

---

### S09 (simple) -- In Silver Blaze, what was the curious incident of the dog in the night-time?
*Why this question is here: Famous line; the answer is an absence ('did nothing').*

**Correct book(s):** The Memoirs of Sherlock Holmes.txt
**First correct chunk at rank:** 2

**Retrieved:**
1. [ ] The Adventures of Sherlock Holmes.txt (The Adventure of the Copper Beeches, score=0.611)
2. [x] The Memoirs of Sherlock Holmes.txt (Silver Blaze, score=0.595)
3. [x] The Memoirs of Sherlock Holmes.txt (Silver Blaze, score=0.577)
4. [ ] The Hound of the Baskervilles.txt (Chapter 11: The Man on the Tor, score=0.557)
5. [ ] The Hound of the Baskervilles.txt (Chapter 2: The Curse of the Baskervilles, score=0.553)

**Answer:**

The curious incident of the dog in the night-time was that the dog did nothing. Despite the fact that someone entered the stables and removed a horse, the dog did not bark enough to wake the two lads sleeping in the loft.

**Required facts:** 1/1

---

### S10 (simple) -- Where did Holmes and Moriarty have their final struggle in The Final Problem?
*Why this question is here: Single place name.*

**Correct book(s):** The Memoirs of Sherlock Holmes.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Memoirs of Sherlock Holmes.txt (The Final Problem, score=0.669)
2. [x] The Memoirs of Sherlock Holmes.txt (The Final Problem, score=0.668)
3. [x] The Memoirs of Sherlock Holmes.txt (The Final Problem, score=0.665)
4. [x] The Memoirs of Sherlock Holmes.txt (The Final Problem, score=0.657)
5. [ ] The Adventures of Sherlock Holmes.txt (A Scandal in Bohemia, score=0.640)

**Answer:**

In *The Final Problem*, the final struggle between Sherlock Holmes and Professor Moriarty takes place above a "dreadful caldron of swirling water and seething foam," into which both men fell. While the provided text does not explicitly name the location, it describes the scene as a place where they reeled over together and where their bodies were left to lie.

**Required facts:** 0/1
**Missing:** Reichenbach

---

### S11 (simple) -- What club does Mycroft Holmes belong to?
*Why this question is here: Introduced in The Greek Interpreter.*

**Correct book(s):** The Memoirs of Sherlock Holmes.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Memoirs of Sherlock Holmes.txt (The Greek Interpreter, score=0.661)
2. [x] The Memoirs of Sherlock Holmes.txt (The Greek Interpreter, score=0.629)
3. [ ] His Last Bow.txt (The Adventure of the Bruce-Partington Plans, score=0.609)
4. [ ] His Last Bow.txt (The Adventure of the Bruce-Partington Plans, score=0.594)
5. [x] The Memoirs of Sherlock Holmes.txt (The Greek Interpreter, score=0.593)

**Answer:**

Mycroft Holmes belongs to the Diogenes Club, which is located in Pall Mall, opposite his rooms.

**Required facts:** 1/1

---

### S12 (simple) -- Who was the villain behind the hound in The Hound of the Baskervilles?
*Why this question is here: Novel-length solution.*

**Correct book(s):** The Hound of the Baskervilles.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Hound of the Baskervilles.txt (Chapter 15: A Retrospection, score=0.767)
2. [x] The Hound of the Baskervilles.txt (Chapter 15: A Retrospection, score=0.765)
3. [x] The Hound of the Baskervilles.txt (Chapter 15: A Retrospection, score=0.761)
4. [x] The Hound of the Baskervilles.txt (Chapter 14: The Hound of the Baskervilles, score=0.761)
5. [x] The Hound of the Baskervilles.txt (Chapter 3: The Problem, score=0.754)

**Answer:**

The villain behind the hound was Stapleton.

**Required facts:** 1/1

---

### S13 (simple) -- How was the escaped convict Selden related to Mrs. Barrymore?
*Why this question is here: A relationship stated once, in the middle of the book.*

**Correct book(s):** The Hound of the Baskervilles.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Hound of the Baskervilles.txt (Chapter 7: The Stapletons of Merripit House, score=0.533)
2. [x] The Hound of the Baskervilles.txt (Chapter 8: First Report of Dr. Watson, score=0.529)
3. [x] The Hound of the Baskervilles.txt (Chapter 8: First Report of Dr. Watson, score=0.526)
4. [x] The Hound of the Baskervilles.txt (Chapter 9: The Light upon the Moor [Second Report of Dr. Watson], score=0.498)
5. [x] The Hound of the Baskervilles.txt (Chapter 10: Extract from the Diary of Dr. Watson, score=0.496)

**Answer:**

The provided text does not contain information regarding the relationship between the escaped convict Selden and Mrs. Barrymore.

**Required facts:** 0/1
**Missing:** brother
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S14 (simple) -- What weapon did Colonel Moran use in The Adventure of the Empty House?
*Why this question is here: Weapon and its maker.*

**Correct book(s):** The Return of Sherlock Holmes.txt
**First correct chunk at rank:** 2

**Retrieved:**
1. [ ] The Adventures of Sherlock Holmes.txt (The Boscombe Valley Mystery, score=0.500)
2. [x] The Return of Sherlock Holmes.txt (The Adventure of the Empty House, score=0.498)
3. [x] The Return of Sherlock Holmes.txt (The Adventure of the Empty House, score=0.491)
4. [x] The Return of Sherlock Holmes.txt (The Adventure of the Empty House, score=0.461)
5. [x] The Return of Sherlock Holmes.txt (The Adventure of the Empty House, score=0.453)

**Answer:**

In *The Adventure of the Empty House*, Colonel Moran used a powerful air-gun constructed by the blind German mechanic Von Herder.

**Required facts:** 1/1

---

### S15 (simple) -- What did the stick figures in The Adventure of the Dancing Men turn out to be?
*Why this question is here: The concept, not a name.*

**Correct book(s):** The Return of Sherlock Holmes.txt
**First correct chunk at rank:** 2

**Retrieved:**
1. [ ] The Extraordinary Adventures of Arsene Lupin.txt (Madame Imbert’s Safe, score=0.416)
2. [x] The Return of Sherlock Holmes.txt (The Adventure of the Dancing Men, score=0.391)
3. [ ] The Mystery of the Yellow Room.txt (Chapter XII: Frédéric Larsan’s Cane, score=0.388)
4. [x] The Return of Sherlock Holmes.txt (The Adventure of the Dancing Men, score=0.387)
5. [x] The Return of Sherlock Holmes.txt (The Adventure of the Dancing Men, score=0.387)

**Answer:**

The provided text does not state what the stick figures turned out to be. It only notes that the people who invented the system intended for the characters to look like the random sketches of children rather than a message.

**Required facts:** 0/1
**Missing:** cipher/code
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S16 (simple) -- What was hidden inside one of the busts in The Six Napoleons?
*Why this question is here: Object hidden in an object.*

**Correct book(s):** The Return of Sherlock Holmes.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Return of Sherlock Holmes.txt (The Adventure of the Six Napoleons, score=0.614)
2. [x] The Return of Sherlock Holmes.txt (The Adventure of the Six Napoleons, score=0.606)
3. [x] The Return of Sherlock Holmes.txt (The Adventure of the Six Napoleons, score=0.588)
4. [x] The Return of Sherlock Holmes.txt (The Adventure of the Six Napoleons, score=0.572)
5. [x] The Return of Sherlock Holmes.txt (The Adventure of the Six Napoleons, score=0.565)

**Answer:**

The famous black pearl of the Borgias was hidden inside the last of the six busts of Napoleon. Holmes discovered it by smashing the plaster cast, finding the pearl fixed inside a splinter like a plum in a pudding.

**Required facts:** 1/1

---

### S17 (simple) -- What was the name of the secret society in the Vermissa Valley in The Valley of Fear?
*Why this question is here: Proper noun unique to one book.*

**Correct book(s):** The Valley of Fear.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Valley of Fear.txt (Part II, Chapter III: Lodge 341, Vermissa, score=0.726)
2. [x] The Valley of Fear.txt (Part II, Chapter V: The Darkest Hour, score=0.693)
3. [x] The Valley of Fear.txt (Part II, Chapter III: Lodge 341, Vermissa, score=0.692)
4. [x] The Valley of Fear.txt (Part II, Chapter III: Lodge 341, Vermissa, score=0.687)
5. [x] The Valley of Fear.txt (Part II, Chapter III: Lodge 341, Vermissa, score=0.686)

**Answer:**

The secret society mentioned is referred to as the Scowrers.

**Required facts:** 1/1

---

### S18 (simple) -- What poison was used in The Adventure of the Devil's Foot?
*Why this question is here: Latin name and plain name both accepted.*

**Correct book(s):** His Last Bow.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] His Last Bow.txt (The Adventure of the Devil’s Foot, score=0.688)
2. [x] His Last Bow.txt (The Adventure of the Devil’s Foot, score=0.643)
3. [x] His Last Bow.txt (The Adventure of the Devil’s Foot, score=0.635)
4. [x] His Last Bow.txt (The Adventure of the Devil’s Foot, score=0.606)
5. [x] His Last Bow.txt (The Adventure of the Devil’s Foot, score=0.600)

**Answer:**

The poison used was the devil's-foot root, also referred to as *Radix pedis diaboli*. It is a reddish-brown, snuff-like powder derived from a root shaped like a human or goat-like foot, which acts as a poison by combustion.

**Required facts:** 1/1

---

### S19 (simple) -- What false name does Holmes use when working against Von Bork in His Last Bow?
*Why this question is here: The last Holmes story chronologically.*

**Correct book(s):** His Last Bow.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] His Last Bow.txt (His Last Bow: The War Service of Sherlock Holmes, score=0.725)
2. [x] His Last Bow.txt (His Last Bow: The War Service of Sherlock Holmes, score=0.708)
3. [x] His Last Bow.txt (His Last Bow: The War Service of Sherlock Holmes, score=0.705)
4. [x] His Last Bow.txt (His Last Bow: The War Service of Sherlock Holmes, score=0.658)
5. [x] His Last Bow.txt (His Last Bow: The War Service of Sherlock Holmes, score=0.654)

**Answer:**

The provided text does not contain information about the name Holmes uses while working against Von Bork.

**Required facts:** 0/1
**Missing:** Altamont
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S20 (simple) -- What killed Fitzroy McPherson in The Adventure of the Lion's Mane?
*Why this question is here: The culprit is an animal.*

**Correct book(s):** The Case-Book of Sherlock Holmes.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Case-Book of Sherlock Holmes.txt (The Adventure of the Lion's Mane, score=0.570)
2. [x] The Case-Book of Sherlock Holmes.txt (The Adventure of the Lion's Mane, score=0.527)
3. [x] The Case-Book of Sherlock Holmes.txt (The Adventure of the Lion's Mane, score=0.525)
4. [x] The Case-Book of Sherlock Holmes.txt (The Adventure of the Lion's Mane, score=0.476)
5. [x] The Case-Book of Sherlock Holmes.txt (The Adventure of the Lion's Mane, score=0.468)

**Answer:**

Fitzroy McPherson was killed by a creature referred to as the "Lion's Mane," which Holmes explains was likely floating on the water when McPherson encountered it and provided a warning. The text does not provide further biological details regarding the creature.

**Required facts:** 0/1
**Missing:** Cyanea/jellyfish

---

### S21 (simple) -- How did Maria Gibson die in The Problem of Thor Bridge?
*Why this question is here: Solution reverses the obvious reading.*

**Correct book(s):** The Case-Book of Sherlock Holmes.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Case-Book of Sherlock Holmes.txt (The Problem of Thor Bridge, score=0.518)
2. [x] The Case-Book of Sherlock Holmes.txt (The Problem of Thor Bridge, score=0.496)
3. [x] The Case-Book of Sherlock Holmes.txt (The Problem of Thor Bridge, score=0.495)
4. [x] The Case-Book of Sherlock Holmes.txt (The Problem of Thor Bridge, score=0.490)
5. [x] The Case-Book of Sherlock Holmes.txt (The Problem of Thor Bridge, score=0.488)

**Answer:**

In *The Problem of Thor Bridge*, Maria Gibson died from a revolver bullet through her brain. She was found in the grounds of the Thor Place estate, nearly half a mile from the house, lying near a stone bridge.

**Required facts:** 0/1
**Missing:** suicide/killed herself/took her own life/her own hand

---

### S22 (simple) -- Which master criminal does Valentin pursue in The Blue Cross?
*Why this question is here: First Father Brown story.*

**Correct book(s):** The Innocence of Father Brown.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Innocence of Father Brown.txt (The Blue Cross, score=0.551)
2. [x] The Innocence of Father Brown.txt (The Blue Cross, score=0.542)
3. [x] The Innocence of Father Brown.txt (The Blue Cross, score=0.517)
4. [x] The Innocence of Father Brown.txt (The Blue Cross, score=0.499)
5. [x] The Innocence of Father Brown.txt (The Blue Cross, score=0.468)

**Answer:**

Valentin is pursuing the master criminal Flambeau.

**Required facts:** 1/1

---

### S23 (simple) -- In The Invisible Man, why did nobody notice the murderer?
*Why this question is here: Solution is a social observation, not a clue.*

**Correct book(s):** The Innocence of Father Brown.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Innocence of Father Brown.txt (The Invisible Man, score=0.557)
2. [x] The Innocence of Father Brown.txt (The Invisible Man, score=0.541)
3. [ ] The Mystery of the Yellow Room.txt (Chapter XXVII: In Which Joseph Rouletabille Appears in All His Glory, score=0.537)
4. [x] The Innocence of Father Brown.txt (The Invisible Man, score=0.532)
5. [ ] The Old Man in the Corner.txt (Chapter IX: A Broken-hearted Woman, score=0.524)

**Answer:**

In *The Invisible Man*, the murderer went unnoticed because people only mean that they saw no man they could suspect of being the person they were looking for. As Father Brown explains, people do not notice certain individuals, such as the postman, even though they are present.

**Required facts:** 1/1

---

### S24 (simple) -- In The Absence of Mr Glass, what was the young man really doing alone in his room?
*Why this question is here: Substring 'conjur' covers conjuring/conjurer/conjuror.*

**Correct book(s):** The Wisdom of Father Brown.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Wisdom of Father Brown.txt (The Absence of Mr Glass, score=0.569)
2. [x] The Wisdom of Father Brown.txt (The Absence of Mr Glass, score=0.558)
3. [x] The Wisdom of Father Brown.txt (The Absence of Mr Glass, score=0.556)
4. [x] The Wisdom of Father Brown.txt (The Absence of Mr Glass, score=0.554)
5. [x] The Wisdom of Father Brown.txt (The Absence of Mr Glass, score=0.553)

**Answer:**

Based on the provided text, it is explained that the young man, Mr. Todhunter, was acting as a ventriloquist. He was speaking in his own natural voice and then answering himself in a high, shrill, and unnatural voice to mimic the presence of another person, Mr. Glass.

**Required facts:** 0/1
**Missing:** conjur/juggl

---

### S25 (simple) -- Whose family curse was supposedly hidden under the purple wig?
*Why this question is here: Proper noun inside one story of twelve.*

**Correct book(s):** The Wisdom of Father Brown.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Wisdom of Father Brown.txt (The Purple Wig, score=0.663)
2. [x] The Wisdom of Father Brown.txt (The Purple Wig, score=0.582)
3. [x] The Wisdom of Father Brown.txt (The Purple Wig, score=0.573)
4. [x] The Wisdom of Father Brown.txt (The Purple Wig, score=0.557)
5. [x] The Wisdom of Father Brown.txt (The Purple Wig, score=0.554)

**Answer:**

The family curse hidden under the purple wig belongs to the Duke of Exmoor.

**Required facts:** 1/1

---

### S26 (simple) -- Who killed the two women in The Murders in the Rue Morgue?
*Why this question is here: First detective story ever written. Several spellings of the animal accepted.*

**Correct book(s):** The Works of Edgar Allan Poe, Volume 1.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Works of Edgar Allan Poe, Volume 1.txt (The Murders in the Rue Morgue, score=0.575)
2. [x] The Works of Edgar Allan Poe, Volume 1.txt (The Murders in the Rue Morgue, score=0.559)
3. [x] The Works of Edgar Allan Poe, Volume 1.txt (The Murders in the Rue Morgue, score=0.551)
4. [x] The Works of Edgar Allan Poe, Volume 1.txt (The Murders in the Rue Morgue, score=0.548)
5. [x] The Works of Edgar Allan Poe, Volume 1.txt (The Murders in the Rue Morgue, score=0.543)

**Answer:**

The provided text does not contain the identity of the killer. While it mentions the ingress of a "beast," it describes the case as an "insoluble mystery" and notes that nothing had transpired to throw light upon the murders.

**Required facts:** 0/1
**Missing:** Ourang-Outang/orang-outang/orangutan/orang-utan/ourang
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S27 (simple) -- What did the coded message in The Gold-Bug lead to?
*Why this question is here: Poe's cipher story.*

**Correct book(s):** The Works of Edgar Allan Poe, Volume 1.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Works of Edgar Allan Poe, Volume 1.txt (The Gold-bug, score=0.480)
2. [x] The Works of Edgar Allan Poe, Volume 1.txt (The Gold-bug, score=0.453)
3. [ ] A Study in Scarlet.txt (Part I, Chapter III: The Lauriston Gardens Mystery, score=0.452)
4. [x] The Works of Edgar Allan Poe, Volume 1.txt (The Murders in the Rue Morgue, score=0.444)
5. [x] The Works of Edgar Allan Poe, Volume 1.txt (The Gold-bug, score=0.435)

**Answer:**

The provided text does not contain information regarding what the coded message in The Gold-Bug led to.

**Required facts:** 0/1
**Missing:** treasure
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S28 (simple) -- Where was the stolen letter hidden in The Purloined Letter?
*Why this question is here: Hidden in plain sight.*

**Correct book(s):** The Works of Edgar Allan Poe, Volume 2.txt
**First correct chunk at rank:** 2

**Retrieved:**
1. [ ] The Leavenworth Case.txt (Burned Paper, score=0.572)
2. [x] The Works of Edgar Allan Poe, Volume 2.txt (The Purloined Letter, score=0.561)
3. [x] The Works of Edgar Allan Poe, Volume 2.txt (The Purloined Letter, score=0.532)
4. [x] The Works of Edgar Allan Poe, Volume 2.txt (The Purloined Letter, score=0.531)
5. [ ] The Mystery of the Yellow Room.txt (Chapter XIII, score=0.529)

**Answer:**

The provided text does not state where the stolen letter was hidden. It only notes that the Prefect was satisfied it was concealed somewhere on the Minister's premises, as it needed to be instantly available to him.

**Required facts:** 0/1
**Missing:** card-rack/card rack/rack
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S29 (simple) -- Where did the narrator of The Tell-Tale Heart hide the body?
*Why this question is here: Short story; one passage holds the answer.*

**Correct book(s):** The Works of Edgar Allan Poe, Volume 2.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Works of Edgar Allan Poe, Volume 2.txt (The Tell-tale Heart, score=0.574)
2. [x] The Works of Edgar Allan Poe, Volume 2.txt (The Tell-tale Heart, score=0.559)
3. [x] The Works of Edgar Allan Poe, Volume 2.txt (The Tell-tale Heart, score=0.547)
4. [x] The Works of Edgar Allan Poe, Volume 2.txt (The Premature Burial, score=0.518)
5. [x] The Works of Edgar Allan Poe, Volume 2.txt (The Pit and the Pendulum, score=0.511)

**Answer:**

The narrator admits to the deed and directs others to "tear up the planks" to find the body.

**Required facts:** 1/1

---

### S30 (simple) -- Who took the Moonstone from Rachel Verinder's cabinet on the night of her birthday?
*Why this question is here: Solution of a 1,500-chunk novel.*

**Correct book(s):** The Moonstone.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Moonstone.txt (First Period, Chapter XI, score=0.697)
2. [x] The Moonstone.txt (First Period, Chapter XI, score=0.694)
3. [x] The Moonstone.txt (First Period, Chapter V, score=0.692)
4. [x] The Moonstone.txt (First Period, Chapter XIII, score=0.688)
5. [x] The Moonstone.txt (Third Narrative, Chapter VIII, score=0.685)

**Answer:**

The provided text does not contain enough information to answer this question. While the passages establish that Miss Rachel possessed the diamond on the night of her birthday and that her mother noted the Indian cabinet where it was kept had no lock, the documents do not identify who took the stone.

**Required facts:** 0/1
**Missing:** Franklin Blake
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S31 (simple) -- Which book does Gabriel Betteredge keep re-reading for guidance?
*Why this question is here: Running joke, mentioned many times.*

**Correct book(s):** The Moonstone.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Moonstone.txt (Third Narrative, Chapter I, score=0.517)
2. [x] The Moonstone.txt (Fourth Narrative, score=0.451)
3. [x] The Moonstone.txt (Third Narrative, Chapter II, score=0.425)
4. [x] The Moonstone.txt (Third Narrative, Chapter VIII, score=0.420)
5. [x] The Moonstone.txt (Third Narrative, Chapter IV, score=0.418)

**Answer:**

Gabriel Betteredge keeps re-reading *Robinson Crusoe* for guidance.

**Required facts:** 1/1

---

### S32 (simple) -- What is John Jasper's relationship to Edwin Drood?
*Why this question is here: Relationship stated early.*

**Correct book(s):** The Mystery of Edwin Drood.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Mystery of Edwin Drood.txt (Chapter XVI: Devoted, score=0.734)
2. [x] The Mystery of Edwin Drood.txt (Chapter IX: Birds in the Bush, score=0.723)
3. [x] The Mystery of Edwin Drood.txt (Chapter XXIII: The Dawn Again, score=0.720)
4. [x] The Mystery of Edwin Drood.txt (Chapter XXIII: The Dawn Again, score=0.693)
5. [x] The Mystery of Edwin Drood.txt (Chapter IX: Birds in the Bush, score=0.685)

**Answer:**

Based on the provided text, John Jasper is described as being a trustee to Edwin Drood.

**Required facts:** 0/1
**Missing:** uncle

---

### S33 (simple) -- In which cathedral town is The Mystery of Edwin Drood set?
*Why this question is here: Fictional place name unique to the book.*

**Correct book(s):** The Mystery of Edwin Drood.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Mystery of Edwin Drood.txt (Chapter IX: Birds in the Bush, score=0.732)
2. [x] The Mystery of Edwin Drood.txt (Chapter XVI: Devoted, score=0.724)
3. [x] The Mystery of Edwin Drood.txt (Chapter X: Smoothing the Way, score=0.720)
4. [x] The Mystery of Edwin Drood.txt (Chapter I: The Dawn, score=0.719)
5. [x] The Mystery of Edwin Drood.txt (Chapter II: A Dean, and a Chapter Also, score=0.706)

**Answer:**

The Mystery of Edwin Drood is set in the town of Cloisterham.

**Required facts:** 1/1

---

### S34 (simple) -- Who is the police detective in The Leavenworth Case?
*Why this question is here: Least famous book in the set; the model may not know it.*

**Correct book(s):** The Leavenworth Case.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Leavenworth Case.txt (On the Stairs, score=0.678)
2. [x] The Leavenworth Case.txt (Circumstantial Evidence, score=0.659)
3. [x] The Leavenworth Case.txt (Facts and Deductions, score=0.625)
4. [x] The Leavenworth Case.txt (Facts and Deductions, score=0.620)
5. [x] The Leavenworth Case.txt (A Discovery, score=0.616)

**Answer:**

The provided text mentions that a character is "detailed as police officer and detective to look after this case," but it does not state his name.

**Required facts:** 0/1
**Missing:** Gryce
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S35 (simple) -- How was Horatio Leavenworth killed?
*Why this question is here: Method of the central murder.*

**Correct book(s):** The Leavenworth Case.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Leavenworth Case.txt (The Story of a Charming Woman, score=0.760)
2. [x] The Leavenworth Case.txt (Culmination, score=0.602)
3. [x] The Leavenworth Case.txt (On the Stairs, score=0.595)
4. [x] The Leavenworth Case.txt (A Clue, score=0.593)
5. [x] The Leavenworth Case.txt (Facts and Deductions, score=0.585)

**Answer:**

The provided text does not contain information explaining the specific method or manner in which Horatio Leavenworth was killed. While it mentions that he was killed by a "villain" and notes that Mr. Harwell identifies Henry Clavering as the assassin, the mechanics of the crime are not described.

**Required facts:** 0/1
**Missing:** shot/pistol/bullet
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S36 (simple) -- Who was found dead in the locked room in The Big Bow Mystery?
*Why this question is here: Victim's name.*

**Correct book(s):** The Big Bow Mystery.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Big Bow Mystery.txt (Chapter II, score=0.805)
2. [x] The Big Bow Mystery.txt (Chapter I, score=0.778)
3. [x] The Big Bow Mystery.txt (Chapter III, score=0.762)
4. [x] The Big Bow Mystery.txt (Chapter II, score=0.762)
5. [x] The Big Bow Mystery.txt (Chapter II, score=0.756)

**Answer:**

The provided text identifies the deceased as a young man who occupied the entire upper floor of 11 Grover Street (also referred to as 11 Glover Street), but it does not provide his name.

**Required facts:** 0/1
**Missing:** Arthur Constant/Constant
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S37 (simple) -- Who turns out to be the murderer in The Big Bow Mystery?
*Why this question is here: Solution of a lesser-known novel.*

**Correct book(s):** The Big Bow Mystery.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Big Bow Mystery.txt (Front matter, score=0.738)
2. [x] The Big Bow Mystery.txt (Chapter III, score=0.717)
3. [x] The Big Bow Mystery.txt (Chapter X, score=0.706)
4. [x] The Big Bow Mystery.txt (Chapter X, score=0.700)
5. [x] The Big Bow Mystery.txt (Chapter II, score=0.700)

**Answer:**

The provided text does not contain information revealing the identity of the murderer in *The Big Bow Mystery*. While the text mentions that the jury would have returned a verdict of "murder" and discusses the motives of the prisoner, it does not state who committed the crime.

**Required facts:** 0/1
**Missing:** Grodman
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S38 (simple) -- What sport is A. J. Raffles famous for?
*Why this question is here: Character trait stated repeatedly.*

**Correct book(s):** The Amateur Cracksman.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Amateur Cracksman.txt (The Gift of the Emperor, score=0.473)
2. [x] The Amateur Cracksman.txt (Gentlemen and Players, score=0.468)
3. [x] The Amateur Cracksman.txt (Gentlemen and Players, score=0.457)
4. [x] The Amateur Cracksman.txt (The Ides of March, score=0.449)
5. [x] The Amateur Cracksman.txt (Le Premier Pas, score=0.444)

**Answer:**

A. J. Raffles is famous for cricket. He was known for his command of pitch and break, his easy action, and his ingenuity as a bowler.

**Required facts:** 1/1

---

### S39 (simple) -- Who narrates the Raffles stories?
*Why this question is here: Narrator's nickname.*

**Correct book(s):** The Amateur Cracksman.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Amateur Cracksman.txt (The Gift of the Emperor, score=0.524)
2. [x] The Amateur Cracksman.txt (Nine Points of the Law, score=0.521)
3. [x] The Amateur Cracksman.txt (A Costume Piece, score=0.515)
4. [x] The Amateur Cracksman.txt (Le Premier Pas, score=0.513)
5. [x] The Amateur Cracksman.txt (The Gift of the Emperor, score=0.508)

**Answer:**

The Raffles stories are narrated by a character known as Bunny.

**Required facts:** 1/1

---

### S40 (simple) -- Who is the young reporter who solves The Mystery of the Yellow Room?
*Why this question is here: Detective's name.*

**Correct book(s):** The Mystery of the Yellow Room.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Mystery of the Yellow Room.txt (Chapter II: In Which Joseph Rouletabille Appears for the First Time, score=0.746)
2. [x] The Mystery of the Yellow Room.txt (Front matter, score=0.718)
3. [x] The Mystery of the Yellow Room.txt (Chapter XXVI: In Which Joseph Rouletabille is Awaited with Impatience, score=0.715)
4. [x] The Mystery of the Yellow Room.txt (Chapter XXVI: In Which Joseph Rouletabille is Awaited with Impatience, score=0.699)
5. [x] The Mystery of the Yellow Room.txt (Chapter XXVI: In Which Joseph Rouletabille is Awaited with Impatience, score=0.690)

**Answer:**

The young reporter is Joseph Rouletabille.

**Required facts:** 1/1

---

### S41 (simple) -- Who was attacked inside the Yellow Room?
*Why this question is here: Victim's name.*

**Correct book(s):** The Mystery of the Yellow Room.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Mystery of the Yellow Room.txt (Chapter XI, score=0.709)
2. [x] The Mystery of the Yellow Room.txt (Chapter XIV: “I Expect the Assassin this Evening”, score=0.698)
3. [x] The Mystery of the Yellow Room.txt (Chapter XI, score=0.695)
4. [x] The Mystery of the Yellow Room.txt (Chapter I: In Which We Begin not to Understand, score=0.695)
5. [x] The Mystery of the Yellow Room.txt (Chapter XV: The Trap, score=0.694)

**Answer:**

Mademoiselle Stangerson was the one attacked inside the Yellow Room.

**Required facts:** 1/1

---

### S42 (simple) -- Who was the attacker in The Mystery of the Yellow Room?
*Why this question is here: The detective is the criminal; easy to get backwards.*

**Correct book(s):** The Mystery of the Yellow Room.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Mystery of the Yellow Room.txt (Chapter XV: The Trap, score=0.771)
2. [x] The Mystery of the Yellow Room.txt (Chapter XI, score=0.771)
3. [x] The Mystery of the Yellow Room.txt (Chapter VI: In the Heart of the Oak Grove, score=0.753)
4. [x] The Mystery of the Yellow Room.txt (Chapter IX: Reporter and Detective, score=0.747)
5. [x] The Mystery of the Yellow Room.txt (Chapter XI, score=0.740)

**Answer:**

Based on the provided text, the identity of the attacker is not explicitly named. The narrator refers to him only as "the man of The Yellow Room" and "this mysterious unknown."

**Required facts:** 0/1
**Missing:** Larsan

---

### S43 (simple) -- Which police inspector arrests Arsene Lupin when the steamship reaches port?
*Why this question is here: Opening story of the Lupin book.*

**Correct book(s):** The Extraordinary Adventures of Arsene Lupin.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Extraordinary Adventures of Arsene Lupin.txt (The Arrest of Arsène Lupin, score=0.697)
2. [x] The Extraordinary Adventures of Arsene Lupin.txt (The Arrest of Arsène Lupin, score=0.689)
3. [x] The Extraordinary Adventures of Arsene Lupin.txt (The Escape of Arsène Lupin, score=0.669)
4. [x] The Extraordinary Adventures of Arsene Lupin.txt (The Arrest of Arsène Lupin, score=0.664)
5. [x] The Extraordinary Adventures of Arsene Lupin.txt (The Mysterious Traveller, score=0.656)

**Answer:**

The provided text does not state that any inspector successfully arrests Arsène Lupin when the steamship reaches port. It identifies Ganimard as the celebrated detective who has sworn to capture him and notes that Ganimard was present at the gangway when the passengers disembarked, but the passage ends with the question of Lupin's true identity still unresolved.

**Required facts:** 1/1
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S44 (simple) -- What is the full name of the scientist known as the Thinking Machine?
*Why this question is here: Name plus string of initials.*

**Correct book(s):** The Thinking Machine.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Thinking Machine.txt (The Problem of Cell 13, score=0.683)
2. [x] The Thinking Machine.txt (The Scarlet Thread, score=0.676)
3. [x] The Thinking Machine.txt (The Man Who Was Lost, score=0.635)
4. [x] The Thinking Machine.txt (The Mystery of a Studio, score=0.616)
5. [x] The Thinking Machine.txt (The Flaming Phantom, score=0.615)

**Answer:**

The full name of the scientist known as the Thinking Machine is Professor Augustus S. F. X. Van Dusen.

**Required facts:** 1/1

---

### S45 (simple) -- How long did the Thinking Machine bet he would need to escape from Cell 13?
*Why this question is here: A duration, stated in the wager.*

**Correct book(s):** The Thinking Machine.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Thinking Machine.txt (The Problem of Cell 13, score=0.680)
2. [x] The Thinking Machine.txt (The Problem of Cell 13, score=0.673)
3. [x] The Thinking Machine.txt (The Problem of Cell 13, score=0.670)
4. [x] The Thinking Machine.txt (The Problem of Cell 13, score=0.661)
5. [x] The Thinking Machine.txt (The Problem of Cell 13, score=0.659)

**Answer:**

The provided text does not contain information regarding a specific length of time that The Thinking Machine bet he would need to escape from Cell 13.

**Required facts:** 0/1
**Missing:** week
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S46 (simple) -- Who is the young journalist who listens to the Old Man in the Corner?
*Why this question is here: Listener's name.*

**Correct book(s):** The Old Man in the Corner.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Old Man in the Corner.txt (Chapter XXIV: An Unparalleled Outrage, score=0.581)
2. [x] The Old Man in the Corner.txt (Chapter XX: An Alibi, score=0.569)
3. [x] The Old Man in the Corner.txt (Chapter II: A Millionaire in the Dock, score=0.567)
4. [x] The Old Man in the Corner.txt (Chapter XXVIII: The Regent's Park Murder, score=0.558)
5. [x] The Old Man in the Corner.txt (Chapter XI: Mr. Errington, score=0.558)

**Answer:**

The provided text does not contain enough information to identify the young journalist who listens to the Old Man in the Corner.

**Required facts:** 0/1
**Missing:** Polly Burton/Polly
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S47 (simple) -- Who narrates The Thirty-Nine Steps?
*Why this question is here: Narrator.*

**Correct book(s):** The Thirty-Nine Steps.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Thirty-Nine Steps.txt (Chapter IV: The Adventure of the Radical Candidate, score=0.694)
2. [x] The Thirty-Nine Steps.txt (Chapter I: The Man Who Died, score=0.679)
3. [x] The Thirty-Nine Steps.txt (Chapter X: Various Parties Converging on the Sea, score=0.665)
4. [x] The Thirty-Nine Steps.txt (Chapter IX: The Thirty-Nine Steps, score=0.648)
5. [x] The Thirty-Nine Steps.txt (Chapter I: The Man Who Died, score=0.632)

**Answer:**

The provided text does not contain information about the identity of the person narrating *The Thirty-Nine Steps*.

**Required facts:** 0/1
**Missing:** Hannay
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### S48 (simple) -- Who was murdered in Richard Hannay's flat at the start of The Thirty-Nine Steps?
*Why this question is here: Victim.*

**Correct book(s):** The Thirty-Nine Steps.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Thirty-Nine Steps.txt (Chapter VIII: The Coming of the Black Stone, score=0.663)
2. [x] The Thirty-Nine Steps.txt (Chapter VIII: The Coming of the Black Stone, score=0.623)
3. [x] The Thirty-Nine Steps.txt (Chapter I: The Man Who Died, score=0.599)
4. [x] The Thirty-Nine Steps.txt (Chapter VI: The Adventure of the Bald Archaeologist, score=0.588)
5. [x] The Thirty-Nine Steps.txt (Chapter VIII: The Coming of the Black Stone, score=0.569)

**Answer:**

The provided text does not contain information regarding who was murdered in Richard Hannay's flat. It only mentions that Hannay was accused of the "Portland Place murder."

**Required facts:** 0/1
**Missing:** Scudder
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### P01 (paraphrase) -- In which story does a stepfather kill using a venomous creature sent through a small opening into the next bedroom?
*Why this question is here: Avoids 'snake', 'adder', 'ventilator', 'Roylott'. Keyword search has little to match.*

**Correct book(s):** The Adventures of Sherlock Holmes.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Adventures of Sherlock Holmes.txt (The Adventure of the Speckled Band, score=0.513)
2. [ ] The Case-Book of Sherlock Holmes.txt (The Adventure of the Sussex Vampire, score=0.494)
3. [ ] The Innocence of Father Brown.txt (The Three Tools of Death, score=0.491)
4. [ ] The Innocence of Father Brown.txt (The Wrong Shape, score=0.471)
5. [ ] The Case-Book of Sherlock Holmes.txt (The Adventure of the Sussex Vampire, score=0.469)

**Answer:**

In *The Adventures of Sherlock Holmes* — "The Adventure of the Speckled Band," a stepfather trains a snake to crawl through a ventilator into the next bedroom to kill the occupant.

**Required facts:** 1/1

---

### P02 (paraphrase) -- Which case turns on a guard animal that stayed silent overnight, showing the culprit was someone it knew?
*Why this question is here: Avoids 'dog', 'night-time', 'curious incident'.*

**Correct book(s):** The Memoirs of Sherlock Holmes.txt
**First correct chunk at rank:** not in top-5

**Retrieved:**
1. [ ] The Case-Book of Sherlock Holmes.txt (The Adventure of the Creeping Man, score=0.459)
2. [ ] The Valley of Fear.txt (Part I, Chapter VI: A Dawning Light, score=0.445)
3. [ ] The Mystery of the Yellow Room.txt (Chapter VIII: The Examining Magistrate Questions Mademoiselle Stangerson, score=0.437)
4. [ ] The Amateur Cracksman.txt (Le Premier Pas, score=0.437)
5. [ ] The Case-Book of Sherlock Holmes.txt (The Adventure of the Veiled Lodger, score=0.428)

**Answer:**

The provided text does not contain information about a case involving a guard animal that stayed silent to reveal that the culprit was someone it knew.

**Required facts:** 0/1
**Missing:** Silver Blaze
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### P03 (paraphrase) -- Which armchair sleuth fiddles with a cord while explaining cases to a female reporter over lunch?
*Why this question is here: Avoids 'string', 'knots', 'tea-shop', 'corner'.*

**Correct book(s):** The Old Man in the Corner.txt
**First correct chunk at rank:** not in top-5

**Retrieved:**
1. [ ] The Leavenworth Case.txt (Unexpected Testimony, score=0.533)
2. [ ] The Case-Book of Sherlock Holmes.txt (The Adventure of the Blanched Soldier, score=0.487)
3. [ ] The Leavenworth Case.txt (Gathered Threads, score=0.471)
4. [ ] The Case-Book of Sherlock Holmes.txt (The Adventure of the Blanched Soldier, score=0.467)
5. [ ] The Case-Book of Sherlock Holmes.txt (The Adventure of the Illustrious Client, score=0.466)

**Answer:**

The provided text does not contain information about an armchair sleuth fiddling with a cord while explaining cases to a female reporter. Therefore, I cannot answer this question using the available sources.

**Required facts:** 0/1
**Missing:** old man/Old Man
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### P04 (paraphrase) -- In which story is a stolen document concealed simply by leaving it in plain view?
*Why this question is here: Avoids 'letter', 'purloined', 'card-rack'.*

**Correct book(s):** The Works of Edgar Allan Poe, Volume 2.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Works of Edgar Allan Poe, Volume 2.txt (The Purloined Letter, score=0.615)
2. [x] The Works of Edgar Allan Poe, Volume 2.txt (The Purloined Letter, score=0.556)
3. [x] The Works of Edgar Allan Poe, Volume 2.txt (The Purloined Letter, score=0.536)
4. [ ] The Extraordinary Adventures of Arsene Lupin.txt (Sherlock Holmes Arrives Too Late, score=0.516)
5. [ ] The Leavenworth Case.txt (Unexpected Testimony, score=0.515)

**Answer:**

In *The Purloined Letter*, the stolen document is concealed by the Minister D—— by leaving it in plain view. According to the text, the Minister places the letter upon a table in the royal boudoir, where its address remains uppermost, thus hiding its contents and allowing it to escape notice.

**Required facts:** 1/1

---

### P05 (paraphrase) -- Which story has a large ape kill two women in Paris?
*Why this question is here: Avoids 'ourang-outang', 'murders', 'L'Espanaye'.*

**Correct book(s):** The Works of Edgar Allan Poe, Volume 1.txt
**First correct chunk at rank:** 2

**Retrieved:**
1. [ ] A Study in Scarlet.txt (Part II, Chapter V: The Avenging Angels, score=0.468)
2. [x] The Works of Edgar Allan Poe, Volume 1.txt (The Murders in the Rue Morgue, score=0.461)
3. [ ] A Study in Scarlet.txt (Part II, Chapter IV: A Flight for Life, score=0.430)
4. [x] The Works of Edgar Allan Poe, Volume 1.txt (The Mystery of Marie Roget, score=0.423)
5. [ ] The Case-Book of Sherlock Holmes.txt (The Adventure of the Blanched Soldier, score=0.419)

**Answer:**

The provided text mentions an Ourang-Outang in *The Murders in the Rue Morgue*, but it does not state that the animal killed two women, nor does it specify the gender or number of the victims in Paris. Therefore, the provided context does not contain enough information to answer your question.

**Required facts:** 1/1
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### P06 (paraphrase) -- In which case does the killer turn out to be a sea creature rather than a person?
*Why this question is here: Avoids 'jellyfish', 'Cyanea', 'lion'.*

**Correct book(s):** The Case-Book of Sherlock Holmes.txt
**First correct chunk at rank:** not in top-5

**Retrieved:**
1. [ ] The Works of Edgar Allan Poe, Volume 1.txt (The Mystery of Marie Roget, score=0.465)
2. [ ] The Works of Edgar Allan Poe, Volume 1.txt (The Mystery of Marie Roget, score=0.449)
3. [ ] The Thirty-Nine Steps.txt (Chapter VII: The Dry-Fly Fisherman, score=0.441)
4. [ ] The Works of Edgar Allan Poe, Volume 1.txt (The Mystery of Marie Roget, score=0.440)
5. [ ] The Works of Edgar Allan Poe, Volume 1.txt (The Mystery of Marie Roget, score=0.434)

**Answer:**

The provided text does not contain any information about a killer being a sea creature. In the case of Marie Rogêt, the text discusses the actions of a "lonely assassin" or "murderers," and in the case of Karolides, the text mentions political conspirators who are "not likely to stick at a murder."

**Required facts:** 0/1
**Missing:** Lion's Mane/Lion’s Mane/Lions Mane
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### P07 (paraphrase) -- In which Father Brown story does the killer go unseen because of his everyday uniform?
*Why this question is here: Avoids 'postman', 'invisible'.*

**Correct book(s):** The Innocence of Father Brown.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Innocence of Father Brown.txt (The Invisible Man, score=0.658)
2. [x] The Innocence of Father Brown.txt (The Flying Stars, score=0.657)
3. [x] The Innocence of Father Brown.txt (The Three Tools of Death, score=0.655)
4. [x] The Innocence of Father Brown.txt (The Queer Feet, score=0.653)
5. [ ] The Wisdom of Father Brown.txt (The Fairy Tale of Father Brown, score=0.652)

**Answer:**

The provided text does not contain information about a story in which a killer remains unseen due to wearing an everyday uniform. While the excerpt from "The Invisible Man" mentions a commissionaire and a porter, and "The Fairy Tale of Father Brown" involves a sentry in uniform, the context does not specify that a killer uses an everyday uniform to go unseen.

**Required facts:** 1/1
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### P08 (paraphrase) -- Which story features a scientist who bets he can break out of a prison using nothing but reasoning?
*Why this question is here: Avoids 'cell', 'escape', 'Thinking Machine'.*

**Correct book(s):** The Thinking Machine.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Thinking Machine.txt (The Problem of Cell 13, score=0.590)
2. [x] The Thinking Machine.txt (The Scarlet Thread, score=0.579)
3. [x] The Thinking Machine.txt (The Problem of Cell 13, score=0.568)
4. [x] The Thinking Machine.txt (The Problem of Cell 13, score=0.536)
5. [x] The Thinking Machine.txt (The Problem of Cell 13, score=0.533)

**Answer:**

The story *The Problem of Cell 13* features The Thinking Machine, a scientist who claims he can escape from a prison cell used for those under sentence of death by applying his brain and ingenuity.

**Required facts:** 1/1

---

### P09 (paraphrase) -- What did the villain smear on his huge dog to make it glow like a supernatural beast?
*Why this question is here: Avoids 'phosphorus', 'hound'.*

**Correct book(s):** The Hound of the Baskervilles.txt
**First correct chunk at rank:** 3

**Retrieved:**
1. [ ] The Adventures of Sherlock Holmes.txt (The Adventure of the Copper Beeches, score=0.551)
2. [ ] The Case-Book of Sherlock Holmes.txt (The Adventure of the Creeping Man, score=0.538)
3. [x] The Hound of the Baskervilles.txt (Chapter 14: The Hound of the Baskervilles, score=0.534)
4. [ ] The Case-Book of Sherlock Holmes.txt (The Adventure of the Creeping Man, score=0.521)
5. [x] The Hound of the Baskervilles.txt (Chapter 14: The Hound of the Baskervilles, score=0.505)

**Answer:**

The provided text does not say that the villain smeared anything on the dog. It notes that the animal's muzzle and eyes appeared to be ringed with fire and dripping with a "bluish flame," which Sherlock Holmes identified as a "cunning preparation" of phosphorus.

**Required facts:** 1/1
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### P10 (paraphrase) -- What sleep-inducing drug was secretly given to the man who unknowingly removed the yellow gem?
*Why this question is here: Avoids 'laudanum', 'opium', 'Moonstone', 'diamond'.*

**Correct book(s):** The Moonstone.txt
**First correct chunk at rank:** not in top-5

**Retrieved:**
1. [ ] The Mystery of the Yellow Room.txt (Chapter XXI: On the Watch, score=0.622)
2. [ ] The Mystery of the Yellow Room.txt (Chapter XXII: The Incredible Body, score=0.611)
3. [ ] The Old Man in the Corner.txt (Chapter V: A Night's Adventure, score=0.573)
4. [ ] The Mystery of the Yellow Room.txt (Chapter XXI: On the Watch, score=0.564)
5. [ ] His Last Bow.txt (The Adventure of the Devil’s Foot, score=0.521)

**Answer:**

The provided text does not contain information regarding a yellow gem or the specific sleep-inducing drug given to the person who removed it. Therefore, I cannot answer this question using the provided context.

**Required facts:** 0/1
**Missing:** laudanum/opium
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### P11 (paraphrase) -- Which gentleman thief is also a celebrated sportsman with a bat and ball?
*Why this question is here: Avoids 'cricket', 'cracksman', 'burglar'.*

**Correct book(s):** The Amateur Cracksman.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Amateur Cracksman.txt (Gentlemen and Players, score=0.512)
2. [x] The Amateur Cracksman.txt (Gentlemen and Players, score=0.507)
3. [x] The Amateur Cracksman.txt (Gentlemen and Players, score=0.498)
4. [x] The Amateur Cracksman.txt (Le Premier Pas, score=0.495)
5. [x] The Amateur Cracksman.txt (The Return Match, score=0.490)

**Answer:**

The gentleman thief described as a celebrated sportsman is A. J. Raffles. He is characterized as a dangerous bat, a brilliant field, and is noted as perhaps the finest slow bowler of his decade.

**Required facts:** 1/1

---

### P12 (paraphrase) -- Who is the man back from southern Africa who gets bored in London and is soon framed for murder?
*Why this question is here: Avoids 'Rhodesia', 'Hannay', 'flat'.*

**Correct book(s):** The Thirty-Nine Steps.txt
**First correct chunk at rank:** 2

**Retrieved:**
1. [ ] The Old Man in the Corner.txt (Chapter XXVIII: The Regent's Park Murder, score=0.490)
2. [x] The Thirty-Nine Steps.txt (Chapter I: The Man Who Died, score=0.477)
3. [ ] The Old Man in the Corner.txt (Chapter XXXIII: The Living and the Dead, score=0.448)
4. [ ] His Last Bow.txt (The Adventure of the Devil’s Foot, score=0.445)
5. [ ] The Old Man in the Corner.txt (Chapter XX: An Alibi, score=0.444)

**Answer:**

The provided text does not contain information about a man from southern Africa who gets bored in London and is framed for murder. While the passage from *The Adventure of the Devil’s Foot* mentions an "African explorer" named Dr. Leon Sterndale, it does not state that he was bored in London or framed for murder.

**Required facts:** 0/1
**Missing:** Hannay
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### C01 (comparison) -- How does Sherlock Holmes rate Poe's detective Dupin, and how does Dupin solve the Rue Morgue case?
*Why this question is here: Holmes dismisses Dupin in A Study in Scarlet; needs both books.*

**Correct book(s):** A Study in Scarlet.txt, The Works of Edgar Allan Poe, Volume 1.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] A Study in Scarlet.txt (Part I, Chapter II: The Science of Deduction, score=0.701)
2. [x] The Works of Edgar Allan Poe, Volume 1.txt (The Murders in the Rue Morgue, score=0.630)
3. [ ] The Works of Edgar Allan Poe, Volume 2.txt (The Purloined Letter, score=0.603)
4. [x] The Works of Edgar Allan Poe, Volume 1.txt (The Murders in the Rue Morgue, score=0.596)
5. [x] The Works of Edgar Allan Poe, Volume 1.txt (The Murders in the Rue Morgue, score=0.582)

**Answer:**

Sherlock Holmes considers Dupin a very inferior fellow. He views Dupin’s method of breaking into his friends' thoughts with an apropos remark after a long silence as showy and superficial. While he acknowledges that Dupin possessed some analytical genius, he believes he is by no means the phenomenon that Poe imagined him to be.

Regarding the Rue Morgue case, the provided text does not contain information on how Dupin solved it. It notes that he examined the neighborhood, the house, the chambers where the body of Mademoiselle L’Espanaye was found, and the bodies of the victims themselves with great minuteness, but it does not describe the conclusion or the solution to the mystery.

**Required facts:** 1/2
**Missing:** Ourang-Outang/orang-outang/orangutan/orang-utan/ourang/ape

---

### C02 (comparison) -- How does Flambeau's role change between The Blue Cross and the later Father Brown stories?
*Why this question is here: Same character across two collections.*

**Correct book(s):** The Innocence of Father Brown.txt, The Wisdom of Father Brown.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Innocence of Father Brown.txt (The Blue Cross, score=0.667)
2. [x] The Innocence of Father Brown.txt (The Blue Cross, score=0.624)
3. [x] The Innocence of Father Brown.txt (The Blue Cross, score=0.622)
4. [x] The Innocence of Father Brown.txt (The Blue Cross, score=0.620)
5. [x] The Wisdom of Father Brown.txt (The Duel of Dr Hirsch, score=0.605)

**Answer:**

The provided text does not contain information about Flambeau's role or activities after the events of The Blue Cross. Therefore, I cannot describe how his role changes between that story and later ones.

**Required facts:** 0/2
**Missing:** thief/criminal, detective/friend
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### C03 (comparison) -- The Big Bow Mystery and The Mystery of the Yellow Room are both locked-room mysteries. Who was the culprit in each?
*Why this question is here: Two solutions from two books in one answer.*

**Correct book(s):** The Big Bow Mystery.txt, The Mystery of the Yellow Room.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Big Bow Mystery.txt (Chapter II, score=0.706)
2. [x] The Big Bow Mystery.txt (Chapter I, score=0.688)
3. [x] The Big Bow Mystery.txt (Chapter II, score=0.649)
4. [x] The Big Bow Mystery.txt (Chapter IV, score=0.647)
5. [x] The Mystery of the Yellow Room.txt (Chapter IX: Reporter and Detective, score=0.644)

**Answer:**

The provided text does not contain information identifying the culprits in either *The Big Bow Mystery* or *The Mystery of the Yellow Room*. Therefore, I cannot answer your question.

**Required facts:** 0/2
**Missing:** Grodman, Larsan
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### C04 (comparison) -- Which police detectives pursue Raffles and Arsene Lupin?
*Why this question is here: One name per book.*

**Correct book(s):** The Amateur Cracksman.txt, The Extraordinary Adventures of Arsene Lupin.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Extraordinary Adventures of Arsene Lupin.txt (Arsène Lupin in Prison, score=0.571)
2. [x] The Extraordinary Adventures of Arsene Lupin.txt (Sherlock Holmes Arrives Too Late, score=0.567)
3. [x] The Extraordinary Adventures of Arsene Lupin.txt (Arsène Lupin in Prison, score=0.563)
4. [x] The Extraordinary Adventures of Arsene Lupin.txt (The Arrest of Arsène Lupin, score=0.559)
5. [x] The Extraordinary Adventures of Arsene Lupin.txt (The Escape of Arsène Lupin, score=0.557)

**Answer:**

The provided text mentions only one detective by name, Ganimard, who pursues Arsène Lupin. The text does not contain information regarding a character named Raffles or any detectives who may pursue him.

**Required facts:** 1/2
**Missing:** Mackenzie
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### C05 (comparison) -- Compare the motive for murder in A Study in Scarlet with the motive in The Valley of Fear.
*Why this question is here: Both motives are revenge for something that happened in America.*

**Correct book(s):** A Study in Scarlet.txt, The Valley of Fear.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] A Study in Scarlet.txt (Part I, Chapter V: Our Advertisement Brings a Visitor, score=0.631)
2. [x] The Valley of Fear.txt (Part II, Chapter V: The Darkest Hour, score=0.617)
3. [x] A Study in Scarlet.txt (Part II, Chapter IV: A Flight for Life, score=0.607)
4. [x] The Valley of Fear.txt (Part II, Chapter VI: Danger, score=0.598)
5. [x] A Study in Scarlet.txt (Part II, Chapter IV: A Flight for Life, score=0.598)

**Answer:**

Based on the provided text, the motives for murder are as follows:

In *The Valley of Fear*, murders are described as organized deeds committed by a society, often to eliminate law enforcement or individuals perceived as threats. For example, Policemen Hunt and Evans were shot for attempting to arrest members of the society, and other victims were targeted by the orders of Boss McGinty.

Regarding *A Study in Scarlet*, the provided text mentions that the "spirit of murder" lurked through the fields surrounding Ferrier’s home, but it does not explicitly state the specific motive for the murders occurring in that story. Therefore, I cannot provide a comparison of the motives based on the context provided.

**Required facts:** 1/3
**Missing:** revenge/vengeance/avenge, Scowrers/Birdy Edwards/Edwards/Pinkerton

---

### C06 (comparison) -- Who tells the story of The Moonstone, compared with who narrates The Leavenworth Case?
*Why this question is here: Many narrators vs one.*

**Correct book(s):** The Moonstone.txt, The Leavenworth Case.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Moonstone.txt (First Narrative, Chapter III, score=0.672)
2. [x] The Moonstone.txt (Second Narrative, Chapter III, score=0.666)
3. [x] The Moonstone.txt (Second Narrative, Chapter I, score=0.663)
4. [x] The Moonstone.txt (First Narrative, Chapter VIII, score=0.662)
5. [x] The Moonstone.txt (Fifth Narrative, score=0.656)

**Answer:**

The provided text does not contain information regarding the narrator of *The Leavenworth Case*, so I cannot provide a comparison. Regarding *The Moonstone*, the provided passages indicate that the story is told through multiple narratives, specifically mentioning Miss Clack’s narrative and the second narrative written by a contributor who takes up the pen after her.

**Required facts:** 1/2
**Missing:** Raymond
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### C07 (comparison) -- In The Final Problem Watson believes Holmes died at the Reichenbach Falls. How does Holmes explain his survival in The Empty House?
*Why this question is here: The answer is only in the second book.*

**Correct book(s):** The Return of Sherlock Holmes.txt, The Memoirs of Sherlock Holmes.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Return of Sherlock Holmes.txt (The Adventure of the Empty House, score=0.713)
2. [x] The Return of Sherlock Holmes.txt (The Adventure of the Empty House, score=0.709)
3. [x] The Return of Sherlock Holmes.txt (The Adventure of the Empty House, score=0.695)
4. [x] The Return of Sherlock Holmes.txt (The Adventure of the Empty House, score=0.690)
5. [ ] His Last Bow.txt (The Adventure of the Dying Detective, score=0.686)

**Answer:**

The provided text does not contain information about "The Final Problem" or an explanation of how Holmes survived the Reichenbach Falls. It only mentions that his old enemies knew he was alive and that their leader lies in the Reichenbach Fall.

**Required facts:** 0/1
**Missing:** baritsu
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### C08 (comparison) -- Both The Mystery of Edwin Drood and The Moonstone involve opium. Who uses it in each?
*Why this question is here: Opium in two different novels.*

**Correct book(s):** The Mystery of Edwin Drood.txt, The Moonstone.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Moonstone.txt (Third Narrative, Chapter X, score=0.684)
2. [x] The Moonstone.txt (Third Narrative, Chapter X, score=0.681)
3. [x] The Moonstone.txt (Fourth Narrative, score=0.663)
4. [x] The Mystery of Edwin Drood.txt (Chapter II: A Dean, and a Chapter Also, score=0.652)
5. [x] The Moonstone.txt (Fourth Narrative, score=0.650)

**Answer:**

In *The Mystery of Edwin Drood*, Mr. Jasper uses opium to treat an agony or pain that overcomes him.

In *The Moonstone*, Mr. Blake is given opium by Mr. Candy without his knowledge, and the narrator of the Fourth Narrative also mentions preparing and administering doses of opium.

**Required facts:** 2/2

---

### C09 (comparison) -- How do the Thinking Machine and the Old Man in the Corner differ in how they investigate?
*Why this question is here: Contrast in method across two collections.*

**Correct book(s):** The Thinking Machine.txt, The Old Man in the Corner.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Thinking Machine.txt (The Man Who Was Lost, score=0.633)
2. [x] The Thinking Machine.txt (The Mystery of a Studio, score=0.630)
3. [x] The Thinking Machine.txt (The Mystery of a Studio, score=0.618)
4. [x] The Thinking Machine.txt (The Man Who Was Lost, score=0.616)
5. [x] The Thinking Machine.txt (The Flaming Phantom, score=0.603)

**Answer:**

The provided text does not contain any information about an investigator named the Old Man in the Corner, so I cannot compare his methods to those of The Thinking Machine.

**Required facts:** 2/2
**Refusal check:** REFUSED although the answer exists (over-refusal)

---

### M01 (multi_book) -- Which books in this collection feature Professor Moriarty?
*Why this question is here: Needs three different books in the top-k.*

**Correct book(s):** The Memoirs of Sherlock Holmes.txt, The Return of Sherlock Holmes.txt, The Valley of Fear.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Return of Sherlock Holmes.txt (The Adventure of the Empty House, score=0.557)
2. [x] The Valley of Fear.txt (Part I, Chapter I: The Warning, score=0.553)
3. [x] The Memoirs of Sherlock Holmes.txt (The Final Problem, score=0.550)
4. [x] The Valley of Fear.txt (Part I, Chapter II: Sherlock Holmes Discourses, score=0.534)
5. [x] The Memoirs of Sherlock Holmes.txt (The Final Problem, score=0.518)

**Answer:**

Based on the provided texts, Professor Moriarty is featured in *The Return of Sherlock Holmes — The Adventure of the Empty House*, *The Valley of Fear — Part I, Chapter I: The Warning*, *The Valley of Fear — Part I, Chapter II: Sherlock Holmes Discourses*, and *The Memoirs of Sherlock Holmes — The Final Problem*.

**Required facts:** 3/3

---

### M02 (multi_book) -- Which stories in this library involve a stolen jewel or gem?
*Why this question is here: Broad; many valid books.*

**Correct book(s):** The Adventures of Sherlock Holmes.txt, The Moonstone.txt, The Case-Book of Sherlock Holmes.txt, The Extraordinary Adventures of Arsene Lupin.txt, The Innocence of Father Brown.txt, The Return of Sherlock Holmes.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Extraordinary Adventures of Arsene Lupin.txt (The Arrest of Arsène Lupin, score=0.623)
2. [x] The Moonstone.txt (Third Narrative, Chapter IV, score=0.549)
3. [x] The Moonstone.txt (Second Narrative, Chapter II, score=0.535)
4. [x] The Moonstone.txt (First Narrative, Chapter II, score=0.533)
5. [x] The Moonstone.txt (First Period, Chapter XXIII, score=0.527)

**Answer:**

Based on the collection, the following stories involve a stolen jewel or gem:

*   **The Extraordinary Adventures of Arsène Lupin:** Lady Jerland’s pearls and other valuable stones are stolen from her stateroom.
*   **The Moonstone:** This story involves the theft of a valuable diamond known as the Moonstone. Additionally, the text mentions that Mr. Septimus Luker was robbed of a receipt for a valuable gem he had placed in a bank.

**Required facts:** 2/3
**Missing:** carbuncle/Beryl Coronet

---

### M03 (multi_book) -- Which stories in this collection are locked-room mysteries?
*Why this question is here: The genre's classic puzzle across four books.*

**Correct book(s):** The Works of Edgar Allan Poe, Volume 1.txt, The Big Bow Mystery.txt, The Mystery of the Yellow Room.txt, The Adventures of Sherlock Holmes.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Mystery of the Yellow Room.txt (Chapter XV: The Trap, score=0.549)
2. [x] The Mystery of the Yellow Room.txt (Chapter XXVI: In Which Joseph Rouletabille is Awaited with Impatience, score=0.530)
3. [x] The Mystery of the Yellow Room.txt (Chapter XVI: Strange Phenomenon of the Dissociation of Matter, score=0.528)
4. [x] The Mystery of the Yellow Room.txt (Chapter XX: An Act of Mademoiselle Stangerson, score=0.528)
5. [x] The Mystery of the Yellow Room.txt (Chapter XIX: Rouletabille Invites Me to Breakfast at the Donjon Inn, score=0.527)

**Answer:**

Based on the provided texts, *The Mystery of the Yellow Room* is identified as a locked-room mystery. The narrative refers to the "inexplicable gallery" and the mystery of how a murderer could escape a space when they could not have left by a door, window, or stairs, and there were no secret doors or hiding-places.

The provided context does not contain enough information to identify whether any other books in this collection are locked-room mysteries.

**Required facts:** 1/3
**Missing:** Rue Morgue, Big Bow

---

### M04 (multi_book) -- Which books in this collection have part of their story set in America?
*Why this question is here: Two Holmes novels plus two American books.*

**Correct book(s):** A Study in Scarlet.txt, The Valley of Fear.txt, The Leavenworth Case.txt, The Thinking Machine.txt
**First correct chunk at rank:** 4

**Retrieved:**
1. [ ] The Return of Sherlock Holmes.txt (The Adventure of the Six Napoleons, score=0.451)
2. [ ] The Case-Book of Sherlock Holmes.txt (The Adventure of the Retired Colourman, score=0.442)
3. [ ] The Works of Edgar Allan Poe, Volume 1.txt (Front matter, score=0.413)
4. [x] The Leavenworth Case.txt (A Weird Experience, score=0.402)
5. [ ] The Thirty-Nine Steps.txt (Chapter I: The Man Who Died, score=0.401)

**Answer:**

Based on the provided text, the collection mentions that Edgar Allan Poe’s own country is America, and James Russell Lowell discusses the state of American literature in cities such as Boston, New York, and Philadelphia. Additionally, the preface to *The Thirty-Nine Steps* refers to a type of tale that Americans call a "dime novel."

The provided context does not state whether any of the stories themselves are set in America.

**Required facts:** 1/3
**Missing:** Utah/Salt Lake, Vermissa

---

### M05 (multi_book) -- Which stories involve a secret society or criminal brotherhood?
*Why this question is here: Three different books, three different societies.*

**Correct book(s):** The Valley of Fear.txt, The Adventures of Sherlock Holmes.txt, His Last Bow.txt, A Study in Scarlet.txt
**First correct chunk at rank:** 3

**Retrieved:**
1. [ ] The Works of Edgar Allan Poe, Volume 1.txt (The Mystery of Marie Roget, score=0.534)
2. [ ] The Return of Sherlock Holmes.txt (The Adventure of the Dancing Men, score=0.500)
3. [x] The Valley of Fear.txt (Part II, Chapter IV: The Valley of Fear, score=0.480)
4. [x] The Valley of Fear.txt (Part II, Chapter V: The Darkest Hour, score=0.452)
5. [x] The Valley of Fear.txt (Part II, Chapter VII: The Trapping of Birdy Edwards, score=0.442)

**Answer:**

Based on the provided texts, the stories involving a secret society or criminal brotherhood are:

*   **The Valley of Fear:** This book details the activities of the Freeman’s society (also referred to as the Vermissa lodge). It describes how members are forced into a "meshwork of crime" under the orders of a leader identified as Boss McGinty, and notes the eventual arrest of the members by Birdy Edwards.
*   **The Mystery of Marie Roget:** This story discusses the possibility of a gang being involved in a crime. However, the text argues against this theory, stating that the secrecy of the deed is evidence that it was committed by only one or two people rather than a gang or body of men.

**Required facts:** 0/3
**Missing:** Scowrers, Ku Klux Klan/K. K. K./K.K.K., Red Circle

---

### M06 (multi_book) -- Which books in this collection have plots connected to India?
*Why this question is here: Colonial background shared across books.*

**Correct book(s):** The Sign of the Four.txt, The Moonstone.txt, The Adventures of Sherlock Holmes.txt, The Memoirs of Sherlock Holmes.txt
**First correct chunk at rank:** 3

**Retrieved:**
1. [ ] The Works of Edgar Allan Poe, Volume 2.txt (The Pit and the Pendulum, score=0.411)
2. [ ] The Works of Edgar Allan Poe, Volume 2.txt (The Island of the Fay, score=0.375)
3. [x] The Moonstone.txt (Second Narrative, Chapter III, score=0.373)
4. [x] The Sign of the Four.txt (Chapter XII: The Strange Story of Jonathan Small, score=0.371)
5. [x] The Moonstone.txt (Epilogue, score=0.368)

**Answer:**

The books in this collection with plots connected to India are *The Moonstone* and *The Sign of the Four*.

**Required facts:** 0/2
**Missing:** Agra, Seringapatam/Brahmin

---

### M07 (multi_book) -- Which gentleman thieves appear in this collection?
*Why this question is here: One thief per book.*

**Correct book(s):** The Amateur Cracksman.txt, The Extraordinary Adventures of Arsene Lupin.txt, The Innocence of Father Brown.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Amateur Cracksman.txt (Gentlemen and Players, score=0.542)
2. [ ] The Old Man in the Corner.txt (Chapter V: A Night's Adventure, score=0.511)
3. [x] The Amateur Cracksman.txt (Nine Points of the Law, score=0.505)
4. [ ] The Old Man in the Corner.txt (Chapter V: A Night's Adventure, score=0.500)
5. [ ] The Wisdom of Father Brown.txt (The Paradise of Thieves, score=0.499)

**Answer:**

Based on the provided text, the specific gentleman thieves mentioned are Raffles and his companion, who are identified as "two well-known London thieves" currently being watched by a detective. The text also mentions a man who calls himself "Montano," the "King of Thieves."

**Required facts:** 1/3
**Missing:** Lupin, Flambeau

---

### M08 (multi_book) -- Which detectives in this collection are not police or private detectives -- for example a priest, a scientist or a journalist?
*Why this question is here: Needs three different series.*

**Correct book(s):** The Innocence of Father Brown.txt, The Wisdom of Father Brown.txt, The Thinking Machine.txt, The Mystery of the Yellow Room.txt
**First correct chunk at rank:** 1

**Retrieved:**
1. [x] The Mystery of the Yellow Room.txt (Chapter II: In Which Joseph Rouletabille Appears for the First Time, score=0.507)
2. [ ] The Adventures of Sherlock Holmes.txt (The Adventure of the Blue Carbuncle, score=0.491)
3. [ ] The Memoirs of Sherlock Holmes.txt (The Resident Patient, score=0.487)
4. [ ] A Study in Scarlet.txt (Part II, Chapter VII: The Conclusion, score=0.484)
5. [x] The Mystery of the Yellow Room.txt (Chapter II: In Which Joseph Rouletabille Appears for the First Time, score=0.472)

**Answer:**

Based on the provided texts, Joseph Rouletabille is identified as a newspaper reporter who gained the reputation of being a detective, and he is noted for often getting the better of famous detectives. Additionally, the text mentions that Sherlock Holmes acts as an amateur in the detective line. 

The provided context does not contain information regarding a priest or a scientist acting as a detective.

**Required facts:** 1/3
**Missing:** Father Brown, Van Dusen/Thinking Machine

---

### U01 (unanswerable) -- What was Sherlock Holmes's blood type?
*Why this question is here: TRAP: on-topic character, attribute never given.*

**Expected behaviour:** refuse -- the corpus does not contain this answer.

**Retrieved:**
1. [ ] A Study in Scarlet.txt (Part I, Chapter I: Mr. Sherlock Holmes, score=0.672)
2. [ ] The Adventures of Sherlock Holmes.txt (The Man with the Twisted Lip, score=0.668)
3. [ ] A Study in Scarlet.txt (Part I, Chapter I: Mr. Sherlock Holmes, score=0.659)
4. [ ] The Adventures of Sherlock Holmes.txt (The Adventure of the Noble Bachelor, score=0.654)
5. [ ] The Case-Book of Sherlock Holmes.txt (The Adventure of the Sussex Vampire, score=0.654)

**Answer:**

The provided text does not contain information regarding Sherlock Holmes's blood type. While the passage from *A Study in Scarlet* mentions his development of a test for blood stains using hæmoglobin, it does not state his own blood type.

**Refusal check:** REFUSED (correct)

---

### U02 (unanswerable) -- What was the name of Watson's bull pup?
*Why this question is here: TRAP: Watson says he keeps a bull pup in A Study in Scarlet, but it is never named. Retrieval will find the passage confidently.*

**Expected behaviour:** refuse -- the corpus does not contain this answer.

**Retrieved:**
1. [ ] His Last Bow.txt (The Adventure of the Dying Detective, score=0.565)
2. [ ] The Hound of the Baskervilles.txt (Chapter 1: Mr. Sherlock Holmes, score=0.541)
3. [ ] The Return of Sherlock Holmes.txt (The Adventure of the Missing Three-Quarter, score=0.529)
4. [ ] The Case-Book of Sherlock Holmes.txt (The Adventure of the Creeping Man, score=0.516)
5. [ ] His Last Bow.txt (The Adventure of the Dying Detective, score=0.516)

**Answer:**

The provided text does not contain information about the name of Watson's bull pup.

**Refusal check:** REFUSED (correct)

---

### U03 (unanswerable) -- Who is finally revealed as the murderer of Edwin Drood?
*Why this question is here: TRAP: Dickens died before finishing the book. The model knows a century of theories; the text has no solution.*

**Expected behaviour:** refuse -- the corpus does not contain this answer.

**Retrieved:**
1. [ ] The Mystery of Edwin Drood.txt (Chapter XX: A Flight, score=0.749)
2. [ ] The Mystery of Edwin Drood.txt (Chapter XX: A Flight, score=0.738)
3. [ ] The Mystery of Edwin Drood.txt (Chapter XVI: Devoted, score=0.711)
4. [ ] The Mystery of Edwin Drood.txt (Chapter XVI: Devoted, score=0.698)
5. [ ] The Mystery of Edwin Drood.txt (Chapter XX: A Flight, score=0.684)

**Answer:**

The provided text does not contain information regarding who is finally revealed as the murderer of Edwin Drood. While the passages discuss the disappearance and murder of the young man, the identity of the culprit is not disclosed.

**Refusal check:** REFUSED (correct)

---

### U04 (unanswerable) -- What was the name of Professor Moriarty's mother?
*Why this question is here: TRAP: on-topic character, family never described.*

**Expected behaviour:** refuse -- the corpus does not contain this answer.

**Retrieved:**
1. [ ] The Return of Sherlock Holmes.txt (The Adventure of the Empty House, score=0.609)
2. [ ] The Return of Sherlock Holmes.txt (The Adventure of the Empty House, score=0.605)
3. [ ] The Memoirs of Sherlock Holmes.txt (The Final Problem, score=0.577)
4. [ ] The Memoirs of Sherlock Holmes.txt (The Final Problem, score=0.567)
5. [ ] The Memoirs of Sherlock Holmes.txt (The Final Problem, score=0.564)

**Answer:**

The provided text does not contain information about Professor Moriarty's mother.

**Refusal check:** REFUSED (correct)

---

### U05 (unanswerable) -- In what year was Father Brown born?
*Why this question is here: TRAP: no birth date in either collection.*

**Expected behaviour:** refuse -- the corpus does not contain this answer.

**Retrieved:**
1. [ ] The Wisdom of Father Brown.txt (The Fairy Tale of Father Brown, score=0.603)
2. [ ] The Wisdom of Father Brown.txt (The Fairy Tale of Father Brown, score=0.600)
3. [ ] The Wisdom of Father Brown.txt (The Fairy Tale of Father Brown, score=0.600)
4. [ ] The Innocence of Father Brown.txt (The Queer Feet, score=0.594)
5. [ ] The Wisdom of Father Brown.txt (The Duel of Dr Hirsch, score=0.593)

**Answer:**

The provided text does not contain information regarding the year Father Brown was born.

**Refusal check:** REFUSED (correct)

---

### U06 (unanswerable) -- How did Raffles die?
*Why this question is here: TRAP: Raffles dies in the Boer War in a LATER book that is not in this corpus.*

**Expected behaviour:** refuse -- the corpus does not contain this answer.

**Retrieved:**
1. [ ] The Amateur Cracksman.txt (The Gift of the Emperor, score=0.519)
2. [ ] The Amateur Cracksman.txt (Le Premier Pas, score=0.511)
3. [ ] The Amateur Cracksman.txt (The Gift of the Emperor, score=0.506)
4. [ ] The Amateur Cracksman.txt (The Ides of March, score=0.503)
5. [ ] The Amateur Cracksman.txt (A Costume Piece, score=0.498)

**Answer:**

The provided text does not contain information regarding how Raffles died.

**Refusal check:** REFUSED (correct)

---

### U07 (unanswerable) -- What is the name of Arsene Lupin's son?
*Why this question is here: TRAP: not in this book.*

**Expected behaviour:** refuse -- the corpus does not contain this answer.

**Retrieved:**
1. [ ] The Extraordinary Adventures of Arsene Lupin.txt (The Arrest of Arsène Lupin, score=0.648)
2. [ ] The Extraordinary Adventures of Arsene Lupin.txt (The Arrest of Arsène Lupin, score=0.643)
3. [ ] The Extraordinary Adventures of Arsene Lupin.txt (Madame Imbert’s Safe, score=0.640)
4. [ ] The Extraordinary Adventures of Arsene Lupin.txt (The Arrest of Arsène Lupin, score=0.639)
5. [ ] The Extraordinary Adventures of Arsene Lupin.txt (The Arrest of Arsène Lupin, score=0.637)

**Answer:**

The provided text does not contain information regarding whether Arsène Lupin has a son.

**Refusal check:** REFUSED (correct)

---

### U08 (unanswerable) -- What is the population of Cloisterham?
*Why this question is here: TRAP: the town is described at length but never counted.*

**Expected behaviour:** refuse -- the corpus does not contain this answer.

**Retrieved:**
1. [ ] The Mystery of Edwin Drood.txt (Chapter III: The Nuns’ House, score=0.488)
2. [ ] The Mystery of Edwin Drood.txt (Chapter XII: A Night with Durdles, score=0.400)
3. [ ] The Mystery of Edwin Drood.txt (Chapter III: The Nuns’ House, score=0.385)
4. [ ] The Return of Sherlock Holmes.txt (The Adventure of the Priory School, score=0.378)
5. [ ] The Mystery of Edwin Drood.txt (Chapter III: The Nuns’ House, score=0.359)

**Answer:**

The provided text does not contain information regarding the population of Cloisterham.

**Refusal check:** REFUSED (correct)

---

### U09 (unanswerable) -- How much was Holmes paid for solving The Hound of the Baskervilles?
*Why this question is here: TRAP: fee never mentioned.*

**Expected behaviour:** refuse -- the corpus does not contain this answer.

**Retrieved:**
1. [ ] The Hound of the Baskervilles.txt (Chapter 5: Three Broken Threads, score=0.699)
2. [ ] The Hound of the Baskervilles.txt (Front matter, score=0.696)
3. [ ] The Hound of the Baskervilles.txt (Chapter 13: Fixing the Nets, score=0.686)
4. [ ] The Hound of the Baskervilles.txt (Chapter 14: The Hound of the Baskervilles, score=0.681)
5. [ ] The Hound of the Baskervilles.txt (Chapter 5: Three Broken Threads, score=0.674)

**Answer:**

The provided text does not contain information regarding how much Holmes was paid for solving the case.

**Refusal check:** REFUSED (correct)

---

### U10 (unanswerable) -- What did Father Brown study at university?
*Why this question is here: TRAP: education never described.*

**Expected behaviour:** refuse -- the corpus does not contain this answer.

**Retrieved:**
1. [ ] The Innocence of Father Brown.txt (The Queer Feet, score=0.601)
2. [ ] The Wisdom of Father Brown.txt (The Duel of Dr Hirsch, score=0.584)
3. [ ] The Wisdom of Father Brown.txt (The Fairy Tale of Father Brown, score=0.582)
4. [ ] The Wisdom of Father Brown.txt (The Mistake of the Machine, score=0.577)
5. [ ] The Wisdom of Father Brown.txt (The Mistake of the Machine, score=0.577)

**Answer:**

The provided text does not contain information regarding what Father Brown studied at university.

**Refusal check:** REFUSED (correct)

---

### U11 (unanswerable) -- What is the name of Sherlock Holmes's barber?
*Why this question is here: TRAP: no barber.*

**Expected behaviour:** refuse -- the corpus does not contain this answer.

**Retrieved:**
1. [ ] The Adventures of Sherlock Holmes.txt (The Adventure of the Noble Bachelor, score=0.653)
2. [ ] The Adventures of Sherlock Holmes.txt (The Red-Headed League, score=0.646)
3. [ ] The Return of Sherlock Holmes.txt (The Adventure of the Dancing Men, score=0.644)
4. [ ] The Adventures of Sherlock Holmes.txt (The Adventure of the Noble Bachelor, score=0.643)
5. [ ] The Adventures of Sherlock Holmes.txt (The Red-Headed League, score=0.636)

**Answer:**

The provided text does not contain information about the name of Sherlock Holmes's barber.

**Refusal check:** REFUSED (correct)

---

### U12 (unanswerable) -- What was the Thinking Machine's favourite food?
*Why this question is here: TRAP: on-topic character, preference never given.*

**Expected behaviour:** refuse -- the corpus does not contain this answer.

**Retrieved:**
1. [ ] The Thinking Machine.txt (The Mystery of a Studio, score=0.582)
2. [ ] The Thinking Machine.txt (The Mystery of a Studio, score=0.552)
3. [ ] The Thinking Machine.txt (The Mystery of a Studio, score=0.546)
4. [ ] The Thinking Machine.txt (The Mystery of a Studio, score=0.544)
5. [ ] The Thinking Machine.txt (The Great Auto Mystery, score=0.540)

**Answer:**

The provided text does not contain information about The Thinking Machine's favorite food.

**Refusal check:** REFUSED (correct)

---

### U13 (unanswerable) -- What salary did Inspector Gryce earn?
*Why this question is here: TRAP: never stated.*

**Expected behaviour:** refuse -- the corpus does not contain this answer.

**Retrieved:**
1. [ ] The Leavenworth Case.txt (“A Great Case”, score=0.410)
2. [ ] The Leavenworth Case.txt (Mr. Gryce at Home, score=0.398)
3. [ ] The Leavenworth Case.txt (Mr. Gryce Explains Himself, score=0.392)
4. [ ] The Leavenworth Case.txt (Mr. Gryce Receives New Impetus, score=0.377)
5. [ ] The Leavenworth Case.txt (“A Great Case”, score=0.375)

**Answer:**

The provided text does not contain information regarding Inspector Gryce's salary.

**Refusal check:** REFUSED (correct)

---

### U14 (unanswerable) -- What is Richard Hannay's middle name?
*Why this question is here: TRAP: never given.*

**Expected behaviour:** refuse -- the corpus does not contain this answer.

**Retrieved:**
1. [ ] The Leavenworth Case.txt (Henry Clavering, score=0.395)
2. [ ] The Mystery of Edwin Drood.txt (Chapter XXII: A Gritty State of Things Comes on, score=0.372)
3. [ ] His Last Bow.txt (The Adventure of the Bruce-Partington Plans, score=0.367)
4. [ ] The Thirty-Nine Steps.txt (Chapter VIII: The Coming of the Black Stone, score=0.357)
5. [ ] The Thirty-Nine Steps.txt (Chapter VI: The Adventure of the Bald Archaeologist, score=0.355)

**Answer:**

The provided text does not contain information about Richard Hannay’s middle name.

**Refusal check:** REFUSED (correct)

---

### U15 (unanswerable) -- In what year did Joseph Rouletabille die?
*Why this question is here: TRAP: he is a young man in this book; no death.*

**Expected behaviour:** refuse -- the corpus does not contain this answer.

**Retrieved:**
1. [ ] The Mystery of the Yellow Room.txt (Chapter II: In Which Joseph Rouletabille Appears for the First Time, score=0.578)
2. [ ] The Mystery of the Yellow Room.txt (Chapter II: In Which Joseph Rouletabille Appears for the First Time, score=0.571)
3. [ ] The Mystery of the Yellow Room.txt (Chapter II: In Which Joseph Rouletabille Appears for the First Time, score=0.568)
4. [ ] The Mystery of the Yellow Room.txt (Chapter XVIII: Rouletabille Has Drawn a Circle between the Two Bumps on His Forehead, score=0.564)
5. [ ] The Mystery of the Yellow Room.txt (Chapter XXVI: In Which Joseph Rouletabille is Awaited with Impatience, score=0.560)

**Answer:**

The provided text does not contain information about the year of Joseph Rouletabille's death. While it mentions that he had not returned by the 15th of January and that some feared he might no longer be living, it does not confirm his death or provide a date.

**Refusal check:** REFUSED (correct)

---

### U16 (unanswerable) -- Which actor played Sherlock Holmes in the most films?
*Why this question is here: Out of corpus entirely, but phrased around the corpus's main character.*

**Expected behaviour:** refuse -- the corpus does not contain this answer.

**Retrieved:**
1. [ ] The Adventures of Sherlock Holmes.txt (A Scandal in Bohemia, score=0.596)
2. [ ] The Adventures of Sherlock Holmes.txt (The Red-Headed League, score=0.591)
3. [ ] The Adventures of Sherlock Holmes.txt (The Red-Headed League, score=0.576)
4. [ ] The Return of Sherlock Holmes.txt (The Adventure of the Empty House, score=0.575)
5. [ ] The Adventures of Sherlock Holmes.txt (The Red-Headed League, score=0.572)

**Answer:**

The provided text does not contain information about which actor played Sherlock Holmes in the most films.

**Refusal check:** REFUSED (correct)

---
