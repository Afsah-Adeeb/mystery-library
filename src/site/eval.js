/* Evaluation page: every number comes from eval/summary.json (via /api/evaluation),
 * (each question's similarity score included). Nothing is typed in by
 * hand except the one-off label experiment in section 07, which is not in the summary.
 *
 * Every bar shares one 0-to-1 scale, carries its 95% interval as a whisker, and
 * prints its value beside it, so nothing depends on reading a colour or a length. */

const $ = (s, r = document) => r.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const f2 = v => (v ?? 0).toFixed(2);
const ciText = m => m && m.n ? `[${f2(m.lo)}–${f2(m.hi)}]` : "";

/* ------------------------------------------------------------ tooltip */

const tip = $("#tip");
document.addEventListener("pointerover", e => {
  const el = e.target.closest("[data-tip]");
  if (!el) return;
  tip.innerHTML = el.dataset.tip;
  tip.classList.add("on");
});
document.addEventListener("pointermove", e => {
  if (!tip.classList.contains("on")) return;
  tip.style.left = `${e.clientX}px`;
  tip.style.top = `${e.clientY}px`;
});
document.addEventListener("pointerout", e => {
  if (e.target.closest("[data-tip]")) tip.classList.remove("on");
});

/* ------------------------------------------------------------ pieces */

function tile({ n, ci, k, s, accent = false, warm = false }) {
  return `<div class="tile${warm ? " warm" : ""}">
    <span class="n${accent ? " accent" : ""}">${n}</span>
    <span class="ci">${ci || "&nbsp;"}</span>
    <span class="k">${k}</span>
    <span class="s">${s}</span>
  </div>`;
}

function barRows(rows) {
  return rows.map(r => {
    const m = r.m || {};
    const tipHtml = `<b>${esc(r.label)}</b><br>${f2(m.value)} ${ciText(m)}${m.n ? ` · n=${m.n}` : ""}`;
    return `<div class="bar-row">
      <span class="bar-label">${esc(r.label)}${r.sub ? `<small>${esc(r.sub)}</small>` : ""}</span>
      <span class="bar-track" data-tip="${esc(tipHtml)}">
        <span class="fill${r.hero ? " main" : ""}" data-w="${(m.value || 0) * 100}" style="width:0"></span>
        ${m.n ? `<span class="whisker" style="left:${m.lo * 100}%; width:${(m.hi - m.lo) * 100}%"></span>` : ""}
      </span>
      <span class="bar-val">${f2(m.value)} <small>${ciText(m)}</small></span>
    </div>`;
  }).join("");
}
const axis = compact => `<div class="axis${compact ? " compact" : ""}"><span></span><span><i>0</i><i>0.25</i><i>0.5</i><i>0.75</i><i>1</i></span><span></span></div>`;

function grow() {   // bars slide out to their value once drawn
  requestAnimationFrame(() => document.querySelectorAll(".fill[data-w]").forEach(el => { el.style.width = `${el.dataset.w}%`; }));
}

/* ------------------------------------------------------------ sections */

function hero(s) {
  const r = s.retrieval || {}, b = (s.baselines || {}).arms || {};
  const total = (r.n_answerable || 0) + (r.n_unanswerable || 0);
  $("#ev-lede").textContent = `${total} hand-labelled questions: ${r.n_answerable} the books can answer, and ${r.n_unanswerable} trick questions they deliberately cannot. Every number carries a 95% confidence interval, including the ones that don't flatter the system.`;
  $("#report-meta").textContent = `${total} questions · updated ${(r.updated || "").slice(0, 10)}`;
  const cr = r.correct_refusal;
  $("#tiles").innerHTML = [
    tile({ n: f2(r["hit@5"]?.value), ci: ciText(r["hit@5"]), k: "Right book in the top 5", s: "of the passages handed to the model", accent: true }),
    tile({ n: f2(r["hit@1"]?.value), ci: ciText(r["hit@1"]), k: "Right book ranked first", s: "the very first passage was from it" }),
    tile({ n: cr ? `${Math.round(cr.value * cr.n)}/${cr.n}` : "—", ci: ciText(cr), k: "Trick questions declined", s: "it never invented an answer" }),
    tile({ n: f2(b.random?.hit?.value), ci: ciText(b.random?.hit), k: "Random floor", s: "what five random passages score" }),
  ].join("");
}

