const PASS_MARK = 10;
function parseCSV(text) {
  const lines = text.trim().split(/\r?\n/);
  const header = lines[0].split(";").map((h) => h.replace(/"/g, ""));
  return lines.slice(1).map((line) => {
    const cells = line.split(";").map((c) => c.replace(/"/g, ""));
    const row = {};
    header.forEach((h, i) => { const n = Number(cells[i]); row[h] = cells[i] !== "" && !Number.isNaN(n) ? n : cells[i]; });
    row.passed = row.G3 >= PASS_MARK ? 1 : 0;
    return row;
  });
}
function columnsFor(rows, withGrades) {
  const skip = new Set(["G1", "G2", "G3", "passed"]);
  const base = Object.keys(rows[0]).filter((c) => !skip.has(c));
  return withGrades ? base.concat(["G1", "G2"]) : base;
}
function fitEncoder(rows, cols) {
  const spec = cols.map((c) => {
    if (typeof rows[0][c] === "string") return { col: c, type: "cat", levels: Array.from(new Set(rows.map((r) => r[c]))).sort() };
    const v = rows.map((r) => r[c]);
    const mean = v.reduce((a, b) => a + b, 0) / v.length;
    const sd = Math.sqrt(v.reduce((a, b) => a + (b - mean) ** 2, 0) / v.length) || 1;
    return { col: c, type: "num", mean, sd };
  });
  const names = spec.flatMap((s) => (s.type === "cat" ? s.levels.map((l) => s.col + "=" + l) : [s.col]));
  const transform = (r) => spec.flatMap((s) => (s.type === "cat" ? s.levels.map((l) => (r[s.col] === l ? 1 : 0)) : [(r[s.col] - s.mean) / s.sd]));
  return { names, transform };
}
const sigmoid = (z) => 1 / (1 + Math.exp(-z));
function trainLogReg(X, y, opt) {
  const o = Object.assign({ C: 1, iters: 1500, lr: 0.15 }, opt || {});
  const n = X.length, d = X[0].length, lam = 1 / (o.C * n);
  const w = new Array(d).fill(0), vw = new Array(d).fill(0); let b = 0, vb = 0;
  for (let t = 0; t < o.iters; t++) {
    const gw = new Array(d).fill(0); let gb = 0;
    for (let i = 0; i < n; i++) {
      const xi = X[i]; let z = b;
      for (let j = 0; j < d; j++) z += w[j] * xi[j];
      const e = sigmoid(z) - y[i]; gb += e;
      for (let j = 0; j < d; j++) gw[j] += e * xi[j];
    }
    for (let j = 0; j < d; j++) { vw[j] = 0.9 * vw[j] - o.lr * (gw[j] / n + lam * w[j]); w[j] += vw[j]; }
    vb = 0.9 * vb - o.lr * (gb / n); b += vb;
  }
  return { w, b };
}
function trainModel(rows, cols, opt) {
  const enc = fitEncoder(rows, cols);
  const m = trainLogReg(rows.map(enc.transform), rows.map((r) => r.passed), opt);
  return { enc, w: m.w, b: m.b };
}
function predict(model, row) {
  const x = model.enc.transform(row);
  const items = x.map((v, j) => ({ name: model.enc.names[j], value: v * model.w[j] }));
  const p = sigmoid(items.reduce((a, c) => a + c.value, model.b));
  return { p, items };
}
function rocAuc(scores, labels) {
  const idx = scores.map((s, i) => i).sort((a, b) => scores[a] - scores[b]);
  const ranks = new Array(scores.length); let i = 0;
  while (i < idx.length) { let j = i; while (j + 1 < idx.length && scores[idx[j + 1]] === scores[idx[i]]) j++; const r = (i + j) / 2 + 1; for (let k = i; k <= j; k++) ranks[idx[k]] = r; i = j + 1; }
  let sum = 0, nPos = 0; labels.forEach((l, k) => { if (l === 1) { sum += ranks[k]; nPos++; } });
  return (sum - (nPos * (nPos + 1)) / 2) / (nPos * (labels.length - nPos));
}
function mulberry(seed) { return function () { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
// One stratified 5-fold repeat; returns per-fold metrics.
function cvRepeat(rows, withGrades, rep, folds) {
  const cols = columnsFor(rows, withGrades), rand = mulberry(42 + rep), fold = new Array(rows.length), out = [];
  [0, 1].forEach((cls) => {
    const ids = rows.map((r, i) => i).filter((i) => rows[i].passed === cls);
    for (let i = ids.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); const t = ids[i]; ids[i] = ids[j]; ids[j] = t; }
    ids.forEach((id, k) => (fold[id] = k % folds));
  });
  for (let f = 0; f < folds; f++) {
    const tr = rows.filter((_, i) => fold[i] !== f), te = rows.filter((_, i) => fold[i] === f);
    const m = trainModel(tr, cols), ps = te.map((r) => predict(m, r).p), ys = te.map((r) => r.passed);
    const fails = ys.map((y, i) => i).filter((i) => ys[i] === 0);
    out.push({ acc: ps.filter((p, i) => (p >= 0.5 ? 1 : 0) === ys[i]).length / ys.length, auc: rocAuc(ps, ys), rec: fails.filter((i) => ps[i] < 0.5).length / fails.length });
  }
  return out;
}
function defaultsFor(rows) {
  const d = {};
  Object.keys(rows[0]).forEach((c) => {
    if (typeof rows[0][c] === "string") { const cnt = {}; rows.forEach((r) => (cnt[r[c]] = (cnt[r[c]] || 0) + 1)); d[c] = Object.entries(cnt).sort((a, b) => b[1] - a[1])[0][0]; }
    else { const v = rows.map((r) => r[c]).sort((a, b) => a - b); d[c] = v[Math.floor(v.length / 2)]; }
  });
  return d;
}
