import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { getAgentDir } from "@earendil-works/pi-coding-agent";

const AGENT_DIR = getAgentDir();
const REMOTE_HOST = process.env.PI_REMOTE_SUBAGENT_HOST ?? "";
const REMOTE_HOME = process.env.PI_REMOTE_SUBAGENT_HOME ?? "";
const REACHABILITY_CACHE_MS = 60_000;
const RECEIPT_MAX_BYTES = 1_048_576;
const RECEIPT_LOG = process.env.PI_REMOTE_SUBAGENT_RECEIPT_LOG
	?? path.join(AGENT_DIR, "logs", "remote-subagent-build.log");
const KILL_SWITCH = path.join(AGENT_DIR, "remote-subagents-off");

type FallbackReason = "unreachable" | "unmapped" | "disabled" | "unconfigured";

export type RemoteSubagentDispatch =
	| { remote: true; command: "ssh"; args: string[]; mappedCwd: string }
	| { remote: false; reason: FallbackReason };

const reachabilityCache = new Map<string, { reachable: boolean; expiresAt: number }>();
const pendingReachabilityChecks = new Map<string, Promise<boolean>>();
const validRemoteHost = () => /^[A-Za-z0-9][A-Za-z0-9_.@:-]*$/.test(REMOTE_HOST);
const validRemoteHome = () => /^\/[-A-Za-z0-9._/]+$/.test(REMOTE_HOME) && !REMOTE_HOME.split("/").includes("..");

/** Quote exactly one POSIX-shell argument. */
export function shellQuote(value: string): string {
	return `'${value.replace(/'/g, "'\\''")}'`;
}

function canonicalPath(value: string): string {
	try {
		return fs.realpathSync.native(value);
	} catch {
		return path.resolve(value);
	}
}

function mapRoot(cwd: string, localRoot: string, remoteRoot: string): string | null {
	if (cwd === localRoot) return remoteRoot;
	return cwd.startsWith(`${localRoot}/`) ? `${remoteRoot}${cwd.slice(localRoot.length)}` : null;
}

/**
 * PI_REMOTE_SUBAGENT_MAP is a semicolon-separated allowlist:
 *   /local/root=/remote/root;/another/local=/another/remote
 */
export function mapLocalCwdToRemote(cwd: string): string | null {
	const resolved = canonicalPath(cwd);
	for (const entry of (process.env.PI_REMOTE_SUBAGENT_MAP ?? "").split(";")) {
		const split = entry.indexOf("=");
		if (split < 1) continue;
		const localRoot = canonicalPath(entry.slice(0, split));
		const remoteRoot = entry.slice(split + 1).replace(/\/$/, "");
		if (!remoteRoot.startsWith("/")) continue;
		const mapped = mapRoot(resolved, localRoot, remoteRoot);
		if (mapped) return mapped;
	}
	return null;
}

function remoteRootForMappedPath(mappedCwd: string): string | null {
	const roots = (process.env.PI_REMOTE_SUBAGENT_MAP ?? "")
		.split(";")
		.flatMap((entry) => {
			const split = entry.indexOf("=");
			return split < 1 ? [] : [entry.slice(split + 1).replace(/\/$/, "")];
		})
		.filter((root) => root.startsWith("/") && (mappedCwd === root || mappedCwd.startsWith(`${root}/`)))
		.sort((a, b) => b.length - a.length);
	return roots[0] ?? null;
}

/** Resolve both paths remotely and enforce the configured root after symlinks. */
function canonicalRemoteGuard(mappedCwd: string): string | null {
	const root = remoteRootForMappedPath(mappedCwd);
	if (!root) return null;
	return `root=$(realpath ${shellQuote(root)}) && cwd=$(realpath ${shellQuote(mappedCwd)}) && case "$cwd" in "$root"|"$root"/*) ;; *) exit 64 ;; esac`;
}

/** Rewrite a local home path to its remote equivalent. */
function mapHomePath(value: string): string {
	const home = os.homedir();
	return REMOTE_HOME && (value === home || value.startsWith(`${home}/`))
		? `${REMOTE_HOME}${value.slice(home.length)}`
		: value;
}

