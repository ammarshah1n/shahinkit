#!/usr/bin/env python3
"""Safe, local ShahinKit renderer and lifecycle manager. Python stdlib only."""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
import uuid
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_NAME = ".shahinkit-manifest.json"
RECEIPT_NAME = ".shahinkit-install-receipt.json"
BACKUP_DIR = ".shahinkit-backups"
SCHEMA_VERSION = 2
BACKUP_RETENTION = 3
CANONICAL_ORIGIN = "https://github.com/ammarshah1n/shahinkit.git"
# Release owner replaces UNSET before public release; UNSET always fails closed.
MAINTAINER_FINGERPRINT = "UNSET"
AGENTS = ("claude-code", "opencode", "codex")
FEATURES = ("ponytail", "caveman")
BLOCK_RE = re.compile(r"<!-- shahinkit:begin (?P<name>[a-z-]+) -->\n?(?P<body>.*?)<!-- shahinkit:end (?P=name) -->", re.S)
BLOCK_TOKEN_RE = re.compile(r"<!-- shahinkit:(?:begin|end) [a-z-]+ -->")
SECTION_RE = re.compile(r"\n?<!-- SHAHINKIT:(PONYTAIL|CAVEMAN):START -->.*?<!-- SHAHINKIT:\1:END -->\n?", re.S)


class ManagerError(Exception):
    pass


def fail(message: str) -> None:
    raise ManagerError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def relpath(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        fail("path must be non-empty normalized POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts) or path.as_posix() != value:
        fail(f"unsafe path: {value!r}")
    return path


def assert_no_symlink(path: Path, allow_missing_leaf: bool = True) -> None:
    """Check every existing ancestor using lstat; dangling links are links too."""
    try:
        if stat.S_ISLNK(path.lstat().st_mode):
            fail(f"symlink rejected: {path}")
    except FileNotFoundError:
        pass
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            if allow_missing_leaf:
                continue
            fail(f"missing required path: {current}")
        if stat.S_ISLNK(mode):
            fail(f"symlink rejected: {current}")


def safe_child(base: Path, relative: str, *, required: bool = False) -> Path:
    relpath(relative)
    assert_no_symlink(base)
    base_real = base.resolve(strict=False)
    candidate = base_real.joinpath(*PurePosixPath(relative).parts)
    assert_no_symlink(candidate, allow_missing_leaf=not required)
    if not candidate.resolve(strict=False).is_relative_to(base_real):
        fail(f"path escapes root: {relative}")
    if required:
        try:
            mode = candidate.lstat().st_mode
        except FileNotFoundError:
            fail(f"missing required path: {relative}")
        if not stat.S_ISREG(mode):
            fail(f"regular file required: {relative}")
    return candidate


def read_source(relative: str) -> bytes:
    path = safe_child(ROOT, relative, required=True)
    return path.read_bytes()


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        fail(f"invalid JSON {path.name}: {error}")


def load_manifest() -> dict:
    manifest = load_json(safe_child(ROOT, MANIFEST_NAME, required=True))
    if not isinstance(manifest, dict) or manifest.get("manifest_version") != 1:
        fail("unsupported manifest")
    for entry in manifest.get("owned_files", []):
        path = entry.get("path")
        relpath(path)
        data = read_source(path)
        if entry.get("source_sha256") != digest(data) or entry.get("render_sha256") != digest(data):
            fail(f"immutable manifest digest mismatch: {path}")
    for agent, files in manifest.get("adapter_inputs", {}).items():
        if agent not in AGENTS or not isinstance(files, dict):
            fail("invalid adapter input manifest")
        for relative, expected in files.items():
            relpath(relative)
            actual = digest(read_source(f"{agent}/{relative}"))
            if actual != expected:
                fail(f"immutable manifest digest mismatch: {agent}/{relative}")
    return manifest


def git(args: list[str]) -> str:
    command = ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.pager=cat", "-c", "diff.external=false", *args]
    result = subprocess.run(command, cwd=ROOT, env={"PATH": os.environ.get("PATH", "")}, text=True, capture_output=True, check=False)
    if result.returncode:
        fail(f"git verification failed: {' '.join(args)}")
    return result.stdout.strip()


def provenance(allow_development: bool) -> dict:
    manifest = load_manifest()
    tree = digest(canonical_json({
        "owned_files": [(item["path"], item["source_sha256"]) for item in manifest.get("owned_files", [])],
        "adapter_inputs": manifest.get("adapter_inputs", {}),
    }))
    origin = git(["config", "--get", "remote.origin.url"])
    if any(ord(character) < 32 for character in origin) or "@" in origin.split("://", 1)[-1].split("/", 1)[0]:
        fail("unsafe origin URL")
    normalized_origin = origin.removesuffix(".git")
    if normalized_origin not in ("https://github.com/ammarshah1n/shahinkit", "git@github.com:ammarshah1n/shahinkit"):
        fail("origin is not canonical GitHub owner/repository")
    head = git(["rev-parse", "HEAD"])
    tags = git(["tag", "--points-at", "HEAD"]).splitlines()
    tag = next((value for value in tags if git(["cat-file", "-t", value]) == "tag"), "")
    public = bool(tag)
    if public:
        result = subprocess.run(["git", "verify-tag", "--raw", tag], cwd=ROOT, text=True, capture_output=True, check=False)
        signer = re.search(r"\[GNUPG:\] VALIDSIG ([0-9A-F]+)", result.stdout + result.stderr)
        public = result.returncode == 0 and MAINTAINER_FINGERPRINT != "UNSET" and bool(signer) and signer.group(1) == MAINTAINER_FINGERPRINT
    if not public and not allow_development:
        fail("public provenance unavailable; pass --allow-development-checkout for non-public development use")
    return {"kind": "public-release" if public else "development-only", "repository": "github.com/ammarshah1n/shahinkit", "head": head, "tag": tag or None, "tree_sha256": tree, "manifest_sha256": digest(read_source(MANIFEST_NAME))}


def root_for(agent: str, scope: str, destination: str | None) -> tuple[Path, Path]:
    if destination:
        supplied = Path(destination).expanduser().absolute()
        try:
            if stat.S_ISLNK(supplied.lstat().st_mode):
                fail(f"symlink rejected: {supplied}")
        except FileNotFoundError:
            pass
        root = supplied.resolve(strict=False)
        # Isolated destination is intentionally self-contained: $HOME maps here/home.
        home = root / "home"
    elif scope == "project":
        root, home = Path.cwd().absolute(), Path.home().absolute()
    else:
        defaults = {
            "claude-code": Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))),
            "opencode": Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "opencode",
            "codex": Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))),
        }
        root, home = defaults[agent], Path.home().absolute()
    assert_no_symlink(root)
    assert_no_symlink(home)
    return root.resolve(strict=False), home.resolve(strict=False)


