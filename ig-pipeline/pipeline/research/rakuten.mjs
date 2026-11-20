// Rakuten market scan → research/runs/<run>/market/rakuten-<category>.json + market.md
//   npm run research:rakuten                          all categories (needs .env keys)
//   npm run research:rakuten -- facial-device hair-dryer
//   npm run research:rakuten -- --fixture             offline: research/fixtures/rakuten/*.json (fake data)
//   npm run research:rakuten -- --run 20261120-1405   write into an existing run
//   npm run research:rakuten -- --check-setup         .env / config readiness (never prints key values)
//   npm run research:rakuten -- --ping                one 1-item search request to confirm the keys work
// Every item keeps the price it had at fetch time with fetchedAt and the source URL. itemPrice is the shop's
// current selling price; it is NOT a regular (通常) price. Regular price and sale periods come from evidence work.
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { ROOT, config, jstIso, newRunId, runDir, loadEnv, parseArgs, writeJson } from "./lib.mjs";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const rakutenTime = (s) => (s ? `${s.replace(" ", "T")}:00+09:00` : null); // "2026-11-21 20:00" → ISO JST

/** Items come back as [{Item:{…}}] (formatVersion 1) or [{…}] (formatVersion 2). */
export function normalize(json, source, fetchedAt) {
  const items = (json.Items ?? json.items ?? []).map((x) => x.Item ?? x);
  return items.map((it, i) => ({
    source,
    rank: it.rank ?? i + 1,
    itemName: it.itemName,
    itemCode: it.itemCode,
    shopName: it.shopName,
    itemUrl: it.itemUrl,
    affiliateUrl: it.affiliateUrl || null,
    price: { value: it.itemPrice, label: "取得時点の販売価格（税込・送料別の場合あり）", taxIncluded: it.taxFlag === 0, url: it.itemUrl, fetchedAt },
    timeSale: it.startTime || it.endTime ? { start: rakutenTime(it.startTime), end: rakutenTime(it.endTime), note: "ショップのタイムセール期間（API の startTime / endTime）" } : null,
    pointCampaign: it.pointRate > 1 ? { rate: it.pointRate, start: rakutenTime(it.pointRateStartTime), end: rakutenTime(it.pointRateEndTime) } : null,
    reviewCount: it.reviewCount ?? 0,
    reviewAverage: Number(it.reviewAverage ?? 0),
    genreId: it.genreId ?? null,
    imageUrls: (it.mediumImageUrls ?? []).map((u) => (typeof u === "string" ? u : u.imageUrl)).filter(Boolean).map((u) => u.replace(/\?_ex=\d+x\d+$/, "?_ex=1000x1000")),
  }));
}

/** Request URL without credentials (safe to store in files). */
const publicUrl = (endpoint, params) => `${endpoint}?${new URLSearchParams(params)}`;

async function call(endpoint, params) {
  const { RAKUTEN_APP_ID, RAKUTEN_ACCESS_KEY, RAKUTEN_REFERER, RAKUTEN_AFFILIATE_ID } = process.env;
  if (!RAKUTEN_APP_ID || !RAKUTEN_ACCESS_KEY)
    throw new Error("RAKUTEN_APP_ID / RAKUTEN_ACCESS_KEY が .env にありません（.env.example を参照）。キーがない間は --fixture で動作確認できます。");
  const q = new URLSearchParams({ applicationId: RAKUTEN_APP_ID, accessKey: RAKUTEN_ACCESS_KEY, format: "json", formatVersion: "2", ...params });
  if (RAKUTEN_AFFILIATE_ID) q.set("affiliateId", RAKUTEN_AFFILIATE_ID);
  const headers = RAKUTEN_REFERER ? { Referer: RAKUTEN_REFERER, Origin: new URL(RAKUTEN_REFERER).origin } : {};
  const res = await fetch(`${endpoint}?${q}`, { headers });
  const body = await res.text();
  if (!res.ok) throw new Error(`楽天 API ${res.status}: ${body.slice(0, 300)}\n→ 403/404 のときは research/config.json のエンドポイントと、アプリの「許可されたWebサイト」と RAKUTEN_REFERER を確認`);
  return JSON.parse(body);
}

