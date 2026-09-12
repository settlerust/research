// Time the tunable search in WASM under Node on sampled main-phase views, either at fixed
// depths with the clock off (to measure transitions per second) or under named search
// requests with a real clock (to see what a browser budget completes).
// Usage:
//   node analysis/browser_budget_wasm.mjs rate VIEWS.jsonl OUT.json --wasm DIR [--depths 2,3] [--repeats 3]
//   node analysis/browser_budget_wasm.mjs budget VIEWS.jsonl OUT.json --wasm DIR --configs CONFIGS.json [--repeats 3]
// CONFIGS.json maps a label to a search request object. Views come from the server's
// `structure --views` tool. Every analysis is repeated and the fastest repeat is kept, so a
// loaded machine biases the timings less; CPU time is recorded beside wall time.
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const [mode, viewsPath, outPath, ...rest] = process.argv.slice(2);
if (!["rate", "budget"].includes(mode) || !viewsPath || !outPath) {
  throw new Error("usage: browser_budget_wasm.mjs rate|budget VIEWS.jsonl OUT.json --wasm DIR [--depths 2,3] [--configs FILE] [--repeats N] [--limit N]");
}
const option = (name, fallback) => (rest.includes(name) ? rest[rest.indexOf(name) + 1] : fallback);
const wasmDir = path.resolve(option("--wasm", "../web/lib/agents/wasm"));
const depths = option("--depths", "2,3").split(",").map(Number);
const repeats = Number(option("--repeats", "3"));
const limit = Number(option("--limit", "Infinity"));
const configs = mode === "budget" ? JSON.parse(readFileSync(option("--configs"), "utf8")) : null;
const rows = readFileSync(viewsPath, "utf8").split("\n").filter(Boolean).map((line) => JSON.parse(line)).slice(0, limit);

const { default: init, ExpectimaxPlayer } = await import(pathToFileURL(path.join(wasmDir, "expectimax.js")).href);
await init({ module_or_path: readFileSync(path.join(wasmDir, "expectimax_bg.wasm")) });

function analyse(row, search) {
  const player = new ExpectimaxPlayer();
  try {
    for (const batch of row.history) player.on_events(JSON.stringify(batch));
    const cpu = process.cpuUsage();
    const started = performance.now();
    const report = JSON.parse(player.analyze(JSON.stringify({ view: row.view, search })));
    const wallMs = performance.now() - started;
    const used = process.cpuUsage(cpu);
    const s = report.statistics;
    return { wallMs, cpuMs: (used.user + used.system) / 1000, transitions: s.transitions, leaves: s.leaves,
      depthCompleted: s.depth_completed, aborted: Boolean(s.aborted), candidates: report.candidates.length,
      cacheHits: s.cache_hits ?? 0, cachedTransitions: s.cached_transitions ?? 0 };
  } finally {
    player.free();
  }
}
function best(row, search) {
  let kept;
  for (let i = 0; i < repeats; i++) {
    const r = analyse(row, search);
    if (!kept || r.wallMs < kept.wallMs) kept = r;
  }
  return kept;
}
// Warm the module once so the first timed analysis does not carry start-up cost.
analyse(rows[0], { depth: 1, iterative: false, time_budget_ms: 0 });

const arms = mode === "rate"
  ? depths.map((depth) => [`depth ${depth}`, { depth, iterative: false, time_budget_ms: 0, samples: 4, scenarios: 8, inner_scenarios: 4, node_budget: 4_000_000 }])
  : Object.entries(configs);
const results = [];
for (const row of rows) {
  const line = [];
  for (const [label, search] of arms) {
    const r = best(row, search);
    results.push({ seed: row.seed, turn: row.turn, seat: row.seat, label, search, ...r });
    line.push(`${label}: ${r.wallMs.toFixed(0)} ms (cpu ${r.cpuMs.toFixed(0)}), ${r.transitions} transitions, depth ${r.depthCompleted}${r.aborted ? " aborted" : ""}`);
  }
  console.error(`seed ${row.seed} turn ${row.turn} seat ${row.seat}: ${line.join("; ")}`);
}
writeFileSync(outPath, JSON.stringify({ node: process.version, mode, views: rows.length, repeats, wasm: wasmDir, arms: Object.fromEntries(arms), results }, null, 1));
console.log(`wrote ${results.length} measurements to ${outPath}`);
