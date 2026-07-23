import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';

const execFileAsync = promisify(execFile);
const DEFAULT_LIMITS = Object.freeze({
  maxDepth: 4,
  maxFiles: 100,
  maxFileBytes: 131072,
  maxTotalBytes: 1048576,
  maxMatches: 50,
  maxOutputBytes: 32768,
  maxSearchMilliseconds: 2000
});
const SECRET_FILE = /(^|\/)(\.env(?:\..*)?|[^/]*(?:secret|credential|password|private[_-]?key)[^/]*)$/i;
const SKIPPED_NAMES = new Set(['.git', 'node_modules']);
const TRUNCATION_MARKER = '[truncated]';
const SEARCH_LIMIT_MARKER = '[search limit reached]';
const SEARCH_TRUNCATION_MARKER = '[truncated; search limit reached]';
const SENSITIVE_KEY = '(?:api[_-]?key|secret|token|password|authorization|cookie|client[_-]?secret|access[_-]?token|refresh[_-]?token|sensitive|proxy[-_]?authorization|x[-_]?api[-_]?key|x[-_]?auth[-_]?token|x[-_]?access[-_]?token|x[-_]?csrf[-_]?token|x[-_]?client[-_]?secret)';
const SENSITIVE_PREFIX = `(?:export[\\t ]+(?:(?:const|let|var)[\\t ]+)?)?(?:(?:"|')?${SENSITIVE_KEY}(?:"|')?)`;
const BLOCK_ASSIGNMENT = new RegExp(`(^[\\t ]*${SENSITIVE_PREFIX}[\\t ]*:[\\t ]*[|>][+-]?[^\\r\\n]*)(?:\\r?\\n[\\t ]+[^\\r\\n]*)*`, 'gim');
const ASSIGNMENT = new RegExp(`(^[\\t ]*${SENSITIVE_PREFIX}[\\t ]*[:=][\\t ]*)(?:"(?:\\\\[\\s\\S]|[^"\\\\])*"|'(?:\\\\[\\s\\S]|[^'\\\\])*'|[^\\r\\n,}\\]]*)`, 'gim');
const EMBEDDED_ASSIGNMENT = new RegExp(`((?:[,{;.][\\t ]*|\\bexport[\\t ]+(?:(?:const|let|var)[\\t ]+)?)${SENSITIVE_PREFIX}[\\t ]*[:=][\\t ]*)(?:"(?:\\\\[\\s\\S]|[^"\\\\])*"|'(?:\\\\[\\s\\S]|[^'\\\\])*'|[^\\r\\n,}\\]]*)`, 'gim');
const HEADER_METHOD = '(?:set|append|setHeader|setRequestHeader)';
const HEADER_RECEIVER = '\\b[A-Za-z_$][\\w$]*(?:\\??\\.[A-Za-z_$][\\w$]*|\\??\\.\\[(?:"[^"]*"|\'[^\']*\')\\])*';
const HEADER_SETTER = new RegExp(`((?:(?:${HEADER_RECEIVER})(?:\\?\\.|\\.)${HEADER_METHOD}|(?:${HEADER_RECEIVER})(?:\\?\\.)?\\[(?:"${HEADER_METHOD}"|'${HEADER_METHOD}')\\]|${HEADER_METHOD})[\\t ]*\\([\\t ]*(?:(?:"|')?${SENSITIVE_KEY}(?:"|')?)[\\t ]*,)[^\\r\\n]*`, 'gim');
const SECRET_TOKEN = /(?:sk|rk|pk)_[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[\w-]{20,}|AKIA[0-9A-Z]{16}/gi;
const PRIVATE_KEY = /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g;
const AUTHORIZATION = /(^[\t ]*authorization[\t ]*:[\t ]*)(?:bearer|token)[\t ]+[^\r\n]+/gim;
const COOKIE = /^[\t ]*(?:cookie|set-cookie)[\t ]*:[\t ]*[^\r\n]+/gim;

export class PublicError extends Error {
  constructor(code) {
    super(code);
    this.code = code;
  }
}

function fail(code) {
  throw new PublicError(code);
}

function sameIdentity(left, right) {
  return left.dev === right.dev && left.ino === right.ino;
}

function isContained(root, candidate) {
  const relative = path.relative(root, candidate);
  return relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative));
}

