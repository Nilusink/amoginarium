"""
Generates Mermaid diagrams and updates READMEs with project architecture.

| ``Path``: tools/arch_gen/generate_architecture.py
| ``Project``: amoginarium
| ``Created``: 28.04.2026
| ``Authors``: LukasKrah
"""
# ruff: noqa: T201

import os
import re
import subprocess
from pathlib import Path


def run_cmd(cmd) -> None:
    # Suppress console spam from pyreverse during recursive runs
    subprocess.run(
        cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def process_packages() -> None:
    """Processes pyreverse output to create a structural mermaid graph."""
    input_file, output_file = "packages.mmd", "structure.mmd"
    if not os.path.exists(input_file):
        return

    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    edges, classes = [], set()
    pattern = re.compile(r"(\w+)\s+(-->|\.\.>)\s+(\w+)")
    class_pattern = re.compile(r"class\s+(\w+)\s*\{?")

    for line in lines:
        if m := pattern.search(line):
            edges.append((m.group(1), m.group(3)))
        if m := class_pattern.search(line):
            classes.add(m.group(1))

    init_imports = {dest for src, dest in edges if src == "__init__"}
    item_to_top, top_items_fs = {}, set()
    root_dir = Path(".")

    for p in root_dir.iterdir():
        if p.name.startswith(".") or (
            p.name.startswith("__") and p.name != "__init__.py"
        ):
            continue
        if p.is_dir():
            top_name = p.name
            top_items_fs.add(top_name)
            item_to_top[top_name] = top_name
            for sub_p in p.rglob("*.py"):
                if sub_p.name != "__init__.py":
                    item_to_top[sub_p.stem] = top_name
        elif p.is_file() and p.suffix == ".py":
            top_name = p.stem
            if top_name in ("__init__", "test"):
                continue
            top_items_fs.add(top_name)
            item_to_top[top_name] = top_name

    valid_top_items = sorted(top_items_fs.intersection(classes))
    if not valid_top_items:
        return

    cross_links = set()
    for src, dest in edges:
        ts, td = item_to_top.get(src), item_to_top.get(dest)
        if ts and td and ts != td:
            cross_links.add((ts, td))

    root_name = root_dir.resolve().name or "_base"
    mmd = ["graph TD\n", '    subgraph Group ["\u200e"]\n']
    mmd += [f"        {i}\n" for i in valid_top_items]
    mmd += ["    end\n\n"]
    mmd += [f"    {root_name} --- {i}\n" for i in valid_top_items if i in init_imports]
    mmd += ["\n"] + [f"    {s} --> {d}\n" for s, d in sorted(cross_links)]

    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(mmd)


def process_classes() -> None:
    """Processes pyreverse output to create a class relationship mermaid graph."""
    input_file = "classes.mmd"
    if not os.path.exists(input_file):
        return

    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    classes, edges = set(), []
    cp, ep = re.compile(r"class\s+(\w+)\s*\{?"), re.compile(r"(\w+)\s+(.*?)\s+(\w+)")

    for line in lines:
        if m := cp.search(line):
            classes.add(m.group(1))
        elif m := ep.search(line):
            u, arrow, v = m.groups()
            if any(x in arrow for x in ["-->", "--|>", "..>"]):
                edges.append((u, v))
                classes.update([u, v])

    if not classes:
        return

    adj = {c: [] for c in classes}
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    visited, components = set(), []
    for c in sorted(classes):
        if c not in visited:
            comp, stack = [], [c]
            visited.add(c)
            while stack:
                node = stack.pop()
                comp.append(node)
                for n in adj[node]:
                    if n not in visited:
                        visited.add(n)
                        stack.append(n)
            components.append(comp)

    isolated = sorted([c[0] for c in components if len(c) == 1])
    trees = [sorted(c) for c in components if len(c) > 1]

    mmd, g_idx = ["graph RL"], 1
    for i in range(0, len(isolated), 5):
        mmd += (
            [f'\n    subgraph Group{g_idx} ["\u200e"]\n']
            + [f"        {n}\n" for n in isolated[i : i + 5]]
            + ["    end"]
        )
        g_idx += 1
    for t in trees:
        mmd += (
            [f'\n    subgraph Group{g_idx} ["\u200e"]\n']
            + [f"        {n}\n" for n in t]
            + ["    end"]
        )
        g_idx += 1
    mmd += ["\n"] + [f"    {u} --> {v}\n" for u, v in edges]

    with open(input_file, "w", encoding="utf-8") as f:
        f.writelines(mmd)


def update_readme_file() -> None:
    """Updates the README in the current folder, injecting content between specific tags."""
    sf, cf, rf = "structure.mmd", "classes.mmd", "README.md"
    sc = open(sf, encoding="utf-8").read().strip() if os.path.exists(sf) else ""
    cc = open(cf, encoding="utf-8").read().strip() if os.path.exists(cf) else ""

    cwd = Path.cwd().resolve().as_posix()
    h_path = cwd[cwd.find("amoginarium") :] if "amoginarium" in cwd else Path.cwd().name
    ticks = "`" * 3

    # Tag constants for strict injection
    S_START, S_END = (
        "<!--- MermaidStructureStart --->",
        "<!--- MermaidStructureEnd --->",
    )
    C_START, C_END = "<!--- MermaidClassesStart --->", "<!--- MermaidClassesEnd --->"

    if not os.path.exists(rf):
        # CREATE: Only if there is actual data
        if sc or cc:
            with open(rf, "w", encoding="utf-8") as f:
                f.write(f"# {h_path}\n\n")
                if sc:
                    f.write(
                        f'<details open>\n\n<summary><h2 style="display:inline-block">Structure</h2></summary>\n{S_START}\n\n{ticks}mermaid\n{sc}\n{ticks}\n\n{S_END}\n</details>\n\n'
                    )
                if cc:
                    f.write(
                        f'<details open>\n\n<summary><h2 style="display:inline-block">Classes</h2></summary>\n{C_START}\n\n{ticks}mermaid\n{cc}\n{ticks}\n\n{C_END}\n</details>\n'
                    )
            print("  -> Created README.md")
        ss, cs = bool(sc), bool(cc)
    else:
        content = open(rf, encoding="utf-8").read()
        ss, cs, updated = False, False, False

        # Structure Injection
        s_idx = content.find(S_START)
        if s_idx != -1:
            e_idx = content.find(S_END, s_idx)
            if e_idx != -1:
                replacement = f"\n\n{ticks}mermaid\n{cc}\n{ticks}\n\n" if cc else "\n"
                content = (
                    content[: s_idx + len(S_START)] + replacement + content[e_idx:]
                )
                ss, updated = True, True

        # Classes Injection
        c_idx = content.find(C_START)
        if c_idx != -1:
            e_idx = content.find(C_END, c_idx)
            if e_idx != -1:
                replacement = f"\n{ticks}mermaid\n{cc}\n{ticks}\n" if cc else "\n"
                content = (
                    content[: c_idx + len(C_START)] + replacement + content[e_idx:]
                )
                cs, updated = True, True

        if updated:
            with open(rf, "w", encoding="utf-8") as f:
                f.write(content)
            print("  -> Updated README.md")
        else:
            print("  -> Skipped README.md (No Mermaid tags found)")

    # Cleanup leftover files
    for _success, file in [(ss, sf), (cs, cf)]:
        if os.path.exists(file):
            os.remove(file)


def run_pipeline(target_dir: Path, require_updatable: bool) -> None:
    """Executes the mapping logic in a specific directory."""
    if not any(target_dir.glob("*.py")):
        return

    if require_updatable:
        readme_file = target_dir / "README.md"
        if not readme_file.exists():
            return
        content = readme_file.read_text(encoding="utf-8", errors="ignore")
        if (
            "<!--- MermaidStructureStart --->" not in content
            and "<!--- MermaidClassesStart --->" not in content
        ):
            return

    original_dir = Path.cwd()
    try:
        os.chdir(target_dir)
        print(f"Processing: {target_dir.resolve().as_posix()}")

        run_cmd("pyreverse -o mmd -k . --source-roots .")
        process_packages()
        run_cmd("pyreverse -o mmd -k .")
        process_classes()
        if os.path.exists("packages.mmd"):
            os.remove("packages.mmd")

        update_readme_file()
    finally:
        os.chdir(original_dir)


def walk_and_process(require_updatable: bool) -> None:
    """Recursively walks through folders to execute the pipeline."""
    root = Path.cwd()
    for dirpath, dirnames, _filenames in os.walk(root):
        dirnames[:] = [
            d
            for d in dirnames
            if not (d.startswith((".", "__")) or d in ("venv", "env"))
        ]
        run_pipeline(Path(dirpath), require_updatable)


def cmd_gen_readme() -> None:
    """Command: gen_readme - Current folder only."""
    run_pipeline(Path.cwd(), require_updatable=False)
    print("Done.")


def cmd_update_readmes() -> None:
    """Command: update_readmes - Recursive, existing tags only."""
    print("Scanning for updatable READMEs recursively...")
    walk_and_process(require_updatable=True)
    print("Done updating existing READMEs.")


def cmd_create_readmes() -> None:
    """Command: create_readmes - Recursive, all Python folders."""
    print("Generating/Updating READMEs for ALL Python folders recursively...")
    walk_and_process(require_updatable=False)
    print("Done generating all READMEs.")


if __name__ == "__main__":
    cmd_gen_readme()
