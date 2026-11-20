// Render the Instagram caption exactly as the engine does (same template captions/caption.njk + tokens.brand),
// so drafts can be checked before they are installed.
import path from "node:path";
import nunjucks from "nunjucks";
import { ROOT, readJson } from "./lib.mjs";

const env = new nunjucks.Environment(new nunjucks.FileSystemLoader(path.join(ROOT, "captions")), { autoescape: false, trimBlocks: true, lstripBlocks: true });
env.addFilter("pad2", (n) => (typeof n === "number" ? String(n).padStart(2, "0") : n));
env.addFilter("yen", (n) => "¥" + Number(n).toLocaleString("ja-JP"));

export function renderCaption(post, items) {
  const T = readJson("tokens/tokens.json");
  const priceNote = T.brand.priceNote.replace("{date}", post.priceDate ?? "投稿");
  const hashtags = [...new Set([...(post.hashtags ?? []), ...T.brand.hashtags])];
  return env.render("caption.njk", { brand: T.brand, post, cover: post.cover, items, priceNote, hashtags }).replace(/\n{3,}/g, "\n\n").trim() + "\n";
}
