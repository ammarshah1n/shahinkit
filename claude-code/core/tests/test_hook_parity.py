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
        self.assertEqual(source.count("read_text"), 2)  # hook-config.json and opt-out
        self.assertIn('"hook-config.json"', source)
        self.assertIn('"opt-out"', source)

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

    def staged_hook(self, tmp, config, opt_out=None):
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