function baselines(s) {
  const r = s.retrieval || {}, b = (s.baselines || {}).arms || {};
  $("#bars-baselines").innerHTML = barRows([
    { label: "This system", sub: "semantic search", m: r["hit@5"], hero: true },
    { label: "Keyword search", sub: "BM25", m: b.bm25?.hit },
    { label: "Random", sub: "5 random passages", m: b.random?.hit },
  ]) + axis(false);
  const sem = r["hit@5"], bm = b.bm25?.hit;
  if (sem && bm) {
    $("#note-baselines").textContent = bm.hi >= sem.lo && sem.hi >= bm.lo
      ? `Keyword search ties it (${f2(bm.value)} against ${f2(sem.value)}; the intervals overlap). Book questions are full of exact names, “Rouletabille”, “Speckled Band”, that keyword search matches perfectly. The two miss different questions, which points at combining them.`
      : `The intervals do not overlap, so the gap over keyword search is real.`;
  }
}

const TYPE_NAMES = { simple: "Simple", paraphrase: "Reworded", comparison: "Comparison", multi_book: "Multi-book" };
function byType(s) {
  const t = (s.retrieval || {}).by_type || {};
  const rows = key => Object.entries(TYPE_NAMES).filter(([k]) => t[k]).map(([k, name]) => ({
    label: name, sub: `${t[k].n} questions`, m: t[k][key], hero: true,
  }));
  $("#bars-type-hit").innerHTML = barRows(rows("hit")) + axis(true);
  $("#bars-type-cov").innerHTML = barRows(rows("coverage")) + axis(true);
}

function answers(s) {
  const r = s.retrieval || {};
  if (!r.fact_coverage) { $("#answer-tiles").innerHTML = `<p class="ev-sub">No generated answers yet.</p>`; return; }
  const cr = r.correct_refusal;
  $("#answer-tiles").innerHTML = [
    tile({ n: cr ? `${Math.round(cr.value * cr.n)}/${cr.n}` : "—", ci: ciText(cr), k: "Trick questions declined", s: "correctly said the books don't say" }),
    tile({ n: f2(r.over_refusal?.value), ci: ciText(r.over_refusal), k: "Real questions declined", s: "lower is better; the weakness", warm: true }),
    tile({ n: f2(r.fact_coverage?.value), ci: ciText(r.fact_coverage), k: "Required facts present", s: "checked against the book text" }),
  ].join("");
}

function robustness(s) {
  const v = (s.robustness || {}).variants || {};
  const NAMES = { original: ["As written", "careful English"], typo: ["With typos", "one every ~12 letters"],
                  casual: ["Casual", "lower case, no polish"], keywords: ["Keywords", "search-box style"] };
  $("#bars-robust").innerHTML = barRows(Object.entries(NAMES).filter(([k]) => v[k]).map(([k, [label, sub]]) => ({
    label, sub, m: v[k].hit, hero: k === "original",
  }))) + axis(true);
}

function heat(s) {
  const sw = s.sweep;
  if (!sw) { $("#heat").innerHTML = `<p class="ev-sub">Sweep not run yet.</p>`; return; }
  const vals = Object.values(sw.grid).map(g => g.hit);
  const lo = Math.min(...vals), hi = Math.max(...vals);
  let html = `<span></span>` + sw.top_ks.map(k => `<span class="h">top ${k}</span>`).join("");
  for (const c of sw.chunk_sizes) {
    html += `<span class="h row">${c.toLocaleString()} chars</span>`;
    for (const k of sw.top_ks) {
      const g = sw.grid[`${c}x${k}`];
      const a = 0.12 + 0.73 * ((g.hit - lo) / ((hi - lo) || 1));
      const live = c === sw.committed.chunk_size && k === sw.committed.top_k;
      const tipHtml = `<b>${c} chars, top ${k}${live ? " · live" : ""}</b><br>Right book: ${f2(g.hit)} · MRR ${f2(g.mrr)} · books reached ${f2(g.coverage)}`;
      html += `<span class="cell${a > 0.5 ? " dark" : ""}${live ? " live" : ""}" style="background: rgba(176,80,28,${a.toFixed(2)})"
                data-tip="${esc(tipHtml)}">${f2(g.hit)}</span>`;
    }
  }
  $("#heat").innerHTML = html;
}

