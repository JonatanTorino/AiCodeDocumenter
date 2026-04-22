#!/usr/bin/env python3
"""
Emit one `_tracking/diagram_candidates/<slug>.yaml` per functional group
in a document-xpp workspace.

This is the deterministic input to Fase 3. The `diagram-writer` agent
consumes these candidate YAMLs and, for each group, opens the `.xpp`
files referenced by `nodes[].file` and the DBML at
`sources.dbml_path` to decide how to render the class diagram.

Inputs (read from <workspace>):
    _tracking/manifest.yaml          -> xpp_root, dbml_path
    _tracking/inventory.csv          -> node metadata (parent, artifact_kind, ...)
    _tracking/dependencies.csv       -> edges
    _tracking/funcionalidades/*.yaml -> group membership (one file per group)

Exclusion list (read from the plugin references):
    plugins/document-xpp/skills/document-xpp/references/exclusion-list.md
    Any `to_class` in dependencies.csv whose name (case-insensitive)
    matches a backticked identifier on a bullet line is dropped silently.

Output (written under <workspace>):
    _tracking/diagram_candidates/<slug>.yaml

Schema: see `references/tracking-schema.md`, section
    `_tracking/diagram_candidates/<slug>.yaml`.

Requires: Python >= 3.10, PyYAML (declared in pyproject.toml).
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit(
        f"build_class_diagrams.py requires Python >= 3.10 "
        f"(pyproject.toml declares `requires-python = \">=3.10\"`); "
        f"running on {sys.version.split()[0]}."
    )

try:
    import yaml  # type: ignore
except ImportError:
    sys.exit(
        "build_class_diagrams.py requires PyYAML. Install it via "
        "`pip install pyyaml` or, at repo root, `pip install -e .` "
        "(pyproject.toml declares the dependency)."
    )

SCHEMA_VERSION = 1

# Path segments that tag a class as a table/view. The upstream xml->xpp
# extractor places AxTable methods under `.../AxTable/<TableName>.xpp`,
# and AxView under `.../AxView/<ViewName>.xpp`. The check is on POSIX-
# normalized path segments so forward slashes are assumed.
TABLE_SEGMENT = "/AxTable/"
VIEW_SEGMENT = "/AxView/"


def load_exclusion_set(exclusion_md: Path) -> set[str]:
    """Extract every backticked identifier from bullet lines."""
    text = exclusion_md.read_text(encoding="utf-8")
    names: set[str] = set()
    for line in text.splitlines():
        if not line.lstrip().startswith("- "):
            continue
        for match in re.findall(r"`([^`]+)`", line):
            # exclusion-list entries may include punctuation like commas
            # inside a single backtick block (rare); split defensively.
            for token in re.split(r"[,\s]+", match):
                token = token.strip()
                if token:
                    names.add(token.lower())
    return names


def read_csv_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def detect_artifact_kind(file_rel: str, inventory_kind: str) -> str:
    """Upgrade `class`/`interface` from inventory to `table`/`view`
    when the file path makes it obvious. Leaves `interface` untouched.
    Enum/EDT are preserved verbatim (dormant in M2 — no rows expected).
    """
    posix = file_rel.replace("\\", "/")
    if inventory_kind == "interface":
        return "interface"
    if TABLE_SEGMENT in posix:
        return "table"
    if VIEW_SEGMENT in posix:
        return "view"
    return inventory_kind  # 'class', 'enum', 'edt'


def build_class_to_group(func_dir: Path) -> dict[str, str]:
    """Return {class_name: slug} across every funcionalidad YAML.

    For ambiguous class names (same name across multiple artifact kinds,
    e.g. AxForm + AxTable) the first occurrence wins. Externals only use
    this as a boolean hint for `in_inventory` + a best-effort slug.
    """
    mapping: dict[str, str] = {}
    for yaml_file in sorted(func_dir.glob("*.yaml")):
        data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        slug = data.get("slug") or yaml_file.stem
        for c in data.get("classes") or []:
            if isinstance(c, dict) and c.get("class"):
                mapping.setdefault(c["class"], slug)
    return mapping


def build_candidate(
    funcionalidad: dict,
    inventory_by_key: dict[tuple[str, str], dict],
    inventory_classes: set[str],
    dependencies: list[dict],
    class_to_group: dict[str, str],
    exclusion_lower: set[str],
    manifest_sources: dict,
) -> dict:
    slug = funcionalidad["slug"]

    # Group identity is the (class, file) pair — NOT just class name.
    # tracking-schema.md says the same class name may appear multiple
    # times in inventory.csv and dependencies.csv (AxForm + AxTable,
    # etc), disambiguated by file/from_file. Collapsing by name would
    # point nodes[].file to the wrong .xpp or drop edges from the
    # sibling artifact.
    group_keys: set[tuple[str, str]] = set()
    group_class_names: set[str] = set()
    for c in funcionalidad.get("classes") or []:
        if isinstance(c, dict) and c.get("class") and c.get("file"):
            group_keys.add((c["class"], c["file"]))
            group_class_names.add(c["class"])

    nodes: list[dict] = []
    for c in funcionalidad.get("classes") or []:
        class_name = c.get("class")
        file_rel = c.get("file")
        if not class_name or not file_rel:
            continue
        inv = inventory_by_key.get((class_name, file_rel))
        if inv is None:
            # Entry declared in funcionalidad but not in current inventory
            # under that exact file. Likely renamed/deleted/moved since
            # classification — skip; the workflow surfaces this on reruns.
            continue
        interfaces_raw = (inv.get("interfaces") or "").strip()
        interfaces = [i for i in interfaces_raw.split(";") if i]
        nodes.append({
            "class": class_name,
            "file": inv["file"],
            "role": c.get("role", "other"),
            "artifact_kind": detect_artifact_kind(inv["file"], inv.get("artifact_kind", "class")),
            "parent": inv.get("parent", "") or "",
            "interfaces": interfaces,
            "methods_count": int(inv.get("methods_count") or 0),
        })

    edges: list[dict] = []
    external_candidates: set[str] = set()
    for dep in dependencies:
        # Filter deps by the (from_class, from_file) pair so a class
        # that exists as both AxForm and AxTable does not bleed edges
        # from the sibling artifact into this group.
        dep_key = (dep.get("from_class", ""), dep.get("from_file", ""))
        if dep_key not in group_keys:
            continue
        to_class = dep["to_class"]
        if to_class.lower() in exclusion_lower:
            continue
        # Heterogeneous targets: dependencies.csv does not carry
        # `to_file`, so `to_in == node` uses class-name membership in
        # the group. Acceptable because the target is addressed by
        # name inside the .xpp (no artifact ambiguity at the call site
        # beyond what the language already resolves).
        if to_class in group_class_names:
            to_in = "node"
        else:
            to_in = "external_ref"
            external_candidates.add(to_class)
        edges.append({
            "from": dep["from_class"],
            "to": to_class,
            "kind": dep["kind"],
            "to_in": to_in,
        })

    external_refs: list[dict] = []
    for cls in sorted(external_candidates):
        in_inv = cls in inventory_classes
        other_slug = class_to_group.get(cls, "") if in_inv else ""
        external_refs.append({
            "class": cls,
            "in_inventory": in_inv,
            "other_group_slug": other_slug,
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "group": {
            "slug": slug,
            "name": funcionalidad.get("name", slug),
            "description": (funcionalidad.get("description") or "").strip(),
        },
        "sources": {
            "xpp_root": manifest_sources.get("xpp_root", ""),
            "dbml_path": manifest_sources.get("dbml_path", "") or "",
        },
        "nodes": nodes,
        "external_refs": external_refs,
        "edges": edges,
    }


def default_exclusion_md() -> Path:
    """Exclusion list lives beside this script's parent `references/`."""
    return Path(__file__).resolve().parent.parent / "references" / "exclusion-list.md"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path,
                        help="Documentation workspace (must contain _tracking/).")
    parser.add_argument("--exclusion-list", type=Path, default=None,
                        help="Override exclusion-list.md path (defaults to plugin's copy).")
    args = parser.parse_args()

    workspace: Path = args.workspace.resolve()
    tracking = workspace / "_tracking"
    if not tracking.is_dir():
        sys.exit(f"Workspace has no _tracking/ — expected at {tracking}")

    manifest_path = tracking / "manifest.yaml"
    inventory_path = tracking / "inventory.csv"
    dependencies_path = tracking / "dependencies.csv"
    funcionalidades_dir = tracking / "funcionalidades"

    for required in (manifest_path, inventory_path, dependencies_path, funcionalidades_dir):
        if not required.exists():
            sys.exit(f"Missing required input: {required}")

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    sources = manifest.get("sources") or {}

    exclusion_md = args.exclusion_list or default_exclusion_md()
    if not exclusion_md.is_file():
        sys.exit(f"exclusion-list.md not found at {exclusion_md}")
    exclusion_lower = load_exclusion_set(exclusion_md)

    inventory = read_csv_rows(inventory_path)
    # Index inventory by (class, file). The same class name may appear
    # multiple times across artifacts (AxForm + AxTable both named
    # `AxnLicParameters`, etc), and each artifact has its own methods
    # and dependencies. Collapsing by name would corrupt nodes[].file.
    inventory_by_key: dict[tuple[str, str], dict] = {}
    inventory_classes: set[str] = set()
    for row in inventory:
        cls = row.get("class") or ""
        file_rel = row.get("file") or ""
        if not cls or not file_rel:
            continue
        inventory_by_key[(cls, file_rel)] = row
        inventory_classes.add(cls)

    dependencies = read_csv_rows(dependencies_path)
    class_to_group = build_class_to_group(funcionalidades_dir)

    yamls = sorted(funcionalidades_dir.glob("*.yaml"))
    if not yamls:
        sys.exit("No funcionalidades/*.yaml found — run Fase 2 first.")

    out_dir = tracking / "diagram_candidates"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"workspace       -> {workspace}")
    print(f"xpp_root        -> {sources.get('xpp_root', '(missing)')}")
    print(f"dbml_path       -> {sources.get('dbml_path') or '(empty — Fase 3 will prompt)'}")
    print(f"inventory rows  -> {len(inventory)}")
    print(f"dependency rows -> {len(dependencies)}")
    print(f"exclusion names -> {len(exclusion_lower)}")
    print(f"funcionalidades -> {len(yamls)}")
    print()

    written = 0
    for yaml_file in yamls:
        data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not data.get("slug"):
            print(f"  SKIP  {yaml_file.name} — missing slug")
            continue
        candidate = build_candidate(
            funcionalidad=data,
            inventory_by_key=inventory_by_key,
            inventory_classes=inventory_classes,
            dependencies=dependencies,
            class_to_group=class_to_group,
            exclusion_lower=exclusion_lower,
            manifest_sources=sources,
        )
        out_path = out_dir / f"{data['slug']}.yaml"
        out_path.write_text(
            yaml.safe_dump(candidate, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        n_nodes = len(candidate["nodes"])
        n_ext = len(candidate["external_refs"])
        n_edges = len(candidate["edges"])
        print(f"  OK    {out_path.name:32s}  nodes={n_nodes:3d}  external_refs={n_ext:3d}  edges={n_edges:3d}")
        written += 1

    print()
    print(f"diagram_candidates -> {out_dir} ({written} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
