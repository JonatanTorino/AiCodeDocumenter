#!/usr/bin/env python3
"""
Parse .xpp files (D365 F&O classes, interfaces) and AxEnum/AxEdt XML metadata
under a SourcePath, and produce inventory.csv + dependencies.csv under an
OutputPath.

Schemas (see plugins/document-xpp/skills/document-xpp/references/tracking-schema.md):

inventory.csv columns:
    file, class, parent, interfaces, methods_count, prefix, artifact_kind

dependencies.csv columns:
    from_class, from_file, to_class, kind

`file` / `from_file` always use '/' as path separator regardless of host OS.

Static analysis coverage:
    - class X, class X extends Y, class X implements I1, I2
    - interface IName
    - methods with any combination of modifiers (public/private/protected/static/final/abstract/internal/...)
    - interface methods (no modifiers)
    - dependency kinds: extends, implements, uses (new Z()), calls (X::member)
    - AxEnum / AxEdt: parsed from <ModuleRoot>/AxEnum/*.xml and <ModuleRoot>/AxEdt/*.xml
      (recursive); only the <Name> element is extracted.

Known limitations (inherited from M1 parser contract):
    - [ExtensionOf(...)] is NOT resolved to the extended class.
    - X++ macros (#define) and pragmas are ignored.
    - Field / parameter types are not extracted as dependencies.
    - One class/interface per .xpp file (AxClass convention).
    - Duplicate class names across artifact types (AxForm + AxTable) produce
      multiple inventory rows; `dependencies.csv.from_file` is the disambiguator.
    - Parent case-sensitivity is preserved verbatim (may be 'common' or 'Common');
      the classifier normalizes if needed.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

if sys.version_info < (3, 10):
    sys.exit(
        f"build_xpp_inventory.py requires Python >= 3.10 "
        f"(pyproject.toml declares `requires-python = \">=3.10\"`); "
        f"running on {sys.version.split()[0]}."
    )

MODIFIERS = (
    "public|private|internal|protected|final|abstract|static|sealed|"
    "hookable|replaceable|client|server|display|edit"
)

DECL_RE = re.compile(
    r"(?:\[[^\]]*\]\s*)?"
    rf"(?:(?:{MODIFIERS})\s+)*"
    r"(class|interface)\s+"
    r"([A-Za-z_][A-Za-z_0-9]*)"
    r"(?:\s+extends\s+([A-Za-z_][A-Za-z_0-9\.]*))?"
    r"(?:\s+implements\s+([^\{]+?))?"
    r"\s*\{",
    re.MULTILINE | re.DOTALL,
)

METHOD_SIG_RE = re.compile(
    r"^\s*"
    rf"(?:(?:{MODIFIERS})\s+)*"
    r"[A-Za-z_][A-Za-z_0-9\.]*\s+"
    r"[A-Za-z_][A-Za-z_0-9]*\s*\("
)

NEW_RE = re.compile(r"\bnew\s+([A-Za-z_][A-Za-z_0-9\.]*)\s*\(")
CALL_RE = re.compile(r"\b([A-Za-z_][A-Za-z_0-9\.]*)\s*::\s*[A-Za-z_][A-Za-z_0-9]*")

BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"//[^\r\n]*")
DQ_STRING_RE = re.compile(r'"(?:[^"\\]|\\.)*"')
SQ_STRING_RE = re.compile(r"'(?:[^'\\]|\\.)*'")


def remove_xpp_noise(content: str) -> str:
    """Strip comments and string literals so regex dependency extraction does not
    pick up identifiers that live in them."""
    content = BLOCK_COMMENT_RE.sub(" ", content)
    content = LINE_COMMENT_RE.sub(" ", content)
    content = DQ_STRING_RE.sub('""', content)
    content = SQ_STRING_RE.sub("''", content)
    return content


def rel_posix(source_root: Path, target: Path) -> str:
    """Return target path relative to source_root, always with '/' separators.

    If target is outside source_root (shouldn't happen in normal runs), falls
    back to the absolute path with normalized separators.
    """
    try:
        rel = target.resolve().relative_to(source_root.resolve())
    except ValueError:
        return target.resolve().as_posix()
    return rel.as_posix()


def xpp_prefix(class_name: str) -> str:
    # Strip leading 'I' for interface naming convention (IFoo -> Foo) before
    # taking the 3-char prefix, matching the existing PS heuristic.
    name = class_name
    if len(name) >= 2 and name[0] == "I" and name[1].isupper():
        name = name[1:]
    return name[:3] if len(name) >= 3 else name


def count_methods(body: str) -> int:
    """Count method signatures at class-body scope only (depth 0).

    Avoids counting `return x(...)` / `throw y(...)` / nested lambdas as methods.
    """
    depth = 0
    count = 0
    for line in body.split("\n"):
        if depth == 0 and METHOD_SIG_RE.match(line):
            count += 1
        depth += line.count("{") - line.count("}")
    return count


def parse_xpp_file(file_path: Path, source_root: Path) -> dict | None:
    try:
        raw = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw = file_path.read_text(encoding="utf-8-sig")
    if not raw:
        return None

    clean = remove_xpp_noise(raw)
    m = DECL_RE.search(clean)
    if not m:
        return None

    kind = m.group(1)
    class_name = m.group(2)
    parent = m.group(3) or ""
    implements_raw = m.group(4) or ""
    interfaces = [p.strip() for p in implements_raw.split(",") if p.strip()] if implements_raw else []

    body = clean[m.end():]
    methods = count_methods(body)

    uses = {
        target for match in NEW_RE.finditer(body)
        if (target := match.group(1)) != class_name
    }
    calls = {
        target for match in CALL_RE.finditer(body)
        if (target := match.group(1)) != class_name
    }

    return {
        "file": rel_posix(source_root, file_path),
        "class": class_name,
        "parent": parent,
        "interfaces": ";".join(interfaces),
        "methods_count": methods,
        "prefix": xpp_prefix(class_name),
        "artifact_kind": kind,  # 'class' | 'interface'
        "uses": sorted(uses),
        "calls": sorted(calls),
    }


def parse_ax_metadata_xml(file_path: Path, source_root: Path, artifact_kind: str) -> dict | None:
    """Parse AxEnum / AxEdt XML metadata. Only extracts <Name>.

    D365 metadata XMLs have a root element like <AxEnum> or <AxEdt> with a
    direct <Name> child. Returns None if the file is malformed or Name is
    missing.
    """
    try:
        tree = ET.parse(file_path)
    except ET.ParseError:
        return None

    root = tree.getroot()
    name_el = root.find("Name")
    if name_el is None or not (name_el.text or "").strip():
        return None

    return {
        "file": rel_posix(source_root, file_path),
        "class": name_el.text.strip(),
        "parent": "",
        "interfaces": "",
        "methods_count": 0,
        "prefix": xpp_prefix(name_el.text.strip()),
        "artifact_kind": artifact_kind,  # 'enum' | 'edt'
        "uses": [],
        "calls": [],
    }


def iter_metadata_files(source_root: Path, folder_name: str) -> Iterable[Path]:
    """Yield *.xml files under any directory named folder_name (recursive)."""
    for dir_path in source_root.rglob(folder_name):
        if not dir_path.is_dir():
            continue
        for xml in dir_path.rglob("*.xml"):
            if xml.is_file():
                yield xml


def write_inventory(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # QUOTE_ALL matches the quoted output produced by PowerShell's Export-Csv,
    # keeping the CSV format stable across the migration.
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["file", "class", "parent", "interfaces", "methods_count", "prefix", "artifact_kind"],
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in writer.fieldnames})


def write_dependencies(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["from_class", "from_file", "to_class", "kind"],
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in writer.fieldnames})


def build(source_path: Path, output_path: Path) -> tuple[int, int, int, int]:
    if not source_path.exists():
        raise SystemExit(f"SourcePath does not exist: {source_path}")

    output_path.mkdir(parents=True, exist_ok=True)

    inventory: list[dict] = []
    dependencies: list[dict] = []
    skipped = 0
    enum_count = 0
    edt_count = 0

    xpp_files = sorted(source_path.rglob("*.xpp"))
    print(f".xpp files found: {len(xpp_files)}")

    for xpp in xpp_files:
        parsed = parse_xpp_file(xpp, source_path)
        if not parsed:
            print(f"WARN: skipped (no class/interface): {xpp}", file=sys.stderr)
            skipped += 1
            continue

        inventory.append(parsed)

        from_class = parsed["class"]
        from_file = parsed["file"]

        if parsed["parent"]:
            dependencies.append({
                "from_class": from_class,
                "from_file": from_file,
                "to_class": parsed["parent"],
                "kind": "extends",
            })

        for iface in parsed["interfaces"].split(";"):
            if iface:
                dependencies.append({
                    "from_class": from_class,
                    "from_file": from_file,
                    "to_class": iface,
                    "kind": "implements",
                })

        for target in parsed["uses"]:
            dependencies.append({
                "from_class": from_class,
                "from_file": from_file,
                "to_class": target,
                "kind": "uses",
            })

        for target in parsed["calls"]:
            dependencies.append({
                "from_class": from_class,
                "from_file": from_file,
                "to_class": target,
                "kind": "calls",
            })

    # AxEnum / AxEdt: metadata-only artifacts, contribute rows to inventory
    # with artifact_kind='enum'|'edt' and zero methods. They never emit
    # dependency rows — they're leaves in the graph.
    for xml in sorted(iter_metadata_files(source_path, "AxEnum")):
        parsed = parse_ax_metadata_xml(xml, source_path, "enum")
        if parsed:
            inventory.append(parsed)
            enum_count += 1

    for xml in sorted(iter_metadata_files(source_path, "AxEdt")):
        parsed = parse_ax_metadata_xml(xml, source_path, "edt")
        if parsed:
            inventory.append(parsed)
            edt_count += 1

    inventory_path = output_path / "inventory.csv"
    dependencies_path = output_path / "dependencies.csv"

    write_inventory(inventory, inventory_path)
    write_dependencies(dependencies, dependencies_path)

    print()
    print(f"inventory.csv    -> {inventory_path} ({len(inventory)} rows)")
    print(f"  classes/interfaces: {len(inventory) - enum_count - edt_count}")
    print(f"  enums:              {enum_count}")
    print(f"  edts:               {edt_count}")
    print(f"dependencies.csv -> {dependencies_path} ({len(dependencies)} rows)")
    if skipped:
        print(f"Skipped          -> {skipped} .xpp files without class/interface")

    return len(inventory), len(dependencies), enum_count + edt_count, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build inventory.csv + dependencies.csv from an X++ source tree.")
    parser.add_argument("--source-path", required=True, help="Root folder containing .xpp files (recursive).")
    parser.add_argument("--output-path", required=True, help="Folder where inventory.csv and dependencies.csv will be written.")
    args = parser.parse_args(argv)

    build(Path(args.source_path), Path(args.output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
