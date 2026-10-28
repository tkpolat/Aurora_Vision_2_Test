import difflib, glob, json, os, re
from pathlib import Path

src = Path('app.py').read_text(encoding='utf-8')
Path('gonder.txt').write_text(src, encoding='utf-8')

o = []
o.append('app.py satir: %d' % len(src.splitlines()))
o.append('')
o.append('=== VARLIK KONTROLU ===')
for k in ['Genel Farm','hp_ratio','target_key','NAMED_KEYS','red_ratio','clean_panel_colors','run_panel_test','0x0008']:
    o.append('%s: %s' % (k, 'VAR' if k in src else 'YOK'))
o.append('')
o.append('=== FONKSIYONLAR ===')
for m in re.finditer(r'^(\s*)def (\w+)\(([^)]*)\)', src, re.M):
    o.append('%sdef %s(%s)' % ('    ' if len(m.group(1)) > 4 else '', m.group(2), m.group(3)))
o.append('')
o.append('=== MOD LISTESI ===')
for m in re.finditer(r"values\s*=\s*\[([^\]]*)\]", src):
    o.append(m.group(1))
o.append('')
o.append('=== AYAR ALANLARI ===')
for m in re.finditer(r"\('(\w+)',\s*'([^']*)',\s*'([^']*)',\s*(True|False)\)", src):
    o.append('%s = %s (secim=%s)' % (m.group(1), m.group(3), m.group(4)))
o.append('')
o.append('=== KURULUM BUTONLARI ===')
for m in re.finditer(r"\('([^']*)',\s*lambda:\s*self\.pick\('(\w+)',\s*(True|False)\)", src):
    o.append('%s -> %s (ornek=%s)' % (m.group(1), m.group(2), m.group(3)))
o.append('')
o.append('=== mode KONTROLLERI ===')
for m in re.finditer(r"c\['mode'\]\s*[!=]=\s*'([^']+)'", src):
    o.append(m.group(1))
o.append('')
o.append('=== required BLOGU ===')
i = src.find('required')
o.append(src[max(0,i-80):i+300])
o.append('')
o.append('=== ESIK DEGERLERI (kullanim sayisi) ===')
for k in ['0.55','0.02','0.01','0.80','0.30']:
    o.append('%s: %d' % (k, src.count(k)))
o.append('')
o.append('=== PROFILLER ===')
for p in sorted(glob.glob('profiles/*/config.json')):
    try:
        c = json.loads(Path(p).read_text(encoding='utf-8'))
        o.append('%s region=%s mode=%s target_key=%s skills=%s' % (p, list(c.get('region',{}).keys()), c.get('mode'), c.get('target_key'), c.get('skills')))
    except Exception as e:
        o.append('%s HATA %s' % (p, e))
Path('ozet.txt').write_text('\n'.join(o), encoding='utf-8')

fs = sorted(glob.glob('app_yedek_*.py'), key=os.path.getmtime)
if fs:
    old = fs[-1]
    d = difflib.unified_diff(Path(old).read_text(encoding='utf-8').splitlines(True), src.splitlines(True), fromfile=old, tofile='app.py')
    Path('fark.txt').write_text(''.join(d), encoding='utf-8')
    print('yedek bulundu:', old)
else:
    Path('fark.txt').write_text('yedek yok', encoding='utf-8')
    print('yedek yok')
print('yazildi: gonder.txt, ozet.txt, fark.txt')
