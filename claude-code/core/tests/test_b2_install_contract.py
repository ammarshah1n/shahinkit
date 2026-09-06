import json
import re
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CANONICAL_URL = "https://github.com/ammarshah1n/shahinkit.git"


class B2InstallContractTests(unittest.TestCase):
    def read(self, relative_path):
        return (ROOT / relative_path).read_text()

    def load_json(self, relative_path):
        return json.loads(self.read(relative_path))

    def test_context_blocks_are_bounded_and_portable(self):
        blocks = {
            "claude-code/core/shared/context/core-policy.block.md": "CORE-POLICY",
            "claude-code/core/shared/context/ponytail-default.block.md": "PONYTAIL",
            "claude-code/core/shared/context/caveman-default.block.md": "CAVEMAN",
            "claude-code/core/shared/context/explain-mode.block.md": "EXPLAIN-MODE",
            "claude-code/core/shared/context/adapter-references.block.md": "ADAPTER-REFERENCES",
        }
        forbidden = re.compile(r"/(?:Users|home)/|\bsk-[A-Za-z0-9]|\bbmc_[A-Za-z0-9]", re.I)
        for path, name in blocks.items():
            content = self.read(path)
            self.assertEqual(content.count(f"<!-- SHAHINKIT:{name}:START -->"), 1)
            self.assertEqual(content.count(f"<!-- SHAHINKIT:{name}:END -->"), 1)
            self.assertLess(content.index("START"), content.index("END"))
            self.assertIsNone(forbidden.search(content), path)

        rendered_destination = "\n".join(self.read(path) for path in blocks)
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "AGENTS.md"
            destination.write_text(rendered_destination)
            self.assertEqual(destination.read_text(), rendered_destination)
        self.assertNotIn("claude-code/core/shared/", rendered_destination)
        self.assertNotIn("claude-code/core/third_party/", rendered_destination)
        caveman = self.read("claude-code/core/shared/context/caveman-default.block.md")
        self.assertIn("full", caveman)
        self.assertIn("Auto-Clarity", caveman)
        explain = self.read("claude-code/core/shared/context/explain-mode.block.md")
        self.assertIn("explain-mode", explain)
        self.assertIn("plain", explain)
        self.assertIn("technical", explain)
        self.assertIn("ask once", explain)

    def test_basic_memory_templates_are_pinned_local_and_parseable(self):
        policy = self.load_json("claude-code/core/shared/mcp/basic-memory/local-config.example.json")
        self.assertEqual(policy["basic_memory_version"], "0.22.1")
        self.assertEqual(policy["projects"]["<LOCAL_PROJECT_NAME>"]["mode"], "local")
        self.assertEqual(policy["default_project"], "<LOCAL_PROJECT_NAME>")
        self.assertEqual(policy["project_root"], "<LOCAL_PROJECT_ROOT>")
        self.assertFalse(policy["auto_update"])
        self.assertFalse(policy["logfire_enabled"])
        self.assertFalse(policy["logfire_send_to_logfire"])
        self.assertTrue(policy["cloud_promo_opt_out"])
        self.assertNotIn("cloud_host", policy)
        self.assertNotIn("cloud_api_key", policy)

        claude = json.loads(self.read("claude-code/core/shared/mcp/basic-memory/claude-code.mcp.json").replace("{{BASIC_MEMORY_ENABLED}}", "false"))
        claude_server = claude["mcpServers"]["basic-memory"]
        self.assertEqual(claude_server["command"], "basic-memory")
        self.assertIn("--project", claude_server["args"])
        self.assertIn("<LOCAL_PROJECT_NAME>", claude_server["args"])

        opencode = json.loads(self.read("claude-code/core/shared/mcp/basic-memory/opencode.mcp.json").replace("{{BASIC_MEMORY_ENABLED}}", "false"))
        server = opencode["mcp"]["basic-memory"]
        self.assertEqual(server["type"], "local")
        self.assertFalse(server["enabled"])
        self.assertEqual(server["command"][0], "basic-memory")

        codex = tomllib.loads(self.read("claude-code/core/shared/mcp/basic-memory/codex.mcp.toml").replace("{{BASIC_MEMORY_ENABLED}}", "false"))
        server = codex["mcp_servers"]["basic-memory"]
        self.assertFalse(server["enabled"])
        self.assertEqual(server["command"], "basic-memory")

        for launcher in (claude_server, opencode["mcp"]["basic-memory"], server):
            serialized = json.dumps(launcher)
            self.assertNotIn("uvx", serialized)
            self.assertNotIn("--from", serialized)
            self.assertNotIn("basic-memory==", serialized)
            env = launcher["env"]
            self.assertEqual(env["BASIC_MEMORY_CONFIG_DIR"], "<LOCAL_BASIC_MEMORY_CONFIG_DIR>")
            self.assertEqual(env["BASIC_MEMORY_DEFAULT_PROJECT"], "<LOCAL_PROJECT_NAME>")
            self.assertEqual(env["BASIC_MEMORY_PROJECT_ROOT"], "<LOCAL_PROJECT_ROOT>")
            self.assertEqual(env["BASIC_MEMORY_AUTO_UPDATE"], "false")
            self.assertEqual(env["BASIC_MEMORY_LOGFIRE_ENABLED"], "false")
            self.assertEqual(env["BASIC_MEMORY_LOGFIRE_SEND_TO_LOGFIRE"], "false")
            self.assertEqual(env["BASIC_MEMORY_CLOUD_PROMO_OPT_OUT"], "true")
            self.assertFalse(any("CLOUD_HOST" in key or "API_KEY" in key for key in env))

    def test_optional_mcp_examples_are_disabled_and_secret_referential(self):
        examples = self.load_json("claude-code/core/shared/mcp/optional/examples.json")["examples"]
        for name in ("context7", "timed", "research", "dev-scope"):
            self.assertFalse(examples[name]["enabled"], name)
        for name in ("context7", "timed", "research"):
            self.assertRegex(examples[name]["secret_env"], r"^[A-Z0-9_]+$")
            self.assertRegex(examples[name]["secret_file"], r"^<[^>]+>$")
        dev_scope = examples["dev-scope"]
        self.assertEqual(dev_scope["transport"], "stdio")
        self.assertTrue(dev_scope["local_only"])
        self.assertTrue(dev_scope["read_only"])

        codex = tomllib.loads(self.read("claude-code/core/shared/mcp/optional/codex.mcp.toml"))
        for server in codex["mcp_servers"].values():
            self.assertFalse(server["enabled"])

    def test_install_document_contract_and_fixtures(self):
        install = self.read("INSTALL.md")
        fixture_root = ROOT / "claude-code" / "core" / "tests" / "fixtures" / "b2" / "install"
        self.assertEqual((fixture_root / "canonical-url.txt").read_text().strip(), CANONICAL_URL)
        request = (fixture_root / "natural-language-request.txt").read_text()
        self.assertIn(CANONICAL_URL, request)
        self.assertIn("OpenCode", request)
        self.assertIn("Preview only", request)

        required = (
            "claude-code/core/scripts/manage.py` is Python-stdlib-only",
            CANONICAL_URL,
            "--agent claude-code",
            "--agent opencode",
            "--agent codex",
            "--preview",
            "--apply",
            "--trust-host",
            "--without-ponytail",
            "--without-caveman",
            "git verify-tag <RELEASE_TAG>",
            "host activation",
            ".shahinkit-install-receipt.json",
            "rollback",
            "--allow-development-checkout",
            "rerun every fail-closed public-release gate",
            "canonical\norigin",
            "release-manifest tree and file digests",
        )
        for value in required:
            self.assertIn(value, install)

        for forbidden in (fixture_root / "rejected-patterns.txt").read_text().splitlines():
            self.assertNotIn(forbidden, install)
        self.assertNotRegex(install, r"/(?:Users|home)/")


if __name__ == "__main__":
    unittest.main()
