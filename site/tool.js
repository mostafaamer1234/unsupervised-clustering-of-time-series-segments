// Pulse Clusters analyzer. Ports of the pipeline in pulse_cluster/: z-score + resample to 256
// samples (io.py), correlation distance (metrics.py), divide and conquer (divide_conquer.py),
// closest pair (closest_pair.py) and centred Kadane (kadane.py). Library: python export_site_data.py
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const FAM = { ECG: "ECG", PPG: "PPG", ABP: "Blood pressure", ARR: "Arrhythmia", STR: "Stress" };
  const FAM_COLOR = { ECG: "#39ff88", PPG: "#2ee6ff", ABP: "#ff4d6d", ARR: "#c77dff", STR: "#ffbe3d" };
  const N = 256, LAGS = 128, BINS = 64;
  let LIB = null;

  // ---------- signal processing ----------
  function zscore(x) {
    const n = x.length, mu = x.reduce((s, v) => s + v, 0) / n;
    const sd = Math.sqrt(x.reduce((s, v) => s + (v - mu) ** 2, 0) / n);
    return x.map((v) => (v - mu) / (sd + 1e-8));
  }
  function resample(x, n = N) {
    if (x.length === n) return x.slice();
    const out = new Array(n);
    for (let i = 0; i < n; i++) {
      const t = (i / (n - 1)) * (x.length - 1), j = Math.floor(t), f = t - j;
      out[i] = j + 1 < x.length ? x[j] * (1 - f) + x[j + 1] * f : x[x.length - 1];
    }
    return out;
  }
  const prep = (raw) => resample(zscore(raw));

  const COS = [], SIN = [];
  for (let k = 1; k <= BINS; k++) {
    const c = new Float64Array(N), s = new Float64Array(N);
    for (let t = 0; t < N; t++) { c[t] = Math.cos((2 * Math.PI * k * t) / N); s[t] = Math.sin((2 * Math.PI * k * t) / N); }
    COS.push(c); SIN.push(s);
  }
  function spectrum(x) {
    const out = new Float64Array(BINS);
    let mx = 0;
    for (let k = 0; k < BINS; k++) {
      let re = 0, im = 0;
      const c = COS[k], s = SIN[k];
      for (let t = 0; t < N; t++) { re += x[t] * c[t]; im -= x[t] * s[t]; }
      out[k] = Math.hypot(re, im);
      if (out[k] > mx) mx = out[k];
    }
    for (let k = 0; k < BINS; k++) out[k] /= mx || 1;
    return out;
  }
  function centredUnit(v) {
    const m = v.reduce((s, a) => s + a, 0) / v.length;
    const c = Float64Array.from(v, (a) => a - m);
    const nrm = Math.sqrt(c.reduce((s, a) => s + a * a, 0)) || 1;
    for (let i = 0; i < c.length; i++) c[i] /= nrm;
    return c;
  }
  function acf(x) {
    const out = new Float64Array(LAGS);
    for (let l = 0; l < LAGS; l++) { let s = 0; for (let t = 0; t + l < N; t++) s += x[t] * x[t + l]; out[l] = s / N; }
    return centredUnit(out);
  }
  const dot = (a, b) => { let s = 0; for (let i = 0; i < a.length; i++) s += a[i] * b[i]; return s; };
  const corrDist = (a, b) => 1 - dot(centredUnit(a), centredUnit(b));
  const euclid2 = (a, b) => { let s = 0; for (let i = 0; i < a.length; i++) s += (a[i] - b[i]) ** 2; return s; };

  // kadane.py: centred absolute differences
  function mostActive(x) {
    const d = []; for (let i = 1; i < x.length; i++) d.push(Math.abs(x[i] - x[i - 1]));
    const m = d.reduce((s, v) => s + v, 0) / d.length;
    let best = -Infinity, cur = 0, start = 0, l = 0, r = 0;
    d.forEach((v0, i) => {
      const v = v0 - m;
      if (cur <= 0) { cur = v; start = i; } else cur += v;
      if (cur > best) { best = cur; l = start; r = i + 1; }
    });
    return { l, r };
  }

  function rng(seed) { // mulberry32
    return () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }

  // ---------- parsing ----------
  function parseSignal(text) {
    const lines = text.trim().split(/\r?\n/).filter((l) => l.trim());
    if (!lines.length) throw new Error("The file is empty.");
    let col = 0;
    const head = lines[0].split(/[,;\t]/).map((h) => h.trim().toLowerCase());
    if (head.some((h) => isNaN(parseFloat(h)))) { const i = head.indexOf("value"); col = i >= 0 ? i : 0; lines.shift(); }
    let vals;
    if (lines.length === 1) vals = lines[0].split(/[\s,;\t]+/).map(Number); // one row of values
    else vals = lines.map((l) => parseFloat(l.split(/[,;\t]/)[col]));
    vals = vals.filter((v) => Number.isFinite(v));
    if (vals.length < 50) throw new Error(`Found ${vals.length} numeric samples. The analyzer needs at least 50.`);
    return vals;
  }

  // ---------- plots ----------
  function pathOf(arr, W, H, lo, hi) {
    const span = hi - lo || 1;
    return arr.map((v, i) => `${i ? "L" : "M"}${((i / (arr.length - 1)) * W).toFixed(1)},${(H - ((v - lo) / span) * H).toFixed(1)}`).join("");
  }
  const range = (a) => { let lo = Infinity, hi = -Infinity; for (const v of a) { if (v < lo) lo = v; if (v > hi) hi = v; } const p = (hi - lo) * 0.08 || 1; return [lo - p, hi + p]; };

  // ---------- library ----------
  async function loadLibrary() {
    const d = await fetch("library.json").then((r) => r.json());
    const x = d.x;
    LIB = { ids: d.ids, x, fam: d.ids.map((i) => i.split("_")[0]), acf: x.map(acf), spec: x.map(spectrum), k: d.k, acc: d.loo_accuracy, per: d.per_family };
  }

  // ---------- one signal ----------
  function analyze(raw, name, excludeIdx = -1) {
    const x = prep(raw), a = acf(x), sp = spectrum(x);
    const dists = LIB.acf.map((b, i) => [i, i === excludeIdx ? Infinity : 1 - dot(a, b)]).sort((p, q) => p[1] - q[1]);
    const nn = dists.slice(0, LIB.k);
    const votes = {};
    nn.forEach(([i]) => (votes[LIB.fam[i]] = (votes[LIB.fam[i]] || 0) + 1));
    const ranked = Object.entries(votes).sort((p, q) => q[1] - p[1]);
    const [top, n] = ranked[0];
    const act = mostActive(x);
    const [lo, hi] = range(x);
    const conf = n === LIB.k ? "All" : n >= LIB.k - 1 ? "Most" : n > LIB.k / 2 ? "Most" : "Some";
    $("out-one").innerHTML = `<div class="fade">
      <div class="verdict">
        <div>
          <span class="label">Looks like</span>
          <p class="big" style="color:${FAM_COLOR[top]};text-shadow:0 0 18px ${FAM_COLOR[top]}66">${esc(FAM[top])}<small>${n} of ${LIB.k} nearest segments</small></p>
          <p class="note">${esc(name)} · ${raw.length.toLocaleString()} samples, resampled to ${N}</p>
        </div>
        <div class="votes bars">${Object.keys(FAM).map((f) => `<div class="bar"><span>${FAM[f]}</span><i><em style="width:${((votes[f] || 0) / LIB.k) * 100}%;background:${FAM_COLOR[f]};color:${FAM_COLOR[f]}"></em></i><output>${votes[f] || 0}/${LIB.k}</output></div>`).join("")}</div>
      </div>
      <div class="chart"><header><b>Signal</b><span>Most active stretch: samples ${act.l}–${act.r} (shaded)</span></header>
        <svg viewBox="0 0 600 170" preserveAspectRatio="none" role="img" aria-label="Signal with its most active stretch shaded">
          <rect class="act" x="${(act.l / (N - 1)) * 600}" y="0" width="${((act.r - act.l) / (N - 1)) * 600}" height="170" />
          <path class="sig" d="${pathOf(x, 600, 170, lo, hi)}" /></svg></div>
      <div class="chart"><header><b>Spectrum</b><span>Frequency bins 1–${BINS}, scaled to the peak</span></header>
        <svg viewBox="0 0 600 170" preserveAspectRatio="none" role="img" aria-label="Magnitude spectrum">
          <path class="spec" d="${pathOf(Array.from(sp), 600, 170, -0.03, 1.05)}L600,170L0,170Z" /></svg></div>
      <h2 class="sub">Closest matches in the library</h2>
      <div class="cards matches">${nn.slice(0, 4).map(([i, d]) => { const [l2, h2] = range(LIB.x[i]); return `<div class="card match"><div class="row" style="justify-content:space-between"><span class="fam">${esc(FAM[LIB.fam[i]])}</span><span class="muted" style="font-size:12px">${esc(LIB.ids[i])}</span></div>
        <svg viewBox="0 0 300 70" preserveAspectRatio="none"><path d="${pathOf(LIB.x[i], 300, 70, l2, h2)}" /></svg><p>Distance ${d.toFixed(3)}</p></div>`; }).join("")}</div>
      <p class="note">Signal type is a vote among the ${LIB.k} library segments whose autocorrelation is closest. The autocorrelation ignores where in the beat a segment starts. Leave-one-out over the library, it is right ${Math.round(LIB.acc * 100)}% of the time (${Object.entries(LIB.per).map(([f, v]) => `${FAM[f]} ${Math.round(v * 100)}%`).join(", ")}). ${conf === "Some" ? "This one was a close vote, so treat it as a guess." : ""}</p>
    </div>`;
  }

  function sampleChips() {
    $("samples").innerHTML = Object.entries(FAM).map(([k, v]) => `<button class="chip" type="button" data-fam="${k}">${v}</button>`).join("");
    $("samples").addEventListener("click", (e) => {
      const b = e.target.closest("[data-fam]"); if (!b || !LIB) return;
      const idx = LIB.fam.map((f, i) => [f, i]).filter(([f]) => f === b.dataset.fam).map(([, i]) => i);
      const i = idx[Math.floor(Math.random() * idx.length)];
      document.querySelectorAll("#samples .chip").forEach((c) => c.setAttribute("aria-pressed", String(c === b)));
      analyze(LIB.x[i], `Library segment ${LIB.ids[i]}`, i);
    });
  }

  function errorOne(msg) { $("out-one").innerHTML = `<div class="empty"><div><b>Couldn't read that signal</b>${esc(msg)}</div></div>`; }

  // ---------- batch ----------
  let batch = []; // {id, raw}
  let method = "kmeans";

  // best of several k-means++ starts, by within-cluster sum of squares
  function kmeans(vecs, k) {
    let best = null;
    for (let s = 0; s < 6; s++) {
      const lab = kmeansOnce(vecs, k, s);
      const cents = Array.from({ length: k }, (_, j) => { const m = vecs.filter((_, i) => lab[i] === j); return m.length ? m[0].map((_, d) => m.reduce((t, v) => t + v[d], 0) / m.length) : null; });
      const sse = vecs.reduce((t, v, i) => t + euclid2(v, cents[lab[i]]), 0);
      if (!best || sse < best.sse) best = { lab, sse };
    }
    return best.lab;
  }
  function kmeansOnce(vecs, k, seed = 0) {
    const r = rng(seed + 1), n = vecs.length;
    const cents = [vecs[Math.floor(r() * n)].slice()];
    while (cents.length < k) { // k-means++
      const d = vecs.map((v) => Math.min(...cents.map((c) => euclid2(v, c))));
      const tot = d.reduce((s, v) => s + v, 0);
      let t = r() * tot, i = 0;
      while (t > d[i] && i < n - 1) { t -= d[i]; i++; }
      cents.push(vecs[i].slice());
    }
    let lab = new Array(n).fill(0);
    for (let it = 0; it < 60; it++) {
      const next = vecs.map((v) => { let b = 0, bd = Infinity; cents.forEach((c, j) => { const dd = euclid2(v, c); if (dd < bd) { bd = dd; b = j; } }); return b; });
      const changed = next.some((v, i) => v !== lab[i]);
      lab = next;
      for (let j = 0; j < k; j++) {
        const mem = vecs.filter((_, i) => lab[i] === j);
        if (mem.length) cents[j] = mem[0].map((_, d) => mem.reduce((s, v) => s + v[d], 0) / mem.length);
      }
      if (!changed && it) break;
    }
    return lab;
  }

  function divideConquer(ids, X, minSize, maxDepth, seed = 0) {
    const r = rng(seed + 1), out = [];
    const U = X.map(centredUnit);
    const dist = (i, j) => 1 - dot(U[i], U[j]);
    (function rec(set, depth) {
      if (set.length <= minSize || depth >= maxDepth) { out.push(set); return; }
      const pivot = set[Math.floor(r() * set.length)];
      const ds = set.filter((i) => i !== pivot).map((i) => [i, dist(i, pivot)]);
      if (!ds.length) { out.push(set); return; }
      const sorted = ds.map((p) => p[1]).sort((a, b) => a - b), m = sorted.length;
      const med = m % 2 ? sorted[(m - 1) / 2] : (sorted[m / 2 - 1] + sorted[m / 2]) / 2;
      const left = ds.filter((p) => p[1] <= med).map((p) => p[0]).concat([pivot]), right = ds.filter((p) => p[1] > med).map((p) => p[0]);
      if (!right.length) { out.push(left); return; }
      rec(left, depth + 1); rec(right, depth + 1);
    })(ids.map((_, i) => i), 0);
    const lab = new Array(ids.length);
    out.forEach((c, j) => c.forEach((i) => (lab[i] = j)));
    return lab;
  }

  function ari(a, b) {
    const n = a.length, key = (x, y) => x + "|" + y, c = new Map(), ra = new Map(), rb = new Map();
    for (let i = 0; i < n; i++) { c.set(key(a[i], b[i]), (c.get(key(a[i], b[i])) || 0) + 1); ra.set(a[i], (ra.get(a[i]) || 0) + 1); rb.set(b[i], (rb.get(b[i]) || 0) + 1); }
    const C2 = (x) => (x * (x - 1)) / 2;
    const sIJ = [...c.values()].reduce((s, v) => s + C2(v), 0), sA = [...ra.values()].reduce((s, v) => s + C2(v), 0), sB = [...rb.values()].reduce((s, v) => s + C2(v), 0);
    const exp = (sA * sB) / C2(n), mx = (sA + sB) / 2;
    return mx === exp ? 0 : (sIJ - exp) / (mx - exp);
  }

  function setBatch(items, label) {
    batch = items;
    $("batch-loaded").textContent = `${items.length.toLocaleString()} signals loaded${label ? ` (${label})` : ""}.`;
    $("run").disabled = items.length < 2;
    if (items.length >= 2) runBatch();
  }

  function runBatch() {
    if (batch.length < 2) return;
    $("out-batch").innerHTML = '<div class="empty"><div><span class="spin"></span></div></div>';
    setTimeout(() => {
      const X = batch.map((b) => prep(b.raw));
      const k = +$("k").value;
      const lab = method === "kmeans" ? kmeans(X.map((x) => Array.from(spectrum(x))), Math.min(k, X.length)) :
        method === "acf" ? kmeans(X.map((x) => Array.from(acf(x))), Math.min(k, X.length)) :
        divideConquer(batch.map((b) => b.id), X, +$("min").value, +$("depth").value);
      renderClusters(X, lab);
    }, 30);
  }

  function renderClusters(X, lab) {
    const fams = batch.map((b) => (b.id.match(/^(ECG|PPG|ABP|ARR|STR)[_-]/i) || [])[1]?.toUpperCase());
    const labelled = fams.every(Boolean);
    const groups = {};
    lab.forEach((c, i) => (groups[c] = groups[c] || []).push(i));
    const list = Object.values(groups).sort((a, b) => b.length - a.length);
    const U = X.map(centredUnit);
    let purity = 0;
    const cards = list.map((mem, ci) => {
      // medoid and closest pair by correlation distance, as in closest_pair.py
      let med = mem[0], best = Infinity, pair = null, pd = Infinity;
      const sample = mem.length > 300 ? mem.slice(0, 300) : mem;
      for (const i of sample) {
        let s = 0;
        for (const j of sample) if (i !== j) { const d = 1 - dot(U[i], U[j]); s += d; if (i < j && d < pd) { pd = d; pair = [i, j]; } }
        if (s < best) { best = s; med = i; }
      }
      const mix = {};
      if (labelled) mem.forEach((i) => (mix[fams[i]] = (mix[fams[i]] || 0) + 1));
      const topFam = labelled ? Object.entries(mix).sort((a, b) => b[1] - a[1])[0] : null;
      if (topFam) purity += topFam[1];
      const lines = mem.slice(0, 8).filter((i) => i !== med).map((i) => { const [l, h] = range(X[i]); return `<path d="${pathOf(X[i], 300, 64, l, h)}" />`; }).join("");
      const [l, h] = range(X[med]);
      return `<div class="card cl"><div class="row" style="justify-content:space-between"><h3>Cluster ${ci + 1}</h3><span class="muted" style="font-size:13px">${mem.length} signal${mem.length === 1 ? "" : "s"}</span></div>
        <svg viewBox="0 0 300 64" preserveAspectRatio="none">${lines}<path class="medoid" d="${pathOf(X[med], 300, 64, l, h)}" /></svg>
        ${labelled ? `<div class="mix">${Object.keys(FAM).filter((f) => mix[f]).map((f) => `<i style="width:${(mix[f] / mem.length) * 100}%;background:${FAM_COLOR[f]}"></i>`).join("")}</div>
        <p class="top-fam">${Math.round((topFam[1] / mem.length) * 100)}% ${esc(FAM[topFam[0]])}</p>` : ""}
        <p>Medoid ${esc(batch[med].id)}</p>
        ${pair ? `<p>Closest pair: ${esc(batch[pair[0]].id)} and ${esc(batch[pair[1]].id)} (${pd.toFixed(3)})</p>` : ""}</div>`;
    }).join("");
    const famIdx = labelled ? fams : null;
    const score = labelled ? ari(famIdx, lab) : null;
    $("out-batch").innerHTML = `<div class="fade">
      <div class="batch-actions"><div class="stats" style="flex:1">
        <div class="stat"><b>${batch.length.toLocaleString()}</b><span>signals</span></div>
        <div class="stat"><b>${list.length}</b><span>clusters</span></div>
        ${labelled ? `<div class="stat"><b>${score.toFixed(3)}</b><span>adjusted Rand index (0 is chance)</span></div>
        <div class="stat"><b>${Math.round((purity / batch.length) * 100)}%</b><span>purity</span></div>` : ""}
      </div></div>
      ${labelled ? `<div class="legend">${Object.keys(FAM).map((f) => `<span><i style="background:${FAM_COLOR[f]};color:${FAM_COLOR[f]}"></i>${FAM[f]}</span>`).join("")}</div>` : ""}
      <div class="cards">${cards}</div>
      <div class="row" style="margin-top:14px;justify-content:space-between;flex-wrap:wrap"><p class="note" style="margin:0">${method === "kmeans" ? "k-means on each signal's magnitude spectrum, which ignores where in the beat it starts." : method === "acf" ? "k-means on each signal's autocorrelation, which also ignores where in the beat it starts." : "Divide and conquer on correlation distance between the shapes, as in the original pipeline. Seeded, so runs repeat."}</p>
      <button class="btn small secondary" id="dl" type="button">Download assignments</button></div>
    </div>`;
    $("dl").onclick = () => {
      const csv = "id,cluster\n" + batch.map((b, i) => `${b.id},${list.findIndex((m) => m.includes(i)) + 1}`).join("\n");
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
      a.download = "pulse-clusters.csv"; a.click(); URL.revokeObjectURL(a.href);
    };
  }

  function setMethod(m) {
    method = m;
    document.querySelectorAll("#method button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.m === m)));
    $("k-group").hidden = m === "dc"; $("dc-group").hidden = m !== "dc";
    $("method-hint").textContent = { kmeans: "Groups signals by frequency content, the best method in the project's original benchmark.",
      acf: "Groups signals by the rhythm in their autocorrelation, the feature the single-signal analyzer uses. Usually the most accurate.",
      dc: "The project's from-scratch splitter: pick a pivot, split at the median distance, recurse." }[m];
    if (batch.length >= 2) runBatch();
  }

  // ---------- wiring ----------
  function wireDrop(label, input, onFiles) {
    ["dragenter", "dragover"].forEach((ev) => label.addEventListener(ev, (e) => { e.preventDefault(); label.classList.add("over"); }));
    ["dragleave", "drop"].forEach((ev) => label.addEventListener(ev, (e) => { e.preventDefault(); label.classList.remove("over"); }));
    label.addEventListener("drop", (e) => onFiles([...e.dataTransfer.files]));
    input.addEventListener("change", () => { onFiles([...input.files]); input.value = ""; });
  }

  function setMode(m) {
    document.querySelectorAll("[data-mode]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.mode === m)));
    $("mode-one").hidden = m !== "one"; $("mode-batch").hidden = m !== "batch";
    $("title").textContent = m === "one" ? "Analyze a signal" : "Cluster a batch of signals";
    $("subtitle").textContent = m === "one" ? "Identify a 10-second ECG, PPG or blood-pressure segment, find its closest matches in a 1,000-segment library, and mark its most active stretch."
      : "Group many segments by similarity with the project's clustering algorithms, see each cluster's typical shape and closest pair, and download the result.";
  }

  document.querySelectorAll("[data-mode]").forEach((b) => b.addEventListener("click", () => setMode(b.dataset.mode)));
  document.querySelectorAll("#method button").forEach((b) => b.addEventListener("click", () => setMethod(b.dataset.m)));
  [["k", "k-out"], ["min", "min-out"], ["depth", "depth-out"]].forEach(([i, o]) => {
    $(i).addEventListener("input", () => ($(o).value = $(i).value));
    $(i).addEventListener("change", runBatch);
  });
  $("run").addEventListener("click", runBatch);
  $("use-lib").addEventListener("click", () => {
    if (!LIB) return;
    const n = +$("lib-n").value, r = rng(7);
    const idx = LIB.ids.map((_, i) => i);
    for (let i = idx.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [idx[i], idx[j]] = [idx[j], idx[i]]; }
    setBatch(idx.slice(0, n).map((i) => ({ id: LIB.ids[i], raw: LIB.x[i] })), "library sample");
  });
  wireDrop($("drop-one"), $("file-one"), async (files) => {
    if (!files.length || !LIB) return;
    try { analyze(parseSignal(await files[0].text()), files[0].name); document.querySelectorAll("#samples .chip").forEach((c) => c.setAttribute("aria-pressed", "false")); }
    catch (err) { errorOne(err.message); }
  });
  $("paste-go").addEventListener("click", () => {
    try { analyze(parseSignal($("paste").value), "Pasted values"); } catch (err) { errorOne(err.message); }
  });
  wireDrop($("drop-batch"), $("file-batch"), async (files) => {
    const items = [], bad = [];
    for (const f of files) {
      try { items.push({ id: f.name.replace(/\.(csv|txt)$/i, ""), raw: parseSignal(await f.text()) }); } catch (_) { bad.push(f.name); }
    }
    setBatch(items, bad.length ? `${bad.length} skipped: not a readable signal` : "your files");
  });

  sampleChips();
  setMethod("acf");
  loadLibrary().then(() => {
    const ecg = LIB.fam.indexOf("ECG");
    document.querySelector('#samples [data-fam="ECG"]').setAttribute("aria-pressed", "true");
    analyze(LIB.x[ecg], `Library segment ${LIB.ids[ecg]}`, ecg);
  }).catch(() => errorOne("The reference library failed to load. Refresh to try again."));
})();