def substitute(text: str, values: dict[str, str]) -> str:
    for name, value in values.items():
        text = re.sub(rf"\{{\{{#{re.escape(name)}\}}\}}(.*?)\{{\{{/{re.escape(name)}\}}\}}", lambda m: m.group(1) if value == "true" else "", text, flags=re.S)
        text = text.replace("{{" + name + "}}", value).replace("<" + name + ">", value)
    if "{{" in text or re.search(r"<(?:LOCAL_|SHAHINKIT_)[A-Z_]+>", text):
        fail("unresolved render placeholder")
    return text


def remove_disabled_sections(text: str, features: dict[str, bool]) -> str:
    return SECTION_RE.sub(lambda m: "\n" if not features[m.group(1).lower()] else m.group(0), text)


def render_basic_memory_enabled(source: str, text: str, enabled: bool) -> str:
    if not enabled or source not in {
        "claude-code/config/mcp.basic-memory.example.json",
        "opencode/opencode.jsonc.example",
        "opencode/opencode.user.jsonc.example",
        "codex/config/config.patch.example.toml",
    }:
        return text
    if source.endswith(".toml"):
        updated, count = re.subn(r"(\[mcp_servers\.basic-memory\][\s\S]*?enabled = )false", r"\1true", text, count=1)
    else:
        updated, count = re.subn(r'("basic-memory"\s*:\s*\{[\s\S]*?"enabled"\s*:\s*)false', r"\1true", text, count=1)
    if count != 1:
        fail(f"Basic Memory launcher missing disabled flag: {source}")
    return updated


def destination_path(root: Path, home: Path, template: str, values: dict[str, str]) -> tuple[Path, str, str]:
    rendered = substitute(template, values)
    if rendered.startswith("$HOME/"):
        base, base_name, relative = home, "home", rendered.removeprefix("$HOME/")
    else:
        base, base_name, relative = root, "root", rendered
    # rendered data/state substitutions are always relative to selected root.
    return safe_child(base, relative), base_name, relative


def add_output(outputs: list[dict], source: str, destination: str, root: Path, home: Path, values: dict[str, str], path_values: dict[str, str], features: dict[str, bool], kind: str = "file") -> None:
    data = read_source(source)
    # All manifest-renderable assets are UTF-8 text; opaque bytes are not a
    # supported installation source because they cannot carry safe templates.
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        fail(f"non-text render asset rejected: {source}")
    text = render_basic_memory_enabled(source, remove_disabled_sections(substitute(text, values), features), features["basic-memory"])
    data = text.encode()
    target, base, relative = destination_path(root, home, destination, path_values)
    if target.name == RECEIPT_NAME or BACKUP_DIR in target.parts:
        fail("manifest may not own receipts or backups")
    outputs.append({"source": source, "path": target, "base": base, "relative": relative, "data": data, "kind": kind})


