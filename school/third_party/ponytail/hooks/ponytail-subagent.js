#!/usr/bin/env node
// ponytail — Claude Code SubagentStart hook
//
// SessionStart context is parent-thread only and never reaches subagents, so
// without this every Task-spawned agent runs ponytail-unaware (issue #252).
// When ponytail mode is active, inject the same ruleset into each subagent.

const { getPonytailInstructions } = require('./ponytail-instructions');
const { readMode, writeHookOutput } = require('./ponytail-runtime');

let failed = false;

function fail(stage, error) {
  if (failed) return;
  failed = true;
  const reason = error instanceof Error ? error.message : String(error);
  process.stderr.write(`ponytail subagent ${stage}: ${reason}\n`);
  process.exitCode = 1;
}

try {
  process.stdout.once('error', (error) => fail('output', error));
  const mode = readMode();
  // Absent flag or off → contract-defined no-op.
  if (mode && mode !== 'off') {
    writeHookOutput('SubagentStart', mode, getPonytailInstructions(mode));
  }
} catch (error) {
  fail('injection', error);
}
