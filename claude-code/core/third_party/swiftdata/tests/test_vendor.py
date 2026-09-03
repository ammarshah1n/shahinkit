import hashlib
import json
import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "LOCK.json"
SKILL = ROOT / "skills" / "swiftdata-pro" / "SKILL.md"
REFERENCES = ROOT / "skills" / "swiftdata-pro" / "references"
SAFETY = "Never automatically install, commit, push, publish, submit, send, book, pay, delete, or mutate an external system. Require explicit user approval."
UPSTREAM_SELECTED_FILES = {
    "LICENSE": "b9b479e6df9f27cbc8e7abe91f771b396f3f0fa114d070c7c0b02c820c6b74dc",
    "swiftdata-pro/SKILL.md": "79164f3bc4942b8ca384057cbe951ca7715aecee4970bea38781d91ddb1c442e",
    "swiftdata-pro/references/class-inheritance.md": "05b22c87e9864a47517ba095c9a870dc320f0e6f4cd85ff9f0b54c5ca356a41d",
    "swiftdata-pro/references/cloudkit.md": "52a549b1713d55be183b79af595d37729426af0abea36ed05f932b718d8ee11f",
    "swiftdata-pro/references/core-rules.md": "8bf45a2af28bfb0648303bb520d3d317d2794b56fcfabe599c4785ccdf02f80a",
    "swiftdata-pro/references/indexing.md": "909167e538461bf517f8fc6b00bfe70d1c8ea19b12a4749088823c275de52a82",
    "swiftdata-pro/references/predicates.md": "623c3195fccdec0ec95c0291223ced7491025b04e59c0b4f4fe5ffd23eb1019b",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SwiftDataVendorTests(unittest.TestCase):
    def test_locked_files_match(self) -> None:
        locked = json.loads(LOCK.read_text())["files"]
        actual = {
            path.relative_to(ROOT).as_posix(): digest(path)
            for path in ROOT.rglob("*")
            if path.is_file() and path != LOCK and "__pycache__" not in path.parts
        }
        self.assertEqual(actual, locked)

    def test_upstream_pin_and_selected_source_hashes(self) -> None:
        locked = json.loads(LOCK.read_text())
        self.assertEqual(locked["repository"], "https://github.com/twostraws/SwiftData-Agent-Skill.git")
        self.assertEqual(locked["version"], "1.0")
        self.assertEqual(locked["commit"], "be7db1864a3a27f0fc1fa7a21d55536370f37818")
        self.assertEqual(locked["tree"], "d2d5ad0172937c0ccb43fa8f6e76218e33258c19")
        self.assertEqual(locked["upstream_selected_files"], UPSTREAM_SELECTED_FILES)
        self.assertEqual(locked["license"]["sha256"], UPSTREAM_SELECTED_FILES["LICENSE"])
        self.assertEqual(digest(ROOT / "LICENSE"), UPSTREAM_SELECTED_FILES["LICENSE"])

    def test_canonical_frontmatter_and_project_authority(self) -> None:
        text = SKILL.read_text()
        frontmatter = re.match(r"^---\n(?P<body>(?:[^\n]+\n)+)---\n", text)
        self.assertIsNotNone(frontmatter)
        self.assertEqual(
            frontmatter.group("body").splitlines(),
            [
                "name: swiftdata-pro",
                "description: Review or improve SwiftData code while preserving the project's declared deployment target and data architecture. Use when reading, writing, or reviewing SwiftData code.",
            ],
        )
        self.assertIn("The project's declared deployment target and architecture are authoritative.", text)
        self.assertIn("If a needed capability is unavailable for that target", text)
        self.assertIn(SAFETY, text)

    def test_version_gates_and_portable_boundaries(self) -> None:
        indexing = (REFERENCES / "indexing.md").read_text()
        inheritance = (REFERENCES / "class-inheritance.md").read_text()
        documents = "\n".join(path.read_text() for path in [SKILL, *sorted(REFERENCES.glob("*.md"))])

        self.assertIn("declared deployment target supports SwiftData indexes", indexing)
        self.assertIn("unavailable for the target", indexing)
        self.assertIn("declared deployment target supports SwiftData model inheritance", inheritance)
        self.assertIn("supports an earlier release", inheritance)
        self.assertIn("Use only CLI tools and project files. Do not automate GUI applications; the human opens apps.", documents)
        self.assertIn("Do not make network calls or mutate external systems unless the user explicitly approves that action.", documents)

        for token in (
            "Swift Concurrency Pro", "SwiftUI Pro", "npx ", "brew install", "curl ", "wget ",
            "osascript", "System Events", "open -a", "http://", "https://", "/Users/", "/home/", "~/",
            "api_key", "secret=", "token=", "password=", "sk-",
        ):
            self.assertNotIn(token.casefold(), documents.casefold(), token)


if __name__ == "__main__":
    unittest.main()
