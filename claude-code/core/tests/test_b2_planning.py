import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILLS = ("idea", "plan", "plans", "mission", "deep-idea", "deep-plan", "delegation-routing")


class B2PlanningSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture_root = ROOT / "claude-code" / "core" / "tests" / "fixtures" / "b2" / "planning"
        cls.capabilities = json.loads((fixture_root / "capabilities.json").read_text())
        cls.excluded_terms = json.loads((fixture_root / "excluded-terms.json").read_text())

    def skill_text(self, skill):
        return (ROOT / "claude-code" / "core" / "shared" / "skills" / skill / "SKILL.md").read_text()

    def test_complete_canonical_skill_family_has_portable_frontmatter(self):
        self.assertEqual(set(self.capabilities), set(SKILLS))
        for skill in SKILLS:
            text = self.skill_text(skill)
            match = re.match(r"^---\nname: ([a-z-]+)\ndescription: (.+)\n---\n", text)
            self.assertIsNotNone(match, skill)
            self.assertEqual(match.group(1), skill)
            self.assertTrue(match.group(2).strip(), skill)

    def test_skills_hold_required_planning_capabilities(self):
        for skill, required_terms in self.capabilities.items():
            text = self.skill_text(skill)
            for term in required_terms:
                self.assertIn(term.casefold(), text.casefold(), f"{skill}: {term}")

    def test_core_skills_exclude_host_and_personal_payload(self):
        for skill in SKILLS:
            text = self.skill_text(skill)
            for term in self.excluded_terms:
                self.assertNotIn(term, text, f"{skill}: {term}")

    def test_plan_family_preserves_explicit_go_and_no_pre_go_implementation(self):
        for skill in ("plan", "deep-plan", "deep-idea"):
            text = self.skill_text(skill)
            self.assertIn("explicit GO", text, skill)
            self.assertRegex(text, r"(?i)(does not implement|No implementation source is written|Implementation starts only)", skill)

    def test_plans_requires_two_unwaivable_gates_before_implementation(self):
        text = self.skill_text("plans")
        self.assertIn("research and plan production only", text)
        self.assertIn("second explicit `GO` always authorizes implementation", text)
        self.assertIn("prior authorization cannot waive this gate", text)
        self.assertIn("No implementation starts before that second explicit `GO`", text)

    def test_delegation_roles_match_shared_schema(self):
        schema = json.loads((ROOT / "claude-code" / "core" / "shared" / "models" / "roles.schema.json").read_text())
        schema_roles = set(schema["$defs"]["roles"]["required"])
        text = self.skill_text("delegation-routing")
        for role in schema_roles:
            self.assertIn(f"`{role}`", text)


if __name__ == "__main__":
    unittest.main()
