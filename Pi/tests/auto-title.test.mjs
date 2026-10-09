import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
const root = process.env.PI_PACKAGE_ROOT || join(execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim(), "@earendil-works/pi-coding-agent");
const { createJiti } = await import(pathToFileURL(join(root, "node_modules/jiti/lib/jiti.mjs")).href);
const here = dirname(fileURLToPath(import.meta.url));
const mod = await createJiti(import.meta.url).import(resolve(here, "../extensions/auto-title.ts"));
test("heuristic excludes commands and produces concise titles", () => {
  const h = mod.heuristicTitle;
  assert.equal(h("Fix the login redirect bug in auth.ts"), "Fix the login redirect bug in auth.ts");
  assert.equal(h("hey can you please refactor the footer"), "Refactor the footer");
  assert.equal(h("/task:plan add search to settings"), "");
  assert.equal(h("/task:plan"), "");
  assert.ok(h("word ".repeat(40)).length <= 49);
});
test("first interactive prompt is named; children, disabled, and later prompts are ignored", async () => {
  const old = process.env.PI_AUTO_TITLE_LLM; process.env.PI_AUTO_TITLE_LLM = "0";
  try {
    const handlers = {}; let name;
    const pi = { on: (e, f) => handlers[e] = f, getSessionName: () => name, setSessionName: (n) => name = n };
    mod.default(pi); await handlers.session_start({}, {});
    await handlers.input({ text: "child prompt" }, { hasUI: false }); assert.equal(name, undefined);
    await handlers.input({ text: "/settings" }, { hasUI: true }); assert.equal(name, undefined);
    await handlers.input({ text: "build the search feature" }, { hasUI: true }); assert.equal(name, "Build the search feature");
    name = "User Rename";
    await handlers.input({ text: "another task" }, { hasUI: true }); assert.equal(name, "User Rename");
  } finally { if (old === undefined) delete process.env.PI_AUTO_TITLE_LLM; else process.env.PI_AUTO_TITLE_LLM = old; }
});
test("LLM refinement requires an explicit provider/model and does not overwrite a manual rename", async () => {
  const oldModel = process.env.PI_AUTO_TITLE_MODEL, oldLLM = process.env.PI_AUTO_TITLE_LLM, oldFetch = globalThis.fetch;
  process.env.PI_AUTO_TITLE_MODEL = "provider/title-model"; delete process.env.PI_AUTO_TITLE_LLM;
  let release; globalThis.fetch = async (_url, options) => { await new Promise((r) => release = r); return { ok: true, json: async () => ({ choices: [{ message: { content: "Better Name" } }] }) }; };
  try {
    const handlers = {}; let name;
    const pi = { on: (e, f) => handlers[e] = f, getSessionName: () => name, setSessionName: (n) => name = n };
    const ctx = { hasUI: true, modelRegistry: { find: (provider, id) => { assert.equal(provider, "provider"); assert.equal(id, "title-model"); return { id, baseUrl: "https://example.invalid/v1" }; }, getApiKeyAndHeaders: async () => ({ ok: true, apiKey: "test" }) } };
    mod.default(pi); await handlers.input({ text: "make a useful feature" }, ctx); assert.equal(name, "Make a useful feature");
    name = "Manual Name"; release(); await new Promise((r) => setTimeout(r, 0)); assert.equal(name, "Manual Name");
  } finally {
    globalThis.fetch = oldFetch;
    if (oldModel === undefined) delete process.env.PI_AUTO_TITLE_MODEL; else process.env.PI_AUTO_TITLE_MODEL = oldModel;
    if (oldLLM === undefined) delete process.env.PI_AUTO_TITLE_LLM; else process.env.PI_AUTO_TITLE_LLM = oldLLM;
  }
});
