// Build post images:  node pipeline/build.mjs data/posts/<post>.json [--only cover,compare] [--fonts]
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import nunjucks from "nunjucks";
import { withBrowser, shoot } from "./shot.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const T = JSON.parse(fs.readFileSync(path.join(ROOT, "tokens/tokens.json"), "utf8"));

const env = nunjucks.configure(path.join(ROOT, "templates"), { autoescape: true, throwOnUndefined: false });
env.addFilter("pad2", (n) => String(n).padStart(2, "0"));
env.addFilter("yen", (n) => "¥" + Number(n).toLocaleString("ja-JP"));
env.addFilter("kebab", (s) => s.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase());
env.addFilter("nl2br", (s) => new nunjucks.runtime.SafeString(nunjucks.lib.escape(String(s ?? "")).replace(/\n/g, "<br>")));

function loadProducts() {
  const list = JSON.parse(fs.readFileSync(path.join(ROOT, "data/products.json"), "utf8"));
  return Object.fromEntries(
    list.map((p) => {
      const cutout = `assets/products/cutout/${p.id}.png`;
      if (!fs.existsSync(path.join(ROOT, cutout))) throw new Error(`cut-out missing for ${p.id}: run npm run cutout`);
      return [p.id, { ...p, cutout, displayHeight: p.displayHeight ?? T.layout.productMaxHeight }];
    })
  );
}

/** Which slides a post gets. Multi-product: cover → details → compare → summary. */
function slidesFor(post) {
  const s = [{ key: "cover", tpl: "a-cover.njk", canvas: "carousel" }];
  return s;
}

export async function buildPost(postFile, { only, fonts } = {}) {
  const post = JSON.parse(fs.readFileSync(postFile, "utf8"));
  const products = loadProducts();
  const items = post.products.map((id) => products[id] ?? (() => { throw new Error(`unknown product ${id}`); })());
  const hero = products[post.cover.hero] ?? items[0];
  const outDir = path.join(ROOT, "out", post.id);
  const htmlDir = path.join(ROOT, ".cache/html", post.id);
  fs.mkdirSync(outDir, { recursive: true });
  fs.mkdirSync(htmlDir, { recursive: true });

  const slides = slidesFor(post).filter((s) => !only || only.includes(s.key));
  const dots = T.palette.aurora[post.cover.aurora]?.dots ?? T.palette.accentDots;
  const results = [];
  await withBrowser(async (browser) => {
    for (const [i, s] of slides.entries()) {
      const c = T.canvas[s.canvas];
      const ctx = { root: pathToFileURL(ROOT).href, T, brand: T.brand, post, cover: post.cover, hero, items, dots, canvas: { name: s.canvas, ...c }, ...s.ctx };
      const html = env.render(s.tpl, ctx);
      const name = `${String(i + 1).padStart(2, "0")}-${s.key}`;
      const htmlFile = path.join(htmlDir, `${name}.html`);
      fs.writeFileSync(htmlFile, html);
      const png = path.join(outDir, `${name}.png`);
      const report = await shoot(browser, htmlFile, png, { width: c.width, height: c.height, fontsReport: fonts });
      results.push(path.relative(ROOT, png));
      console.log("wrote", path.relative(ROOT, png), report ? JSON.stringify(report) : "");
    }
  });
  return results;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  const files = args.filter((a) => a.endsWith(".json"));
  const oi = args.indexOf("--only");
  const only = oi >= 0 ? args[oi + 1].split(",") : null;
  for (const f of files.length ? files : fs.readdirSync(path.join(ROOT, "data/posts")).map((f) => path.join(ROOT, "data/posts", f)))
    await buildPost(f, { only, fonts: args.includes("--fonts") });
}
