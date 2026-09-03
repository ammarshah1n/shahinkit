// Terminal-safe text for untrusted model, tool, cache, and status output.
const OSC = /\x1b\][^\x07\x1b]*(?:\x07|\x1b\\|$)/g;
const ST_BLOCK = /\x1b[P_^][\s\S]*?(?:\x1b\\|$)/g;
const CSI = /\x1b\[[0-?]*[ -/]*[@-~]/g;
const CONTROLS = /[\u0000-\u0008\u000b-\u001f\u007f-\u009f\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]/g;

export function sanitizeTerminalText(value: unknown, maxLength = 200_000): string {
	return String(value ?? "")
		.replace(OSC, "")
		.replace(ST_BLOCK, "")
		.replace(CSI, "")
		.replace(/\x1b/g, "")
		.replace(CONTROLS, "")
		.slice(0, maxLength);
}
