// Build post images:  node pipeline/build.mjs data/posts/<post>.json [--only cover,compare] [--fonts]
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import nunjucks from "nunjucks";
import { withBrowser, shoot } from "./shot.mjs";
import { validateProducts, validatePost } from "./validate.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const T = JSON.parse(fs.readFileSync(path.join(ROOT, "tokens/tokens.json"), "utf8"));

const env = nunjucks.configure(path.join(ROOT, "templates"), { autoescape: true, throwOnUndefined: false });
env.addFilter("pad2", (n) => (typeof n === "number" ? String(n).padStart(2, "0") : n));
env.addFilter("yen", (n) => "¥" + Number(n).toLocaleString("ja-JP"));
env.addFilter("kebab", (s) => s.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase());
env.addFilter("nl2br", (s) => new nunjucks.runtime.SafeString(nunjucks.lib.escape(String(s ?? "")).replace(/\n/g, "<br>")));

// captions are plain text: separate environment without HTML escaping
const capEnv = new nunjucks.Environment(new nunjucks.FileSystemLoader(path.join(ROOT, "captions")), { autoescape: false, trimBlocks: true, lstripBlocks: true });
for (const f of ["pad2", "yen"]) capEnv.addFilter(f, env.getFilter(f));

function loadProducts() {
  const list = JSON.parse(fs.readFileSync(path.join(ROOT, "data/products.json"), "utf8"));
  validateProducts(list);
  return Object.fromEntries(
    list.map((p) => {
      // a hand-made cut-out (Photoshop) wins over the automatic rembg one
      const manual = `assets/products/manual/${p.id}.png`;
      const auto = `assets/products/cutout/${p.id}.png`;
      const cutout = fs.existsSync(path.join(ROOT, manual)) ? manual : auto;
      if (!fs.existsSync(path.join(ROOT, cutout))) throw new Error(`cut-out missing for ${p.id}: run npm run cutout`);
      return [p.id, { ...p, cutout, displayHeight: p.displayHeight ?? T.layout.productMaxHeight }];
    })
  );
}

/** Which slides a post gets. Multi-product: cover → details → compare → summary. */
function slidesFor(post, items) {
  const s = [{ key: "cover", tpl: "a-cover.njk", canvas: "carousel" }];
  items.forEach((item, i) =>
    s.push({ key: `detail-${item.id}`, group: "detail", tpl: "a-detail.njk", canvas: "carousel", ctx: { item, itemNo: i + 1, mirror: i % 2 === 0 } })
  );
  if (items.length >= 2) {
    if (items.length > 4) throw new Error("compare page supports 2–4 products");
    s.push({ key: "compare", tpl: "a-compare.njk", canvas: "carousel" });
  }
  s.push({ key: "summary", tpl: "a-summary.njk", canvas: "carousel" });
  if (post.reel) s.push({ key: "reel-cover", group: "reel", tpl: "b-reel-cover.njk", canvas: "reel", standalone: true, ctx: reelCtx(post) });
  return s;
}

