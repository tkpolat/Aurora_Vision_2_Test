from pathlib import Path

path = Path("app.py")
source = path.read_text(encoding="utf-8-sig")

target_line = "self.key(h,target); self.wait(.25)"
log_line = "self.say(f'HEDEFLEME: {chr(target)} tusu gonderiliyor')"

if "HEDEFLEME:" in source:
    print("Zaten HEDEFLEME logu var; islem yapilmadi.")
elif target_line not in source:
    print("HATA: 'self.key(h,target); self.wait(.25)' satiri bulunamadi.")
else:
    updated = source.replace(
        target_line,
        log_line + "\n" + " " * 24 + target_line,
        1
    )
    path.write_text(updated, encoding="utf-8")
    print("OK: HEDEFLEME logu eklendi.")