import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / "claude-code" / "core" / "hooks" / "shahinkit_hook.py"


class HookParityTests(unittest.TestCase):
    def run_hook(self, payload):
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def test_canonical_hook_is_fail_open_and_event_specific(self):
        cases = {
            "SessionStart": "Prime is available; inspect visible PROJECT_STATE/NEXT/HANDOFF for meaningful work.",
            "SubagentStart": "Worker scope bounded, no controller authority, return evidence.",
        }
        for event, context in cases.items():
            output = self.run_hook(json.dumps({"hook_event_name": event}))
            specific = output["hookSpecificOutput"]
            self.assertEqual(specific["hookEventName"], event)
            self.assertIn(context, specific["additionalContext"])
        self.assertEqual(self.run_hook(json.dumps({"hook_event_name": "Stop"})), {})
        self.assertEqual(self.run_hook("{}"), {})
        self.assertEqual(self.run_hook("[]"), {})
        self.assertEqual(self.run_hook("not-json"), {})

    def test_canonical_hook_has_no_host_or_machine_side_effects(self):
        # The hook reads exactly one file: its own install-time config, resolved
        # relative to itself. It never writes, spawns, or reaches the network.
        source = HOOK.read_text()
        for forbidden in (
            "import subprocess", "from subprocess", "Popen", "system(",
            "import socket", "import urllib", "import http",
            "write_text", "open(", "os.remove", "shutil",
        ):
            self.assertNotIn(forbidden, source)
        self.assertEqual(source.count("read_text"), 3)  # hook-config.json, opt-out, explain-mode
        self.assertIn('"hook-config.json"', source)
        self.assertIn('"opt-out"', source)
        self.assertIn('"explain-mode"', source)

    def test_claude_and_codex_examples_register_only_safe_lifecycle_events(self):
        examples = (
            ROOT / "claude-code/hooks/user.hooks.example.json",
            ROOT / "claude-code/hooks/project.hooks.example.json",
            ROOT / "codex/hooks/user.hooks.example.json",
            ROOT / "codex/hooks/project.hooks.example.json",
        )
        for path in examples:
            config = json.loads(path.read_text())
            self.assertEqual(set(config), {"hooks"})
            self.assertEqual(
                set(config["hooks"]),
                {"SessionStart", "UserPromptSubmit", "SubagentStart"},
            )
            for registrations in config["hooks"].values():
                hook = registrations[0]["hooks"][0]
                self.assertEqual(hook["type"], "command")
                self.assertEqual(hook["command"], "python3 {{SHAHINKIT_HOOK_PATH}}")

    def staged_hook(self, tmp, config, opt_out=None, explain=None):
        """Reproduce an install layout: <root>/hooks/shahinkit_hook.py, the
        install-owned <root>/.shahinkit-data/hook-config.json, and the unowned
        opt-out list beside it."""
        root = Path(tmp)
        (root / "hooks").mkdir()
        staged = root / "hooks" / "shahinkit_hook.py"
        staged.write_bytes(HOOK.read_bytes())
        data = root / ".shahinkit-data"
        data.mkdir()
        (data / "hook-config.json").write_text(json.dumps(config))
        if opt_out is not None:
            (data / "opt-out").write_text("# ShahinKit path opt-out\n" + "\n".join(opt_out) + "\n")
        if explain is not None:
            (data / "explain-mode").write_text(explain + "\n")
        return staged

    def run_staged(self, staged, payload):
        result = subprocess.run(
            [sys.executable, str(staged)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def test_caveman_restates_per_prompt_only_when_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            staged = self.staged_hook(tmp, {"caveman": True})
            output = self.run_staged(staged, {"hook_event_name": "UserPromptSubmit"})
            self.assertIn("Caveman is active", output["hookSpecificOutput"]["additionalContext"])
        with tempfile.TemporaryDirectory() as tmp:
            staged = self.staged_hook(tmp, {"caveman": False})
            self.assertEqual(self.run_staged(staged, {"hook_event_name": "UserPromptSubmit"}), {})
        # No config at all: silent, never a crash.
        self.assertEqual(self.run_hook(json.dumps({"hook_event_name": "UserPromptSubmit"})), {})

    def test_explain_mode_asks_once_then_restates_plain_english(self):
        # Unset is the update path: an existing install has no explain-mode file.
        with tempfile.TemporaryDirectory() as tmp:
            staged = self.staged_hook(tmp, {"caveman": True})
            start = self.run_staged(staged, {"hook_event_name": "SessionStart"})["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Explanation level is unset", start)
            self.assertNotIn(
                "Explanation level is unset",
                self.run_staged(staged, {"hook_event_name": "SubagentStart"})["hookSpecificOutput"]["additionalContext"],
                "a headless worker cannot ask the user",
            )
        for answer in ("plain", "technical"):
            with tempfile.TemporaryDirectory() as tmp:
                staged = self.staged_hook(tmp, {"caveman": True}, explain=answer)
                start = self.run_staged(staged, {"hook_event_name": "SessionStart"})["hookSpecificOutput"]["additionalContext"]
                self.assertNotIn("Explanation level is unset", start)
                prompt = self.run_staged(staged, {"hook_event_name": "UserPromptSubmit"})["hookSpecificOutput"]["additionalContext"]
                self.assertIn("Caveman is active", prompt)
                self.assertEqual("Plain-English mode is active" in prompt, answer == "plain")
        # Plain restatement stands alone when Caveman is off, and an unknown
        # value is treated as unset rather than silently as plain.
        with tempfile.TemporaryDirectory() as tmp:
            staged = self.staged_hook(tmp, {"caveman": False}, explain="plain")
            prompt = self.run_staged(staged, {"hook_event_name": "UserPromptSubmit"})["hookSpecificOutput"]["additionalContext"]
            self.assertNotIn("Caveman is active", prompt)
            self.assertIn("Plain-English mode is active", prompt)
        with tempfile.TemporaryDirectory() as tmp:
            staged = self.staged_hook(tmp, {"caveman": False}, explain="simple-english-please")
            self.assertEqual(self.run_staged(staged, {"hook_event_name": "UserPromptSubmit"}), {})
            self.assertIn(
                "Explanation level is unset",
                self.run_staged(staged, {"hook_event_name": "SessionStart"})["hookSpecificOutput"]["additionalContext"],
            )

    def test_opt_out_path_suppresses_every_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            quiet = Path(tmp) / "quiet"
            (quiet / "nested").mkdir(parents=True)
            staged = self.staged_hook(tmp, {"caveman": True}, opt_out=[str(quiet)])
            for event in ("SessionStart", "SubagentStart", "UserPromptSubmit"):
                self.assertEqual(self.run_staged(staged, {"hook_event_name": event, "cwd": str(quiet)}), {})
                self.assertEqual(
                    self.run_staged(staged, {"hook_event_name": event, "cwd": str(quiet / "nested")}),
                    {},
                    "opt-out must cover subdirectories",
                )
                self.assertIn(
                    "hookSpecificOutput",
                    self.run_staged(staged, {"hook_event_name": event, "cwd": tmp}),
                    "opt-out must not leak to sibling paths",
                )

    def staged_plugin(self, tmp, explain=None, data_dir=True):
        """Reproduce an OpenCode install layout: <root>/plugins/*.mjs beside the
        user-owned <root>/.shahinkit-data/explain-mode. The filesystem read
        lives in the guard plugin; portable-gates stays I/O-free by contract."""
        root = Path(tmp)
        (root / "plugins").mkdir()
        source = ROOT / "opencode/.opencode/plugins/shahinkit-guard.mjs"
        (root / "plugins" / "shahinkit-guard.mjs").write_bytes(source.read_bytes())
        if data_dir:
            data = root / ".shahinkit-data"
            data.mkdir()
            if explain is not None:
                (data / "explain-mode").write_text(explain + "\n")
        return root / "plugins" / "shahinkit-guard.mjs"

    def transformed_system(self, plugin, sessions):
        script = f'''import {{ ShahinkitGuard }} from "{plugin.as_uri()}";
const hooks = await ShahinkitGuard({{ client: {{}} }});
const seen = [];
for (const id of {json.dumps(sessions)}) {{
  const output = {{ system: [] }};
  await hooks["experimental.chat.system.transform"]({{ sessionID: id }}, output);
  seen.push(output.system);
}}
console.log(JSON.stringify(seen));'''
        result = subprocess.run(["node", "--input-type=module", "-e", script], text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_opencode_restates_explain_mode_with_hook_parity(self):
        """OpenCode has no Python hook, so the plugin owns the same per-turn
        restatement and the same ask-once-while-unset behaviour."""
        with tempfile.TemporaryDirectory() as tmp:
            plugin = self.staged_plugin(tmp, explain="plain")
            for turn in self.transformed_system(plugin, ["one", "one"]):
                self.assertTrue(any("PLAIN-ENGLISH MODE ACTIVE" in line for line in turn), "plain is restated every turn")
                self.assertFalse(any("EXPLANATION LEVEL UNSET" in line for line in turn))
        with tempfile.TemporaryDirectory() as tmp:
            plugin = self.staged_plugin(tmp, explain="technical")
            for turn in self.transformed_system(plugin, ["one"]):
                self.assertFalse(any("PLAIN-ENGLISH MODE ACTIVE" in line or "EXPLANATION LEVEL UNSET" in line for line in turn))
        for value in (None, "simple-english-please"):
            with tempfile.TemporaryDirectory() as tmp:
                plugin = self.staged_plugin(tmp, explain=value)
                first, second, other = self.transformed_system(plugin, ["one", "one", "two"])
                self.assertTrue(any("EXPLANATION LEVEL UNSET" in line for line in first))
                self.assertFalse(any("EXPLANATION LEVEL UNSET" in line for line in second), "ask once per session")
                self.assertTrue(any("EXPLANATION LEVEL UNSET" in line for line in other))
        # No install data directory at all: silent, exactly like the Python hook.
        with tempfile.TemporaryDirectory() as tmp:
            plugin = self.staged_plugin(tmp, data_dir=False)
            for turn in self.transformed_system(plugin, ["one"]):
                self.assertFalse(any("EXPLANATION LEVEL UNSET" in line or "PLAIN-ENGLISH MODE ACTIVE" in line for line in turn))

    def test_opencode_prime_is_once_per_session_and_cleanup_is_present(self):
        plugin = ROOT / "opencode/.opencode/plugins/shahinkit-guard.mjs"
        result = subprocess.run(["node", "--check", str(plugin)], text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        script = f'''import {{ ShahinkitGuard }} from "{plugin.as_uri()}";
const hooks = await ShahinkitGuard({{ client: {{}} }});
const first = {{ system: [] }};
await hooks["experimental.chat.system.transform"]({{ sessionID: "one" }}, first);
const second = {{ system: [] }};
await hooks["experimental.chat.system.transform"]({{ sessionID: "one" }}, second);
if (first.system.length !== 1 || second.system.length !== 0) process.exit(1);
await hooks.event({{ event: {{ type: "session.deleted", properties: {{ sessionID: "one" }} }} }});
const reset = {{ system: [] }};
await hooks["experimental.chat.system.transform"]({{ sessionID: "one" }}, reset);
if (reset.system.length !== 1 || !reset.system[0].includes("Prime is available")) process.exit(2);'''
        result = subprocess.run(["node", "--input-type=module", "-e", script], text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
