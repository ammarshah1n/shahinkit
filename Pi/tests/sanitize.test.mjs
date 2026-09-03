import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const PI_ROOT = process.env.PI_PACKAGE_ROOT || join(
	execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim(),
	"@earendil-works/pi-coding-agent",
);
const { createJiti } = await import(pathToFileURL(join(PI_ROOT, "node_modules/jiti/lib/jiti.mjs")).href);
const here = dirname(fileURLToPath(import.meta.url));
const { sanitizeTerminalText } = await createJiti(import.meta.url).import(resolve(here, "../extensions/lib/sanitize.ts"));

const hostile = "ok\x1b]0;owned\x07\x1b[31mred\x1b[0m\x1b_payload\x1b\\\u202etxt\x00\r";
assert.equal(sanitizeTerminalText(hostile), "okredtxt");
assert.equal(sanitizeTerminalText("abcdef", 3), "abc");
console.log("sanitize terminal text: pass");
