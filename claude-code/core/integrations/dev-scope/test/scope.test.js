import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { createScope, __test__, PublicError, validateRelative } from '../lib/scope.js';

async function fixture(overrides = {}) {
  const base = await fs.mkdtemp(path.join(os.tmpdir(), 'dev-scope-'));
  const project = path.join(base, 'project');
  await fs.mkdir(path.join(project, 'src'), { recursive: true });
  await fs.writeFile(path.join(project, 'README.md'), 'hello world\napi_key = keep-me-secret\n');
  await fs.writeFile(path.join(project, 'src', 'code.js'), 'const needle = "found";\n');
  await fs.writeFile(path.join(project, '.env'), 'TOKEN=do-not-show\n');
  const config = {
    roots: [{ id: 'project', label: 'Project', path: 'project', locations: ['README.md', 'src'], extensions: ['.md', '.js'] }],
    limits: { maxDepth: 2, maxFiles: 10, maxFileBytes: 1024, maxTotalBytes: 2048, maxMatches: 5, maxOutputBytes: 1024, maxSearchMilliseconds: 1000 },
    ...overrides
  };
  await fs.writeFile(path.join(base, 'config.json'), JSON.stringify(config));
  return { base, project, scope: await createScope(path.join(base, 'config.json')) };
}

async function denied(action, code) {
  await assert.rejects(action, (error) => error instanceof PublicError && error.code === code);
}

test('requires exact root IDs, safe relative paths, and approved text types', async (t) => {
  const { base, project, scope } = await fixture();
  t.after(() => fs.rm(base, { recursive: true, force: true }));
  await denied(() => scope.readFile('pro', 'README.md'), 'UNKNOWN_ROOT');
  await denied(() => scope.readFile('project', '../README.md'), 'INVALID_PATH');
  await denied(() => scope.readFile('project', '/etc/passwd'), 'INVALID_PATH');
  await fs.writeFile(path.join(project, 'src', 'binary.js'), Buffer.from([0x00, 0x01]));
  await fs.writeFile(path.join(project, 'src', 'other.txt'), 'not allowlisted');
  await denied(() => scope.readFile('project', 'src/binary.js'), 'FILE_DENIED');
  await denied(() => scope.readFile('project', 'src/other.txt'), 'FILE_DENIED');
  assert.throws(() => validateRelative('src//code.js'), /INVALID_PATH/);
});

test('rejects ambiguous root IDs and secret-named allowlist locations', async (t) => {
  const { base } = await fixture();
  t.after(() => fs.rm(base, { recursive: true, force: true }));
  const configPath = path.join(base, 'config.json');
  const config = JSON.parse(await fs.readFile(configPath, 'utf8'));
  config.roots.push({ ...config.roots[0] });
  await fs.writeFile(configPath, JSON.stringify(config));
  await denied(() => createScope(configPath), 'INVALID_CONFIG');
  config.roots = [{ ...config.roots[0], id: 'project', locations: ['.env'] }];
  await fs.writeFile(configPath, JSON.stringify(config));
  await denied(() => createScope(configPath), 'INVALID_CONFIG');
});

test('blocks secret stores and redacts detected values', async (t) => {
  const { base, scope } = await fixture();
  t.after(() => fs.rm(base, { recursive: true, force: true }));
  await denied(() => scope.readFile('project', '.env'), 'LOCATION_DENIED');
  const read = await scope.readFile('project', 'README.md');
  assert.match(read, /api_key = \[REDACTED\]/i);
  assert.doesNotMatch(read, /keep-me-secret/);
  assert.doesNotMatch(await scope.search('project', 'TOKEN'), /do-not-show/);
});

