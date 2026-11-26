// Data: python export_site_data.py (preprocessed segments from data/, same as the pipeline).
const $ = (id) => document.getElementById(id);
const FAMILIES = { ECG: "ECG", PPG: "PPG", ABP: "Blood pressure", ARR: "Arrhythmia", STR: "Stress" };
const BENCH = [
  ["k-means on FFT spectrum, k=5", 5, 0.269, 0.299, 0.431],
  ["Divide and conquer on FFT spectrum", 64, 0.035, 0.237, 0.572],
  ["k-means, z-normalized Euclidean, k=5", 5, 0.037, 0.068, 0.298],
  ["Divide and conquer, correlation (original)", 64, 0.015, 0.142, 0.465],
  ["Agglomerative, correlation, k=5", 5, 0.014, 0.052, 0.278],
];
let D = null, fam = "ECG", pair = [0, 1];

function corrDist(a, b) {
  const n = a.length, ma = a.reduce((s, v) => s + v, 0) / n, mb = b.reduce((s, v) => s + v, 0) / n;
  let num = 0, da = 0, db = 0;
  for (let i = 0; i < n; i++) { num += (a[i] - ma) * (b[i] - mb); da += (a[i] - ma) ** 2; db += (b[i] - mb) ** 2; }
  return 1 - num / Math.sqrt(da * db);
}

function path(arr, W, H, lo, hi) {
  return arr.map((v, i) => `${i ? "L" : "M"}${((i / (arr.length - 1)) * W).toFixed(1)},${(H - ((v - lo) / (hi - lo)) * H).toFixed(1)}`).join("");
}

function drawPair() {
  const [a, b] = pair.map((i) => D[fam][i]);
  const all = a.x.concat(b.x), lo = Math.min(...all) - 0.3, hi = Math.max(...all) + 0.3;
  $("time").innerHTML = `<path class="b" d="${path(b.x, 600, 260, lo, hi)}"/><path class="a" d="${path(a.x, 600, 260, lo, hi)}"/>`;
  $("freq").innerHTML = `<path class="b" d="${path(b.spec, 600, 260, -0.05, 1.08)}"/><path class="a" d="${path(a.spec, 600, 260, -0.05, 1.08)}"/>`;
  $("d-time").textContent = corrDist(a.x, b.x).toFixed(2);
  $("d-freq").textContent = corrDist(a.spec, b.spec).toFixed(2);
}

function rate() {
  const items = D[fam];
  let closer = 0, total = 0;
  for (let i = 0; i < items.length; i++) for (let j = i + 1; j < items.length; j++) {
    total++;
    if (corrDist(items[i].spec, items[j].spec) < corrDist(items[i].x, items[j].x)) closer++;
  }
  $("rate").textContent = `For ${FAMILIES[fam].toLowerCase() === "ecg" || FAMILIES[fam] === "PPG" ? FAMILIES[fam] : FAMILIES[fam].toLowerCase()} segments, the spectra are closer than the shapes in ${closer} of ${total} pairs in this sample.`;
}

function pick(newFam) {
  fam = newFam;
  rate();
  document.querySelectorAll("#fam button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.f === fam)));
  const n = D[fam].length, i = Math.floor(Math.random() * n);
  let j = Math.floor(Math.random() * (n - 1)); if (j >= i) j++;
  pair = [i, j];
  drawPair();
}

function bench() {
  const max = BENCH[0][2];
  $("bench").innerHTML = BENCH.map(([name, k, ari, nmi, pur], i) => `<tr><td><div class="q-bar"><i style="width:${Math.max(3, (ari / max) * 100)}%;background:${i === 0 ? "var(--accent)" : "var(--ink-3)"}"></i><b>${name}</b></div></td><td>${k}</td><td>${ari.toFixed(3)}</td><td>${nmi.toFixed(3)}</td><td>${(pur * 100).toFixed(1)}%</td></tr>`).join("");
}

function multiples() {
  $("multiples").innerHTML = Object.keys(FAMILIES).map((f) => {
    const s = D[f][0], lo = Math.min(...s.x) - 0.2, hi = Math.max(...s.x) + 0.2, W = 256, H = 90;
    return `<div class="mult"><svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"><rect x="${s.l}" y="0" width="${s.r - s.l + 1}" height="${H}"/><path d="${path(s.x, W, H, lo, hi)}"/></svg><p><span>${FAMILIES[f]}</span><span>${s.l}–${s.r}</span></p></div>`;
  }).join("");
}

fetch("data.json").then((r) => r.json()).then((d) => {
  D = d;
  $("fam").innerHTML = Object.entries(FAMILIES).map(([k, v]) => `<button data-f="${k}" aria-pressed="false">${v}</button>`).join("");
  document.querySelectorAll("#fam button").forEach((b) => b.addEventListener("click", () => pick(b.dataset.f)));
  $("shuffle").addEventListener("click", () => pick(fam));
  pick("ARR"); bench(); multiples();
});
