// Render an HTML file to PNG with headless Chromium.
//   node pipeline/shot.mjs <in.html> <out.png> [--width 1080] [--height 1350] [--full] [--scale 1]
// FONT_MODE=fallback forces the bundled OFL fonts (cloud/CI). Default "adobe" prefers
// Adobe Fonts installed via Creative Cloud and falls back automatically when missing.
import { chromium } from "playwright";
import path from "node:path";
import { pathToFileURL } from "node:url";

export async function withBrowser(fn) {
  const browser = await chromium.launch();
  try {
    return await fn(browser);
  } finally {
    await browser.close();
  }
}

/** Return the platform fonts Chromium actually used for each [data-font-role] element. */
export async function reportFonts(page) {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("DOM.enable");
  await cdp.send("CSS.enable");
  const { root } = await cdp.send("DOM.getDocument", { depth: -1 });
  const { nodeIds } = await cdp.send("DOM.querySelectorAll", { nodeId: root.nodeId, selector: "[data-font-role]" });
  const out = {};
  for (const nodeId of nodeIds) {
    const { attributes } = await cdp.send("DOM.getAttributes", { nodeId });
    const role = attributes[attributes.indexOf("data-font-role") + 1];
    const { fonts } = await cdp.send("CSS.getPlatformFontsForNode", { nodeId });
    out[role] ??= new Set();
    fonts.forEach((f) => out[role].add(f.familyName));
  }
  return Object.fromEntries(Object.entries(out).map(([k, v]) => [k, [...v]]));
}

export async function shoot(browser, inFile, outFile, { width = 1080, height = 1350, full = false, scale = 1, fontMode = process.env.FONT_MODE || "adobe", fontsReport = false } = {}) {
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: scale });
  await page.addInitScript((m) => document.documentElement.setAttribute("data-font-mode", m), fontMode);
  await page.goto(pathToFileURL(path.resolve(inFile)).href, { waitUntil: "load" });
  await page.evaluate((m) => document.documentElement.setAttribute("data-font-mode", m), fontMode);
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => [...document.images].every((i) => i.complete));
  const report = fontsReport ? await reportFonts(page) : null;
  await page.screenshot({ path: outFile, fullPage: full, type: outFile.endsWith(".jpg") ? "jpeg" : "png", ...(outFile.endsWith(".jpg") ? { quality: 95 } : {}) });
  await page.close();
  return report;
}

// CLI
if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [inFile, outFile, ...rest] = process.argv.slice(2);
  const opt = {};
  for (let i = 0; i < rest.length; i++) {
    const a = rest[i];
    if (a === "--full") opt.full = true;
    else if (a === "--fonts") opt.fontsReport = true;
    else opt[a.replace(/^--/, "")] = Number(rest[++i]);
  }
  const report = await withBrowser((b) => shoot(b, inFile, outFile, opt));
  if (report) console.log(JSON.stringify(report, null, 2));
  console.log("wrote", outFile);
}
