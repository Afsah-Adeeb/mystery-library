"""
HTTP API and web server for the RAG pipeline -- the replacement for app.py.

WHY THIS EXISTS ALONGSIDE app.py
----------------------------------
app.py is a Streamlit front end. Streamlit re-executes the entire script on
every interaction, which is fine for a prototype and awkward for a public
demo: it puts a ~2s round trip behind clicking a tab, gives no control over
the markup (styling has to be applied *around* Streamlit's DOM, and broke
outright when 1.62 rebuilt tabs on react-aria), and offers no natural way to
show a multi-step pipeline as it runs.

This module serves a hand-written page instead. The Python underneath is
untouched -- crag.py, retrieve.py and generate.py do not know this file
exists, exactly as they do not know app.py exists. Both front ends are
presentation over the same functions.

WHAT THE REWRITE ACTUALLY BUYS
--------------------------------
The interesting one is not speed, it is that the corrective flow becomes
*visible*. crag.py is a LangGraph, and LangGraph graphs can be streamed
node by node. So instead of one opaque spinner, /api/ask emits an event as
each stage completes:

    retrieving  ->  grading  ->  (deepening -> grading)  ->  generating

The grader's verdict arrives before the answer does, which means a visitor
watches the system decide that eight of fifteen passages are irrelevant and
go looking for more. That is the whole thesis of the project, and in the
Streamlit version it was summarised in a line of small text after the fact.

Streaming the graph rather than re-implementing its steps here also means
this file holds no retrieval or grading logic of its own -- if crag.py grows
a node, it shows up in the UI for free.
"""

import json
import queue
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "eval"))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse, StreamingResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

import config  # noqa: E402
import telemetry  # noqa: E402
from crag import crag_graph, route_after_grading  # noqa: E402
from ingest import book_title, chunk_body  # noqa: E402
from retrieve import load_metadata  # noqa: E402

WEB_DIR = Path(__file__).resolve().parent / "web"

