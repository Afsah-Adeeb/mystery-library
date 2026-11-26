/* Front end for the RAG API.
 *
 * No framework and no build step, on purpose: the whole page is four views,
 * one form and a handful of fetches. A bundler would add a toolchain and a
 * node_modules to a project whose substance is Python.
 *
 * The only non-obvious part is the ask flow. /api/ask returns a Server-Sent
 * Events stream rather than a JSON body, because the corrective pipeline has
 * stages worth watching -- the grader's verdict arrives before the answer
 * does. Each `phase` event appends a line to the trace; the final `done`
 * event carries the answer, sources and timings.
 */

const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const state = {
  sessionId: Math.random().toString(36).slice(2, 12),
  busy: false,
  loaded: {},
};

/* ------------------------------------------------------------ navigation */

function show(view) {
  $$(".view").forEach(v => v.classList.toggle("is-active", v.id === `view-${view}`));
  $$(".nav-link").forEach(b => b.classList.toggle("is-active", b.dataset.view === view));
  window.scrollTo({ top: 0, behavior: "instant" });

  // Views fetch once, then stay put. Re-fetching on every click would make
  // the nav feel slower than it is for data that changes at most per answer.
  if (view === "corpus"     && !state.loaded.corpus)     loadCorpus();
  if (view === "evaluation" && !state.loaded.evaluation) loadEvaluation();
  if (view === "activity")  loadActivity();   // live: always refresh
}

$$("[data-view]").forEach(el => {
  el.addEventListener("click", e => { e.preventDefault(); show(el.dataset.view); });
});

/* ------------------------------------------------------------------- ask */

