#!/usr/bin/env python3
"""Sanity checks for the SeerrHA blueprints, example YAML and Glance widget.

Home Assistant's own loader is not available in CI, so this script parses the
files with a loader that understands HA's custom tags (!input, !secret,
!include) and then asserts the structural rules that actually break setups:

* every `!input` used in the automation body is declared in `blueprint.input`
* every declared input is actually used
* rest_command names are valid slugs (a capital letter kills the whole block)
* the Glance widget's README embeds exactly the YAML in widget.yml, and its
  meta.yml has the fields community-widgets requires
"""

from __future__ import annotations

import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
BLUEPRINTS = sorted((ROOT / "blueprints/automation/seerrha").glob("*.yaml"))
GLANCE = ROOT / "glance/seerr-requests"
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


def check_blueprint(path: pathlib.Path) -> None:
    name = path.relative_to(ROOT)
    raw = path.read_text()
    data = yaml.load(raw, Loader=HALoader)

    meta = data.get("blueprint", {})
    for field in ("name", "description", "domain", "source_url"):
        if not meta.get(field):
            errors.append(f"{name}: missing `{field}`")
    if meta.get("domain") != "automation":
        errors.append(f"{name}: domain must be `automation`")
    if not str(meta.get("source_url", "")).endswith(str(name)):
        errors.append(f"{name}: source_url does not point at this file")

    declared = declared_inputs(meta)
    used = set(re.findall(r"!input\s+([a-z0-9_]+)", raw))
    for input_name in sorted(used - declared):
        errors.append(f"{name}: `!input {input_name}` is not declared")
    for input_name in sorted(declared - used):
        errors.append(f"{name}: input `{input_name}` is declared but never used")


def check_glance_widget() -> None:
    widget = (GLANCE / "widget.yml").read_text().rstrip("\n")
    readme = (GLANCE / "README.md").read_text()
    match = re.search(r"## Widget YAML.*?```yaml\n(.*?)\n```", readme, re.S)
    if not match:
        errors.append("glance: README.md has no ```yaml block under ## Widget YAML")
    elif match.group(1) != widget:
        errors.append("glance: the YAML in README.md differs from widget.yml")

    meta = yaml.safe_load((GLANCE / "meta.yml").read_text()) or {}
    for field in ("title", "description", "author"):
        if not meta.get(field):
            errors.append(f"glance: meta.yml is missing `{field}`")
    if not (GLANCE / "preview.png").exists():
        errors.append("glance: preview.png is missing")


def main() -> int:
    for path in sorted(ROOT.glob("**/*.yaml")):
        if ".git" in path.parts:
            continue
        try:
            yaml.load(path.read_text(), Loader=HALoader)
        except yaml.YAMLError as err:
            errors.append(f"{path.relative_to(ROOT)}: invalid YAML: {err}")

    for blueprint in BLUEPRINTS:
        check_blueprint(blueprint)

    for path in (ROOT / "examples/rest_commands.yaml", ROOT / "packages/seerrha.yaml"):
        loaded = yaml.load(path.read_text(), Loader=HALoader)
        commands = loaded.get("rest_command", loaded)
        for name in commands:
            if not SLUG.match(name):
                errors.append(
                    f"{path.relative_to(ROOT)}: `{name}` is not a valid slug "
                    "(lowercase letters, digits and underscores only)"
                )

    check_glance_widget()

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
