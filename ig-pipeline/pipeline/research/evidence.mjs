// Evidence files: research/runs/<run>/evidence/<product-id>.json
//   npm run research:evidence -- new <run> <product-id> --from <category>:<rank|itemCode> [--list search|ranking]
//       scaffold from a market scan item (Rakuten price/URL/time + image source). Brand, names, specs and points
//       are left empty: they must be filled from the maker's official page (with URL + time) before use.
//   npm run research:evidence -- validate <run>
//       schema-check every evidence file in the run
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import Ajv from "ajv";
import { ROOT, readJson, writeJson, runDir, parseArgs, latestRun } from "./lib.mjs";

const ajv = new Ajv({ allErrors: true, strict: false });
const validateSchema = ajv.compile(readJson("research/schema/evidence.schema.json"));

export function schemaErrors(ev) {
  return validateSchema(ev) ? [] : validateSchema.errors.map((e) => `${e.instancePath || "/"} ${e.message}`);
}

export function loadEvidence(runId) {
  const dir = path.join(runDir(runId), "evidence");
  if (!fs.existsSync(dir)) return {};
  return Object.fromEntries(fs.readdirSync(dir).filter((f) => f.endsWith(".json")).map((f) => [f.replace(/\.json$/, ""), readJson(path.join(dir, f))]));
}

function findItem(runId, from, list) {
  const [catKey, pick] = from.split(":");
  const file = path.join(runDir(runId), "market", `rakuten-${catKey}.json`);
  if (!fs.existsSync(file)) throw new Error(`market data not found: ${path.relative(ROOT, file)}（先に npm run research:rakuten）`);
  const m = readJson(file);
  const pool = list ? m[list] : [...m.ranking, ...m.search];
  const it = pool.find((x) => x.itemCode === pick) ?? (list ? pool : m.ranking.length ? m.ranking : m.search).find((x) => String(x.rank) === pick);
  if (!it) throw new Error(`item ${pick} not found in ${catKey}`);
  return { m, it };
}

export function scaffold(runId, productId, from, list) {
  const { m, it } = findItem(runId, from, list);
  const sale = it.timeSale?.end
    ? { value: it.price.value, url: it.itemUrl, fetchedAt: it.price.fetchedAt, label: "楽天ショップのタイムセール価格（要確認）", start: it.timeSale.start ?? undefined, end: it.timeSale.end, itemCode: it.itemCode }
    : null;
  if (sale && !sale.start) delete sale.start;
  return {
    productId,
    runId,
    status: "scaffold",
    fields: { category: { value: m.category.label, url: it.itemUrl, fetchedAt: it.price.fetchedAt, note: `research/config.json のカテゴリ ${m.category.key}` } },
    price: {
      display: it.price.value,
      basis: "unverified",
      regular: null,
      sale,
      rakuten: { value: it.price.value, url: it.itemUrl, fetchedAt: it.price.fetchedAt, label: it.price.label, itemCode: it.itemCode },
    },
    specs: {},
    points: [],
    image: { sourceUrl: it.imageUrls[0] ?? null, sourcePage: it.itemUrl, fetchedAt: it.price.fetchedAt, rights: "placeholder", note: "楽天の商品画像。レイアウト確認用のみ。公開には自分の写真か使用許諾のある画像が必要" },
    links: { rakuten: it.affiliateUrl || it.itemUrl, amazon: null, official: null },
    notes: `scaffold from ${m.mode === "fixture" ? "TEST DATA" : "Rakuten API"}: ${it.itemName}（${it.shopName}）。brand / name / nameJa / specs / points は公式ページで確認して記入する。`,
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const a = parseArgs(process.argv.slice(2));
  const [cmd, runArg, productId] = a._;
  const runId = runArg === "latest" ? latestRun() : runArg;
  if (cmd === "new") {
    if (!runId || !productId || !a.from) { console.log("usage: npm run research:evidence -- new <run|latest> <product-id> --from <category>:<rank|itemCode> [--list search|ranking]"); process.exit(1); }
    if (!/^[a-z0-9][a-z0-9-]*$/.test(productId)) throw new Error("product-id は英小文字・数字・ハイフン");
    const ev = scaffold(runId, productId, a.from, a.list);
    const errs = schemaErrors(ev);
    if (errs.length) throw new Error("scaffold failed schema:\n" + errs.join("\n"));
    const out = path.join(runDir(runId), "evidence", `${productId}.json`);
    if (fs.existsSync(out) && !a.force) throw new Error(`${path.relative(ROOT, out)} already exists (--force to overwrite)`);
    writeJson(out, ev);
    console.log(`→ ${path.relative(ROOT, out)}`);
  } else if (cmd === "validate") {
    const all = loadEvidence(runId);
    let bad = 0;
    for (const [id, ev] of Object.entries(all)) {
      const errs = schemaErrors(ev);
      console.log(errs.length ? `✗ ${id}\n  ${errs.join("\n  ")}` : `✓ ${id} (${ev.status ?? "?"})`);
      bad += errs.length ? 1 : 0;
    }
    if (!Object.keys(all).length) console.log("no evidence files");
    process.exit(bad ? 1 : 0);
  } else {
    console.log("usage: npm run research:evidence -- new|validate …");
    process.exit(1);
  }
}
