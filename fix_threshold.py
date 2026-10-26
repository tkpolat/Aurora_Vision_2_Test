from pathlib import Path

path = Path("app.py")
source = path.read_text(encoding="utf-8-sig")

old = "c['target_match_threshold'] = 0.70"
new = "c['target_match_threshold'] = 0.65"

if old in source:
    updated = source.replace(old, new)
    path.write_text(updated, encoding="utf-8")
    print("OK: esik 0.70 -> 0.65 olarak degistirildi.")
elif new in source:
    print("Zaten esik 0.65.")
else:
    print("HATA: esik satiri bulunamadi. app.py icinde 'target_match_threshold' ara.")