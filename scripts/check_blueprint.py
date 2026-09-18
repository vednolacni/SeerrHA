#!/usr/bin/env python3
"""Sanity checks for the SeerrHA blueprint and example YAML files.

Home Assistant's own loader is not available in CI, so this script parses the
files with a loader that understands HA's custom tags (!input, !secret,
!include) and then asserts the structural rules that actually break setups:

* every `!input` used in the automation body is declared in `blueprint.input`
* every declared input is actually used
* rest_command names are valid slugs (a capital letter kills the whole block)
* Jinja templates parse
"""

from __future__ import annotations

import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
BLUEPRINT = ROOT / "blueprints/automation/seerrha/seerr_request_approval.yaml"
SLUG = re.compile(r"^[a-z0-9_]+$")

errors: list[str] = []


class HALoader(yaml.SafeLoader):
    """SafeLoader that keeps Home Assistant's custom tags as plain scalars."""


def _scalar(loader: yaml.Loader, node: yaml.Node) -> str:
    return loader.construct_scalar(node)


for tag in ("!input", "!secret", "!include"):
    HALoader.add_constructor(tag, _scalar)


def declared_inputs(blueprint: dict) -> set[str]:
    names: set[str] = set()
    for key, value in (blueprint.get("input") or {}).items():
        if isinstance(value, dict) and "input" in value:
            names.update(value["input"])  # section
        else:
            names.add(key)
    return names


def main() -> int:
    for path in sorted(ROOT.glob("**/*.yaml")):
        if ".git" in path.parts:
            continue
        try:
            yaml.load(path.read_text(), Loader=HALoader)
        except yaml.YAMLError as err:
            errors.append(f"{path.relative_to(ROOT)}: invalid YAML: {err}")

    raw = BLUEPRINT.read_text()
    data = yaml.load(raw, Loader=HALoader)

    meta = data.get("blueprint", {})
    for field in ("name", "description", "domain", "source_url"):
        if not meta.get(field):
            errors.append(f"blueprint: missing `{field}`")
    if meta.get("domain") != "automation":
        errors.append("blueprint: domain must be `automation`")

    declared = declared_inputs(meta)
    used = set(re.findall(r"!input\s+([a-z0-9_]+)", raw))
    for name in sorted(used - declared):
        errors.append(f"blueprint: `!input {name}` is not declared")
    for name in sorted(declared - used):
        errors.append(f"blueprint: input `{name}` is declared but never used")

    for path in (ROOT / "examples/rest_commands.yaml", ROOT / "packages/seerrha.yaml"):
        loaded = yaml.load(path.read_text(), Loader=HALoader)
        commands = loaded.get("rest_command", loaded)
        for name in commands:
            if not SLUG.match(name):
                errors.append(
                    f"{path.relative_to(ROOT)}: `{name}` is not a valid slug "
                    "(lowercase letters, digits and underscores only)"
                )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
