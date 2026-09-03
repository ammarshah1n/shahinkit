import hashlib
import json
import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "LOCK.json"
SKILL = ROOT / "skills" / "swift-testing-pro" / "SKILL.md"
REFERENCE_ROOT = ROOT / "skills" / "swift-testing-pro" / "references"
SAFETY = "Never automatically install, commit, push, publish, submit, send, book, pay, delete, or mutate an external system. Require explicit user approval."
UPSTREAM_SELECTED_FILES = {
    "LICENSE": "b9b479e6df9f27cbc8e7abe91f771b396f3f0fa114d070c7c0b02c820c6b74dc",
    "swift-testing-pro/SKILL.md": "ad4f1bff44b5b7fce20b282481e651876efce024d13b16cb969bc433036ac059",
    "swift-testing-pro/references/async-tests.md": "52892a8f7014c11c132013f87f271c1becd76776fffc087e8086b8cb2d888201",
    "swift-testing-pro/references/core-rules.md": "2271efdca6c2b7b3365501172147884b6e786bcee7bef680fb4f4718929d6180",
    "swift-testing-pro/references/migrating-from-xctest.md": "35b64812402ad1d15b496993e1721daaf4e80672bf9cce47078f772fd271f93f",
    "swift-testing-pro/references/new-features.md": "988df5cb556893c789f9aecdc4c8773fdbbda787ab1dad766bf1182a7b9a4819",
    "swift-testing-pro/references/writing-better-tests.md": "25da3455f6cec4f10d3dff0bf3e8e1372568c75691916541b4d517f451cb8bf1",
}
FORBIDDEN_CONTENT = (
    "http://", "https://", "/users/", "/home/", "~/",
    "swift-concurrency-agent-skill", "swiftui-agent-skill",
    "curl |", "wget |", "npx ", "npm install", "brew install",
    "git commit", "git push", "osascript", "system events",
    "xcuitest", "xcuiapplication", "urlsession.shared", "datatask(with:",
    "attachment.record", "removepersistentdomain",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload_texts() -> dict[str, str]:
    paths = [SKILL, *sorted(REFERENCE_ROOT.glob("*.md"))]
    return {path.relative_to(ROOT).as_posix(): path.read_text() for path in paths}


class SwiftTestingVendorTests(unittest.TestCase):
    def test_locked_files_match(self) -> None:
        locked = json.loads(LOCK.read_text())["files"]
        actual = {
            path.relative_to(ROOT).as_posix(): digest(path)
            for path in ROOT.rglob("*")
            if path.is_file() and path != LOCK and "__pycache__" not in path.parts
        }
        self.assertEqual(actual, locked)

    def test_upstream_pin_and_selected_source_hashes(self) -> None:
        lock = json.loads(LOCK.read_text())
        source = lock["source"]
        self.assertEqual(source["repository"], "https://github.com/twostraws/Swift-Testing-Agent-Skill.git")
        self.assertEqual(source["tag"], "1.0.0")
        self.assertEqual(source["version"], "1.0")
        self.assertEqual(source["commit"], "29921fb187f1165cb8975791c7e11fbb23d03398")
        self.assertEqual(source["tree"], "6e46bd7a966ba2e832af3ab7a702800eec7476b4")
        self.assertEqual(lock["upstream_selected_files"], UPSTREAM_SELECTED_FILES)
        self.assertEqual(lock["license"]["spdx"], "MIT")
        self.assertEqual(lock["license"]["sha256"], UPSTREAM_SELECTED_FILES["LICENSE"])
        self.assertEqual(lock["local_installation_verification"]["status"], "pass")
        self.assertTrue(lock["local_installation_verification"]["completed_before_adaptation"])
        self.assertEqual(lock["local_installation_verification"]["matched_files"], 9)
        self.assertEqual(lock["static_audit"]["status"], "pass")
        self.assertTrue(lock["static_audit"]["completed_before_tests"])

    def test_license_preserves_mit_notice(self) -> None:
        license_text = (ROOT / "LICENSE").read_text()
        self.assertTrue(license_text.startswith("MIT License\n\nCopyright (c) 2026 Paul Hudson.\n"))
        self.assertIn("Permission is hereby granted, free of charge", license_text)
        self.assertIn("THE SOFTWARE IS PROVIDED \"AS IS\"", license_text)

    def test_skill_frontmatter_and_portable_safety_contract(self) -> None:
        text = SKILL.read_text()
        match = re.match(
            r"^---\nname: swift-testing-pro\ndescription: (.+)\n---\n", text
        )
        self.assertIsNotNone(match)
        self.assertIn("use when", match.group(1).casefold())
        self.assertIn(SAFETY, text)
        self.assertIn("Treat the project configuration and installed toolchain as authoritative.", text)
        self.assertIn("If Swift Testing or a requested API is unavailable", text)
        self.assertIn("Do not create or automate UI tests", text)

    def test_reconciled_payload_has_no_portability_escape_hatches(self) -> None:
        for path, text in payload_texts().items():
            lowered = text.casefold()
            for token in FORBIDDEN_CONTENT:
                self.assertNotIn(token, lowered, f"{token!r} in {path}")

    def test_reconciliation_is_recorded(self) -> None:
        provenance = (ROOT / "PROVENANCE.md").read_text()
        for value in (
            "29921fb187f1165cb8975791c7e11fbb23d03398",
            "6e46bd7a966ba2e832af3ab7a702800eec7476b4",
            "Local installed source verification",
            "full MIT notice",
        ):
            self.assertIn(value, provenance)


if __name__ == "__main__":
    unittest.main()