const esc = s => String(s ?? "").replace(/[&<>"']/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* The model replies in light markdown. Rendering it with a library would mean
 * shipping one for bold, lists and paragraphs, so this covers exactly what the
 * answers actually contain -- and escapes first, so nothing the model writes
 * can inject markup. */
function renderMarkdown(src) {
  const lines = esc(src).split("\n");
  let html = "", list = null;

  const inline = t => t
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>")   // *The Moonstone*
    .replace(/`([^`]+)`/g, "<code>$1</code>");

  for (const raw of lines) {
    const line = raw.trim();
    const bullet = line.match(/^[-*]\s+(.*)$/);
    const numbered = line.match(/^\d+[.)]\s+(.*)$/);

    if (bullet || numbered) {
      const want = bullet ? "ul" : "ol";
      if (list !== want) { if (list) html += `</${list}>`; html += `<${want}>`; list = want; }
      html += `<li>${inline((bullet || numbered)[1])}</li>`;
      continue;
    }
    if (list) { html += `</${list}>`; list = null; }
    if (line) html += `<p>${inline(line)}</p>`;
  }
  if (list) html += `</${list}>`;
  return html;
}

// What the page shows while each step RUNS (see ask() for why).
const RUNNING = {
  retrieve: "Searching the library",
  grade:    "Grading each passage",
  regrade:  "Grading the new passages",
  answer:   "Writing the answer",
  deepen:   "Too little survived — searching deeper",
  refuse:   "Nothing relevant found — declining",
};

function stepRow(label, extra = "") {
  return `<div class="step is-live"><span class="tick"></span>
            <span class="lbl">${esc(label)}</span>
            <span class="grades">${extra}</span></div>`;
}

async function ask(question) {
  if (state.busy || !question.trim()) return;
  state.busy = true;
  $("#send").disabled = true;
  $("#intro").classList.add("is-hidden");
  $("#suggestions").classList.add("is-hidden");
  $("#q").value = "";

  const turn = document.createElement("article");
  turn.className = "turn";
  turn.innerHTML = `<h2 class="turn-q">${esc(question)}</h2>
                    <div class="trace"></div>
                    <div class="body"></div>`;
  $("#thread").appendChild(turn);
  turn.scrollIntoView({ behavior: "smooth", block: "start" });

  const trace = $(".trace", turn);
  const body  = $(".body", turn);

  const finishLastStep = () => {
    const live = $$(".step.is-live", trace).pop();
    if (live) { live.classList.remove("is-live"); live.classList.add("is-done");
                $(".tick", live).textContent = "✓"; }
  };
  const startStep = label => trace.insertAdjacentHTML("beforeend", stepRow(label));
  const noteOnLiveStep = text => {
    const live = $$(".step.is-live", trace).pop();
    if (live) $(".grades", live).textContent = text;
  };

  // The server reports a step when it FINISHES. Showing only finished steps
  // left the page blank while each one ran -- and for ~30 s on a cold start --
  // which read as "stuck". So the page shows the step that is RUNNING: the
  // first one immediately, and each next one as soon as the previous ends.
  // After grading, the server says which branch the graph took (`next`).
  startStep(RUNNING.retrieve);
  const coldStartHint = setTimeout(() => noteOnLiveStep(
    "waking the server up — the first question after a quiet spell takes ~30 s"), 6000);

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // No top_k or pipeline: the server defaults to corrective RAG at the
      // configured depth. Both remain parameters on /api/ask for the
      // evaluation scripts; neither is a decision to put to a visitor.
      body: JSON.stringify({ question, session_id: state.sessionId }),
    });
    if (!res.ok) throw new Error(`Server returned ${res.status}`);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // SSE frames are separated by a blank line; a partial frame stays in
      // the buffer until the rest of it arrives.
      const frames = buffer.split("\n\n");
      buffer = frames.pop();

      for (const frame of frames) {
        const evt  = (frame.match(/^event: (.*)$/m) || [])[1];
        const data = (frame.match(/^data: (.*)$/m) || [])[1];
        if (!evt || !data) continue;
        const payload = JSON.parse(data);

        if (evt === "phase") {
          clearTimeout(coldStartHint);
          if (payload.node === "retrieve") noteOnLiveStep("");
          if (payload.grades) {
            const g = payload.grades;
            noteOnLiveStep(`${g.relevant || 0} relevant · ${g.partial || 0} partial · ${g.irrelevant || 0} irrelevant`);
          }
          finishLastStep();
          const next = { retrieve: "grade", deepen: "regrade" }[payload.node] || payload.next;
          if (next && RUNNING[next]) startStep(RUNNING[next]);
        } else if (evt === "error") {
          clearTimeout(coldStartHint);
          finishLastStep();
          body.innerHTML = `<div class="refusal"><b>Something went wrong.</b><br>${esc(payload.message)}</div>`;
        } else if (evt === "done") {
          finishLastStep();
          renderAnswer(body, payload);
        }
      }
    }
  } catch (err) {
    clearTimeout(coldStartHint);
    finishLastStep();
    body.innerHTML = `<div class="refusal"><b>Could not reach the server.</b><br>${esc(err.message)}</div>`;
  } finally {
    state.busy = false;
    $("#send").disabled = false;
    $("#q").focus();
  }
}

function renderAnswer(body, d) {
  const t = d.timings || {};
  // Milliseconds below a second, seconds above it. Retrieval is normally
  // ~200ms, but the very first question of a server process also pays for the
  // embedding model to load, which pushes it into the tens of seconds -- and
  // "10664 ms" reads as a bug where "10.7 s" reads as a fact.
  const dur = ms => ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`;

  const bits = [];
  if (t.retrieval_ms  != null) bits.push(`${dur(t.retrieval_ms)} retrieval`);
  if (t.grading_ms)            bits.push(`${dur(t.grading_ms)} grading`);
  if (t.generation_ms)         bits.push(`${dur(t.generation_ms)} generation`);
  if (d.api_calls)             bits.push(`${d.api_calls} API ${d.api_calls === 1 ? "call" : "calls"}`);

  const answerHtml = d.decision === "refuse"
    ? `<div class="refusal"><b>Declined.</b> ${esc(d.answer) ||
        "The graded passages did not contain an answer, so the model was never asked."}</div>`
    : `<div class="answer">${renderMarkdown(d.answer)}</div>`;

  const sources = (d.sources || []).map(s => `
    <div class="source">
      <div class="hd">${esc(s.book)} — ${esc(s.chapter)}<span>${s.score}</span></div>
      <div class="tx">${esc(s.text)}…</div>
    </div>`).join("");

  body.innerHTML = `
    ${answerHtml}
    ${sources ? `<details class="sources"><summary>Sources (${d.sources.length})</summary>${sources}</details>` : ""}
    <div class="meta">
      <span>${esc(bits.join(" · "))}</span>
      <span class="spacer"></span>
      ${d.query_id ? `<button class="vote" data-r="up"   title="Helpful">👍</button>
                      <button class="vote" data-r="down" title="Not helpful">👎</button>` : ""}
    </div>`;

  $$(".vote", body).forEach(btn => btn.addEventListener("click", () => {
    $$(".vote", body).forEach(b => b.classList.remove("is-set"));
    btn.classList.add("is-set");
    fetch("/api/feedback", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query_id: d.query_id, rating: btn.dataset.r }),
    }).catch(() => {});
  }));
}

$("#composer").addEventListener("submit", e => { e.preventDefault(); ask($("#q").value); });
$$(".chip").forEach(c => c.addEventListener("click", () => ask(c.dataset.q)));

/* ---------------------------------------------------------------- corpus */

