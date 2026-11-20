// Manuscript (原稿データ) for an APPROVED idea → research/runs/<run>/drafts/<post-id>/
//   npm run research:draft -- <run|latest> <idea-id> [--allow-placeholder]
// Builds data that matches data/schema/{product,post}.schema.json exactly, only from the approved idea and
// complete evidence files, then checks it. Nothing is written to data/ here (that is research:install).
// --allow-placeholder: accept layout-only images (rights "placeholder"); the post id gets "-layout-only".
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { ROOT, readJson, writeJson, runDir, parseArgs, config, jstIso } from "./lib.mjs";
import { loadEvidence, schemaErrors } from "./evidence.mjs";
import { loadIdeas, checkIdeas, resolveRun } from "./ideas.mjs";
import { approvalProblem } from "./approve.mjs";
import { renderCaption } from "./caption.mjs";
import { lintTexts, postTexts } from "./lint.mjs";
import { validateProducts, validatePost } from "../validate.mjs";
import { writeCsv, productToRow, postToRow, PRODUCT_COLS, POST_COLS } from "../csv.mjs";

const fmtTime = (iso) => iso.slice(0, 16).replace("T", " ");
const short = (iso) => iso.slice(5, 16).replace("T", " ").replace("-", "/");
const nums = (s) => (String(s ?? "").match(/\d[\d,.]*/g) ?? []).map((n) => n.replace(/,/g, "").replace(/\.$/, ""));

/** Evidence must back every value we print. Returns error strings. */
function evidenceProblems(e, testData) {
  const P = e.productId, errs = [], warns = [];
  schemaErrors(e).forEach((x) => errs.push(`${P}: 出典ファイルの形式 ${x}`));
  if (e.status !== "complete") errs.push(`${P}: 出典ファイルが雛形のままです（status を complete にできるまで公式情報で記入）`);
  for (const k of ["category", "brand", "name"]) if (!e.fields?.[k]?.value) errs.push(`${P}: fields.${k}（${{ category: "カテゴリ", brand: "ブランド", name: "商品名" }[k]}）の値と出典がありません`);
  const pr = e.price;
  if (pr.basis === "unverified") errs.push(`${P}: 価格が通常価格かセール価格か確定していません（price.basis）`);
  const used = pr.basis === "sale" ? pr.sale : pr.basis === "regular" ? pr.regular : null;
  if (pr.basis !== "unverified") {
    if (!used) errs.push(`${P}: price.${pr.basis} がありません`);
    else if (used.value !== pr.display) errs.push(`${P}: 表示価格 ${pr.display} と price.${pr.basis}.value ${used.value} が一致しません`);
  }
  if (pr.basis === "sale") {
    if (!pr.sale?.end) errs.push(`${P}: セール価格に終了日時（price.sale.end）がありません`);
    if (!pr.sale?.event && !pr.sale?.label) errs.push(`${P}: セール名（price.sale.event）がありません`);
    if (!pr.regular) warns.push(`${P}: セール価格に対する通常価格（price.regular）が記録されていません`);
  }
  if (!Object.keys(e.specs ?? {}).length) errs.push(`${P}: スペックが1つもありません`);
  for (const [k, v] of Object.entries(e.specs ?? {})) if (/要確認/.test(v.value ?? "") || !v.value) errs.push(`${P}: specs.${k} が未確認です`);
  if (!(e.points ?? []).length) errs.push(`${P}: ポイントが1つもありません`);
  for (const [i, pt] of (e.points ?? []).entries()) {
    if (pt.basis === "spec" && !(pt.specRef in (e.specs ?? {}))) errs.push(`${P}: points[${i}] の根拠スペック「${pt.specRef ?? ""}」が specs にありません`);
    if (pt.basis === "official-quote" && (!pt.url || !pt.fetchedAt)) errs.push(`${P}: points[${i}] は公式表現の引用ですが、引用元 URL・取得日時がありません`);
    if (pt.basis === "official-quote" && !/^「.*」$/.test(pt.text)) errs.push(`${P}: points[${i}] は公式表現の引用なので「」で囲んでください`);
  }
  if (e.image?.rights === "placeholder") warns.push(`${P}: 商品画像はレイアウト確認用です（公開不可）`);
  const urls = JSON.stringify(e).match(/"url":"([^"]+)"/g) ?? [];
  if (!testData && urls.some((u) => u.includes('"url":"fixture:'))) errs.push(`${P}: テスト用データ（fixture:）の出典が含まれています`);
  return { errs, warns };
}

