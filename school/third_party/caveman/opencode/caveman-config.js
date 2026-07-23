export const DEFAULT_MODE = "full";

export const VALID_MODES = new Set([
  "lite", "full", "ultra", "wenyan-lite", "wenyan", "wenyan-ultra"
]);

export function isMode(mode) {
  return VALID_MODES.has(mode);
}

export function resolveStaticMode(mode) {
  return isMode(mode) ? mode : DEFAULT_MODE;
}

export function reinforcementLine(mode = DEFAULT_MODE) {
  const selected = resolveStaticMode(mode);
  return `CAVEMAN MODE ACTIVE (${selected}). Drop articles/filler/pleasantries/hedging. Fragments OK. Code/commits/PRs: write normal. Security, irreversible actions, ambiguous multi-step instructions, and clarification: write normal.`;
}