function pairs() {
  const P = [["Right book first", 0.65, 0.78], ["MRR", 0.74, 0.84], ["Right book in top 5", 0.88, 0.92]];
  $("#pairs").innerHTML = P.map(([name, a, b]) => `
    <div class="pair"><h4>${name}</h4>
      <div class="pr"><span>Without</span><span class="bar-track" data-tip="<b>${name}</b><br>without the label: ${a.toFixed(2)}"><span class="fill" data-w="${a * 100}" style="width:0"></span></span><b>${a.toFixed(2)}</b></div>
      <div class="pr"><span>With</span><span class="bar-track" data-tip="<b>${name}</b><br>with the label: ${b.toFixed(2)}"><span class="fill main" data-w="${b * 100}" style="width:0"></span></span><b>${b.toFixed(2)}</b></div>
    </div>`).join("");
}

/* ------------------------------------------------------------ the dot strip */

function dots(points) {
  if (!points.length) { $("#dots").innerHTML = `<p class="ev-sub">No cached run to plot.</p>`; return; }
  const W = 900, L = 150, R = 30, rowY = { true: 52, false: 128 }, H = 236;
  const xs = points.map(p => p.score);
  const x0 = Math.floor(Math.min(...xs) * 20) / 20, x1 = Math.ceil(Math.max(...xs) * 20) / 20;
  const X = v => L + (v - x0) / (x1 - x0) * (W - L - R);
  const jitter = id => { let h = 0; for (const ch of id) h = (h * 31 + ch.charCodeAt(0)) >>> 0; return ((h % 1000) / 1000 - 0.5) * 40; };

  let svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Similarity of every test question, answerable versus trick">`;
  for (let t = Math.ceil(x0 * 10) / 10; t <= x1 + 1e-9; t += 0.1) {
    svg += `<g class="tick"><line x1="${X(t)}" x2="${X(t)}" y1="18" y2="${H - 26}"/><text x="${X(t)}" y="${H - 8}" text-anchor="middle">${t.toFixed(1)}</text></g>`;
  }
  svg += `<text class="row-label" x="0" y="${rowY.true + 4}">Answerable</text>`;
  svg += `<text class="row-label" x="0" y="${rowY.false + 4}">Trick questions</text>`;

  const drood = points.find(p => /Edwin Drood/.test(p.question) && !p.answerable);
  for (const p of points) {
    const cx = X(p.score), cy = rowY[p.answerable] + jitter(p.id);
    const fill = p.answerable ? "#9C9086" : "#C8632A";
    const tipHtml = `<b>${esc(p.question)}</b><br>${p.answerable ? "answerable" : "trick question"} · similarity ${p.score.toFixed(2)}`;
    svg += `<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="5" fill="${fill}" stroke="#FDFCFA" stroke-width="1.5" data-tip="${esc(tipHtml)}"/>`;
  }
  if (drood) {
    const cx = X(drood.score), cy = rowY.false + jitter(drood.id);
    svg += `<circle cx="${cx}" cy="${cy}" r="10" fill="none" stroke="#1E1A17" stroke-width="1.5"/>`;
    // Labelled BELOW the trick-question row: above it, the label ran into the answerable dots.
    svg += `<line x1="${cx}" y1="${cy + 10}" x2="${cx}" y2="${cy + 30}" stroke="#1E1A17" stroke-width="1"/>`;
    svg += `<text class="callout" x="${cx}" y="${cy + 46}" text-anchor="end">“Who killed Edwin Drood?” ${drood.score.toFixed(2)}</text>`;
  }
  svg += `</svg>`;
  $("#dots").innerHTML = svg;

  if (drood) {
    const ans = points.filter(p => p.answerable);
    const below = ans.filter(p => p.score < drood.score).length;
    $("#note-dots").textContent = `Dickens died before revealing who killed Edwin Drood, so the book cannot answer it. Yet that question looks more similar to its passages than ${below} of the ${ans.length} questions the books do answer. A similarity score measures whether a passage is about the question, never whether it answers it. Only a model reading the passage can tell, which is why every passage is graded before an answer is written.`;
  }
}

/* ------------------------------------------------------------ boot */

(async () => {
  try {
    const { available, summary } = await (await fetch("/api/evaluation")).json();
    if (!available) { $("#tiles").innerHTML = `<div class="loading-note">No evaluation has been run yet.</div>`; return; }
    hero(summary); baselines(summary); byType(summary); answers(summary); robustness(summary); heat(summary); pairs();
    grow();
    dots((summary.retrieval || {}).points || []);
  } catch {
    $("#tiles").innerHTML = `<div class="loading-note">Could not load the results.</div>`;
  }
})();