export function validateRelative(value) {
  if (typeof value !== 'string' || value.length === 0 || value.length > 512 || value.includes('\0') || value.includes('\\') || path.isAbsolute(value)) fail('INVALID_PATH');
  const parts = value.split('/');
  if (parts.some((part) => part.length === 0 || part === '.' || part === '..')) fail('INVALID_PATH');
  return parts.join(path.sep);
}

function validateId(value) {
  if (typeof value !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/.test(value)) fail('UNKNOWN_ROOT');
  return value;
}

function allowedLocation(relative, locations) {
  return locations.some((location) => relative === location || relative.startsWith(`${location}${path.sep}`));
}

function allowedExtension(relative, extensions) {
  return extensions.includes(path.extname(relative).toLowerCase());
}

function redact(text) {
  return text
    .replace(PRIVATE_KEY, '[REDACTED]')
    .replace(BLOCK_ASSIGNMENT, '$1\n[REDACTED]')
    .replace(ASSIGNMENT, '$1[REDACTED]')
    .replace(EMBEDDED_ASSIGNMENT, '$1[REDACTED]')
    .replace(HEADER_SETTER, '$1[REDACTED]')
    .replace(AUTHORIZATION, '$1[REDACTED]')
    .replace(COOKIE, '[REDACTED]')
    .replace(SECRET_TOKEN, '[REDACTED]');
}

function utf8Prefix(text, limit) {
  let bytes = 0;
  let output = '';
  for (const character of text) {
    const characterBytes = Buffer.byteLength(character, 'utf8');
    if (bytes + characterBytes > limit) break;
    output += character;
    bytes += characterBytes;
  }
  return output;
}

function outputWithinLimit(text, limit, marker = TRUNCATION_MARKER) {
  const bytes = Buffer.byteLength(text, 'utf8');
  if (bytes <= limit) return text;
  const prefix = utf8Prefix(text, limit - Buffer.byteLength(marker, 'utf8'));
  return `${prefix}${marker}`;
}

function checkedLimits(limits = {}) {
  const result = { ...DEFAULT_LIMITS };
  for (const [key, defaultValue] of Object.entries(DEFAULT_LIMITS)) {
    if (limits[key] === undefined) continue;
    const minimum = key === 'maxOutputBytes' ? Buffer.byteLength(SEARCH_TRUNCATION_MARKER, 'utf8') : 1;
    if (!Number.isInteger(limits[key]) || limits[key] < minimum || limits[key] > defaultValue) fail('INVALID_CONFIG');
    result[key] = limits[key];
  }
  return result;
}

async function canonicalRoot(configDirectory, root) {
  if (!root || typeof root !== 'object' || !/^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/.test(root.id) || typeof root.path !== 'string' || path.isAbsolute(root.path)) fail('INVALID_CONFIG');
  const relativeRoot = validateRelative(root.path);
  const configured = path.resolve(configDirectory, relativeRoot);
  let canonical;
  let stat;
  try {
    canonical = await fsp.realpath(configured);
    stat = await fsp.lstat(canonical);
  } catch {
    fail('INVALID_CONFIG');
  }
  if (!stat.isDirectory() || stat.isSymbolicLink()) fail('INVALID_CONFIG');
  if (!Array.isArray(root.locations) || root.locations.length === 0 || !Array.isArray(root.extensions) || root.extensions.length === 0) fail('INVALID_CONFIG');
  const locations = root.locations.map(validateRelative);
  if (locations.some((location) => SECRET_FILE.test(location))) fail('INVALID_CONFIG');
  const extensions = root.extensions.map((extension) => {
    if (typeof extension !== 'string' || !/^\.[A-Za-z0-9]+$/.test(extension)) fail('INVALID_CONFIG');
    return extension.toLowerCase();
  });
  return { id: root.id, label: typeof root.label === 'string' ? root.label.slice(0, 80) : root.id, canonical, identity: stat, locations, extensions };
}

async function loadConfig(configPath) {
  const filename = configPath instanceof URL ? configPath : path.resolve(String(configPath));
  let parsed;
  try {
    parsed = JSON.parse(await fsp.readFile(filename, 'utf8'));
  } catch {
    fail('INVALID_CONFIG');
  }
  if (!parsed || !Array.isArray(parsed.roots) || parsed.roots.length === 0 || parsed.roots.length > 20) fail('INVALID_CONFIG');
  const configDirectory = path.dirname(filename instanceof URL ? fileURLToPath(filename) : filename);
  const roots = await Promise.all(parsed.roots.map((root) => canonicalRoot(configDirectory, root)));
  if (new Set(roots.map((root) => root.id)).size !== roots.length) fail('INVALID_CONFIG');
  return { roots, limits: checkedLimits(parsed.limits) };
}