const quant = (xs, q) => { const s = [...xs].sort((a, b) => a - b); return s.length ? s[Math.min(s.length - 1, Math.floor(q * s.length))] : null; };
const yen = (n) => (n == null ? "—" : "¥" + n.toLocaleString("ja-JP"));
const short = (s, n = 40) => (s ?? "").replace(/\|/g, "／").slice(0, n);

function summary(cat, data) {
  const prices = [...data.ranking, ...data.search].map((x) => x.price.value).filter(Boolean);
  const row = (x) => `| ${x.rank} | ${short(x.itemName)} | ${yen(x.price.value)} | ${x.timeSale ? `〜${x.timeSale.end?.slice(5, 16).replace("T", " ")}` : ""} | ${x.reviewAverage.toFixed(2)}（${x.reviewCount}） | ${short(x.shopName, 16)} |`;
  let md = `## ${cat.label}（${cat.key}）\n\n価格帯（${prices.length}件・取得時点の販売価格）：25%点 ${yen(quant(prices, 0.25))} ／ 中央値 ${yen(quant(prices, 0.5))} ／ 75%点 ${yen(quant(prices, 0.75))}\n\n`;
  const head = `| 順位 | 商品名 | 価格 | タイムセール | 評価（件数） | ショップ |\n|---|---|---|---|---|---|\n`;
  md += data.ranking.length ? `### ランキング 上位10\n\n${head}${data.ranking.slice(0, 10).map(row).join("\n")}\n\n` : `> ランキング：genreId 未設定のため未取得\n\n`;
  md += `### 検索（${cat.keywords.join(" / ")}）レビュー件数順 上位10\n\n${head}${[...data.search].sort((a, b) => b.reviewCount - a.reviewCount).slice(0, 10).map((x, i) => row({ ...x, rank: i + 1 })).join("\n")}\n`;
  return md;
}

export async function scan({ categories, fixture, run }) {
  const cfg = config();
  const R = cfg.rakuten;
  const runId = run ?? newRunId();
  const dir = path.join(runDir(runId), "market");
  fs.mkdirSync(dir, { recursive: true });
  if (!fixture && !R.specVerified) console.warn("⚠ research/config.json の rakuten.specVerified が false です。公式仕様の確認前の本番実行です。");
  let md = `# 楽天市場マーケットスキャン ${runId}${fixture ? "（テスト用データ）" : ""}\n\n`;
  md += fixture ? "> **テスト用データ（架空）です。** 商品・価格・ショップは実在しません。\n\n" : `取得日時：各表の値は取得時点のものです。投稿前に商品ページで再確認してください。\n\n`;
  for (const cat of cfg.categories) {
    if (categories.length && !categories.includes(cat.key)) continue;
    const data = { category: cat, mode: fixture ? "fixture" : "api", requests: [], ranking: [], search: [] };
    if (fixture) {
      const t = jstIso();
      for (const kind of ["ranking", "search"]) {
        const f = path.join(ROOT, `research/fixtures/rakuten/${cat.key}.${kind}.json`);
        if (!fs.existsSync(f)) continue;
        data[kind] = normalize(JSON.parse(fs.readFileSync(f, "utf8")), `rakuten-${kind}`, t);
        data.requests.push({ kind, url: `fixture:research/fixtures/rakuten/${cat.key}.${kind}.json`, fetchedAt: t, count: data[kind].length });
      }
    } else {
      if (cat.genreId) {
        const p = { genreId: String(cat.genreId) };
        const t = jstIso();
        data.ranking = normalize(await call(R.rankingEndpoint, p), "rakuten-ranking", t);
        data.requests.push({ kind: "ranking", url: publicUrl(R.rankingEndpoint, p), fetchedAt: t, count: data.ranking.length });
        await sleep(R.minIntervalMs);
      }
      for (const kw of cat.keywords) {
        const p = { keyword: kw, hits: String(R.hits), sort: "-reviewCount", availability: "1", imageFlag: "1", ...(cat.minPrice ? { minPrice: String(cat.minPrice) } : {}), ...(cat.genreId ? { genreId: String(cat.genreId) } : {}) };
        const t = jstIso();
        const items = normalize(await call(R.searchEndpoint, p), "rakuten-search", t);
        data.search.push(...items);
        data.requests.push({ kind: "search", url: publicUrl(R.searchEndpoint, p), fetchedAt: t, count: items.length });
        await sleep(R.minIntervalMs);
      }
    }
    data.fetchedAt = data.requests[0]?.fetchedAt ?? jstIso();
    writeJson(path.join(dir, `rakuten-${cat.key}.json`), data);
    md += summary(cat, data) + "\n";
    console.log(`${cat.key}: ranking ${data.ranking.length} / search ${data.search.length}`);
  }
  fs.writeFileSync(path.join(runDir(runId), "market.md"), md);
  console.log(`→ research/runs/${runId}/market.md`);
  return runId;
}

