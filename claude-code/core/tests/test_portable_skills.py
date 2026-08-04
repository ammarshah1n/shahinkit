import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILLS_ROOT = ROOT / "claude-code" / "core" / "shared" / "skills"
EXISTING_SKILLS = {
    "checkpoint", "context-router", "corrections", "deep-idea", "deep-plan",
    "delegation-routing", "idea", "memory", "miniwrap", "mission", "plan",
    "plans", "prime", "reflect", "self-improve", "session-handoff", "study", "wrap-up",
}
PORTABLE_SKILLS = {
    "audit-tool", "collab", "graphify", "output-style", "parallel-worktrees",
    "research", "skill-builder", "taste-gate", "triage", "watch",
}
SAFETY = "Never automatically install, commit, push, publish, submit, send, book, pay, delete, or mutate an external system. Require explicit user approval."
FORBIDDEN = ("/users/", "/home/", "~/", "timed", "pff", "school", "api_key", "secret=", "token=", "password=", "sk-")


class PortableSkillTests(unittest.TestCase):
    def text(self, name):
        return (SKILLS_ROOT / name / "SKILL.md").read_text()

    def test_exact_portable_skill_set(self):
        actual = {path.parent.name for path in SKILLS_ROOT.glob("*/SKILL.md")}
        self.assertEqual(actual, EXISTING_SKILLS | PORTABLE_SKILLS)

    def test_portable_frontmatter_and_descriptions(self):
        for name in PORTABLE_SKILLS:
            match = re.match(r"^---\nname: ([a-z-]+)\ndescription: (.+)\n---\n", self.text(name))
            self.assertIsNotNone(match, name)
            self.assertEqual(match.group(1), name)
            self.assertIn("use when", match.group(2).casefold(), name)

    def test_portable_safety_and_unavailable_capability_language(self):
        for name in PORTABLE_SKILLS:
            text = self.text(name)
            self.assertIn(SAFETY, text, name)
            self.assertRegex(text, r"(?i)(unavailable|not available)", name)

    def test_portable_content_excludes_personal_paths_and_secrets(self):
        for name in PORTABLE_SKILLS:
            text = self.text(name).casefold()
            for pattern in FORBIDDEN:
                self.assertNotIn(pattern, text, f"{name}: {pattern}")


if __name__ == "__main__":
    unittest.main()
