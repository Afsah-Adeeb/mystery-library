/* Mystery Library mock-up: a library you can open, read, and ask.
 *
 * Library view: a shelf of 23 books. Tap one -> a tap ripple, the cover grows
 * to fill the panel, and the book opens. Reader view: the whole book, by
 * chapter, scrolling; questions go to the corrective RAG flow searching ONLY
 * the open book, and the answer appears in the chat, never on the page.
 * Read Aloud speaks from wherever you are, lighting each word. */

const $  = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"']/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const store = {
  get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode */ } },
};

const SESSION = Math.random().toString(36).slice(2, 10);
const state = { books: [], open: null, busy: false, libBusy: false, opening: false, ticket: 0 };

/* ------------------------------------------------------------ covers */

const BINDINGS = [
  ["#2F4A3A", "#1F3328"], ["#6B2A22", "#4A1C17"], ["#22344F", "#152236"], ["#8A5A1E", "#5E3C12"],
  ["#4B2E4F", "#321E35"], ["#24524F", "#173836"], ["#3A3532", "#252220"], ["#9A4A22", "#6A3216"],
];
const shortTitle = t => t.replace(/^The Works of Edgar Allan Poe, /, "Poe: ").replace(/^The Extraordinary Adventures of /, "");
const binding = b => { const [a, z] = BINDINGS[b.i % BINDINGS.length]; return `linear-gradient(160deg, ${a}, ${z})`; };
const coverHTML = b => `
  <span class="cover" style="background:${binding(b)}">
    <span class="c-title">${esc(shortTitle(b.title))}</span>
    <span class="c-orn">❦</span>
    <span class="c-author">${esc(b.author)}</span>
  </span>`;

function renderGrid(filter = "") {
  const f = filter.trim().toLowerCase();
  const list = state.books.filter(b => !f || `${b.title} ${b.author}`.toLowerCase().includes(f));
  $("#grid").innerHTML = list.map(b => `
    <button class="book" data-file="${esc(b.file)}" aria-label="Open ${esc(b.title)}">
      ${coverHTML(b)}
      <b>${esc(b.title)}</b><small>${esc(b.author)}</small>
    </button>`).join("") || `<p style="color:rgba(247,241,232,.55);font-size:13px">No book matches “${esc(filter)}”.</p>`;
  $("#sp-count").textContent = f ? `${list.length} of ${state.books.length} books` : `Mysteries · ${state.books.length} books`;
  $$(".book", $("#grid")).forEach(el => el.addEventListener("click", e => openBook(el.dataset.file, $(".cover", el), e)));
}
$("#search").addEventListener("input", e => renderGrid(e.target.value));

function renderMarquee() {
  const html = state.books.map(b => `
    <button class="cover" style="background:${binding(b)}" data-file="${esc(b.file)}" aria-label="Open ${esc(b.title)}">
      <span class="c-title">${esc(shortTitle(b.title))}</span><span class="c-orn">❦</span>
      <span class="c-author">${esc(b.author)}</span>
    </button>`).join("");
  $("#covers").innerHTML = html + html;   // twice, so the loop is seamless
  $$(".cover", $("#covers")).forEach(el => el.addEventListener("click", () => {
    $("#app").scrollIntoView({ behavior: "smooth", block: "center" });
    setTimeout(() => {
      if (state.open) closeBook(true);
      const card = $(`.book[data-file="${CSS.escape(el.dataset.file)}"] .cover`);
      openBook(el.dataset.file, card || null);
    }, 520);
  }));
}

/* ------------------------------------------------------------ continue reading */

function refreshContinue() {
  const last = store.get("ml-last", "The Hound of the Baskervilles.txt");
  const b = state.books.find(x => x.file === last) || state.books[0];
  if (!b) return;
  const prog = store.get("ml-progress", {})[b.file] || {};
  $("#cont").dataset.file = b.file;
  $("#cont-title").textContent = b.title;
  $("#ra-title").textContent = b.title;
  $("#cont-ch").textContent = prog.chapter || "Not started";
  $("#cont-bar").style.width = `${Math.round((prog.pct || 0) * 100)}%`;
  $("#cont-cover").style.background = binding(b);
  $("#cont-cover").innerHTML = `<span>${esc(shortTitle(b.title))}</span>`;
}
$("#cont").addEventListener("click", e => openBook($("#cont").dataset.file, $("#cont-cover"), e));
$("#ra-play").addEventListener("click", e => openBook($("#cont").dataset.file, $("#cont-cover"), e, { thenRead: true }));

