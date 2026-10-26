from pathlib import Path
from datetime import datetime
import ast

path = Path("app.py")
source = path.read_text(encoding="utf-8-sig")
tree = ast.parse(source)
lines = source.splitlines(keepends=True)

app = next(
    node for node in tree.body
    if isinstance(node, ast.ClassDef) and node.name == "App"
)

panel_test = next(
    node for node in app.body
    if isinstance(node, ast.FunctionDef) and node.name == "run_panel_test"
)

nested_runs = [
    node for node in ast.walk(panel_test)
    if isinstance(node, ast.FunctionDef) and node.name == "run"
]

if len(nested_runs) != 1:
    raise SystemExit(
        f"ISLEM YAPILMADI: run_panel_test icinde {len(nested_runs)} run bulundu."
    )

nested = nested_runs[0]
start = nested.lineno - 1
end = nested.end_lineno

block = lines[start:end]

dedented = []
for line in block:
    if line.strip():
        if not line.startswith("        "):
            raise SystemExit(
                f"ISLEM YAPILMADI: Beklenmeyen girinti, satir {start + dedented.index(line) + 1}."
            )
        dedented.append(line[4:])
    else:
        dedented.append(line)

dedented[0] = "    def run(self, h, c, samples):\n"
if dedented[1].startswith("         if c['mode']"):
    dedented[1] = "        " + dedented[1].lstrip()

remaining = lines[:start] + lines[end:]
insert_at = panel_test.lineno - 1
updated_lines = (
    remaining[:insert_at]
    + dedented
    + ["\n"]
    + remaining[insert_at:]
)

updated = "".join(updated_lines)

try:
    compile(updated, str(path), "exec")
    checked = ast.parse(updated)
except SyntaxError as error:
    raise SystemExit(
        f"ISLEM YAPILMADI: {error.msg}; satir {error.lineno}. Dosya degistirilmedi."
    )

checked_app = next(
    node for node in checked.body
    if isinstance(node, ast.ClassDef) and node.name == "App"
)

methods = {
    node.name: node
    for node in checked_app.body
    if isinstance(node, ast.FunctionDef)
}

if "run" not in methods:
    raise SystemExit("ISLEM YAPILMADI: run App metodu olmadı.")

if any(
    isinstance(node, ast.FunctionDef) and node.name == "run"
    for node in ast.walk(methods["run_panel_test"])
):
    raise SystemExit("ISLEM YAPILMADI: run hala run_panel_test icinde.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
backup = path.with_name(f"app.before_run_move_{stamp}.py")
backup.write_bytes(path.read_bytes())
path.write_text(updated, encoding="utf-8")

print(f"Yedek: {backup.name}")
print("OK: run App sinifina tasindi. SOZDIZIMI OK.")
print(f"run: satir {methods['run'].lineno}-{methods['run'].end_lineno}")
print(
    f"run_panel_test: satir "
    f"{methods['run_panel_test'].lineno}-{methods['run_panel_test'].end_lineno}"
)