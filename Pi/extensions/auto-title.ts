// Instantly name the first real interactive prompt; an optional configured model can refine it.
// When PI_AUTO_TITLE_MODEL is set, up to 1200 prompt characters are sent to that provider.
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const MAX = 48;
const FILLER = /^(?:(?:hey|hi|ok(?:ay)?|so|yo|please|pls|can you|could you|would you|i want you to|i need you to|i want to|i need to|let'?s|lets|go(?: now)?|now)[\s,.:!-]+)+/i;
export function heuristicTitle(text: string): string {
  let t = text.replace(/```[\s\S]*?```/g, " ").replace(/<[^>]+>/g, " ").replace(/\[(?:image|file)[^\]]*\]/gi, " ").replace(/https?:\/\/\S+/g, " ");
  if (/^\s*\/[\w:-]+(?:\s|$)/.test(t)) return "";
  t = t.split("\n").map((line) => line.trim()).find((line) => /[a-z]{3}/i.test(line.replace(FILLER, ""))) ?? "";
  t = t.replace(/^[#>*\-\d.)\s]+/, "").replace(/[`*_~]/g, "");
  for (let previous = ""; previous !== t;) { previous = t; t = t.replace(FILLER, "").replace(/^\d+[.)]\s*/, ""); }
  t = t.split(/(?<=[.?!])\s|;\s/)[0].replace(/[\s.,:;!?-]+$/, "").replace(/\s+(?:please|pls|thanks|thx)$/i, "").replace(/\s+/g, " ").trim();
  if (t.length > MAX) t = t.slice(0, MAX).replace(/\s+\S*$/, "") + "…";
  return t ? t[0].toUpperCase() + t.slice(1) : "";
}

async function llmTitle(ctx: any, text: string): Promise<string> {
  const configured = process.env.PI_AUTO_TITLE_MODEL;
  const slash = configured?.indexOf("/") ?? -1;
  if (!configured || slash < 1 || slash === configured.length - 1) return "";
  const model = ctx.modelRegistry?.find(configured.slice(0, slash), configured.slice(slash + 1));
  if (!model) return "";
  const auth = await ctx.modelRegistry.getApiKeyAndHeaders(model);
  if (!auth.ok) return "";
  const base = (auth.baseUrl ?? model.baseUrl ?? "").replace(/\/$/, "");
  if (!base) return "";
  const response = await fetch(`${base}/chat/completions`, {
    method: "POST", signal: AbortSignal.timeout(4000),
    headers: { "content-type": "application/json", authorization: `Bearer ${auth.apiKey}`, ...(auth.headers ?? {}) },
    body: JSON.stringify({ model: model.id, max_tokens: 24, temperature: 0,
      messages: [
        { role: "system", content: "Name the user's task in 2-5 words for a terminal tab title. Use Title Case, no quotes or ending punctuation. Output only the title." },
        { role: "user", content: text.slice(0, 1200) },
      ],
    }),
  });
  if (!response.ok) return "";
  const json: any = await response.json();
  const title = String(json?.choices?.[0]?.message?.content ?? "").split("\n")[0].replace(/^["'`*\s]+|["'`*.\s]+$/g, "").trim();
  return title.length >= 3 && title.length <= 60 ? title : "";
}

export default function autoTitle(pi: ExtensionAPI) {
  if (process.env.PI_AUTO_TITLE === "0") return;
  let done = false;
  pi.on("session_start", async () => { done = Boolean(pi.getSessionName()); });
  pi.on("input", async (event: any, ctx: any) => {
    if (done || !ctx.hasUI || event.source === "extension" || event.streamingBehavior) return { action: "continue" };
    if (pi.getSessionName()) { done = true; return { action: "continue" }; }
    const prompt = event.text ?? "";
    const quick = heuristicTitle(prompt);
    if (!quick) return { action: "continue" };
    done = true;
    pi.setSessionName(quick);
    if (process.env.PI_AUTO_TITLE_LLM !== "0" && process.env.PI_AUTO_TITLE_MODEL) {
      llmTitle(ctx, prompt).then((better) => { if (better && pi.getSessionName() === quick) pi.setSessionName(better); }).catch(() => {});
    }
    return { action: "continue" };
  });
}