const ticks = $("#ra-ticks");
for (let i = 0; i < 34; i++) { const t = document.createElement("i"); t.style.height = `${5 + Math.round(10 * Math.abs(Math.sin(i * 2.1)))}px`; ticks.appendChild(t); }

/* ------------------------------------------------------------ opening a book */

const app = $("#app");
const rectIn = el => { const a = app.getBoundingClientRect(), r = el.getBoundingClientRect();
  return { top: r.top - a.top, left: r.left - a.left, right: a.right - r.right, bottom: a.bottom - r.bottom, w: a.width, h: a.height,
           cx: r.left - a.left + r.width / 2, cy: r.top - a.top + r.height / 2 }; };
const inset = (r, round) => `inset(${r.top}px ${r.right}px ${r.bottom}px ${r.left}px round ${round}px)`;
const wait = ms => new Promise(res => setTimeout(res, ms));

async function openBook(file, coverEl, evt, opts = {}) {
  const b = state.books.find(x => x.file === file);
  if (!b || state.opening) return;
  state.opening = true;
  const ticket = ++state.ticket;   // goHome() bumps this to cancel an opening in flight
  stopReading();
  const bookReq = fetch(`/api/book/${encodeURIComponent(file)}`).then(r => r.json());

  // 1. a tap ripple where the finger (or cursor) landed
  if (coverEl) {
    const r = rectIn(coverEl);
    const tap = $("#tap");
    const x = evt && evt.clientX ? evt.clientX - app.getBoundingClientRect().left : r.cx;
    const y = evt && evt.clientY ? evt.clientY - app.getBoundingClientRect().top : r.cy;
    tap.style.left = `${x}px`; tap.style.top = `${y}px`;
    tap.classList.remove("go"); void tap.offsetWidth; tap.classList.add("go");
  }
  await wait(coverEl ? 160 : 0);

  // 2. the cover grows from its place on the shelf to fill the whole panel
  const grow = $("#grow");
  grow.style.background = binding(b);
  $("#grow-title").textContent = b.title;
  grow.style.transition = "none";
  grow.classList.remove("fade");
  grow.style.clipPath = coverEl ? inset(rectIn(coverEl), 6) : "inset(0 round 26px)";
  grow.classList.add("on");
  void grow.offsetWidth;
  grow.style.transition = "clip-path 1s cubic-bezier(.6,.05,.25,1)";
  grow.style.clipPath = "inset(0px 0px 0px 0px round 0px)";
  // The shelf stays put underneath; the growing cover is what covers it.

  const [book] = await Promise.all([bookReq, wait(1000)]);
  if (ticket !== state.ticket) return;   // the logo was clicked mid-animation

  // 3. the page fades in over the grown cover; the player slides up after it
  renderBook(b, book);
  $("#lib").classList.add("is-hidden");
  $("#lib").classList.remove("leaving");
  const read = $("#read");
  read.classList.remove("is-hidden", "leaving");
  read.classList.remove("entering"); void read.offsetWidth; read.classList.add("entering");
  grow.style.transition = "";
  grow.classList.add("fade");
  await wait(420);
  grow.classList.remove("on", "fade");
  state.opening = false;
  store.set("ml-last", file);
  if (opts.thenRead) readAloud();
}

function closeBook(instant = false) {
  stopReading();
  const b = state.open && state.open.meta;
  state.open = null;
  const read = $("#read"), lib = $("#lib");
  const finish = () => {
    read.classList.add("is-hidden"); read.classList.remove("leaving", "entering");
    lib.classList.remove("is-hidden", "leaving");
    lib.classList.remove("entering"); void lib.offsetWidth; lib.classList.add("entering");
    refreshContinue();
  };
  if (instant || !b) { finish(); return; }
  // Reverse of opening: the page folds back into its cover on the shelf.
  const grow = $("#grow");
  grow.style.background = binding(b);
  $("#grow-title").textContent = "";
  grow.style.transition = "none"; grow.style.clipPath = "inset(0px 0px 0px 0px round 0px)";
  grow.classList.remove("fade"); grow.classList.add("on");
  read.classList.add("leaving");
  setTimeout(() => {
    finish();
    const card = $(`.book[data-file="${CSS.escape(b.file)}"] .cover`);
    void grow.offsetWidth;
    grow.style.transition = "clip-path .7s cubic-bezier(.6,.05,.25,1), opacity .25s ease .55s";
    if (card) grow.style.clipPath = inset(rectIn(card), 6);
    grow.style.opacity = "0";
    setTimeout(() => { grow.classList.remove("on"); grow.style.opacity = ""; }, 820);
  }, 260);
}
$("#back").addEventListener("click", () => closeBook());

