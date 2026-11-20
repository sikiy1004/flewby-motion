// Sale calendar: research/calendar.json (persistent, committed)
//   npm run research:calendar                 list ongoing + upcoming events (next 45 days)
//   npm run research:calendar -- check        schema, time order, duplicates, ended events
//   npm run research:calendar -- snapshot <run|latest>   write research/runs/<run>/sales.md
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import Ajv from "ajv";
import { readJson, runDir, parseArgs, latestRun, jstIso } from "./lib.mjs";

const ajv = new Ajv({ allErrors: true, strict: false });
const validate = ajv.compile(readJson("research/schema/calendar.schema.json"));
const STATUS = { confirmed: "公式で確認", reported: "公式発表の報道等で確認", expected: "予想（未発表）" };
const fmt = (iso) => `${iso.slice(5, 10).replace("-", "/")} ${iso.slice(11, 16)}`;

export const loadCalendar = () => readJson("research/calendar.json");
export const findEvent = (id, cal = loadCalendar()) => cal.events.find((e) => e.id === id) ?? null;

export function checkCalendar(cal = loadCalendar(), now = new Date()) {
  const errors = [], warnings = [];
  if (!validate(cal)) validate.errors.forEach((e) => errors.push(`calendar.json${e.instancePath} ${e.message}`));
  const ids = new Set();
  for (const e of cal.events ?? []) {
    if (ids.has(e.id)) errors.push(`${e.id}: id が重複しています`);
    ids.add(e.id);
    if (new Date(e.end) <= new Date(e.start)) errors.push(`${e.id}: 終了が開始より前です`);
    if (new Date(e.end) < now) warnings.push(`${e.id}: 終了済み（${fmt(e.end)}）。投稿案には使えません`);
    if (e.status === "expected") warnings.push(`${e.id}: 予想の日程です。公式発表を確認したら status を更新してください`);
  }
  return { errors, warnings };
}

/** Ongoing or starting within `days`. */
export function upcoming(now = new Date(), days = 45, cal = loadCalendar()) {
  const until = now.getTime() + days * 864e5;
  return cal.events.filter((e) => new Date(e.end) >= now && new Date(e.start).getTime() <= until).sort((a, b) => a.start.localeCompare(b.start));
}

export function calendarTable(events, now = new Date()) {
  if (!events.length) return "（該当なし）\n";
  let md = "| 状態 | イベント | 期間 | 確度 | 出典 |\n|---|---|---|---|---|\n";
  for (const e of events) {
    const live = new Date(e.start) <= now ? "開催中" : "予定";
    md += `| ${live} | ${e.name}（\`${e.id}\`） | ${fmt(e.start)} 〜 ${fmt(e.end)} | ${STATUS[e.status]} | ${e.sources.map((s) => `[${s.title ?? "出典"}](${s.url})`).join("<br>")}（${fmt(e.sources[0].fetchedAt)}取得） |\n`;
  }
  return md;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const a = parseArgs(process.argv.slice(2));
  const [cmd, r] = a._;
  const cal = loadCalendar();
  if (cmd === "check") {
    const c = checkCalendar(cal);
    c.errors.forEach((e) => console.log("✗ " + e));
    c.warnings.forEach((w) => console.log("△ " + w));
    console.log(`${cal.events.length} events, ${c.errors.length} error(s)`);
    process.exit(c.errors.length ? 1 : 0);
  } else if (cmd === "snapshot") {
    const runId = !r || r === "latest" ? latestRun() : r;
    const md = `# セール暦（今後45日）${runId}\n\n作成：${jstIso()}（research/calendar.json 更新：${cal.updatedAt}）\n\n${calendarTable(upcoming())}`;
    fs.writeFileSync(path.join(runDir(runId), "sales.md"), md);
    console.log(`→ research/runs/${runId}/sales.md`);
  } else {
    const ev = upcoming();
    console.log(ev.map((e) => `${new Date(e.start) <= new Date() ? "開催中" : "予定  "} ${fmt(e.start)}〜${fmt(e.end)}  ${e.name}  [${e.status}]  ${e.id}`).join("\n") || "（今後45日の予定なし）");
  }
}
