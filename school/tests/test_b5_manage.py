import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "school/scripts/manage.py"
spec = importlib.util.spec_from_file_location("shahinkit_manage", MANAGER)
manage = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = manage
spec.loader.exec_module(manage)


class B5ManagerTests(unittest.TestCase):
    def fixture(self, agent, scope):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name) / "destination"
        shutil.copytree(ROOT / "school/tests/fixtures/hosts" / agent / scope, root)
        self.addCleanup(temp.cleanup)
        return root

    def cli(self, *args, environment=None):
        env = {**os.environ, **(environment or {})}
        return subprocess.run([sys.executable, str(MANAGER), *args], text=True, capture_output=True, env=env, check=False)

    def command(self, command, agent, scope, root, *extra):
        return self.cli(command, "--agent", agent, "--scope", scope, "--destination", str(root), "--allow-development-checkout", *extra)

    def preview_digest(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        match = re.search(r"^preview-digest: ([0-9a-f]{64})$", result.stdout, re.M)
        self.assertIsNotNone(match, result.stdout)
        return match.group(1)

    def apply(self, command, agent, scope, root, *extra):
        preview = self.command(command, agent, scope, root, *extra)
        digest = self.preview_digest(preview)
        arguments = ["--apply", "--preview-digest", digest]
        if command in ("install", "update"):
            arguments.append("--trust-host")
        result = self.command(command, agent, scope, root, *extra, *arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def local_path(self, root, receipt_item):
        return (root if receipt_item["base"] == "root" else root / "home") / receipt_item["path"]

    def test_matrix_preview_apply_update_uninstall_and_no_unresolved_placeholders(self):
        for agent in ("claude-code", "opencode", "codex"):
            for scope in ("user", "project"):
                with self.subTest(agent=agent, scope=scope):
                    root = self.fixture(agent, scope)
                    before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
                    self.preview_digest(self.command("install", agent, scope, root))
                    self.assertEqual(before, {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()})
                    self.apply("install", agent, scope, root)
                    receipt = json.loads((root / ".shahinkit-install-receipt.json").read_text())
                    self.assertEqual(receipt["schema_version"], 2)
                    self.assertEqual(receipt["adapter"], agent)
                    self.assertTrue(receipt["features"]["ponytail"])
                    self.assertFalse(receipt["features"]["basic-memory"])
                    self.assertTrue(all(item["base"] in ("root", "home") for item in receipt["owned"]))
                    rendered = [self.local_path(root, item) for item in receipt["owned"] if item["path"].endswith((".json", ".jsonc", ".toml", ".mjs"))]
                    corpus = "\n".join(path.read_text(errors="ignore") for path in rendered if path.is_file())
                    self.assertNotIn("{{", corpus)
                    self.assertNotIn("<LOCAL_BASIC_MEMORY", corpus)
                    self.apply("update", agent, scope, root)
                    self.apply("uninstall", agent, scope, root)
                    self.assertFalse((root / ".shahinkit-install-receipt.json").exists())

    def test_codex_user_isolated_destination_uses_root_and_home_aliases_through_lifecycle(self):
        root = self.fixture("codex", "user")
        original = (root / "AGENTS.md").read_text()
        self.apply("install", "codex", "user", root)
        receipt = json.loads((root / ".shahinkit-install-receipt.json").read_text())
        self.assertTrue(any(item["base"] == "home" for item in receipt["owned"]))
        self.assertTrue((root / "home/.agents/skills/course-rag/SKILL.md").is_file())
        self.assertNotIn(str(root), json.dumps(receipt))
        self.apply("update", "codex", "user", root, "--without-caveman")
        self.apply("rollback", "codex", "user", root)
        self.apply("uninstall", "codex", "user", root)
        self.assertEqual((root / "AGENTS.md").read_text(), original)

    def test_auto_user_detection_checks_each_host_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            claude = home / "claude"
            opencode = home / "config/opencode"
            codex = home / "codex"
            claude.mkdir(parents=True)
            opencode.mkdir(parents=True)
            codex.mkdir(parents=True)
            (claude / "settings.json").write_text('{"$schema":"https://json.schemastore.org/claude-code-settings.json"}')
            (opencode / "opencode.jsonc").write_text('{"$schema":"https://opencode.ai/config.json"}')
            (codex / "config.toml").write_text("# Codex marker\n")
            roots = {"CLAUDE_CONFIG_DIR": str(claude.resolve()), "XDG_CONFIG_HOME": str((home / "config").resolve()), "CODEX_HOME": str(codex.resolve())}
            for environment in ({**roots, "CLAUDE_CODE_VERSION": "2.1.209"}, {**roots, "OPENCODE_VERSION": "1.18.0"}, {**roots, "CODEX_VERSION": "0.144.5"}):
                result = self.cli("install", "--agent", "auto", "--scope", "user", "--allow-development-checkout", environment=environment)
                self.assertEqual(result.returncode, 0, result.stderr)
            multiple = self.cli("install", "--agent", "auto", "--scope", "user", "--allow-development-checkout", environment={**roots, "CLAUDE_CODE_VERSION": "2.1.209", "CODEX_VERSION": "0.144.5"})
            self.assertEqual(multiple.returncode, 2)

    def test_instruction_merge_preserves_unmarked_content_replaces_block_and_rejects_duplicates(self):
        root = self.fixture("opencode", "user")
        original = "# My instructions\n\nKeep this exact.\n"
        (root / "AGENTS.md").write_text(original)
        self.apply("install", "opencode", "user", root)
        installed = (root / "AGENTS.md").read_text()
        self.assertIn(original.rstrip(), installed)
        self.assertEqual(installed.count("<!-- shahinkit:begin instructions -->"), 1)
        self.apply("update", "opencode", "user", root)
        self.apply("uninstall", "opencode", "user", root)
        self.assertEqual((root / "AGENTS.md").read_text(), original)
        (root / "AGENTS.md").write_text("<!-- shahinkit:begin instructions -->x<!-- shahinkit:end instructions -->\n<!-- shahinkit:begin instructions -->x<!-- shahinkit:end instructions -->")
        rejected = self.command("install", "opencode", "user", root)
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("duplicate or malformed", rejected.stderr)

    def test_apply_requires_matching_preview_digest_and_changed_plan_is_rejected(self):
        root = self.fixture("claude-code", "user")
        missing = self.command("install", "claude-code", "user", root, "--apply", "--trust-host")
        self.assertEqual(missing.returncode, 2)
        preview = self.command("install", "claude-code", "user", root)
        digest = self.preview_digest(preview)
        mismatch = self.command("install", "claude-code", "user", root, "--apply", "--trust-host", "--preview-digest", "0" * 64)
        self.assertEqual(mismatch.returncode, 2)
        (root / "CLAUDE.md").write_text((root / "CLAUDE.md").read_text() + "changed\n")
        changed = self.command("install", "claude-code", "user", root, "--apply", "--trust-host", "--preview-digest", digest)
        self.assertEqual(changed.returncode, 2)
        self.assertIn("preview digest mismatch", changed.stderr)

    def test_basic_memory_default_off_opt_in_complete_and_course_rag_paths_are_scope_resolved(self):
        root = self.fixture("codex", "user")
        self.apply("install", "codex", "user", root)
        config = (root / "config.toml").read_text()
        self.assertIn("enabled = false", config)
        self.assertFalse((root / ".shahinkit-state/basic-memory/config.json").exists())
        self.apply("update", "codex", "user", root, "--with-basic-memory")
        config = (root / "config.toml").read_text()
        self.assertIn("enabled = true", config)
        local = json.loads((root / ".shahinkit-state/basic-memory/config.json").read_text())
        project = local["projects"]["shahinkit-local"]
        self.assertEqual(project["mode"], "local")
        self.assertEqual(Path(project["path"]), (root / ".shahinkit-state/basic-memory/project").resolve())
        skill = (root / "home/.agents/skills/course-rag/SKILL.md").read_text()
        self.assertIn(str(root / ".shahinkit-data/course-rag"), skill)
        self.assertTrue((root / ".shahinkit-data/course-rag/scripts/build.py").is_file())
        project_root = self.fixture("codex", "project")
        self.apply("install", "codex", "project", project_root)
        project_skill = (project_root / ".agents/skills/course-rag/SKILL.md").read_text()
        self.assertIn(str(project_root.resolve() / ".shahinkit-data/course-rag"), project_skill)

    def test_symlink_swap_rejected_before_uninstall_or_rollback_write(self):
        root = self.fixture("codex", "user")
        self.apply("install", "codex", "user", root)
        target = root / "home/.agents/skills/course-rag/SKILL.md"
        outside = root.parent / "outside"
        outside.write_text("outside")
        target.unlink()
        target.symlink_to(outside)
        preview = self.command("uninstall", "codex", "user", root)
        self.assertEqual(preview.returncode, 2)
        self.assertIn("symlink rejected", preview.stderr)

    def test_path_symlink_provenance_backup_and_manifest_fail_closed(self):
        with self.assertRaises(manage.ManagerError):
            manage.relpath("../escape")
        with self.assertRaises(manage.ManagerError):
            manage.relpath("/absolute")
        root = self.fixture("claude-code", "user")
        outside = root.parent / "outside"
        outside.mkdir()
        shutil.rmtree(root / "skills")
        (root / "skills").symlink_to(outside, target_is_directory=True)
        rejected = self.command("install", "claude-code", "user", root)
        self.assertEqual(rejected.returncode, 2)
        clean = self.fixture("claude-code", "user")
        self.apply("install", "claude-code", "user", clean)
        backup = next((clean / ".shahinkit-backups").glob("*.json"))
        self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o600)
        for index in range(5):
            manage.write_backup(clean.resolve(), [{"base": "root", "kind": "absent", "path": f"x{index}"}])
        self.assertLessEqual(len(list((clean / ".shahinkit-backups").glob("*.json"))), 3)
        manifest = json.loads((ROOT / ".shahinkit-manifest.json").read_text())
        entry = next(item for item in manifest["owned_files"] if item["path"] == "school/scripts/manage.py")
        self.assertEqual(entry["source_sha256"], hashlib.sha256(MANAGER.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
