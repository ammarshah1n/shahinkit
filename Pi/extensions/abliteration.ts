// Abliteration.ai — OpenAI-compatible provider.
// Static model metadata keeps the provider visible in /login before credentials are saved.
// ponytail: no custom stream adapter; pi's OpenAI Chat Completions client is the adapter.
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const models = [
  {
    id: "abliterated-model",
    name: "Abliterated Model",
    reasoning: true,
    input: ["text", "image"] as ("text" | "image")[],
    cost: { input: 3, output: 3, cacheRead: 0.3, cacheWrite: 0 },
    contextWindow: 262144,
    maxTokens: 262134,
    compat: {
      supportsStore: false,
      supportsDeveloperRole: false,
      supportsReasoningEffort: false,
      maxTokensField: "max_tokens" as const,
    },
  },
  {
    id: "abliterated-model-large",
    name: "Abliterated Large",
    reasoning: true,
    input: ["text"] as ("text" | "image")[],
    cost: { input: 5, output: 5, cacheRead: 0.5, cacheWrite: 0 },
    contextWindow: 1000000,
    maxTokens: 999990,
    compat: {
      supportsStore: false,
      supportsDeveloperRole: false,
      supportsReasoningEffort: false,
      maxTokensField: "max_tokens" as const,
    },
  },
];

export default function (pi: ExtensionAPI) {
  pi.registerProvider("abliteration-ai", {
    name: "Abliteration.ai",
    baseUrl: "https://api.abliteration.ai/v1",
    apiKey: "$ABLITERATION_API_KEY",
    api: "openai-completions",
    models,
  });
}
