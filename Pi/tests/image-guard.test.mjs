// node Pi/tests/image-guard.test.mjs
import assert from "node:assert/strict";

// Node >= 22.6 strips TypeScript types natively, so the .ts loads directly.
const { default: imageGuard } = await import(new URL("../extensions/image-guard.ts", import.meta.url).href);

const handlers = {};
const pi = { on: (n, h) => (handlers[n] = h) };
imageGuard(pi);
const run = (payload) => handlers.before_provider_request({ payload }, {});

const PNG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0, 0, 0, 13, 1, 2, 3]).toString("base64");
const JUNK = Buffer.from("this is not an image at all, it is text").toString("base64");

// 1. good image, correctly labelled -> untouched
assert.equal(run({ messages: [{ content: [{ type: "image", source: { type: "base64", media_type: "image/png", data: PNG } }] }] }), undefined);

// 2. mislabelled media type -> repaired, request goes through
const fixed = run({ messages: [{ content: [{ type: "image", source: { type: "base64", media_type: "image/jpeg", data: PNG } }] }] });
assert.equal(fixed.messages[0].content[0].source.media_type, "image/png");

// 3. non-image bytes -> replaced with a text note (no codec error)
const dropped = run({ messages: [{ content: [{ type: "image", source: { type: "base64", media_type: "image/png", data: JUNK } }] }] });
assert.equal(dropped.messages[0].content[0].type, "text");
assert.match(dropped.messages[0].content[0].text, /image-guard/);

// 4. OpenAI/Codex data URL, mislabelled + whitespace -> repaired
const url = run({ input: [{ content: [{ type: "input_image", image_url: `data:image/gif;base64,${PNG.slice(0, 8)}\n${PNG.slice(8)}` }] }] });
assert.match(url.input[0].content[0].image_url, /^data:image\/png;base64,[A-Za-z0-9+/=]+$/);

// 5. empty data -> dropped, not crashed
const empty = run({ messages: [{ content: [{ type: "image", source: { type: "base64", media_type: "image/png", data: "" } }] }] });
assert.equal(empty.messages[0].content[0].type, "text");

console.log("image-guard: 5/5 ok");
