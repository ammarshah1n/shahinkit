import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { chmodSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

process.env.PI_CODING_AGENT_DIR = `${process.env.HOME}/.pi/test-agent`;
process.env.PI_REMOTE_SUBAGENT_HOST = "build-host";
process.env.PI_REMOTE_SUBAGENT_HOME = "/home/worker";
process.env.PI_REMOTE_SUBAGENT_MAP = "/tmp/project=/srv/project;/tmp/other=/srv/other";

const PI_ROOT = process.env.PI_PACKAGE_ROOT || join(
	execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim(),
	"@earendil-works/pi-coding-agent",
);
const { createJiti } = await import(pathToFileURL(join(PI_ROOT, "node_modules/jiti/lib/jiti.mjs")).href);
const here = dirname(fileURLToPath(import.meta.url));
const remote = await createJiti(import.meta.url, {
	alias: { "@earendil-works/pi-coding-agent": PI_ROOT },
}).import(resolve(here, "../extensions/subagent/remote.ts"));

assert.equal(remote.shellQuote("a'b"), "'a'\\''b'");
assert.equal(remote.mapLocalCwdToRemote("/tmp/project/pkg"), "/srv/project/pkg");
assert.equal(remote.mapLocalCwdToRemote("/tmp/project-two"), null);
assert.equal(remote.mapLocalCwdToRemote("/unmapped"), null);
assert.equal(remote.composeRemoteCommand("/outside", []), "exit 64");

const command = remote.composeRemoteCommand("/srv/project/pkg", ["-e", `${process.env.HOME}/.pi/test-agent/extensions/fast-mode.ts`]);
assert.match(command, /PI_CODING_AGENT_DIR='\/home\/worker\/\.pi\/test-agent'/);
assert.match(command, /realpath '\/srv\/project'/);
assert.match(command, /realpath '\/srv\/project\/pkg'/);
assert.match(command, /cd "\$cwd"/);
assert.match(command, /'--no-extensions'/);
assert.match(command, /\/home\/worker\/\.pi\/test-agent\/extensions\/fast-mode\.ts/);

const fake = mkdtempSync(join(tmpdir(), "shahinkit-ssh-"));
const ssh = join(fake, "ssh");
const log = join(fake, "capture");
writeFileSync(ssh, `#!/bin/sh\nprintf '%s\\n' "$*" >> "$SSH_LOG.commands"\ncat >> "$SSH_LOG.stdin"\nprintf '\\n---\\n' >> "$SSH_LOG.stdin"\n`);
chmodSync(ssh, 0o700);
const oldPath = process.env.PATH;
process.env.PATH = `${fake}:${oldPath}`;
process.env.SSH_LOG = log;
try {
	const staged = await remote.stageRemotePromptFiles("SYSTEM PRIVATE WORDS", "TASK PRIVATE WORDS");
	assert.match(staged.system, /^\/home\/worker\/\.pi\/tmp\/subagent-[0-9a-f-]+\/system\.md$/);
	assert.match(staged.task, /\/task\.md$/);
	await remote.removeRemotePromptFiles(staged.dir);
	const commands = readFileSync(`${log}.commands`, "utf8");
	const stdin = readFileSync(`${log}.stdin`, "utf8");
	assert.doesNotMatch(commands, /SYSTEM PRIVATE WORDS|TASK PRIVATE WORDS/);
	assert.match(stdin, /SYSTEM PRIVATE WORDS/);
	assert.match(stdin, /Task: TASK PRIVATE WORDS/);
	assert.match(commands, /rm -rf/);
	writeFileSync(ssh, "#!/bin/sh\nexit 1\n");
	await assert.rejects(
		remote.stageRemotePromptFiles("SYSTEM", "TASK"),
		/remote prompt staging and rollback failed/,
	);
} finally {
	process.env.PATH = oldPath;
	delete process.env.SSH_LOG;
	rmSync(fake, { recursive: true, force: true });
}

console.log("RESULT: ALL PASS");