// ---- B-plan stroke placement (deterministic per post seed)
function mulberry32(a) {
  return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
function reelCtx(post) {
  const reel = post.reel;
  const layout = JSON.parse(fs.readFileSync(path.join(ROOT, `templates/b-layouts/${reel.layout ?? "scatter-a"}.json`), "utf8"));
  const paint = JSON.parse(fs.readFileSync(path.join(ROOT, "generators/presets/paint.json"), "utf8")).strokes;
  const rnd = mulberry32(reel.seed ?? 1);
  const shuffle = (a) => a.map((v) => [rnd(), v]).sort((x, y) => x[0] - y[0]).map((x) => x[1]);
  const isAccent = (p) => p.colors.length === 1 && p.colors[0] === "black" && p.length <= 320;
  let pool = shuffle(paint.filter((p) => !isAccent(p)).map((p) => p.name));
  let accents = shuffle(paint.filter(isAccent).map((p) => p.name));
  if (reel.strokes) pool = [...reel.strokes];
  const strokes = layout.slots.map((sl) => {
    const name = sl.pool === "accent" ? accents.shift() ?? pool.shift() : pool.shift() ?? accents.shift();
    const j = (k) => (rnd() - 0.5) * 2 * k;
    if (!name) return null;
    // size by the sprite's longest side so tall (rotated) strokes don't blow up
    const png = fs.readFileSync(path.join(ROOT, `assets/paint/${name}.png`));
    const pw = png.readUInt32BE(16), ph = png.readUInt32BE(20);
    const longSide = sl.w * (0.92 + rnd() * 0.16);
    const dw = Math.round(pw >= ph ? longSide : longSide * (pw / ph));
    return { ...sl, name, dw, x: Math.round(sl.x + j(24)), y: Math.round(sl.y + j(20)), rot: +(sl.rot + j(6)).toFixed(1) };
  }).filter(Boolean);
  return { reel, layout, strokes };
}

const get = (obj, dotted) => dotted.split(".").reduce((o, k) => (o == null ? o : o[k]), obj);
const yen = (n) => "¥" + Number(n).toLocaleString("ja-JP");

/** Compare table rows. Default: price + spec keys shared by every item + first point. */
function compareRows(post, items) {
  let rows = post.compare?.rows;
  if (!rows) {
    const shared = Object.keys(items[0].specs).filter((k) => items.every((it) => k in it.specs));
    rows = [{ label: "価格", field: "price" }, ...shared.slice(0, 4).map((k) => ({ label: k, spec: k })), { label: "推しポイント", field: "points.0" }];
  }
  return rows.map((r) => ({
    label: r.label,
    kind: r.field === "price" ? "price" : "text",
    cells: items.map((it) => {
      const v = r.spec ? it.specs[r.spec] : get(it, r.field);
      if (v == null || v === "") return "—";
      return r.field === "price" ? yen(v) : String(v);
    }),
  }));
}

export async function buildPost(postFile, { only, fonts } = {}) {
  const post = JSON.parse(fs.readFileSync(postFile, "utf8"));
  const products = loadProducts();
  validatePost(post, products, path.relative(ROOT, path.resolve(postFile)));
  const items = post.products.map((id) => products[id] ?? (() => { throw new Error(`unknown product ${id}`); })());
  const hero = products[post.cover.hero] ?? items[0];
  const outDir = path.join(ROOT, "out", post.id);
  const htmlDir = path.join(ROOT, ".cache/html", post.id);
  fs.mkdirSync(outDir, { recursive: true });
  fs.mkdirSync(htmlDir, { recursive: true });

  const all = slidesFor(post, items);
  const carouselCount = all.filter((s) => !s.standalone).length;
  const slides = all.map((s, i) => ({ ...s, index: i })).filter((s) => !only || only.includes(s.key) || only.includes(s.group));
  const priceNote = T.brand.priceNote.replace("{date}", post.priceDate ?? "投稿");
  const dots = T.palette.aurora[post.cover.aurora]?.dots ?? T.palette.accentDots;
  const results = [];
  await withBrowser(async (browser) => {
    for (const s of slides) {
      const c = T.canvas[s.canvas];
      const ctx = {
        root: pathToFileURL(ROOT).href, T, brand: T.brand, post, cover: post.cover, compare: post.compare ?? {}, summary: post.summary ?? {},
        hero, items, dots, priceNote, compareRows: items.length >= 2 ? compareRows(post, items) : [],
        pageNo: s.index === 0 || s.standalone ? null : `${String(s.index + 1).padStart(2, "0")} / ${String(carouselCount).padStart(2, "0")}`,
        canvas: { name: s.canvas, ...c }, ...s.ctx,
      };
      const html = env.render(s.tpl, ctx);
      const name = s.standalone ? s.key : `${String(s.index + 1).padStart(2, "0")}-${s.key}`;
      const htmlFile = path.join(htmlDir, `${name}.html`);
      fs.writeFileSync(htmlFile, html);
      const png = path.join(outDir, `${name}.png`);
      const report = await shoot(browser, htmlFile, png, { width: c.width, height: c.height, fontsReport: fonts });
      results.push(path.relative(ROOT, png));
      console.log("wrote", path.relative(ROOT, png), report ? JSON.stringify(report) : "");
    }
  });
  // caption
  const hashtags = [...new Set([...(post.hashtags ?? []), ...T.brand.hashtags])];
  const caption = capEnv.render("caption.njk", { brand: T.brand, post, cover: post.cover, items, priceNote, hashtags }).replace(/\n{3,}/g, "\n\n").trim() + "\n";
  fs.writeFileSync(path.join(outDir, "caption.txt"), caption);
  results.push(path.relative(ROOT, path.join(outDir, "caption.txt")));
  return results;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  const files = args.filter((a) => a.endsWith(".json"));
  const oi = args.indexOf("--only");
  const only = oi >= 0 ? args[oi + 1].split(",") : null;
  for (const f of files.length ? files : fs.readdirSync(path.join(ROOT, "data/posts")).map((f) => path.join(ROOT, "data/posts", f)))
    await buildPost(f, { only, fonts: args.includes("--fonts") });
}
