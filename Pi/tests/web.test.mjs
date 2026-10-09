import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const here = dirname(fileURLToPath(import.meta.url));
const script = resolve(here, "../bin/web");
const home = mkdtempSync(`${tmpdir()}/shahinkit-web-`);
const env = { ...process.env, HOME: home, WEB_PROXY: "not a proxy" };
delete env.BRAVE_API_KEY;
delete env.EXA_API_KEY;

try {
  const help = spawnSync("python3", [script, "--help"], { encoding: "utf8", env });
  assert.equal(help.status, 0, help.stderr);
  assert.match(help.stdout, /web search/);
  assert.match(help.stdout, /web research/);

  const usage = spawnSync("python3", [script], { encoding: "utf8", env });
  assert.equal(usage.status, 2);
  assert.match(usage.stderr, /web get/);

  const missingKeys = spawnSync("python3", [script, "search", "no network"], {
    encoding: "utf8", env,
  });
  assert.equal(missingKeys.status, 1);
  assert.match(missingKeys.stderr, /missing .* API key/i);
  assert.doesNotMatch(missingKeys.stderr, /proxy retry|blocked|unreachable/i);
} finally {
  rmSync(home, { recursive: true, force: true });
}

console.log("RESULT: ALL PASS");