/** Compose the one remote-shell argument supplied to ssh. */
export function composeRemoteCommand(mappedCwd: string, piArgs: string[]): string {
	// Remote global extensions may be host-specific; workers only need built-in tools.
	const remotePiArgs = ["--no-extensions", ...piArgs.map(mapHomePath)];
	const remoteAgentDir = mapHomePath(AGENT_DIR);
	const guard = canonicalRemoteGuard(mappedCwd);
	if (!guard) return "exit 64";
	return `export PI_CODING_AGENT_DIR=${shellQuote(remoteAgentDir)}; export PATH=$HOME/.local/bin:$PATH; ${guard} && cd "$cwd" && pi ${remotePiArgs.map(shellQuote).join(" ")}`;
}

function remotePromptPrepareCommand(dir: string): string {
	const base = `${REMOTE_HOME.replace(/\/$/, "")}/.pi/tmp`;
	return `[ ! -L ${shellQuote(REMOTE_HOME)} ] && [ ! -L ${shellQuote(`${REMOTE_HOME}/.pi`)} ] && mkdir -p ${shellQuote(base)} && [ ! -L ${shellQuote(base)} ] && home=$(realpath ${shellQuote(REMOTE_HOME)}) && root=$(realpath ${shellQuote(base)}) && [ "$root" = "$home/.pi/tmp" ] && mkdir -p ${shellQuote(dir)} && [ ! -L ${shellQuote(dir)} ] && staged=$(realpath ${shellQuote(dir)}) && [ "$staged" = "$root/${path.posix.basename(dir)}" ]`;
}

function remotePromptRemoveCommand(dir: string): string {
	const base = `${REMOTE_HOME.replace(/\/$/, "")}/.pi/tmp`;
	return `if [ -e ${shellQuote(dir)} ]; then [ ! -L ${shellQuote(REMOTE_HOME)} ] && [ ! -L ${shellQuote(base)} ] && home=$(realpath ${shellQuote(REMOTE_HOME)}) && root=$(realpath ${shellQuote(base)}) && [ "$root" = "$home/.pi/tmp" ] && [ ! -L ${shellQuote(dir)} ] && staged=$(realpath ${shellQuote(dir)}) && [ "$staged" = "$root/${path.posix.basename(dir)}" ] || exit 65; rm -rf "$staged"; fi`;
}

function sshWithInput(command: string, input?: string): Promise<void> {
	return new Promise((resolve, reject) => {
		const proc = spawn("ssh", ["-o", "BatchMode=yes", "-o", "ConnectTimeout=5", REMOTE_HOST, command], {
			stdio: ["pipe", "ignore", "ignore"],
		});
		proc.once("error", reject);
		proc.once("close", (code) => code === 0 ? resolve() : reject(new Error("remote prompt operation failed")));
		proc.stdin.end(input ?? "");
	});
}

export async function stageRemotePromptFiles(systemPrompt: string, task: string): Promise<{ dir: string; system: string; task: string }> {
	if (!validRemoteHost() || !validRemoteHome()) throw new Error("invalid remote prompt configuration");
	const dir = `${REMOTE_HOME.replace(/\/$/, "")}/.pi/tmp/subagent-${randomUUID()}`;
	const system = `${dir}/system.md`;
	const taskPath = `${dir}/task.md`;
	try {
		const prepare = remotePromptPrepareCommand(dir);
		await sshWithInput(`umask 077; ${prepare} && cat > ${shellQuote(system)}`, systemPrompt);
		await sshWithInput(`umask 077; ${prepare} && cat > ${shellQuote(taskPath)}`, `Task: ${task}\n`);
		return { dir, system, task: taskPath };
	} catch (error) {
		try {
			await sshWithInput(remotePromptRemoveCommand(dir));
		} catch {
			throw new Error(`remote prompt staging and rollback failed; remove ${dir} manually`, { cause: error });
		}
		throw error;
	}
}

export async function removeRemotePromptFiles(dir: string): Promise<void> {
	const base = `${REMOTE_HOME.replace(/\/$/, "")}/.pi/tmp/subagent-`;
	const suffix = dir.startsWith(base) ? dir.slice(base.length) : "";
	if (!validRemoteHost() || !validRemoteHome() || !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(suffix)) {
		throw new Error("refusing invalid remote prompt cleanup path");
	}
	await sshWithInput(remotePromptRemoveCommand(dir));
}

function remoteExtensionPath(piArgs: string[]): string | null {
	const index = piArgs.indexOf("-e");
	return index >= 0 && piArgs[index + 1] ? mapHomePath(piArgs[index + 1]) : null;
}