app = FastAPI(title="The Mystery Library", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


# --- Pages -------------------------------------------------------------------

@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/warmup")
def warmup():
    """Load the embedding model and index now, before anyone has asked anything.

    Cloud Run scales to zero, so the first visitor after a quiet spell meets a
    fresh container, and loading the search model takes ~30 seconds. The page
    calls this the moment it opens, so the load happens while the visitor is
    still reading and typing rather than after they press Enter.

    It is a request rather than a background thread on purpose: Cloud Run only
    gives a container CPU while a request is open, so a thread started at boot
    would barely run between page load and the first question.
    """
    from retrieve import base_index_and_metadata
    base_index_and_metadata()
    return {"ready": True}


@app.get("/healthz")
def healthz():
    """Liveness probe. Deliberately does NOT touch the embedding model.

    Cloud Run's startup probe hits this, and a probe that waited on a ~35s
    torch import would fail the deployment before the app ever served
    anything.
    """
    return {"ok": True}


# --- Corpus ------------------------------------------------------------------

_pretty = book_title   # "The Moonstone.txt" -> "The Moonstone"


def _catalog():
    """Author, year and source link per file, as written by download_books.py."""
    try:
        with open(config.BOOK_CATALOG_PATH, encoding="utf-8") as f:
            return {b["file"]: b for b in json.load(f)}
    except (OSError, ValueError):
        return {}   # the corpus view still works, just without authors


@app.get("/api/corpus")
def corpus():
    """What is in the index. Reads metadata only -- no model, ~0.03s."""
    meta = load_metadata()
    by_book = {}
    for chunk in meta:
        entry = by_book.setdefault(chunk["source_book"], {"chunks": 0, "chapters": set()})
        entry["chunks"] += 1
        entry["chapters"].add(chunk["chapter"])

    catalog = _catalog()
    books = [{
        "title": _pretty(name),
        "file": name,
        "author": catalog.get(name, {}).get("author", ""),
        "year": catalog.get(name, {}).get("year"),
        "url": catalog.get(name, {}).get("url"),
        "chunks": vals["chunks"],
        "chapters": len(vals["chapters"]),
    } for name, vals in by_book.items()]
    # Oldest first: the order the genre was invented in.
    books.sort(key=lambda b: (b["year"] or 9999, b["title"]))
    return {
        "books": books,
        "total_books": len(books),
        "total_chunks": len(meta),
        "total_chapters": sum(b["chapters"] for b in books),
        "total_authors": len({b["author"] for b in books if b["author"]}),
    }


# --- Ask ---------------------------------------------------------------------

class AskRequest(BaseModel):
    question: str
    top_k: int = config.DEFAULT_TOP_K
    pipeline: str = "crag"          # "crag" | "plain"
    session_id: str = "web"


# Human-readable copy for each graph node, kept here rather than in the
# browser so the UI cannot drift from the graph it is describing.
PHASE_LABELS = {
    "retrieve": "Searching the library",
    "grade": "Grading each passage",
    "deepen": "Too little survived — searching deeper",
    "generate": "Writing the answer",
    "refuse": "Nothing relevant found — declining",
}


def _sse(event, payload):
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def _friendly_error(exc):
    """Turn an API failure into a sentence a visitor can act on.

    The raw text is a JSON blob from Google's SDK, which tells a visitor
    nothing except that something broke.
    """
    text = str(exc)
    if any(s in text for s in ("503", "UNAVAILABLE", "500", "INTERNAL")):
        return "The AI model is busy right now (Google reports high demand). Please try again in a minute."
    if "429" in text or "RESOURCE_EXHAUSTED" in text:
        return ("This free demo has used up its AI quota for now. "
                "Please try again later -- the limit resets daily.")
    return text[:400]


def _run_graph(question, top_k, pipeline, out):
    """Run the flow on a worker thread, pushing progress onto `out`.

    LangGraph's .stream() is a blocking generator, so it runs here rather than
    in the request handler; the handler drains the queue and forwards each
    item to the browser as it arrives. Anything raised is put on the queue as
    an error rather than killing the thread silently.
    """
    try:
        started = time.perf_counter()
        # The live model for every step, grading included. Left as None, the
        # grader would fall back to BENCHMARK_MODEL_NAME and share its quota
        # with evaluation runs -- see config.GEMINI_MODEL_NAME.
        state = {"question": question, "top_k": top_k,
                 "index": None, "metadata": None,
                 "model": config.GEMINI_MODEL_NAME}

        if pipeline == "plain":
            # Plain RAG is the baseline arm, kept so the two can be compared
            # live on the same question. It has no stages worth narrating.
            from generate import answer_traced
            out.put(("phase", {"node": "retrieve",
                               "label": PHASE_LABELS["retrieve"]}))
            result = answer_traced(question, top_k=top_k, model=config.GEMINI_MODEL_NAME)
            out.put(("phase", {"node": "generate",
                               "label": PHASE_LABELS["generate"]}))
            result["decision"] = "answer"
            result["api_calls"] = 1
        else:
            final = None
            for update in crag_graph().stream(state):
                for node, delta in update.items():
                    payload = {"node": node,
                               "label": PHASE_LABELS.get(node, node)}
                    # The grader's verdict is the most interesting thing the
                    # flow produces, so it is surfaced the moment it exists
                    # rather than waiting for the final answer.
                    #
                    # Counted from `labels` rather than read from a
                    # `grade_counts` key: the node returns the raw per-chunk
                    # labels and the counts are only assembled at the end of
                    # crag_answer(), which is too late to narrate.
                    if node == "grade" and delta.get("labels"):
                        labels = delta["labels"]
                        payload["grades"] = {
                            grade: labels.count(grade)
                            for grade in ("relevant", "partial", "irrelevant")
                        }
                        payload["graded"] = len(labels)
                    final = {**(final or {}), **delta}
                    # Tell the page what happens next, so it can show that
                    # step as running instead of sitting silent until it ends.
                    # Asks the graph's own router, so the page cannot drift
                    # from the real decision.
                    if node == "grade":
                        payload["next"] = route_after_grading(final)
                    out.put(("phase", payload))
            result = final or {}

        result["total_ms"] = (time.perf_counter() - started) * 1000
        out.put(("result", result))
    except Exception as exc:  # noqa: BLE001
        out.put(("error", {"message": _friendly_error(exc)}))
    finally:
        out.put((None, None))


@app.post("/api/ask")
def ask(req: AskRequest):
    question = (req.question or "").strip()
    if not question:
        raise HTTPException(400, "Question is empty.")
    top_k = max(1, min(int(req.top_k), 15))

    def stream():
        out = queue.Queue()
        worker = threading.Thread(
            target=_run_graph, args=(question, top_k, req.pipeline, out),
            daemon=True)
        worker.start()

        result = None
        while True:
            kind, payload = out.get()
            if kind is None:
                break
            if kind == "result":
                result = payload
                continue
            if kind == "error":
                yield _sse("error", payload)
                return
            yield _sse("phase", payload)

        if result is None:
            yield _sse("error", {"message": "The pipeline returned nothing."})
            return

        chunks = result.get("sent_chunks") or result.get("chunks") or []
        sources = [{
            "book": _pretty(c["source_book"]),
            "chapter": c.get("chapter", ""),
            "score": round(float(c.get("score", 0.0)), 3),
            # Without the "Book — Chapter" label line: the UI shows those
            # in the source's header already.
            "text": chunk_body(c)[:600],
        } for c in chunks]

        # Same event log the Streamlit front end writes, so the Activity view
        # covers whoever used the system rather than whichever UI they used.
        query_id = None
        try:
            query_id = telemetry.log_query(
                question=question,
                answer=result.get("answer", ""),
                retrieved_chunks=result.get("chunks") or chunks,
                retrieval_ms=result.get("retrieval_ms", 0.0),
                generation_ms=result.get("generation_ms", 0.0),
                top_k=top_k, usage=result, surface="web",
                session_id=req.session_id,
            )
        except Exception:  # noqa: BLE001  monitoring must never break answering
            pass

        yield _sse("done", {
            "query_id": query_id,
            "answer": result.get("answer", ""),
            "decision": result.get("decision", "answer"),
            "grades": result.get("grade_counts"),
            "deepened": bool(result.get("deepened")),
            "kept": result.get("kept_chunks"),
            "sources": sources,
            "timings": {
                "retrieval_ms": round(result.get("retrieval_ms") or 0),
                "grading_ms": round(result.get("grading_ms") or 0),
                "generation_ms": round(result.get("generation_ms") or 0),
                "total_ms": round(result.get("total_ms") or 0),
            },
            "api_calls": result.get("api_calls"),
        })

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


# --- Feedback ----------------------------------------------------------------

class FeedbackRequest(BaseModel):
    query_id: str
    rating: str


@app.post("/api/feedback")
def feedback(req: FeedbackRequest):
    try:
        telemetry.log_feedback(req.query_id, req.rating)
    except Exception:  # noqa: BLE001
        pass
    return {"ok": True}


# --- Read-only views ---------------------------------------------------------

@app.get("/api/metrics")
def metrics():
    """Live telemetry: what the system actually did, on real questions."""
    try:
        records = telemetry.build_records()
        summary = telemetry.summarize(records)
    except Exception:  # noqa: BLE001
        return {"available": False}

    if not records:
        return {"available": False}

    # summarize() already counts per-book hits; recomputing them here would be
    # a second implementation of the same thing, free to drift.
    coverage = [(_pretty(name), n)
                for name, n in (summary.get("book_hits") or {}).items()]
    coverage.sort(key=lambda kv: -kv[1])

    # Counter is not JSON-serialisable in a way the browser wants, and it has
    # already been flattened into `coverage` above.
    summary = {k: v for k, v in summary.items() if k != "book_hits"}

    return {
        "available": True,
        "summary": summary,
        "coverage": coverage,
        "recent": [{
            "question": r.get("question", "")[:160],
            "top_score": round(r.get("top_score") or 0, 3),
            "total_ms": round(r.get("total_ms") or 0),
            "flagged": bool(r.get("hallucination_risk")),
        } for r in records[-25:][::-1]],
    }


@app.get("/api/evaluation")
def evaluation():
    """The offline evaluation results, as written by the eval suite."""
    import eval_core
    data = eval_core.read_summary()
    data.pop("_test", None)
    return {"available": bool(data), "summary": data}


if __name__ == "__main__":
    import os

    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0",
                port=int(os.environ.get("PORT", 8000)), reload=False)
