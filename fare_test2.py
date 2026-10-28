import ctypes as C
from ctypes import wintypes as W
import time

U = C.WinDLL('user32', use_last_error=True)

class MI(C.Structure):
    _fields_=[('dx',W.LONG),('dy',W.LONG),('mouseData',W.DWORD),('dwFlags',W.DWORD),('time',W.DWORD),('extra',C.c_size_t)]
class KI(C.Structure):
    _fields_=[('vk',W.WORD),('scan',W.WORD),('flags',W.DWORD),('time',W.DWORD),('extra',C.c_size_t)]
class UN(C.Union):
    _fields_=[('mi',MI),('ki',KI)]
class IN(C.Structure):
    _fields_=[('type',W.DWORD),('u',UN)]

U.SendInput.argtypes=[W.UINT,C.POINTER(IN),C.c_int]
U.SendInput.restype=W.UINT
U.SetCursorPos.argtypes=[C.c_int,C.c_int]
U.SetCursorPos.restype=W.BOOL

def pos():
    p=W.POINT(); U.GetCursorPos(C.byref(p)); return (p.x,p.y)

def fg():
    h=U.GetForegroundWindow()
    n=U.GetWindowTextLengthW(h); b=C.create_unicode_buffer(n+1); U.GetWindowTextW(h,b,n+1)
    return b.value

def winrect():
    h=U.GetForegroundWindow(); r=W.RECT(); U.GetWindowRect(h, C.byref(r))
    return (r.left, r.top, r.right, r.bottom)

def absmove(x,y,vd):
    vx=U.GetSystemMetrics(76); vy=U.GetSystemMetrics(77)
    vw=U.GetSystemMetrics(78); vh=U.GetSystemMetrics(79)
    f=0x0001|0x8000|(0x4000 if vd else 0)
    nx=round((x-vx)*65535/(vw-1)); ny=round((y-vy)*65535/(vh-1))
    inp=IN(type=0,u=UN(mi=MI(dx=nx,dy=ny,dwFlags=f)))
    U.SendInput(1,C.byref(inp),C.sizeof(IN))

print('>>> Simdi OYUNA tikla ve ORADA KAL. Faresini oynatma.')
time.sleep(3)
print('ON PLANDAKI PENCERE =', fg())
print('Pencere dikdortgeni  =', winrect())
print('baslangic            =', pos())

print('1) SetCursorPos(500,400)')
U.SetCursorPos(500,400); time.sleep(0.5)
print('   sonuc =', pos(), '| on planda =', fg())

print('2) SendInput MUTLAK + VIRTUALDESK -> (700,400)')
absmove(700,400,True); time.sleep(0.5)
print('   sonuc =', pos(), '| on planda =', fg())

print('3) SendInput MUTLAK, VIRTUALDESK YOK -> (900,400)')
absmove(900,400,False); time.sleep(0.5)
print('   sonuc =', pos(), '| on planda =', fg())

print('4) SendInput GORELI (+150,+0)')
inp=IN(type=0,u=UN(mi=MI(dx=150,dy=0,dwFlags=0x0001)))
U.SendInput(1,C.byref(inp),C.sizeof(IN)); time.sleep(0.5)
print('   sonuc =', pos(), '| on planda =', fg())

print('5) Mutlak (700,400) + SOL TIK')
absmove(700,400,False); time.sleep(0.3)
U.SendInput(1,C.byref(IN(type=0,u=UN(mi=MI(dwFlags=0x0002)))),C.sizeof(IN)); time.sleep(0.1)
U.SendInput(1,C.byref(IN(type=0,u=UN(mi=MI(dwFlags=0x0004)))),C.sizeof(IN)); time.sleep(0.5)
print('   sonuc =', pos())

input('ENTER ile kapat...')