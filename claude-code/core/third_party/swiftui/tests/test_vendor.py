import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "LOCK.json"
REPOSITORY = "https://github.com/twostraws/SwiftUI-Agent-Skill.git"
COMMIT = "36163743db0f7bc6d64723f0bc0a8fa69d08fc4b"
UPSTREAM_SELECTED_FILES = {
    "LICENSE": "cad4ce365913759559b9fc878f83e0c36b8dc65831c8d5e87d82834f68e7346b",
    "swiftui-pro/SKILL.md": "016a4fb9cad11596fa2038dd3eb4c8ff10b1a054025fe8fea104ad3cc5d9ff89",
    "swiftui-pro/references/accessibility.md": "0752544f0b6042ab87321e774203bb3bfb8c1eb3da0207c46ce4a9162d4456c0",
    "swiftui-pro/references/api.md": "12fa73d65a19c9d08224f925801db8eec914b1cedf5b2f86a38cdda04a66377a",
    "swiftui-pro/references/data.md": "5cc50484c525f748839e12174c065f7ea5fdd4380ce04b6885a906ecd6e6a318",
    "swiftui-pro/references/design.md": "a730e05be38f166f38784cfbceed8b6c28adf174181d8fdd02980f7d8c621391",
    "swiftui-pro/references/hygiene.md": "91d96f45f3ffa02f5553c288415f3c3d5f317cab7d8d9c6c60240ea6c44a2b01",
    "swiftui-pro/references/navigation.md": "a3adb302455993aff85bbb6b5845ed2fcffa137c8b2ded99c937f3e4b7fcd77b",
    "swiftui-pro/references/performance.md": "1b503e3807e216d6b34b45f18bfba89214cea2fa1b88dd7ae8f482ebf0f03616",
    "swiftui-pro/references/swift.md": "8c31c5f5f99b3fa9586f0260cd1a4b1688dc7bda5e8de2891eb3f9d6a791125a",
    "swiftui-pro/references/views.md": "87cdd3d96e8e562aefe35070a59664e3536cfcc014bd8437cff603477f7e5a1d",
}
SAFETY_SENTENCE = (
    "Never automatically install, commit, push, publish, submit, send, book, "
    "pay, delete, or mutate an external system. Require explicit user approval."
)
FORBIDDEN_PAYLOAD = (
    "ios 26",
    "swift 6.2",
    "http://",
    "https://",
    "curl ",
    "wget ",
    "npx ",
    "npm install",
    "brew install",
    "/users/",
    "~/",
    "osascript",
    "system events",
    "open -a",
    "renderpreview",
    "documentationsearch",
    "xcode mcp",
    "swiftdata-agent-skill",
    "swift-concurrency-agent-skill",
    "swift-testing-agent-skill",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SwiftUIVendorTests(unittest.TestCase):
    def test_locked_files_match(self) -> None:
        locked = json.loads(LOCK.read_text())["files"]
        actual = {
            path.relative_to(ROOT).as_posix(): digest(path)
            for path in ROOT.rglob("*")
            if path.is_file() and path != LOCK and "__pycache__" not in path.parts
        }
        self.assertEqual(actual, locked)

    def test_lock_pins_verified_upstream_selection(self) -> None:
        lock = json.loads(LOCK.read_text())
        self.assertEqual(lock["repository"], REPOSITORY)
        self.assertEqual(lock["commit"], COMMIT)
        self.assertEqual(lock["version"], "1.0")
        self.assertEqual(lock["license"]["spdx"], "MIT")
        self.assertEqual(lock["upstream_selected_files"], UPSTREAM_SELECTED_FILES)
        self.assertEqual(lock["license"]["sha256"], UPSTREAM_SELECTED_FILES["LICENSE"])

        provenance = (ROOT / "PROVENANCE.md").read_text()
        for value in (REPOSITORY, COMMIT, "Historical skill version: `1.0`"):
            self.assertIn(value, provenance)

    def test_payload_is_portable_and_self_contained(self) -> None:
        skill = (ROOT / "skills" / "swiftui-pro" / "SKILL.md").read_text()
        self.assertRegex(
            skill,
            r"\A---\nname: swiftui-pro\ndescription: [^\n]+\n---\n",
        )
        frontmatter = skill.split("---", 2)[1].strip().splitlines()
        self.assertEqual(len(frontmatter), 2)
        self.assertIn(SAFETY_SENTENCE, skill)
        self.assertIn("deployment target", skill)
        self.assertIn("toolchain", skill)
        self.assertIn("unavailable", skill)
        self.assertIn("does not require any companion skill", skill)

        for path in (ROOT / "skills").rglob("*.md"):
            content = path.read_text(encoding="utf-8").lower()
            for token in FORBIDDEN_PAYLOAD:
                self.assertNotIn(token, content, f"{token!r} in {path}")

    def test_only_declared_markdown_guidance_is_vendored(self) -> None:
        actual = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "skills" / "swiftui-pro").rglob("*")
            if path.is_file()
        }
        expected = {
            "skills/swiftui-pro/SKILL.md",
            "skills/swiftui-pro/LICENSE",
            *(
                f"skills/swiftui-pro/references/{name}.md"
                for name in (
                    "accessibility",
                    "api",
                    "data",
                    "design",
                    "hygiene",
                    "navigation",
                    "performance",
                    "swift",
                    "views",
                )
            ),
        }
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
