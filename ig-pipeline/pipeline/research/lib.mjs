// Shared helpers for the research layer.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
export const readJson = (f) => JSON.parse(fs.readFileSync(path.isAbsolute(f) ? f : path.join(ROOT, f), "utf8"));
export const writeJson = (f, v) => {
  const p = path.isAbsolute(f) ? f : path.join(ROOT, f);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, JSON.stringify(v, null, 2) + "\n");
};
export const config = () => readJson("research/config.json");

/** ISO 8601 in JST with offset, e.g. 2026-11-20T14:05:09+09:00 */
export function jstIso(d = new Date()) {
  const j = new Date(d.getTime() + 9 * 3600e3).toISOString().replace(/\.\d+Z$/, "");
  return `${j}+09:00`;
}
/** Run id: YYYYMMDD-HHmm (JST) */
export const newRunId = (d = new Date()) => jstIso(d).slice(0, 16).replace(/[-:]/g, "").replace("T", "-");
export const runDir = (id) => path.join(ROOT, "research/runs", id);
export function latestRun() {
  const dir = path.join(ROOT, "research/runs");
  const ids = fs.existsSync(dir) ? fs.readdirSync(dir).filter((d) => /^\d{8}-\d{4}/.test(d)).sort() : [];
  return ids.at(-1) ?? null;
}

/** Minimal .env loader (no dependency). Existing environment variables win. */
export function loadEnv() {
  const f = path.join(ROOT, ".env");
  if (!fs.existsSync(f)) return;
  for (const line of fs.readFileSync(f, "utf8").split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
    if (m && !(m[1] in process.env)) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
  }
}

export function parseArgs(argv) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const k = a.slice(2);
      if (argv[i + 1] !== undefined && !argv[i + 1].startsWith("--")) out[k] = argv[++i];
      else out[k] = true;
    } else out._.push(a);
  }
  return out;
}