async function loadCorpus() {
  const el = $("#corpus-body");
  try {
    const d = await (await fetch("/api/corpus")).json();
    state.loaded.corpus = true;
    $("#kicker-text").textContent =
      `Corrective RAG · ${d.total_books} books · ${d.total_chunks.toLocaleString()} passages`;

    el.innerHTML = `
      <div class="stats">
        <div class="stat"><div class="n">${d.total_books}</div><div class="k">Books</div></div>
        <div class="stat"><div class="n">${d.total_authors}</div><div class="k">Authors</div></div>
        <div class="stat"><div class="n">${d.total_chapters}</div><div class="k">Chapters &amp; stories</div></div>
        <div class="stat"><div class="n">${d.total_chunks.toLocaleString()}</div><div class="k">Searchable passages</div></div>
      </div>
      ${d.books.map(b => `
        <div class="row">
          <div class="t">${b.url ? `<a href="${esc(b.url)}" target="_blank" rel="noopener">${esc(b.title)}</a>` : esc(b.title)}
            <span class="a">${esc(b.author)}${b.year ? `, ${b.year}` : ""}</span></div>
          <div class="m">${b.chapters} chapters<br>${b.chunks} passages</div>
        </div>`).join("")}`;
  } catch {
    el.innerHTML = `<div class="note">Could not load the corpus.</div>`;
  }
}

/* ------------------------------------------------------------ evaluation */

const ci = (d, dp = 2) => d && d.n
  ? `${d.value.toFixed(dp)} <span style="color:var(--faint)">[${d.lo.toFixed(dp)}–${d.hi.toFixed(dp)}]</span>`
  : "—";

async function loadEvaluation() {
  const el = $("#evaluation-body");
  try {
    const { available, summary: s } = await (await fetch("/api/evaluation")).json();
    state.loaded.evaluation = true;
    if (!available) {
      el.innerHTML = `<div class="note">No evaluation has been run yet.</div>`;
      return;
    }

    const r = s.retrieval || {}, b = (s.baselines || {}).arms || {}, cb = s.closed_book || {};
    const cv = s.crag_vs_rag || {};
    // The counts come from the results themselves so they cannot drift from the test set.
    const sub = document.querySelector("#view-evaluation .view-sub");
    if (r.n_answerable) sub.textContent =
      `Measured against ${r.n_answerable + r.n_unanswerable} hand-labelled questions — ` +
      `${r.n_answerable} the corpus can answer, ${r.n_unanswerable} it deliberately cannot. ` +
      `Every figure carries a 95% confidence interval.`;
    let html = `
      <div class="stats">
        <div class="stat"><div class="n accent">${(r["hit@5"]?.value ?? 0).toFixed(2)}</div>
          <div class="k">Hit Rate@5</div><div class="s">n=${r.n_answerable || 0} questions</div></div>
        <div class="stat"><div class="n">${(r.mrr?.value ?? 0).toFixed(2)}</div>
          <div class="k">MRR</div><div class="s">how high the right book ranks</div></div>
        <div class="stat"><div class="n">${(b.bm25?.hit?.value ?? 0).toFixed(2)}</div>
          <div class="k">BM25 baseline</div><div class="s">keyword search</div></div>
        <div class="stat"><div class="n">${(b.random?.hit?.value ?? 0).toFixed(2)}</div>
          <div class="k">Random floor</div><div class="s">what anything scores</div></div>
      </div>`;

    if (r.correct_refusal) {
      html += `<div class="note"><b>It refuses when it should.</b> On
        ${r.n_unanswerable} questions the corpus genuinely cannot answer, it declined
        ${(r.correct_refusal.value * 100).toFixed(0)}% of the time` +
        (cb.cb_refuse_unans && !cb.stale
          ? ` — against ${(cb.cb_refuse_unans.value * 100).toFixed(0)}% for the same model
              with no documents supplied, which fabricated an answer to every one.`
          : `.`) + `</div>`;
    }

    if (b.bm25 && r["hit@5"]) {
      const overlap = b.bm25.hit.hi >= r["hit@5"].lo;
      html += `<div class="note"><b>Compared against a real baseline.</b>
        ${(r["hit@5"].value).toFixed(2)} against ${(b.bm25.hit.value).toFixed(2)} for BM25
        keyword search. ${overlap
          ? "The intervals overlap, so this test set cannot establish that the embeddings win overall — they lead most on reworded questions."
          : "The intervals do not overlap, so the gap is real."}</div>`;
    }

    if (cv.plain && cv.crag) {
      const rows = [
        ["Required facts present", "fact_coverage", 2],
        ["Wrongly refused (lower is better)", "over_refusal", 2],
        ["Correctly refused", "correct_refusal", 2],
        ["Model calls per question", "api_calls", 2],
        ["Seconds per answer", "latency_s", 1],
      ];
      html += `<h3 class="section-h">Corrective vs plain retrieval</h3>
        <div class="table-wrap"><table>
        <thead><tr><th></th><th>Plain</th><th>Corrective</th></tr></thead><tbody>` +
        rows.map(([label, k, d]) => `<tr><td>${label}</td>
          <td class="num">${ci(cv.plain[k], d)}</td>
          <td class="num">${ci(cv.crag[k], d)}</td></tr>`).join("") +
        `</tbody></table></div>
        <p class="view-sub" style="margin-top:.8rem">Grading passages costs roughly
         ${(cv.crag.api_calls.value / cv.plain.api_calls.value).toFixed(1)}× the model calls
         and ${(cv.crag.latency_s.value / cv.plain.latency_s.value).toFixed(1)}× the time. What it buys:
         it searches deeper when the first five passages are crowded out by near-duplicate books.</p>`;
    }

    if (r.by_type) {
      html += `<h3 class="section-h">By question type</h3><div class="table-wrap"><table>
        <thead><tr><th>Type</th><th>n</th><th>Hit@5</th><th>MRR</th><th>Books reached</th></tr></thead><tbody>` +
        Object.entries(r.by_type).map(([k, v]) => `<tr>
          <td>${esc(k.replace("_", "-"))}</td><td class="num">${v.n}</td>
          <td class="num">${ci(v.hit)}</td><td class="num">${ci(v.mrr, 3)}</td>
          <td class="num">${ci(v.coverage)}</td></tr>`).join("") +
        `</tbody></table></div>
        <p class="view-sub" style="margin-top:.8rem">A single average hides where it fails. Hit@5
         says a multi-book question succeeded the moment <em>one</em> right book appears; the last
         column says how many of the books it needed were actually reached.</p>`;
    }

    const rob = (s.robustness || {}).variants;
    if (rob) {
      html += `<h3 class="section-h">Robustness to badly-typed questions</h3><div class="table-wrap"><table>
        <thead><tr><th>Variant</th><th>Hit@5</th><th>Same top book</th></tr></thead><tbody>` +
        Object.entries(rob).map(([k, v]) => `<tr>
          <td>${esc(k)}</td><td class="num">${ci(v.hit)}</td>
          <td class="num">${k === "original" ? "—" : ci(v.same_top)}</td></tr>`).join("") +
        `</tbody></table></div>`;
    }

    el.innerHTML = html;
  } catch {
    el.innerHTML = `<div class="note">Could not load the evaluation results.</div>`;
  }
}