async function ensureRoot(root) {
  let before;
  let resolved;
  let after;
  try {
    before = await fsp.lstat(root.canonical);
    resolved = await fsp.realpath(root.canonical);
    after = await fsp.lstat(root.canonical);
  } catch {
    fail('ROOT_UNAVAILABLE');
  }
  if (!before.isDirectory() || before.isSymbolicLink() || resolved !== root.canonical || !sameIdentity(before, after) || !sameIdentity(before, root.identity)) fail('ROOT_UNAVAILABLE');
}

async function stablePath(root, candidate, expected) {
  await ensureRoot(root);
  let before;
  let resolved;
  let after;
  try {
    before = await fsp.lstat(candidate);
    resolved = await fsp.realpath(candidate);
    after = await fsp.lstat(candidate);
  } catch {
    fail('NOT_FOUND');
  }
  if (before.isSymbolicLink()) fail('SYMLINK_DENIED');
  if (!sameIdentity(before, after) || (expected && !sameIdentity(before, expected))) fail('PATH_CHANGED');
  if (!isContained(root.canonical, resolved)) fail('PATH_DENIED');
  return before;
}

async function checkedPath(root, relative, { directory = false, file = false } = {}) {
  const normalized = validateRelative(relative);
  if (!allowedLocation(normalized, root.locations)) fail('LOCATION_DENIED');
  if (SECRET_FILE.test(normalized)) fail('FILE_DENIED');
  await ensureRoot(root);
  const candidate = path.resolve(root.canonical, normalized);
  if (!isContained(root.canonical, candidate)) fail('INVALID_PATH');
  let current = root.canonical;
  const parts = normalized.split(path.sep);
  for (let index = 0; index < parts.length; index += 1) {
    current = path.join(current, parts[index]);
    const stat = await stablePath(root, current);
    if (index < parts.length - 1 && !stat.isDirectory()) fail('NOT_FOUND');
  }
  const finalStat = await stablePath(root, candidate);
  if ((directory && !finalStat.isDirectory()) || (file && !finalStat.isFile())) fail('TYPE_DENIED');
  return { candidate, stat: finalStat, relative: normalized };
}

async function openVerifiedFile(root, relative, maxBytes) {
  const checked = await checkedPath(root, relative, { file: true });
  if (!allowedExtension(checked.relative, root.extensions)) fail('FILE_DENIED');
  if (checked.stat.nlink > 1) fail('HARDLINK_DENIED');
  if (checked.stat.size > maxBytes) fail('FILE_TOO_LARGE');
  const noFollow = fs.constants.O_NOFOLLOW ?? 0;
  let handle;
  try {
    handle = await fsp.open(checked.candidate, fs.constants.O_RDONLY | noFollow);
    const opened = await handle.stat();
    const after = await stablePath(root, checked.candidate, checked.stat);
    if (!sameIdentity(checked.stat, opened) || !sameIdentity(opened, after)) fail('PATH_CHANGED');
    if (opened.nlink > 1) fail('HARDLINK_DENIED');
    if (opened.size > maxBytes) fail('FILE_TOO_LARGE');
    const buffer = Buffer.alloc(Number(opened.size) + 1);
    const { bytesRead } = await handle.read(buffer, 0, buffer.length, 0);
    if (bytesRead > maxBytes || buffer.subarray(0, bytesRead).includes(0)) fail('FILE_DENIED');
    const finalStat = await stablePath(root, checked.candidate, opened);
    if (!sameIdentity(opened, finalStat)) fail('PATH_CHANGED');
    const bytes = buffer.subarray(0, bytesRead);
    return { text: redact(bytes.toString('utf8')), bytes: bytesRead, relative: checked.relative };
  } catch (error) {
    if (error instanceof PublicError) throw error;
    fail('READ_DENIED');
  } finally {
    await handle?.close();
  }
}

async function streamDirectory(root, relative, visitor) {
  const checked = await checkedPath(root, relative, { directory: true });
  let directory;
  try {
    await stablePath(root, checked.candidate, checked.stat);
    directory = await fsp.opendir(checked.candidate, { bufferSize: 32 });
    await stablePath(root, checked.candidate, checked.stat);
    for await (const entry of directory) {
      await stablePath(root, checked.candidate, checked.stat);
      if (await visitor(entry) === false) break;
    }
    await stablePath(root, checked.candidate, checked.stat);
  } catch (error) {
    if (error instanceof PublicError) throw error;
    fail('READ_DENIED');
  } finally {
    await directory?.close().catch((error) => {
      if (error?.code !== 'ERR_DIR_CLOSED') throw error;
    });
  }
}

