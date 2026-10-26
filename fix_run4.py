from pathlib import Path
from datetime import datetime
import ast

path = Path("app.py")

backups = sorted(path.parent.glob("app.before_run_move_*.py"))
if not backups:
    raise SystemExit("ISLEM YAPILMADI: app.before_run_move_*.py yedegi bulunamadi.")

backup = backups[-1]
source = backup.read_text(encoding="utf-8-sig")
lines = source.splitlines(keepends=True)

run_start = None

for index, line in enumerate(lines):
    if line.rstrip("\r\n") == "        def run(self,h,c,samples):":
        run_start = index
        break

if run_start is None:
    raise SystemExit("ISLEM YAPILMADI: 8 bosluklu nested run bulunamadi.")

block = []

for line in lines[run_start:]:
    if not line.strip():
        block.append(line)
        continue

    indent = len(line) - len(line.lstrip(" "))

    if indent < 8:
        break

    block.append(line)

while block and not block[-1].strip():
    block.pop()

if len(block) < 50:
    raise SystemExit(
        f"ISLEM YAPILMADI: run bloğu cok kisa bulundu: {len(block)} satir."
    )

dedented = []
for line in block:
    if line.strip():
        if not line.startswith("        "):
            raise SystemExit(
                "ISLEM YAPILMADI: run bloğunda beklenmeyen girinti var."
            )
        dedented.append(line[4:])
    else:
        dedented.append(line)

dedented[0] = "    def run(self, h, c, samples):\n"

panel_start = next(
    index for index, line in enumerate(lines)
    if line.rstrip("\r\n") == "    def run_panel_test(self, h, c, samples):"
)

remaining = lines[:run_start] + lines[run_start + len(block):]

updated_lines = (
    remaining[:panel_start]
    + dedented
    + ["\n"]
    + remaining[panel_start:]
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

run_method = methods["run"]

if run_method.end_lineno - run_method.lineno < 50:
    raise SystemExit(
        f"ISLEM YAPILMADI: run hala kisa gorunuyor: "
        f"{run_method.lineno}-{run_method.end_lineno}"
    )

if any(
    isinstance(node, ast.FunctionDef) and node.name == "run"
    for node in ast.walk(methods["run_panel_test"])
):
    raise SystemExit("ISLEM YAPILMADI: run hala run_panel_test icinde.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
new_backup = path.with_name(f"app.before_run_fix4_{stamp}.py")
new_backup.write_bytes(path.read_bytes())
path.write_text(updated, encoding="utf-8")

print(f"Geri yuklenen yedek: {backup.name}")
print(f"Yeni yedek: {new_backup.name}")
print("OK: run tam olarak App sinifina tasindi. SOZDIZIMI OK.")
print(f"run: satir {run_method.lineno}-{run_method.end_lineno}")
print(
    f"run_panel_test: satir "
    f"{methods['run_panel_test'].lineno}-{methods['run_panel_test'].end_lineno}"
)