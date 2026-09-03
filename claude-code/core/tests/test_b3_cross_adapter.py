import hashlib
import importlib.util
import json
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[3]
ROLES = ("controller", "research", "implementation", "review", "mechanical")
SHARED_SKILLS = sorted(path.parent.name for path in (ROOT / "claude-code" / "core" / "shared" / "skills").glob("*/SKILL.md"))
MEMORY = sorted(path.name for path in (ROOT / "claude-code" / "core" / "shared" / "memory").glob("*.md"))
VENDOR_FILE_MAPPINGS = json.loads((ROOT / "claude-code" / "core" / "tests" / "fixtures" / "vendor-file-mappings.json").read_text())


def destination_path(scope_root, home_root, destination, data_root):
    destination = destination.replace("{{SHAHINKIT_DATA_DIR}}", str(data_root))
    if destination.startswith("$HOME/"):
        return home_root / destination.removeprefix("$HOME/")
    return scope_root / destination


BUDGET_SUBSTITUTIONS = {
    "BUDGET_PRESET": "default",
    "DELEGATION_MODE": "strict",
    "INLINE_FILE_LIMIT": "2",
    "INLINE_LINE_LIMIT": "60",
    "CROSS_HOST_ROUTE": "No second host is configured; keep every route on this host.",
    **{
        f"ROLE_MODEL_{role.upper()}": model
        for role, model in {
            r: a["model"]
            for r, a in json.loads(
                (ROOT / "claude-code/core/shared/models/presets.json").read_text()
            )["presets"]["default"]["hosts"]["opencode"].items()
        }.items()
    },
}


def render_feature_template(content, values):
    for mode in ("PONYTAIL_ENABLED", "CAVEMAN_ENABLED"):
        content = re.sub(rf"\{{\{{#{mode}\}}\}}(.*?)\{{\{{/{mode}\}}\}}", lambda match: match.group(1) if values[mode] == "true" else "", content, flags=re.S)
        content = content.replace(f"{{{{{mode}}}}}", values[mode])
    for name, value in BUDGET_SUBSTITUTIONS.items():
        content = content.replace(f"{{{{{name}}}}}", value)
    return content


def assert_safe_manifest_path(testcase, path, root=ROOT):
    testcase.assertTrue(path, "manifest path must not be empty")
    testcase.assertNotIn("\\", path)
    normalized = PurePosixPath(path)
    testcase.assertFalse(normalized.is_absolute(), path)
    testcase.assertEqual(path, normalized.as_posix(), path)
    testcase.assertNotIn("..", normalized.parts, path)
    testcase.assertNotIn(".", normalized.parts, path)
    candidate = root
    testcase.assertFalse(stat.S_ISLNK(candidate.lstat().st_mode), path)
    for part in normalized.parts:
        candidate /= part
        testcase.assertFalse(stat.S_ISLNK(candidate.lstat().st_mode), path)
    return candidate


def assert_safe_render_destination(testcase, scope_root, home_root, data_root, destination):
    testcase.assertIsInstance(destination, str)
    testcase.assertTrue(destination, "render destination must not be empty")
    if destination.startswith("$HOME/"):
        base, relative = home_root, destination.removeprefix("$HOME/")
    elif destination.startswith("{{SHAHINKIT_DATA_DIR}}"):
        base, relative = data_root, destination.removeprefix("{{SHAHINKIT_DATA_DIR}}").lstrip("/")
    else:
        base, relative = scope_root, destination
    testcase.assertNotIn("{{", relative, destination)
    testcase.assertNotIn("\\", relative, destination)
    normalized = PurePosixPath(relative)
    testcase.assertFalse(normalized.is_absolute(), destination)
    testcase.assertEqual(relative, normalized.as_posix(), destination)
    testcase.assertNotIn("..", normalized.parts, destination)
    testcase.assertNotIn(".", normalized.parts, destination)
    candidate = base
    testcase.assertFalse(stat.S_ISLNK(candidate.lstat().st_mode), destination)
    for part in normalized.parts:
        candidate /= part
        try:
            mode = candidate.lstat().st_mode
        except FileNotFoundError:
            continue
        testcase.assertFalse(stat.S_ISLNK(mode), destination)
    testcase.assertTrue(candidate.resolve().is_relative_to(base.resolve()), destination)
    return candidate