def outputs_for(agent: str, scope: str, root: Path, home: Path, features: dict[str, bool]) -> list[dict]:
    render = load_json(safe_child(ROOT, f"{agent}/render-manifest.json", required=True))
    if render.get("adapter") != agent:
        fail("adapter manifest mismatch")
    data_dir = safe_child(root, ".shahinkit-data")
    state_dir = safe_child(root, ".shahinkit-state")
    basic_memory_dir = safe_child(root, ".shahinkit-state/basic-memory")
    values = {
        "SHAHINKIT_DATA_DIR": str(data_dir),
        "SHAHINKIT_STATE_DIR": str(state_dir),
        "LOCAL_BASIC_MEMORY_CONFIG_DIR": str(basic_memory_dir),
        "LOCAL_PROJECT_NAME": "shahinkit-local",
        "LOCAL_PROJECT_PATH": str(safe_child(basic_memory_dir, "project")),
        "LOCAL_PROJECT_ROOT": str(root),
        "BASIC_MEMORY_ENABLED": str(features["basic-memory"]).lower(),
        "PONYTAIL_ENABLED": str(features["ponytail"]).lower(),
        "CAVEMAN_ENABLED": str(features["caveman"]).lower(),
        "DEV_SCOPE_ENTRYPOINT": "disabled",
        "DEV_SCOPE_CONFIG_FILE": "disabled",
    }
    path_values = {**values,
        "SHAHINKIT_DATA_DIR": ".shahinkit-data",
        "SHAHINKIT_STATE_DIR": ".shahinkit-state",
        "LOCAL_BASIC_MEMORY_CONFIG_DIR": ".shahinkit-state/basic-memory",
        "LOCAL_PROJECT_PATH": ".shahinkit-state/basic-memory/project",
        "LOCAL_PROJECT_ROOT": ".",
    }
    required = render.get("render", {}).get("required_substitutions", [])
    if any(not values.get(key) for key in required):
        fail("missing required render substitution")
    outputs: list[dict] = []
    if agent == "claude-code":
        for item in render.get("copies", []) + render.get("adapter_assets", []):
            destination = item["destination"]
            if scope == "project":
                for prefix in ("skills/", "agents/", "commands/"):
                    if destination.startswith(prefix):
                        destination = ".claude/" + destination
                        break
            add_output(outputs, item["source"], destination, root, home, values, path_values, features)
        # Context is merged into existing host instruction file, never whole-file overwrite.
        for output in outputs:
            if output["base"] == "root" and output["relative"] == "CLAUDE.md":
                output["kind"] = "instruction"
    else:
        instruction = "AGENTS.md"
        add_output(outputs, f"{agent}/AGENTS.md", instruction, root, home, values, path_values, features, "instruction")
        skill_root = render["render_rules"]["scope_roots"][scope]["skills"]
        for skill in render.get("shared_skills", []):
            add_output(outputs, f"school/shared/skills/{skill}/SKILL.md", f"{skill_root}/{skill}/SKILL.md", root, home, values, path_values, features)
        for vendor, skills in render.get("vendor_skills", {}).items():
            if not features.get(vendor, True):
                continue
            for skill in skills:
                add_output(outputs, f"school/third_party/{vendor}/skills/{skill}/SKILL.md", f"{skill_root}/{skill}/SKILL.md", root, home, values, path_values, features)
        for name in render.get("shared_memory", []):
            add_output(outputs, f"school/shared/memory/{name}", f".shahinkit-state/memory/{name}", root, home, values, path_values, features)
        if agent == "opencode":
            spec = render["render"]["scope_templates"][scope]
            add_output(outputs, spec["config"], spec["config_destination"], root, home, values, path_values, features, "json-config")
            add_output(outputs, "opencode/.opencode/plugins/portable-gates.mjs", spec["plugin_destination"].removesuffix(".features.mjs") + ".mjs", root, home, values, path_values, features)
            add_output(outputs, spec["plugin_features"], spec["plugin_destination"], root, home, values, path_values, features)
            for relative in render["adapter_assets"]:
                if relative in ("AGENTS.md", "opencode.jsonc.example", "opencode.user.jsonc.example", ".opencode/plugins/portable-gates.mjs", ".opencode/plugins/portable-gates.features.mjs"):
                    continue
                target = relative.removeprefix(".opencode/")
                if relative.startswith(".opencode/") and scope == "project":
                    target = relative
                add_output(outputs, f"opencode/{relative}", target, root, home, values, path_values, features)
        else:
            destinations = render["scope_install_destinations"][scope]
            for source, destination in destinations.items():
                add_output(outputs, f"codex/{source}", destination, root, home, values, path_values, features, "toml-config" if source == "config/config.patch.example.toml" else "file")
            for item in render["course_rag"]["outputs"]:
                destination = item.get("destination", item.get("destinations", {}).get(scope))
                add_output(outputs, item["source"], destination, root, home, values, path_values, features)
    if features["basic-memory"]:
        add_output(outputs, "school/shared/mcp/basic-memory/local-config.example.json", ".shahinkit-state/basic-memory/config.json", root, home, values, path_values, features)
    unique: dict[Path, dict] = {}
    for output in outputs:
        previous = unique.get(output["path"])
        if previous and previous["data"] != output["data"]:
            fail(f"two render entries conflict: {output['relative']}")
        unique[output["path"]] = previous if previous and previous["kind"] == "instruction" else output
    return list(unique.values())


