import { DEFAULT_MODE, isMode, reinforcementLine } from "./caveman-config.js";

function modeChange(text) {
  const prompt = String(text || "").trim().toLowerCase();
  if (!prompt) return null;
  if (/\b(stop|disable|deactivate|turn off)\b.*\bcaveman\b/.test(prompt) ||
      /\bcaveman\b.*\b(stop|disable|deactivate|turn off)\b/.test(prompt) ||
      /\bnormal mode\b/.test(prompt)) return "off";

  const command = prompt.match(/^(?:\/caveman|activate caveman mode:)\s*(\S*)/);
  if (!command) return null;
  const requested = command[1];
  if (!requested) return DEFAULT_MODE;
  if (requested === "off" || requested === "stop" || requested === "disable") return "off";
  if (requested === "wenyan-full") return "wenyan";
  return isMode(requested) ? requested : null;
}

export const CavemanPlugin = async () => {
  let selectedMode = DEFAULT_MODE;

  return {
    "chat.message": async (_input, output) => {
      for (const part of output?.parts || []) {
        if (part?.type !== "text") continue;
        const next = modeChange(part.text);
        if (next) selectedMode = next;
      }
    },
    "experimental.chat.system.transform": async (_input, output) => {
      if (selectedMode !== "off" && Array.isArray(output?.system)) {
        output.system.push(reinforcementLine(selectedMode));
      }
    }
  };
};

export default CavemanPlugin;
