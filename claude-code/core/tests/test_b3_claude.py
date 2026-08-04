import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ADAPTER = ROOT / "claude-code"
FIXTURE = ROOT / "claude-code" / "core" / "tests" / "fixtures" / "b3" / "claude-contract.json"


class B3ClaudeAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(FIXTURE.read_text())
        cls.render = json.loads((ADAPTER / "render-manifest.json").read_text())

    def test_json_assets_parse_and_use_current_claude_names(self):
        for path in (ADAPTER / "config").glob("*.json"):
            json.loads(path.read_text())
        for path in (ADAPTER / "hooks").glob("*.json"):
            json.loads(path.read_text())
        self.assertEqual(self.render["claude_code_version"], ">=2.1.209 <2.2.0")
        self.assertIn(".claude/settings.json", (ADAPTER / "README.md").read_text())
        self.assertIn(".mcp.json", (ADAPTER / "README.md").read_text())
        settings = self.render["settings_patches"]
        self.assertEqual(settings["base_source"], "claude-code/config/settings.patch.example.json")
        self.assertEqual(set(settings["hook_sources"]), {"user", "project"})
        self.assertEqual(settings["hook_script_source"], "claude-code/core/hooks/shahinkit_hook.py")
        self.assertEqual(settings["destinations"], {"user": "settings.json", "project": ".claude/settings.json"})

    def test_render_references_cover_every_shared_asset_without_symlinks(self):
        copies = {(item["source"], item["destination"]) for item in self.render["copies"]}
        for skill in self.contract["shared_skills"]:
            source = f"claude-code/core/shared/skills/{skill}/SKILL.md"
            self.assertTrue((ROOT / source).is_file(), source)
            self.assertIn((source, f"skills/{skill}/SKILL.md"), copies)
        for template in self.contract["shared_memory"]:
            source = f"claude-code/core/shared/memory/{template}"
            self.assertTrue((ROOT / source).is_file(), source)
            self.assertIn((source, f"memory/templates/{template}"), copies)
        claude = (ADAPTER / "CLAUDE.md").read_text()
        self.assertEqual(len(self.render["context_renders"]), len(self.contract["shared_context"]))
        for marker in self.contract["shared_context"]:
            self.assertEqual(claude.count(f"<!-- SHAHINKIT:{marker}:START -->"), 1)
            self.assertEqual(claude.count(f"<!-- SHAHINKIT:{marker}:END -->"), 1)
        for item in self.render["context_renders"]:
            source = (ROOT / item["source"]).read_text().strip()
            pattern = rf"<!-- SHAHINKIT:{item['marker']}:START -->.*?<!-- SHAHINKIT:{item['marker']}:END -->"
            self.assertEqual(re.search(pattern, claude, flags=re.S).group(0), source)
        for path in ADAPTER.rglob("*"):
            self.assertFalse(path.is_symlink(), path)

    def test_pinned_vendor_skills_are_rendered_without_colliding_command_shims(self):
        copies = {(item["source"], item["destination"]) for item in self.render["copies"]}
        for skill in ("ponytail", "ponytail-audit", "ponytail-debt", "ponytail-gain", "ponytail-help", "ponytail-review"):
            self.assertIn((f"claude-code/core/third_party/ponytail/skills/{skill}/SKILL.md", f"skills/{skill}/SKILL.md"), copies)
        for skill in ("caveman", "caveman-commit", "caveman-help", "caveman-review"):
            self.assertIn((f"claude-code/core/third_party/caveman/skills/{skill}/SKILL.md", f"skills/{skill}/SKILL.md"), copies)
        self.assertFalse(any(destination.startswith("commands/") for _, destination in copies))
        self.assertFalse(any((ADAPTER / "commands").glob("*.md")))
        readme = (ADAPTER / "README.md").read_text()
        self.assertIn("canonical slash-command definitions", readme)

    def test_agents_have_explicit_role_models_and_no_permission_bypass(self):
        roles = json.loads((ROOT / "claude-code" / "core" / "shared" / "models" / "roles.schema.json").read_text())
        defaults = roles["x-shahinkit"]["defaults"]["claude-code"]
        rendered = json.loads((ADAPTER / "config/roles.resolved.example.json").read_text())
        for name, model in self.contract["roles"].items():
            text = (ADAPTER / "agents" / f"{name}.md").read_text()
            self.assertRegex(text, rf"(?m)^name: {re.escape(name)}$")
            self.assertRegex(text, rf"(?m)^model: {re.escape(model)}$")
            self.assertNotIn("model: inherit", text)
            self.assertNotIn("bypassPermissions", text)
            self.assertEqual(defaults[name], model)
            self.assertEqual(rendered["roles"][name]["resolved_model"], model)
        controller = (ADAPTER / "agents/controller.md").read_text()
        self.assertIn("tools: Agent, Read, Glob, Grep, Bash, Edit, Write", controller)

    def test_lifecycle_hooks_are_explicit_safe_and_host_native(self):
        generic = json.loads((ADAPTER / "hooks/generic.disabled.example.json").read_text())
        self.assertEqual(generic["status"], "retired-example")
        for scope in ("user", "project"):
            hooks = json.loads((ADAPTER / f"hooks/{scope}.hooks.example.json").read_text())["hooks"]
            self.assertEqual(set(hooks), {"SessionStart", "SubagentStart"})
            self.assertIn("{{SHAHINKIT_HOOK_PATH}}", json.dumps(hooks))
        lifecycle = json.loads((ADAPTER / "hooks/managed-lifecycle.after-trust.json").read_text())
        self.assertEqual(lifecycle["activation"]["required"], ["preview", "apply", "trust-host"])
        self.assertTrue(lifecycle["activation"]["default_enabled"])
        self.assertTrue(lifecycle["activation"]["host_reload_required"])
        self.assertFalse(lifecycle["hooks"]["filesystem_writes"])
        self.assertFalse(lifecycle["hooks"]["telemetry"])
        for mode in ("ponytail", "caveman"):
            self.assertTrue(lifecycle["modes"][mode]["enabled"])
            self.assertEqual(lifecycle["modes"][mode]["default"], "full")
            self.assertEqual(lifecycle["modes"][mode]["hook_registration"], "none")

    def test_security_and_failure_contracts(self):
        mcp = json.loads((ADAPTER / "config/mcp.basic-memory.example.json").read_text())
        server = mcp["mcpServers"]["basic-memory"]
        self.assertEqual(server["command"], "basic-memory")
        self.assertEqual(server["args"][-1], "<LOCAL_PROJECT_NAME>")
        self.assertEqual(server["env"]["BASIC_MEMORY_FORCE_LOCAL"], "true")
        self.assertEqual(server["env"]["BASIC_MEMORY_EXPLICIT_ROUTING"], "true")
        self.assertNotIn("BASIC_MEMORY_FORCE_CLOUD", server["env"])
        local = json.loads((ROOT / "claude-code" / "core" / "shared" / "mcp" / "basic-memory" / "local-config.example.json").read_text())
        project = local["projects"]["<LOCAL_PROJECT_NAME>"]
        self.assertEqual(project["mode"], "local")
        self.assertIsNone(project["workspace_id"])
        self.assertIn(("claude-code/core/shared/mcp/basic-memory/local-config.example.json", "config/basic-memory.local-config.example.json"), {(item["source"], item["destination"]) for item in self.render["copies"]})
        self.assertNotIn("API_KEY", json.dumps(server))
        corpus = "\n".join(
            path.read_text(errors="ignore")
            for path in ADAPTER.rglob("*")
            if path.is_file()
            and path.relative_to(ADAPTER).parts[0] != "core"
            and "course-rag" not in path.parts
        )
        self.assertIsNone(re.search(r"/(?:Users|home)/", corpus))
        self.assertNotIn("bypassPermissions", corpus)
        self.assertNotIn("curl |", corpus)
        self.assertNotIn("npx -y", corpus)
        self.assertIn("Never symlink.", self.render["render_rules"]["copy"])
        self.assertIn("automatic writes", json.dumps(lifecycle := json.loads((ADAPTER / "hooks/managed-lifecycle.after-trust.json").read_text())))


if __name__ == "__main__":
    unittest.main()
