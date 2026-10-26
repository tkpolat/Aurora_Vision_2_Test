METHOD = '    def run_panel_test(self, h, c, samples):\n        import csv\n        from datetime import datetime\n\n        session = ROOT / \'debug\' / datetime.now().strftime(\'panel_%Y%m%d_%H%M%S_%f\')\n        count = 0\n        scores = []\n        try:\n            session.mkdir(parents=True, exist_ok=False)\n            self.say(\'PANEL TEST: Giris GONDERILMEZ. 5 saniye icinde oyuna gec.\')\n            self.say(\'Tek hedef durumunu 15 saniye koru. Diger durum icin ayri test baslat.\')\n            self.wait(5)\n            self.guard(h)\n            end = time.monotonic() + 15\n            with mss.mss() as sct, (session / \'measurements.csv\').open(\'w\', newline=\'\', encoding=\'utf-8\') as file:\n                writer = csv.writer(file)\n                writer.writerow([\'frame\', \'time\', \'score\', \'threshold\', \'accepted\', \'raw_file\'])\n                while not self.stop.is_set() and time.monotonic() < end:\n                    self.guard(h)\n                    im = self.capture(sct, h)\n                    raw = self.cut(im, c[\'region\'][\'panel\']).copy()\n                    panel, template = clean_panel_colors(raw, samples[\'panel\'], c[\'panel_color\'])\n                    if template.shape[0] > panel.shape[0] or template.shape[1] > panel.shape[1]:\n                        raise RuntimeError(\'Panel ornegi arama alanina sigmiyor\')\n                    hits = detect(panel, template, c[\'panel_color\'], 0.01, [1.0])\n                    score = hits[0][0] if hits else 0.0\n                    accepted = score >= c[\'threshold\']\n                    count += 1\n                    stamp = datetime.now().strftime(\'%H:%M:%S.%f\')[:-3]\n                    base = f\'{count:04d}\'\n                    images = {\n                        base + \'_raw.png\': raw,\n                        base + \'_filtered.png\': panel,\n                        base + \'_mask.png\': (feature(panel, c[\'panel_color\']) * 255).astype(np.uint8),\n                    }\n                    if count == 1:\n                        images[\'template_raw.png\'] = samples[\'panel\']\n                        images[\'template_mask.png\'] = (feature(template, c[\'panel_color\']) * 255).astype(np.uint8)\n                    for name, image in images.items():\n                        ok, data = cv2.imencode(\'.png\', image)\n                        if not ok:\n                            raise RuntimeError(\'PNG kodlama basarisiz\')\n                        data.tofile(str(session / name))\n                    writer.writerow([count, stamp, f\'{score:.4f}\', c[\'threshold\'], accepted, base + \'_raw.png\'])\n                    file.flush()\n                    scores.append(score)\n                    self.say(f\'PANEL TEST #{count:04d} {stamp}: skor={score:.3f}, sonuc={"OK" if accepted else "RED"}, goruntu={base}_raw.png\')\n                    if self.bus.qsize() < 5:\n                        # Nearest-neighbor zoom preserves the actual captured letters.\n                        zoom = cv2.resize(raw, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST)\n                        self.bus.put((\'image\', zoom))\n                    self.wait(0.30)\n        except InterruptedError:\n            self.say(\'Panel testi kullanici tarafindan durduruldu\')\n        except Exception as e:\n            self.say(f\'PANEL TEST HATA: {e}\')\n        finally:\n            self.stop.set()\n            if scores:\n                self.say(f\'Panel testi: {len(scores)} olcum; min={min(scores):.3f}, medyan={np.median(scores):.3f}, max={max(scores):.3f}\')\n            self.say(\'Kayit klasoru: \' + str(session))\n            self.say(\'Panel testi tamamlandi. Fare ve klavye girdisi gonderilmedi.\')\n\n'

from pathlib import Path
from datetime import datetime
import ast

path = Path(__file__).resolve().with_name('app.py')
text = path.read_text(encoding='utf-8-sig')
if 'def run_panel_test(' in text:
    raise SystemExit('Panel test zaten eklenmis. Dosya degistirilmedi.')

old_modes = "['Dry','Click test','Farm','Z Farm']"
new_modes = "['Dry','Panel test','Click test','Farm','Z Farm']"
old_start = "    def run(self,h,c,samples):\n        stats=[]"
new_start = "    def run(self,h,c,samples):\n        if c['mode'] == 'Panel test':\n            self.run_panel_test(h, c, samples)\n            return\n        stats=[]"

if text.count(old_modes) != 1 or text.count(old_start) != 1:
    raise SystemExit('Beklenen kod bulunamadi. Hicbir degisiklik yapilmadi. Mevcut dosyayi paylasin.')

updated = text.replace(old_modes, new_modes, 1)
updated = updated.replace(old_start, METHOD + new_start, 1)
updated = updated.replace("required=['panel'] if c['mode']=='Z Farm' else ['scene','panel']", "required=['panel'] if c['mode'] in ('Z Farm', 'Panel test') else ['scene','panel']", 1)
ast.parse(updated)
backup = path.with_name('app_backup_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.py.bak')
backup.write_bytes(path.read_bytes())
path.write_text(updated, encoding='utf-8')
print('Panel test eklendi. Python sozdizimi kontrolu basarili.')
print('Yedek:', backup.name)
print('Simdi uygulamayi yeniden acin; profili yukledikten SONRA Panel test secin.')