def render_destinations(render, scope):
    for item in render.get("context_renders", []) + render.get("copies", []):
        yield item["destination"]
    for item in render.get("adapter_assets", []):
        if isinstance(item, dict):
            yield item["destination"]
    for output in render.get("course_rag", {}).get("outputs", []):
        if "destination" in output:
            yield output["destination"]
        else:
            yield output["destinations"][scope]
    for destination in render.get("course_rag", {}).get("skill_destinations", {}).values():
        yield destination
    patch = render.get("settings_patches")
    if patch:
        yield patch["destinations"][scope]
        yield patch["hook_script_destinations"][scope]
    hooks = render.get("hooks")
    if hooks:
        yield hooks["script_destinations"][scope]
        yield hooks["config_destinations"][scope]
    destinations = render.get("scope_install_destinations", {}).get(scope, render.get("install_destinations", {}))
    yield from destinations.values()
    template = render.get("render", {}).get("scope_templates", {}).get(scope)
    if template:
        yield template["config_destination"]
        yield template["plugin_destination"]
    skill_root = render["render_rules"]["scope_roots"][scope]["skills"]
    for mapping in render.get("vendor_file_mappings", []):
        for name in mapping["files"]:
            yield f"{skill_root}/{mapping['skill']}/{name}"


class B3CrossAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "claude-code" / "core" / "shared" / "models" / "roles.schema.json").read_text())
        cls.claude = json.loads((ROOT / "claude-code/render-manifest.json").read_text())
        cls.codex = json.loads((ROOT / "codex/render-manifest.json").read_text())
        cls.opencode = json.loads((ROOT / "opencode/render-manifest.json").read_text())

    def test_context_and_skill_maps_reference_canonical_assets(self):
        self.assertEqual(sorted(self.claude["shared"]["skills"]), SHARED_SKILLS)
        self.assertEqual(sorted(self.claude["shared"]["memory"]), MEMORY)
        for render in (self.claude, self.codex, self.opencode):
            if render is not self.claude:
                self.assertEqual(sorted(render["shared_skills"]), SHARED_SKILLS)
                self.assertEqual(sorted(render["shared_memory"]), MEMORY)
                self.assertEqual(render["vendor_skills"]["ponytail"], ["ponytail", "ponytail-audit", "ponytail-debt", "ponytail-gain", "ponytail-help", "ponytail-review"])
                self.assertEqual(render["vendor_skills"]["caveman"], ["caveman", "caveman-commit", "caveman-help", "caveman-review"])
            self.assertEqual(render["vendor_file_mappings"], VENDOR_FILE_MAPPINGS)
        for skill in SHARED_SKILLS:
            self.assertRegex((ROOT / "claude-code" / "core" / "shared" / "skills" / skill / "SKILL.md").read_text(), rf"(?m)^name: {re.escape(skill)}$")

    def test_context_renders_match_canonical_bytes_and_render_sources_are_digest_backed(self):
        manifest = json.loads((ROOT / ".shahinkit-manifest.json").read_text())
        owned = {entry["path"]: entry for entry in manifest["owned_files"]}
        adapters = (("claude-code", self.claude), ("codex", self.codex), ("opencode", self.opencode))
        for host, render in adapters:
            destination = ROOT / host / "CLAUDE.md" if host == "claude-code" else ROOT / host / "AGENTS.md"
            content = destination.read_text()
            for item in render["context_renders"]:
                canonical = assert_safe_manifest_path(self, item["source"]).read_text().strip()
                pattern = rf"<!-- SHAHINKIT:{item['marker']}:START -->.*?<!-- SHAHINKIT:{item['marker']}:END -->"
                self.assertEqual(re.search(pattern, content, flags=re.S).group(0), canonical)
                self.assertIn(item["source"], owned)
            sources = set(render.get("mcp_templates", []))
            sources.update(item["source"] for item in render.get("copies", []))
            sources.update(item["source"] for item in render.get("adapter_assets", []) if isinstance(item, dict))
            sources.update(render.get("render", {}).get("byte_copy", []))
            sources.update(render.get("render", {}).get("templates", []))
            sources.update(output["source"] for output in render.get("course_rag", {}).get("outputs", []))
            sources.update(spec[key] for spec in render.get("render", {}).get("scope_templates", {}).values() for key in ("config", "agents", "plugin_features"))
            if "settings_patches" in render:
                settings = render["settings_patches"]
                sources.add(settings["base_source"])
                sources.update(settings["hook_sources"].values())
                sources.add(settings["hook_script_source"])
            if "hooks" in render:
                sources.add(render["hooks"]["script_source"])
                sources.update(render["hooks"]["config_sources"].values())
            sources.update(f"{host}/{item}" for item in render.get("adapter_assets", []) if isinstance(item, str))
            skills = render.get("shared", {}).get("skills", render.get("shared_skills", []))
            memory = render.get("shared", {}).get("memory", render.get("shared_memory", []))
            sources.update(f"claude-code/core/shared/skills/{skill}/SKILL.md" for skill in skills)
            sources.update(f"claude-code/core/shared/memory/{name}" for name in memory)
            for vendor, names in render.get("vendor_skills", {}).items():
                sources.update(f"claude-code/core/third_party/{vendor}/skills/{name}/SKILL.md" for name in names)
            vendor_file_sources = {
                f"{mapping['source_root']}/{name}"
                for mapping in render.get("vendor_file_mappings", [])
                for name in mapping["files"]
            }
            sources.update(vendor_file_sources)
            for source in sources:
                candidate = ROOT.joinpath(*PurePosixPath(source).parts)
                root_is_absent = any(
                    source.startswith(f"{mapping['source_root']}/") and not (ROOT / mapping["source_root"]).is_dir()
                    for mapping in render.get("vendor_file_mappings", [])
                )
                if source in vendor_file_sources and root_is_absent:
                    continue  # Vendor roots land with their own pinned manifest update.
                candidate = assert_safe_manifest_path(self, source)
                self.assertTrue(candidate.is_file(), source)
                source_host = next((name for name in ("claude-code", "codex", "opencode") if source.startswith(f"{name}/")), None)
                if source_host and not source.startswith("claude-code/core/"):
                    relative = source.removeprefix(f"{source_host}/")
                    self.assertIn(relative, manifest["adapter_inputs"][source_host])
                    self.assertEqual(manifest["adapter_inputs"][source_host][relative], hashlib.sha256(candidate.read_bytes()).hexdigest())
                else:
                    self.assertIn(source, owned)
                    self.assertEqual(owned[source]["source_sha256"], hashlib.sha256(candidate.read_bytes()).hexdigest())

    def test_catalog_discovers_declarative_vendor_roots(self):
        catalog_path = ROOT / "claude-code" / "core" / "scripts" / "build_catalog.py"
        spec = importlib.util.spec_from_file_location("shahinkit_catalog", catalog_path)
        catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(catalog)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            render_path = root / "claude-code" / "render-manifest.json"
            render_path.parent.mkdir(parents=True)
            render_path.write_text(json.dumps({"vendor_skills": {}, "vendor_file_mappings": VENDOR_FILE_MAPPINGS}))
            for mapping in VENDOR_FILE_MAPPINGS:
                path = root / mapping["source_root"] / "SKILL.md"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"---\nname: {mapping['skill']}\ndescription: use when testing catalog discovery\n---\n")
            course = root / "claude-code" / "skills" / "course-rag" / "SKILL.md"
            course.parent.mkdir(parents=True)
            course.write_text("---\nname: course-rag\ndescription: use when testing catalog discovery\n---\n")
            self.assertEqual({item["name"] for item in catalog.skills(root)}, {"course-rag", *(mapping["skill"] for mapping in VENDOR_FILE_MAPPINGS)})

    def test_required_install_assets_are_explicit_and_present(self):
        expected = {
            "claude-code": ["CLAUDE.md", "config/mcp.basic-memory.example.json", "agents/controller.md", "skills/course-rag/SKILL.md", "course-rag/scripts/build.py", "course-rag/scripts/search.py"],
            "codex": ["AGENTS.md", "config/config.patch.example.toml", "config/agents/controller.toml", "course-rag/SKILL.md", "course-rag/scripts/build.py", "course-rag/scripts/search.py"],
            "opencode": ["AGENTS.md", "opencode.jsonc.example", "opencode.user.jsonc.example", ".opencode/plugins/portable-gates.mjs", ".opencode/plugins/portable-gates.features.mjs", ".opencode/plugins/shahinkit-guard.mjs", ".opencode/agents/controller.md"],
        }
        for host, assets in expected.items():
            render = {"claude-code": self.claude, "codex": self.codex, "opencode": self.opencode}[host]
            self.assertEqual(render["required_install_assets"], assets)
            for asset in assets:
                self.assertTrue((ROOT / host / asset).is_file(), f"{host}/{asset}")
                self.assertIn(asset, json.loads((ROOT / ".shahinkit-manifest.json").read_text())["adapter_inputs"][host])
                destinations = render.get("scope_install_destinations")
                if destinations:
                    if asset in ("AGENTS.md", "course-rag/SKILL.md", "course-rag/scripts/build.py", "course-rag/scripts/search.py"):
                        continue  # rendered through the instruction or course-rag declarations
                    self.assertTrue(all(destinations[scope][asset] for scope in ("user", "project")))
                else:
                    self.assertTrue(render["install_destinations"][asset])

    def test_main_manifest_and_adapter_render_digests_match_source_bytes(self):
        manifest = json.loads((ROOT / ".shahinkit-manifest.json").read_text())
        for entry in manifest["owned_files"]:
            digest = hashlib.sha256(assert_safe_manifest_path(self, entry["path"]).read_bytes()).hexdigest()
            self.assertEqual(entry["source_sha256"], digest)
            self.assertEqual(entry["render_sha256"], digest)
        for host, files in manifest["adapter_inputs"].items():
            for relative, digest in files.items():
                path = f"{host}/{relative}"
                self.assertEqual(digest, hashlib.sha256(assert_safe_manifest_path(self, path).read_bytes()).hexdigest())
        for render in (self.claude, self.codex, self.opencode):
            for key, value in render.items():
                if key.endswith("sha256"):
                    self.assertRegex(value, r"^[0-9a-f]{64}$")

    def test_exact_role_defaults_and_no_inheritance(self):
        claude_roles = json.loads((ROOT / "claude-code" / "core" / "tests" / "fixtures" / "b3" / "claude-contract.json").read_text())["roles"]
        codex_roles = json.loads((ROOT / "claude-code" / "core" / "tests" / "fixtures" / "b3" / "codex-contract.json").read_text())["roles"]
        opencode_roles = json.loads((ROOT / "claude-code" / "core" / "tests" / "fixtures" / "b3" / "opencode" / "contract.json").read_text())["roles"]
        expected_defaults = {
            "claude-code": claude_roles,
            "codex": codex_roles,
            "opencode": opencode_roles,
        }
        actual_defaults = self.schema["x-shahinkit"]["defaults"]
        for host, expected in expected_defaults.items():
            for role, model in expected.items():
                self.assertIsInstance(model, str, f"{host}/{role}")
                self.assertTrue(model, f"{host}/{role}")
                self.assertIsInstance(actual_defaults[host][role], str, f"{host}/{role}")
                self.assertTrue(actual_defaults[host][role], f"{host}/{role}")
            self.assertEqual(actual_defaults[host], expected)
        for role in ROLES:
            claude = (ROOT / "claude-code/agents" / f"{role}.md").read_text()
            self.assertRegex(claude, rf"(?m)^name: {role}$")
            self.assertIn("model: {{ROLE_MODEL_%s}}" % role.upper(), claude)
            codex = tomllib.loads((ROOT / "codex/config/agents" / f"{role}.toml").read_text())
            self.assertEqual(codex["model"], "{{ROLE_MODEL_%s}}" % role.upper())
            opencode = (ROOT / "opencode/.opencode/agents" / f"{role}.md").read_text()
            self.assertIn("model: {{ROLE_MODEL_%s}}" % role.upper(), opencode)
        corpus = "\n".join(path.read_text(errors="ignore") for host in ("claude-code", "codex", "opencode") for path in (ROOT / host).rglob("*") if path.is_file())
        self.assertNotRegex(corpus, r"(?im)^\s*(inherit|inherits_from|model_from_role)\s*[:=]")

    def test_exact_host_destination_maps_and_activation_claims(self):
        self.assertEqual(self.claude["render_rules"]["scope_roots"], {
            "user": {"instructions": "CLAUDE.md", "skills": "skills", "commands": "commands", "agents": "agents", "settings": "settings.json", "mcp": ".claude.json", "data": "{{SHAHINKIT_DATA_DIR}}"},
            "project": {"instructions": "CLAUDE.md", "skills": ".claude/skills", "commands": ".claude/commands", "agents": ".claude/agents", "settings": ".claude/settings.json", "mcp": ".mcp.json", "data": "{{SHAHINKIT_DATA_DIR}}"},
        })
        self.assertEqual(self.codex["render_rules"]["scope_roots"]["project"]["skills"], ".agents/skills")
        self.assertEqual(self.codex["render_rules"]["scope_roots"]["user"]["skills"], "$HOME/.agents/skills")
        self.assertNotIn(".codex/skills", " ".join(self.codex["course_rag"]["skill_destinations"].values()))
        self.assertEqual(self.opencode["render_rules"]["scope_roots"]["project"]["skills"], ".opencode/skills")
        self.assertEqual(self.opencode["render_rules"]["scope_roots"]["user"]["plugins"], "plugins")
        lifecycle = json.loads((ROOT / "claude-code/hooks/managed-lifecycle.after-trust.json").read_text())
        self.assertEqual(lifecycle["activation"]["required"], ["preview", "apply", "trust-host"])
        self.assertTrue(all(lifecycle["modes"][mode]["enabled"] for mode in ("ponytail", "caveman")))
        self.assertIn("after preview, apply, and host-trust", self.codex["render_rules"]["activation"])
        self.assertIn("after preview, apply, and host-trust", self.opencode["render_rules"]["activation"])
        self.assertNotIn("plugin", json.loads((ROOT / "opencode/opencode.jsonc.example").read_text()))

    def test_codex_scope_destinations_join_fixture_roots(self):
        fixtures = ROOT / "claude-code" / "core" / "tests" / "fixtures" / "hosts" / "codex"
        home = fixtures / "home"
        expected = {
            "user": {
                "config/config.patch.example.toml": fixtures / "user/config.toml",
                "config/agents/controller.toml": fixtures / "user/agents/controller.toml",
            },
            "project": {
                "config/config.patch.example.toml": fixtures / "project/.codex/config.toml",
                "config/agents/controller.toml": fixtures / "project/.codex/agents/controller.toml",
            },
        }
        for scope, assets in expected.items():
            scope_root = fixtures / scope
            destinations = self.codex["scope_install_destinations"][scope]
            agent_root = scope_root / ("agents" if scope == "user" else ".codex/agents")
            for role in ROLES:
                assets[f"config/agents/{role}.toml"] = agent_root / f"{role}.toml"
            for asset, final_path in assets.items():
                self.assertEqual(destination_path(scope_root, home, destinations[asset], fixtures / "data"), final_path)

    def test_opencode_rendered_feature_combinations_cover_static_and_plugin_outputs(self):
        node = shutil.which("node")
        self.assertIsNotNone(node)
        render = self.opencode["render"]
        for scope, spec in render["scope_templates"].items():
            for ponytail, caveman in (("true", "true"), ("false", "true"), ("true", "false"), ("false", "false")):
                values = {"PONYTAIL_ENABLED": ponytail, "CAVEMAN_ENABLED": caveman}
                with tempfile.TemporaryDirectory() as temporary:
                    output = Path(temporary)
                    config_text = render_feature_template((ROOT / spec["config"]).read_text(), values)
                    agents = render_feature_template((ROOT / spec["agents"]).read_text(), values)
                    self.assertNotIn("{{", config_text)
                    self.assertNotIn("{{", agents)
                    config = json.loads(config_text)
                    config_path = output / spec["config_destination"]
                    config_path.parent.mkdir(parents=True, exist_ok=True)
                    config_path.write_text(config_text)
                    (output / "AGENTS.md").write_text(agents)
                    feature = output / spec["plugin_destination"]
                    feature.parent.mkdir(parents=True)
                    feature_text = render_feature_template((ROOT / spec["plugin_features"]).read_text(), values)
                    self.assertNotIn("{{", feature_text)
                    feature.write_text(feature_text)
                    plugin = output / (spec["plugin_destination"].removesuffix(".features.mjs") + ".mjs")
                    plugin.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(ROOT / render["byte_copy"][0], plugin)
                    self.assertEqual("SHAHINKIT:PONYTAIL:START" in agents, ponytail == "true")
                    self.assertEqual("SHAHINKIT:CAVEMAN:START" in agents, caveman == "true")
                    expected = int(ponytail == "true") + int(caveman == "true")
                    result = subprocess.run([node, "--input-type=module", "-e", f'''import createPlugin from "{plugin.as_uri()}";
const hooks = await createPlugin(); const output = {{ system: [] }};
await hooks["experimental.chat.system.transform"]({{ sessionID: "one" }}, output);
if (output.system.length !== {expected}) process.exit(1);'''], text=True, capture_output=True, check=False)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_render_manifest_defaults_enable_supported_features(self):
        expected = {
            "claude-code": {"required": {"SHAHINKIT_DATA_DIR", "SHAHINKIT_STATE_DIR", "LOCAL_BASIC_MEMORY_CONFIG_DIR", "LOCAL_PROJECT_NAME", "LOCAL_PROJECT_PATH", "LOCAL_PROJECT_ROOT", "SHAHINKIT_HOOK_PATH", "PONYTAIL_ENABLED", "CAVEMAN_ENABLED", "BUDGET_PRESET", "DELEGATION_MODE", "INLINE_FILE_LIMIT", "INLINE_LINE_LIMIT", "CROSS_HOST_ROUTE", "ROLE_MODEL_CONTROLLER", "ROLE_MODEL_RESEARCH", "ROLE_MODEL_IMPLEMENTATION", "ROLE_MODEL_REVIEW", "ROLE_MODEL_MECHANICAL"}, "defaults": {}},
            "codex": {"required": {"SHAHINKIT_DATA_DIR", "SHAHINKIT_STATE_DIR", "LOCAL_BASIC_MEMORY_CONFIG_DIR", "LOCAL_PROJECT_NAME", "LOCAL_PROJECT_PATH", "LOCAL_PROJECT_ROOT", "SHAHINKIT_HOOK_PATH", "PONYTAIL_ENABLED", "CAVEMAN_ENABLED", "BUDGET_PRESET", "DELEGATION_MODE", "INLINE_FILE_LIMIT", "INLINE_LINE_LIMIT", "CROSS_HOST_ROUTE", "ROLE_MODEL_CONTROLLER", "ROLE_MODEL_RESEARCH", "ROLE_MODEL_IMPLEMENTATION", "ROLE_MODEL_REVIEW", "ROLE_MODEL_MECHANICAL"}, "defaults": {}},
            "opencode": {"required": {"SHAHINKIT_DATA_DIR", "SHAHINKIT_STATE_DIR", "LOCAL_BASIC_MEMORY_CONFIG_DIR", "LOCAL_PROJECT_NAME", "LOCAL_PROJECT_PATH", "LOCAL_PROJECT_ROOT", "PONYTAIL_ENABLED", "CAVEMAN_ENABLED", "BUDGET_PRESET", "DELEGATION_MODE", "INLINE_FILE_LIMIT", "INLINE_LINE_LIMIT", "CROSS_HOST_ROUTE", "ROLE_MODEL_CONTROLLER", "ROLE_MODEL_RESEARCH", "ROLE_MODEL_IMPLEMENTATION", "ROLE_MODEL_REVIEW", "ROLE_MODEL_MECHANICAL"}, "defaults": {"PONYTAIL_ENABLED": "true", "CAVEMAN_ENABLED": "true"}},
        }
        for host, render in (("claude-code", self.claude), ("codex", self.codex), ("opencode", self.opencode)):
            substitutions = render.get("render", {})
            self.assertEqual(set(substitutions.get("required_substitutions", [])), expected[host]["required"])
            self.assertEqual(substitutions.get("default_substitutions", {}), expected[host]["defaults"])
        defaults = self.opencode["render"]["default_substitutions"]
        for scope, spec in self.opencode["render"]["scope_templates"].items():
            agents = render_feature_template((ROOT / spec["agents"]).read_text(), defaults)
            feature = render_feature_template((ROOT / spec["plugin_features"]).read_text(), defaults)
            self.assertIn("SHAHINKIT:PONYTAIL:START", agents, scope)
            self.assertIn("SHAHINKIT:CAVEMAN:START", agents, scope)
            self.assertIn('ponytail: "true" === "true"', feature)
            self.assertIn('caveman: "true" === "true"', feature)

    def test_render_destinations_stay_within_selected_safe_scope_roots(self):
        for host, render in (("claude-code", self.claude), ("codex", self.codex), ("opencode", self.opencode)):
            for scope in ("user", "project"):
                with tempfile.TemporaryDirectory() as temporary:
                    scope_root = Path(temporary) / host / scope
                    home_root = Path(temporary) / host / "home"
                    data_root = scope_root / "data"
                    for root in (scope_root, home_root, data_root):
                        root.mkdir(parents=True, exist_ok=True)
                    for destination in render_destinations(render, scope):
                        assert_safe_render_destination(self, scope_root, home_root, data_root, destination)

    def test_manifest_source_and_destination_ancestor_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inside = root / "inside"
            outside = root / "outside"
            inside.mkdir()
            outside.mkdir()
            fixtures = {
                "inside-link": inside,
                "outside-link": outside,
                "dangling-link": root / "missing",
            }
            for name, target in fixtures.items():
                (root / name).symlink_to(target, target_is_directory=True)
                with self.subTest(source=name):
                    with self.assertRaises(AssertionError):
                        assert_safe_manifest_path(self, f"{name}/file", root)
                with self.subTest(destination=name):
                    with self.assertRaises(AssertionError):
                        assert_safe_render_destination(self, root, root, root, f"{name}/file")

    def test_generic_gates_disabled_basic_memory_local_and_no_unsupported_fields(self):
        claude_generic = json.loads((ROOT / "claude-code/hooks/generic.disabled.example.json").read_text())
        codex_generic = json.loads((ROOT / "codex/hooks/generic-gates.disabled.example.json").read_text())
        self.assertEqual(claude_generic["status"], "retired-example")
        self.assertEqual(codex_generic["status"], "retired-example")
        local_config = json.loads((ROOT / "claude-code" / "core" / "shared" / "mcp" / "basic-memory" / "local-config.example.json").read_text())
        project = local_config["projects"]["<LOCAL_PROJECT_NAME>"]
        self.assertEqual(project["mode"], "local")
        self.assertIsNone(project["workspace_id"])
        claude_mcp = json.loads((ROOT / "claude-code/config/mcp.basic-memory.example.json").read_text())["mcpServers"]["basic-memory"]
        codex_mcp = tomllib.loads((ROOT / "codex/config/config.patch.example.toml").read_text())["mcp_servers"]["basic-memory"]
        opencode_mcp = json.loads((ROOT / "opencode/opencode.jsonc.example").read_text())["mcp"]["basic-memory"]
        shared_claude = json.loads((ROOT / "claude-code" / "core" / "shared" / "mcp" / "basic-memory" / "claude-code.mcp.json").read_text())["mcpServers"]["basic-memory"]
        shared_codex = tomllib.loads((ROOT / "claude-code" / "core" / "shared" / "mcp" / "basic-memory" / "codex.mcp.toml").read_text())["mcp_servers"]["basic-memory"]
        shared_opencode = json.loads((ROOT / "claude-code" / "core" / "shared" / "mcp" / "basic-memory" / "opencode.mcp.json").read_text())["mcp"]["basic-memory"]
        self.assertEqual(claude_mcp["command"], codex_mcp["command"])
        self.assertEqual(claude_mcp, shared_claude)
        self.assertEqual(codex_mcp, shared_codex)
        self.assertEqual(opencode_mcp, shared_opencode)
        self.assertEqual(opencode_mcp["type"], "local")
        for mcp in (claude_mcp, codex_mcp, opencode_mcp):
            encoded = json.dumps(mcp)
            self.assertIn("basic-memory", encoded)
            self.assertNotRegex(encoded, r'(?i)"?(url|token|api[_-]?key|secret)"?\s*:')
            self.assertEqual(mcp["env"]["BASIC_MEMORY_FORCE_LOCAL"], "true")
            self.assertEqual(mcp["env"]["BASIC_MEMORY_EXPLICIT_ROUTING"], "true")
            self.assertNotIn("BASIC_MEMORY_FORCE_CLOUD", mcp["env"])
        self.assertNotIn("skillOverrides", (ROOT / "claude-code/config/settings.patch.example.json").read_text())
        self.assertFalse((ROOT / "codex/hooks/ponytail.lifecycle.managed.example.toml").exists())

    def test_course_rag_remains_local_portable_and_adapter_documented(self):
        claude = ROOT / "claude-code/course-rag"
        codex = ROOT / "codex/course-rag"
        for root in (claude, codex):
            corpus = "\n".join(path.read_text() for path in root.rglob("*") if path.is_file())
            self.assertIn("local SQLite", corpus)
            self.assertRegex(corpus, r"(?i)(never|does not) upload")
            self.assertNotRegex(corpus, r"/(?:Users|home)/|\$HOME")
        self.assertEqual((claude / "scripts/build.py").read_bytes(), (codex / "scripts/build.py").read_bytes())
        self.assertEqual((claude / "scripts/search.py").read_bytes(), (codex / "scripts/search.py").read_bytes())
        for root in (claude, codex):
            self.assertIn("{{SHAHINKIT_DATA_DIR}}/course-rag", (root / "scripts/build.py").read_text())
            self.assertIn("{{SHAHINKIT_DATA_DIR}}/course-rag", (root / "README.md").read_text())
        self.assertIn("{{SHAHINKIT_DATA_DIR}}/course-rag/scripts/build.py", (ROOT / "claude-code/skills/course-rag/SKILL.md").read_text())
        self.assertIn("{{SHAHINKIT_DATA_DIR}}/course-rag/scripts/build.py", (ROOT / "codex/course-rag/SKILL.md").read_text())

    def test_course_rag_render_smoke_skips_symlinks_and_uses_data_destination(self):
        source_script = ROOT / "claude-code/course-rag/scripts/build.py"
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            source = temporary_path / "source"
            source.mkdir()
            (source / "inside.txt").write_text("inside course text")
            outside = temporary_path / "outside.txt"
            outside.write_text("outside course text")
            (source / "outside-link.txt").symlink_to(outside)
            data = temporary_path / "installed-data"
            rendered = temporary_path / "build.py"
            rendered.write_text(source_script.read_text().replace("{{SHAHINKIT_DATA_DIR}}", str(data)))
            result = subprocess.run(
                [sys.executable, str(rendered), "--subject", "Course", "--source", str(source)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"index: {data.resolve()}/course-rag/course.sqlite", result.stdout)
            self.assertIn("indexed files: 1", result.stdout)
            self.assertFalse((data / "course-rag/course.sqlite").is_symlink())

    def test_manifest_covers_each_adapter_input_with_fresh_digest_and_no_symlinks(self):
        manifest = json.loads((ROOT / ".shahinkit-manifest.json").read_text())
        inputs = manifest["adapter_inputs"]
        for host in ("claude-code", "codex", "opencode"):
            actual = {
                path.relative_to(ROOT / host).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (ROOT / host).rglob("*")
                if path.is_file()
                and not (host == "claude-code" and path.relative_to(ROOT / host).parts[0] == "core")
            }
            self.assertEqual(inputs[host], actual)
            for relative in inputs[host]:
                assert_safe_manifest_path(self, f"{host}/{relative}")
            for path in (ROOT / host).rglob("*"):
                self.assertFalse(path.is_symlink(), path)
        payload = "\n".join(
            path.read_text(errors="ignore")
            for host in ("claude-code", "codex", "opencode")
            for path in (ROOT / host).rglob("*")
            if path.is_file()
            and not (host == "claude-code" and path.relative_to(ROOT / host).parts[0] == "core")
        )
        self.assertNotRegex(payload, r"/(?:Users|home)/|\bsk-[A-Za-z0-9]|BEGIN [A-Z ]*PRIVATE KEY")
        self.assertNotIn("curl |", payload)
        self.assertNotIn("npx -y", payload)


if __name__ == "__main__":
    unittest.main()
