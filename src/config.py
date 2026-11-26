"""
Central place for every path and knob used across the project.
Keeping these here (instead of scattered magic numbers in each script)
means you only change one place when tuning the pipeline, and it's the
first file you'd show an interviewer to explain your setup.
"""

import os
from pathlib import Path

# --- Paths -------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BOOKS_DIR = PROJECT_ROOT / "data" / "books"            # plain-text books (download_books.py)
BOOK_CATALOG_PATH = BOOKS_DIR / "catalog.json"        # title / author / year per file
BOOKS_TEXT_DIR = PROJECT_ROOT / "data" / "books_text"  # output of export_text.py
CHUNKS_PATH = PROJECT_ROOT / "data" / "chunks.jsonl"    # output of ingest.py
VECTOR_STORE_DIR = PROJECT_ROOT / "data" / "vector_store"
FAISS_INDEX_PATH = VECTOR_STORE_DIR / "index.faiss"
CHUNK_METADATA_PATH = VECTOR_STORE_DIR / "chunk_metadata.jsonl"

# --- Chunking ------------------------------------------------------------
# Measured in characters, not tokens, to keep things simple and dependency-free.
# ~1000 chars is roughly 200-250 words / ~250-300 tokens for English text.
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200  # chars shared between consecutive chunks, to avoid cutting ideas in half

# --- Embedding model -------------------------------------------------------
# Local, free, CPU-friendly sentence-transformers model. 384-dim output.
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# --- Generation model (Gemini) --------------------------------------------
# The live app's model, for BOTH grading and answering (api.py passes it to
# the whole corrective flow). Deliberately a DIFFERENT model from
# BENCHMARK_MODEL_NAME, because free-tier quota is counted per model per day.
# Learned the hard way on launch day: the live site briefly shared
# gemini-3.1-flash-lite with an evaluation run, the run spent the day's 500
# requests, and the public demo went dark for 15 hours. Separate models mean
# an evaluation can never starve the demo, or the other way round.
#
# Read from the environment first, so the deployed service can be moved to
# another model with `gcloud run services update --update-env-vars
# GEMINI_MODEL_NAME=...` -- no rebuild -- if this one's quota or availability
# changes. (gemini-3.6-flash is NOT a good choice: 20 requests/day, shared
# with the original research-paper site on the same key.)
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-3.5-flash-lite")

# Model used by compare_rag.py for BOTH arms of the semantic-vs-agentic
# benchmark. Separate from GEMINI_MODEL_NAME for two reasons:
#
#  1. Fairness. The comparison is about retrieval strategy, so both arms must
#     run on an identical model -- otherwise the result measures the models.
#     Pinning it here makes that impossible to get wrong by accident.
#  2. Quota. Free-tier Gemini quota is per-model-per-day, and the benchmark is
#     request-hungry (an agentic run spends several requests per question).
#     Pointing it at a different model from the live app means a benchmark run
#     cannot exhaust the quota the deployed app depends on.
#
# gemini-3.6-flash allows only 20 requests/day on the free tier, which one
# benchmark run would blow through; the lite models have far more headroom.
#
# "Far more" is 500/day, measured from the 429 payload:
#     GenerateRequestsPerDayPerProjectPerModel-FreeTier, quotaValue: 500
# Worth budgeting for, because the evaluation suite is hungrier than it looks:
#     evaluate.py --generate   55 calls   (one per question)
#     closed_book.py          110 calls   (both arms, all questions)
#     judge.py                110 calls   (55 answers x 2 passes)
# That is 275 for one clean pass, so roughly one full re-run per day before
# the cap bites -- and a re-run after fixing a label costs the same again.
# This is exactly why generated answers are cached (eval/.answers_cache.json)
# and why `evaluate.py --from-cache` exists: re-scoring cached answers after
# improving a heuristic costs nothing, and is the difference between fixing a
# scoring bug today and waiting until tomorrow to see the corrected number.
BENCHMARK_MODEL_NAME = "gemini-3.1-flash-lite"

# --- Retrieval -------------------------------------------------------------
DEFAULT_TOP_K = 5

# --- Evaluation --------------------------------------------------------
TEST_QUESTIONS_PATH = PROJECT_ROOT / "eval" / "test_questions.json"
EVAL_RESULTS_PATH = PROJECT_ROOT / "eval" / "results.md"
COMPARISON_RESULTS_PATH = PROJECT_ROOT / "eval" / "comparison.md"  # compare_rag.py
BASELINE_RESULTS_PATH = PROJECT_ROOT / "eval" / "baselines.md"     # baselines.py
CLOSED_BOOK_RESULTS_PATH = PROJECT_ROOT / "eval" / "closed_book.md"  # closed_book.py
SWEEP_RESULTS_PATH = PROJECT_ROOT / "eval" / "sweep.md"            # sweep.py
ROBUSTNESS_RESULTS_PATH = PROJECT_ROOT / "eval" / "robustness.md"  # robustness.py
JUDGE_RESULTS_PATH = PROJECT_ROOT / "eval" / "judge.md"            # judge.py
# Cache of generated answers, so judge.py does not pay to regenerate them.
ANSWER_CACHE_PATH = PROJECT_ROOT / "eval" / ".answers_cache.json"
EVAL_K_VALUES = [1, 3, 5]  # report precision/hit rate at each of these k values

# --- Monitoring / telemetry ------------------------------------------------
# Append-only event log of every question the system answers (see telemetry.py).
TELEMETRY_LOG_PATH = PROJECT_ROOT / "data" / "telemetry" / "events.jsonl"
TELEMETRY_ENABLED = True

