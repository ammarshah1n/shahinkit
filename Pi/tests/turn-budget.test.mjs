import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
const agentDir = mkdtempSync(join(tmpdir(), "shahinkit-budget-"));
process.env.PI_CODING_AGENT_DIR = agentDir;
writeFileSync(join(agentDir, "turn-budget.json"), JSON.stringify({ cheaperModelPattern: "economy" }));
const root = process.env.PI_PACKAGE_ROOT || join(execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim(), "@earendil-works/pi-coding-agent");
const { createJiti } = await import(pathToFileURL(join(root, "node_modules/jiti/lib/jiti.mjs")).href);
const here = dirname(fileURLToPath(import.meta.url));
const mod = await createJiti(import.meta.url).import(resolve(here, "../extensions/turn-budget.ts"));
function harness() {
  const handlers = {}, sent = [], notices = [], commands = {};
  const pi = { on: (e, f) => handlers[e] = f, sendMessage: (...x) => sent.push(x), registerCommand: (n, d) => commands[n] = d };
  const ctx = { model: { id: "ordinary" }, ui: { setStatus() {}, notify: (...x) => notices.push(x) }, abort() { this.aborts++; }, aborts: 0 };
  return { pi, handlers, sent, notices, commands, ctx, start: async () => handlers.agent_start({}, ctx), assistant: async (cost = 0.1) => handlers.turn_end({ message: { role: "assistant", usage: { cost: { total: cost } } } }, ctx), human: async () => { await handlers.input({}); await handlers.agent_start({}, ctx); } };
}
test("budget defaults, configurable cheaper profile, pause, warning, reset and commands", async () => {
  try {
    assert.deepEqual(mod.DEFAULTS, { msgs: 250, cost: 40, minutes: 90, turns: 12 });
    assert.deepEqual(mod.limitsFor("economy-model"), { msgs: 125, cost: 20, minutes: 45, turns: 6 });
    const h = harness(); mod.default(h.pi); await h.human();
    for (let i = 0; i < 188; i++) await h.assistant(0);
    assert.equal(h.sent.length, 1, "75% warning sent once");
    assert.equal(h.sent[0][1].deliverAs, "steer");
    for (let i = 188; i < 250; i++) await h.assistant(0);
    assert.match(globalThis.__piTurnBudget.exhausted(), /assistant messages/);
    assert.equal(h.ctx.aborts, 1);
    await h.human(); assert.equal(globalThis.__piTurnBudget.exhausted(), undefined);
    await h.commands.budget.handler("off", h.ctx); assert.equal(globalThis.__piTurnBudget.state().enabled, false);
    await h.commands.budget.handler("on", h.ctx); assert.equal(globalThis.__piTurnBudget.state().enabled, true);
  } finally { rmSync(agentDir, { recursive: true, force: true }); }
});
test("provider usage limit trips immediately; unrelated error does not", async () => {
  const handlers = {}, pi = { on: (e, f) => handlers[e] = f, sendMessage() {}, registerCommand() {} };
  let aborts = 0; const ctx = { model: { id: "ordinary" }, ui: { setStatus() {}, notify() {} }, abort: () => aborts++ };
  mod.default(pi); await handlers.agent_start({}, ctx);
  await handlers.turn_end({ message: { role: "assistant", stopReason: "error", errorMessage: "fetch failed" } }, ctx);
  assert.equal(globalThis.__piTurnBudget.exhausted(), undefined);
  await handlers.turn_end({ message: { role: "assistant", stopReason: "error", errorMessage: "usage limit reached" } }, ctx);
  assert.match(globalThis.__piTurnBudget.exhausted(), /usage limit/); assert.equal(aborts, 1);
});
