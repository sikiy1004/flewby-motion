// Post ideas of a run: research/runs/<run>/ideas.json  →  ideas.md (投稿案リスト)
//   npm run research:ideas -- check <run|latest>     schema + freshness + expiry checks
//   npm run research:ideas -- render <run|latest>    write ideas.md (runs check first)
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { pathToFileURL } from "node:url";
import Ajv from "ajv";
import { readJson, runDir, parseArgs, latestRun, config, jstIso } from "./lib.mjs";
import { loadEvidence } from "./evidence.mjs";
import { lintTexts } from "./lint.mjs";

const ajv = new Ajv({ allErrors: true, strict: false });
const validate = ajv.compile(readJson("research/schema/ideas.schema.json"));

export const ideaHash = (idea) => crypto.createHash("sha256").update(JSON.stringify(idea)).digest("hex").slice(0, 16);
export const resolveRun = (r) => (!r || r === "latest" ? latestRun() : r);
export const loadIdeas = (runId) => readJson(path.join(runDir(runId), "ideas.json"));

const yen = (n) => (n == null ? "—" : "¥" + Number(n).toLocaleString("ja-JP"));
const fmt = (iso) => (iso ? iso.slice(5, 16).replace("T", " ").replace("-", "/") : "");
const hoursSince = (iso, now) => (now - new Date(iso)) / 3600e3;

/** Errors block the idea list; warnings are shown in it. */
export function checkIdeas(doc, runId, now = new Date()) {
  const errors = [], warnings = [];
  if (!validate(doc)) validate.errors.forEach((e) => errors.push(`ideas.json${e.instancePath} ${e.message}`));
  const ev = loadEvidence(runId);
  const maxAge = config().freshness.priceMaxAgeHours;
  const ids = new Set();
  for (const idea of doc.ideas ?? []) {
    const P = idea.id;
    if (ids.has(P)) errors.push(`${P}: id が重複しています`);
    ids.add(P);
    // copy rules already at idea stage, so a violating idea never reaches the owner's list
    for (const f of lintTexts([["theme", idea.theme], ["cover.kicker", idea.cover?.kicker], ["cover.lead", idea.cover?.lead], ["reel.headline", idea.reel?.headline], ["reel.sub", idea.reel?.sub], ["reel.accent", idea.reel?.accent]]))
      (f.level === "error" ? errors : warnings).push(`${P}: ${f.where}「${f.match}」${f.reason}`);
    if (idea.design === "B" && !idea.reel) errors.push(`${P}: B案には reel.headline が必要です`);
    if (idea.design === "A" && idea.format.startsWith("reel")) errors.push(`${P}: A案に reel の形式は使えません`);
    if (idea.format === "compare" && idea.products.length < 2) errors.push(`${P}: 比較は商品2〜4点です`);
    if (idea.timing?.windowEnd && new Date(idea.timing.windowEnd) < now) errors.push(`${P}: 連動するセール（${idea.timing.event ?? ""}）は ${fmt(idea.timing.windowEnd)} に終了しています`);
    if (new Date(idea.timing?.recommended + "T23:59:59+09:00") < now) errors.push(`${P}: 推奨日 ${idea.timing.recommended} が過ぎています`);
    for (const p of idea.products) {
      const e = ev[p.productId];
      if (!e) { errors.push(`${P}: 出典ファイルがありません（evidence/${p.productId}.json）`); continue; }
      const pr = e.price;
      const used = pr.basis === "sale" ? pr.sale : pr.basis === "regular" ? pr.regular : pr.rakuten;
      if (!used?.fetchedAt) errors.push(`${P}/${p.productId}: 価格に取得日時がありません`);
      else if (hoursSince(used.fetchedAt, now) > maxAge) errors.push(`${P}/${p.productId}: 価格の取得から ${Math.round(hoursSince(used.fetchedAt, now))} 時間経っています（上限 ${maxAge} 時間）。再取得してください`);
      if (pr.sale?.end && new Date(pr.sale.end) < now) errors.push(`${P}/${p.productId}: セール価格の期限（${fmt(pr.sale.end)}）が切れています`);
      if (pr.basis === "unverified") warnings.push(`${P}/${p.productId}: 価格が通常かセールか未確認（原稿データの生成前に確定が必要）`);
      if (e.status !== "complete") warnings.push(`${P}/${p.productId}: 出典ファイルが雛形のまま（名前・スペック・ポイントは公式情報で記入が必要）`);
      if (e.image?.rights === "placeholder") warnings.push(`${P}/${p.productId}: 商品画像はレイアウト確認用（公開には自分の写真か使用許諾のある画像が必要）`);
    }
  }
  const b = (doc.ideas ?? []).filter((i) => i.design === "B").length, n = (doc.ideas ?? []).length;
  if (n >= 3 && b / n > 0.4) warnings.push(`B案が ${b}/${n} 件です（目安は全体の約2割）`);
  if (doc.testData) warnings.push("テスト用データから作った案です（公開不可）");
  return { errors, warnings };
}

