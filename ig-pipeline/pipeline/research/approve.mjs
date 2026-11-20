// Owner approval of post ideas — run this YOURSELF in a terminal. It refuses to run without an interactive
// terminal, so an assistant/automation cannot approve on your behalf.
//   npm run research:approve -- <run|latest> I01 I03      approve ideas
//   npm run research:approve -- status <run|latest>      show what is approved
// Writes research/runs/<run>/approval.json with a fingerprint of each approved idea; if the idea is edited
// afterwards, draft generation refuses until it is approved again.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import readline from "node:readline/promises";
import { pathToFileURL } from "node:url";
import { runDir, jstIso, readJson, writeJson } from "./lib.mjs";
import { loadIdeas, checkIdeas, ideaHash, resolveRun } from "./ideas.mjs";

export function loadApproval(runId) {
  const f = path.join(runDir(runId), "approval.json");
  return fs.existsSync(f) ? readJson(f) : { runId, approved: [] };
}

/** Pure check: null if `rec` approves exactly this version of `idea`, else a reason. */
export function approvalProblemFor(idea, rec, runId = "<run>") {
  if (!rec) return `${idea.id} は承認されていません（npm run research:approve -- ${runId} ${idea.id}）`;
  if (rec.hash !== ideaHash(idea)) return `${idea.id} は承認後に内容が変更されています。確認して承認し直してください`;
  return null;
}

/** Returns null if the idea is approved and unchanged, else a reason. */
export function approvalProblem(runId, ideaId) {
  const idea = loadIdeas(runId).ideas.find((i) => i.id === ideaId);
  if (!idea) return `${ideaId} は ${runId} にありません`;
  return approvalProblemFor(idea, loadApproval(runId).approved.find((x) => x.id === ideaId), runId);
}

async function main() {
  const args = process.argv.slice(2);
  if (args[0] === "status") {
    const runId = resolveRun(args[1]);
    const ap = loadApproval(runId);
    const ideas = loadIdeas(runId).ideas;
    for (const i of ideas) {
      const p = approvalProblem(runId, i.id);
      console.log(`${p ? "・" : "✓"} ${i.id} ${i.theme}${p ? "" : `（承認 ${ap.approved.find((x) => x.id === i.id).approvedAt}）`}`);
    }
    return;
  }
  const runId = resolveRun(args[0]);
  const ids = args.slice(1);
  if (!runId || !ids.length) { console.log("usage: npm run research:approve -- <run|latest> I01 [I02 …]"); process.exit(1); }
  if (!process.stdin.isTTY || !process.stdout.isTTY) {
    console.error("承認はオーナーがターミナルで直接実行してください（対話できない環境からは承認できません）");
    process.exit(2);
  }
  const doc = loadIdeas(runId);
  const c = checkIdeas(doc, runId);
  const chosen = ids.map((id) => doc.ideas.find((i) => i.id === id) ?? (() => { throw new Error(`${id} は ${runId} にありません`); })());
  const blocking = c.errors.filter((e) => ids.some((id) => e.startsWith(id)));
  if (blocking.length) { blocking.forEach((e) => console.log("✗ " + e)); console.log("期限切れ・古い価格などがあるため承認できません"); process.exit(1); }
  console.log(`\n${runId} の次の案を承認します：`);
  for (const i of chosen) console.log(`  ${i.id}  ${i.design}案  ${i.theme}  ／ ${i.cover.word.toUpperCase()} ／ 推奨 ${i.timing.recommended}`);
  c.warnings.filter((w) => ids.some((id) => w.startsWith(id)) || !/^I\d{2}/.test(w)).forEach((w) => console.log("  △ " + w));
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const ans = (await rl.question("\nよろしいですか？ (y/N) ")).trim().toLowerCase();
  rl.close();
  if (ans !== "y" && ans !== "yes") { console.log("中止しました"); return; }
  const ap = loadApproval(runId);
  const by = os.userInfo().username;
  for (const i of chosen) {
    ap.approved = ap.approved.filter((x) => x.id !== i.id);
    ap.approved.push({ id: i.id, hash: ideaHash(i), approvedAt: jstIso(), by });
  }
  writeJson(path.join(runDir(runId), "approval.json"), ap);
  console.log(`✓ 承認を記録しました → research/runs/${runId}/approval.json`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main().catch((e) => { console.error(e.message); process.exit(1); });
