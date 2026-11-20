// Competitor "post type" log — semi-manual by design. Nothing here fetches Instagram: the owner looks at public
// posts and pastes them; Claude classifies the *type* and records it. Captions are never stored verbatim
// (hook = a short paraphrase only).
//   npm run research:competitors -- add --account @x --url https://www.instagram.com/p/… --format carousel \
//        --slides 7 --theme "…" --category facial-device --structure "表紙→…" --headline-pattern "…" \
//        [--hook "…"] [--cta "…"] [--posted 2026-11-18] [--notes "…"] [--entered-by owner|claude]
//   npm run research:competitors -- check              validate log.csv (also after editing it in a spreadsheet)
//   npm run research:competitors -- summary [--days 30]   → research/competitors/summary.md
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { ROOT, config, jstIso, parseArgs } from "./lib.mjs";
import { parseCsv, writeCsv } from "../csv.mjs";

const FILE = path.join(ROOT, "research/competitors/log.csv");
export const COLS = ["recordedAt", "account", "postUrl", "postedAt", "format", "slides", "theme", "category", "structure", "headlinePattern", "hook", "cta", "notes", "enteredBy"];
const FORMATS = ["carousel", "reel", "image", "unknown"];
const FORMAT_JA = { carousel: "カルーセル", reel: "リール", image: "1枚画像", unknown: "不明" };

export const loadLog = () => (fs.existsSync(FILE) ? parseCsv(fs.readFileSync(FILE, "utf8")) : []);
const save = (rows) => { fs.mkdirSync(path.dirname(FILE), { recursive: true }); writeCsv(FILE, COLS, rows); };

export function checkRow(r, i = 0) {
  const errs = [], warns = [];
  const at = `row ${i + 2}`;
  const known = config().competitors;
  if (!/^@[A-Za-z0-9._]+$/.test(r.account ?? "")) errs.push(`${at}: account は @ から始まる ID`);
  else if (!known.includes(r.account)) warns.push(`${at}: ${r.account} は research/config.json の competitors にありません`);
  if (!/^https:\/\/www\.instagram\.com\/(p|reel|reels)\/[A-Za-z0-9_-]+\/?/.test(r.postUrl ?? "")) errs.push(`${at}: postUrl は https://www.instagram.com/p/… か /reel/… の公開投稿 URL`);
  if (!FORMATS.includes(r.format)) errs.push(`${at}: format は ${FORMATS.join(" / ")}`);
  if (r.slides && !/^\d+$/.test(r.slides)) errs.push(`${at}: slides は数字`);
  if (r.postedAt && !/^\d{4}-\d{2}-\d{2}$/.test(r.postedAt)) errs.push(`${at}: postedAt は YYYY-MM-DD`);
  for (const k of ["theme", "structure", "headlinePattern"]) if (!r[k]) errs.push(`${at}: ${k} が空です`);
  if ((r.hook ?? "").length > 40) errs.push(`${at}: hook は40字までの要約（キャプションや表紙の文をそのまま写さない）`);
  if (r.category && r.category !== "other" && !config().categories.some((c) => c.key === r.category)) warns.push(`${at}: category「${r.category}」は config にないキー`);
  return { errs, warns };
}

export function summarize(rows, days = 30, now = new Date()) {
  const since = now.getTime() - days * 864e5;
  const recent = rows.filter((r) => new Date(r.recordedAt).getTime() >= since);
  const count = (key) => Object.entries(recent.reduce((m, r) => ((m[r[key] || "—"] = (m[r[key] || "—"] ?? 0) + 1), m), {})).sort((a, b) => b[1] - a[1]);
  const tbl = (title, key, map = (x) => x) => `### ${title}\n\n| 項目 | 件数 |\n|---|---|\n${count(key).map(([k, n]) => `| ${map(k)} | ${n} |`).join("\n")}\n\n`;
  let md = `# 競合の投稿の「型」（直近${days}日・${recent.length}件）\n\n作成：${jstIso(now)}。出典は各投稿の URL（オーナーが確認した公開投稿）。キャプション本文は保存していません。\n\n`;
  if (!recent.length) return md + "（記録なし）\n";
  md += tbl("アカウント別", "account") + tbl("形式", "format", (k) => FORMAT_JA[k] ?? k) + tbl("カテゴリ", "category") + tbl("見出しの作り方", "headlinePattern") + tbl("構成", "structure");
  md += `### 記録一覧\n\n| 記録日 | アカウント | 形式 | テーマ | 見出しの作り方 | 表紙の要点 | URL |\n|---|---|---|---|---|---|---|\n`;
  for (const r of [...recent].sort((a, b) => b.recordedAt.localeCompare(a.recordedAt)))
    md += `| ${r.recordedAt.slice(0, 10)} | ${r.account} | ${FORMAT_JA[r.format] ?? r.format}${r.slides ? `・${r.slides}枚` : ""} | ${r.theme} | ${r.headlinePattern} | ${r.hook ?? ""} | ${r.postUrl} |\n`;
  md += `\n> 参考の使い方：テーマや構成の傾向を知るためだけに使い、文言や画像は真似しない。このアカウントの世界観（A案／B案）は変えない。\n`;
  return md;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const a = parseArgs(process.argv.slice(2));
  const cmd = a._[0];
  const rows = loadLog();
  if (cmd === "add") {
    const r = {
      recordedAt: jstIso(), account: a.account, postUrl: a.url, postedAt: a.posted ?? "", format: a.format, slides: a.slides ?? "",
      theme: a.theme, category: a.category ?? "", structure: a.structure, headlinePattern: a["headline-pattern"], hook: a.hook ?? "",
      cta: a.cta ?? "", notes: a.notes ?? "", enteredBy: a["entered-by"] ?? "owner",
    };
    const { errs, warns } = checkRow(r, rows.length);
    if (rows.some((x) => x.postUrl.replace(/\/$/, "") === (r.postUrl ?? "").replace(/\/$/, ""))) errs.push("この URL は記録済みです");
    warns.forEach((w) => console.log("△ " + w));
    if (errs.length) { errs.forEach((e) => console.log("✗ " + e)); process.exit(1); }
    save([...rows, r]);
    console.log(`✓ 記録しました（${rows.length + 1}件目）→ research/competitors/log.csv`);
  } else if (cmd === "check") {
    let bad = 0;
    rows.forEach((r, i) => { const { errs, warns } = checkRow(r, i); errs.forEach((e) => console.log("✗ " + e)); warns.forEach((w) => console.log("△ " + w)); bad += errs.length; });
    console.log(`${rows.length} rows, ${bad} error(s)`);
    process.exit(bad ? 1 : 0);
  } else if (cmd === "summary") {
    const md = summarize(rows, Number(a.days ?? 30));
    fs.mkdirSync(path.dirname(FILE), { recursive: true });
    fs.writeFileSync(path.join(ROOT, "research/competitors/summary.md"), md);
    console.log("→ research/competitors/summary.md");
  } else {
    console.log("usage: npm run research:competitors -- add|check|summary …");
    process.exit(1);
  }
}
