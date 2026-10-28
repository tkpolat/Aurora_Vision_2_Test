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

print('INPUT boyutu =', C.sizeof(IN))
print('baslangic =', pos())
print('5 saniye icinde OYUNA gec...')
time.sleep(5)

print('--- A) SendInput MUTLAK (0,0) ---')
inp = IN(type=0, u=UN(mi=MI(dx=0, dy=0, dwFlags=0x0001|0x8000)))
r = U.SendInput(1, C.byref(inp), C.sizeof(IN))
time.sleep(0.15)
print('  dondu =', r, ' hata =', C.get_last_error(), ' sonuc =', pos())

print('--- B) SetCursorPos (300,300) ---')
ok = U.SetCursorPos(300, 300)
time.sleep(0.15)
print('  dondu =', ok, ' sonuc =', pos())

print('--- C) SendInput GORELI (+200,+0) ---')
inp = IN(type=0, u=UN(mi=MI(dx=200, dy=0, dwFlags=0x0001)))
r = U.SendInput(1, C.byref(inp), C.sizeof(IN))
time.sleep(0.15)
print('  dondu =', r, ' sonuc =', pos())

input('ENTER ile kapat...')