export function renderIdeas(doc, runId, checks) {
  const ev = loadEvidence(runId);
  const priceCell = (pid) => {
    const e = ev[pid]; if (!e) return "—";
    const pr = e.price, used = pr.basis === "sale" ? pr.sale : pr.basis === "regular" ? pr.regular : pr.rakuten;
    const kind = { sale: `セール${pr.sale?.end ? `〜${fmt(pr.sale.end)}` : ""}`, regular: "通常", unverified: "未確認" }[pr.basis];
    return `${yen(pr.display)}（${kind}・${fmt(used?.fetchedAt)}取得）`;
  };
  let md = `# 投稿案リスト ${runId}\n\n作成：${doc.createdAt}${doc.testData ? "　**※テスト用データ（架空の商品）から作った案です。公開できません。**" : ""}\n\n`;
  if (doc.summary) md += `${doc.summary}\n\n`;
  md += `| ID | テーマ | 対象商品（価格） | デザイン | 表紙の英単語 | 見出し案 | 推奨タイミング |\n|---|---|---|---|---|---|---|\n`;
  for (const i of doc.ideas) {
    const prods = i.products.map((p) => `${p.label}<br>${priceCell(p.productId)}`).join("<br>");
    const head = i.design === "B" ? `${i.reel.headline.replace(/\n/g, "")}<br><sub>${i.reel.sub ?? ""}</sub>` : i.cover.lead.replace(/\n/g, "");
    const word = [i.cover.word, ...(i.cover.wordAlternatives ?? [])].map((w, k) => (k ? w : `**${w.toUpperCase()}**`)).join(" / ");
    const timing = `${i.timing.recommended}${i.timing.event ? `<br>${i.timing.event}` : ""}`;
    md += `| ${i.id} | ${i.theme} | ${prods} | ${i.design === "A" ? "A案 カルーセル" : "B案 リール"}（${i.format}） | ${word} | ${head} | ${timing} |\n`;
  }
  md += `\n## 各案の詳細\n`;
  for (const i of doc.ideas) {
    md += `\n### ${i.id}　${i.theme}\n\n`;
    if (i.angle) md += `- 切り口：${i.angle}\n`;
    md += `- なぜ今：${i.why}\n- タイミング：${i.timing.recommended}${i.timing.event ? `（${i.timing.event}${i.timing.windowStart ? ` ${fmt(i.timing.windowStart)}〜${fmt(i.timing.windowEnd)}` : ""}）` : ""}。${i.timing.reason}\n`;
    md += `- 表紙：${i.cover.kicker ? `${i.cover.kicker} ／ ` : ""}**${i.cover.word.toUpperCase()}** ／ ${i.cover.lead.replace(/\n/g, " ")}（オーロラ：${i.aurora}）\n`;
    if (i.reel) md += `- リール：${i.reel.headline.replace(/\n/g, " ")} ／ ${i.reel.sub ?? ""}${i.reel.accent ? ` ／ ${i.reel.accent}` : ""}\n`;
    if (i.hashtags?.length) md += `- ハッシュタグ案：${i.hashtags.join(" ")}\n`;
    if (i.risks?.length) md += `- 注意：${i.risks.join(" ／ ")}\n`;
    md += `- 出典：\n${i.sources.map((s) => `  - ${s.title ?? s.url}（${s.url}・${fmt(s.fetchedAt)}取得）`).join("\n")}\n`;
  }
  if (checks.warnings.length) md += `\n## 確認が必要な点\n\n${checks.warnings.map((w) => `- ${w}`).join("\n")}\n`;
  md += `\n---\n承認するには、ターミナルで次を実行してください（例：I01 と I03 を承認）：\n\n\`\`\`bash\nnpm run research:approve -- ${runId} I01 I03\n\`\`\`\n`;
  return md;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const a = parseArgs(process.argv.slice(2));
  const [cmd, r] = a._;
  const runId = resolveRun(r);
  if (!runId || !["check", "render"].includes(cmd)) { console.log("usage: npm run research:ideas -- check|render <run|latest>"); process.exit(1); }
  const doc = loadIdeas(runId);
  const c = checkIdeas(doc, runId);
  c.errors.forEach((e) => console.log("✗ " + e));
  c.warnings.forEach((w) => console.log("△ " + w));
  if (c.errors.length) { console.log(`${c.errors.length} error(s) — 投稿案リストは作りません`); process.exit(1); }
  if (cmd === "render") {
    fs.writeFileSync(path.join(runDir(runId), "ideas.md"), renderIdeas(doc, runId, c));
    console.log(`→ research/runs/${runId}/ideas.md`);
  } else console.log(`ok: ${doc.ideas.length} idea(s)`);
}
