import re
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ROLES = ("controller", "research", "implementation", "review", "mechanical")
CLAUDE_MODELS = {
    "controller": "opus",
    "research": "sonnet",
    "implementation": "sonnet",
    "review": "sonnet",
    "mechanical": "haiku",
}
CODEX_MODELS = {
    "controller": "gpt-5.6-sol",
    "research": "gpt-5.6-terra",
    "implementation": "gpt-5.6-terra",
    "review": "gpt-5.6-terra",
    "mechanical": "gpt-5.4-mini",
}
OPENCODE_MODELS = {
    "controller": "openai/gpt-5.6-sol",
    "research": "openai/gpt-5.6-terra",
    "implementation": "openai/gpt-5.6-terra",
    "review": "openai/gpt-5.6-terra",
    "mechanical": "openai/gpt-5.4-mini",
}
OPENCODE_STEPS = {"controller": 16, "research": 10, "implementation": 14, "review": 12, "mechanical": 8}
OPENCODE_PERMISSIONS = {
    "controller": {"doom_loop": "ask", "edit": "ask", "bash": "ask", "task": "allow", "external_directory": "deny", "webfetch": "deny", "websearch": "deny"},
    "research": {"doom_loop": "ask", "edit": "deny", "bash": "ask", "task": "deny", "external_directory": "deny", "webfetch": "deny", "websearch": "deny"},
    "implementation": {"doom_loop": "ask", "edit": "ask", "bash": "ask", "task": "deny", "external_directory": "deny", "webfetch": "deny", "websearch": "deny"},
    "review": {"doom_loop": "ask", "edit": "deny", "bash": "ask", "task": "deny", "external_directory": "deny", "webfetch": "deny", "websearch": "deny"},
    "mechanical": {"doom_loop": "ask", "edit": "ask", "bash": "ask", "task": "deny", "external_directory": "deny", "webfetch": "deny", "websearch": "deny"},
}
SEMANTICS = {
    "controller": ("architecture", "privacy", "security", "data-loss", "routing", "final acceptance"),
    "research": ("bounded", "sources", "uncertainty", "final acceptance"),
    "implementation": ("bounded", "verification", "architecture", "final acceptance"),
    "review": ("independent", "review", "final acceptance"),
    "mechanical": ("deterministic", "ambiguity", "final acceptance"),
}


def markdown_frontmatter(path):
    match = re.match(r"^---\n(.*?)\n---\n", path.read_text(), re.S)
    if not match:
        raise AssertionError(f"missing frontmatter: {path}")
    values, permissions, section = {}, {}, None
    for line in match.group(1).splitlines():
        if line.startswith("  ") and section == "permission":
            key, value = line.strip().split(": ", 1)
            permissions[key] = value
        elif ":" in line:
            key, value = line.split(":", 1)
            section = key
            values[key] = value.strip()
    values["permission"] = permissions
    return values


class AgentParityTests(unittest.TestCase):
    def test_all_hosts_have_exact_roles_and_explicit_models(self):
        claude = ROOT / "claude-code" / "agents"
        codex = ROOT / "codex" / "config" / "agents"
        opencode = ROOT / "opencode" / ".opencode" / "agents"
        self.assertEqual({path.stem for path in claude.glob("*.md")}, set(ROLES))
        self.assertEqual({path.stem for path in codex.glob("*.toml")}, set(ROLES))
        self.assertEqual({path.stem for path in opencode.glob("*.md")}, set(ROLES))
        for role in ROLES:
            self.assertEqual(markdown_frontmatter(claude / f"{role}.md")["name"], role)
            self.assertEqual(markdown_frontmatter(claude / f"{role}.md")["model"], CLAUDE_MODELS[role])
            agent = tomllib.loads((codex / f"{role}.toml").read_text())
            self.assertEqual(agent["name"], role)
            self.assertEqual(agent["model"], CODEX_MODELS[role])
            self.assertIn(agent["model_reasoning_effort"], {"low", "high"})
            self.assertEqual(markdown_frontmatter(opencode / f"{role}.md")["model"], OPENCODE_MODELS[role])

    def test_role_boundaries_are_semantically_aligned_and_non_inheriting(self):
        for role in ROLES:
            contents = [
                (ROOT / "claude-code" / "agents" / f"{role}.md").read_text().lower(),
                (ROOT / "codex" / "config" / "agents" / f"{role}.toml").read_text().lower(),
                (ROOT / "opencode" / ".opencode" / "agents" / f"{role}.md").read_text().lower(),
            ]
            for content in contents:
                for term in SEMANTICS[role]:
                    self.assertIn(term, content, f"{role}: {term}")
                self.assertNotRegex(content, r"(?m)^\s*(inherit|inherits_from|model_from_role)\s*[:=]")
                self.assertNotRegex(content, r"/(?:users|home)/|~/(?:documents|library)|\bsk-[a-z0-9]|begin [a-z ]*private key")
                self.assertNotIn("shahinkit-", content)

    def test_opencode_uses_native_modes_and_unchanged_bounded_permissions(self):
        agents = ROOT / "opencode" / ".opencode" / "agents"
        for role in ROLES:
            agent = markdown_frontmatter(agents / f"{role}.md")
            self.assertEqual(agent["mode"], "primary" if role == "controller" else "subagent")
            self.assertEqual(int(agent["maxSteps"]), OPENCODE_STEPS[role])
            self.assertEqual(agent["permission"], OPENCODE_PERMISSIONS[role])


if __name__ == "__main__":
    unittest.main()
