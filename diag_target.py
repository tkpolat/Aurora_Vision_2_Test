from pathlib import Path

lines = Path("app.py").read_text(encoding="utf-8-sig").splitlines()

print("--- 820-880: Genel Farm hedef dongusu ---")
for number in range(820, min(881, len(lines) + 1)):
    print(f"{number:4}: {lines[number - 1]}")