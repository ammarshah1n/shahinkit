import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { chmodSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = mkdtempSync(join(tmpdir(), "shahinkit-subagent-"));
const config = join(root, "config");
const fakeBin = join(root, "bin");
mkdirSync(join(config, "agents"), { recursive: true });
mkdirSync(fakeBin);
writeFileSync(join(config, "agents", "worker.md"), "---\nname: worker\ndescription: test worker\n---\n");
const fakePi = join(fakeBin, "pi");
writeFileSync(fakePi, `#!/bin/sh\nprintf '%s\\n' '{"type":"message_end","message":{"role":"assistant","content":[{"type":"text","text":"partial child output"}],"stopReason":"end"}}'\nfor arg do case "$arg" in @*) grep -Eq 'bounded|aborted' "\${arg#@}" && sleep 5;; esac; done\n`);
chmodSync(fakePi, 0o700);

process.env.PI_CODING_AGENT_DIR = config;
process.env.PI_SUBAGENT_TIMEOUT_MIN = "0.02";
process.env.PATH = `${fakeBin}:${process.env.PATH}`;
const PI_ROOT = process.env.PI_PACKAGE_ROOT || join(
  execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim(),
  "@earendil-works/pi-coding-agent",
);
const { createJiti } = await import(pathToFileURL(join(PI_ROOT, "node_modules/jiti/lib/jiti.mjs")).href);
const here = dirname(fileURLToPath(import.meta.url));
const extension = await createJiti(import.meta.url, {
  alias: {
    "@earendil-works/pi-coding-agent": PI_ROOT,
    "@earendil-works/pi-ai": join(PI_ROOT, "node_modules/@earendil-works/pi-ai"),
    "@earendil-works/pi-tui": join(PI_ROOT, "node_modules/@earendil-works/pi-tui"),
    typebox: join(PI_ROOT, "node_modules/typebox/build/index.mjs"),
  },
}).import(resolve(here, "../extensions/subagent/index.ts"));

const tools = new Map();
const listeners = new Map();
let backgroundResults = 0;
let resolveBackground;
const backgroundDone = new Promise((resolve) => { resolveBackground = resolve; });
extension.default({
  registerTool: (tool) => tools.set(tool.name, tool),
  on: (event, callback) => listeners.set(event, callback),
  sendMessage: () => { if (++backgroundResults === 2) resolveBackground(); },
});
const ctx = {
  cwd: root,
  isProjectTrusted: () => false,
  hasUI: false,
  ui: { notify() {}, confirm: async () => true, setStatus() {} },
};
const tool = tools.get("subagent");
const originalScript = process.argv[1];
process.argv[1] = join(root, "missing-entrypoint.js");
try {
  const timeout = await tool.execute("timeout", { agent: "worker", task: "bounded" }, new AbortController().signal, undefined, ctx);
  assert.equal(timeout.isError, true);
  assert.match(timeout.content[0].text, /timed out/);
  assert.match(timeout.content[0].text, /partial child output/);
  assert.equal(timeout.details.results[0].stopReason, "error");

  const abortController = new AbortController();
  const abortedCall = tool.execute("abort", { agent: "worker", task: "aborted" }, abortController.signal, undefined, ctx);
  setTimeout(() => abortController.abort(), 300);
  const aborted = await abortedCall;
  assert.equal(aborted.isError, true);
  assert.match(aborted.content[0].text, /partial child output/);
  assert.equal(aborted.details.results[0].stopReason, "aborted");

  const forced = await tool.execute("parallel", {
    tasks: [{ agent: "worker", task: "one" }, { agent: "worker", task: "two" }],
  }, undefined, undefined, ctx);
  assert.match(forced.content[0].text, /Multiple blocking tasks are forbidden; forced background: true/);
  await backgroundDone;
} finally {
  process.argv[1] = originalScript;
  rmSync(root, { recursive: true, force: true });
}
console.log("RESULT: ALL PASS");
