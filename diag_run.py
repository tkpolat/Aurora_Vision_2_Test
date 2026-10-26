from pathlib import Path
import ast

source = Path("app.py").read_text(encoding="utf-8-sig")
tree = ast.parse(source)

app = next(
    node for node in tree.body
    if isinstance(node, ast.ClassDef) and node.name == "App"
)

methods = {
    node.name: (node.lineno, node.end_lineno)
    for node in app.body
    if isinstance(node, ast.FunctionDef)
}

for name in ("start", "run", "run_panel_test", "select_targets", "select_targetsü"):
    if name in methods:
        print(f"{name}: {methods[name][0]}-{methods[name][1]}")