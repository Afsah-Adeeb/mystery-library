"""
Step 4: Pass retrieved chunks + the question to an LLM to produce an answer.

This is the "G" in RAG. Retrieval found the relevant text; this step asks
Gemini to read that text and write a grounded answer, instead of relying
on whatever it memorized during training.

PROMPT DESIGN
---------------
The prompt has two deliberate rules baked in:
  1. Only answer from the provided context (this is what makes it
     "retrieval-augmented" rather than just chatting with a generic LLM --
     the model's job is to synthesize the retrieved text, not recall facts
     from its own training data).
  2. Say so explicitly if the context doesn't contain the answer, instead
     of guessing. This matters a lot for evaluation later (Step 5): we want
     to be able to tell "hallucinated" apart from "correctly said I don't know."

The model is deliberately NOT asked to cite sources inline in the answer
text (no "[The Moonstone, Ch. 4]" scattered through the prose) -- that reads
as clutter compared to a normal AI chat answer. Grounding is still fully
checkable: the retrieved chunks (book and chapter metadata tracked all the
way from ingest.py) are returned alongside the answer and shown in a
collapsed "Sources" section by the UI, the same pattern ChatGPT and
Gemini use for citations.

WHY RULE 1 MATTERS MORE FOR THESE BOOKS
-----------------------------------------
The model has read Sherlock Holmes. Famous public-domain books are all over
its training data, so it could answer many questions here from memory --
sometimes correctly, sometimes with a confident blend of the book, a film
and a fan theory. "Only from the context" is what keeps every answer
traceable to a passage the reader can check. eval/closed_book.py measures
exactly how much the model knows WITHOUT the books, so the value the
retrieval adds is a number rather than a claim.

The model used is config.GEMINI_MODEL_NAME: on Gemini's free tier, fast,
and more than capable of summarising a handful of retrieved passages.
"""

import os
import time

from dotenv import load_dotenv
from google import genai

import config
from retrieve import retrieve, search

load_dotenv()  # reads GEMINI_API_KEY from a local .env file (see .env.example)

_client = None


class DailyQuotaExhausted(RuntimeError):
    """The free tier's per-day request quota is gone. Waiting will not help.

    Lives here, next to the Gemini client, because several unrelated callers
    need to catch it -- the agentic arm, the evaluation suite, and CRAG. It
    used to live in agent_rag.py, which meant every one of them had to import
    the agent machinery just to name an exception, and made it easy to define
    a second class with the same name that `except` clauses would miss.
    """


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not set. Copy .env.example to .env and add your key "
                "(get one free at https://aistudio.google.com/apikey)."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def build_prompt(question, retrieved_chunks):
    """Combine the question with retrieved context into one prompt for Gemini."""
    context_blocks = [chunk["text"] for chunk in retrieved_chunks]
    context = "\n\n---\n\n".join(context_blocks)

    return f"""You are a librarian answering questions about a collection of classic \
mystery and detective books (Sherlock Holmes, Father Brown, Poe, The Moonstone and \
others). Each passage below begins with the book and chapter it comes from.

Answer the question using ONLY the context below. Follow these rules:
- If the context does not contain enough information to answer, say so explicitly \
instead of guessing. Do NOT fill gaps from your own memory of these books, films or \
adaptations, even if you know the story.
- Write a clean, natural answer, like a normal AI chat assistant. You may name the \
book or story in a sentence, but do NOT insert bracketed citations or chapter \
references -- sources are shown separately by the UI.
- Be concise and specific: names, places and objects exactly as the book gives them.

Context:
{context}

Question: {question}

Answer:"""


def _extract_usage(response):
    """Pull token counts off a Gemini response, tolerating SDK shape changes.

    Token counts are how the monitoring layer reports cost, but they're
    metadata -- if a future SDK version renames these fields, that must not
    break answering. Missing counts simply show as unknown in the dashboard.
    """
    meta = getattr(response, "usage_metadata", None)
    if meta is None:
        return {"input_tokens": None, "output_tokens": None}
    return {
        "input_tokens": getattr(meta, "prompt_token_count", None),
        "output_tokens": getattr(meta, "candidates_token_count", None),
    }


