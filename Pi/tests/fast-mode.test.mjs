import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { execFileSync } from "node:child_process";

const configDir = mkdtempSync(join(tmpdir(), "shahinkit-fast-"));
process.env.PI_CODING_AGENT_DIR = configDir;
const PI_ROOT = process.env.PI_PACKAGE_ROOT || join(execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim(), "@earendil-works/pi-coding-agent");
const PKG = join(PI_ROOT, "node_modules");
const { createJiti } = await import(pathToFileURL(join(PKG, "jiti/lib/jiti.mjs")).href);
const jiti = createJiti(import.meta.url, {
  alias: {
    "@earendil-works/pi-coding-agent": PI_ROOT,
    "@earendil-works/pi-tui": join(PKG, "@earendil-works/pi-tui"),
  },
});
const here = dirname(fileURLToPath(import.meta.url));
const load = (name) => jiti.import(resolve(here, `../extensions/${name}.ts`), { default: true });

try {
  test("Fast Mode is opt-in; Astra is always standard tier; Claude fast is separately opt-in", async () => {
    const mod = await load("fast-mode");
    const hooks = {};
    const commands = {};
    const notices = [];
    mod({ on: (name, fn) => { hooks[name] = fn; }, registerCommand: (name, def) => { commands[name] = def; } });
    const ctx = (provider, id, compat = {}) => ({ model: { provider, id, compat } });

    const normal = { model: "gpt-6-luna" };
    await hooks.before_provider_request({ payload: normal }, ctx("openai-codex", "gpt-6-luna"));
    assert.equal(normal.service_tier, undefined, "missing state defaults off");

    const ui = { notify: (text) => notices.push(text) };
    await commands.fast.handler("on", { ui });
    const fast = { model: "gpt-6-luna" };
    await hooks.before_provider_request({ payload: fast }, ctx("openai-codex", "gpt-6-luna"));
    assert.equal(fast.service_tier, "priority");

    const astra = { model: "gpt-6-astra-mini", service_tier: "priority" };
    await hooks.before_provider_request({ payload: astra }, ctx("openai-codex", "gpt-6-astra-mini"));
    assert.equal(astra.service_tier, undefined, "Astra strips even a preexisting priority tier");

    const claude = { model: "claude-opus-5", speed: "fast" };
    await hooks.before_provider_request({ payload: claude }, ctx("anthropic", "claude-opus-5"));
    assert.equal(claude.speed, undefined, "Claude fast defaults off");
    await commands.fast.handler("claude on", { ui });
    assert.match(notices.at(-1), /extra usage/);
    const enabled = { model: "claude-opus-5" };
    const claudeCtx = ctx("anthropic", "claude-opus-5", { supportsEagerToolInputStreaming: false });
    await hooks.before_provider_request({ payload: enabled }, claudeCtx);
    assert.equal(enabled.speed, "fast");
    const event = { headers: {} };
    await hooks.before_provider_headers(event, claudeCtx);
    assert.match(event.headers["anthropic-beta"], /fast-mode-2026-02-01/);
  });

  test("double-Escape installs its editor even when another editor exists", async () => {
    const mod = await load("double-escape-clear");
    let installed;
    let start;
    mod({ on: (_name, fn) => { start = fn; } });
    start({}, { mode: "tui", ui: { getEditorComponent: () => ({}), setEditorComponent: (factory) => { installed = factory; } } });
    assert.equal(typeof installed, "function");
  });

  test("Abliteration model pricing and env-only credential reference", async () => {
    const mod = await load("abliteration");
    let provider;
    mod({ registerProvider: (name, value) => { provider = { name, ...value }; } });
    assert.equal(provider.apiKey, "$ABLITERATION_API_KEY");
    assert.deepEqual(provider.models.map(({ id }) => id), ["abliterated-model", "abliterated-model-large-v2", "abliterated-model-large"]);
    assert.deepEqual(provider.models[0].cost, { input: 1, output: 3, cacheRead: 0.1, cacheWrite: 0 });
    assert.deepEqual(provider.models[1].cost, { input: 3, output: 5, cacheRead: 0.3, cacheWrite: 0 });
  });
} finally {
  process.on("exit", () => rmSync(configDir, { recursive: true, force: true }));
}