/* The logo always means "start again": wherever you are -- mid-book, mid-
 * answer, mid-animation -- it returns to the fresh landing page. */
const LIB_MSGS_START = $("#lib-msgs").innerHTML;
function goHome() {
  state.ticket++;                 // cancels a book that is still opening
  state.opening = false;
  stopReading();
  const grow = $("#grow");
  grow.style.transition = "none";
  grow.classList.remove("on", "fade");
  if (state.open || !$("#read").classList.contains("is-hidden")) closeBook(true);
  $("#lib").classList.remove("leaving");
  $("#search").value = "";
  renderGrid();
  $("#lib-msgs").innerHTML = LIB_MSGS_START;
  $("#lib-q").value = "";
  $("#q").value = "";
  window.scrollTo({ top: 0, behavior: "smooth" });
}
$(".brand").addEventListener("click", e => { e.preventDefault(); goHome(); });

/* ------------------------------------------------------------ the page */

function renderBook(meta, book) {
  state.open = { meta, chapters: book.chapters };
  $("#rd-book").textContent = meta.title;
  $("#rd-ch").textContent = "";
  const parts = [];
  book.chapters.forEach((ch, ci) => {
    parts.push(`<h3 class="ch-title" data-ci="${ci}">${esc(ch.title)}</h3>`);
    ch.paras.forEach(p => parts.push(/^[IVXLC]+\.?$/.test(p) ? `<p class="sec">${esc(p)}</p>` : `<p>${esc(p)}</p>`));
  });
  const text = $("#text");
  text.innerHTML = parts.join("");
  text.classList.remove("speaking");

  // A fresh chat for each book.
  $$(".msg-q, .msg-a", $("#msgs")).forEach(n => n.remove());
  $("#chat-hint").classList.remove("is-hidden");

  const saved = store.get("ml-progress", {})[meta.file];
  text.scrollTop = 0;
  requestAnimationFrame(() => {
    if (saved && saved.pct) text.scrollTop = saved.pct * (text.scrollHeight - text.clientHeight);
    onScroll();
  });
}

let scrollTimer = null;
function onScroll() {
  const text = $("#text");
  if (!state.open) return;
  const max = text.scrollHeight - text.clientHeight;
  const pct = max > 0 ? text.scrollTop / max : 0;
  $("#rd-pct").textContent = `${Math.round(pct * 100)}%`;
  const heads = $$(".ch-title", text);
  let cur = heads[0];
  for (const h of heads) { if (h.offsetTop - text.offsetTop <= text.scrollTop + 90) cur = h; else break; }
  const chapter = cur ? cur.textContent : "";
  $("#rd-ch").textContent = chapter ? `· ${chapter}` : "";
  clearTimeout(scrollTimer);
  scrollTimer = setTimeout(() => {
    const all = store.get("ml-progress", {});
    all[state.open.meta.file] = { pct, chapter };
    store.set("ml-progress", all);
  }, 300);
}
$("#text").addEventListener("scroll", () => requestAnimationFrame(onScroll), { passive: true });

/* ------------------------------------------------------------ asking */

function inlineMd(t) {
  return esc(t).replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>").replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>");
}
const renderAnswer = text => text.split(/\n+/).filter(Boolean).map(p => `<p>${inlineMd(p.replace(/^[-*]\s+/, "• "))}</p>`).join("");
const STATUS = { retrieve: "reading the book…", grade: "checking the passages…", deepen: "looking further…", answer: "writing…" };

/* One question through the corrective flow. `book` scopes the search to the
 * open book; without it, the whole library is searched. */
async function askFlow(question, book, { onStatus }) {
  const res = await fetch("/api/ask-book", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, book, session_id: SESSION }),
  });
  if (!res.ok) throw new Error(`Server returned ${res.status}`);
  const reader = res.body.getReader(), dec = new TextDecoder();
  let buf = "", result = null;
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    const frames = buf.split("\n\n"); buf = frames.pop();
    for (const f of frames) {
      const evt = (f.match(/^event: (.*)$/m) || [])[1], data = (f.match(/^data: (.*)$/m) || [])[1];
      if (!evt || !data) continue;
      const p = JSON.parse(data);
      if (evt === "phase") onStatus(p.node === "retrieve" ? STATUS.grade : p.node === "grade" ? (STATUS[p.next] || "") : p.node === "deepen" ? STATUS.grade : "");
      if (evt === "done") result = p;
      if (evt === "error") throw new Error(p.message);
    }
  }
  return result || { decision: "refuse", answer: "" };
}