# Below this top-1 cosine similarity, retrieval is treated as "weak" -- the
# index had nothing that really matched the question.
#
# This number is measured, not guessed (`python eval/measure_threshold.py`).
# Running 10 on-topic questions and 8 deliberately off-topic ones ("What is
# the capital of Brazil?") through retrieval gave these top-1 scores on the
# 23-book corpus:
#     on-topic  : min 0.478, median 0.669, max 0.765
#     off-topic : min 0.147, median 0.235, max 0.524
# Unlike the research papers this project started on, the groups OVERLAP.
# "Write a poem about the ocean" scores 0.524 -- novels and Poe's tales are
# full of the sea -- and "What houses exist at Hogwarts?" scores 0.441,
# because "houses" is an ordinary word in literature. A technical corpus
# shares no vocabulary with off-topic questions; a literary one shares a lot.
# So 0.46 is the cut that gets the fewest wrong: 1 of 18 (the ocean poem).
# Re-measure if the corpus or the embedding model changes.
#
# KNOWN LIMIT, measured and left in deliberately rather than tuned away.
# Even that partial separation holds only for questions that are off-topic in
# VOCABULARY. evaluate.py runs 16 questions that are on-topic in wording but
# unanswerable from the books ("What was Sherlock Holmes's blood type?",
# "Who is finally revealed as the murderer of Edwin Drood?" -- Dickens died
# before writing the answer), and 14 of the 16 score ABOVE this threshold.
# The Drood question scores 0.749, higher than 73 of the 77 answerable ones.
# (On the research papers it was 14 of 15. Same finding, new corpus.)
#
# So this threshold detects "the user asked about something else entirely",
# not "the books cannot answer this". The hallucination_risk flag built on it
# in telemetry.py inherits that blind spot, and the Activity view should not
# be read as catching realistic unanswerable questions.
#
# Raising the threshold does not fix it: to catch the Drood question it would
# have to sit above almost every genuine question too. The signal is not there
# to be recovered by tuning, because a question and a passage can be about
# exactly the same thing while the passage still fails to contain the answer.
# Cosine similarity measures aboutness, not answerhood. The defences that do
# work are the LLM grader (grader.py) and the model's own refusal behaviour,
# which evaluate.py --generate and crag_vs_rag.py measure directly.
LOW_CONFIDENCE_THRESHOLD = 0.46

# --- Agentic retrieval (the comparison arm; see agent_rag.py) --------------
# How many model turns the search loop may take before it is cut off. Each
# turn is a full API round trip, so this is the cost ceiling per question:
# without it, a model that keeps searching runs up cost indefinitely.
AGENT_MAX_TURNS = 8
AGENT_GREP_MAX_RESULTS = 30    # cap on matches returned by one grep call
AGENT_READ_MAX_LINES = 120     # cap on lines returned by one read call

# A count cap alone is NOT enough, and getting this wrong is expensive. The
# exported text is one paragraph per line, so a single "line" can be 3000+
# chars -- 30 matched lines came back as 127,000 characters in testing, which
# went straight into the context window and cost ~113k input tokens for one
# question. Every tool output therefore needs a byte budget as well as a count
# budget (production harnesses do both: Pi caps grep at 100 matches AND 50KB).
AGENT_GREP_MAX_CHARS = 12000   # total budget for one grep result
AGENT_GREP_LINE_CHARS = 320    # per-match preview; read_book fetches the rest
AGENT_READ_MAX_CHARS = 12000   # total budget for one read result

# Free-tier Gemini rate-limits per minute as well as per day, so any batch run
# has to pace itself or it will die on 429s partway through and waste the quota
# it already spent. Measured from the 429 payload rather than assumed: the
# limit is per-model, and gemini-3.1-flash-lite reports
#     GenerateRequestsPerMinutePerProjectPerModel-FreeTier, quotaValue: 15
# so a batch script needs at least 60/15 = 4 seconds between calls. Scripts
# take a --pause flag for this; the retry below is the safety net, not the plan.
API_RATE_LIMIT_RPM = 15
API_MIN_PAUSE_SECONDS = 60 / API_RATE_LIMIT_RPM  # 4.0
API_RETRY_ATTEMPTS = 5
API_RETRY_BASE_SECONDS = 20

# --- Corrective RAG (see grader.py / crag.py) ------------------------------
# How many chunks must be graded "relevant" before the system answers straight
# away. Below this, it retrieves deeper and re-grades once before deciding.
#
# 2 rather than 1 on purpose. With top_k=5 a healthy retrieval usually yields
# 2-4 relevant chunks, so 1 would almost never trigger the correction and CRAG
# would reduce to plain RAG plus an extra API call. This is the main knob worth
# sweeping once there are enough questions to separate the settings.
CRAG_MIN_RELEVANT = 2

# How far down the ranked list to look when the first pass was too thin. The
# retrieval itself is a local FAISS search and costs nothing; only the re-grade
# costs a request. Deeper also surfaces MORE BOOKS, which is the one lever
# Stage 1 has against the measured multi_book coverage of 0.37.
CRAG_DEEP_TOP_K = 15

# Hard ceiling on retrieval attempts per question (initial + deepened). Without
# it a stubborn question could loop; with it the worst case is a known 3 API
# calls (grade, re-grade, answer).
CRAG_MAX_ATTEMPTS = 2
