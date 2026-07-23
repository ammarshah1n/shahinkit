#!/usr/bin/env node
// ponytail — Claude Code SessionStart activation hook
//
// Runs on every session start: writes its host-scoped mode flag and emits
// Ponytail rules as hidden SessionStart context.

const { getDefaultMode } = require('./ponytail-config');
const { getPonytailInstructions } = require('./ponytail-instructions');
const {
  clearMode,
  isCodex,
  isCopilot,
  setMode,
  writeHookOutput,
} = require('./ponytail-runtime');

let failed = false;

function fail(stage, error) {
  if (failed) return;
  failed = true;
  const reason = error instanceof Error ? error.message : String(error);
  process.stderr.write(`ponytail activation ${stage}: ${reason}\n`);
  process.exitCode = 1;
}

try {
  process.stdout.once('error', (error) => fail('output', error));
  const mode = getDefaultMode();

  // "off" is a contract-defined no-op after clearing host state.
  if (mode === 'off') {
    clearMode();
    const hookOutput = (isCodex || isCopilot) ? '' : 'OK';
    writeHookOutput('SessionStart', 'off', hookOutput);
  } else {
    setMode(mode);
    writeHookOutput('SessionStart', mode, getPonytailInstructions(mode));
  }
} catch (error) {
  fail('failed', error);
}