function safeGitEnvironment() {
  return Object.freeze({
    PATH: '/usr/bin:/bin',
    LANG: 'C',
    LC_ALL: 'C',
    HOME: '/nonexistent',
    GIT_CONFIG_NOSYSTEM: '1',
    GIT_CONFIG_GLOBAL: '/dev/null',
    GIT_OPTIONAL_LOCKS: '0',
    GIT_CONFIG_COUNT: '0',
    GIT_TERMINAL_PROMPT: '0',
    GIT_PAGER: 'cat',
    GIT_EXTERNAL_DIFF: '',
    GIT_DIFF_EXTERNAL: ''
  });
}

export async function resolveTrustedGit() {
  for (const candidate of ['/usr/bin/git', '/bin/git']) {
    try {
      const resolved = await fsp.realpath(candidate);
      const stat = await fsp.stat(resolved);
      if (stat.isFile() && (stat.mode & 0o111) !== 0) return resolved;
    } catch {
      // Try next compiled-in system location.
    }
  }
  return null;
}

function gitArguments(root, args) {
  return ['-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', '-c', 'core.pager=cat', '-c', 'diff.external=', '-c', 'diff.trustExitCode=false', '--no-pager', '-C', root.canonical, ...args];
}

async function git(root, gitPath, args, outputLimit) {
  await ensureRoot(root);
  if (!gitPath) return '(unavailable)';
  const fixed = gitArguments(root, args);
  try {
    const result = await execFileAsync(gitPath, fixed, { env: safeGitEnvironment(), timeout: 3000, maxBuffer: 65536, windowsHide: true });
    return outputWithinLimit(redact(result.stdout.trim() || '(none)'), outputLimit);
  } catch {
    return '(unavailable)';
  }
}

function deadlineExceeded(deadline) {
  return Date.now() > deadline;
}

async function walk(root, relative, depth, state, onFile) {
  if (state.files >= state.limits.maxFiles || deadlineExceeded(state.deadline)) {
    state.partial = true;
    return;
  }
  await streamDirectory(root, relative, async (entry) => {
    if (state.files >= state.limits.maxFiles || deadlineExceeded(state.deadline)) {
      state.partial = true;
      return false;
    }
    const child = path.join(relative, entry.name);
    if (SKIPPED_NAMES.has(entry.name) || entry.isSymbolicLink()) return true;
    if (entry.isDirectory()) {
      if (allowedLocation(child, root.locations)) {
        if (depth < state.limits.maxDepth) await walk(root, child, depth + 1, state, onFile);
        else state.partial = true;
      }
      return true;
    }
    if (!entry.isFile() || SECRET_FILE.test(child) || !allowedExtension(child, root.extensions)) return true;
    await onFile(child);
    return true;
  });
}