def instruction_change(path: Path, rendered: bytes) -> tuple[bytes, dict]:
    payload = rendered.decode()
    if not path.exists():
        return f"<!-- shahinkit:begin instructions -->\n{payload.rstrip()}\n<!-- shahinkit:end instructions -->\n".encode(), {"kind": "instruction-block", "marker": "instructions"}
    current = path.read_text()
    matches = list(BLOCK_RE.finditer(current))
    tokens = BLOCK_TOKEN_RE.findall(current)
    if tokens and (len(matches) != 1 or matches[0].group("name") != "instructions" or len(tokens) != 2):
        fail(f"duplicate or malformed ShahinKit instruction markers: {path}")
    if not matches:
        separator = "" if not current or current.endswith("\n") else "\n"
        new = f"{current}{separator}\n<!-- shahinkit:begin instructions -->\n{payload.rstrip()}\n<!-- shahinkit:end instructions -->\n"
        return new.encode(), {"kind": "instruction-block", "marker": "instructions"}
    match = matches[0]
    new = current[:match.start("body")] + "\n" + payload.rstrip() + "\n" + current[match.end("body"):]
    return new.encode(), {"kind": "instruction-block", "marker": "instructions"}


def location_key(base: str, relative: str) -> tuple[str, str]:
    if base not in ("root", "home"):
        fail("unknown path base")
    relpath(relative)
    return base, relative


def location_path(root: Path, home: Path, base: str, relative: str, *, required: bool = False) -> Path:
    location_key(base, relative)
    return safe_child(root if base == "root" else home, relative, required=required)


def output_key(output: dict) -> tuple[str, str]:
    return location_key(output["base"], output["relative"])


def receipt_key(item: dict) -> tuple[str, str]:
    return location_key(item.get("base", ""), item.get("path", ""))


def json_config_change(path: Path, rendered: bytes) -> tuple[bytes, dict]:
    desired = json.loads(rendered)
    if not path.exists():
        return json.dumps(desired, indent=2, sort_keys=True).encode() + b"\n", {"kind": "file"}
    try:
        current = json.loads(path.read_text())
    except json.JSONDecodeError:
        fail(f"cannot safely structurally merge JSON/JSONC config: {path}")
    if not isinstance(current, dict) or current.get("$schema") not in (None, desired.get("$schema")):
        fail(f"cannot safely structurally merge config schema: {path}")
    before: dict[str, object] = {}
    for key, value in desired.items():
        if key == "$schema":
            current.setdefault(key, value)
        elif key not in current:
            current[key] = value
            before[key] = None
        elif isinstance(value, list) and isinstance(current[key], list):
            additions = [item for item in value if item not in current[key]]
            if additions:
                current[key].extend(additions)
                before[key] = {"list_added": additions}
        elif isinstance(value, dict) and isinstance(current[key], dict):
            additions = {name: item for name, item in value.items() if name not in current[key]}
            if additions:
                current[key].update(additions)
                before[key] = {"dict_added": additions}
        elif current[key] != value:
            fail(f"cannot safely structurally merge config key {key}: {path}")
    return json.dumps(current, indent=2, sort_keys=True).encode() + b"\n", {"kind": "json", "changes": before}


def toml_config_change(path: Path, rendered: bytes) -> tuple[bytes, dict]:
    if not path.exists():
        return rendered, {"kind": "file"}
    original = path.read_text()
    managed = re.compile(r"\n?# shahinkit:begin config\n.*?# shahinkit:end config\n?", re.S)
    baseline = managed.sub("", original, count=1)
    try:
        existing = tomllib.loads(baseline)
        candidate = tomllib.loads(rendered.decode())
    except tomllib.TOMLDecodeError:
        fail(f"cannot safely structurally merge TOML config: {path}")
    conflicts = set(existing).intersection(candidate)
    if conflicts:
        fail(f"cannot safely merge TOML; reviewed fragment required for: {', '.join(sorted(conflicts))}")
    block = "\n# shahinkit:begin config\n" + rendered.decode().rstrip() + "\n# shahinkit:end config\n"
    return (baseline + block).encode(), {"kind": "toml-block", "marker": "config", "before": ""}


def changed_plan(outputs: list[dict], root: Path, home: Path, prior: dict | None = None) -> list[dict]:
    plan = []
    owned = {receipt_key(item): item for item in (prior or {}).get("owned", [])}
    for output in outputs:
        path = output["path"]
        assert_no_symlink(path)
        data, ownership = output["data"], {"kind": "file"}
        if output["kind"] == "instruction":
            data, ownership = instruction_change(path, data)
        elif output["kind"] == "json-config":
            data, ownership = json_config_change(path, data)
        elif output["kind"] == "toml-config":
            data, ownership = toml_config_change(path, data)
        old = path.read_bytes() if path.exists() else None
        key = output_key(output)
        label = f"{key[0]}:{key[1]}"
        if old is not None and output["kind"] == "file":
            prior_item = owned.get(key)
            if not prior_item:
                fail(f"unowned destination collision: {label}")
            if digest(old) != prior_item["sha256"]:
                fail(f"managed file modified or missing: {label}")
        if old != data:
            plan.append({**output, "data": data, "old": old, "ownership": ownership})
    return plan