/* -------------------------------------------------------------- activity */

async function loadActivity() {
  const el = $("#activity-body");
  try {
    const d = await (await fetch("/api/metrics")).json();
    if (!d.available) {
      el.innerHTML = `<div class="note">Nothing logged yet. Ask a question and it will appear here.</div>`;
      return;
    }
    const s = d.summary || {};
    const max = Math.max(1, ...d.coverage.map(([, n]) => n));

    el.innerHTML = `
      <div class="stats">
        <div class="stat"><div class="n">${s.total_queries ?? 0}</div><div class="k">Questions answered</div></div>
        <div class="stat"><div class="n">${((s.median_total_ms ?? 0) / 1000).toFixed(1)}s</div><div class="k">Median response</div></div>
        <div class="stat"><div class="n">${(s.mean_top_score ?? 0).toFixed(2)}</div><div class="k">Mean retrieval score</div></div>
        <div class="stat"><div class="n">${s.hallucination_risk_count ?? 0}</div><div class="k">Flagged for review</div></div>
      </div>

      <h3 class="section-h">Which books get reached</h3>
      ${d.coverage.map(([name, n]) => `
        <div style="margin-bottom:.6rem">
          <div style="display:flex;justify-content:space-between;font-size:.83rem;margin-bottom:.25rem">
            <span>${esc(name)}</span><span style="color:var(--faint)">${n}</span></div>
          <div class="bar"><i style="width:${(n / max * 100).toFixed(0)}%"></i></div>
        </div>`).join("")}

      <h3 class="section-h">Recent questions</h3>
      ${d.recent.map(q => `
        <div class="row">
          <div class="t">${esc(q.question)} ${q.flagged ? '<span class="flag">flagged</span>' : ""}</div>
          <div class="m">${q.top_score} · ${(q.total_ms / 1000).toFixed(1)}s</div>
        </div>`).join("")}`;
  } catch {
    el.innerHTML = `<div class="note">Could not load activity.</div>`;
  }
}

/* Corpus counts feed the kicker in the hero, so fetch them at load. */
loadCorpus();
/* Start loading the search model now, while the visitor reads and types, so a
 * cold server is (nearly) warm by the time they press Enter. Fire and forget. */
fetch("/api/warmup").catch(() => {});
$("#q").focus();