function nextIssue(currentId) {
  const dir = path.join(ROOT, "data/posts");
  const posts = fs.readdirSync(dir).filter((f) => f.endsWith(".json")).map((f) => readJson(path.join(dir, f)));
  const same = posts.find((p) => p.id === currentId);
  if (same) return same.collection;
  const number = Math.max(1, ...posts.map((p) => p.collection.number));
  const issue = Math.max(0, ...posts.filter((p) => p.collection.number === number).map((p) => p.collection.issue)) + 1;
  return { number, issue };
}

/** The only entry point used by the commands: approval is always checked first. */
export function buildDraft(runId, ideaId, opts = {}) {
  const ap = approvalProblem(runId, ideaId);
  if (ap) return { errors: [ap], warnings: [], stoppedBeforeGeneration: true };
  return generateDraft(runId, ideaId, opts);
}

/** Generation + checks, without the approval gate. Not exposed as a command; used by buildDraft and by tests. */
export function generateDraft(runId, ideaId, { allowPlaceholder = false, now = new Date() } = {}) {
  const errors = [], warnings = [];
  const doc = loadIdeas(runId);
  const idea = doc.ideas.find((i) => i.id === ideaId);
  const cfg = config();
  const T = readJson("tokens/tokens.json");
  const ideaChecks = checkIdeas({ ...doc, ideas: [idea] }, runId, now);
  errors.push(...ideaChecks.errors);
  const evAll = loadEvidence(runId);
  const evs = idea.products.map((p) => evAll[p.productId]).filter(Boolean);
  for (const e of evs) { const r = evidenceProblems(e, !!doc.testData); errors.push(...r.errs); warnings.push(...r.warns); }
  const placeholder = evs.some((e) => e.image?.rights === "placeholder");
  if (placeholder && !allowPlaceholder) errors.push("レイアウト確認用の画像が含まれています。自分の写真か使用許諾のある画像に差し替えるか、レイアウト確認だけなら --allow-placeholder を付けてください");
  if (errors.length) return { errors, warnings, stoppedBeforeGeneration: true };

  // ---------- products (exactly the engine schema) ----------
  const products = evs.map((e) => {
    const cat = cfg.categories.find((c) => c.label === e.fields.category?.value);
    const p = {
      id: e.productId,
      category: e.fields.category?.value ?? cat?.label,
      categoryEn: cat?.labelEn,
      brand: e.fields.brand.value,
      name: e.fields.name.value,
      nameJa: e.fields.nameJa?.value,
      price: e.price.display,
      image: `assets/products/raw/${e.productId}.jpg`,
      specs: Object.fromEntries(Object.entries(e.specs).map(([k, v]) => [k, String(v.value)])),
      points: e.points.map((pt) => pt.text),
      links: Object.fromEntries(Object.entries({ rakuten: e.links?.rakuten, amazon: e.links?.amazon }).filter(([, v]) => v)),
    };
    for (const k of Object.keys(p)) if (p[k] === undefined) delete p[k];
    return p;
  });

  // ---------- post ----------
  const priceTimes = evs.map((e) => (e.price.basis === "sale" ? e.price.sale : e.price.regular).fetchedAt).sort();
  const sales = evs.filter((e) => e.price.basis === "sale");
  let priceDate = fmtTime(priceTimes[0]);
  if (sales.length) {
    const end = sales.map((e) => e.price.sale.end).sort()[0];
    const ev = [...new Set(sales.map((e) => e.price.sale.event ?? e.price.sale.label))].join("・");
    priceDate += `（${ev}価格を含む・${short(end)}まで）`;
  }
  const postId = `${idea.timing.recommended.replace(/-/g, "")}-${idea.id.toLowerCase()}${placeholder ? "-layout-only" : ""}`;
  const post = {
    id: postId,
    collection: nextIssue(postId),
    priceDate,
    cover: { word: idea.cover.word, ...(idea.cover.kicker ? { kicker: idea.cover.kicker } : {}), lead: idea.cover.lead, aurora: idea.aurora, hero: products[0].id },
    products: products.map((p) => p.id),
    ...(products.length >= 2 ? { compare: { kicker: idea.cover.kicker ?? "Compare", lead: "公式スペックで、並べて比べる。" } } : {}),
    ...(idea.design === "B" ? { reel: { headline: idea.reel.headline, ...(idea.reel.sub ? { sub: idea.reel.sub } : {}), ...(idea.reel.accent ? { accent: idea.reel.accent } : {}), kicker: idea.format === "reel-ranking" ? "Reel / Ranking" : "Reel / Conclusion" } } : {}),
    ...(idea.hashtags?.length ? { hashtags: idea.hashtags } : {}),
  };

  // ---------- engine schema (same validators the build uses) ----------
  const existing = readJson("data/products.json").filter((p) => !products.some((n) => n.id === p.id));
  const merged = [...existing, ...products];
  try { validateProducts(merged); } catch (e) { errors.push(e.message.replace(/\n {2}/g, "\n    ")); }
  try { validatePost(post, Object.fromEntries(merged.map((p) => [p.id, p])), `post ${postId}`); } catch (e) { errors.push(e.message); }

  // ---------- caption + copy rules ----------
  const caption = renderCaption(post, products);
  const findings = lintTexts(postTexts(post, products, caption));
  const msg = (f) => `${f.where}：「${f.match}」${f.reason}\n    → ${f.suggest}`;
  findings.filter((f) => f.level === "error").forEach((f) => errors.push(msg(f)));
  findings.filter((f) => f.level === "warn").forEach((f) => warnings.push(msg(f)));

  // ---------- numbers without a source ----------
  const backed = new Set([...evs.flatMap((e) => [...Object.values(e.specs).flatMap((v) => nums(v.value)), ...e.points.filter((p) => p.basis === "official-quote").flatMap((p) => nums(p.text)), String(e.price.display)]), ...Array.from({ length: products.length }, (_, i) => String(i + 1))]);
  const texts = [["cover.lead", post.cover.lead], ["cover.kicker", post.cover.kicker], ["reel.headline", post.reel?.headline], ["reel.sub", post.reel?.sub], ...products.flatMap((p) => p.points.map((t, i) => [`${p.id}.points[${i}]`, t]))];
  for (const [where, t] of texts) for (const n of nums(t)) if (!backed.has(n)) errors.push(`${where}：数値「${n}」の出典がありません（スペック・価格・公式引用のいずれにもない）`);

  // ---------- PR / disclosure ----------
  if (!caption.startsWith("【PR】") || !caption.includes(T.brand.prNotice)) errors.push("キャプションの1行目に PR 表記がありません");
  if (!caption.includes(T.brand.sourceNote)) errors.push("キャプションに「公式情報に基づく」旨の注記がありません");
  if (!fs.readFileSync(path.join(ROOT, "templates/a-summary.njk"), "utf8").includes("brand.prNotice")) errors.push("まとめページのテンプレートに PR 表記がありません");

  return { errors, warnings, postId, post, products, caption, idea, evs, placeholder, testData: !!doc.testData };
}