def receipt_path(root: Path) -> Path:
    return safe_child(root, RECEIPT_NAME)


def receipt_payload(receipt: dict) -> dict:
    return {key: value for key, value in receipt.items() if key != "integrity_sha256"}


def verify_receipt(root: Path) -> dict:
    path = receipt_path(root)
    if not path.exists():
        fail("destination receipt missing")
    receipt = load_json(path)
    if not isinstance(receipt, dict) or receipt.get("schema_version") != SCHEMA_VERSION:
        fail("unsupported receipt")
    if receipt.get("integrity_sha256") != digest(canonical_json(receipt_payload(receipt))):
        fail("receipt integrity mismatch")
    if not re.fullmatch(r"[0-9a-f]{64}", receipt.get("source_manifest_sha256", "")):
        fail("invalid receipt source manifest digest")
    owned = receipt.get("owned")
    if not isinstance(owned, list):
        fail("invalid receipt ownership")
    for item in owned:
        if not isinstance(item, dict):
            fail("invalid receipt ownership")
        receipt_key(item)
        if not re.fullmatch(r"[0-9a-f]{64}", item.get("sha256", "")):
            fail("invalid receipt owned digest")
    baseline = receipt.get("baseline")
    if not isinstance(baseline, list):
        fail("invalid receipt baseline")
    for operation in baseline:
        if not isinstance(operation, dict):
            fail("invalid receipt baseline")
        location_key(operation.get("base", ""), operation.get("path", ""))
        if operation.get("kind") == "file":
            try:
                base64.b64decode(operation.get("before_b64", ""), validate=True)
            except ValueError:
                fail("invalid receipt baseline")
        elif operation.get("kind") != "absent":
            fail("invalid receipt baseline")
    return receipt


def write_atomic(path: Path, data: bytes, mode: int = 0o600) -> None:
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "supports_dir_fd"):
        fail("secure POSIX dirfd primitives unavailable")
    assert_no_symlink(path)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory = os.open(path.anchor, flags)
    try:
        for component in path.parent.absolute().parts[1:]:
            try:
                child = os.open(component, flags, dir_fd=directory)
            except FileNotFoundError:
                os.mkdir(component, 0o700, dir_fd=directory)
                child = os.open(component, flags, dir_fd=directory)
            os.close(directory)
            directory = child
        try:
            if stat.S_ISLNK(os.stat(path.name, dir_fd=directory, follow_symlinks=False).st_mode):
                fail(f"symlink rejected: {path}")
        except FileNotFoundError:
            pass
        temporary = f".shahinkit-tmp-{uuid.uuid4().hex}"
        handle = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode, dir_fd=directory)
        try:
            view = memoryview(data)
            while view:
                view = view[os.write(handle, view):]
            os.fsync(handle)
        finally:
            os.close(handle)
        os.replace(temporary, path.name, src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)
    finally:
        os.close(directory)