async function askInBook(question) {
  question = question.trim();
  if (!question || state.busy || !state.open) return;
  state.busy = true; $("#send").disabled = true; $("#q").value = "";
  $("#chat-hint").classList.add("is-hidden");
  const msgs = $("#msgs");
  msgs.insertAdjacentHTML("beforeend", `<div class="msg-q rise">${esc(question)}</div>`);
  const a = document.createElement("div");
  a.className = "msg-a rise";
  a.innerHTML = `<img class="avatar" src="assets/otter-logo.png" alt=""><div class="bubble typing"><span class="dots"><i></i><i></i><i></i></span><small>reading the book…</small></div>`;
  setTimeout(() => { msgs.appendChild(a); msgs.scrollTop = msgs.scrollHeight; }, 180);
  const bubble = $(".bubble", a);
  try {
    const r = await askFlow(question, state.open.meta.file, { onStatus: s => { if (s) $("small", bubble).textContent = s; } });
    bubble.classList.remove("typing");
    if (r.decision === "refuse") { bubble.classList.add("declined"); bubble.textContent = "Not in this book."; }
    else bubble.innerHTML = renderAnswer(r.answer);
  } catch (err) {
    bubble.classList.remove("typing"); bubble.classList.add("declined"); bubble.textContent = err.message;
  } finally {
    state.busy = false; $("#send").disabled = false;
    msgs.scrollTop = msgs.scrollHeight;
  }
}
$("#composer").addEventListener("submit", e => { e.preventDefault(); askInBook($("#q").value); });
$$("#chat-hint .chip").forEach(c => c.addEventListener("click", () => askInBook(c.textContent)));

async function askLibrary(question) {
  question = question.trim();
  if (!question || state.libBusy) return;
  state.libBusy = true; $("#lib-q").value = "";
  const msgs = $("#lib-msgs");
  msgs.insertAdjacentHTML("beforeend", `<div class="msg-q rise">${esc(question)}</div>
    <div class="msg-a rise"><div class="bubble typing"><span class="dots"><i></i><i></i><i></i></span></div></div>`);
  msgs.scrollTop = msgs.scrollHeight;
  const bubble = $$(".bubble", msgs).pop();
  try {
    const r = await askFlow(question, null, { onStatus: () => {} });
    bubble.classList.remove("typing");
    if (r.decision === "refuse") { bubble.classList.add("declined"); bubble.textContent = "Not in these books."; }
    else bubble.innerHTML = renderAnswer(r.answer);
  } catch (err) {
    bubble.classList.remove("typing"); bubble.textContent = err.message;
  } finally {
    state.libBusy = false; msgs.scrollTop = msgs.scrollHeight;
  }
}
$("#lib-form").addEventListener("submit", e => { e.preventDefault(); askLibrary($("#lib-q").value); });

/* ------------------------------------------------------------ read aloud */

const wave = $("#wave");
for (let i = 0; i < 26; i++) {
  const b = document.createElement("i");
  b.style.height = `${8 + Math.round(16 * Math.abs(Math.sin(i * 1.7)))}px`;
  b.style.animationDelay = `${(i % 7) * -0.13}s`;
  wave.appendChild(b);
}

const speech = { on: false, para: null, started: 0, clock: null };
const canSpeak = "speechSynthesis" in window;
if (!canSpeak) { $("#player").classList.add("is-hidden"); $(".ra-card").classList.add("is-hidden"); }

function unwrap(p) { if (p && p.dataset.plain != null) { p.textContent = p.dataset.plain; delete p.dataset.plain; } }

function stopReading() {
  if (canSpeak) speechSynthesis.cancel();
  speech.on = false;
  clearInterval(speech.clock);
  $("#player").classList.remove("playing");
  $("#text").classList.remove("speaking");
  $$("#text p.now").forEach(p => { p.classList.remove("now"); unwrap(p); });
}

function firstVisibleParagraph() {
  const text = $("#text");
  return $$("p", text).find(p => p.offsetTop - text.offsetTop + p.offsetHeight > text.scrollTop + 10) || $("p", text);
}