export function writeDraft(runId, d) {
  const dir = path.join(runDir(runId), "drafts", d.postId);
  fs.mkdirSync(dir, { recursive: true });
  writeJson(path.join(dir, "post.json"), d.post);
  writeJson(path.join(dir, "products.json"), d.products);
  writeCsv(path.join(dir, "posts.csv"), POST_COLS, [postToRow(d.post)]);
  writeCsv(path.join(dir, "products.csv"), PRODUCT_COLS, d.products.map(productToRow));
  fs.writeFileSync(path.join(dir, "caption.txt"), d.caption);
  // evidence table: where every printed number came from
  let md = `# 原稿データ ${d.postId}（${d.idea.id}：${d.idea.theme}）\n\n生成：${jstIso()}${d.testData ? "　**※テスト用データ（架空の商品）。公開不可。**" : ""}${d.placeholder ? "　**※レイアウト確認用の画像を含む（公開不可）**" : ""}\n\n`;
  md += `判定：${d.errors.length ? `✗ エラー ${d.errors.length} 件（取り込み不可）` : "✓ エラーなし（npm run research:install で取り込み可）"}　警告 ${d.warnings.length} 件\n\n`;
  if (d.errors.length) md += `## エラー\n\n${d.errors.map((e) => `- ${e.replace(/\n/g, "\n  ")}`).join("\n")}\n\n`;
  if (d.warnings.length) md += `## 警告（判断が必要）\n\n${d.warnings.map((e) => `- ${e.replace(/\n/g, "\n  ")}`).join("\n")}\n\n`;
  md += `## 価格と出典\n\n| 商品 | 表示価格 | 種別 | 通常価格 | セール | 取得元 | 取得日時 |\n|---|---|---|---|---|---|---|\n`;
  for (const e of d.evs) {
    const pr = e.price, used = pr.basis === "sale" ? pr.sale : pr.regular;
    md += `| ${e.productId} | ¥${pr.display.toLocaleString("ja-JP")} | ${pr.basis === "sale" ? "セール" : "通常"} | ${pr.regular ? `¥${pr.regular.value?.toLocaleString("ja-JP")}（${pr.regular.label}）` : "—"} | ${pr.sale ? `${pr.sale.event ?? pr.sale.label}${pr.sale.start ? ` ${short(pr.sale.start)}` : ""}〜${short(pr.sale.end)}` : "—"} | ${used.url} | ${used.fetchedAt} |\n`;
  }
  md += `\n## スペック・ポイントと出典\n\n| 商品 | 項目 | 値 | 取得元 | 取得日時 |\n|---|---|---|---|---|\n`;
  for (const e of d.evs) {
    for (const [k, v] of Object.entries(e.specs)) md += `| ${e.productId} | ${k} | ${v.value}${v.quote ? "（公式表現の引用）" : ""} | ${v.url} | ${v.fetchedAt} |\n`;
    for (const p of e.points) md += `| ${e.productId} | ポイント | ${p.text}（${p.basis === "spec" ? `スペック「${p.specRef}」に基づく` : "公式表現の引用"}） | ${p.url ?? e.specs[p.specRef]?.url ?? ""} | ${p.fetchedAt ?? e.specs[p.specRef]?.fetchedAt ?? ""} |\n`;
    md += `| ${e.productId} | 画像 | ${e.image.rights} | ${e.image.sourceUrl ?? "—"} | ${e.image.fetchedAt ?? ""} |\n`;
  }
  md += `\n## 生成したファイル\n\n- post.json / products.json（既存スキーマ準拠）\n- posts.csv / products.csv（pipeline/csv.mjs の列定義）\n- caption.txt（キャプション案・ハッシュタグ案）\n`;
  fs.writeFileSync(path.join(dir, "check.md"), md);
  return dir;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const a = parseArgs(process.argv.slice(2));
  const [r, ideaId] = a._;
  const runId = resolveRun(r);
  if (!runId || !ideaId) { console.log("usage: npm run research:draft -- <run|latest> <idea-id> [--allow-placeholder]"); process.exit(1); }
  const d = buildDraft(runId, ideaId, { allowPlaceholder: !!a["allow-placeholder"] });
  if (d.stoppedBeforeGeneration) {
    d.errors.forEach((e) => console.log("✗ " + e));
    d.warnings.forEach((w) => console.log("△ " + w));
    console.log("原稿データは生成していません");
    process.exit(1);
  }
  const dir = writeDraft(runId, d);
  d.errors.forEach((e) => console.log("✗ " + e));
  d.warnings.forEach((w) => console.log("△ " + w));
  console.log(`${d.errors.length ? "✗" : "✓"} ${path.relative(ROOT, dir)}/（check.md に判定と出典の一覧）`);
  process.exit(d.errors.length ? 1 : 0);
}
