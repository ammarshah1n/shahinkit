import assert from "node:assert/strict";
import { CavemanPlugin } from "../opencode/plugin.js";

const plugin = await CavemanPlugin();
const reminder = async () => {
  const output = { system: [] };
  await plugin["experimental.chat.system.transform"]({}, output);
  return output.system.join("\n");
};
const choose = async (text) => {
  await plugin["chat.message"]({}, { parts: [{ type: "text", text }] });
};

assert.match(await reminder(), /\(full\)/);
await choose("/caveman lite");
const liteReminder = await reminder();
assert.match(liteReminder, /\(lite\)/);
assert.doesNotMatch(liteReminder, /\(full\)/);
await choose("Activate caveman mode: ultra");
assert.match(await reminder(), /\(ultra\)/);
await choose("/caveman wenyan");
assert.match(await reminder(), /\(wenyan\)/);
await choose("normal mode");
assert.equal(await reminder(), "");