test('redacts complete quoted, header, cookie, and multiline secret values', async (t) => {
  const source = [
    '"api_key": "json-secret-value",',
    "'token': 'yaml-secret-value'",
    'client_secret: |-',
    '  multiline-secret-one',
    '  multiline-secret-two',
    'export SENSITIVE=export-secret-value',
    'export API_KEY="export-api-secret-value"',
    'export const SENSITIVE = "export-const-secret-value"',
    'export let API_KEY = "export-let-secret-value"',
    'export var token = "export-var-secret-value"',
    'Authorization: Bearer bearer-secret-value',
    'Authorization: Token token-secret-value',
    'Authorization: Basic basic-secret-value',
    'Authorization: Digest digest-secret-value',
    'X-Api-Key: header-secret-value',
    '"X-Auth-Token": "quoted-header-secret-value"',
    "'Proxy-Authorization': 'quoted-proxy-secret-value'",
    'Cookie: session=cookie-secret-value; other=still-secret',
    'const payload = { apiKey: "embedded-js-secret", safe: "keep-js-safe" };',
    '{ "x_api_key": "embedded-json-secret", "safe": "keep-json-safe" }',
    'metadata: { token: "embedded-yaml-secret", title: "keep-yaml-safe" }',
    'headers.set("Authorization", "Bearer setter-auth-secret");',
    "xhr.setRequestHeader('X-Api-Key', 'setter-api-secret');",
    'request.headers.append("Cookie", "session=setter-cookie-secret");',
    'client.setHeader("X-Auth-Token", setterTokenSecret);',
    'headers?.set("Authorization", "Bearer " + optionalSetterSecret);',
    'headers["set"]("X-Api-Key", `key ${bracketSetterSecret}`);',
    'xhr?.setRequestHeader("Authorization", "Basic " + basicSetterSecret);',
    'headers.set("Accept", "application/json");'
  ].join('\n');
  const { base, project, scope } = await fixture({ limits: { maxFileBytes: 4096 } });
  t.after(() => fs.rm(base, { recursive: true, force: true }));
  await fs.writeFile(path.join(project, 'README.md'), source);
  const redacted = await scope.readFile('project', 'README.md');
  for (const leaked of ['json-secret-value', 'yaml-secret-value', 'multiline-secret-one', 'multiline-secret-two', 'export-secret-value', 'export-api-secret-value', 'export-const-secret-value', 'export-let-secret-value', 'export-var-secret-value', 'bearer-secret-value', 'token-secret-value', 'basic-secret-value', 'digest-secret-value', 'header-secret-value', 'quoted-header-secret-value', 'quoted-proxy-secret-value', 'cookie-secret-value', 'still-secret', 'embedded-js-secret', 'embedded-json-secret', 'embedded-yaml-secret', 'setter-auth-secret', 'setter-api-secret', 'setter-cookie-secret', 'setterTokenSecret', 'optionalSetterSecret', 'bracketSetterSecret', 'basicSetterSecret']) {
    assert.doesNotMatch(redacted, new RegExp(leaked));
  }
  assert.match(redacted, /"api_key": \[REDACTED\]/);
  assert.match(redacted, /Authorization: \[REDACTED\]/);
  assert.match(redacted, /export SENSITIVE=\[REDACTED\]/);
  assert.match(redacted, /export const SENSITIVE = \[REDACTED\]/);
  assert.match(redacted, /X-Api-Key: \[REDACTED\]/);
  assert.match(redacted, /headers\.set\("Authorization",\[REDACTED\]/);
  assert.match(redacted, /setRequestHeader\('X-Api-Key',\[REDACTED\]/);
  assert.match(redacted, /request\.headers\.append\("Cookie",\[REDACTED\]/);
  assert.match(redacted, /headers\?\.set\("Authorization",\[REDACTED\]/);
  assert.match(redacted, /headers\["set"\]\("X-Api-Key",\[REDACTED\]/);
  assert.match(redacted, /xhr\?\.setRequestHeader\("Authorization",\[REDACTED\]/);
  assert.match(redacted, /keep-js-safe/);
  assert.match(redacted, /keep-json-safe/);
  assert.match(redacted, /keep-yaml-safe/);
  assert.match(redacted, /\[REDACTED\]/);
});

test('does not follow symlink escapes or swapped final files', async (t) => {
  const { base, project, scope } = await fixture();
  t.after(() => fs.rm(base, { recursive: true, force: true }));
  await fs.symlink('/etc', path.join(project, 'src', 'escape'));
  await denied(() => scope.listDirectory('project', 'src/escape'), 'SYMLINK_DENIED');
  const target = path.join(project, 'src', 'code.js');
  await fs.rm(target);
  await fs.symlink('/etc/passwd', target);
  await denied(() => scope.readFile('project', 'src/code.js'), 'SYMLINK_DENIED');
});

test('rejects hard-linked files before read and search', async (t) => {
  const { base, project, scope } = await fixture();
  t.after(() => fs.rm(base, { recursive: true, force: true }));
  const outside = path.join(base, 'outside.js');
  const linked = path.join(project, 'src', 'linked.js');
  await fs.writeFile(outside, 'const hardLinkSecret = "do-not-leak";\n');
  await fs.link(outside, linked);
  await denied(() => scope.readFile('project', 'src/linked.js'), 'HARDLINK_DENIED');
  assert.doesNotMatch(await scope.search('project', 'hardLinkSecret'), /do-not-leak/);
});

test('enforces file and output bounds during literal search', async (t) => {
  const { base, project } = await fixture({ limits: { maxDepth: 2, maxFiles: 1, maxFileBytes: 1024, maxTotalBytes: 1024, maxMatches: 1, maxOutputBytes: 60, maxSearchMilliseconds: 1000 } });
  t.after(() => fs.rm(base, { recursive: true, force: true }));
  await fs.writeFile(path.join(project, 'src', 'more.js'), 'found\nfound\n');
  const scope = await createScope(path.join(base, 'config.json'));
  const result = await scope.search('project', 'found');
  assert.ok(Buffer.byteLength(result) <= 60);
  assert.match(result, /\[search limit reached\]$/);
  await fs.writeFile(path.join(project, 'src', 'code.js'), 'x'.repeat(200));
  const read = await scope.readFile('project', 'src/code.js');
  assert.ok(Buffer.byteLength(read) <= 60);
  assert.match(read, /\[truncated\]$/);
  const unicode = __test__.outputWithinLimit('😀'.repeat(20), 11);
  assert.equal(unicode, '[truncated]');
  assert.ok(Buffer.byteLength(unicode) <= 11);
});

test('labels depth and total-byte budget pruning as partial', async (t) => {
  const { base, project } = await fixture({
    roots: [{ id: 'project', label: 'Project', path: 'project', locations: ['src'], extensions: ['.js'] }],
    limits: { maxDepth: 1, maxFiles: 10, maxFileBytes: 1024, maxTotalBytes: 40, maxMatches: 10, maxOutputBytes: 200, maxSearchMilliseconds: 1000 }
  });
  t.after(() => fs.rm(base, { recursive: true, force: true }));
  await fs.mkdir(path.join(project, 'src', 'nested', 'deeper'), { recursive: true });
  await fs.writeFile(path.join(project, 'src', 'nested', 'deeper', 'deep.js'), 'const deepBudgetNeedle = true;\n');
  await fs.writeFile(path.join(project, 'src', 'later.js'), 'const byteBudgetNeedle = "this file exceeds the remaining byte budget";\n');
  const scope = await createScope(path.join(base, 'config.json'));
  const depthResult = await scope.search('project', 'deepBudgetNeedle');
  assert.match(depthResult, /\[search limit reached\]$/);
  const byteResult = await scope.search('project', 'byteBudgetNeedle');
  assert.match(byteResult, /\[search limit reached\]$/);
  assert.ok(Buffer.byteLength(byteResult) <= 200);
});

test('labels partial matched search results before enforcing output cap', async (t) => {
  const { base, scope } = await fixture({
    roots: [{ id: 'project', label: 'Project', path: 'project', locations: ['src'], extensions: ['.js'] }],
    limits: { maxDepth: 2, maxFiles: 10, maxFileBytes: 1024, maxTotalBytes: 2048, maxMatches: 1, maxOutputBytes: 200, maxSearchMilliseconds: 1000 }
  });
  t.after(() => fs.rm(base, { recursive: true, force: true }));
  const result = await scope.search('project', 'found');
  assert.match(result, /project:src\/code\.js:1:/);
  assert.match(result, /\[search limit reached\]$/);
  assert.ok(Buffer.byteLength(result) <= 200);
});

test('preserves search-limit label when matched output also truncates', async (t) => {
  const { base, scope } = await fixture({
    roots: [{ id: 'project', label: 'Project', path: 'project', locations: ['src'], extensions: ['.js'] }],
    limits: { maxDepth: 2, maxFiles: 10, maxFileBytes: 1024, maxTotalBytes: 2048, maxMatches: 1, maxOutputBytes: 60, maxSearchMilliseconds: 1000 }
  });
  t.after(() => fs.rm(base, { recursive: true, force: true }));
  const result = await scope.search('project', 'found');
  assert.match(result, /\[truncated; search limit reached\]$/);
  assert.ok(Buffer.byteLength(result) <= 60);
});

test('fails closed when deterministic root replacement is detected', async (t) => {
  const { base, project, scope } = await fixture();
  t.after(() => fs.rm(base, { recursive: true, force: true }));
  await fs.rename(project, `${project}-moved`);
  await fs.mkdir(path.join(project, 'src'), { recursive: true });
  await denied(() => scope.listDirectory('project', 'src'), 'ROOT_UNAVAILABLE');
});

test('git execution disables malicious fsmonitor and has fixed sanitized environment', () => {
  const environment = __test__.safeGitEnvironment();
  assert.equal(environment.GIT_CONFIG_GLOBAL, '/dev/null');
  assert.equal(environment.GIT_CONFIG_COUNT, '0');
  assert.equal(environment.GIT_TERMINAL_PROMPT, '0');
  assert.equal(environment.GIT_EXTERNAL_DIFF, '');
  assert.equal(environment.PATH, '/usr/bin:/bin');
  assert.equal('HOME' in environment, true);
  const args = __test__.gitArguments({ canonical: '/trusted/project' }, ['status', '--short']);
  assert.deepEqual(args.slice(0, 10), ['-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', '-c', 'core.pager=cat', '-c', 'diff.external=', '-c', 'diff.trustExitCode=false']);
  assert.ok(args.includes('--no-pager'));
});

test('exposes Git metadata', async (t) => {
  const { base, scope } = await fixture();
  t.after(() => fs.rm(base, { recursive: true, force: true }));
  assert.equal(typeof scope.gitStatus, 'function');
});
