import ctypes as C
from ctypes import wintypes as W
import json, time, threading, queue, re
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import simpledialog
try: C.windll.user32.SetProcessDpiAwarenessContext(C.c_void_p(-4))
except Exception: pass
import cv2
import numpy as np
import mss
from PIL import Image, ImageTk

U=C.WinDLL('user32',use_last_error=True)
U.GetForegroundWindow.restype=W.HWND
U.IsWindow.argtypes=[W.HWND]; U.IsWindow.restype=W.BOOL
U.GetClientRect.argtypes=[W.HWND,C.POINTER(W.RECT)]
U.ClientToScreen.argtypes=[W.HWND,C.POINTER(W.POINT)]
U.GetWindowTextLengthW.argtypes=[W.HWND]
U.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,C.c_int]
U.IsWindowVisible.argtypes=[W.HWND]
U.GetAsyncKeyState.argtypes=[C.c_int]; U.GetAsyncKeyState.restype=C.c_short
PTR=C.c_size_t
class MI(C.Structure): _fields_=[('dx',W.LONG),('dy',W.LONG),('mouseData',W.DWORD),('dwFlags',W.DWORD),('time',W.DWORD),('extra',PTR)]
class KI(C.Structure): _fields_=[('vk',W.WORD),('scan',W.WORD),('flags',W.DWORD),('time',W.DWORD),('extra',PTR)]
class UNION(C.Union): _fields_=[('mi',MI),('ki',KI)]
class INPUT(C.Structure): _fields_=[('type',W.DWORD),('u',UNION)]
U.SendInput.argtypes=[W.UINT,C.POINTER(INPUT),C.c_int]; U.SendInput.restype=W.UINT
ENUM=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
U.EnumWindows.argtypes=[ENUM,W.LPARAM]

def windows():
    found=[]
    @ENUM
    def cb(h,p):
        if U.IsWindowVisible(h):
            n=U.GetWindowTextLengthW(h)
            b=C.create_unicode_buffer(n+1); U.GetWindowTextW(h,b,n+1)
            if b.value: found.append((int(h),b.value))
        return True
    U.EnumWindows(cb,0)
    return found

def geometry(h):
    r=W.RECT(); p=W.POINT()
    if not U.IsWindow(h) or not U.GetClientRect(h,C.byref(r)) or not U.ClientToScreen(h,C.byref(p)):
        raise RuntimeError('Oyun penceresi artik gecerli degil')
    if r.right<100 or r.bottom<100: raise RuntimeError('Gecersiz pencere boyutu')
    return p.x,p.y,r.right,r.bottom

def feature(bgr,color):
    hsv=cv2.cvtColor(bgr,cv2.COLOR_BGR2HSV)
    h,s,v=cv2.split(hsv)
    if color=='red': mask=((h<=13)|(h>=170))&(s>=85)&(v>=55)
    elif color=='purple': mask=(h>=115)&(h<=169)&(s>=40)&(v>=65)
    else: mask=(s<=100)&(v>=155)
    return mask.astype(np.float32)