def secure_unlink(path: Path) -> None:
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        fail("secure POSIX dirfd primitives unavailable")
    assert_no_symlink(path)
    directory = os.open(path.parent.absolute(), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        mode = os.stat(path.name, dir_fd=directory, follow_symlinks=False).st_mode
        if stat.S_ISLNK(mode):
            fail(f"symlink rejected: {path}")
        os.unlink(path.name, dir_fd=directory)
        os.fsync(directory)
    finally:
        os.close(directory)


def write_backup(root: Path, operations: list[dict]) -> str | None:
    if not operations:
        return None
    backup_id = f"{dt.datetime.now(dt.UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:12]}"
    backup = {"schema_version": SCHEMA_VERSION, "backup_id": backup_id, "operations": operations}
    directory = safe_child(root, BACKUP_DIR)
    write_atomic(safe_child(directory, f"{backup_id}.json"), canonical_json(backup) + b"\n")
    backups = sorted(directory.glob("*.json"), key=lambda item: item.name)
    for stale in backups[:-BACKUP_RETENTION]:
        assert_no_symlink(stale)
        secure_unlink(stale)
    return backup_id


def operation_from_old(base: str, relative: str, old: bytes | None, after: bytes | None = None) -> dict:
    operation = {"base": base, "path": relative, "kind": "absent" if old is None else "file"}
    if old is not None:
        operation["before_b64"] = base64.b64encode(old).decode()
    if after is not None:
        operation["after_sha256"] = digest(after)
    return operation


def apply_plan(root: Path, home: Path, agent: str, scope: str, features: dict[str, bool], provenance_data: dict, plan: list[dict], prior: dict | None) -> dict:
    backups = []
    owned = []
    baseline = {receipt_key(item): item for item in (prior or {}).get("baseline", [])}
    for change in plan:
        path, old, ownership = change["path"], change["old"], change["ownership"]
        base, relative = change["base"], change["relative"]
        backups.append(operation_from_old(base, relative, old, change["data"]))
        baseline.setdefault((base, relative), operation_from_old(base, relative, old))
    # Durably persist all preimages before touching a destination. If any
    # subsequent write fails, restore exact in-memory preimages immediately.
    backup_id = write_backup(root, backups) or (prior or {}).get("backup_id")
    backup_sha256 = None
    if backup_id:
        backup_sha256 = digest(safe_child(root, f"{BACKUP_DIR}/{backup_id}.json", required=True).read_bytes())
    written = []
    try:
        for change in plan:
            if change["ownership"]["kind"] == "remove":
                secure_unlink(change["path"])
            else:
                write_atomic(change["path"], change["data"], 0o600)
            written.append(change)
    except Exception:
        for change in reversed(written):
            if change["old"] is None:
                if change["path"].exists():
                    secure_unlink(change["path"])
            else:
                write_atomic(change["path"], change["old"], 0o600)
        raise
    # Preserve previous ownership for unchanged files; changed desired state owns new bytes.
    by_path = {receipt_key(item): item for item in (prior or {}).get("owned", [])}
    for change in plan:
        base, relative = change["base"], change["relative"]
        key = (base, relative)
        if change["ownership"]["kind"] == "remove":
            by_path.pop(key, None)
        else:
            by_path[key] = {"base": base, "path": relative, "sha256": digest(change["data"]), "kind": change["ownership"]["kind"], "marker": change["ownership"].get("marker"), "changes": change["ownership"].get("changes", {})}
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "receipt_id": uuid.uuid4().hex,
        "adapter": agent,
        "scope": scope,
        "features": features,
        "owned": sorted(by_path.values(), key=lambda item: (item["base"], item["path"])),
        "baseline": sorted(baseline.values(), key=lambda item: (item["base"], item["path"])),
        "backup_id": backup_id,
        "backup_sha256": backup_sha256,
        "source_manifest_sha256": digest(read_source(MANIFEST_NAME)),
        "provenance": provenance_data,
        "fresh_session_verification": "Restart host; confirm selected modes and local-only Basic Memory before relying on install.",
    }
    if prior:
        receipt["previous_receipt"] = prior
    receipt["integrity_sha256"] = digest(canonical_json(receipt_payload(receipt)))
    write_atomic(receipt_path(root), json.dumps(receipt, indent=2, sort_keys=True).encode() + b"\n")
    return receipt


def preview_payload(label: str, root: Path, home: Path, agent: str, scope: str, features: dict[str, bool], provenance_data: dict, plan: list[dict], prior: dict | None) -> dict:
    return {
        "command": label,
        "agent": agent,
        "scope": scope,
        "bases": {"root": str(root.resolve(strict=False)), "home": str(home.resolve(strict=False))},
        "features": features,
        "provenance": provenance_data,
        "receipt_id": (prior or {}).get("receipt_id"),
        "operations": [{"base": change["base"], "path": change["relative"], "action": change["ownership"]["kind"], "preimage_sha256": digest(change["old"]) if change["old"] is not None else None, "output_sha256": digest(change["data"]) if change["data"] is not None else None} for change in plan],
    }


def preview(label: str, root: Path, home: Path, agent: str, scope: str, features: dict[str, bool], provenance_data: dict, plan: list[dict], prior: dict | None) -> str:
    preview_data = preview_payload(label, root, home, agent, scope, features, provenance_data, plan, prior)
    preview_digest = digest(canonical_json(preview_data))
    print(f"{label}: adapter={agent} scope={scope} root={root} home={home}")
    print(f"provenance={provenance_data['kind']} repository={provenance_data['repository']} head={provenance_data['head']} tag={provenance_data['tag']}")
    print(f"features=ponytail:{str(features['ponytail']).lower()} caveman:{str(features['caveman']).lower()} trust-host required")
    for change in plan:
        action = "create" if change["old"] is None else "managed-change"
        print(f"{action}: {change['base']}:{change['relative']} preimage={digest(change['old']) if change['old'] is not None else 'absent'}")
    if not plan:
        print("no changes (idempotent)")
    print("fresh-session: restart host and verify selected modes; trust remains host-controlled.")
    print(f"preview-digest: {preview_digest}")
    return preview_digest


def assert_owned_current(root: Path, home: Path, item: dict) -> Path:
    base, relative = receipt_key(item)
    path = location_path(root, home, base, relative, required=True)
    if digest(path.read_bytes()) != item["sha256"]:
        fail(f"managed file modified or missing: {base}:{relative}")
    return path


def current_owned_unchanged(root: Path, home: Path, receipt: dict) -> None:
    for item in receipt["owned"]:
        assert_owned_current(root, home, item)


def receipt_outputs_match_manifest(root: Path, receipt: dict, outputs: list[dict]) -> None:
    """Receipt narrows ownership; current verified render map remains authority."""
    allowed = {output_key(output) for output in outputs}
    for item in receipt["owned"]:
        base, relative = receipt_key(item)
        if (base, relative) not in allowed:
            fail(f"receipt path is not current manifest output: {base}:{relative}")


