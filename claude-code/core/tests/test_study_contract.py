import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "claude-code" / "core" / "shared" / "skills" / "study" / "SKILL.md"
MARKER = "<!-- shahinkit-study:v1 -->"
START = "<!-- shahinkit-study:begin -->"
END = "<!-- shahinkit-study:end -->"


class StudyContractTests(unittest.TestCase):
    def setUp(self):
        self.skill = SKILL.read_text()
        self.manifest = json.loads((ROOT / ".shahinkit-manifest.json").read_text())
        self.renders = {
            host: json.loads((ROOT / host / "render-manifest.json").read_text())
            for host in ("claude-code", "opencode", "codex")
        }

    def test_all_adapters_render_one_canonical_study_skill(self):
        self.assertRegex(self.skill, r"(?m)^name: study$")
        self.assertEqual(self.skill.count("# Study"), 1)
        self.assertIn("study", self.renders["claude-code"]["shared"]["skills"])
        for host in ("opencode", "codex"):
            self.assertIn("study", self.renders[host]["shared_skills"])
        claude = {(item["source"], item["destination"]) for item in self.renders["claude-code"]["copies"]}
        self.assertIn(("claude-code/core/shared/skills/study/SKILL.md", "skills/study/SKILL.md"), claude)

    def test_opencode_wrapper_only_delegates_to_shared_skill(self):
        wrapper = (ROOT / "opencode/.opencode/commands/study.md").read_text()
        self.assertRegex(wrapper, r"^---\ndescription: .+\nagent: controller\npermalink: opencode-command-files/study\n---\n")
        self.assertEqual(wrapper.count("Use `study` skill."), 1)
        self.assertIn("$ARGUMENTS", wrapper)
        self.assertNotIn("<!-- shahinkit-study", wrapper)

    def test_canonical_schema_and_safety_requirements_are_explicit(self):
        for required in (MARKER, START, END, "shahinkit_study: 1", "vault_root: ."):
            self.assertIn(required, self.skill)
        canonical = re.search(r"```markdown\n(?P<content>.*?)\n```", self.skill, re.S)
        self.assertIsNotNone(canonical)
        self.assertEqual(
            canonical.group("content"),
            "---\nshahinkit_study: 1\nvault_root: .\n---\n"
            "<!-- shahinkit-study:v1 -->\n<!-- shahinkit-study:begin -->\n"
            "subjects: []\n<!-- shahinkit-study:end -->",
        )
        self.assertIn("Current note path", self.skill)
        self.assertIn("Working directory", self.skill)
        for required in (
            "both roots resolve and differ", "existing Obsidian vault",
            "regular non-symlink file", "lstat", "case-insensitive duplicates",
            "resolved destination outside", "CONFIRM STUDY SETUP", "re-check",
            "preserving every byte outside block", "not-supplied-yet",
            "user-authorised-external", "location_kind: external",
            "safely YAML-decode it to a scalar string", "canonical/real path",
            "JSON-style double-quoted YAML scalar", "Never interpolate",
            "exclusive-create", "file identity", "same-directory",
            "atomic", "unsupported no-follow/exclusive/identity",
            "portable fail-closed contract",
        ):
            self.assertIn(required, self.skill)

    def test_no_rag_dependency_or_sample_course_payload(self):
        self.assertIn("never invokes or depends on Course-RAG", self.skill)
        self.assertNotIn("course-rag/scripts", self.skill)
        self.assertNotIn("sqlite", self.skill.lower())
        self.assertNotRegex(self.skill, r"(?im)^\s*-\s+(biology|history|english|mathematics)\b")

    def test_manifest_and_acceptance_checklist_are_complete_and_synced(self):
        owned = {item["path"]: item for item in self.manifest["owned_files"]}
        self.assertIn("claude-code/core/shared/skills/study/SKILL.md", owned)
        self.assertIn("claude-code/core/docs/STUDY-ACCEPTANCE-v1.md", owned)
        for path, entry in owned.items():
            candidate = ROOT / path
            self.assertTrue(candidate.is_file(), path)
            self.assertEqual(entry["source_sha256"], hashlib.sha256(candidate.read_bytes()).hexdigest(), path)
            self.assertEqual(entry["render_sha256"], hashlib.sha256(candidate.read_bytes()).hexdigest(), path)
        for host in ("claude-code", "opencode", "codex"):
            actual = {
                path.relative_to(ROOT / host).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (ROOT / host).rglob("*")
                if path.is_file()
                and not (host == "claude-code" and path.relative_to(ROOT / host).parts[0] == "core")
            }
            self.assertEqual(self.manifest["adapter_inputs"][host], actual)
        checklist = (ROOT / "claude-code" / "core" / "docs" / "STUDY-ACCEPTANCE-v1.md").read_text()
        for case in (
            "Clean vault", "Existing folders/files", "Unmarked Study.md collision",
            "Malformed or duplicate markers", "Study.md symlink or nonregular",
            "Subject symlink or non-directory", "Traversal or duplicate", "No content yet",
            "External reference", "Reconfigure preserves outside notes",
            "Target changes after confirmation", "Conflicting note/cwd roots",
            "Existing mapping traversal", "Existing mapping symlink folder",
            "Existing mapping duplicate folder", "Existing mapping missing or non-directory",
            "YAML scalar escaping round-trip", "Symlinked vault root component",
            "Reconfiguration target swap", "Unsupported safe write tools",
        ):
            self.assertIn(case, checklist)

    def test_readme_says_lifecycle_commands_are_explicit(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn("Hooks never run Prime or Wrap Up automatically", readme)
        self.assertIn("do **not** record prompts", readme)


if __name__ == "__main__":
    unittest.main()
