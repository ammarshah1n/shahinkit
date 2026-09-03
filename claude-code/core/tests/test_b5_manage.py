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
import tomllib
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
MANAGER = ROOT / "claude-code" / "core" / "scripts" / "manage.py"
spec = importlib.util.spec_from_file_location("shahinkit_manage", MANAGER)
manage = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = manage
spec.loader.exec_module(manage)


class B5ManagerTests(unittest.TestCase):
    def test_duplicate_render_destinations_fail_closed(self):
        duplicate = [
            {"path": Path("/tmp/same"), "relative": "first", "data": b"one"},
            {"path": Path("/tmp/same"), "relative": "second", "data": b"one"},
        ]
        with self.assertRaisesRegex(manage.ManagerError, "duplicate render destination"):
            manage.reject_duplicate_outputs(duplicate)

    def fixture(self, agent, scope):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name) / "destination"
        shutil.copytree(ROOT / "claude-code" / "core" / "tests" / "fixtures" / "hosts" / agent / scope, root)
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
                    if agent == "claude-code":
                        settings = root / ("settings.json" if scope == "user" else ".claude/settings.json")
                        hooks = json.loads(settings.read_text())["hooks"]
                        self.assertEqual(set(hooks), {"SessionStart", "UserPromptSubmit", "SubagentStart"})
                        script = root / ("hooks/shahinkit_hook.py" if scope == "user" else ".claude/hooks/shahinkit_hook.py")
                        self.assertTrue(script.is_file())
                        self.assertIn(str(script), json.dumps(hooks))
                        self.assertNotIn("$HOME", json.dumps(hooks))
                    elif agent == "codex":
                        hooks_path = root / ("hooks.json" if scope == "user" else ".codex/hooks.json")
                        hooks = json.loads(hooks_path.read_text())["hooks"]
                        self.assertEqual(set(hooks), {"SessionStart", "UserPromptSubmit", "SubagentStart"})
                        script = root / ("hooks/shahinkit_hook.py" if scope == "user" else ".codex/hooks/shahinkit_hook.py")
                        self.assertTrue(script.is_file())
                        self.assertIn(str(script), json.dumps(hooks))
                        self.assertNotIn("$HOME", json.dumps(hooks))
                    else:
                        config = json.loads((root / "opencode.jsonc").read_text())
                        prefix = "plugins" if scope == "user" else ".opencode/plugins"
                        self.assertNotIn(f"./{prefix}/portable-gates.mjs", config.get("plugin", []))
                        self.assertTrue((root / prefix / "portable-gates.mjs").is_file())
                        self.assertTrue((root / prefix / "shahinkit-guard.mjs").is_file())
                        skill_root = "skills" if scope == "user" else ".opencode/skills"
                        self.assertTrue((root / skill_root / "course-rag/SKILL.md").is_file())
                        self.assertTrue((root / ".shahinkit-data/course-rag/scripts/build.py").is_file())
                        command_root = "commands" if scope == "user" else ".opencode/commands"
                        self.assertFalse((root / command_root / "study.md").read_bytes().endswith(b"\n"))
                    self.apply("update", agent, scope, root, "--without-caveman")
                    self.apply("rollback", agent, scope, root)
                    restored = json.loads((root / ".shahinkit-install-receipt.json").read_text())
                    self.assertTrue(restored["features"]["caveman"])
                    self.apply("uninstall", agent, scope, root)
                    self.assertFalse((root / ".shahinkit-install-receipt.json").exists())

    def test_vendor_sidecars_cover_all_host_lifecycles_and_receipt_digests(self):
        mappings = json.loads((ROOT / "claude-code/core/tests/fixtures/vendor-file-mappings.json").read_text())
        with tempfile.TemporaryDirectory() as temporary:
            fixture_root = Path(temporary)
            source_files = {
                f"{mapping['source_root']}/{name}": fixture_root / mapping["source_root"] / name
                for mapping in mappings
                for name in mapping["files"]
            }
            for source, path in source_files.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(f"initial {source}\n".encode())
            original_read_source = manage.read_source

            def fixture_read_source(source):
                path = source_files.get(source)
                return path.read_bytes() if path else original_read_source(source)

            with mock.patch.object(manage, "read_source", side_effect=fixture_read_source):
                for agent in ("claude-code", "opencode", "codex"):
                    for scope in ("user", "project"):
                        with self.subTest(agent=agent, scope=scope):
                            for source, path in source_files.items():
                                path.write_bytes(f"initial {source}\n".encode())
                            root = self.fixture(agent, scope).resolve()
                            home = root / "home"
                            features = {"ponytail": True, "caveman": True, "basic-memory": False}
                            outputs = manage.outputs_for(agent, scope, root, home, features)
                            receipt = manage.apply_plan(
                                root,
                                home,
                                agent,
                                scope,
                                features,
                                {"kind": "test"},
                                manage.changed_plan(outputs, root, home),
                                None,
                            )
                            skill_root = json.loads((ROOT / agent / "render-manifest.json").read_text())["render_rules"]["scope_roots"][scope]["skills"]
                            for mapping in mappings:
                                for name in mapping["files"]:
                                    source = f"{mapping['source_root']}/{name}"
                                    base = "home" if skill_root.startswith("$HOME/") else "root"
                                    destination = f"{skill_root.removeprefix('$HOME/')}/{mapping['skill']}/{name}"
                                    item = next(item for item in receipt["owned"] if item["base"] == base and item["path"] == destination)
                                    self.assertEqual(item["sha256"], hashlib.sha256(source_files[source].read_bytes()).hexdigest())
                                    self.assertEqual(self.local_path(root, item).read_bytes(), source_files[source].read_bytes())

                            changed_source = next(source for source in source_files if source.endswith("references/async-tests.md"))
                            source_files[changed_source].write_bytes(b"updated vendor sidecar\n")
                            updated_outputs = manage.outputs_for(agent, scope, root, home, features)
                            update_plan = manage.changed_plan(updated_outputs, root, home, receipt)
                            self.assertTrue(any(change["source"] == changed_source for change in update_plan))
                            updated_receipt = manage.apply_plan(root, home, agent, scope, features, {"kind": "test"}, update_plan, receipt)
                            updated_item = next(item for item in updated_receipt["owned"] if item["path"].endswith(f"/{mappings[0]['skill']}/references/async-tests.md"))
                            self.assertEqual(updated_item["sha256"], hashlib.sha256(b"updated vendor sidecar\n").hexdigest())

                            manage.rollback(root, home, updated_receipt)
                            restored = manage.verify_receipt(root)
                            restored_item = next(item for item in restored["owned"] if item["path"].endswith(f"/{mappings[0]['skill']}/references/async-tests.md"))
                            self.assertEqual(self.local_path(root, restored_item).read_bytes(), f"initial {changed_source}\n".encode())
                            manage.remove_owned(root, home, restored)
                            self.assertFalse(manage.receipt_path(root).exists())
                            self.assertFalse(self.local_path(root, restored_item).exists())

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
            roots = {"HOME": str(home.resolve()), "CLAUDE_CONFIG_DIR": str(claude.resolve()), "XDG_CONFIG_HOME": str((home / "config").resolve()), "CODEX_HOME": str(codex.resolve())}
            for environment in ({**roots, "CLAUDE_CODE_VERSION": "2.1.209"}, {**roots, "OPENCODE_VERSION": "1.18.0"}, {**roots, "CODEX_VERSION": "0.145.0"}):
                result = self.cli("install", "--agent", "auto", "--scope", "user", "--allow-development-checkout", environment=environment)
                self.assertEqual(result.returncode, 0, result.stderr)
            multiple = self.cli("install", "--agent", "auto", "--scope", "user", "--allow-development-checkout", environment={**roots, "CLAUDE_CODE_VERSION": "2.1.209", "CODEX_VERSION": "0.145.0"})
            self.assertEqual(multiple.returncode, 2)

    def test_instruction_merge_preserves_unmarked_content_replaces_block_and_rejects_duplicates(self):
        root = self.fixture("opencode", "user")
        original = "# My instructions\n\nKeep this exact.\n"
        (root / "AGENTS.md").write_text(original)
        self.apply("install", "opencode", "user", root)
        installed = (root / "AGENTS.md").read_text()
        self.assertIn(original.rstrip(), installed)
        self.assertEqual(installed.count("<!-- shahinkit:begin instructions -->"), 1)
        preview = self.command("update", "opencode", "user", root)
        self.preview_digest(preview)
        self.assertNotIn("managed-change: root:AGENTS.md", preview.stdout)
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
        entry = next(item for item in manifest["owned_files"] if item["path"] == "claude-code/core/scripts/manage.py")
        self.assertEqual(entry["source_sha256"], hashlib.sha256(MANAGER.read_bytes()).hexdigest())

    def test_receipt_write_failure_restores_destination_and_leaves_no_ownership_gap(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "destination"
            home = root / "home"
            home.mkdir(parents=True)
            target = root / "settings.json"
            target.write_bytes(b"before\n")
            plan = [{
                "path": target,
                "base": "root",
                "relative": "settings.json",
                "old": b"before\n",
                "data": b"after\n",
                "ownership": {"kind": "file"},
            }]
            original = manage.write_atomic
            failed = False

            def fail_receipt_once(path, data, mode=0o600, **kwargs):
                nonlocal failed
                if path == manage.receipt_path(root) and not failed:
                    failed = True
                    raise OSError("simulated receipt failure")
                return original(path, data, mode, **kwargs)

            with mock.patch.object(manage, "write_atomic", side_effect=fail_receipt_once):
                with self.assertRaisesRegex(OSError, "simulated receipt failure"):
                    manage.apply_plan(root, home, "claude-code", "user", {"ponytail": True, "caveman": True, "basic-memory": False}, {"kind": "test"}, plan, None)
            self.assertEqual(target.read_bytes(), b"before\n")
            self.assertFalse(manage.receipt_path(root).exists())

    def test_preserve_existing_keeps_regular_skill_and_symlink_untouched(self):
        claude = self.fixture("claude-code", "user")
        claude_prime = claude / "skills/prime/SKILL.md"
        claude_prime.parent.mkdir(parents=True)
        claude_prime.write_text("personal prime\n")
        self.apply("install", "claude-code", "user", claude, "--preserve-existing")
        self.assertEqual(claude_prime.read_text(), "personal prime\n")
        claude_receipt = json.loads((claude / ".shahinkit-install-receipt.json").read_text())
        self.assertTrue(claude_receipt["preserve_existing"])
        self.assertIn({"base": "root", "path": "skills/prime/SKILL.md"}, claude_receipt["preserved"])
        self.apply("uninstall", "claude-code", "user", claude)
        self.assertEqual(claude_prime.read_text(), "personal prime\n")

        opencode = self.fixture("opencode", "user")
        external = opencode / "existing-prime"
        external.mkdir()
        (external / "SKILL.md").write_text("linked personal prime\n")
        (opencode / "skills/prime").symlink_to(external, target_is_directory=True)
        self.apply("install", "opencode", "user", opencode, "--preserve-existing")
        self.assertTrue((opencode / "skills/prime").is_symlink())
        self.assertEqual((external / "SKILL.md").read_text(), "linked personal prime\n")
        opencode_receipt = json.loads((opencode / ".shahinkit-install-receipt.json").read_text())
        self.assertIn({"base": "root", "path": "skills/prime/SKILL.md"}, opencode_receipt["preserved"])
        self.apply("uninstall", "opencode", "user", opencode)
        self.assertTrue((opencode / "skills/prime").is_symlink())

    def test_preserve_existing_keeps_symlinked_claude_settings_untouched(self):
        root = self.fixture("claude-code", "user")
        settings = root / "settings.json"
        external = root.parent / "personal-settings.json"
        external.write_text('{"personal":true}\n')
        settings.unlink()
        settings.symlink_to(external)
        self.apply("install", "claude-code", "user", root, "--preserve-existing")
        self.assertTrue(settings.is_symlink())
        self.assertEqual(external.read_text(), '{"personal":true}\n')
        receipt = json.loads((root / ".shahinkit-install-receipt.json").read_text())
        self.assertIn({"base": "root", "path": "settings.json"}, receipt["preserved"])
        self.apply("uninstall", "claude-code", "user", root)
        self.assertTrue(settings.is_symlink())

    def test_atomic_write_rechecks_preimage_at_replace_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary).resolve() / "target"
            target.write_bytes(b"planned")
            original = manage.read_leaf
            raced = False

            def race(directory, name, path):
                nonlocal raced
                if not raced:
                    raced = True
                    target.write_bytes(b"concurrent")
                return original(directory, name, path)

            with mock.patch.object(manage, "read_leaf", side_effect=race):
                with self.assertRaisesRegex(manage.ManagerError, "planned preimage changed"):
                    manage.write_atomic(target, b"replacement", expected=b"planned")
            self.assertEqual(target.read_bytes(), b"concurrent")
            self.assertEqual(list(target.parent.glob(".shahinkit-tmp-*")), [])

    def test_update_adopts_exact_next_verified_file_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            target = root / "command.md"
            target.write_bytes(b"next verified source\n")
            output = {"source": "test", "path": target, "base": "root", "relative": "command.md", "data": b"next verified source\n", "kind": "file"}
            prior = {"owned": [{"base": "root", "path": "command.md", "sha256": hashlib.sha256(b"prior source\n").hexdigest(), "kind": "file"}]}
            manage.current_owned_unchanged(root, root / "home", prior, [output])
            plan = manage.changed_plan([output], root, root / "home", prior, preserve_existing=True)
            self.assertEqual(len(plan), 1)
            self.assertEqual(plan[0]["old"], plan[0]["data"])

    def test_preserve_existing_merges_only_missing_codex_tables(self):
        root = self.fixture("codex", "user")
        config = root / "config.toml"
        config.write_text(config.read_text() + """
[agents]
max_threads = 3

[mcp_servers.basic-memory]
command = "personal-memory"
enabled = true
""")
        self.apply("install", "codex", "user", root, "--preserve-existing")
        parsed = tomllib.loads(config.read_text())
        self.assertEqual(parsed["agents"]["max_threads"], 3)
        self.assertIn("controller", parsed["agents"])
        self.assertEqual(parsed["mcp_servers"]["basic-memory"], {"command": "personal-memory", "enabled": True})
        self.apply("uninstall", "codex", "user", root)
        restored = tomllib.loads(config.read_text())
        self.assertEqual(restored["agents"], {"max_threads": 3})
        self.assertEqual(restored["mcp_servers"]["basic-memory"], {"command": "personal-memory", "enabled": True})

    def test_preserve_existing_leaves_jsonc_config_byte_exact(self):
        root = self.fixture("opencode", "user")
        config = root / "opencode.jsonc"
        original = b'{\n  // personal comment\n  "$schema": "https://opencode.ai/config.json",\n  "plugin": [],\n}\n'
        config.write_bytes(original)
        self.apply("install", "opencode", "user", root, "--preserve-existing")
        self.assertEqual(config.read_bytes(), original)
        receipt = json.loads((root / ".shahinkit-install-receipt.json").read_text())
        self.assertIn({"base": "root", "path": "opencode.jsonc"}, receipt["preserved"])
        self.apply("uninstall", "opencode", "user", root)
        self.assertEqual(config.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