export async function createScope(configPath) {
  const { roots, limits } = await loadConfig(configPath);
  const byId = new Map(roots.map((root) => [root.id, root]));
  const gitPath = await resolveTrustedGit();
  const getRoot = (id) => {
    const root = byId.get(validateId(id));
    if (!root) fail('UNKNOWN_ROOT');
    return root;
  };

  return {
    async listProjects() {
      return outputWithinLimit(roots.map((root) => `${root.id}: ${root.label}`).join('\n'), limits.maxOutputBytes);
    },
    async overview(id) {
      const root = getRoot(id);
      await ensureRoot(root);
      const locations = root.locations.map((location) => `- ${location}`).join('\n');
      const status = await git(root, gitPath, ['status', '--short', '--untracked-files=no'], limits.maxOutputBytes);
      const commits = await git(root, gitPath, ['log', '--no-decorate', '--oneline', '-n', '3'], limits.maxOutputBytes);
      return outputWithinLimit(`=== Approved Locations ===\n${locations}\n\n=== Git Status ===\n${status}\n\n=== Recent Commits ===\n${commits}`, limits.maxOutputBytes);
    },
    async readFile(id, relative) {
      const root = getRoot(id);
      const file = await openVerifiedFile(root, relative, limits.maxFileBytes);
      return outputWithinLimit(file.text, limits.maxOutputBytes);
    },
    async listDirectory(id, relative) {
      const root = getRoot(id);
      let output = '';
      let truncated = false;
      await streamDirectory(root, relative, (entry) => {
        if (SKIPPED_NAMES.has(entry.name) || SECRET_FILE.test(path.join(validateRelative(relative), entry.name))) return true;
        const line = `${entry.isDirectory() ? 'd' : 'f'} ${entry.name}`;
        const next = output.length === 0 ? line : `${output}\n${line}`;
        if (Buffer.byteLength(next, 'utf8') > limits.maxOutputBytes) {
          truncated = true;
          return false;
        }
        output = next;
        return true;
      });
      return truncated ? outputWithinLimit(`${output}${'x'.repeat(limits.maxOutputBytes)}`, limits.maxOutputBytes) : output || '(empty)';
    },
    async search(id, query) {
      if (typeof query !== 'string' || query.length === 0 || query.length > 256) fail('INVALID_QUERY');
      const selected = id === undefined ? roots : [getRoot(id)];
      const state = { files: 0, bytes: 0, matches: [], limits, deadline: Date.now() + limits.maxSearchMilliseconds, partial: false };
      for (const root of selected) {
        for (const location of root.locations) {
          if (state.files >= limits.maxFiles || state.matches.length >= limits.maxMatches || deadlineExceeded(state.deadline)) {
            state.partial = true;
            break;
          }
          let locationStat;
          try {
            locationStat = await checkedPath(root, location);
          } catch (error) {
            if (error instanceof PublicError && error.code === 'NOT_FOUND') continue;
            throw error;
          }
          if (locationStat.stat.isFile()) {
            if (allowedExtension(location, root.extensions)) await searchFile(root, location, query, state);
          } else if (locationStat.stat.isDirectory()) {
            await walk(root, location, 0, state, (child) => searchFile(root, child, query, state));
          }
        }
      }
      const limited = state.partial || deadlineExceeded(state.deadline) || state.files >= limits.maxFiles || state.bytes >= limits.maxTotalBytes || state.matches.length >= limits.maxMatches;
      const results = state.matches.join('\n') || '(no matches)';
      return outputWithinLimit(`${results}${limited ? `\n${SEARCH_LIMIT_MARKER}` : ''}`, limits.maxOutputBytes, limited ? SEARCH_TRUNCATION_MARKER : TRUNCATION_MARKER);
    },
    async gitStatus(id) {
      const root = getRoot(id);
      const status = await git(root, gitPath, ['status', '--short', '--untracked-files=no'], limits.maxOutputBytes);
      const commits = await git(root, gitPath, ['log', '--no-decorate', '--oneline', '-n', '5'], limits.maxOutputBytes);
      return outputWithinLimit(`=== Status ===\n${status}\n\n=== Recent Commits ===\n${commits}`, limits.maxOutputBytes);
    },
  };
}

async function searchFile(root, relative, query, state) {
  if (state.files >= state.limits.maxFiles || state.bytes >= state.limits.maxTotalBytes || state.matches.length >= state.limits.maxMatches || deadlineExceeded(state.deadline)) {
    state.partial = true;
    return;
  }
  let file;
  try {
    file = await openVerifiedFile(root, relative, Math.min(state.limits.maxFileBytes, state.limits.maxTotalBytes - state.bytes));
  } catch (error) {
    if (error instanceof PublicError && ['FILE_TOO_LARGE', 'HARDLINK_DENIED', 'READ_DENIED', 'NOT_FOUND', 'SYMLINK_DENIED', 'PATH_CHANGED'].includes(error.code)) {
      state.partial = true;
      return;
    }
    throw error;
  }
  state.files += 1;
  state.bytes += file.bytes;
  const needle = query.toLocaleLowerCase('en-US');
  for (const [index, line] of file.text.split(/\r?\n/).entries()) {
    if (state.matches.length >= state.limits.maxMatches || deadlineExceeded(state.deadline)) {
      state.partial = true;
      return;
    }
    if (line.toLocaleLowerCase('en-US').includes(needle)) state.matches.push(`${root.id}:${file.relative}:${index + 1}: ${line.trim()}`);
  }
}

export function toToolResult(value) {
  if (value instanceof PublicError) return { isError: true, content: [{ type: 'text', text: `Request denied: ${value.code}` }] };
  return { content: [{ type: 'text', text: String(value) }] };
}

export const __test__ = { redact, safeGitEnvironment, isContained, outputWithinLimit, gitArguments };