function speakParagraph(p) {
  if (!speech.on || !p) { stopReading(); return; }
  if (p.classList.contains("sec")) { speakParagraph(nextPara(p)); return; }
  $$("#text p.now").forEach(x => { x.classList.remove("now"); unwrap(x); });
  speech.para = p;
  p.classList.add("now");
  const raw = p.textContent;
  p.dataset.plain = raw;
  const spans = [];
  let html = "", cursor = 0;
  for (const tok of raw.split(/(\s+)/)) {
    if (tok.trim()) { spans.push({ start: cursor, len: tok.length }); html += `<span class="w">${esc(tok)}</span>`; }
    else html += tok;
    cursor += tok.length;
  }
  p.innerHTML = html;
  const els = $$(".w", p);

  // Keep the paragraph being read in view, as a reader's eye would.
  const text = $("#text");
  const top = p.offsetTop - text.offsetTop, bottom = top + p.offsetHeight;
  if (top < text.scrollTop + 40 || bottom > text.scrollTop + text.clientHeight - 110) {
    text.scrollTo({ top: Math.max(0, top - 80), behavior: "smooth" });
  }

  const u = new SpeechSynthesisUtterance(raw);
  u.rate = 0.97;
  const voices = speechSynthesis.getVoices();
  const voice = voices.find(v => /en-GB/i.test(v.lang)) || voices.find(v => /^en/i.test(v.lang));
  if (voice) u.voice = voice;
  u.onboundary = e => {
    if (e.name && e.name !== "word") return;
    const i = spans.findIndex(s => e.charIndex >= s.start && e.charIndex < s.start + s.len);
    $$(".w.now", p).forEach(w => w.classList.remove("now"));
    if (els[i]) els[i].classList.add("now");
  };
  u.onend = () => { if (speech.on && speech.para === p) speakParagraph(nextPara(p)); };
  speechSynthesis.speak(u);
}
function nextPara(p) { let n = p.nextElementSibling; while (n && n.tagName !== "P") n = n.nextElementSibling; return n; }

function readAloud() {
  if (!canSpeak || !state.open) return;
  if (speech.on) { stopReading(); return; }
  speech.on = true;
  speech.started = Date.now();
  $("#player").classList.add("playing");
  $("#text").classList.add("speaking");
  const clock = $("#ra-clock");
  speech.clock = setInterval(() => {
    const s = Math.floor((Date.now() - speech.started) / 1000);
    clock.textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  }, 500);
  speakParagraph(firstVisibleParagraph());
}
$("#play").addEventListener("click", readAloud);

/* ------------------------------------------------------------ page chrome */

$$("[data-ask-cta]").forEach(a => a.addEventListener("click", e => {
  e.preventDefault();
  $("#app").scrollIntoView({ behavior: "smooth", block: "center" });
  setTimeout(() => (state.open ? $("#q") : $("#lib-q")).focus({ preventScroll: true }), 480);
}));

const BITS = ["🔍", "🕯️", "📜", "🗝️", "🖋️", "🌙", "📖", "🦉", "☕", "🎩", "✉️", "🕰️", "✨"];
const trail = $("#trail");
let last = null;
if (!matchMedia("(prefers-reduced-motion: reduce)").matches) trail.addEventListener("pointermove", e => {
  const r = trail.getBoundingClientRect();
  const x = e.clientX - r.left, y = e.clientY - r.top;
  if (last && Math.hypot(x - last.x, y - last.y) < 26) return;   // one bit per ~26px of travel
  last = { x, y };
  const bit = document.createElement("span");
  bit.className = "bit";
  bit.textContent = BITS[Math.floor(Math.random() * BITS.length)];
  const rnd = (a, b) => a + Math.random() * (b - a);
  bit.style.cssText = `left:${x}px; top:${y}px; font-size:${Math.round(rnd(16, 28))}px;
    --x:${Math.round(rnd(-40, 40))}px; --y:${Math.round(rnd(0, 85))}px;
    --r:${Math.round(rnd(-30, 30))}deg; --d:${rnd(1.0, 1.5).toFixed(2)}s;`;
  bit.addEventListener("animationend", () => bit.remove());
  trail.appendChild(bit);
});
trail.addEventListener("pointerleave", () => { last = null; });

const io = new IntersectionObserver(entries => entries.forEach(en => {
  if (en.isIntersecting) $$(".links a[data-nav]").forEach(a => a.classList.toggle("is-active", a.dataset.nav === en.target.id));
}), { rootMargin: "-45% 0px -50% 0px" });
["top", "shelf", "how"].forEach(id => { const el = document.getElementById(id); if (el) io.observe(el); });

/* ------------------------------------------------------------ boot */

(async () => {
  try {
    const d = await (await fetch("/api/corpus")).json();
    state.books = (d.books || []).map((b, i) => ({ ...b, i }));
  } catch { state.books = []; }
  renderGrid();
  renderMarquee();
  refreshContinue();
})();
fetch("/api/warmup").catch(() => {});   // load the search model while the visitor looks around