function checkRemotePrerequisites(mappedCwd: string, piArgs: string[]): Promise<boolean> {
	return new Promise((resolve) => {
		let settled = false;
		const finish = (reachable: boolean) => {
			if (settled) return;
			settled = true;
			resolve(reachable);
		};
		const extensionPath = remoteExtensionPath(piArgs);
		const guard = canonicalRemoteGuard(mappedCwd);
		if (!guard) return finish(false);
		const check = `${guard} && test -d "$cwd"${extensionPath ? ` && test -f ${shellQuote(extensionPath)}` : ""}`;

		try {
			const proc = spawn(
				"ssh",
				["-o", "BatchMode=yes", "-o", "ConnectTimeout=3", REMOTE_HOST, check],
				{ stdio: "ignore" },
			);
			proc.once("error", () => finish(false));
			proc.once("close", (code) => finish(code === 0));
		} catch {
			finish(false);
		}
	});
}

async function areRemotePrerequisitesReachable(mappedCwd: string, piArgs: string[]): Promise<boolean> {
	const cacheKey = `${mappedCwd}\0${remoteExtensionPath(piArgs) ?? ""}`;
	const now = Date.now();
	const cached = reachabilityCache.get(cacheKey);
	if (cached && cached.expiresAt > now) return cached.reachable;

	const pending = pendingReachabilityChecks.get(cacheKey);
	if (pending) return pending;

	const check = checkRemotePrerequisites(mappedCwd, piArgs)
		.then((reachable) => {
			reachabilityCache.set(cacheKey, { reachable, expiresAt: Date.now() + REACHABILITY_CACHE_MS });
			return reachable;
		})
		.catch(() => false)
		.finally(() => pendingReachabilityChecks.delete(cacheKey));
	pendingReachabilityChecks.set(cacheKey, check);
	return check;
}

async function logReceipt(agent: string, cwd: string, dispatch: RemoteSubagentDispatch): Promise<void> {
	// Default local operation is not diagnostically interesting and should not
	// create an indefinite cwd history merely because remote routing is absent.
	if (!dispatch.remote && dispatch.reason === "unconfigured") return;
	const receipt = {
		at: new Date().toISOString(),
		agent,
		cwd,
		route: dispatch.remote ? "remote" : "local",
		...(dispatch.remote ? { mappedCwd: dispatch.mappedCwd } : { reason: dispatch.reason }),
	};
	try {
		await fs.promises.mkdir(path.dirname(RECEIPT_LOG), { recursive: true });
		try {
			if ((await fs.promises.stat(RECEIPT_LOG)).size >= RECEIPT_MAX_BYTES) {
				await fs.promises.rm(`${RECEIPT_LOG}.1`, { force: true });
				await fs.promises.rename(RECEIPT_LOG, `${RECEIPT_LOG}.1`);
				await fs.promises.chmod(`${RECEIPT_LOG}.1`, 0o600);
			}
		} catch { /* no current receipt */ }
		await fs.promises.appendFile(RECEIPT_LOG, `${JSON.stringify(receipt)}\n`, { encoding: "utf8", mode: 0o600 });
		await fs.promises.chmod(RECEIPT_LOG, 0o600);
	} catch {
		// Receipt failures must never block a safe local dispatch.
	}
}

export async function resolveRemoteSubagent(
	agent: string,
	cwd: string,
	piArgs: string[],
): Promise<RemoteSubagentDispatch> {
	let dispatch: RemoteSubagentDispatch;
	try {
		if (process.env.PI_REMOTE_SUBAGENTS === "0" || fs.existsSync(KILL_SWITCH)) {
			dispatch = { remote: false, reason: "disabled" };
		} else if (
			!REMOTE_HOST || !validRemoteHost() || !validRemoteHome() || !process.env.PI_REMOTE_SUBAGENT_MAP || mapHomePath(AGENT_DIR) === AGENT_DIR
		) {
			dispatch = { remote: false, reason: "unconfigured" };
		} else {
			const mappedCwd = mapLocalCwdToRemote(cwd);
			if (!mappedCwd) {
				dispatch = { remote: false, reason: "unmapped" };
			} else if (!(await areRemotePrerequisitesReachable(mappedCwd, piArgs))) {
				dispatch = { remote: false, reason: "unreachable" };
			} else {
				dispatch = {
					remote: true,
					command: "ssh",
					args: ["-o", "BatchMode=yes", REMOTE_HOST, composeRemoteCommand(mappedCwd, piArgs)],
					mappedCwd,
				};
			}
		}
	} catch {
		dispatch = { remote: false, reason: "unreachable" };
	}

	await logReceipt(agent, cwd, dispatch);
	return dispatch;
}
