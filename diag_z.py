from pathlib import Path

lines = Path("app.py").read_text(encoding="utf-8-sig").splitlines()

keywords = (
    "Z Farm",
    "Genel Farm",
    "target=ord",
    "target_key",
    "self.key(h,target",
    "self.key(h, target",
    "verify()",
)

print("--- ilgili satirlar ---")
for number, line in enumerate(lines, 1):
    if any(keyword in line for keyword in keywords):
        print(f"{number:4}: {line.rstrip()}")