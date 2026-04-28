"""
my_tools/arch_gen/generate_architecture.py

Project: amoginarium
Created: 28.04.2026
Authors: LukasKrah
"""
import os
import re
import subprocess
from pathlib import Path


def run_cmd(cmd):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)


def process_packages():
    input_file = "packages.mmd"
    output_file = "structure.mmd"
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, 'r') as f:
        lines = f.readlines()

    edges, classes = [], set()
    pattern = re.compile(r'(\w+)\s+(-->|\.\.>)\s+(\w+)')
    class_pattern = re.compile(r'class\s+(\w+)\s*\{?')

    for line in lines:
        if m := pattern.search(line): edges.append((m.group(1), m.group(3)))
        if m := class_pattern.search(line): classes.add(m.group(1))

    init_imports = {dest for src, dest in edges if src == "__init__"}
    item_to_top, top_items_fs = {}, set()
    root_dir = Path(".")

    for p in root_dir.iterdir():
        if p.name.startswith('.') or (p.name.startswith('__') and p.name != '__init__.py'):
            continue
        if p.is_dir():
            top_name = p.name
            top_items_fs.add(top_name)
            item_to_top[top_name] = top_name
            for sub_p in p.rglob('*.py'):
                if sub_p.name != '__init__.py': item_to_top[sub_p.stem] = top_name
        elif p.is_file() and p.suffix == '.py':
            top_name = p.stem
            if top_name in ('__init__', 'test'): continue
            top_items_fs.add(top_name)
            item_to_top[top_name] = top_name

    valid_top_items = sorted(top_items_fs.intersection(classes))
    cross_links = set()
    for src, dest in edges:
        ts, td = item_to_top.get(src), item_to_top.get(dest)
        if ts and td and ts != td: cross_links.add((ts, td))

    root_name = root_dir.resolve().name or "_base"
    mmd = ["graph TD\n", '    subgraph Group [" "]\n']
    mmd += [f"        {i}\n" for i in valid_top_items]
    mmd += ["    end\n\n"]
    mmd += [f"    {root_name} --- {i}\n" for i in valid_top_items if i in init_imports]
    mmd += ["\n"] + [f"    {s} --> {d}\n" for s, d in sorted(cross_links)]

    with open(output_file, 'w') as f:
        f.writelines(mmd)
    print(f"Generated {output_file}")


def process_classes():
    input_file = "classes.mmd"
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, 'r') as f:
        lines = f.readlines()
    classes, edges = set(), []
    cp, ep = re.compile(r'class\s+(\w+)\s*\{?'), re.compile(r'(\w+)\s+(.*?)\s+(\w+)')

    for line in lines:
        if m := cp.search(line):
            classes.add(m.group(1))
        elif m := ep.search(line):
            u, arrow, v = m.groups()
            if any(x in arrow for x in ['-->', '--|>', '..>']):
                edges.append((u, v))
                classes.update([u, v])

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
        mmd += [f'\n    subgraph Group{g_idx} [" "]\n'] + [f'        {n}\n' for n in isolated[i:i + 5]] + ['    end']
        g_idx += 1
    for t in trees:
        mmd += [f'\n    subgraph Group{g_idx} [" "]\n'] + [f'        {n}\n' for n in t] + ['    end']
        g_idx += 1
    mmd += ["\n"] + [f'    {u} --> {v}\n' for u, v in edges]

    with open(input_file, 'w') as f:
        f.writelines(mmd)
    print(f"Generated classes.mmd")


def update_readme():
    sf, cf, rf = "structure.mmd", "classes.mmd", "README.md"
    sc = open(sf).read().strip() if os.path.exists(sf) else ""
    cc = open(cf).read().strip() if os.path.exists(cf) else ""

    cwd = Path.cwd().resolve().as_posix()
    h_path = cwd[cwd.find("amoginarium"):] if "amoginarium" in cwd else f"{Path.cwd().name}"
    ticks = "`" * 3

    if not os.path.exists(rf):
        with open(rf, 'w') as f:
            f.write(
                f"# {h_path}\n\n<details open>\n\n<summary><h2 style=\"display:inline-block\">Structure</h2></summary>\n\n<!--- MermaidStructureStart --->\n")
            if sc: f.write(f"{ticks}mermaid\n{sc}\n{ticks}\n")
            f.write(
                "<!--- MermaidStructureEnd --->\n\n</details>\n\n<details open>\n\n<summary><h2 style=\"display:inline-block\">Classes</h2></summary>\n\n<!--- MermaidClassesStart --->\n")
            if cc: f.write(f"{ticks}mermaid\n{cc}\n{ticks}\n")
            f.write("<!--- MermaidClassesEnd --->\n\n</details>\n")
        ss, cs = bool(sc), bool(cc)
        print("Created README.md")
    else:
        content = open(rf).read()
        ss, cs = False, False
        m_pairs = [("<!--- MermaidStructureStart --->", "<!--- MermaidStructureEnd --->", sc),
                   ("<!--- MermaidClassesStart --->", "<!--- MermaidClassesEnd --->", cc)]
        for start, end, graph in m_pairs:
            s_idx = content.find(start)
            e_idx = content.find(end)
            if s_idx != -1 and e_idx != -1 and graph:
                content = content[:s_idx + len(start)] + f"\n{ticks}mermaid\n{graph}\n{ticks}\n" + content[e_idx:]
                if "Structure" in start:
                    ss = True
                else:
                    cs = True
        with open(rf, 'w') as f:
            f.write(content)
        print("Updated README.md")

    for success, file in [(ss, sf), (cs, cf)]:
        if success and os.path.exists(file):
            os.remove(file)
            print(f"Imported {file} successfully. Deleted.")
        else:
            print(f"Did not import {file}")


def main():
    run_cmd("pyreverse -o mmd -k . --source-roots .")
    process_packages()
    run_cmd("pyreverse -o mmd -k .")
    process_classes()
    if os.path.exists("packages.mmd"): os.remove("packages.mmd")
    update_readme()


if __name__ == "__main__":
    main()
