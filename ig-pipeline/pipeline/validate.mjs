// Validate products / posts against data/schema/*.schema.json with readable errors.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import Ajv from "ajv";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const ajv = new Ajv({ allErrors: true, strict: false });
const load = (f) => JSON.parse(fs.readFileSync(path.join(ROOT, f), "utf8"));
const vProduct = ajv.compile(load("data/schema/product.schema.json"));
const vPost = ajv.compile(load("data/schema/post.schema.json"));

const fmt = (errs, where) => errs.map((e) => `  ${where}${e.instancePath || "/"} ${e.message}${e.params?.allowedValues ? ": " + e.params.allowedValues.join(", ") : ""}${e.params?.additionalProperty ? ` (${e.params.additionalProperty})` : ""}`).join("\n");

export function validateProducts(list) {
  const problems = [];
  if (!Array.isArray(list)) problems.push("  products.json must be an array");
  else {
    const seen = new Set();
    list.forEach((p, i) => {
      if (!vProduct(p)) problems.push(fmt(vProduct.errors, `products[${i}:${p.id ?? "?"}]`));
      if (seen.has(p.id)) problems.push(`  products[${i}] duplicate id "${p.id}"`);
      seen.add(p.id);
      if (p.image && !fs.existsSync(path.join(ROOT, p.image))) problems.push(`  products[${i}:${p.id}] image not found: ${p.image}`);
    });
  }
  if (problems.length) throw new Error("data/products.json is invalid:\n" + problems.join("\n"));
}

export function validatePost(post, products, file = "post") {
  const problems = [];
  if (!vPost(post)) problems.push(fmt(vPost.errors, ""));
  for (const id of [...(post.products ?? []), post.cover?.hero].filter(Boolean))
    if (!products[id]) problems.push(`  unknown product id "${id}" (not in data/products.json)`);
  if (problems.length) throw new Error(`${file} is invalid:\n` + problems.join("\n"));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const list = load("data/products.json");
  validateProducts(list);
  const byId = Object.fromEntries(list.map((p) => [p.id, p]));
  const files = process.argv.slice(2).length ? process.argv.slice(2) : fs.readdirSync(path.join(ROOT, "data/posts")).filter((f) => f.endsWith(".json")).map((f) => path.join("data/posts", f));
  for (const f of files) validatePost(JSON.parse(fs.readFileSync(f, "utf8")), byId, f);
  console.log(`ok: ${list.length} products, ${files.length} posts`);
}
