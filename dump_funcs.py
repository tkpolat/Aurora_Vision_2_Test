from pathlib import Path
import re

s = Path('app.py').read_text(encoding='utf-8-sig')
names = ['click', 'attack', 'skill', 'press', 'key', 'loop', 'run', 'target', 'delay']

for m in re.finditer(r'    def (\w+)\(.*?(?=\n    def |\nclass |\Z)', s, re.S):
    name = m.group(1)
    if any(k in name.lower() for k in names):
        print('\n\n===== FONKSIYON: ' + name + ' =====')
        print(m.group(0))
        print('\n===== SON =====')
