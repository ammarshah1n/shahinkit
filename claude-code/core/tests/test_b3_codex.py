import json
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CODEX = ROOT / "codex"


class B3CodexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((ROOT / "claude-code" / "core" / "tests" / "fixtures" / "b3" / "codex-contract.json").read_text())

    def read(self, relative_path):
        return (CODEX / relative_path).read_text()

    def render(self, content, values):
        for name, value in values.items():
            content = content.replace(f"{{{{{name}}}}}", value).replace(f"<{name}>", value)
        return content

    def test_toml_templates_parse_and_use_separate_agent_files(self):
        config_text = self.read("config/config.patch.example.toml")
        config = tomllib.loads(config_text.replace("{{BASIC_MEMORY_ENABLED}}", "false"))
        self.assertNotIn("profiles", config)
        self.assertNotIn("projects", config)
        for forbidden in ("model", "approval_policy", "sandbox_mode", "network_access", "trust_level"):
            self.assertNotIn(forbidden, config)
        self.assertEqual(set(config["agents"]), set(self.contract["roles"]))
        for role in self.contract["roles"]:
            self.assertEqual(config["agents"][role]["config_file"], f"agents/{role}.toml")
        basic_memory = config["mcp_servers"]["basic-memory"]
        self.assertEqual(basic_memory["command"], "basic-memory")
        self.assertEqual(basic_memory["args"][:3], ["mcp", "--transport", "stdio"])
        self.assertFalse(basic_memory["enabled"])
        self.assertEqual(basic_memory["env"]["BASIC_MEMORY_FORCE_LOCAL"], "true")
        self.assertEqual(basic_memory["env"]["BASIC_MEMORY_EXPLICIT_ROUTING"], "true")
        self.assertNotIn("BASIC_MEMORY_FORCE_CLOUD", basic_memory["env"])
        self.assertNotIn("url", basic_memory)
        self.assertNotIn("CLOUD_HOST", json.dumps(basic_memory))
        optional = tomllib.loads(self.read("config/mcp.optional.disabled.example.toml"))
        self.assertTrue(all(not server["enabled"] for server in optional["mcp_servers"].values()))

        render = json.loads(self.read("render-manifest.json"))
        self.assertEqual(render["render_rules"]["scope_roots"]["project"]["skills"], ".agents/skills")
        self.assertEqual(render["render_rules"]["scope_roots"]["user"]["skills"], "$HOME/.agents/skills")
        self.assertNotIn(".codex/skills", json.dumps(render))
        self.assertIn("preview, apply, and host-trust", render["render_rules"]["activation"])
        fixture = json.loads((ROOT / "claude-code" / "core" / "tests" / "fixtures" / "b3" / "codex-render-values.json").read_text())
        self.assertEqual(render["render"]["required_substitutions"], fixture["required_substitutions"])

    def test_role_models_are_independent_and_exact(self):
        for role, model in self.contract["roles"].items():
            agent = tomllib.loads(self.read(f"config/agents/{role}.toml"))
            self.assertEqual(agent["name"], role)
            self.assertEqual(agent["model"], model)
            self.assertNotIn("inherit", json.dumps(agent).lower())
            self.assertTrue(agent["description"])
            self.assertTrue(agent["developer_instructions"].strip())

    def test_render_map_uses_canonical_assets_without_stale_copies(self):
        render = json.loads(self.read("render-manifest.json"))
        self.assertEqual(render["shared_skills"], self.contract["shared_skills"])
        self.assertEqual(render["shared_memory"], ["CORRECTIONS.md", "HANDOFF.md", "LEARNINGS.md", "NEXT.md", "PROJECT_STATE.md"])
        self.assertEqual(render["vendor_skills"]["ponytail"][0], "ponytail")
        self.assertEqual(render["vendor_skills"]["caveman"][0], "caveman")
        self.assertFalse(any((CODEX / ".agents").rglob("SKILL.md")))
        self.assertFalse(any((CODEX / "memory/templates").glob("*.md")))
        self.assertRegex(self.read("course-rag/SKILL.md"), r"(?m)^name: course-rag$")
        self.assertIn("{{SHAHINKIT_DATA_DIR}}/course-rag", self.read("course-rag/SKILL.md"))
        self.assertIn("<SOURCE_FOLDER>", self.read("course-rag/README.md"))
        self.assertTrue((CODEX / "course-rag/scripts/build.py").is_file())
        self.assertTrue((CODEX / "course-rag/scripts/search.py").is_file())

    def test_render_fixture_substitutes_enabled_config_and_builds_then_searches(self):
        render = json.loads(self.read("render-manifest.json"))
        values = {
            "SHAHINKIT_DATA_DIR": "rendered-data",
            "LOCAL_BASIC_MEMORY_CONFIG_DIR": "rendered-config",
            "LOCAL_PROJECT_NAME": "course-memory",
            "LOCAL_PROJECT_PATH": "rendered-project-path",
            "LOCAL_PROJECT_ROOT": "rendered-project-root",
            "BASIC_MEMORY_ENABLED": "true",
        }
        templates = set(render["render"]["templates"])
        self.assertIn("codex/config/config.patch.example.toml", templates)
        self.assertTrue(set(output["source"] for output in render["course_rag"]["outputs"]).issubset(templates | set(render["render"]["byte_copy"])))
        config = self.render((ROOT / next(source for source in templates if source.endswith("config.patch.example.toml"))).read_text(), values)
        local = self.render((ROOT / next(source for source in templates if source.endswith("local-config.example.json"))).read_text(), values)
        self.assertNotIn("<", config + local)
        self.assertNotIn("{{", config + local)
        self.assertFalse(tomllib.loads(config)["mcp_servers"]["basic-memory"]["enabled"])
        self.assertEqual(json.loads(local)["projects"]["course-memory"]["mode"], "local")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = root / "data"
            source = root / "source"
            source.mkdir()
            (source / "note.txt").write_text("photosynthesis converts light")
            rendered_values = {**values, "SHAHINKIT_DATA_DIR": str(data)}
            for output in render["course_rag"]["outputs"]:
                destination_template = output["destination"] if "destination" in output else output["destinations"]["project"]
                destination = root / self.render(destination_template, rendered_values)
                destination.parent.mkdir(parents=True, exist_ok=True)
                template_source = ROOT / output["source"]
                content = template_source.read_text()
                destination.write_text(self.render(content, rendered_values))
            build = data / "course-rag/scripts/build.py"
            search = data / "course-rag/scripts/search.py"
            built = subprocess.run([sys.executable, str(build), "--subject", "Biology", "--source", str(source)], text=True, capture_output=True, check=False)
            self.assertEqual(built.returncode, 0, built.stderr)
            found = subprocess.run([sys.executable, str(search), "Biology", "photosynthesis"], text=True, capture_output=True, check=False)
            self.assertEqual(found.returncode, 0, found.stderr)
            self.assertIn("note.txt", found.stdout)

    def test_native_lifecycle_hooks_are_safe_and_registered(self):
        generic = json.loads(self.read("hooks/generic-gates.disabled.example.json"))
        self.assertEqual(generic["status"], "retired-example")
        for scope in ("user", "project"):
            hooks = json.loads(self.read(f"hooks/{scope}.hooks.example.json"))["hooks"]
            self.assertEqual(set(hooks), {"SessionStart", "SubagentStart"})
            self.assertIn("{{SHAHINKIT_HOOK_PATH}}", json.dumps(hooks))
        agents = self.read("AGENTS.md")
        self.assertIn("Native `SessionStart` and `SubagentStart` hooks", agents)
        self.assertIn("write no files", agents)

    def test_rendered_context_and_security_boundaries(self):
        agents = self.read("AGENTS.md")
        for marker in ("CORE-POLICY", "PONYTAIL", "CAVEMAN", "ADAPTER-REFERENCES"):
            self.assertEqual(agents.count(f"<!-- SHAHINKIT:{marker}:START -->"), 1)
            self.assertEqual(agents.count(f"<!-- SHAHINKIT:{marker}:END -->"), 1)
        forbidden = re.compile(r"/(?:Users|home)/|~/(?:Documents|Library)|\bsk-[A-Za-z0-9]|BEGIN [A-Z ]*PRIVATE KEY", re.I)
        for path in CODEX.rglob("*"):
            self.assertFalse(path.is_symlink(), path)
            if path.is_file():
                content = path.read_text()
                self.assertIsNone(forbidden.search(content), path)
                self.assertNotIn('approval_policy = "never"', content, path)
                self.assertNotIn("network_access = true", content, path)
                self.assertNotIn("trust_level =", content, path)
                self.assertNotIn("[profiles.", content, path)


if __name__ == "__main__":
    unittest.main()
