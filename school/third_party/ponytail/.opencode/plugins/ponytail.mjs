// ponytail — OpenCode plugin.
//
// Injects the Ponytail ruleset into every chat system prompt and registers
// slash commands. OpenCode mode stays in this plugin instance only: every new
// session starts full and no user-global state file is read or written.

import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// The shared instruction builder is CommonJS; bridge to it from this ES module.
const require = createRequire(import.meta.url);
const { getPonytailInstructions } = require('../../hooks/ponytail-instructions');

const DEFAULT_MODE = 'full';
const MODES = new Set(['off', 'lite', 'full', 'ultra']);

export function sessionKey(input) {
  const key = input?.sessionID || input?.sessionId || input?.session?.id;
  return typeof key === 'string' && key ? key : null;
}

function commandMode(argumentsText) {
  const mode = String(argumentsText || '').trim().toLowerCase() || DEFAULT_MODE;
  return MODES.has(mode) ? mode : DEFAULT_MODE;
}

export function parseCommandFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  // Tolerate CRLF: a Windows checkout (autocrlf) delivers \r\n, npm ships \n.
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  if (!match) return null;
  const description = match[1].match(/description:\s*(.+)/)?.[1]?.trim();
  return { description, template: match[2].trim() };
}

export default async ({ client } = {}) => {
  const log = (level, message) => {
    try { client && client.app && client.app.log({ body: { service: 'ponytail', level, message } }); } catch (e) {}
  };

  const ponytailSkillsDir = path.resolve(__dirname, '../../skills');
  const modesBySession = new Map();

  const modeFor = (input) => {
    const key = sessionKey(input);
    return (key && modesBySession.get(key)) || DEFAULT_MODE;
  };

  return {
    // Register slash commands + skills directory.
    config: async (config) => {
      if (!config.command) config.command = {};
      const commandDir = path.join(__dirname, '..', 'command');
      try {
        for (const file of fs.readdirSync(commandDir).filter((f) => f.endsWith('.md'))) {
          const name = path.basename(file, '.md');
          const parsed = parseCommandFile(path.join(commandDir, file));
          if (parsed) config.command[name] = parsed;
        }
      } catch (e) {}

      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];
      if (!config.skills.paths.includes(ponytailSkillsDir)) {
        config.skills.paths.push(ponytailSkillsDir);
      }
    },

    // Append the ruleset to the system prompt every turn.
    'experimental.chat.system.transform': async (input, output) => {
      const mode = modeFor(input);
      if (mode === 'off') return;
      output.system.push(getPonytailInstructions(mode));
    },

    // `/ponytail <level>` applies only to this OpenCode session. Missing session
    // identity intentionally falls back to full rather than risking cross-chat state.
    'command.execute.before': async (input) => {
      if (!input || input.command !== 'ponytail') return;
      const key = sessionKey(input);
      if (!key) return;
      const mode = commandMode(input.arguments);
      modesBySession.set(key, mode);
      log('info', 'ponytail ' + mode);
    },
  };
};
