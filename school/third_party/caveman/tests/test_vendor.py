import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "LOCK.json"
TRUSTED = ROOT.parents[1] / "tests" / "fixtures" / "vendors" / "caveman.json"
FORBIDDEN_RUNTIME = (
    "child_process", "subprocess", "process.env", "os.environ", "fetch(",
    "http://", "https://", "curl ", "wget ", "npx ", "telemetry",
    "postinstall", "install.sh", "install.ps1", "spawn(", "exec("
)
FORBIDDEN_INSTRUCTIONS = ("curl |", "wget |", "npx -y")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CavemanVendorTests(unittest.TestCase):
    def test_locked_files_match(self) -> None:
        locked = json.loads(LOCK.read_text())["files"]
        actual = {
            path.relative_to(ROOT).as_posix(): digest(path)
            for path in ROOT.rglob("*")
            if path.is_file() and path != LOCK and "__pycache__" not in path.parts
        }
        self.assertEqual(actual, locked)

    def test_trusted_fixture_binds_lock_and_provenance(self) -> None:
        trusted = json.loads(TRUSTED.read_text())
        locked = json.loads(LOCK.read_text())
        self.assertEqual(digest(LOCK), trusted["lock_sha256"])
        for key in ("repository", "tag", "commit", "tree", "upstream_selected_files"):
            self.assertEqual(locked[key], trusted[key])
        self.assertEqual(locked["license"], trusted["license"])

        provenance = (ROOT / "PROVENANCE.md").read_text()
        for key in ("repository", "tag", "commit", "tree"):
            self.assertIn(trusted[key], provenance)

    def test_payload_has_no_runtime_escape_hatches(self) -> None:
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix != ".js":
                continue
            content = path.read_text(encoding="utf-8").lower()
            for token in FORBIDDEN_RUNTIME:
                self.assertNotIn(token, content, f"{token!r} in {path}")

    def test_instructions_have_no_remote_execution_examples(self) -> None:
        for path in ROOT.rglob("*.md"):
            content = path.read_text(encoding="utf-8").lower()
            for token in FORBIDDEN_INSTRUCTIONS:
                self.assertNotIn(token, content, f"{token!r} in {path}")

    def test_static_mode_defaults_to_full(self) -> None:
        config = (ROOT / "opencode" / "caveman-config.js").read_text()
        self.assertIn('DEFAULT_MODE = "full"', config)
        self.assertIn("Auto-Clarity", (ROOT / "skills" / "caveman" / "SKILL.md").read_text())
        plugin = (ROOT / "opencode" / "plugin.js").read_text()
        self.assertIn('selectedMode !== "off"', plugin)
        self.assertIn('output.system.push(reinforcementLine(selectedMode))', plugin)


if __name__ == "__main__":
    unittest.main()