# Short waits on purpose. The live page sits behind Firebase Hosting, which
# gives up on a request after 60 seconds, so a long backoff would turn a busy
# minute into a hard error anyway. The evaluation scripts have their own,
# longer retry (eval_core.call_with_retry) because nobody is waiting on them.
BUSY_RETRY_WAITS = (2, 5)


def _call_with_busy_retry(call):
    """Retry a model call when Gemini says it is busy (503/500), briefly.

    "This model is currently experiencing high demand" is Google's side and
    usually clears in seconds. Anything else -- a bad key, a daily quota --
    is raised at once, because waiting will not fix it.
    """
    for wait in BUSY_RETRY_WAITS + (None,):
        try:
            return call()
        except Exception as exc:  # noqa: BLE001
            busy = any(s in str(exc) for s in ("503", "UNAVAILABLE", "500", "INTERNAL"))
            if not busy or wait is None:
                raise
            time.sleep(wait)


def generate_with_usage(question, retrieved_chunks, model=None):
    """Answer from chunks, returning the text plus cost/latency metadata.

    This is the core call. It returns a dict rather than a bare string so the
    monitoring layer (telemetry.py) can record how long generation took and
    how many tokens it burned -- measured here, at the actual API boundary,
    rather than estimated by the caller.

    `model` overrides config.GEMINI_MODEL_NAME. compare_rag.py uses it to pin
    both arms of the benchmark to one model, so the comparison measures
    retrieval strategy rather than the difference between two models.

    Returns: {"answer": str, "generation_ms": float,
              "input_tokens": int|None, "output_tokens": int|None}
    """
    prompt = build_prompt(question, retrieved_chunks)
    client = _get_client()

    started = time.perf_counter()
    response = _call_with_busy_retry(lambda: client.models.generate_content(
        model=model or config.GEMINI_MODEL_NAME,
        contents=prompt,
    ))
    generation_ms = (time.perf_counter() - started) * 1000

    return {
        "answer": response.text,
        "generation_ms": generation_ms,
        **_extract_usage(response),
    }


def generate_answer_from_chunks(question, retrieved_chunks):
    """Ask Gemini to answer `question` using an already-retrieved list of chunks.

    Split out from generate_answer() so callers that already retrieved chunks
    (e.g. evaluate.py, which needs the chunks anyway for precision@k) don't
    pay for a second, redundant embedding + FAISS search of the same question.

    Thin wrapper over generate_with_usage() for callers that only want the text.
    """
    return generate_with_usage(question, retrieved_chunks)["answer"]


def answer_traced(question, top_k=config.DEFAULT_TOP_K, index=None, metadata=None, model=None):
    """Run the full pipeline and time each stage separately.

    Both front ends (cli.py, app.py) go through this so the monitoring layer
    sees identical fields no matter where a question came from. Splitting the
    two timings matters: retrieval and generation have wildly different cost
    profiles, and reporting only a combined number hides which one to optimize.

    Pass `index`/`metadata` to search a caller-built index instead of the
    committed one -- that's how app.py includes session-uploaded books.

    Returns: {"answer", "chunks", "retrieval_ms", "generation_ms",
              "input_tokens", "output_tokens"}
    """
    started = time.perf_counter()
    if index is not None:
        chunks = search(question, index, metadata, top_k=top_k)
    else:
        chunks = retrieve(question, top_k=top_k)
    retrieval_ms = (time.perf_counter() - started) * 1000

    result = generate_with_usage(question, chunks, model=model)
    return {"chunks": chunks, "retrieval_ms": retrieval_ms, **result}


def generate_answer(question, top_k=config.DEFAULT_TOP_K):
    """Retrieve relevant chunks, then ask Gemini to answer using only that context.

    Returns (answer_text, retrieved_chunks) so callers can show sources alongside the answer.
    """
    retrieved_chunks = retrieve(question, top_k=top_k)
    answer = generate_answer_from_chunks(question, retrieved_chunks)
    return answer, retrieved_chunks


if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) or "What killed Julia Stoner in The Speckled Band?"
    answer, sources = generate_answer(question)

    print(f"Question: {question}\n")
    print(f"Answer:\n{answer}\n")
    print("Sources used:")
    for chunk in sources:
        print(f"  - {chunk['source_book']} ({chunk['chapter']}, score={chunk['score']:.3f})")
