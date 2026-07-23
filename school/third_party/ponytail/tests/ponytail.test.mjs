import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
import test from 'node:test';

const root = fileURLToPath(new URL('..', import.meta.url));
const read = (relative) => readFile(path.join(root, relative), 'utf8');
const sha256 = (value) => createHash('sha256').update(value).digest('hex');

function runHook(hook, { input = '', env = {}, nodeArgs = [] } = {}) {
  return spawnSync(process.execPath, [...nodeArgs, path.join(root, 'hooks', hook)], {
    cwd: root,
    encoding: 'utf8',
    env: { ...process.env, ...env },
    input,
    stdio: ['pipe', 'pipe', 'pipe'],
  });
}

async function temporaryState(run) {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'ponytail-hook-'));
  try {
    return await run(directory);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}

async function filesUnder(directory, prefix = '') {
  const entries = await readdir(directory, { withFileTypes: true });
  const paths = await Promise.all(entries.map(async (entry) => {
    const relative = path.join(prefix, entry.name);
    return entry.isDirectory() ? filesUnder(path.join(directory, entry.name), relative) : [relative];
  }));
  return paths.flat();
}

test('OpenCode mode stays session-scoped and defaults full', async () => {
  const pluginPath = pathToFileURL(path.join(root, '.opencode/plugins/ponytail.mjs')).href;
  const plugin = (await import(pluginPath)).default;
  const hooks = await plugin();
  const system = async (sessionID) => {
    const output = { system: [] };
    await hooks['experimental.chat.system.transform']({ sessionID }, output);
    return output.system.join('\n');
  };

  assert.match(await system('one'), /level: full/);
  await hooks['command.execute.before']({ command: 'ponytail', arguments: 'ultra', sessionID: 'one' });
  assert.match(await system('one'), /level: ultra/);
  assert.match(await system('two'), /level: full/);

  await hooks['command.execute.before']({ command: 'ponytail', arguments: 'off', sessionID: 'one' });
  assert.equal(await system('one'), '');
  await hooks['command.execute.before']({ command: 'ponytail', arguments: 'ultra' });
  assert.match(await system(undefined), /level: full/);

  const source = await read('.opencode/plugins/ponytail.mjs');
  assert.doesNotMatch(source, /XDG_CONFIG_HOME|homedir|writeFileSync|mkdirSync|\.ponytail-active/);
});

test('hook commands surface Node and hook failures', async () => {
  const hooks = JSON.parse(await read('hooks/claude-codex-hooks.json'));
  for (const event of Object.values(hooks.hooks).flat()) {
    const hook = event.hooks[0];
    assert.doesNotMatch(hook.command, /;\s*exit\s+0/);
    assert.doesNotMatch(hook.commandWindows, /Get-Command/);
    assert.match(hook.command, /^node "/);
    assert.match(hook.commandWindows, /^node "/);
  }
});

test('normal activation emits full Ponytail rules and exits zero', async () => {
  await temporaryState(async (directory) => {
    const activation = runHook('ponytail-activate.js', {
      env: { PLUGIN_DATA: directory, PONYTAIL_DEFAULT_MODE: 'full' },
    });
    assert.equal(activation.status, 0);
    assert.equal(activation.stderr, '');
    const output = JSON.parse(activation.stdout);
    assert.equal(output.systemMessage, 'PONYTAIL:FULL');
    assert.match(output.hookSpecificOutput.additionalContext, /PONYTAIL MODE ACTIVE — level: full/);
    assert.match(output.hookSpecificOutput.additionalContext, /# Ponytail/);
    assert.equal(await readFile(path.join(directory, '.ponytail-active'), 'utf8'), 'full');
  });
});

test('hooks fail closed for malformed input and state access failures', async () => {
  const malformed = runHook('ponytail-mode-tracker.js', { input: '{' });
  assert.equal(malformed.status, 1);
  assert.match(malformed.stderr, /^ponytail mode tracker failed:/);

  await temporaryState(async (directory) => {
    const stateFile = path.join(directory, 'not-a-directory');
    await writeFile(stateFile, 'x');
    const env = { PLUGIN_DATA: stateFile, PONYTAIL_DEFAULT_MODE: 'full' };

    const activation = runHook('ponytail-activate.js', { env });
    assert.equal(activation.status, 1);
    assert.match(activation.stderr, /^ponytail activation failed:/);

    const tracker = runHook('ponytail-mode-tracker.js', {
      env,
      input: JSON.stringify({ prompt: '/ponytail ultra' }),
    });
    assert.equal(tracker.status, 1);
    assert.match(tracker.stderr, /^ponytail mode tracker failed:/);

    const subagent = runHook('ponytail-subagent.js', { env });
    assert.equal(subagent.status, 1);
    assert.match(subagent.stderr, /^ponytail subagent injection:/);
  });
});

test('activation and subagent injection fail closed when output fails', async () => {
  await temporaryState(async (directory) => {
    const preload = path.join(directory, 'stdout-failure.cjs');
    await writeFile(preload, 'process.stdout.write = () => { throw new Error("forced output failure"); };');
    const env = { PLUGIN_DATA: directory, PONYTAIL_DEFAULT_MODE: 'full' };
    const nodeArgs = ['--require', preload];

    const activation = runHook('ponytail-activate.js', { env, nodeArgs });
    assert.equal(activation.status, 1);
    assert.match(activation.stderr, /^ponytail activation failed: forced output failure/);

    await writeFile(path.join(directory, '.ponytail-active'), 'full');
    const subagent = runHook('ponytail-subagent.js', { env, nodeArgs });
    assert.equal(subagent.status, 1);
    assert.match(subagent.stderr, /^ponytail subagent injection: forced output failure/);
  });
});

test('help truthfully lists six local skills and commands', async () => {
  const help = await read('skills/ponytail-help/SKILL.md');
  const command = await read('.opencode/command/ponytail-help.md');
  const names = ['ponytail', 'ponytail-review', 'ponytail-audit', 'ponytail-debt', 'ponytail-gain', 'ponytail-help'];
  for (const name of names) {
    assert.match(help, new RegExp(`\\*\\*${name}\\*\\*`));
    assert.match(command, new RegExp(`/${name}`));
  }
  for (const content of [help, command]) {
    assert.doesNotMatch(content, /marketplace|auto-update|npm install|brew upgrade|https?:\/\//i);
  }
});

test('LOCK.json payload is externally pinned and internally complete', async () => {
  const lockText = await read('LOCK.json');
  const lock = JSON.parse(lockText);
  const fixturePath = new URL('../../../tests/fixtures/vendors/ponytail.json', import.meta.url);
  const fixture = JSON.parse(await readFile(fixturePath, 'utf8'));

  assert.equal(sha256(lockText), fixture.lockSha256);
  assert.equal(lock.source.commit, fixture.source.commit);
  assert.equal(lock.source.tree, fixture.source.tree);
  assert.equal(lock.testReceipt.status, 'network-denied pass');
  const payloadFiles = (await filesUnder(root)).filter((file) => file !== 'LOCK.json').sort();
  assert.deepEqual(Object.keys(lock.files).sort(), payloadFiles);
  for (const [relative, expected] of Object.entries(lock.files)) {
    assert.equal(sha256(await read(relative)), expected, relative);
  }
});