def detect(image,templ,color,threshold,scales):
    scene=feature(image,color); base=feature(templ,color)
    candidates=[]
    for scale in scales:
        w=max(3,round(base.shape[1]*scale)); h=max(3,round(base.shape[0]*scale))
        if w>scene.shape[1] or h>scene.shape[0]: continue
        t=cv2.resize(base,(w,h),interpolation=cv2.INTER_NEAREST)
        mass=float(t.sum())
        if mass<15: continue
        dot=cv2.matchTemplate(scene,t,cv2.TM_CCORR)
        integral=cv2.integral(scene)
        totals=integral[h:,w:]-integral[:-h,w:]-integral[h:,:-w]+integral[:-h,:-w]
        score=np.clip(2*dot/(totals+mass+1e-6),0,1).astype(np.float32)
        for _ in range(16):
            _,val,_,loc=cv2.minMaxLoc(score)
            if val<threshold: break
            x,y=loc; candidates.append((float(val),x,y,w,h))
            score[max(0,y-h//2):y+h//2+1,max(0,x-w//2):x+w//2+1]=0
    candidates.sort(reverse=True); kept=[]
    for c in candidates:
        _,x,y,w,h=c
        if all(abs(x+w/2-(k[1]+k[3]/2))>max(w,k[3])*0.55 or abs(y+h/2-(k[2]+k[4]/2))>max(h,k[4])*0.6 for k in kept): kept.append(c)
    return kept
def clean_panel_colors(panel, template, color):
    if color != 'purple':
        return panel, template

    template_hsv = cv2.cvtColor(template, cv2.COLOR_BGR2HSV)
    valid = feature(template, 'purple') > 0

    if int(valid.sum()) < 15:
        raise RuntimeError(
            "Panel orneginde yeterli mor yazi pikseli yok"
        )

    hues = template_hsv[:, :, 0][valid]
    histogram = np.bincount(hues, minlength=180)
    dominant_hue = int(histogram.argmax())

    def filtered(image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hue = hsv[:, :, 0].astype(np.int16)

        difference = np.abs(hue - dominant_hue)
        difference = np.minimum(difference, 180 - difference)

        keep = (
            (difference <= 8)
            & (hsv[:, :, 1] >= 40)
            & (hsv[:, :, 2] >= 65)
        )

        result = image.copy()
        result[~keep] = 0
        return result

    return filtered(panel), filtered(template)
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'profiles'; DATA.mkdir(exist_ok=True)
class App:
    def __init__(self,root):
        self.root=root; root.title('Aurora Vision 2 - Calibration Build')
        root.configure(bg='#1e1e1e')

        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('.', background='#1e1e1e', foreground='#e0e0e0')
        style.configure('TFrame', background='#1e1e1e')
        style.configure('TLabel', background='#1e1e1e', foreground='#e0e0e0')
        style.configure('TButton', background='#2d2d2d', foreground='#e0e0e0', bordercolor='#3a3a3a')
        style.map('TButton', background=[('active', '#3a3a3a')])
        style.configure('TLabelframe', background='#1e1e1e', foreground='#e0e0e0', bordercolor='#3a3a3a')
        style.configure('TLabelframe.Label', background='#1e1e1e', foreground='#4fc3f7')
        style.configure('TCombobox', fieldbackground='#252525', background='#2d2d2d', foreground='#e0e0e0')
        style.configure('TEntry', fieldbackground='#252525', foreground='#e0e0e0', insertcolor='#e0e0e0')
        self.stop=threading.Event(); self.bus=queue.Queue(); self.worker=None; self.samples={}; self.region={}; self.size=None
        self.vars={}; self.window_map={}; self.photo=None
        self.targets = {}
        root.columnconfigure(0, weight=1)
        root.rowconfigure(3, weight=1)

        # Oyun penceresi
        window_frame = ttk.LabelFrame(root, text=' Oyun Penceresi ')
        window_frame.pack(fill='x', padx=8, pady=(8, 4))
        window_frame.columnconfigure(1, weight=1)

        ttk.Button(window_frame, text='Pencereleri yenile', command=self.refresh).grid(row=0, column=0, padx=6, pady=6)
        self.win = tk.StringVar()
        self.combo = ttk.Combobox(window_frame, textvariable=self.win, width=60, state='readonly')
        self.combo.grid(row=0, column=1, sticky='ew', padx=6, pady=6)

        # Profil ve mod
        profile_frame = ttk.LabelFrame(root, text=' Profil ve Mod ')
        profile_frame.pack(fill='x', padx=8, pady=4)
        profile_frame.columnconfigure(1, weight=1)
        profile_frame.columnconfigure(3, weight=1)

        ttk.Label(profile_frame, text='Profil / Mob Adı').grid(row=0, column=0, sticky='w', padx=6, pady=4)
        self.vars['profile'] = tk.StringVar(value='Hob Goblin')
        ttk.Entry(profile_frame, textvariable=self.vars['profile'], width=24).grid(row=0, column=1, sticky='ew', padx=6, pady=4)

        ttk.Label(profile_frame, text='Mod').grid(row=0, column=2, sticky='w', padx=6, pady=4)
        self.vars['mode'] = tk.StringVar(value='Dry')
        ttk.Combobox(
            profile_frame,
            textvariable=self.vars['mode'],
            values=['Dry', 'Panel test', 'Click test', 'Farm', 'Z Farm', 'Genel Farm'],
            state='readonly',
            width=16
        ).grid(row=0, column=3, sticky='ew', padx=6, pady=4)

        # Kurulum
        setup_frame = ttk.LabelFrame(root, text=' Kurulum ')
        setup_frame.pack(fill='x', padx=8, pady=4)

        setup_buttons = [
            ('1 Oyun Ekran Alanı', lambda: self.pick('scene', False),
             'Mob adaylarının aranacağı alan'),
            ('2 Seçilen Mob Ad Alanı', lambda: self.pick('panel', False),
             'Üstteki seçili mob adının alanı'),
            ('3 Ekranda Mob Adı Örneği', lambda: self.pick('scene', True),
             'Sahnedeki mob adı referansı'),
            ('4 Seçilen Mob Adı Örneği', lambda: self.pick('panel', True),
             'Seçili mob adı referansı'),
            ('5 Can Barı Alanı', lambda: self.pick('hp', False),
             'Saldırıda mob canını izleyeceği alan'),
        ]

        for index, (text, command, help_text) in enumerate(setup_buttons):
            row = index // 2
            column = (index % 2) * 2
            ttk.Button(setup_frame, text=text, command=command).grid(
                row=row, column=column, sticky='ew', padx=6, pady=4
            )
            ttk.Label(setup_frame, text=help_text, foreground='#9e9e9e').grid(
                row=row, column=column + 1, sticky='w', padx=6, pady=4
            )

        setup_frame.columnconfigure(0, weight=1)
        setup_frame.columnconfigure(2, weight=1)

        # Ayarlar
        settings_frame = ttk.LabelFrame(root, text=' Ayarlar ')
        settings_frame.pack(fill='x', padx=8, pady=4)

        fields = [
            ('scene_color', 'Sahne Yazı Rengi', 'red', True),
            ('panel_color', 'Seçilen Mob Yazı Rengi', 'purple', True),
            ('threshold', 'Sahne Eşleşme Eşiği', '0.80', False),
            ('offset', 'İsmin Altından Tıklama (px)', '30', False),
            ('skills', 'Saldırı Tuşları', 'R', False),
            ('target_key', 'Hedefleme Tuşu (Genel Farm)', 'Z', False),
            ('delay', 'Tuş Aralığı (saniye)', '0.30', False),
            ('timeout', 'Güvenlik Zaman Aşımı (saniye)', '20', False),
        ]

        for row, (key, label, value, is_choice) in enumerate(fields):
            ttk.Label(settings_frame, text=label).grid(row=row, column=0, sticky='w', padx=6, pady=3)
            self.vars[key] = tk.StringVar(value=value)
            if is_choice:
                values = ['red', 'purple', 'light']
                ttk.Combobox(
                    settings_frame,
                    textvariable=self.vars[key],
                    values=values,
                    state='readonly',
                    width=18
                ).grid(row=row, column=1, sticky='w', padx=6, pady=3)
            else:
                ttk.Entry(settings_frame, textvariable=self.vars[key], width=18).grid(
                    row=row, column=1, sticky='w', padx=6, pady=3
                )
        # Hedef Mob ve Wolf
        target_frame = ttk.LabelFrame(root, text=' Hedef Mob ve Wolf ')
        target_frame.pack(fill='x', padx=8, pady=4)
        target_frame.columnconfigure(1, weight=1)
        target_frame.columnconfigure(3, weight=1)

        ttk.Button(target_frame, text='Mob Adi Sec (Anlik)', command=self.capture_target).grid(
            row=0, column=0, padx=6, pady=4, sticky='ew'
        )
        self.target_count = tk.StringVar(value='Kayitli mob: 0')
        ttk.Label(target_frame, textvariable=self.target_count, foreground='#9e9e9e').grid(
            row=0, column=1, sticky='w', padx=6, pady=4
        )

        self.vars['wolf_enabled'] = tk.BooleanVar(value=False)
        ttk.Checkbutton(target_frame, text='Wolf kullan', variable=self.vars['wolf_enabled']).grid(
            row=1, column=0, padx=6, pady=4, sticky='w'
        )
        ttk.Label(target_frame, text='F Bar').grid(row=1, column=1, sticky='e', padx=6, pady=4)
        self.vars['wolf_f_key'] = tk.StringVar(value='F6')
        ttk.Entry(target_frame, textvariable=self.vars['wolf_f_key'], width=8).grid(
            row=1, column=2, padx=6, pady=4
        )
        ttk.Label(target_frame, text='Slot').grid(row=1, column=2, sticky='e', padx=(30,6), pady=4)
        self.vars['wolf_slot'] = tk.StringVar(value='1')
        ttk.Entry(target_frame, textvariable=self.vars['wolf_slot'], width=6).grid(
            row=1, column=3, padx=6, pady=4
        )
        # Kontrol
        control_frame = ttk.LabelFrame(root, text=' Çalıştırma ')
        control_frame.pack(fill='x', padx=8, pady=4)

        ttk.Button(control_frame, text='BAŞLAT (5 sn)', command=self.start).grid(
            row=0, column=0, padx=6, pady=6, sticky='ew'
        )
        ttk.Button(control_frame, text='DUR / Insert', command=self.stop.set).grid(
            row=0, column=1, padx=6, pady=6, sticky='ew'
        )
        ttk.Button(control_frame, text='Profil Kaydet', command=self.save).grid(
            row=0, column=2, padx=6, pady=6, sticky='ew'
        )
        ttk.Button(control_frame, text='Profil Yükle', command=self.load).grid(
            row=0, column=3, padx=6, pady=6, sticky='ew'
        )

        for column in range(4):
            control_frame.columnconfigure(column, weight=1)

        # Önizleme ve log
        self.view = ttk.Label(root)
        self.view.pack(padx=8, pady=4)

        log_frame = ttk.LabelFrame(root, text=' Durum Günlüğü ')
        log_frame.pack(fill='both', expand=True, padx=8, pady=(4, 8))

        self.log = tk.Text(
            log_frame,
            width=125,
            height=9,
            wrap='word',
            bg='#121212',
            fg='#e0e0e0',
            insertbackground='#e0e0e0',
            relief='flat'
        )
        self.log.pack(fill='both', expand=True, padx=4, pady=4)
        self.refresh(); root.after(80,self.poll)
        threading.Thread(target=self.hotkey,daemon=True).start()
        root.protocol('WM_DELETE_WINDOW',self.close)

    def say(self,s): self.bus.put(('log',str(s)))
    def active(self): return self.worker is not None and self.worker.is_alive()
    def refresh(self):
        self.window_map={f'{title} [0x{h:x}]':h for h,title in windows() if title!='Aurora Vision 2 - Calibration Build'}
        self.combo['values']=list(self.window_map)
        for label in self.window_map:
            if 'knight' in label.lower(): self.win.set(label); break
    def hwnd(self):
        if self.win.get() not in self.window_map: raise ValueError('Oyun penceresini listeden sec')
        return self.window_map[self.win.get()]
    def hotkey(self):
        while True:
            if U.GetAsyncKeyState(0x2D)&0x8000: self.stop.set()
            time.sleep(0.015)
    def close(self): self.stop.set(); self.root.destroy()
    def poll(self):
        for _ in range(100):
            try: kind,value=self.bus.get_nowait()
            except queue.Empty: break
            if kind=='log': self.log.insert('end',value+'\n'); self.log.see('end')
            elif kind=='image':
                self.photo=ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(value,cv2.COLOR_BGR2RGB)))
                self.view.configure(image=self.photo)
        self.root.after(80,self.poll)
    def capture(self,sct,h):
        x,y,w,hh=geometry(h)
        if self.size and [w,hh]!=self.size: raise RuntimeError('Pencere boyutu degisti; yeniden kalibre et')
        return np.array(sct.grab(dict(left=x,top=y,width=w,height=hh)))[:,:,:3].copy()
    def pick(self,key,sample):
        if self.active(): return
        try: h=self.hwnd()
        except Exception as e: messagebox.showerror('Pencere',str(e)); return
        self.root.withdraw(); self.root.after(450,lambda:self.do_pick(h,key,sample))
    def capture_target(self):
        if self.active(): return
        try: h=self.hwnd()
        except Exception as e: messagebox.showerror('Pencere',str(e)); return
        name=simpledialog.askstring('Mob Adi','Kaydedilecek mob adi (Ingilizce karakter):',parent=self.root)
        if not name: return
        name=re.sub(r'[^A-Za-z0-9 _-]','',name.strip())
        if not name:
            messagebox.showerror('Mob Adi','Gecerli bir isim gir'); return
        try:
            if 'panel' not in self.region: raise ValueError('Once panel bolgesini sec (2 Seçilen Mob Ad Alanı)')
            with mss.mss() as sct:
                im=self.capture(sct,h)
            crop=self.cut(im,self.region['panel'])
            if crop is None or crop.size==0: raise ValueError('Panel goruntusu alinamadi')
            d=self.folder()/'targets'; d.mkdir(parents=True,exist_ok=True)
            ok,data=cv2.imencode('.png',crop)
            if not ok: raise RuntimeError('PNG kodlama basarisiz')
            (d/(name+'.png')).write_bytes(data.tobytes())
            self.targets[name] = crop.copy()
            if hasattr(self, 'target_count'):
                self.target_count.set(f'Kayitli mob: {len(self.targets)}')
            cpath=self.folder()/'config.json'
            c=json.loads(cpath.read_text(encoding='utf-8'))
            t=c.get('targets',[])
            if name not in t: t.append(name)
            c['targets']=t
            cpath.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
            self.say(f"Mob sablonu kaydedildi: {name}")
        except Exception as e:
            import traceback
            details = traceback.format_exc()
            print(details, flush=True)
            messagebox.showerror('Mob Sec', details)
    def do_pick(self,h,key,sample):
        try:
            with mss.mss() as sct: image=self.capture(sct,h)
            r=cv2.selectROI('Drag tight region, ENTER confirms / ESC cancels',image,False,False)
            cv2.destroyAllWindows()
            x,y,w,hh=map(int,r)
            if w<4 or hh<4: return
            self.size=[image.shape[1],image.shape[0]]
            if sample:
                color=self.vars[key+'_color'].get()
                crop=image[y:y+hh,x:x+w].copy()
                if feature(crop,color).sum()<15: raise ValueError('Secilen renkte yeterli yazi pikseli yok. Rengi veya kesiti duzelt.')
                self.samples[key]=crop
                self.say(f'{key} ornegi: {w}x{hh}, renk={color}')
            else:
                self.region[key]=[x,y,w,hh]; self.say(f'{key} alani: {self.region[key]}')
        except Exception as e: self.say(e)
        finally: self.root.deiconify()
    def settings(self):
        c = {}
        for k, var in self.vars.items():
            value = var.get()
            c[k] = value.strip() if isinstance(value, str) else value
        c.update(region=self.region.copy(),size=self.size,skill_rotation=getattr(self,'skill_rotation',None))
        c['threshold']=float(c['threshold']); c['offset']=int(c['offset']); c['delay']=float(c['delay']); c['timeout']=float(c['timeout'])
        if not .5<=c['threshold']<=.99 or c['delay']<.05 or not 1<=c['timeout']<=120: raise ValueError('Esik / sure gecersiz')
        return c
    def folder(self):
        name=re.sub(r'[^\w -]','_',self.vars['profile'].get()).strip()
        if not name: raise ValueError('Profil adi gerekli')
        return DATA/name
    def save(self):
        if self.active(): return
        try:
            p=self.folder(); p.mkdir(exist_ok=True)
            (p/'config.json').write_text(json.dumps(self.settings(),indent=2),encoding='utf-8')
            for k,v in self.samples.items(): cv2.imencode('.png',v)[1].tofile(str(p/(k+'.png')))
            self.say('Profil kaydedildi: '+p.name)
        except Exception as e: self.say(e)
    def load(self):
        if self.active(): return
        try:
            p=self.folder(); c=json.loads((p/'config.json').read_text(encoding='utf-8'))
            for k in self.vars:
                if k in c: self.vars[k].set(str(c[k]))
            self.region=c['region']; self.size=c['size']; self.samples={}
            self.skill_rotation=c.get('skill_rotation')
            self.targets={}
            tdir=p/'targets'
            if tdir.exists():
                for f in sorted(tdir.glob('*.png')):
                    img=cv2.imdecode(np.fromfile(str(f),dtype=np.uint8),cv2.IMREAD_COLOR)
                    if img is not None: self.targets[f.stem]=img
            self.say(f"Hedef mob sablonu: {len(self.targets)}")
            for k in ['scene','panel']:
                if (p/(k+'.png')).exists(): self.samples[k]=cv2.imdecode(np.fromfile(str(p/(k+'.png')),dtype=np.uint8),cv2.IMREAD_COLOR)
            self.say('Profil yuklendi')
        except Exception as e: self.say(e)
        def select_targets(self):
         names = sorted(self.targets)
        if not names:
            messagebox.showerror(
                'Hedef Mob',
                'Once Mob Adi Sec (Anlik) ile en az bir mob kaydet.',
                parent=self.root
            )
            return None

        result = None
        dialog = tk.Toplevel(self.root)
        dialog.title('Bu oturumda kesilecek moblar')
        dialog.transient(self.root)

        ttk.Label(
            dialog,
            text='Kesilecek moblari sec. Birden fazla secim yapabilirsin.'
        ).pack(padx=12, pady=(12, 6))

        choices = tk.Listbox(
            dialog,
            selectmode=tk.MULTIPLE,
            exportselection=False,
            width=40,
            height=min(12, max(4, len(names)))
        )
        choices.pack(fill='both', expand=True, padx=12, pady=6)

        previous = set(getattr(self, 'selected_target_names', []))
        for index, name in enumerate(names):
            choices.insert(tk.END, name)
            if name in previous:
                choices.selection_set(index)

        def approve():
            nonlocal result
            selected = [names[i] for i in choices.curselection()]
            if not selected:
                messagebox.showwarning(
                    'Hedef Mob',
                    'En az bir mob sec.',
                    parent=dialog
                )
                return
            result = selected
            dialog.destroy()

        buttons = ttk.Frame(dialog)
        buttons.pack(fill='x', padx=12, pady=(6, 12))
        ttk.Button(
            buttons, text='Sec ve devam et', command=approve
        ).pack(side='left')
        ttk.Button(
            buttons, text='Iptal', command=dialog.destroy
        ).pack(side='right')

        dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)
        dialog.grab_set()
        self.root.wait_window(dialog)
        return result
    def start(self):
        if self.active():
            self.say('Once mevcut testi durdur')
            return

        try:
            c = self.settings()
            h = self.hwnd()

            modes = [
                'Dry', 'Panel test', 'Click test',
                'Farm', 'Z Farm', 'Genel Farm'
            ]
            c['mode'] = next(
                (
                    mode for mode in modes
                    if mode.lower() == c['mode'].strip().lower()
                ),
                c['mode']
            )

            if c['mode'] not in modes:
                raise ValueError('Gecersiz mod')

            target_mode = c['mode'] in ('Z Farm', 'Genel Farm')

            if c['mode'] == 'Panel test':
                sample_required = ['panel']
                region_required = ['panel']
            elif target_mode:
                sample_required = []
                region_required = ['panel', 'hp']
            else:
                sample_required = ['scene', 'panel']
                region_required = ['scene', 'panel', 'hp']

            missing = [
                'ornek: ' + key
                for key in sample_required
                if self.samples.get(key) is None
            ]
            missing += [
                'alan: ' + key
                for key in region_required
                if key not in c['region']
            ]
            if missing:
                raise ValueError('Eksik ogeler: ' + ', '.join(missing))

            samples = {
                key: image.copy()
                for key, image in self.samples.items()
                if image is not None
            }

            self.keylist(c['skills'])

            if c['mode'] == 'Genel Farm':
                target_keys = self.keylist(c['target_key'])
                if len(target_keys) != 1:
                    raise ValueError('Tek bir hedefleme tusu gir')

            if target_mode:
                selected = self.select_targets()
                if selected is None:
                    return

                self.selected_target_names = selected
                c['target_templates'] = {
                    name: self.targets[name].copy()
                    for name in selected
                }
                self.say('Secili moblar: ' + ', '.join(selected))

            # Gecici baslangic degeri; kayitlarla kalibre edilecek.
            c['target_match_threshold'] = 0.70

        except Exception as e:
            messagebox.showerror('Ayar', str(e))
            return

        self.stop.clear()
        self.worker = threading.Thread(
            target=self.run,
            args=(h, c, samples),
            daemon=True
        )
        self.worker.start()
    def wait(self,t):
        if self.stop.wait(t): raise InterruptedError()
    def guard(self,h):
        if self.stop.is_set(): raise InterruptedError()
        if int(U.GetForegroundWindow() or 0)!=h: raise RuntimeError('Oyun odagi kayboldu; durduruldu')
        if not U.IsWindow(h): raise RuntimeError('Pencere kapandi')
    def send(self,i):
        a=(INPUT*1)(i)
        if U.SendInput(1,a,C.sizeof(INPUT))!=1: raise RuntimeError(f'SendInput basarisiz: {C.get_last_error()}')
    def key(self,h,vk):
        self.guard(h)
        scan = U.MapVirtualKeyW(vk, 0)
        if not scan:
            raise RuntimeError(f'Tus scan kodu bulunamadi: vk={vk}')
        self.send(
            INPUT(
                type=1,
                u=UNION(
                    ki=KI(
                        vk=vk,
                        scan=scan,
                        flags=0x0008
                    )
                )
            )
        )
        try:
            self.wait(.035)
        finally:
            self.send(
                INPUT(
                    type=1,
                    u=UNION(
                        ki=KI(
                            vk=vk,
                            scan=scan,
                            flags=0x0008 | 0x0002
                        )
                    )
                )
            )
    def click(self, h, x, y):
        self.guard(h)

        U.GetCursorPos.argtypes = [C.POINTER(W.POINT)]
        U.GetCursorPos.restype = W.BOOL

        def position():
            p = W.POINT()
            if not U.GetCursorPos(C.byref(p)):
                raise RuntimeError(
                    f"GetCursorPos basarisiz: {C.get_last_error()}"
                )
            return p.x, p.y

        before = position()

        vx = U.GetSystemMetrics(76)
        vy = U.GetSystemMetrics(77)
        vw = U.GetSystemMetrics(78)
        vh = U.GetSystemMetrics(79)

        if vw <= 1 or vh <= 1:
            raise RuntimeError("Sanal masaustu boyutu gecersiz")

        if not (vx <= x < vx + vw and vy <= y < vy + vh):
            raise RuntimeError(
                f"Hedef masaustu disinda: ({x},{y})"
            )

        nx = round((x - vx) * 65535 / (vw - 1))
        ny = round((y - vy) * 65535 / (vh - 1))

        self.say(
            f"FARE: once={before}, hedef ekran=({x},{y}), "
            f"masaustu=({vx},{vy},{vw},{vh}), "
            f"INPUT boyutu={C.sizeof(INPUT)}"
        )

        self.send(
            INPUT(
                type=0,
                u=UNION(
                    mi=MI(
                        dx=nx,
                        dy=ny,
                        dwFlags=0x0001 | 0x8000 | 0x4000
                    )
                )
            )
        )

        self.say(f"FARE: mutlak hareket sonrasi={position()}")

        # C# projesindeki Nudge(1, 0)
        self.guard(h)
        self.send(
            INPUT(
                type=0,
                u=UNION(mi=MI(dx=1, dy=0, dwFlags=0x0001))
            )
        )
        self.wait(0.003)

        # C# projesindeki Nudge(-1, 0)
        self.guard(h)
        self.send(
            INPUT(
                type=0,
                u=UNION(mi=MI(dx=-1, dy=0, dwFlags=0x0001))
            )
        )
        self.wait(0.003)

        self.wait(0.060)
        self.guard(h)

        after = position()
        self.say(f"FARE: hareket sonrasi={after}")

        distance = (
            (after[0] - x) ** 2 + (after[1] - y) ** 2
        ) ** 0.5

        if distance > 8:
            raise RuntimeError(
                f"Imlec hedefe ulasmadi; fark={distance:.1f}px. "
                "Guvenlik nedeniyle tiklama gonderilmedi."
            )

        self.send(
            INPUT(type=0, u=UNION(mi=MI(dwFlags=0x0002)))
        )
        try:
            self.wait(0.12)
        finally:
            self.send(
                INPUT(type=0, u=UNION(mi=MI(dwFlags=0x0004)))
            )

        self.say(
            "Sol tus bas/birak komutlari gonderildi; "
            "oyun ici secim ayrica dogrulanacak."
        )
    NAMED_KEYS={'tab':0x09,'space':0x20,'enter':0x0D,'esc':0x1B,'shift':0x10,'ctrl':0x11,'alt':0x12}
    def keylist(self,text):
        keys=[]
        for s in text.lower().replace(' ','').split(','):
            if not s: continue
            if s in self.NAMED_KEYS: keys.append(self.NAMED_KEYS[s])
            elif len(s)==1 and s.isascii() and s.isalnum(): keys.append(ord(s.upper()))
            elif re.fullmatch(r'f([1-9]|1[0-2])',s): keys.append(0x6F+int(s[1:]))
            else: raise ValueError('Desteklenen tuslar: A-Z, 0-9, F1-F12, tab/space/enter/esc/shift/ctrl/alt')
        return keys
    def cut(self,image,r):
        x,y,w,h=r
        if x<0 or y<0 or x+w>image.shape[1] or y+h>image.shape[0]: raise RuntimeError('Alan pencere disinda')
        return image[y:y+h,x:x+w]
    def hp_ratio(self,sct,h,c):
        self.guard(h)
        hp=self.cut(self.capture(sct,h),c['region']['hp'])
        b,g,r=cv2.split(hp)
        return float(np.mean((r>90)&(r>g*1.4)&(r>b*1.4)))
    def run_panel_test(self, h, c, samples):
        import csv
        from datetime import datetime

        session = ROOT / 'debug' / datetime.now().strftime('panel_%Y%m%d_%H%M%S_%f')
        count = 0
        scores = []
        try:
            session.mkdir(parents=True, exist_ok=False)
            self.say('PANEL TEST: Giris GONDERILMEZ. 5 saniye icinde oyuna gec.')
            self.say('Tek hedef durumunu 15 saniye koru. Diger durum icin ayri test baslat.')
            self.wait(5)
            self.guard(h)
            end = time.monotonic() + 15
            with mss.mss() as sct, (session / 'measurements.csv').open('w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['frame', 'time', 'score', 'threshold', 'accepted', 'raw_file'])
                while not self.stop.is_set() and time.monotonic() < end:
                    self.guard(h)
                    im = self.capture(sct, h)
                    raw = self.cut(im, c['region']['panel']).copy()
                    panel, template = clean_panel_colors(raw, samples['panel'], c['panel_color'])
                    if template.shape[0] > panel.shape[0] or template.shape[1] > panel.shape[1]:
                        raise RuntimeError('Panel ornegi arama alanina sigmiyor')
                    hits = detect(panel, template, c['panel_color'], 0.01, [1.0])
                    score = hits[0][0] if hits else 0.0
                    accepted = score >= 0.55
                    count += 1
                    stamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    base = f'{count:04d}'
                    images = {
                        base + '_raw.png': raw,
                        base + '_filtered.png': panel,
                        base + '_mask.png': (feature(panel, c['panel_color']) * 255).astype(np.uint8),
                    }
                    if count == 1:
                        images['template_raw.png'] = samples['panel']
                        images['template_mask.png'] = (feature(template, c['panel_color']) * 255).astype(np.uint8)
                    for name, image in images.items():
                        ok, data = cv2.imencode('.png', image)
                        if not ok:
                            raise RuntimeError('PNG kodlama basarisiz')
                        data.tofile(str(session / name))
                    writer.writerow([count, stamp, f'{score:.4f}', 0.55, accepted, base + '_raw.png'])
                    file.flush()
                    scores.append(score)
                    self.say(f'PANEL TEST #{count:04d} {stamp}: skor={score:.3f}, sonuc={"OK" if accepted else "RED"}, goruntu={base}_raw.png')
                    if self.bus.qsize() < 5:
                        # Nearest-neighbor zoom preserves the actual captured letters.
                        zoom = cv2.resize(raw, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST)
                        self.bus.put(('image', zoom))
                    self.wait(0.30)
        except InterruptedError:
            self.say('Panel testi kullanici tarafindan durduruldu')
        except Exception as e:
            self.say(f'PANEL TEST HATA: {e}')
        finally:
            self.stop.set()
            if scores:
                self.say(f'Panel testi: {len(scores)} olcum; min={min(scores):.3f}, medyan={np.median(scores):.3f}, max={max(scores):.3f}')
            self.say('Kayit klasoru: ' + str(session))
            self.say('Panel testi tamamlandi. Fare ve klavye girdisi gonderilmedi.')

        def run(self,h,c,samples):
         if c['mode'] == 'Panel test':
            self.run_panel_test(h, c, samples)
            return
        stats=[]
        try:
            self.say('5 saniye icinde listeden sectigin oyuna gec. Insert durdurur.'); self.wait(5)
            live=c['mode']!='Dry'
            if live: self.guard(h)
            keys=self.keylist(c['skills']); nextclick=0; lastreport=0; engaged=False; since=0; idx=0; confirmations=0
            basic=c.get('basic_attack') or {'key': 'R', 'interval': 1.0}
            basic_vk=self.keylist(basic['key'])[0]
            basic_interval=float(basic.get('interval', 1.0))
            last_basic=0
            rotation=[s for s in (c.get('skill_rotation') or []) if s.get('enabled', True)]
            for s in rotation: s['_vk']=self.keylist(s['key'])[0]
            last_used={}
            last_dead=None; dead_until=0
            with mss.mss() as sct:
        def verify():
            self.guard(h)
            im = self.capture(sct, h)
            raw_panel = self.cut(im, c['region']['panel'])

            if raw_panel is None or raw_panel.size == 0:
                        raise RuntimeError('Panel goruntusu bos')

                    templates = c.get('target_templates')
            if templates is None:
                        # Diger modlarin mevcut panel kontrolunu koru.
                        templates = {'panel': samples['panel']}
                        threshold = 0.55
                    else:
                        threshold = c['target_match_threshold']

                    best_name = None
            best_score = float('-inf')
            valid_count = 0

            for name, template in templates.items():
                        panel, cleaned_template = clean_panel_colors(
                            raw_panel.copy(),
                            template.copy(),
                            c['panel_color']
                        )

                        if (
                            cleaned_template.shape[0] > panel.shape[0]
                            or cleaned_template.shape[1] > panel.shape[1]
                        ):
                            continue

                        valid_count += 1
                        hits = detect(
                            panel,
                            cleaned_template,
                            c['panel_color'],
                            0.01,
                            [1.0]
                        )
                        score = float(hits[0][0]) if hits else 0.0

                        if score > best_score:
                            best_score = score
                            best_name = name

                    if valid_count == 0:
                        raise RuntimeError(
                            'Secili mob ornekleri panel alanina sigmiyor. '
                            'Panel alanini ve mob orneklerini yeniden sec.'
                        )

                    accepted = best_score >= threshold
                    self.say(
                        f"HEDEF: en yakin={best_name}, "
                        f"skor={best_score:.3f}, esik={threshold:.2f}, "
                        f"sonuc={'OK' if accepted else 'RED'}"
                    )
                return accepted
    while not self.stop.is_set():
                    t=time.perf_counter()
                    if live: self.guard(h)
                    if engaged:
                        if time.monotonic()-since>c['timeout']: raise RuntimeError('Hedef zaman asimi. Can barini elle kontrol et.')
                        if not verify():
                            engaged=False; self.say('Ust ad kayboldu; saldiri kesildi'); continue
                        hp = self.cut(self.capture(sct, h), c['region']['hp'])
                        b, g, r = cv2.split(hp)
                        red_ratio = float(
                            np.mean(
                                (r > 90) &
                                (r > g * 1.4) &
                                (r > b * 1.4)
                            )
                        )
                        if red_ratio < 0.02:
                            engaged=False
                            self.say(f'Mob oldu; can bari kayboldu (kirmizi={red_ratio:.3f}). Yeni aday aranacak')
                            continue
                        now=time.monotonic()
                        skill_used=False
                        for s in rotation:
                            if now-last_used.get(s['_vk'],0)>=float(s.get('cooldown',0)):
                                self.key(h,s['_vk'])
                                last_used[s['_vk']]=time.monotonic()
                                self.say(f"SKILL: {s['key']} basildi; cooldown {float(s.get('cooldown',0)):.1f} sn")
                                skill_used=True
                                break
                        if skill_used or now-last_basic>=basic_interval:
                            self.key(h,basic_vk)
                            last_basic=time.monotonic()
                            self.say("BASIC: R basildi")
                        self.wait(c.get('attack_delay',0.12)); continue
                    image=self.capture(sct,h)
                    if c['mode'] in ('Z Farm', 'Genel Farm'):
                        target=ord('Z') if c['mode']=='Z Farm' else self.keylist(c['target_key'])[0]
                        self.key(h,target); self.wait(.25)
                        if verify():
                            self.wait(.1)
                            if verify() and self.hp_ratio(sct,h,c)>=0.02:
                                self.key(h,ord('R')); engaged=True; since=time.monotonic(); idx=0
                                self.say('Genel hedef dogrulandi (ad + can bari)' if c['mode']=='Genel Farm' else 'Z hedefi dogrulandi')
                        self.wait(.2); continue
                    roi=c['region']['scene']; scene=self.cut(image,roi)
                    hits=detect(scene,samples['scene'],c['scene_color'],c['threshold'],[.9,1,1.1])
                    elapsed=(time.perf_counter()-t)*1000; stats.append(elapsed)
                    draw=scene.copy()
                    for score,x,y,w,hh in hits:
                        cv2.rectangle(draw,(x,y),(x+w,y+hh),(0,255,0),1)
                        cv2.drawMarker(draw,(x+w//2,y+hh+c['offset']),(0,255,255),cv2.MARKER_CROSS,12)
                        cv2.putText(draw,f'{score:.2f}',(x,y-3),cv2.FONT_HERSHEY_SIMPLEX,.4,(255,255,255),1)
                    if self.bus.qsize()<5:
                        ratio=min(1,950/draw.shape[1],400/draw.shape[0])
                        self.bus.put(('image',cv2.resize(draw,None,fx=ratio,fy=ratio)))
                    if time.monotonic()-lastreport>1:
                        self.say(f'Aday {len(hits)} | analiz {elapsed:.0f} ms'); lastreport=time.monotonic()
                    if live and hits and time.monotonic()>nextclick:
                        center=np.array([scene.shape[1]/2,scene.shape[0]/2])
                        target=min(hits,key=lambda z:np.linalg.norm(np.array([z[1]+z[3]/2,z[2]+z[4]/2])-center))
                        old=np.array([target[1]+target[3]/2,target[2]+target[4]/2])
                        freshimage=self.capture(sct,h)
                        fresh=detect(self.cut(freshimage,roi),samples['scene'],c['scene_color'],c['threshold'],[.9,1,1.1])
                        if not fresh: continue
                        current=min(fresh,key=lambda z:np.linalg.norm(np.array([x+w/2,y+hh/2])-old))
                        sc,x,y,w,hh=current
                        if np.linalg.norm(np.array([x+w/2,y+hh/2])-old)>70: continue
                        if last_dead is not None and time.monotonic()<dead_until:
                            if np.linalg.norm(np.array([x+w/2,y+hh/2])-last_dead)<45:
                                continue
                        px=roi[0]+x+w//2; py=roi[1]+y+hh+c['offset']
                        if not (roi[0]<=px<roi[0]+roi[2] and roi[1]<=py<roi[1]+roi[3]): continue
                        ox,oy,_,_=geometry(h)
                        self.click(h,ox+px,oy+py); nextclick=time.monotonic()+1.2
                        self.say(f'Tiklama: client ({px},{py}), skor {sc:.2f}')
                        good = False
                        consecutive = 0
                        deadline = time.monotonic() + 1.5

                        self.wait(0.15)

                        while time.monotonic() < deadline:
                            self.guard(h)

                            if verify():
                                consecutive += 1
                                if consecutive >= 2:
                                    good = True
                                    break
                            else:
                                consecutive = 0

                            self.wait(0.10)
                        self.say('UST HEDEF DOGRULANDI' if good else 'Dogrulama basarisiz; saldiri YOK')
                        if c['mode']=='Click test': break
                        if good:
                            self.say(f'SALDIRI: {keys} gonderiliyor')
                            self.key(h,ord('R')); engaged=True; since=time.monotonic(); idx=0
                    self.wait(.08)
        except InterruptedError: self.say('Durdurma istegi islendi')
        except Exception as e: self.say(f'HATA / DURDU: {e}')
        finally:
            self.stop.set()
            if stats: self.say(f'Tarama medyan {np.median(stats):.0f} ms; p95 {np.percentile(stats,95):.0f} ms')
            self.say('Calisma tamamlandi')

if __name__=='__main__':
    root=tk.Tk(); App(root); root.mainloop()
