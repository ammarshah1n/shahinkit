import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = mkdtempSync(join(tmpdir(), "shahinkit-trust-"));
const config = join(root, "config");
const project = join(root, "project");
mkdirSync(join(config, "agents"), { recursive: true });
mkdirSync(join(project, ".pi", "agents"), { recursive: true });
writeFileSync(join(project, ".pi", "agents", "project-worker.md"), `---\nname: project-worker\ndescription: test\n---\nPROJECT_PROMPT\n`);
process.env.PI_CODING_AGENT_DIR = config;

const PI_ROOT = process.env.PI_PACKAGE_ROOT || join(
	execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim(),
	"@earendil-works/pi-coding-agent",
);
const { createJiti } = await import(pathToFileURL(join(PI_ROOT, "node_modules/jiti/lib/jiti.mjs")).href);
const here = dirname(fileURLToPath(import.meta.url));
const agents = await createJiti(import.meta.url, {
	alias: { "@earendil-works/pi-coding-agent": PI_ROOT },
}).import(resolve(here, "../extensions/subagent/agents.ts"));

const blocked = agents.discoverAgents(project, "project", false);
assert.deepEqual(blocked.agents, []);
assert.equal(blocked.projectAgentsDir, null);

const trusted = agents.discoverAgents(project, "project", true);
assert.equal(trusted.agents.length, 1);
assert.equal(trusted.agents[0].name, "project-worker");
assert.equal(trusted.agents[0].source, "project");

rmSync(root, { recursive: true, force: true });
console.log("RESULT: ALL PASS");
