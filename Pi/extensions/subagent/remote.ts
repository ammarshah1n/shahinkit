import { spawn } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

const FEDORA = "fedora";
const REMOTE_HOME = "/home/ammarshahin";
const REACHABILITY_CACHE_MS = 60_000;
const RECEIPT_LOG = "/Users/integrale/Documents/station/logs/remote-subagent-build.log";
const KILL_SWITCH = path.join(os.homedir(), ".pi", "agent", "remote-subagents-off");

type FallbackReason = "unreachable" | "unmapped" | "disabled";

export type RemoteSubagentDispatch =
	| { remote: true; command: "ssh"; args: string[]; mappedCwd: string }
	| { remote: false; reason: FallbackReason };

const reachabilityCache = new Map<string, { reachable: boolean; expiresAt: number }>();
const pendingReachabilityChecks = new Map<string, Promise<boolean>>();

/** Quote exactly one POSIX-shell argument. */
export function shellQuote(value: string): string {
	return `'${value.replace(/'/g, "'\\''")}'`;
}

function mapRoot(cwd: string, localRoot: string, remoteRoot: string): string | null {
	if (cwd === localRoot) return remoteRoot;
	return cwd.startsWith(`${localRoot}/`) ? `${remoteRoot}${cwd.slice(localRoot.length)}` : null;
}

export function mapMacCwdToFedora(cwd: string): string | null {
	const resolved = path.resolve(cwd);
	return (
		mapRoot(resolved, "/Users/integrale/Documents", `${REMOTE_HOME}/repos`) ??
		mapRoot(resolved, "/Users/integrale/time-manager-desktop", `${REMOTE_HOME}/repos/time-manager-desktop`) ??
		mapRoot(resolved, "/Users/integrale/facilitated", `${REMOTE_HOME}/repos/facilitated`)
	);
}

/**
 * Rewrite a Mac home path to its fedora equivalent.
 * The caller passes absolute Mac paths (e.g. `-e .../extensions/fast-mode.ts`);
 * shipped verbatim they make the remote `pi` die with "Extension path does not
 * exist", which killed every remote dispatch until 2026-08-27.
 */
function mapHomePath(value: string): string {
	const home = os.homedir();
	return value === home || value.startsWith(`${home}/`)
		? `${REMOTE_HOME}${value.slice(home.length)}`
		: value;
}

/** Compose the one remote-shell argument supplied to ssh. */
export function composeRemoteCommand(mappedCwd: string, piArgs: string[]): string {
	// Fedora's globally synced extensions include Mac-only imports; subagents only need built-in tools.
	const remotePiArgs = ["--no-extensions", ...piArgs.map(mapHomePath)];
	return `export PATH=$HOME/.local/bin:$PATH; cd ${shellQuote(mappedCwd)} && pi ${remotePiArgs.map(shellQuote).join(" ")}`;
}

function checkFedoraDirectory(mappedCwd: string): Promise<boolean> {
	return new Promise((resolve) => {
		let settled = false;
		const finish = (reachable: boolean) => {
			if (settled) return;
			settled = true;
			resolve(reachable);
		};

		try {
			const proc = spawn(
				"ssh",
				["-o", "BatchMode=yes", "-o", "ConnectTimeout=3", FEDORA, `test -d ${shellQuote(mappedCwd)}`],
				{ stdio: "ignore" },
			);
			proc.once("error", () => finish(false));
			proc.once("close", (code) => finish(code === 0));
		} catch {
			finish(false);
		}
	});
}

async function isFedoraDirectoryReachable(mappedCwd: string): Promise<boolean> {
	const now = Date.now();
	const cached = reachabilityCache.get(mappedCwd);
	if (cached && cached.expiresAt > now) return cached.reachable;

	const pending = pendingReachabilityChecks.get(mappedCwd);
	if (pending) return pending;

	const check = checkFedoraDirectory(mappedCwd)
		.then((reachable) => {
			reachabilityCache.set(mappedCwd, { reachable, expiresAt: Date.now() + REACHABILITY_CACHE_MS });
			return reachable;
		})
		.catch(() => false)
		.finally(() => pendingReachabilityChecks.delete(mappedCwd));
	pendingReachabilityChecks.set(mappedCwd, check);
	return check;
}

async function logReceipt(agent: string, cwd: string, dispatch: RemoteSubagentDispatch): Promise<void> {
	const receipt = {
		at: new Date().toISOString(),
		agent,
		cwd,
		route: dispatch.remote ? "remote" : "local",
		...(dispatch.remote ? { mappedCwd: dispatch.mappedCwd } : { reason: dispatch.reason }),
	};
	try {
		await fs.promises.mkdir(path.dirname(RECEIPT_LOG), { recursive: true });
		await fs.promises.appendFile(RECEIPT_LOG, `${JSON.stringify(receipt)}\n`, "utf8");
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
		} else {
			const mappedCwd = mapMacCwdToFedora(cwd);
			if (!mappedCwd) {
				dispatch = { remote: false, reason: "unmapped" };
			} else if (!(await isFedoraDirectoryReachable(mappedCwd))) {
				dispatch = { remote: false, reason: "unreachable" };
			} else {
				dispatch = {
					remote: true,
					command: "ssh",
					args: ["-o", "BatchMode=yes", FEDORA, composeRemoteCommand(mappedCwd, piArgs)],
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
