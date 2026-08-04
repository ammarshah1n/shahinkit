import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ADAPTER = ROOT / "opencode"
OPENCODE = ADAPTER / ".opencode"
CONTRACT = json.loads((ROOT / "claude-code" / "core" / "tests" / "fixtures" / "b3" / "opencode" / "contract.json").read_text())


class B3OpenCodeTests(unittest.TestCase):
    def read(self, relative_path):
        return (ADAPTER / relative_path).read_text()

    def assert_local_basic_memory(self, server):
        self.assertEqual(server["type"], "local")
        self.assertFalse(server["enabled"])
        self.assertEqual(server["command"], ["basic-memory", "mcp", "--transport", "stdio", "--project", "<LOCAL_PROJECT_NAME>"])
        self.assertEqual(server["env"]["BASIC_MEMORY_CONFIG_DIR"], "<LOCAL_BASIC_MEMORY_CONFIG_DIR>")
        self.assertEqual(server["env"]["BASIC_MEMORY_DEFAULT_PROJECT"], "<LOCAL_PROJECT_NAME>")
        self.assertEqual(server["env"]["BASIC_MEMORY_PROJECT_ROOT"], "<LOCAL_PROJECT_ROOT>")
        self.assertEqual(server["env"]["BASIC_MEMORY_FORCE_LOCAL"], "true")
        self.assertEqual(server["env"]["BASIC_MEMORY_EXPLICIT_ROUTING"], "true")
        self.assertEqual(server["env"]["BASIC_MEMORY_AUTO_UPDATE"], "false")
        self.assertEqual(server["env"]["BASIC_MEMORY_LOGFIRE_ENABLED"], "false")
        self.assertEqual(server["env"]["BASIC_MEMORY_LOGFIRE_SEND_TO_LOGFIRE"], "false")
        self.assertEqual(server["env"]["BASIC_MEMORY_CLOUD_PROMO_OPT_OUT"], "true")
        self.assertNotIn("BASIC_MEMORY_FORCE_CLOUD", server["env"])
        self.assertNotIn("url", server)
        self.assertNotIn("headers", server)

    def render_template(self, content, values):
        for mode in ("PONYTAIL_ENABLED", "CAVEMAN_ENABLED"):
            content = re.sub(rf"\{{\{{#{mode}\}}\}}(.*?)\{{\{{/{mode}\}}\}}", lambda match: match.group(1) if values[mode] == "true" else "", content, flags=re.S)
        for name, value in values.items():
            content = content.replace(f"{{{{{name}}}}}", value)
        return content

    def render_scope(self, scope, values=None):
        render = json.loads(self.read("render-manifest.json"))["render"]
        values = values or render["default_substitutions"]
        spec = render["scope_templates"][scope]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = json.loads(self.render_template((ROOT / spec["config"]).read_text(), values))
            (root / spec["config_destination"]).write_text(json.dumps(config))
            (root / "AGENTS.md").write_text(self.render_template((ROOT / spec["agents"]).read_text(), values))
            feature = root / spec["plugin_destination"]
            feature.parent.mkdir(parents=True)
            feature.write_text(self.render_template((ROOT / spec["plugin_features"]).read_text(), values))
            plugin = root / (spec["plugin_destination"].removesuffix(".features.mjs") + ".mjs")
            plugin.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / render["byte_copy"][0], plugin)
            skill = root / config["skills"]["paths"][0] / "prime" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            shutil.copy2(ROOT / "claude-code" / "core" / "shared" / "skills" / "prime" / "SKILL.md", skill)
            yield root, config, plugin

    def test_jsonc_example_uses_current_local_contract(self):
        config = json.loads(self.read("opencode.jsonc.example"))
        self.assertEqual(config["$schema"], "https://opencode.ai/config.json")
        self.assertEqual(config["default_agent"], "controller")
        self.assertFalse(config["autoupdate"])
        self.assertEqual(config["share"], "disabled")
        self.assertEqual(config["skills"]["paths"], [".opencode/skills"])
        self.assertNotIn("plugin", config)
        self.assertEqual(set(config["mcp"]), {"basic-memory", "dev-scope"})

        basic_memory = config["mcp"]["basic-memory"]
        self.assert_local_basic_memory(basic_memory)
        self.assertFalse(config["mcp"]["dev-scope"]["enabled"])
        self.assertEqual(config["mcp"]["dev-scope"]["type"], "local")

    def test_user_scope_example_uses_user_relative_paths(self):
        config = json.loads(self.read("opencode.user.jsonc.example"))
        self.assertEqual(config["skills"]["paths"], ["skills"])
        self.assertNotIn("plugin", config)
        self.assert_local_basic_memory(config["mcp"]["basic-memory"])

    def test_user_scope_render_smoke_uses_config_relative_skills_and_plugin(self):
        for scope in ("user", "project"):
            for root, config, plugin in self.render_scope(scope):
                self.assertTrue((root / config["skills"]["paths"][0] / "prime" / "SKILL.md").is_file())
                self.assertTrue(plugin.is_file())
                result = subprocess.run([shutil.which("node"), "--check", str(plugin)], text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_agents_are_explicit_independent_and_use_permissions_and_step_caps(self):
        for role, model in CONTRACT["roles"].items():
            content = self.read(f".opencode/agents/{role}.md")
            self.assertIn(f"model: {model}", content)
            self.assertIn("maxSteps:", content)
            self.assertIn("permission:", content)
            self.assertNotRegex(content, r"(?m)^steps:")
            self.assertNotIn("tools:", content)
            self.assertNotIn("inherit:", content)
            self.assertNotIn("inherits_from:", content)
        self.assertIn("mode: primary", self.read(".opencode/agents/controller.md"))
        for worker in ("research", "implementation", "review", "mechanical"):
            content = self.read(f".opencode/agents/{worker}.md")
            self.assertIn("mode: subagent", content)
            self.assertIn("task: deny", content)
        self.assertIn("edit: deny", self.read(".opencode/agents/research.md"))
        self.assertIn("edit: deny", self.read(".opencode/agents/review.md"))

    def test_commands_are_thin_controller_wrappers(self):
        for name in CONTRACT["commands"]:
            content = self.read(f".opencode/commands/{name}.md")
            self.assertRegex(content, r"^---\ndescription: .+\nagent: controller\n(?:permalink: opencode-command-files/[a-z0-9-]+\n)?---\n", name)
            self.assertIn("$ARGUMENTS", content, name)
            self.assertNotIn("!`", content, name)

    def test_render_map_uses_canonical_assets_without_stale_copies(self):
        rendered = json.loads(self.read("render-manifest.json"))
        self.assertEqual(rendered["opencode_version"], CONTRACT["version"])
        self.assertEqual(sorted(rendered["shared_skills"]), sorted(CONTRACT["skills"]))
        self.assertEqual(rendered["shared_memory"], sorted(CONTRACT["memory"]))
        self.assertEqual(rendered["render_rules"]["scope_roots"]["project"]["skills"], ".opencode/skills")
        self.assertEqual(rendered["render_rules"]["scope_roots"]["user"]["skills"], "skills")
        self.assertEqual(rendered["course_rag"]["skill_destinations"], {"user": "skills/course-rag/SKILL.md", "project": ".opencode/skills/course-rag/SKILL.md"})
        self.assertEqual(len(rendered["course_rag"]["outputs"]), 6)
        self.assertEqual(rendered["scope_examples"], {"user": "opencode.user.jsonc.example", "project": "opencode.jsonc.example"})
        self.assertEqual(rendered["render"]["default_substitutions"], {"PONYTAIL_ENABLED": "true", "CAVEMAN_ENABLED": "true"})
        self.assertEqual(rendered["vendor_skills"]["ponytail"][0], "ponytail")
        self.assertEqual(rendered["vendor_skills"]["caveman"][0], "caveman")
        self.assertFalse(any((OPENCODE / "skills").rglob("SKILL.md")))
        self.assertFalse(any((ADAPTER / "memory").glob("*.md")))
        agents = self.read("AGENTS.md")
        for block in ("CORE-POLICY", "PONYTAIL", "CAVEMAN", "ADAPTER-REFERENCES"):
            self.assertIn(f"<!-- SHAHINKIT:{block}:START -->", agents)
            self.assertIn(f"<!-- SHAHINKIT:{block}:END -->", agents)

    def test_plugin_is_local_payload_minimized_and_syntax_valid(self):
        plugin = OPENCODE / "plugins/portable-gates.mjs"
        content = plugin.read_text()
        for forbidden in ("process.env", "child_process", "fetch(", "http://", "https://", "readFile", "writeFile", "spawn(", "exec("):
            self.assertNotIn(forbidden, content)
        self.assertIn("sessionModes", content)
        self.assertIn("session.deleted", content)
        self.assertIn("ignored invalid lifecycle event", content)
        self.assertNotIn("JSON.stringify(input)", content)
        self.assertNotIn("JSON.stringify(event)", content)
        node = shutil.which("node")
        self.assertIsNotNone(node, "node is required for plugin syntax verification")
        result = subprocess.run([node, "--check", str(plugin)], text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_plugin_defaults_and_per_session_mode_change(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "node is required for plugin lifecycle verification")
        for root, _, plugin in self.render_scope("project"):
            plugin_url = plugin.as_uri()
            script = f'''import createPlugin from "{plugin_url}";
const hooks = await createPlugin({{ client: {{ app: {{ log: () => {{}} }} }} }});
const first = {{ system: [] }};
await hooks["experimental.chat.system.transform"]({{ sessionID: "one" }}, first);
if (first.system.length !== 2 || !first.system[0].includes("(full)") || !first.system[1].includes("(full)")) process.exit(1);
await hooks["chat.message"]({{ sessionID: "one" }}, {{ parts: [{{ type: "text", text: "/ponytail off" }}] }});
await hooks["command.execute.before"]({{ sessionID: "one", command: "ponytail", arguments: "off" }});
const second = {{ system: [] }};
await hooks["experimental.chat.system.transform"]({{ sessionID: "one" }}, second);
if (second.system.length !== 1 || !second.system[0].includes("CAVEMAN")) process.exit(2);
const other = {{ system: [] }};
await hooks["experimental.chat.system.transform"]({{ sessionID: "two" }}, other);
if (other.system.length !== 2) process.exit(3);
await hooks.event({{ event: {{ type: "session.deleted", properties: {{ sessionID: "one" }} }} }});
const reset = {{ system: [] }};
await hooks["experimental.chat.system.transform"]({{ sessionID: "one" }}, reset);
if (reset.system.length !== 2) process.exit(4);'''
            result = subprocess.run([node, "--input-type=module", "-e", script], text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_plugin_honors_managed_feature_opt_outs(self):
        node = shutil.which("node")
        self.assertIsNotNone(node)
        for scope in ("user", "project"):
            for ponytail, caveman in (("true", "true"), ("false", "true"), ("true", "false"), ("false", "false")):
                for root, _, plugin in self.render_scope(scope, {"PONYTAIL_ENABLED": ponytail, "CAVEMAN_ENABLED": caveman}):
                    rendered_agents = (root / "AGENTS.md").read_text()
                    self.assertEqual("SHAHINKIT:PONYTAIL:START" in rendered_agents, ponytail == "true")
                    self.assertEqual("SHAHINKIT:CAVEMAN:START" in rendered_agents, caveman == "true")
                    expected = int(ponytail == "true") + int(caveman == "true")
                    script = f'''import createPlugin from "{plugin.as_uri()}";
const hooks = await createPlugin();
const output = {{ system: [] }};
await hooks["experimental.chat.system.transform"]({{ sessionID: "one" }}, output);
if (output.system.length !== {expected}) process.exit(1);'''
                    result = subprocess.run([node, "--input-type=module", "-e", script], text=True, capture_output=True, check=False)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_plugin_detects_stop_phrases_without_substring_matches(self):
        node = shutil.which("node")
        for _, _, plugin in self.render_scope("project"):
            script = f'''import createPlugin from "{plugin.as_uri()}";
const hooks = await createPlugin();
await hooks["chat.message"]({{ sessionID: "one" }}, {{ parts: [{{ type: "text", text: "please stop ponytail" }}] }});
const stopped = {{ system: [] }};
await hooks["experimental.chat.system.transform"]({{ sessionID: "one" }}, stopped);
if (stopped.system.length !== 1 || !stopped.system[0].includes("CAVEMAN")) process.exit(1);
await hooks["chat.message"]({{ sessionID: "two" }}, {{ parts: [{{ type: "text", text: "do not stop ponytailing" }}] }});
const unchanged = {{ system: [] }};
await hooks["experimental.chat.system.transform"]({{ sessionID: "two" }}, unchanged);
if (unchanged.system.length !== 2) process.exit(2);'''
            result = subprocess.run([node, "--input-type=module", "-e", script], text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_plugin_ignores_negated_stop_phrases_for_both_modes(self):
        node = shutil.which("node")
        for _, _, plugin in self.render_scope("project"):
            script = f'''import createPlugin from "{plugin.as_uri()}";
const hooks = await createPlugin();
for (const [id, text] of [["one", "do not ever stop ponytail"], ["two", "don't stop caveman"], ["three", "never stop ponytail"], ["four", "not stop caveman"], ["five", "avoid stop ponytail"]]) {{
  await hooks["chat.message"]({{ sessionID: id }}, {{ parts: [{{ type: "text", text }}] }});
  const output = {{ system: [] }};
  await hooks["experimental.chat.system.transform"]({{ sessionID: id }}, output);
  if (output.system.length !== 2) process.exit(1);
}}
for (const [id, text] of [["six", "do not use normal mode"], ["seven", "never normal mode"], ["eight", "avoid normal mode"]]) {{
  await hooks["chat.message"]({{ sessionID: id }}, {{ parts: [{{ type: "text", text }}] }});
  const output = {{ system: [] }};
  await hooks["experimental.chat.system.transform"]({{ sessionID: id }}, output);
  if (output.system.length !== 2) process.exit(2);
}}
await hooks["chat.message"]({{ sessionID: "nine" }}, {{ parts: [{{ type: "text", text: "please stop caveman" }}] }});
const stopped = {{ system: [] }};
await hooks["experimental.chat.system.transform"]({{ sessionID: "nine" }}, stopped);
if (stopped.system.length !== 1 || !stopped.system[0].includes("PONYTAIL")) process.exit(3);
await hooks["chat.message"]({{ sessionID: "ten" }}, {{ parts: [{{ type: "text", text: "please use normal mode" }}] }});
const normal = {{ system: [] }};
await hooks["experimental.chat.system.transform"]({{ sessionID: "ten" }}, normal);
if (normal.system.length !== 0) process.exit(4);'''
            result = subprocess.run([node, "--input-type=module", "-e", script], text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_plugin_preserves_combined_explicit_clauses(self):
        node = shutil.which("node")
        for _, _, plugin in self.render_scope("project"):
            script = f'''import createPlugin from "{plugin.as_uri()}";
const hooks = await createPlugin();
await hooks["chat.message"]({{ sessionID: "one" }}, {{ parts: [{{ type: "text", text: "stop ponytail; caveman off" }}] }});
const output = {{ system: [] }};
await hooks["experimental.chat.system.transform"]({{ sessionID: "one" }}, output);
if (output.system.length !== 0) process.exit(1);'''
            result = subprocess.run([node, "--input-type=module", "-e", script], text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_plugin_parses_slash_commands_per_clause_without_negated_prose(self):
        node = shutil.which("node")
        for _, _, plugin in self.render_scope("project"):
            script = f'''import createPlugin from "{plugin.as_uri()}";
const hooks = await createPlugin();
await hooks["chat.message"]({{ sessionID: "one" }}, {{ parts: [{{ type: "text", text: "/ponytail off; /caveman off" }}] }});
const stopped = {{ system: [] }};
await hooks["experimental.chat.system.transform"]({{ sessionID: "one" }}, stopped);
if (stopped.system.length !== 0) process.exit(1);
await hooks["chat.message"]({{ sessionID: "two" }}, {{ parts: [{{ type: "text", text: "do not ever /ponytail off; never /caveman off" }}] }});
const unchanged = {{ system: [] }};
await hooks["experimental.chat.system.transform"]({{ sessionID: "two" }}, unchanged);
if (unchanged.system.length !== 2) process.exit(2);'''
            result = subprocess.run([node, "--input-type=module", "-e", script], text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_apply_lifecycle_documentation_and_no_symlinks_or_private_payload(self):
        readme = self.read("README.md")
        self.assertIn("--apply", readme)
        self.assertIn("trust confirmation", readme)
        self.assertIn("--without-ponytail", readme)
        self.assertIn("--without-caveman", readme)
        self.assertIn("No symlinks", readme)
        corpus = "\n".join(path.read_text() for path in ADAPTER.rglob("*") if path.is_file())
        self.assertIsNone(re.search(r"/(?:Users|home)/", corpus))
        self.assertIsNone(re.search(r"\bsk-[A-Za-z0-9]", corpus))
        self.assertIsNone(re.search(r"\b[A-Z0-9_]*(?:API_KEY|TOKEN|SECRET)\s*=\s*[^<\s]", corpus))
        for directory, _, files in os.walk(ADAPTER):
            for filename in files:
                self.assertFalse((Path(directory) / filename).is_symlink())


if __name__ == "__main__":
    unittest.main()