def restore_operations(root: Path, home: Path, operations: list[dict], receipt: dict) -> list[str]:
    owned = {receipt_key(item): item for item in receipt["owned"]}
    restored = []
    for operation in operations:
        base, relative = location_key(operation.get("base", ""), operation.get("path", ""))
        item = owned.get((base, relative))
        if item:
            # Revalidate immediately before each destructive lifecycle write.
            assert_owned_current(root, home, item)
        path = location_path(root, home, base, relative)
        if not item:
            expected = operation.get("after_sha256")
            current = path.read_bytes() if path.exists() else None
            if (expected is None and current is not None) or (expected is not None and (current is None or digest(current) != expected)):
                fail(f"managed file modified or missing: {base}:{relative}")
        if operation.get("kind") == "absent":
            if path.exists():
                secure_unlink(path)
        elif operation.get("kind") == "file":
            try:
                before = base64.b64decode(operation["before_b64"], validate=True)
            except (KeyError, ValueError):
                fail("invalid backup preimage")
            write_atomic(path, before)
        else:
            fail("invalid backup operation")
        restored.append(f"{base}:{relative}")
    return restored


def remove_owned(root: Path, home: Path, receipt: dict) -> list[str]:
    current_owned_unchanged(root, home, receipt)
    baseline = receipt.get("baseline")
    if not isinstance(baseline, list):
        fail("receipt baseline missing")
    removed = restore_operations(root, home, baseline, receipt)
    secure_unlink(receipt_path(root))
    return removed


def rollback(root: Path, home: Path, receipt: dict) -> list[str]:
    current_owned_unchanged(root, home, receipt)
    backup_id = receipt.get("backup_id")
    if not backup_id:
        fail("receipt has no backup")
    backup_path = safe_child(root, f"{BACKUP_DIR}/{backup_id}.json", required=True)
    if receipt.get("backup_sha256") != digest(backup_path.read_bytes()):
        fail("backup integrity mismatch")
    backup = load_json(backup_path)
    operations = backup.get("operations")
    if not isinstance(operations, list):
        fail("invalid backup operations")
    restored = restore_operations(root, home, operations, receipt)
    previous = receipt.get("previous_receipt")
    if previous:
        write_atomic(receipt_path(root), json.dumps(previous, indent=2, sort_keys=True).encode() + b"\n")
    else:
        secure_unlink(receipt_path(root))
    return restored


def detect_agent(scope: str, destination: str | None) -> str:
    matches = []
    checks = {
        "claude-code": ("CLAUDE_CODE_VERSION", "settings.json" if scope == "user" else ".claude/settings.json", "https://json.schemastore.org/claude-code-settings.json", (2, 1, 209), (2, 2, 0)),
        "opencode": ("OPENCODE_VERSION", "opencode.jsonc", "https://opencode.ai/config.json", (1, 17, 20), (2, 0, 0)),
        "codex": ("CODEX_VERSION", "config.toml" if scope == "user" else ".codex/config.toml", None, (0, 144, 5), (0, 145, 0)),
    }
    for agent, (environment, config, schema, minimum, maximum) in checks.items():
        root, _ = root_for(agent, scope, destination)
        version = os.environ.get(environment)
        path = safe_child(root, config)
        if not version or not path.exists():
            continue
        try:
            parsed_version = tuple(int(piece) for piece in version.split("."))
        except ValueError:
            continue
        if len(parsed_version) != 3 or not minimum <= parsed_version < maximum:
            continue
        try:
            parsed = tomllib.loads(path.read_text()) if agent == "codex" else json.loads(path.read_text())
        except (json.JSONDecodeError, tomllib.TOMLDecodeError):
            continue
        if schema is None or parsed.get("$schema") == schema:
            matches.append(agent)
    if len(matches) != 1:
        fail("auto detection requires exactly one complete verified marker set; use --agent explicitly")
    return matches[0]


