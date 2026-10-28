import ctypes as C
from ctypes import wintypes as W
import time

U=C.WinDLL('user32',use_last_error=True)
PTR=C.c_size_t
class MI(C.Structure): _fields_=[('dx',W.LONG),('dy',W.LONG),('mouseData',W.DWORD),('dwFlags',W.DWORD),('time',W.DWORD),('extra',PTR)]
class KI(C.Structure): _fields_=[('vk',W.WORD),('scan',W.WORD),('flags',W.DWORD),('time',W.DWORD),('extra',PTR)]
class UNION(C.Union): _fields_=[('mi',MI),('ki',KI)]
class INPUT(C.Structure): _fields_=[('type',W.DWORD),('u',UNION)]

U.SendInput.argtypes=[W.UINT,C.POINTER(INPUT),C.c_int]; U.SendInput.restype=W.UINT
U.SetCursorPos.argtypes=[C.c_int,C.c_int]; U.SetCursorPos.restype=W.BOOL
U.GetForegroundWindow.restype=W.HWND
U.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]; U.PostMessageW.restype=W.BOOL
U.ScreenToClient.argtypes=[W.HWND,C.POINTER(W.POINT)]; U.ScreenToClient.restype=W.BOOL

def send(i): return U.SendInput(1,(INPUT*1)(i),C.sizeof(INPUT))

def absmove(x,y):
    vx=U.GetSystemMetrics(76); vy=U.GetSystemMetrics(77)
    vw=U.GetSystemMetrics(78); vh=U.GetSystemMetrics(79)
    nx=round((x-vx)*65535/(vw-1)); ny=round((y-vy)*65535/(vh-1))
    send(INPUT(type=0,u=UNION(mi=MI(dx=nx,dy=ny,dwFlags=0x0001|0x8000|0x4000))))

def d_down(): send(INPUT(type=0,u=UNION(mi=MI(dwFlags=0x0002))))
def d_up():   send(INPUT(type=0,u=UNION(mi=MI(dwFlags=0x0004))))

def pm(x,y,msg,w):
    h=U.GetForegroundWindow()
    p=W.POINT(x,y); U.ScreenToClient(h,C.byref(p))
    lp=(p.y<<16)|(p.x & 0xFFFF)
    U.PostMessageW(h,msg,w,lp)

print('>>> OYUNA tikla ve ORADA KAL. Her A/B/C blogunda KARAKTERE bak.')
time.sleep(3)

print('=== A) PostMessage tabanli tik (3 nokta) ===')
for i,(x,y) in enumerate([(600,600),(1200,600),(960,700)],1):
    U.SetCursorPos(x,y); time.sleep(0.15)
    pm(x,y,0x0200,0); time.sleep(0.03)
    pm(x,y,0x0201,1); time.sleep(0.08); pm(x,y,0x0202,0)
    print(f'  A{i} tiklandi ({x},{y})'); time.sleep(1.0)

print('=== B) SendInput down + jiggle + up (3 nokta) ===')
for i,(x,y) in enumerate([(600,500),(1200,500),(960,800)],1):
    absmove(x,y); time.sleep(0.08); d_down(); time.sleep(0.05)
    send(INPUT(type=0,u=UNION(mi=MI(dx=2,dy=0,dwFlags=0x0001)))); time.sleep(0.04)
    send(INPUT(type=0,u=UNION(mi=MI(dx=-2,dy=0,dwFlags=0x0001)))); time.sleep(0.04)
    d_up()
    print(f'  B{i} tiklandi ({x},{y})'); time.sleep(1.0)

print('=== C) SendInput uzun basilis 350ms (3 nokta) ===')
for i,(x,y) in enumerate([(700,650),(1300,650),(960,350)],1):
    absmove(x,y); time.sleep(0.1); d_down(); time.sleep(0.35); d_up()
    print(f'  C{i} tiklandi ({x},{y})'); time.sleep(1.0)

print('=== D) KLAVYE: vk ile C, sonra scancode ile C ===')
for name,flags in [('vk',0),('scancode',0x0008)]:
    scan=U.MapVirtualKeyW(0x43,0)
    send(INPUT(type=1,u=UNION(ki=KI(vk=0x43,scan=scan,flags=flags)))); time.sleep(0.06)
    send(INPUT(type=1,u=UNION(ki=KI(vk=0x43,scan=scan,flags=flags|0x0002))))
    print(f'  {name} ile C gonderildi'); time.sleep(1.0)

print('BITTI. Hangi harf/bloglarda karakter tepki verdi?')
input('ENTER...')