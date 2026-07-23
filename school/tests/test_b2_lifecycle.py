import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "school" / "tests" / "fixtures" / "b2" / "lifecycle"


class B2LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((FIXTURES / "valid-skill-names.json").read_text())
        self.capabilities = json.loads((FIXTURES / "capabilities.json").read_text())
        self.forbidden = json.loads((FIXTURES / "forbidden-content.json").read_text())["terms"]

    def skill(self, name):
        return (ROOT / "school" / "shared" / "skills" / name / "SKILL.md").read_text()

    def test_complete_host_neutral_skill_family(self):
        for name in self.contract["skills"]:
            content = self.skill(name)
            self.assertIn(f"name: {name}", content)
            self.assertIn("description:", content)

    def test_each_lifecycle_skill_has_capability_assertions(self):
        self.assertEqual(set(self.capabilities), set(self.contract["skills"]))
        for name, required_terms in self.capabilities.items():
            content = self.skill(name).casefold()
            for term in required_terms:
                self.assertIn(term.casefold(), content, f"{name}: {term}")

    def test_markdown_is_authoritative_and_basic_memory_optional(self):
        content = self.skill("memory")
        self.assertIn("Markdown files are human-readable source of truth.", content)
        self.assertIn("Basic Memory is optional", content)
        self.assertIn("Never store or copy raw transcripts", content)

    def test_lifecycle_has_single_state_authorities(self):
        memory = self.skill("memory")
        router = self.skill("context-router")
        wrap_up = self.skill("wrap-up")
        for content in (memory, router, wrap_up):
            self.assertIn("PROJECT_STATE.md", content)
            self.assertIn("NEXT.md", content)
        self.assertIn("Do not duplicate current state across files.", memory)
        self.assertIn("Do not write same item to multiple state authorities.", router)
        self.assertIn("remains current-state authority", wrap_up)

    def test_prime_is_read_only_and_miniwrap_stays_small(self):
        prime = self.skill("prime")
        miniwrap = self.skill("miniwrap")
        self.assertIn("Read-only", prime)
        self.assertIn("do not create, edit, move, delete, install, index, sync, commit", prime)
        self.assertIn("Escalate to `wrap-up`", miniwrap)
        self.assertIn("Do not update `PROJECT_STATE.md`, `NEXT.md`, or `HANDOFF.md`", miniwrap)

    def test_templates_define_each_authority(self):
        expected = {
            "PROJECT_STATE.md": "## Current Status",
            "NEXT.md": "## Restart Action",
            "HANDOFF.md": "## Resume Context",
            "LEARNINGS.md": "## LRN-<YYYYMMDD>-<NNN>",
            "CORRECTIONS.md": "## COR-<YYYYMMDD>-<NNN>",
        }
        for template in self.contract["templates"]:
            content = (ROOT / "school" / "shared" / "memory" / template).read_text()
            self.assertIn("<PROJECT_NAME>", content)
            self.assertIn(expected[template], content)

    def test_portable_content_excludes_private_and_automatic_behavior(self):
        files = [self.skill(name) for name in self.contract["skills"]]
        files.extend((ROOT / "school" / "shared" / "memory" / name).read_text() for name in self.contract["templates"])
        corpus = "\n".join(files).lower()
        for term in self.forbidden:
            self.assertNotIn(term.lower(), corpus, term)

    def test_wrap_up_commit_is_conditional_and_never_pushes_automatically(self):
        content = self.skill("wrap-up")
        self.assertIn("only when user explicitly requests it", content)
        self.assertIn("Never push automatically.", content)


if __name__ == "__main__":
    unittest.main()