function checkSetup() {
  const cfg = config(), R = cfg.rakuten, env = process.env;
  const mark = (ok) => (ok ? "✓" : "✗");
  const mask = (v) => (v ? `設定あり（${v.length}文字）` : "未設定");
  console.log(`${mark(!!env.RAKUTEN_APP_ID)} RAKUTEN_APP_ID：${mask(env.RAKUTEN_APP_ID)}`);
  console.log(`${mark(/^pk_/.test(env.RAKUTEN_ACCESS_KEY ?? ""))} RAKUTEN_ACCESS_KEY：${mask(env.RAKUTEN_ACCESS_KEY)}${env.RAKUTEN_ACCESS_KEY && !/^pk_/.test(env.RAKUTEN_ACCESS_KEY) ? "（pk_ で始まっていません）" : ""}`);
  let refOk = false; try { refOk = !!env.RAKUTEN_REFERER && new URL(env.RAKUTEN_REFERER).protocol === "https:"; } catch {}
  console.log(`${mark(refOk)} RAKUTEN_REFERER：${env.RAKUTEN_REFERER ? (refOk ? new URL(env.RAKUTEN_REFERER).origin : "https:// から始まる URL にしてください") : "未設定（アプリの「許可されたWebサイト」と同じドメイン）"}`);
  console.log(`・ RAKUTEN_AFFILIATE_ID：${mask(env.RAKUTEN_AFFILIATE_ID)}（任意）`);
  console.log(`${mark(R.specVerified)} 公式仕様の確認（research/config.json rakuten.specVerified）：${R.specVerified ? "確認済み" : "未確認 → Claude Code で /research を実行すると最初に確認します"}`);
  console.log(`・ 接続先：${R.searchEndpoint}\n         ${R.rankingEndpoint}`);
  const noGenre = cfg.categories.filter((c) => !c.genreId).map((c) => c.key);
  console.log(`・ genreId 未設定のカテゴリ：${noGenre.length ? noGenre.join(", ") + "（ランキングは取得せず、検索だけ行います）" : "なし"}`);
}

async function ping() {
  const R = config().rakuten;
  const t = jstIso();
  const json = await call(R.searchEndpoint, { keyword: "美顔器", hits: "1", availability: "1" });
  const it = normalize(json, "rakuten-search", t)[0];
  console.log(`✓ 楽天 API に接続できました（${t}）`);
  if (it) console.log(`  例：${it.itemName?.slice(0, 40)} ／ ¥${it.price.value?.toLocaleString("ja-JP")} ／ ${it.shopName}`);
  const keys = Object.keys((json.Items ?? json.items ?? [])[0]?.Item ?? (json.Items ?? json.items ?? [])[0] ?? {});
  console.log(`  返ってきた項目（公式仕様の確認用）：${keys.join(", ")}`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  loadEnv();
  const a = parseArgs(process.argv.slice(2));
  if (a["check-setup"]) { checkSetup(); process.exit(0); }
  if (a.ping) { ping().catch((e) => { console.error("✗ " + e.message); process.exit(1); }); }
  else scan({ categories: a._, fixture: !!a.fixture, run: a.run }).catch((e) => { console.error(e.message); process.exit(1); });
}
