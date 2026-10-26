AURORA VISION 2 - STATIK DENETIM VE TEST SURUMU

DURUM
Bu, paylasilan C# projesinin derlenmis veya yamalanmis surumu DEGILDIR.
Iki projenin mantigindan olusturulmus yeni Python uygulamasidir.
Python sozdizimi kontrol edilmistir; Windows, SendInput ve oyun ici test YAPILMADI.
Kaynak C# tekrar kullanilmamistir. Test sonuclari olmadan hata kesin cozuldu denemez.

KURULUM
Python 3.11 64-bit, Windows, gorunur ve kucultulmemis oyun penceresi.
  py -3.11 -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  .venv\Scripts\python.exe app.py
VS Code ile klasoru acabilirsiniz.

KALIBRASYON
Oyun penceresini acilir listeden SECIN. Geri sayim hedef pencereyi degistirmez.
1 Sahne alani: Sohbet, arayuz ve ust panel haric yaratigin gorunebilecegi alan.
2 Ust ad alani: Ustte secili yaratigin sadece ismini iceren alan.
3 Sahne isim ORNEGI: Sahnedeki Hob Goblin yazisinin TAMAMINI cok dar cerceveleyin.
4 Ust ad ORNEGI: Ust paneldeki Hob Goblin yazisinin TAMAMINI dar cerceveleyin.
Her secimde ENTER onaylar. Ornekler iki ayri goruntu olmalidir.
Sahne renk red, ust panel purple varsayilanlari kullanicinin ekran ornegine gore secilmistir.
Maskede yeterli piksel yok hatasinda renk secimini kontrol edin. Bunlar tum sunucularda gecerli degil.
Kaydet/yukle profil adi kutusuyla calisir. Eski C# sablonlarini otomatik yuklemez.

TESTLER
A Dry: Sadece bulma ve panelde onizleme. Oyun uzerine cizim yapmaz. Giris gondermez.
B Click test: Tek tiklama + iki ust panel kontrolu. R veya skill GONDERMEZ; sonra durur.
C Farm: Mouse secimi, iki panel kontrolu, bir kez R, sonra tus dizisi.
D Z Farm: Z secimi ve iki panel kontrolu; bu modda sahne ornegi gerekli degil.
Canli modlarda oyun on planda olmali. Odagi zorla degistirmez. F12 global durdurma.
Pencere boyutu degisirse yeniden kalibre edin. Tus oncesi hedef kontrolu vardir.
Durdurma suren goruntu eslesmesinin bitmesini bekleyebilir; calisan dongu varken ikincisi baslamaz.

GIRIS
SendInput sonucundaki eklenen olay sayisi kontrol edilir. 0 donmesi nedenini her zaman aciklamaz.
Oyun daha yuksek yetkiyle calisiyorsa Windows girisleri engelleyebilir. Koruma atlatma yok.
Windows masaustune yonelik girisler atomik pencere mesajlari degildir; odak son anda degisebilir.
Tus birakma finally ile denenir. Islem zorla sonlandirilirsa garanti yoktur.

ALGILAYICI
OCR yerine renk maskesi uzerinde kayan Dice eslesmesi: 2*kesisim/(sablon+aday).
Sahne .9/1/1.1 olcekleriyle, panel tek olcekte aranir. Arka plan RGB degerleri karsilastirilmaz.
Kirmizi/koyu veya mor yazi filtreleri tum arka plan degisimlerine bagisiklik SAGLAMAZ.
Ayni renkte nesneler, parilti, ortulme, antialiasing, farkli yazi boyutu ve yakin isimler hata uretebilir.
Yalnizca isim etiketinin tamamini ornekleyin. Bir tek harf veya buyuk bos alan secmeyin.
Esik dusurmek yanlis pozitifleri artirir. Once kalibrasyonu duzeltin.
Sabit offset govdeyi kesin bulmaz. Perspektif degisimlerinde manuel kalibrasyon gerekir.
Bu surum can barindan olum tespiti, yol bulma, kamera kontrolu, cooldown ve nesne kimligi izlemez.
Ustte eski ayni isim kalirsa tiklama dogrulamasi yeni bireyin secildigini kanitlamaz.
Azami saldiri suresi bu riski sinirlar; tam farm guvenilirligi icin HP/kimlik dogrulamasi sonraki istir.
Onceden baslatilmis oyun otomatik saldirisi uygulama durunca oyun tarafinda devam edebilir.

C# DENETIMI
- Diff: refColor<0, opak ToArgb degerlerini gecersiz sayar. Ayri tanimli bayragi gerekir.
- TickClick: ust panel dogrulamadan ApproachMs sonunda Engage.
- TickZ: dogrulamasiz Engage ayni cagrida kosulsuz Idle ile siliniyor.
- null yakalamada Engage temizlenmiyor; AttackLoop eski durumda devam edebilir.
- AttackLoop icinde tus basi Running/odak/hedef kontrolu yok.
- Stop/Start Join veya gorev sahipligi olmadan eski threadleri tekrar etkinlestirebilir.
- Bot ve Watcher Jiggle: ortak giris kilidi disinda imlec hareketi; tiklamayi bozabilir.
- SendInput, PrintWindow ve BitBlt donus degerleri yok sayiliyor.
- GrabAuto karanlik goruntude ayni modu tekrarlar; fallback yok.
- Scene/panel tek sablon havuzu; gorunum farki ele alinmiyor.
- ScoreAt max(NCC,BinScore) farkli anlamli skorlari birlestirir, arka plan uyumu puani sisirebilir.
- Template.FromBitmap Gray.Length uzerinde toplar: yeni Template dizisi tam boy oldugu icin bu akista sorun degil.
- same: onceki konum yakinindaki herhangi eslesmeyi ayni hedef sayiyor; nesne kimligi yok.
- sabit Reclick ve offset perspektif/hareket garantisi vermiyor.
- Preview sablonlari yenilenmiyor; eski sablonla sonuc gosterebilir.
- UI timer uzerinde goruntu tarama hotkey/menu yanitini geciktirebilir.
- FPS hesaplamasi islem suresiyle sinirli; timer ve dongu beklemelerini kapsamiyor.
- WindowKeyword ilk eslesme: yanlis pencere riski. Acik handle secimi kullanilmali.
- Pot/UI renk toleransi 0-255 ama RGB L1 fark 0-765. Etiket/olcek tutarsiz.
- PriorityForm tum sablonlari listeye ekler; secim listesiyle oncelik listesi karisiyor.
- Config.Save/Load hatalari yutuluyor; loglanmali.
- Dosya adi temizleme / yol karakterleri ve sablon uzerine yazma kontrolu yetersiz.
- _cap ve timer/image kaynaklari icin tam yasam dongusu yonetimi eksik.

KABUL KRITERI ONERISI
En az 3 arka plan, birden fazla mesafe, duran ve hareket eden hedeflerde deneyin.
30 tek tiklama testi icin dogru tiklama / dogru panel / basarisiz dogrulama sayisini tutun.
Hedef olmayan yazilari da ekleyin. Yanlis pozitif cikarsa canli Farm kullanmayin.
Bu sayilar gercek test sonucu degil, test planidir.
