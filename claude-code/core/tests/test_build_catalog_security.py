import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "build_catalog.py"
spec = importlib.util.spec_from_file_location("build_catalog", SCRIPT)
build_catalog = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(build_catalog)


class BuildCatalogSecurityTests(unittest.TestCase):
    def test_vendor_mapping_cannot_escape_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / "claude-code" / "render-manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({
                "vendor_file_mappings": [{"source_root": "../../outside", "skill": "bad", "files": ["SKILL.md"]}]
            }))
            with self.assertRaisesRegex(ValueError, "unsafe|escapes"):
                build_catalog.vendor_skill_paths(root)

    def test_vendor_mapping_symlink_cannot_escape_third_party(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            third_party = root / "claude-code" / "core" / "third_party"
            third_party.mkdir(parents=True)
            outside = root / "outside"
            outside.mkdir()
            (third_party / "linked").symlink_to(outside, target_is_directory=True)
            manifest = root / "claude-code" / "render-manifest.json"
            manifest.write_text(json.dumps({
                "vendor_file_mappings": [{
                    "source_root": "claude-code/core/third_party/linked/vendor",
                    "skill": "bad",
                    "files": ["SKILL.md"],
                }]
            }))
            with self.assertRaisesRegex(ValueError, "escapes"):
                build_catalog.vendor_skill_paths(root)


if __name__ == "__main__":
    unittest.main()