def sync(check_only: bool) -> int:
    manifest = load_manifest()
    entries = manifest.get("manager", {}).get("sync_generated", [])
    if not isinstance(entries, list):
        fail("invalid sync manifest")
    drift = []
    for entry in entries:
        source, target = entry.get("source"), entry.get("target")
        if not isinstance(source, str) or not isinstance(target, str) or not source.startswith(("school/shared/", "school/third_party/")):
            fail("sync source must be declared canonical school/shared/vendor asset")
        data = read_source(source)
        path = safe_child(ROOT, target)
        if path.exists() and path.read_bytes() == data:
            continue
        drift.append((source, target, data))
    for source, target, data in drift:
        print(f"drift: {target} <- {source}")
    if drift and check_only:
        return 1
    if drift:
        for _, target, data in drift:
            write_atomic(safe_child(ROOT, target), data, 0o644)
    print("sync: clean" if not drift else f"sync: wrote {len(drift)} file(s)")
    return 0


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sync_parser = sub.add_parser("sync")
    group = sync_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    for name in ("install", "update", "uninstall", "rollback"):
        command = sub.add_parser(name)
        command.add_argument("--agent", choices=(*AGENTS, "auto"), default="auto")
        command.add_argument("--scope", choices=("user", "project"), required=True)
        command.add_argument("--destination")
        command.add_argument("--apply", action="store_true")
        command.add_argument("--preview", action="store_true")
        command.add_argument("--preview-digest", metavar="SHA256")
        command.add_argument("--allow-development-checkout", action="store_true")
        if name == "rollback":
            command.add_argument("--receipt", help="destination receipt ID; must match local receipt")
        if name in ("install", "update"):
            command.add_argument("--trust-host", action="store_true")
            command.add_argument("--without-ponytail", action="store_true")
            command.add_argument("--without-caveman", action="store_true")
            command.add_argument("--with-basic-memory", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = arguments()
    try:
        if args.command == "sync":
            return sync(args.check)
        agent = detect_agent(args.scope, args.destination) if args.agent == "auto" else args.agent
        root, home = root_for(agent, args.scope, args.destination)
        if args.command in ("install", "update"):
            if args.apply and not args.trust_host:
                fail("--apply requires --trust-host; installer never grants host trust")
            if args.apply and not args.preview_digest:
                fail("--apply requires --preview-digest from a matching prior preview")
            provenance_data = provenance(args.allow_development_checkout)
            features = {"ponytail": not args.without_ponytail, "caveman": not args.without_caveman, "basic-memory": args.with_basic_memory}
            prior = verify_receipt(root) if args.command == "update" else None
            if prior and (prior["adapter"] != agent or prior["scope"] != args.scope):
                fail("receipt adapter/scope mismatch")
            outputs = outputs_for(agent, args.scope, root, home, features)
            if prior:
                prior_outputs = outputs_for(agent, args.scope, root, home, prior["features"])
                receipt_outputs_match_manifest(root, prior, prior_outputs)
                current_owned_unchanged(root, home, prior)
            plan = changed_plan(outputs, root, home, prior)
            if prior:
                current_paths = {output_key(output) for output in outputs}
                for item in prior["owned"]:
                    base, relative = receipt_key(item)
                    if (base, relative) not in current_paths:
                        path = location_path(root, home, base, relative, required=True)
                        plan.append({"path": path, "base": base, "relative": relative, "data": None, "old": path.read_bytes(), "ownership": {"kind": "remove"}})
            preview_digest = preview(args.command, root, home, agent, args.scope, features, provenance_data, plan, prior)
            if args.apply:
                if args.preview_digest != preview_digest:
                    fail("preview digest mismatch; run preview again and copy its exact digest")
                # Re-check exact preimages after digest comparison, immediately before mutation.
                for change in plan:
                    assert_no_symlink(change["path"])
                    current = change["path"].read_bytes() if change["path"].exists() else None
                    if current != change["old"]:
                        fail(f"planned preimage changed: {change['base']}:{change['relative']}")
                if not plan and prior:
                    print("applied: no changes (idempotent)")
                else:
                    apply_plan(root, home, agent, args.scope, features, provenance_data, plan, prior)
                    print("applied: restart host and complete fresh-session verification")
            return 0
        receipt = verify_receipt(root)
        if receipt["adapter"] != agent or receipt["scope"] != args.scope:
            fail("receipt adapter/scope mismatch")
        receipt_outputs_match_manifest(root, receipt, outputs_for(agent, args.scope, root, home, receipt["features"]))
        if args.apply and not args.preview_digest:
            fail("--apply requires --preview-digest from a matching prior preview")
        if args.command == "rollback" and args.receipt and args.receipt != receipt["receipt_id"]:
            fail("rollback receipt ID does not match destination receipt")
        if args.command == "uninstall":
            current_owned_unchanged(root, home, receipt)
            plan = [{"base": item["base"], "relative": item["path"], "old": location_path(root, home, item["base"], item["path"], required=True).read_bytes(), "data": None, "ownership": {"kind": "remove"}} for item in receipt["owned"]]
            digest_value = preview("uninstall", root, home, agent, args.scope, receipt["features"], receipt["provenance"], plan, receipt)
            if args.apply:
                if args.preview_digest != digest_value:
                    fail("preview digest mismatch; run preview again and copy its exact digest")
                print("removed: " + ", ".join(remove_owned(root, home, receipt)))
        else:
            current_owned_unchanged(root, home, receipt)
            backup_id = receipt.get("backup_id")
            if not backup_id:
                fail("receipt has no backup")
            backup = load_json(safe_child(root, f"{BACKUP_DIR}/{backup_id}.json", required=True))
            operations = backup.get("operations")
            if not isinstance(operations, list):
                fail("invalid backup operations")
            plan = [{"base": item["base"], "relative": item["path"], "old": location_path(root, home, item["base"], item["path"], required=True).read_bytes() if location_path(root, home, item["base"], item["path"]).exists() else None, "data": base64.b64decode(item["before_b64"]) if item.get("kind") == "file" else None, "ownership": {"kind": "rollback"}} for item in operations]
            digest_value = preview("rollback", root, home, agent, args.scope, receipt["features"], receipt["provenance"], plan, receipt)
            if args.apply:
                if args.preview_digest != digest_value:
                    fail("preview digest mismatch; run preview again and copy its exact digest")
                print("restored: " + ", ".join(rollback(root, home, receipt)))
        return 0
    except ManagerError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
