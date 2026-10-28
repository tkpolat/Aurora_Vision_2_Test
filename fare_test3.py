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
U.GetCursorPos.argtypes=[C.POINTER(W.POINT)]; U.GetCursorPos.restype=W.BOOL

def position():
    p=W.POINT(); U.GetCursorPos(C.byref(p)); return p.x,p.y

# --- app.py'deki send() ile BIREBIR ayni ---
def send(i):
    a=(INPUT*1)(i)
    r=U.SendInput(1,a,C.sizeof(INPUT))
    return r

def absmove(x,y):
    vx=U.GetSystemMetrics(76); vy=U.GetSystemMetrics(77)
    vw=U.GetSystemMetrics(78); vh=U.GetSystemMetrics(79)
    nx=round((x-vx)*65535/(vw-1)); ny=round((y-vy)*65535/(vh-1))
    return send(INPUT(type=0,u=UNION(mi=MI(dx=nx,dy=ny,dwFlags=0x0001|0x8000|0x4000))))

def click(x,y):
    absmove(x,y); time.sleep(0.06)
    send(INPUT(type=0,u=UNION(mi=MI(dwFlags=0x0002))))
    time.sleep(0.12)
    send(INPUT(type=0,u=UNION(mi=MI(dwFlags=0x0004))))

print('>>> Simdi OYUNA tikla ve ORADA KAL. Farene dokunma.')
time.sleep(3)
print('baslangic =', position())

print('A) app.send() ile mutlak -> (500,300)')
print('   dondu =', absmove(500,300)); time.sleep(0.4)
print('   sonuc =', position())

print('B) app.send() ile mutlak -> (1200,300)')
print('   dondu =', absmove(1200,300)); time.sleep(0.4)
print('   sonuc =', position())

print('C) Gercek tiklama testi: sirayla bos alanlara tiklanacak.')
print('   KARAKTERIN YER DEGISTIRIP DEGISTIRMEDIGINE BAK.')
for (x,y) in [(600,600),(1300,600),(960,450),(960,700)]:
    click(x,y)
    print(f'   tiklandi ({x},{y}); imlec simdi = {position()}')
    time.sleep(0.7)

print('BITTI. Karakter tiklamalara tepki verdi mi?')
input('ENTER ile kapat...')