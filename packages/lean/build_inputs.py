"""Describe the exact local sources and installed import artifacts of an export.

This module reads files only. It neither executes Lake nor trusts declarations.
"""

import hashlib
from pathlib import Path
import re

FORMAT = "slean-lean-build-inputs/0.1-draft.1"
PARTS = (".olean", ".olean.server", ".olean.private", ".ir", ".ir.sig")


def file_digest(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def module_path(name):
    # Lean's ordinary path convention; do not flatten quoted/numeric names.
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*", name):
        raise ValueError("Unsupported module path: " + name)
    return Path(*name.split("."))


def package_directory(name):
    value = name[1:-1] if name.startswith("«") and name.endswith("»") else name
    if not value or value in {".", ".."} or "/" in value or "\\" in value:
        raise ValueError("Unsafe Lake package name")
    return value


def roots(project, lock, toolchain):
    entries = [{"name": "root", "kind": "source", "directory": project.resolve()},
               {"name": "lean", "kind": "toolchain", "directory": toolchain.resolve() / "src/lean"},
               {"name": "lean", "kind": "toolchain", "directory": toolchain.resolve() / "src/lean/lake"}]
    for package in lock["packages"]:
        if package["type"] == "path":
            directory = (project / package["dir"]).resolve()
            kind = "source"
        elif package["type"] == "git":
            directory = (project / lock["packagesDir"] / package_directory(package["name"])).resolve()
            kind = "dependency"
        else:
            raise ValueError("Unsupported Lake dependency")
        entries.append({"name": package["name"], "kind": kind, "directory": directory,
                        "revision": package.get("rev"), "url": package.get("url")})
    # Nested Lake checkouts belong to their dependency, not the encompassing root.
    return sorted(entries, key=lambda item: len(item["directory"].parts), reverse=True)


def compiled_parts(base):
    base = Path(base)
    parts = []
    for suffix in PARTS:
        path = base.with_suffix(suffix)
        if path.is_file():
            parts.append({"suffix": suffix, "size": str(path.stat().st_size), "sha256": file_digest(path)})
    if not parts or parts[0]["suffix"] != ".olean":
        raise ValueError("Missing compiled module")
    return parts


def snapshot(raw, project, lock, toolchain, add, canonical):
    if "modules" not in raw:
        return  # Older extraction remains inspectable, not reconstructable.
    locations = roots(project, lock, toolchain)
    selected = {item["module"] for item in raw["declarations"]}
    modules, seen = [], set()
    for item in raw["modules"]:
        name = item["module"]
        relative = module_path(name)
        if item["module_name"] != [["str", part] for part in name.split(".")] or name in seen:
            raise ValueError("Ambiguous module name or duplicate import")
        seen.add(name)
        source = Path(item["source_path"]).resolve(strict=True)
        origin = next((entry for entry in locations if source.is_relative_to(entry["directory"])), None)
        if origin is None or source.suffix != ".lean":
            raise ValueError("Module source is outside the declared environment")
        if source.relative_to(origin["directory"]) != relative.with_suffix(".lean"):
            raise ValueError("Unsupported source-root layout")
        compiled = Path(item["compiled_path"]).resolve(strict=True)
        expected = (toolchain / "lib/lean" if origin["kind"] == "toolchain"
                    else origin["directory"] / ".lake/build/lib/lean") / relative.with_suffix(".olean")
        if compiled != expected.resolve(strict=True):
            raise ValueError("Compiled module differs from its source origin")
        kind = "source" if name in selected else origin["kind"]
        record = {"module": name, "imports": item["imports"], "kind": kind,
                  "package": origin["name"]}
        if kind == "source":
            data = source.read_bytes()
            record["source"] = add("sources/" + hashlib.sha256(data).hexdigest() + ".lean", data)
        else:
            record["compiled"] = compiled_parts(compiled)
        modules.append(record)
    if not selected.issubset(seen) or any(set(item["imports"]) - seen for item in modules):
        raise ValueError("Incomplete import closure")
    packages = {entry["name"]: {k: entry[k] for k in ("name", "kind", "revision", "url") if k in entry}
                for entry in locations if any(item["package"] == entry["name"] for item in modules)}
    value = {"format": FORMAT, "toolchain": raw["lean_version"],
             "modules": sorted(modules, key=lambda item: item["module"]),
             "packages": sorted(packages.values(), key=lambda item: item["name"])}
    add("environment/build-inputs.json", canonical(value) + b"\n")
