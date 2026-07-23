import hashlib
import json
import re
import stat
import subprocess
import unittest
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
ROLE_NAMES = ("controller", "research", "implementation", "review", "mechanical")


class B1ContractTests(unittest.TestCase):
    def load_json(self, relative_path):
        return json.loads((ROOT / relative_path).read_text())

    def schema_errors(self, schema, instance):
        def resolve(reference):
            value = schema
            for part in reference.removeprefix("#/").split("/"):
                value = value[part]
            return value

        def validate(value, rule):
            if "$ref" in rule:
                return validate(value, resolve(rule["$ref"]))
            errors = []
            if "allOf" in rule:
                for child in rule["allOf"]:
                    errors.extend(validate(value, child))
            if "if" in rule and not validate(value, rule["if"]):
                errors.extend(validate(value, rule.get("then", {})))
            if "not" in rule and not validate(value, rule["not"]):
                errors.append("forbidden value")
            if "anyOf" in rule and all(validate(value, child) for child in rule["anyOf"]):
                errors.append("no anyOf branch matched")
            if rule.get("type") == "object" and not isinstance(value, dict):
                return ["expected object"]
            if rule.get("type") == "string" and not isinstance(value, str):
                return ["expected string"]
            if "enum" in rule and value not in rule["enum"]:
                errors.append("unexpected enum")
            if "const" in rule and value != rule["const"]:
                errors.append("unexpected const")
            if isinstance(value, str):
                if len(value) < rule.get("minLength", 0):
                    errors.append("string too short")
                if "pattern" in rule and not re.search(rule["pattern"], value):
                    errors.append("pattern mismatch")
            if isinstance(value, dict):
                for key in rule.get("required", []):
                    if key not in value:
                        errors.append(f"missing {key}")
                properties = rule.get("properties", {})
                if rule.get("additionalProperties") is False:
                    errors.extend(f"unknown {key}" for key in value if key not in properties)
                for key, child in properties.items():
                    if key in value:
                        errors.extend(validate(value[key], child))
            return errors

        return validate(instance, schema)

    def role_input(self, host, defaults):
        return {
            "host": host,
            "roles": {
                role: {
                    "default_model": model,
                    "resolved_model": model,
                    "override_setting": f"shahinkit.models.{role}",
                }
                for role, model in defaults.items()
            },
        }

    def test_role_defaults_overrides_and_independent_resolution(self):
        schema = self.load_json("school/shared/models/roles.schema.json")
        expected = self.load_json("school/tests/fixtures/b1/role-defaults.json")
        self.assertEqual(schema["x-shahinkit"]["defaults"], expected)
        role = schema["$defs"]["role"]
        self.assertEqual(role["required"], ["default_model", "resolved_model", "override_setting"])
        self.assertFalse(role["additionalProperties"])
        forbidden = role["not"]["anyOf"]
        self.assertEqual(forbidden, [{"required": ["inherits_from"]}, {"required": ["inherit"]}, {"required": ["model_from_role"]}])
        self.assertEqual(schema["x-shahinkit"]["render_source"], "roles.<role>.resolved_model")
        for host, defaults in expected.items():
            self.assertEqual(tuple(defaults), ROLE_NAMES, host)
            self.assertTrue(all(defaults[role] for role in ROLE_NAMES), host)
            default_input = self.role_input(host, defaults)
            self.assertEqual(self.schema_errors(schema, default_input), [], host)
            self.assertEqual(
                {role: value["resolved_model"] for role, value in default_input["roles"].items()},
                defaults,
                host,
            )

            overridden = self.role_input(host, defaults)
            overridden["roles"]["research"]["resolved_model"] = "user-selected-model"
            self.assertEqual(self.schema_errors(schema, overridden), [], host)

            unknown = self.role_input(host, defaults)
            unknown["roles"]["research"]["override_setting"] = "shahinkit.models.unknown"
            self.assertTrue(self.schema_errors(schema, unknown), host)

            unknown_key = self.role_input(host, defaults)
            unknown_key["roles"]["research"]["override"] = "user-selected-model"
            self.assertTrue(self.schema_errors(schema, unknown_key), host)

            cross_role = self.role_input(host, defaults)
            cross_role["roles"]["research"]["override_setting"] = "shahinkit.models.controller"
            self.assertTrue(self.schema_errors(schema, cross_role), host)

            inherited = self.role_input(host, defaults)
            inherited["roles"]["implementation"]["inherits_from"] = "controller"
            self.assertTrue(self.schema_errors(schema, inherited), host)

    def test_manifest_owned_paths_are_normalized_and_digest_backed(self):
        manifest = self.load_json(".shahinkit-manifest.json")
        self.assertNotIn("future_assets", manifest)
        owned_paths = {entry["path"] for entry in manifest["owned_files"]}
        expected_paths = {
            "README.md", "INSTALL.md", "school/README.md", "school/docs/integration-catalog.md",
            "school/docs/INSTALL-RECEIPT-SCHEMA.md", "school/docs/STUDY-ACCEPTANCE-v1.md",
            "school/scripts/manage.py",
        }
        for directory in (
            "school/shared/policies",
            "school/shared/models",
            "school/shared/context",
            "school/shared/skills",
            "school/shared/memory",
            "school/shared/mcp",
        ):
            expected_paths.update(
                path.relative_to(ROOT).as_posix()
                for path in (ROOT / directory).rglob("*")
                if path.is_file()
            )
        expected_paths.update(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "school" / "docs" / "evidence").rglob("*")
            if path.is_file()
        )
        expected_paths.update(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "school" / "third_party").rglob("*")
            if path.is_file()
            and "tests" not in path.relative_to(ROOT / "school" / "third_party").parts
            and path.name != "README.md"
        )
        expected_paths.update(
            f"school/integrations/dev-scope/{name}"
            for name in (
                "README.md",
                "config.example.json",
                "index.js",
                "lib/scope.js",
                "package.json",
                "package-lock.json",
            )
        )
        self.assertEqual(owned_paths, expected_paths)
        rules = manifest["path_rules"]
        self.assertTrue(rules["relative_only"])
        self.assertTrue(rules["normalized"])
        self.assertTrue(rules["forbid_dotdot"])
        self.assertTrue(rules["forbid_symlinks"])
        for entry in manifest["owned_files"]:
            self.assertIn("category", entry)
            self.assertTrue(entry["category"])
            raw_path = entry["path"]
            self.assertIsInstance(raw_path, str)
            self.assertTrue(raw_path)
            self.assertFalse(raw_path.startswith("./"))
            self.assertNotIn("//", raw_path)
            self.assertNotIn("\\", raw_path)
            path = PurePosixPath(raw_path)
            self.assertFalse(path.is_absolute())
            self.assertNotIn("..", path.parts)
            self.assertNotIn(".", path.parts)
            self.assertEqual(path.as_posix(), raw_path)
            target = ROOT.joinpath(*path.parts)
            current = ROOT
            for component in path.parts:
                current = current / component
                self.assertFalse(stat.S_ISLNK(current.lstat().st_mode), raw_path)
            content = target.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            self.assertEqual(entry["source_sha256"], digest)
            self.assertEqual(entry["render_sha256"], digest)

    def test_published_root_has_exactly_four_source_directories(self):
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-co", "--exclude-standard"],
            text=True,
            capture_output=True,
            check=True,
        )
        directories = {
            relative.parts[0]
            for value in result.stdout.splitlines()
            if (relative := Path(value)).parts and (ROOT / relative).exists() and len(relative.parts) > 1
        }
        self.assertEqual(directories, {"claude-code", "codex", "opencode", "school"})
        self.assertFalse((ROOT / ".github").exists())


if __name__ == "__main__":
    unittest.main()
