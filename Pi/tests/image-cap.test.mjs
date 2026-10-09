import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
const root = process.env.PI_PACKAGE_ROOT || join(execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim(), "@earendil-works/pi-coding-agent");
const { createJiti } = await import(pathToFileURL(join(root, "node_modules/jiti/lib/jiti.mjs")).href);
const here = dirname(fileURLToPath(import.meta.url));
const mod = await createJiti(import.meta.url).import(resolve(here, "../extensions/image-cap.ts"));
function png(width, height) { const b = Buffer.alloc(24); Buffer.from([137,80,78,71,13,10,26,10]).copy(b); b.writeUInt32BE(width, 16); b.writeUInt32BE(height, 20); return b; }
test("sniffs PNG bytes, extracts dimensions, fixes mislabeled compliant images", async () => {
  const data = png(600, 400).toString("base64");
  assert.equal(mod.sniffMimeType(png(600, 400)), "image/png");
  assert.deepEqual(mod.dimensionsFromBytes(png(600, 400)), { width: 600, height: 400 });
  const result = await mod.normalizeImageBlock({ type: "image", mimeType: "image/jpeg", data });
  assert.equal(result.changed, true); assert.equal(result.block.mimeType, "image/png");
  assert.deepEqual(mod.imageViolations(result.block), []);
});
test("invalid blocks and unavailable converters pass through without loss", async () => {
  const bad = { type: "image", mimeType: "image/png", data: "not base64!" };
  assert.equal((await mod.normalizeImageBlock(bad)).block, bad);
  const oversized = { type: "image", mimeType: "image/png", data: png(4000, 2000).toString("base64") };
  const untouched = await mod.normalizeImageBlock(oversized, { binaries: [] });
  assert.equal(untouched.changed, false); assert.equal(untouched.block, oversized);
});
test("input, message_end, and context hooks normalize image content", async () => {
  const handlers = {}; mod.default({ on: (name, fn) => handlers[name] = fn });
  const image = { type: "image", mimeType: "image/jpeg", data: png(300, 200).toString("base64") };
  const input = await handlers.input({ text: "inspect", images: [image] });
  assert.equal(input.action, "transform"); assert.equal(input.images[0].mimeType, "image/png");
  const message = await handlers.message_end({ message: { role: "user", content: [image] } });
  assert.equal(message.message.content[0].mimeType, "image/png");
  const context = await handlers.context({ messages: [{ role: "custom", content: [image] }] });
  assert.equal(context.messages[0].content[0].mimeType, "image/png");
});
