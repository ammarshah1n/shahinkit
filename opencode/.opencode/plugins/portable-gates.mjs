import { managedFeatures } from "./portable-gates.features.mjs";

const DEFAULT_MODE = "full";
const PONYTAIL_MODES = new Set(["off", "lite", "full", "ultra"]);
const CAVEMAN_MODES = new Set(["off", "lite", "full", "ultra", "wenyan-lite", "wenyan", "wenyan-ultra"]);
const sessionModes = new Map();
const enabledModes = {
  ponytail: managedFeatures.ponytail !== false,
  caveman: managedFeatures.caveman !== false,
};

function sessionID(input) {
  const value = input?.sessionID ?? input?.sessionId ?? input?.session?.id;
  return typeof value === "string" && value ? value : null;
}

function selectedMode(text, command, allowed) {
  const source = String(text ?? "").trim().toLowerCase();
  if (!source) return null;
  const clauses = source.split(/[;\n.!?]+/).map((clause) => clause.trim()).filter(Boolean);
  const polite = /^(?:(?:please|kindly|just)\s+|(?:can|could|would)\s+you\s+)?/;
  const negated = /\b(?:do not(?:\s+ever)?|don't|never|not|avoid)\b/;
  const explicit = new RegExp(`^(?:stop\\s+${command}|${command}\\s+off)$`);
  const slash = new RegExp(`^/${command}(?:\\s+(\\S+))?$`);
  for (const clause of clauses) {
    if (negated.test(clause)) continue;
    const commandClause = clause.replace(polite, "");
    const slashMatch = commandClause.match(slash);
    if (slashMatch) {
      const value = slashMatch[1] || DEFAULT_MODE;
      if (allowed.has(value)) return value;
      continue;
    }
    if (commandClause === "normal mode" || commandClause === "use normal mode" || explicit.test(commandClause)) return "off";
  }
  return null;
}

function requestedModes(parts) {
  const next = {};
  for (const part of Array.isArray(parts) ? parts : []) {
    if (part?.type !== "text") continue;
    const ponytail = selectedMode(part.text, "ponytail", PONYTAIL_MODES);
    const caveman = selectedMode(part.text, "caveman", CAVEMAN_MODES);
    if (ponytail) next.ponytail = ponytail;
    if (caveman) next.caveman = caveman;
  }
  return next;
}

function commandMode(argumentsText, allowed) {
  const value = String(argumentsText ?? "").trim().toLowerCase() || DEFAULT_MODE;
  return allowed.has(value) ? value : null;
}

function setModes(id, modes) {
  if (!id || Object.keys(modes).length === 0) return;
  sessionModes.set(id, { ...sessionModes.get(id), ...modes });
}

function warn(client) {
  try {
    client?.app?.log?.({
      body: { service: "shahinkit-portable-gates", level: "warn", message: "ignored invalid lifecycle event" },
    });
  } catch {
    // Logging is best-effort; plugins must not hide an OpenCode session failure.
  }
}

function ponytailInstruction(mode) {
  return `PONYTAIL MODE ACTIVE (${mode}). Use smallest correct solution. Prefer existing code, standard library, and native features. Do not simplify security, data-loss protection, accessibility, or explicit requirements.`;
}

function cavemanInstruction(mode) {
  return `CAVEMAN MODE ACTIVE (${mode}). Preserve technical substance with terse prose. Code, commits, PRs, security warnings, irreversible actions, ambiguity, and clarification requests remain normal clarity.`;
}

export default async ({ client } = {}) => ({
  "chat.message": async (input, output) => {
    try {
      const id = sessionID(input);
      const modes = requestedModes(output?.parts);
      setModes(id, modes);
    } catch {
      warn(client);
    }
  },
  "command.execute.before": async (input) => {
    try {
      const id = sessionID(input);
      if (input?.command === "ponytail") setModes(id, { ponytail: commandMode(input.arguments, PONYTAIL_MODES) ?? DEFAULT_MODE });
      if (input?.command === "caveman") setModes(id, { caveman: commandMode(input.arguments, CAVEMAN_MODES) ?? DEFAULT_MODE });
    } catch {
      warn(client);
    }
  },
  "experimental.chat.system.transform": async (input, output) => {
    try {
      if (!Array.isArray(output?.system)) throw new TypeError("system prompt unavailable");
      const modes = sessionModes.get(sessionID(input)) ?? {};
       if (enabledModes.ponytail && (modes.ponytail ?? DEFAULT_MODE) !== "off") output.system.push(ponytailInstruction(modes.ponytail ?? DEFAULT_MODE));
       if (enabledModes.caveman && (modes.caveman ?? DEFAULT_MODE) !== "off") output.system.push(cavemanInstruction(modes.caveman ?? DEFAULT_MODE));
    } catch {
      warn(client);
    }
  },
  event: async ({ event }) => {
    if (event?.type !== "session.deleted") return;
    const id = event.properties?.info?.id ?? event.properties?.sessionID;
    if (typeof id === "string") sessionModes.delete(id);
  },
});
