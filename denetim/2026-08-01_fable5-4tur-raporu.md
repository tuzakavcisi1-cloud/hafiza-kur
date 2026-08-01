# Dördüncü tur denetim raporu — `hafiza-kur` v2.4.1

**Denetçi:** Fable 5 (claude-opus-5) · **Tarih:** 1 Ağustos 2026
**Denetlenen:** `hafiza.py` · 4 394 satır ·
SHA256 `738849C086512C7485048C58570EEDCA045E21550EF9BE357197FF577126F300` — **bağımsız
olarak doğrulandı**, `.skill` paketindeki kopya da aynı.
**Ortam:** Linux x86_64 · Python 3.11.15 · konteyner. İzin sınıfını ölçmek için ayrıca
`uid=1001 (denetci)` adında **root olmayan** bir kullanıcı açtım; ENOSPC sınıfı için
600 KB'lık bir `tmpfs` bağladım.

---

## 1. KARAR

# DÜZELT

Üç YÜKSEK bulgu var ve üçü de aynı yerden çıkıyor: **hüküm veren kod, hükmü veremediği
anlara karşı hâlâ dayanıksız.** Biri kendi düzelttiğini sandığın kusurun (Y-4′) tam
kendisi ve tek satırlık bir sıralama hatası yüzünden hiç kapanmamış; biri `kapi`'nin
gerçek bir KIRMIZI'yı tek bayt ile "araç kusuru"na çevirmesine izin veriyor; biri yarıda
kesilen bir `derle`'den **araç içi çıkışı olmayan kalıcı bir yanlış-kırmızı** bırakıyor.

---

## 2. BULGULAR

Sıralama ciddiyete göre. Her bulgu **koşuldu**; koşmadığım hiçbir şeyi bulgu yazmadım.

---

### B4-1 🔴 YÜKSEK — ENOSPC'te kilit KALICI olarak sızıyor; proje bir daha yazılamıyor

**(a) Hüküm.** `kilit_al` sahipliği (`KILIT[0]`) kilit dosyasına **yazdıktan sonra**
kaydediyor; yazma ENOSPC ile düşerse `atexit`'teki `kilit_birak` hiçbir şey yapmaz ve
0-baytlık `.kilit` sonsuza kadar kalır — yani `Y-4′` diye kapatıldığı yazılan kusur
**hiç kapanmamış**.

**(b) Üreten tam komut dizisi.**

```bash
mount -t tmpfs -o size=600k tmpfs /mnt/kucuk
mkdir -p /mnt/kucuk/p && (cd /mnt/kucuk/p && git init -q .)
python3 hafiza.py kur   --kok=/mnt/kucuk/p
python3 hafiza.py not   --kok=/mnt/kucuk/p --konu=genel-durum --metin="ilk not metni"
python3 hafiza.py derle --kok=/mnt/kucuk/p
dd if=/dev/zero of=/mnt/kucuk/dolgu bs=1k count=10000     # diski TAM doldur
python3 hafiza.py muhur --kok=/mnt/kucuk/p "disk dolu iken muhurleme denemesi"
rm -f /mnt/kucuk/dolgu                                     # yer aç
find /mnt/kucuk/p -name .kilit -exec ls -la {} \;
python3 hafiza.py not --kok=/mnt/kucuk/p --konu=genel-durum --metin="deneme-metni"
```

**(c) Gerçek çıktı.**

```
HATA: DISK DOLU (ENOSPC) — islem tamamlanamadi.
=== disk bosaldi. kilit kaldi mi: ===
-rwxr-xr-x 1 root root 0 Aug  1 11:32 /mnt/kucuk/p/arsiv/hafiza/.kilit
=== bundan sonra HER yazma komutu: ===
  not   -> HATA: BASKA BIR YAZMA ISLEMI SURUYOR (kilit: arsiv/hafiza/.kilit)   exit=2
  derle -> HATA: BASKA BIR YAZMA ISLEMI SURUYOR (kilit: arsiv/hafiza/.kilit)   exit=2
  muhur -> HATA: BASKA BIR YAZMA ISLEMI SURUYOR (kilit: arsiv/hafiza/.kilit)   exit=2
  karar -> HATA: BASKA BIR YAZMA ISLEMI SURUYOR (kilit: arsiv/hafiza/.kilit)   exit=2
```

**(d) Neden kusur.** `01_DORDUNCU_YANIT §2.3 / Y-4′` şunu yazıyor: *"ENOSPC …
`kilit_birak`: pid **yoksa** dosya bizimdir (O_EXCL ile biz açtık), silinir."* O kural
**hiç çalışmıyor**, çünkü `kilit_birak`'ın ilk satırı `p, ino = KILIT[0], KILIT[1]` ve
`if not p: return`. `kilit_al`'da sıra şu (satır 674–678):

```python
    fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)   # <-- kilit ARTIK VAR
    with os.fdopen(fd, "w", ...) as f:
        f.write("pid=%d · ..." % ...)                       # <-- ENOSPC BURADA
    KILIT[0] = p                                            # <-- HİÇ ÇALIŞMIYOR
```

Sahiplik, kilidin var olduğu andan **sonra** kaydediliyor; arada bir istisna varsa kilit
sahipsiz kalıyor. Sonuç, düzeltmenin engellemeye çalıştığı şeyin birebir aynısı: *"proje
kalıcı yazmaya kapalı"*. Ve bu, aracın kendi doktrininin (`fail-closed` + `atexit`
güvencesi) en çok güvenilen parçası.

**Doğrulama (teşhisin kanıtı).** `KILIT[0] = p` satırını `with` bloğunun **önüne**
aldım, başka hiçbir şeye dokunmadım, aynı senaryoyu koştum:

```
DUZELTILMIS SURUM — kalan kilit sayisi: 0
MUHURLENDI: BAF2F98FBFE0516B...     -> sonraki yazma exit=0
```

**(e) Ciddiyet: YÜKSEK.** Tek bir disk-dolu anı projeyi kalıcı olarak yazmaya kapatıyor;
kurtuluş yalnız kullanıcının dosyayı elle silmesi (aracın kendisi bu durumda "başka bir
işlem sürüyor" diyerek yanlış teşhis koyuyor).

---

### B4-2 🔴 YÜKSEK — `kapi`, `SystemExit` dışındaki her istisnada TÜM hükmü kaybediyor; gerçek KIRMIZI exit 3'e kaçıyor

**(a) Hüküm.** `cmd_kapi` yalnız `except SystemExit` yakalıyor; `zincir_dogrula` ise
halka alanının **tipini** doğrulamıyor. `_ZINCIR.jsonl`'de tek bir `"halka": 1234`
(metin yerine sayı) `TypeError` üretiyor, `cmd_kapi`'nin gövdesinden dışarı çıkıyor,
**o ana kadar toplanmış bütün bulgular basılmadan kayboluyor**, exit 3 ve mesaj *"bu bir
ARAÇ KUSURUDUR"* oluyor.

**(b) Üreten tam komut dizisi.**

```bash
mkdir t2 && (cd t2 && git init -q .)
python3 hafiza.py kur   --kok=t2
python3 hafiza.py muhur --kok=t2 "ikinci halka icin gerekce"
# GERÇEK bir kırmızı üret: zorunlu bölüm satırını sil
python3 - <<'PY'
p="t2/PROJE_HAFIZA.md"; L=open(p,encoding="utf-8").read().split("\n")
open(p,"w",encoding="utf-8",newline="\n").write("\n".join(s for s in L if not s.startswith("## KIRMIZI")))
PY
python3 hafiza.py kapi --kok=t2 ; echo "exit=$?"        # ADIM 1
python3 - <<'PY'
import json; p="t2/arsiv/hafiza/_ZINCIR.jsonl"
L=[json.loads(s) for s in open(p,encoding="utf-8") if s.strip()]
L[0]["halka"]=1234
open(p,"w",encoding="utf-8",newline="\n").write("\n".join(json.dumps(k,ensure_ascii=False) for k in L)+"\n")
PY
python3 hafiza.py kapi --kok=t2 ; echo "exit=$?"        # ADIM 2
```

**(c) Gerçek çıktı.**

```
ADIM 1 (yalnız gerçek kırmızı):
  [H1] 1 satir KAYIP (snapshot'ta var, hicbir ciktida yok):
        - KAYIP: ## KIRMIZI ÇİZGİLER / AÇIK KAPILAR
  [H1-KOVA] 1 satir CANLIDA OLMALIYDI, YOK — BEYANSIZ TASINMA
  [H3] zorunlu bolum YOK: ## KIRMIZI CIZGILER
  exit=1                              <-- doğru hüküm

ADIM 2 (aynı kırmızı + halka tipi bozuk):
HATA: BEKLENMEYEN DURUM — bu bir ARAC KUSURUDUR, senin dosyalarinin hukmu degil.
  TypeError: unsupported operand type(s) for +: 'int' and 'str'
  Tam iz: /root/denetim/hafiza_hata_izi.txt
  exit=3                              <-- "ölçemedim, hüküm yok"; ÜÇ bulgu görünmüyor
```

**(d) Neden kusur.** Üç ayrı sözü aynı anda bozuyor:

1. `cmd_kapi`'nin kendi docstring'i: *"ne olursa olsun O ANA KADAR TOPLANAN hüküm
   basılır"* — `SystemExit` dışındaki hiçbir istisnada basılmıyor.
2. A-2'nin kuralı: *"gerçek kapı bulgusu VARSA 1 döner"* — burada gerçek üç bulgu var,
   1 dönmüyor.
3. `references/`'de bu sınıfın (Y-3, "defter bozuk → temiz hata") **sınırda** kapatıldığı
   yazıyor. Kapanmamış: `_json_coz`/`defter_liste` şema doğrulaması `_ZINCIR.jsonl`'in
   **alan tiplerine** uygulanmıyor.

Ve saldırgan tarafı önemli: defteri tahrif edebilen biri aynı hamleyle `halka`'yı sayı
yapabilir; gürültülü bir KIRMIZI, kendini suçlayan bir çökmeye dönüşür. `kapi || dur`
yine durur (3 ≠ 0), ama insan da, ajan da çıktıdan **yanlış** sonucu çıkarır: "araç
bozuk", "denetim izim tahrif edilmiş" değil.

**Sınıfın tamamını ölçtüm.** 210 tip-karışıklığı denemesi koştum (`_ZINCIR.jsonl`,
`_CIPA.json`, `.hafizarc`'ın tüm alanları × `int/float/bool/None/[]/{}/["a"]/{"a":1}`).
Sonuç: **210'da 5'i** ham istisna üretiyor ve **hepsi tek alandan**: `_ZINCIR[i].halka`.
Yani delik dar ve kapatılması ucuz — ama `cmd_kapi`'nin sınır davranışı ayrıca
düzeltilmeli, çünkü bir sonraki tip hatası başka bir alandan gelecek.

```
TOPLAM DENEME: 210
ARAC KUSURU (ham istisna) uretenler: 5
  exit=3  _ZINCIR[0].halka = 1234        TypeError: ... 'int' and 'str'
  exit=3  _ZINCIR[0].halka = 1.5         TypeError: ... 'float' and 'str'
  exit=3  _ZINCIR[0].halka = True        TypeError: ... 'bool' and 'str'
  exit=3  _ZINCIR[0].halka = ['a']       TypeError: can only concatenate list ...
  exit=3  _ZINCIR[0].halka = {'a': 1}    TypeError: ... 'dict' and 'str'
```

**(e) Ciddiyet: YÜKSEK.** Bu, senin §4.1'de sorduğun **5(b)** sorusunun cevabıdır:
**evet, gerçek bir kırmızı 3'e kaçabiliyor.**

---

### B4-3 🔴 YÜKSEK — Yarıda kesilen `derle`, araç içi çıkışı OLMAYAN kalıcı yanlış-kırmızı bırakıyor

**(a) Hüküm.** `cmd_derle` beyan defterini (`_YENI_SATIRLAR.txt` / `_KOVA.json`) canlı
dosyayı yazmadan **önce** güncelliyor; canlıya yazma düşerse (EACCES/EROFS/ENOSPC/Ctrl-C)
defter "bu satırlar canlıya eklendi" der, canlı dosya eklenmemiştir — ve bu durumdan
**hiçbir araç komutu çıkaramıyor**; `kapi`'nin verdiği tavsiye de yanlış.

**(b) Üreten tam komut dizisi** (root olmayan kullanıcı olarak):

```bash
mkdir r5 && (cd r5 && git init -q .)
python3 hafiza.py kur   --kok=r5
python3 hafiza.py not   --kok=r5 --konu=genel-durum --metin="ilk not metni"
python3 hafiza.py derle --kok=r5
python3 hafiza.py not   --kok=r5 --konu=genel-durum --metin="ikinci not metni"
chmod 444 r5/PROJE_HAFIZA.md            # canlı yazılamaz (salt-okunur repo / EROFS eşdeğeri)
python3 hafiza.py derle --kok=r5 ; echo "exit=$?"
chmod 644 r5/PROJE_HAFIZA.md            # kullanıcı sorunu düzeltir
python3 hafiza.py kapi  --kok=r5
python3 hafiza.py derle --kok=r5        # aracın önerdiği tek makul hamle
python3 hafiza.py kapi  --kok=r5
```

**(c) Gerçek çıktı.**

```
derle(0444) exit=3
HATA: BEKLENMEYEN DURUM — bu bir ARAC KUSURUDUR ...
  PermissionError: [Errno 13] Permission denied: '.../PROJE_HAFIZA.md'

-- izin geri verildi; kapi:
   [H1] 2 satir KAYIP (snapshot'ta var, hicbir ciktida yok)
   [H1-KOVA] 2 satir CANLIDA OLMALIYDI, YOK — BEYANSIZ TASINMA:
         -> Tasimayi ARACLA yap: hafiza.py emekli <bas>-<son> --not "..."

-- derle yeniden kosuldu; SON kapi:
   [H1] 2 satir KAYIP ...
   [H1-KOVA] 2 satir CANLIDA OLMALIYDI, YOK ...
   gunluk/ kalan fragman: 0            <-- fragman tükendi, kırmızı kalıcı
```

`_YENI_SATIRLAR.txt`'de "ikinci not metni" **iki kez** duruyor (biri çöken koşumdan,
biri başarılı koşumdan), `_KOVA.json > ek_canli` de aynı şekilde. Muhasebe çok-küme
olduğu için beklenen sayı 2, gerçek 1 → `[H1] KAYIP` kalıcı.

**(d) Neden kusur.**

- `zincir_on_kontrol`'ün docstring'i *"yazan her komut, İŞE BAŞLAMADAN …"* diyor —
  ama yalnız zincirin okunabilirliğini ön-kontrol ediyor; **yazılabilirliği** hiç
  sormuyor. Yarıda kalma penceresi kapatılmamış, yalnız daraltılmış.
- Bu, aracın var oluş sebebinin tersi: yanlış-pozitif üretip kullanıcıyı **elle blok
  cerrahisine** itiyor. Üstelik önerdiği çare (`emekli`) durumu **kötüleştirir**: canlıda
  zaten olmayan satırları arşive taşımaya çalışır.
- Tek gerçek çıkış, `_YENI_SATIRLAR.txt`'yi elle düzeltmek — ki aracın kendi kuralı
  *"defterler denetim izidir, elle düzeltme"* diyor ve `kapi` bu yolu hiç söylemiyor.
- Tetikleyiciler egzotik değil: salt-okunur çalışma kopyası, disk dolu, Ctrl-C, OOM,
  konteyner tahliyesi, ağ diskinin kopması.

Aynı sınıfın **kurtulabilen** kolunu da ölçtüm: `arsiv/hafiza/gunluk` salt-okunur iken
`derle` → `[H0] defter MUHURSUZ degismis ×3`, ama yeniden `derle` YEŞİL veriyor. Yani
sorun tüm yarıda kalmalarda değil, **beyan-canlı sırasında**.

**(e) Ciddiyet: YÜKSEK.** Kurtarılabilirlik, bu aracın en çok iddia ettiği özellik
(§4). Bu pencerede iddia tutmuyor.

---

### B4-4 🟠 ORTA-YÜKSEK — İzin/salt-okunur sınıfı "ARAÇ KUSURU" diye teşhis ediliyor

**(a) Hüküm.** Belgede exit 3'ün tanımlı kollarından biri olan *"izin yok"*, kodda özel
bir dal değil: EACCES/EPERM/EROFS son ağın genel koluna düşüyor ve kullanıcıya *"bu bir
ARAÇ KUSURUDUR"* + "Tam iz: hafiza_hata_izi.txt" deniyor.

**(b) Üreten tam komut dizisi** — `uid=1001` (root **değil**) olarak, 9 senaryo:

```bash
su denetci -c 'bash /tmp/izin/kos.sh'     # kur/not/derle/karar/muhur/kapi × chmod 555/444/000
```

**(c) Gerçek çıktı (özet tablo).**

| # | Senaryo | exit | Hüküm metni |
|---|---|---|---|
| 1 | `muhur`, `arsiv/hafiza` 0555 | 3 | **ARAÇ KUSURU** (`PermissionError … .kilit`) |
| 2 | `kapi`, `arsiv/hafiza` 0555 | 0 | temiz — YEŞİL (doğru; `kapi` yazmıyor) |
| 3 | `kapi`, `_ZINCIR.jsonl` 0000 | 3 | temiz (`DOSYA OKUNAMADI`) ✔ |
| 4 | `kapi`, `PROJE_HAFIZA.md` 0000 | 3 | temiz (`DOSYA OKUNAMADI`) ✔ |
| 5 | `derle`, canlı 0444 | 3 | **ARAÇ KUSURU** + B4-3'ün kalıcı kırmızısı |
| 6 | `not`, `gunluk/` 0555 | 3 | **ARAÇ KUSURU** |
| 7 | `kur`, kök 0555 | 3 | **ARAÇ KUSURU** (`.hafizarc`) |
| 8 | `karar`, `kararlar/` 0555 | 3 | **ARAÇ KUSURU** |
| 9 | `derle`, arşiv `gunluk` 0555 | 3 | **ARAÇ KUSURU** + 3× `[H0] MUHURSUZ` |

**(d) Neden kusur.** Çıkış kodu doğru (3), **hüküm yanlış**. Bir `chmod`, kullanıcıya
"aracın bir hatası var, iz dosyasını aç" diye sunuluyor; doğru hüküm ENOSPC dalındaki
gibi olmalı: *"bu bir ARAÇ kusuru değil; şu yola yazma iznin yok"* + hangi yol + ne
yapılacağı. Aracın kendi ayrımı (`ARAÇ KUSURU` ≠ `ORTAM/PROJE YAPISI`) tam da burada
çöküyor. Ayrıca `t_y42`'nin Y-1 senaryosu bunu göremez, çünkü tek ölçütü *"ham traceback
var mı"* — hepsinde yok, hepsi "geçer".

**(e) Ciddiyet: ORTA-YÜKSEK.** Yanlış teşhis, kullanıcıyı doğru çareden uzaklaştırır ve
denetimde "araç olgun değil" delili sayılır — senin kendi Y-3 gerekçenle.

---

### B4-5 🟠 ORTA — `hafiza_hata_izi.txt` PROJE AĞACININ DIŞINA yazılıyor

**(a) Hüküm.** Son ağ, hata izini koşulsuz `os.getcwd()` altına yazıyor; `--kok` başka
yerdeyken bu, proje ağacının **dışı**dır — aracın `cli_yol_coz` ile "tek kapı"ya
bağladığı, `B-2`/`B-3` diye kapatılan sınıfın yeni kılığı. Üstelik bunu yapan `kapi`,
yani salt-okuma olması gereken ÖLÇÜM komutu.

**(b) Üreten tam komut dizisi.**

```bash
mkdir -p /tmp/disaridan && cd /tmp/disaridan
python3 ~/denetim/hafiza.py kapi --kok=/root/denetim/t1     # t1'de bozuk halka var
ls -la /tmp/disaridan
cd / && python3 ~/denetim/hafiza.py kapi --kok=/root/denetim/t1
```

**(c) Gerçek çıktı.**

```
  Tam iz: /tmp/disaridan/hafiza_hata_izi.txt
-rw-r--r-- 1 root root 790 Aug  1 11:29 hafiza_hata_izi.txt
hafiza.py 2.4.1 · 2026-08-01T11:29:56
komut: kapi --kok=/root/denetim/t1
Traceback (most recent call last): ...
...
  Tam iz: /hafiza_hata_izi.txt              <-- cwd `/` iken kök dizine yazdı
```

**(d) Neden kusur.** `00_OKU_BENI §3`: *"yazma izni yalnız verdiğin dizine"*. `cli_yol_coz`:
*"Hafıza ve denetim izi proje ağacının DIŞINDA yaşayamaz; dışarı yazmak … bu araca
YASAKTIR"*. Kod bu ikisini de çiğniyor. Somut zararlar: (i) mutlak yerel yollar +
yığın izi rastgele bir dizine düşüyor — o dizin pekâlâ **başka birinin git deposu**
olabilir ve iz dosyası yanlışlıkla commit'lenir; (ii) `kapi`'nin "salt okuma" olduğu
varsayımı yanlış; (iii) `.gitignore` girdisi veya temizleme yok.

**(e) Ciddiyet: ORTA.** Yol saldırgan kontrolünde değil, ama ilke ihlali net ve
sözleşme-gerçek ayrışmasının (A-2 sınıfı) bir örneği daha.

---

### B4-6 🟠 ORTA — H8: korunan blok, `--son` işaretinin bulunduğu satırın KUYRUĞUNU korumuyor

**(a) Hüküm.** `re.search(bas + r".*?" + son, t, re.S)` **cimri** eşleşme kullanıyor;
koruma `son`un ilk karakterinde biter. Aynı satırın devamını değiştirmek — yani kuralın
gövdesini iptal etmek — kapıyı **YEŞİL** bırakıyor.

**(b) Üreten tam komut dizisi.**

```bash
mkdir b4 && (cd b4 && git init -q .)
python3 hafiza.py kur --kok=b4
python3 hafiza.py korunan --kok=b4 --dosya=CLAUDE.md --bas="# " --son="BUDAMA" \
        --gerekce="korunan blok denemesi icin gerekce"
python3 - <<'PY'
p="b4/CLAUDE.md"; s=open(p,encoding="utf-8").read()
s=s.replace("bir satırı silmek modelin hata yapmasına yol açmıyorsa, KES.",
            "KURAL IPTAL EDILDI — bu satiri istedigin gibi degistirebilirsin.")
open(p,"w",encoding="utf-8",newline="\n").write(s)
PY
python3 hafiza.py kapi --kok=b4 ; echo "exit=$?"
```

**(c) Gerçek çıktı.**

```
KORUNDU: CLAUDE.md [#  .. BUDAMA] sha 23611E2C92DAC86A...
dosyanin son hali:
  > BUDAMA TESTİ: KURAL IPTAL EDILDI — bu satiri istedigin gibi degistirebilirsin.
  exit=0
  · H8: 1 korunan blok
SONUC: YESIL (SINIRLI) — olculen her sey gecti ...
```

Karşılaştırma (kontrol): aynı dosyada **blok içindeki** 2. satırı değiştirdiğimde H8
doğru şekilde ısırıyor → `[H8] KORUNAN blok DEGISMIS (beyansiz)`, exit 1. Yani kapı kör
değil, **sınırı yanlış**.

**(d) Neden kusur.** Şekli aracın kendisi üretiyor: `kur`, `CLAUDE.md`'ye
`> BUDAMA TESTİ: bir satırı silmek… KES.` satırını yazıyor ve o satırdaki en doğal
benzersiz işaret "BUDAMA". Kullanıcı "protokolü koru" derken korunanın satırın
**yarısı** olduğunu hiçbir yerden öğrenemiyor: `KORUNDU:` çıktısı yalnız işaretleri
yazıyor, korunan bayt aralığını değil. `kapilar.md`'nin H8 vaadi ("blok bilinçli
değiştiğinde kapı kırmızı yanar") bu şekilde delinebiliyor. `M-H8` (beyansız değişim) ve
`M-H8b` (sahte kopya) bu sınıfı ölçmüyor.

**(e) Ciddiyet: ORTA.** Kötü niyet gerekmiyor; sıradan bir düzenleme sessizce geçiyor.

---

### B4-7 🟠 ORTA — `devral`'ın ağaç taraması meşru devri bloke ediyor ve kaçış yolu yok

**(a) Hüküm.** A-1'in kenar düzeltmesi (`agactaki_kilitler`) ağaçtaki **her** `.kilit`i
durdurucu sayıyor; alakasız bir alt projedeki **bayat** kilit `devral`'ı tümden
kilitliyor — üstelik aracın kendi teşhisi "silmen güvenli" diyor ama yine de reddediyor.

**(b) Üreten tam komut dizisi.**

```bash
mkdir -p /tmp/dv/vendor/altproje/arsiv/hafiza && cd /tmp/dv && git init -q .
printf '# Proje Hafizasi\n> Son guncelleme: 2026-08-01\n\n## GUNCEL DURUM\n- ilerlemis\n' > PROJE_HAFIZA.md
echo "pid=999999 · 2026-07-01T10:00:00 · komut: derle" > vendor/altproje/arsiv/hafiza/.kilit
python3 ~/denetim/hafiza.py devral --kok=/tmp/dv
```

**(c) Gerçek çıktı.**

```
HATA: BASKA BIR YAZMA ISLEMI SURUYOR (kilit: vendor/altproje/arsiv/hafiza/.kilit)
  Tani: pid 999999 ARTIK YOK — bu kilit BAYAT (cokme kalintisi). Silmen guvenli: ...
```

Aynı kilit `node_modules/x/.kilit` altındayken `devral` **sorunsuz geçiyor** (exit 0).

**(d) Neden kusur.** Kapsam hem geniş hem dar:

- **Geniş:** hariç listesi 6 adlık sabit bir denylist (`.git, node_modules, __pycache__,
  .venv, dist, build`). `vendor/`, `target/`, `.tox/`, `Pods/`, `.gradle/`, `out/`,
  `bin/`, `.next/`, `.cache/`, `site-packages/` kapsam içinde — yani üçüncü taraf
  ağaçlardaki bir dosya adı meşru devri durduruyor.
- **Dar:** `node_modules` hariç tutulduğu için oradaki **gerçek** bir yazar görülmüyor.
  Tanımın kendisi "ağacın tamamı" değil, "ağacın rastgele bir alt kümesi".
- **Çıkış yok:** `devral` ömürde bir kez koşar, `--zorla` yok, ve engel bayat bir kilit
  için bile geçerli. Bu, tam da 2. tasarım denemesinin *"meşru v1 devralmasını tümden
  kilitledi"* hatasının daha yumuşak bir tekrarı.
- **Asimetri:** `kur` bu taramayı yapmıyor (yalnız kendi yolunun kilidini alıyor).
  Gerekçe ("iki ad alanı aynı canlıya yazar") `kur` için de geçerliyken uygulanmamış.
- **TOCTOU:** tarama ile `kilit_al(y)` arasında pencere var; eski ad alanında o aralıkta
  başlayan bir yazar görünmez.

**(e) Ciddiyet: ORTA.** Veri kaybı yok; ama `devral` bu skill'in **tek giriş kapısı** ve
burada takılan kullanıcının elinde belge yok.

---

### B4-8 🟠 ORTA — Ölçüm hatası hâlâ exit 1 döndürebiliyor (senin 5(a) sorunun: EVET)

**(a) Hüküm.** Okunamayan bir arşiv dosyası `fail("H1", …)` üretiyor; yani saf bir
**ölçüm hatası** gerçek kırmızıyla aynı kodu (1) veriyor, sözleşme ise "izin yok → 3"
diyor.

**(b/c) Komut ve çıktı** (root olmayan kullanıcı):

```bash
chmod 000 a1/arsiv/hafiza/HAFIZA_01.md
python3 hafiza.py kapi --kok=a1 ; echo exit=$?
```
```
SONUC: FAIL (3 bulgu)
  [H1] 1 arsiv dosyasi OKUNAMADI — bu dosyalardaki satirlar 'KAYIP' gorunebilir ...
exit=1
```

**(d) Neden kusur.** Yalnız sözleşme ihlali. Yön "güvenli" (gürültülü) ama sonuç şu:
`kapi`'nin çıkış kodu **"tahrif" ile "chmod"u ayırt edemiyor** — A-2'nin çözmeye
çalıştığı problemin ta kendisi, başka bir kolda. `kapi_yalit`'in aynı çağrıyı `O`'ya
(ölçülemedi) yazması ile hemen ardından `fail(...)` çağrılması birbiriyle de çelişiyor:
aynı olay hem `?` hem `[H1]` olarak raporlanıyor.

**(e) Ciddiyet: ORTA.**

---

### B4-9 🟡 DÜŞÜK-ORTA — BOM'lu dosyalar sahte `[H1] KAYIP` ve yanlış çare üretiyor

**(a) Hüküm.** `oku()` `utf-8` ile açıyor (`utf-8-sig` değil); Windows Not Defteri'nin
"UTF-8" kaydı BOM ekler ve ilk satır değişmiş sayılır.

**(b/c) Komut ve çıktı.**

```bash
python3 -c "d=open('bom/PROJE_HAFIZA.md',encoding='utf-8').read();
open('bom/PROJE_HAFIZA.md','w',encoding='utf-8-sig',newline='\n').write(d)"
python3 hafiza.py kapi --kok=bom
```
```
  [H1] 1 satir KAYIP (snapshot'ta var, hicbir ciktida yok):
        - KAYIP: # bom — CANLI HAFIZA
  [H1-KOVA] 1 satir CANLIDA OLMALIYDI, YOK — BEYANSIZ TASINMA
        -> Tasimayi ARACLA yap: hafiza.py emekli <bas>-<son> --not "..."
```

`.hafizarc` BOM'lu iken:
```
HATA: DEFTER BOZUK — .hafizarc
  gecersiz JSON — satir 1, sutun 1: Unexpected UTF-8 BOM (decode using utf-8-sig)
  Yol: elle duzelt ya da surum kontrolunden geri al ...
```

**(d) Neden kusur.** Üç katmanlı ironi: (1) `oku()`'nun UTF-8 hata mesajı kullanıcıyı
*"Not Defteri > Farklı Kaydet > Kodlama: UTF-8"*'e yönlendiriyor — Windows'ta bu tam da
BOM üretebilen yol; (2) canlı dosyada BOM, içerik hiç değişmemişken `KAYIP` diyor ve
yanlış çareyi (`emekli`) öneriyor; (3) `.hafizarc` bir **defter değil**, yapılandırma
dosyası — "sürüm kontrolünden geri al" çaresi burada abartılı, doğru çare "BOM'suz
kaydet" ve mesaj bunu söylemiyor. Bu, "Windows ÖLÇÜLMEDİ" başlığının somut ilk faturası.

**(e) Ciddiyet: DÜŞÜK-ORTA.** Veri kaybı yok, ama hedef kullanıcı kitlesi (Türkçe +
Windows) için en olası ilk arıza.

---

### B4-10 🟡 DÜŞÜK — `not`, 1–2 karakterlik gövdeye "Boş fragman yazılmaz" diyor

```bash
python3 hafiza.py not --kok=p --konu=genel-durum --metin="x"
HATA: Bos fragman yazilmaz. --metin ver ya da stdin'den boru et.   exit=2
```

Eşik `len(govde.strip()) < 3` (satır 1651) ama mesaj "boş" diyor. Kullanıcı `--metin`
verdiğini bildiği için mesajı kendi girdisiyle bağdaştıramaz. **DÜŞÜK.**
İlgili not: `if not govde and not sys.stdin.isatty(): govde = sys.stdin.read()` — stdin'i
kapanmayan bir boruya bağlı bir CI adımında bu çağrı **süresiz bekler**; zaman aşımı yok.

---

### B4-11 🟡 DÜŞÜK — `zincir_dogrula` her `kapi` koşumunda İKİ KEZ çalışıyor

Satır 2743 ve 2748 aynı işlevi ayrı ayrı çağırıyor; ikisi de tüm zinciri gezip **tüm
defter SHA'larını** yeniden hesaplıyor.

```
4 001 halkalı zincir · kapi süresi (3 koşum ortalaması)
  mevcut (çift çağrı) : 0.36 0.36 0.35 sn
  tek çağrıya indirilmiş: 0.25 0.24 0.23 sn      -> ~%45 israf
```

Mutlak değer küçük, ama zincir **append-only ve sıkıştırmasız**: bu maliyet projenin
ömrü boyunca doğrusal büyüyor. **DÜŞÜK** (ama düzeltmesi üç satır).

---

## 3. KIDEMLİ MÜHENDİS İNCELEMESİ

Soru "kırılıyor mu" değil, "bu ürün yaşar mı".

### 3.1 Mimari ve karmaşıklık bütçesi

**Değeri hak eden kısım.** Fikir sağlam ve nadir: *ölçülmeyen kapının hükmü yoktur*
(`isir`), *ölçemediğine ölçemiyorum de* (`?` kolu), *beyan et ya da kır*. Bu üçü,
gördüğüm çoğu "lint" aracından daha olgun bir epistemoloji. Bağımlılık sıfır,
taşınabilirlik yüksek, denetim izi düz metin. Bunları söküp atmak sistemi kötüleştirir.

**Hak etmeyen kısım — üç tane.**

1. **`hafiza.py` tek dosya ve artık okunamıyor.** 4 394 satırın büyük kısmı *koda değil,
   koda iliştirilmiş denetim tarihine* ait. Örnek: `kilit_al` 52 satır, bunun 30'u
   yorum; `zincir_dogrula` 135 satır, yarısı geçmiş bulgu anlatısı. Bu, ilk okumada
   müthiş; altıncı ayda **düşman**: B4-1 tam da 52 satırlık bir işlevin içindeki tek
   satırlık sıralamaydı ve 30 satırlık gerekçe onu **gizledi**. Öneri: gerekçeler
   `references/denetim-yaniti.md`'ye taşınsın, kodda yalnız `# B-5/Y-4′ → bkz.
   denetim-yaniti#Y-4prime` biçiminde çapa kalsın. Kod %35–40 kısalır, tarih kaybolmaz.
2. **`_kapi_govde` 724 satırlık tek bir işlev.** 16 kapı aynı gövdede, ortak `F/N/O`
   listelerine yazıyor, sırası anlamlı. Sonuç ölçüldü: bir kapının çökmesi diğerlerini
   götürüyor (B4-2), bir kapı hem `?` hem `[H1]` üretebiliyor (B4-8). Doğru soyutlama
   **zaten kodun içinde ama yarım**: `kapi_yalit`. Her kapı `def h1(ctx) -> [Bulgu]`
   olmalı, `cmd_kapi` hepsini tek tek `kapi_yalit` ile koşmalı. O zaman "bir kapı
   ölçülemedi" tek bir yerde, tek bir kuralla ele alınır ve B4-2 **yapısal olarak**
   imkânsızlaşır. On iki turluk yama katmanının gizlediği soyutlama budur.
3. **`isir`'in mutant kataloğu (700+ satır) motorun içinde.** Test verisi ürün kodunda.
   `isir` ayrı bir modül olmalı; `hafiza.py`'nin dağıtılan yüzeyi küçülür.

**Sökülse iyi olur:** hiçbir kapı. **Ama** H14'ün git kolu ile H9 birleştirilebilir
(ikisi de git'e soruyor, ikisi de ayrı `subprocess` koşuyor), ve `--siki`'nin ayrı bir
bayrak olması yerine `.hafizarc`'ta bir politika alanı olması daha tutarlı olurdu
(H15 zaten politikayı ölçüyor).

**Ben olsam neyi baştan yazardım:** kapı katmanını. Kapılar saf işlev olsun, girdi
`ctx`, çıktı `[Bulgu(kapi, duzey, mesaj, care)]`. Raporlama, çıkış kodu ve yalıtım tek
yerde. Bugün bu üçü 724 satıra dağılmış durumda ve A-2/B4-2/B4-8 hep bu dağılımdan
doğdu.

### 3.2 Sözleşme tasarımı

**Bugünkü çıktı insana bakan bir çıktı**, otomasyona konabilir bir arayüz değil. Kanıt:
`kapi` çıktısını makineyle okumanın tek yolu metin ayrıştırmak (`SONUC:` satırı, `·`/`?`
öneki, `[H1]` etiketi). Bir CI'nin "hangi kapı ölçülmedi" sorusuna cevap vermesi için
Türkçe cümle ayrıştırması gerekiyor. **Öneri: `--json` çıktısı.** `{"surum":…,
"hukum":"YESIL_SINIRLI","cikis":0,"kapilar":[{"ad":"H9","durum":"OLCULEMEDI","sebep":…}]}`.
Bu tek ekleme, §3.8'deki uyumluluk sorununu da çözer (kod yerine alan adı sözleşmesi).

**Sözleşme–gerçek ayrışması A-2'den ibaret değil.** Bu turda ölçtüğüm ayrışmalar:

| Belge ne diyor | Kod ne yapıyor | Bulgu |
|---|---|---|
| "3 = … izin yok" | izin hatası → "ARAÇ KUSURU" mesajı | B4-4 |
| "3 = … beklenmeyen iç hata" | `kapi`'de iç hata → rapor **hiç** basılmıyor | B4-2 |
| "gerçek kapı bulgusu VARSA 1" | tip hatasında kırmızı görünmüyor, 3 dönüyor | B4-2 |
| "ne olursa olsun toplanan hüküm basılır" (docstring) | yalnız `SystemExit` için | B4-2 |
| "dışarı yazmak YASAKTIR" | hata izi `cwd`'ye yazılıyor | B4-5 |
| "ENOSPC'te kendi kilidimizi silebiliyoruz" | silinmiyor, kalıcı kilit | B4-1 |
| "300k satır Türkçe ~6 sn" | bu makinede 10.09 sn (kendi testin KALDI diyor) | §3.6 |

Ortak kök: **sözleşme prozada, uygulama kodda, ikisini bağlayan yürütülebilir bir şey
yok.** Çare: çıkış kodu sözleşmesini `t_y42`'nin bir bölümü değil, **SKILL.md'den
üretilen bir tablo** hâline getir ve testi o tablodan koş.

`ISIRDI/KAÇTI/KURULAMADI` sözlüğü **iyi** — üç değerli mantık burada doğru kurulmuş.
Ama `KURULAMADI`/`SINANMADI` ikiliği (kendi uyarın) hâlâ duruyor; tek kelimeye indir.

### 3.3 Eşzamanlılık

**Kilit modeli bütün olarak sağlam değil; iki kusuru var, biri ölümcül.**

- **Kayıt–edinim sırası (B4-1).** `O_EXCL` doğru, `atexit` doğru, sahiplik doğrulaması
  doğru — ama sahiplik **kilit var olduktan sonra** kaydediliyor. Kilit protokollerinde
  değişmez kural: *kaynağı yaratan işlem, yaratma başarılı olduğu anda sorumluluğu
  üstlenir.* Düzeltme tek satır.
- **Granülerlik çok kaba.** Ölçtüm: 8 paralel `not` → **4 başarılı, 4 × exit 2**, dört
  notun içeriği hiç yazılmadı. Oysa `not`'un yaptığı iş, `gunluk/` altına **benzersiz
  adlı yeni bir dosya** yazmak — çakışma yaratmayan bir işlem. `protokol.md` ise tam bu
  deseni öneriyor: *"Alt ajanlar canlı hafızaya doğrudan yazmaz; yalnız `gunluk/` altına
  fragman yazar."* Yani aracın önerdiği çok-ajanlı desen, aracın kendi kilidi yüzünden
  **kayıplı**. `not` global kilidi almamalı (yalnız `--yeni-konu` kolu, KONULAR.md +
  halka yazdığı için almalı). 8 paralel `derle` testinde ise davranış **doğru**:
  1 başarı, 7 × exit 2, sızan kilit 0, kapı yeşil.
- **Yarış penceresi.** Inode kimliği pencereyi daraltıyor, kapatmıyor — bunu zaten
  yazmışsın ve ölçmüşsün (20/20 inode yeniden kullanımı). Katılıyorum ve kapanışın
  ucuz olduğunu ekliyorum: kilit dosyasına `os.urandom(8).hex()` bir jeton yaz,
  bırakırken jetonu karşılaştır. 3 satır, `st_ctime_ns`'e gerek yok, Windows'ta da
  çalışır.
- **Ağ dosya sistemi.** `O_EXCL` NFSv2'de güvenilmez, NFSv3+/SMB'de genelde çalışır ama
  `st_ino` **yeniden bağlamada değişebilir** ve `os.kill(pid,0)` **başka makinedeki**
  pid'i ölçer — yani paylaşılan bir depoda "pid 4242 YAŞIYOR" cümlesi anlamsızdır, hatta
  yanıltıcıdır. Kilit dosyasına **hostname** yazılmalı ve farklı host ise teşhis
  "ölçülemedi" demeli. Bugün "YAŞIYOR, BEKLE" diyor — bu yanlış bir kesinlik.

### 3.4 Hata yönetimi ve kurtarılabilirlik

Son ağın mimarisi doğru (`_guvenli_calistir`, sınırda dallanma, `raise` yok) ve
`Y-1`'in dersi gerçekten öğrenilmiş. **Ama kurtarılabilirlik ölçüldüğünde çöküyor:**

- B4-3: yarıda kesilen `derle` → kalıcı yanlış-kırmızı, araç içi çıkış yok, **verilen
  tavsiye yanlış**. Bu, "bir kullanıcı bozuk durumdan çıkabiliyor mu" sorusunun ölçülmüş
  cevabıdır: **bu pencerede hayır.**
- B4-1: kalıcı kilit → aracın kendi teşhisi "başka bir işlem sürüyor" diyor, oysa yok.
- Genel eksik: **hiçbir yazma atomik değil.** `yaz()` doğrudan hedefe yazıyor. Doğrusu
  `tempfile` + `os.replace` (aynı dizinde, POSIX'te atomik, Windows'ta da `os.replace`
  atomik). Bu tek değişiklik B4-3'ün sınıfını (yarım dosya) **ve** kısmi defter
  yazımlarını birlikte kapatır. Ayrıca canlı yazımı ile beyan yazımı **aynı işlem
  birimi** olmalı: önce canlıyı geçici dosyaya yaz, sonra defterleri yaz, en son
  `os.replace`. Bugün sıra tam tersi.
- **Fail-closed kararı (`.hafizarc` var + `_CIPA.json` yok → yazma kapalı) savunulabilir**
  — ama "kurtarma komutu tarif etmiyorum" duruşu **fazla katı**. Mesaj bir kurtarma
  komutu tarif etmesin, ama **durumu ölçen** bir komut tarif edebilir:
  `hafiza.py tani` (salt okuma; "şu dosya yok, şu var, git'te şu commit'te vardı").
  Kaçamak kolaylaştırmaz, kullanıcıyı köşeden çıkarır. Bugün kullanıcı köşede.

### 3.5 Taşınabilirlik

**Yalnız Linux'ta ölçüldü** iddiasını geri çekmen doğruydu. Windows'ta somut olarak ne
kırılır (kod okuyarak; **ölçmedim, ölçemedim**):

| Varsayım | Windows'ta |
|---|---|
| `os.kill(pid, 0)` | `AttributeError`/`OSError` → `_surec_yasiyor` `None` döner (kod bunu **doğru** ele almış) ✔ |
| `st_ino` | Python `os.stat` Windows'ta `st_ino` **verir** (NTFS file id), ama FAT/exFAT ve bazı ağ sürücülerinde 0 → sahiplik kontrolü sessizce etkisizleşir |
| `st_nlink` | NTFS'te doğru, exFAT/FAT'te hep 1 → **H-LINK kapısı sessizce kör olur** ("hardlink yok" der, ölçmemiştir) |
| `os.remove` açık dosyada | Windows'ta `PermissionError` → başka bir süreç `.kilit`i açık tutuyorsa `kilit_birak` sessizce yutar (`except OSError: pass`) → kilit sızar |
| SIGPIPE | Windows'ta yok; `BrokenPipeError` yerine `OSError(EINVAL/EPIPE)` gelebilir → sarmalayıcı `errno`ya bakıyor, çoğunlukla tutar ✔ |
| `os.sep == "\\"` | `cli_yol_coz` bunu doğru ele almış ✔; ama `kok_disina_mi` sürücü harfi farkını (`C:` vs `D:`) `realpath` ile çözüyor — UNC yollarında (`\\sunucu\pay`) `startswith(k + os.sep)` **yanlış negatif** verebilir |
| BOM | B4-9 — ölçtüm, kırılıyor |
| CRLF | Okuma tarafı doğru (universal newlines), ama `derle` dosyayı **sessizce LF'e çeviriyor** (ölçtüm: 49 LF, 0 CRLF) → `core.autocrlf` kapalı bir Windows checkout'unda her `derle` tüm dosyayı diff yapar |

**Sessiz varsayımlar** (en tehlikelisi): `st_nlink`/`st_ino`'nun her dosya sisteminde
anlamlı olduğu. Her ikisi de **ölçülemediğinde `?` demeli**, bugün "temiz" diyor. Bu,
aracın kendi ilkesinin ihlali.

### 3.6 Test kalitesi ve bakım

**İyi olan:** sabotaj disiplini gerçek ve işliyor — kendi kurduğum 10 sabotajdan 8'i
doğru mutantı öldürdü. Bu, çoğu projede hiç olmayan bir şey.

**Bakılabilirlik: sınırda.** `t_y42.py` 1 590 satır, 58 senaryo, hepsi tek dosyada,
paylaşılan `yeni()`/`kos()` yardımcılarıyla. Altı ay sonra bir senaryonun neyi ölçtüğünü
anlamak için 40 satır okumak gerekiyor. Süre: bende `t_y42` ~13 dk, `isir` 6.8 sn.
13 dakika **kabul edilebilir ama tehlikeli**: bu süre insanları "koşmadan commit"e iter.
Bölünmeli — hızlı çekirdek (~90 sn) + gecelik tam koşum.

**Kırılgan (flaky) senaryo: var, bir tane, ve ciddi.** `B-6` çıplak duvar saati eşiği
(`< 8 sn`) kullanıyor. Bende:

```
KALDI  B-6  300k satirlik canlida kapi < 8 sn | ascii 8.74 sn (tam=True) · turkce 10.09 sn (tam=True)
SONUC: 56 gecti · 1 kaldi · 1 olculemedi (toplam 58)
```

Beyanın **57 geçti · 0 kaldı**. Yani `t_y42`'nin sonucu **makineye bağlı** ve beyan
edilen sayı yeniden üretilemiyor. Bu bir kod kusuru olmayabilir (makinem seninkinden
yavaş olabilir; saf-Python referansım: 6M döngü 0.61 sn) — ama **test kusuru**: bir kapı
testi kalibrasyonsuz mutlak süreye bağlanamaz. Doğrusu: aynı koşumda bir referans işi
ölç, eşiği ona oranla koy; ya da eşiği aşınca `KALDI` değil `ÖLÇÜLEMEDİ (makine yavaş)`
de. Aracın kendi doktrini de bunu söylüyor.

**Sabotaj ölçeklenmiyor:** elle yapılıyor ve yalnız yeni testlere uygulanmış. Ölçeklenmesi
zor değil: `fail()` çağrılarını bir kimlikle işaretle, kimliği ortam değişkeniyle sustur,
`isir`'ı N kez koş. Ben bunu 10 sabotaj için 6 dakikada kurdum; tam katalog bir gecelik
işidir ve **kapsam envanterini otomatik üretir**.

**Ölçüm–iddia bağının en zayıf yeri:** koşucusu pakette olmayan dört ölçüm (§3.9'da
yargım var).

### 3.7 Gözlemlenebilirlik ve kullanıcı deneyimi

**İnsan için:** `kapi` çıktısı gerçekten 10 saniyede okunuyor. `·` / `?` / `[Hx]` üçlüsü
iyi bir görsel dilbilgisi. `SONUC: YESIL (SINIRLI)` cümlesi — nadir görülen bir dürüstlük.

**Ajan (LLM) için: kısmen.** Bir ajan çıktıdan doğru sonucu **çoğunlukla** çıkarır, ama
üç yerde yanılır: (i) `KURULAMADI`/`SINANMADI` ikiliği, (ii) exit 3'ün iki farklı anlamı
(B4-2/B4-4), (iii) `?` satırlarının çıkış koduna hiç yansımaması. `--json` bunların
üçünü de bitirir.

**Mesajlar eylem tarif ediyor mu?** Çoğu evet, ve bazıları örnek niteliğinde
(`_kilit_tanisi` üç ayrı duruma üç ayrı çare veriyor — çok iyi). Ama **yanlış çare veren
üç yer ölçtüm**: B4-3 (`emekli` öner, durumu kötüleştirir), B4-9 (`sürüm kontrolünden
geri al`, doğrusu BOM'suz kaydet), B4-4 (`Tam iz: …txt`, doğrusu `chmod`). Bir çare
yanlışsa, çaresizlikten kötüdür: kullanıcı onu **uygular**.

### 3.8 Geriye dönük uyumluluk

v2.4.1 çıkış kodu semantiğini **kırıcı** biçimde değiştirdi: eskiden 1 dönen haller artık
3, eskiden 2 dönen haller artık 3. Kurulu bir projede `kapi || dur` etkilenmez
(ikisi de sıfır dışı), ama `if [ $? -eq 1 ]` yazan bir sarmalayıcı **sessizce** kırmızıyı
kaçırır. Sürüm `2.4.0 → 2.4.1` — semver'e göre bu bir **yama** sürümü; olması gereken
`2.5.0` (hatta arayüz sözleşmesini ciddiye alıyorsan `3.0.0`).

Göç yolu yok: `SKILL.md` yeni sözleşmeyi anlatıyor ama "v2.4.0'dan geliyorsanız şunu
değiştirin" demiyor, `kapi` de eski davranışa dönecek bir bayrak sunmuyor. **Öneri:**
(a) sürümü `2.5.0` yap, (b) `SKILL.md`'ye 5 satırlık bir "göç" kutusu ekle, (c) `--json`
gelirse çıkış kodu bağımlılığı zaten azalır.

---

## 4. KAPSAM ENVANTERİ — 36 mutant + 58 senaryo neyi ölçmüyor

Her sınıf için önerilen mutantı da yazıyorum.

| # | Ölçülmeyen sınıf | Önerilen mutant / senaryo |
|---|---|---|
| 1 | **İzin/salt-okunur (EACCES/EPERM/EROFS)** — B4-4. Y-1 var ama tek ölçütü "ham traceback yok" ve root'ta hiç koşmuyor | `M-IZIN`: mutant kopyada `arsiv/hafiza`, `gunluk/`, canlı dosya sırayla `chmod 0555/0444`; her yazma komutu için **(a)** ham traceback yok **(b)** mesaj "ARAÇ KUSURU" **değil** **(c)** yola ve `chmod`'a işaret ediyor. Root'ta koşulamazsa `ÖLÇÜLEMEDİ` de — ama CI'da `unshare -r` ile ölçülebilir |
| 2 | **Yarıda kesilen yazma / atomiklik** — B4-3 | `M-YARIM`: `yaz()`'ı N'inci çağrıda `OSError` atacak şekilde sar (ortam değişkeniyle), `derle` koş, sonra **düzelt ve yeniden koş**; ölçüt: `kapi` YEŞİL'e dönmeli. Bugün dönmüyor |
| 3 | **Defter alan TİPİ (SystemExit olmayan istisna)** — B4-2 | `M-TIP`: `_ZINCIR[i].halka` sırayla `int/list/dict` yapılır; ölçüt: `kapi` **rapor basıyor** ve `[H0]` bulgusu veriyor, exit 1 |
| 4 | **`kapi`'nin kısmi hüküm sözü** | `M-KAPIYARIM`: kapı gövdesinin ortasında yapay `RuntimeError`; ölçüt: o ana kadarki `[Hx]` satırları **basılmış** olmalı |
| 5 | **Kök dışına yazma: hata izi dosyası** — B4-5 | `M-IZDOSYA`: `cwd` proje dışında, `kapi` çökertilir; ölçüt: proje dışında yeni dosya **oluşmamalı** |
| 6 | **H8 blok sınırı (son işaretinin kuyruğu)** — B4-6 | `M-H8c`: `--son` işaretinden **sonraki** metin değiştirilir; ölçüt: `[H8]` ısırmalı |
| 7 | **`devral`'ın yanlış-blok yolu** — B4-7 | `M-DEVRALBLOK`: `vendor/x/.kilit` (bayat) konur; ölçüt: meşru `devral` **geçmeli** ya da açıkça bir zorlama yolu göstermeli |
| 8 | **`onceki_kurulum_izleri`'nin AĞAÇ taraması** (bkz. §5, S7) | `M-DEVIR2`: proje **hiç `derle` görmemiş** olsun (canlıda `kaynak=` yok), `.hafizarc` + hafıza dizini silinsin, ağaçta yalnız `HAFIZA_01.md` kalsın; ölçüt: `devral` izi bulmalı |
| 9 | **`devral`'ın kendi `kilit_al`'ı** (bkz. §5, S3) | `M-KILITK2`: ağaç taraması sabote edilmiş sürümde iki eşzamanlı `devral`; ölçüt: ikincisi durmalı |
| 10 | **Kodlama: BOM / CRLF / UTF-16** — B4-9 | `M-BOM`: canlı dosya `utf-8-sig` ile yeniden kaydedilir; ölçüt: `KAYIP` **değil**, "BOM tespit edildi" |
| 11 | **Windows / macOS** — hiç | En azından `st_ino == 0` ve `st_nlink == 1` zorlandığında H-LINK ve kilit sahipliğinin `?` demesi ölçülmeli |
| 12 | **Kilit TOCTOU** (`agactaki_kilitler` → `kilit_al` arası) | `M-KILITYARIS`: taramadan sonra, `kilit_al`'dan önce dışarıdan kilit yaratılır |
| 13 | **Zincir ölçeği** | `M-ZINCIR10K`: 10 000 halkalı zincirde `kapi` süresi ve bellek; bugün hiç ölçülmüyor ve zincir sıkıştırmasız |
| 14 | **Saat / DST / yerel saat** | `M-DST`: DST geçiş gününde `H12`/`H14`/halka `t` karşılaştırmaları |
| 15 | **H9 mutantı** (senin bildiğin) | Mutant kopyaya `.git` alınabilir (yalnız `git init` + tek commit) — "alınmıyor" bir tercih, imkânsızlık değil |
| 16 | **`not`'un kilit granülerliği** (§3.3) | `M-NOTPARALEL`: 8 eşzamanlı `not`; ölçüt: 8 fragmanın 8'i de yazılmalı. Bugün 4'ü yazılıyor |

---

## 5. TEST DENETİMİ — sabotajı nereye uyguladım, hangisi sahte ısırıyor

`hafiza.py`'nin 10 ayrı korumasını tek tek devre dışı bırakıp (`if False` / gövde boşaltma)
`isir`'ı yeniden koştum. Temel koşumda ilgili yedi mutantın hepsi `ISIRDI` diyor.

```
S1  kur'un kilit_al'i kaldirildi              M-KILITK=KACTI    ✔ sinifini olcuyor
S2  devral'in AGAC TARAMASI kaldirildi        M-KILITK=KACTI    ✔
S3  devral'in kilit_al'i kaldirildi           M-KILITK=ISIRDI   ✗ ÖLÇMÜYOR (isir exit=0)
S4  bos zincir sarti kaldirildi               M-AKLAMA=KACTI    ✔
S5  zincir_dogrula bos-zincir bulgusu kalktı  M-H0d=KACTI       ✔
S6  onceki_kurulum_izleri: CANLI iz okunmuyor M-DEVIR=KACTI     ✔
S7  onceki_kurulum_izleri: AGAC taramasi yok  M-DEVIR=ISIRDI    ✗ ÖLÇMÜYOR (isir exit=0)
S8  halka ZAMAN denetimi kaldirildi           M-H0t=KACTI       ✔
S9  cli_yol_coz kacis reddi kaldirildi        M-KACIS=KACTI     ✔
S10 kilit_birak SAHIPLIK dogrulamasi kalktı   M-KILIT=KACTI     ✔
```

**Sahte/eksik ısıran üç test:**

1. **`M-DEVIR` (S7) — §2.2'nin BAŞLIK mekanizmasını ölçmüyor.** `onceki_kurulum_izleri`'nin
   **tüm ağacı tarayan** kolu tamamen kaldırıldığında mutant hâlâ `ISIRDI` diyor ve
   `isir` **exit 0** veriyor. Yani M-DEVIR yalnız canlı hafızadaki `kaynak="…/gunluk/…"`
   izini ölçüyor — ki o iz **ancak proje en az bir kez `derle` görmüşse** var (taze
   projede M-DEVIR'in `KURULAMADI` demesinin sebebi de bu). Sonuç: *"iz TÜM AĞAÇTA
   aranır"* vaadinin **ısıran testi yok**; yarın o döngü kaldırılsa `isir` fark etmez.
2. **`M-KILITK` (S3) — A-1 düzeltmesinin üçte birini ölçmüyor.** `devral`'ın kendi
   `kilit_al(y)` çağrısı kaldırıldığında mutant `ISIRDI` diyor, `isir` exit 0. Mutant
   `kur`'un kilidini (S1) ve ağaç taramasını (S2) ölçüyor; `devral`'ın kilidi ölçüsüz.
3. **`t_y42` `Y-4` "pid'siz kilit KALICI kilit üretmiyor" — SAHTE.** Test kilit
   dosyasını **elle** `yazd(kp, "")` ile yaratıyor, sonra **kendisi** `os.remove(kp)`
   yapıp `muhur`un çalıştığını doğruluyor. Yani ölçtüğü şey (a) teşhis metninde "sil"
   geçmesi, (b) kilit **elle silindikten sonra** aracın çalışması. İddia edilen davranışı
   — *"`kilit_al`'ın O_EXCL ile açtığı, pid yazılamamış kilidi `kilit_birak` siler"* —
   hiç koşmuyor. Kanıt: **B4-1 bu testin altından geçti.**

**Ayrıca eksik:** `t_a2` (çıkış kodu sözleşmesi) kesilmenin yalnız `SystemExit` kolunu
ölçüyor; B4-2'nin kolunu (SystemExit olmayan istisna) hiç görmüyor — dolayısıyla "dördü
de senaryoyla ölçülü" ifadesi fazla geniş.

**Yeniden üretilebilirlik.** Beyan edilen sayılar:

| Ölçüm | Beyan | Bende |
|---|---|---|
| `isir` (taze proje) | 34/34 + 2 KURULAMADI, exit 2 | **aynı** ✔ |
| `isir` (derle sonrası) | 36/36, exit 0 | **aynı** ✔ |
| `t_y3.py` | 20/20, exit 0 | **aynı** ✔ |
| `t_y42.py` | 57 geçti · 0 kaldı · 1 ölçülemedi | **56 geçti · 1 KALDI · 1 ölçülemedi** ✗ (B-6) |
| `hafiza.py` SHA256 | `7388…F300` | **aynı** ✔ (paketteki kopya da) |
| Satır sayısı | 4 394 | **aynı** ✔ |

**Salt-okunur senaryosunun sonucu (sorduğun).** Ben de root'um, o yüzden `t_y42`'nin Y-1
senaryosu bende de `ÖLÇÜLEMEDİ` dedi. Ayrı bir kullanıcı (`uid=1001`) açıp sınıfı elle
ölçtüm: **ham traceback yok** (Y-1'in ölçütü geçiyor), **ama** 9 senaryonun 6'sında hüküm
"ARAÇ KUSURU" (B4-4) ve bir senaryoda kalıcı yanlış-kırmızı (B4-3). Yani senaryo, geçse
bile sınıfın **yalnız en küçük parçasını** ölçüyor.

---

## 6. DOKUZ BİLİNÇLİ AÇIĞA DAİR YARGIM

**1. "Yeniden çıpalama engellenemez, yalnız görünür kılınır."**
**Katılıyorum — bu doğru duruş, kendini kandırmak değil.** Dosya tabanlı bir düzende
yazma erişimi olan bir aktöre karşı bütünlük garantisi vermek matematiksel olarak
imkânsız; üç denemende de bunu ölçtün ve dördüncüde doğru sonucu çıkardın. Yazılım
güvenliğinde bunun adı var: *tamper-evidence*, *tamper-proof* değil. **İki şartla:**
(a) `SKILL.md` bunu "aklama mümkündür ama sessiz değildir" diye zaten yazıyor — bu cümle
korunmalı ve zayıflatılmamalı; (b) ama §5, S7'de ölçtüğüm gibi bu mekanizmanın **ısıran
testi yok**. Duruş savunulabilir, **kanıtı eksik**. Kanıtı olmayan bir duruş, bir sonraki
turda sessizce çürür.

**2. "Zincir anahtarsızdır; mtime dedektörü işaret eder, hüküm vermez."**
**Doğru denge.** O-2'de mtime'ı FAIL'den ISARET'e indirmen bu turun en olgun kararı:
klon/zip/senkron yanlış-pozitifini ölçüp geri adım attın. Anahtarlı bir zincir (HMAC)
anahtarı nereye koyacağın sorusunu doğurur ve depo içinde bir anahtar hiçbir şey çözmez —
gerçek çözüm depo-dışı tarih (git), sen de bunu yazmışsın. **Ekleme:** `H9` zaten git'i
ölçüyor; zincirin son halkasının SHA'sını **commit mesajına** yazmayı öneren bir satır
(`kapilar.md`'de) bu boşluğu ücretsiz kapatır — git reflog depo-dışı sayılmasa da
uzak depo öyledir.

**3. "Baseline satırını düzeltmenin araç-destekli yolu yok."**
**Katılmıyorum — artık katı bırakmak maliyetli.** Gerekçen ("otomatik onar, kapının
engellediği şeyi kolaylaştırır") 1. turda geçerliydi; ama o zamandan beri `_DUZELTMELER.json`
**beyanlı** bir düzeltme mekanizması olarak zaten var ve H1 onu doğruluyor (sahte
düzeltme kaynağı yakalanıyor). Yani mekanizma mevcut, yalnız **CLI'sı yok**. Öneri:
`hafiza.py duzelt --satir N --yeni "…" --gerekce "…"` — tam olarak elle yazılanı yazsın,
fazlasını değil. Bu bir kaçamak değil; bugün kullanıcıyı JSON'u elle düzenlemeye itiyorsun
ve **elle düzenleme tam da riskli olan şey**.

**4. "`politika_gerekce` gerçek bir kaçış deliği; gizlenemez ama kullanılabilir."**
**Katılıyorum, tasarım doğru** — ama ölçtüğüm bir eksik var: gevşetilmiş bir kapı `kapi`
çıktısında `?` ile görünüyor ve **çıkış kodu 0**. Yani gerekçe "gizlenemez" ama
**otomasyon tarafından görülemez**. `--json` (§3.2) bunu çözer; ya da `--kapsam-zorunlu`
bayrağı `?` varsa 3 döndürsün.

**5. "`.hafizarc` var + `_CIPA.json` yok → yazma kapalı, araç içi kurtarma yok."**
**Fail-closed kararına katılıyorum, "araç içi hiçbir şey yok" kısmına katılmıyorum.**
§3.4'te yazdım: *kurtarma* komutu tarif etme, ama *tanı* komutu tarif et. Bugün
kullanıcının elinde yalnız "bu bir VERİ KAYBIDIR" cümlesi var ve git'siz bir projede bu
cümle çıkışsız. Salt-okuma bir `tani` komutu kaçamak üretmez.

**6. "H9'un otomatik mutantı yok."**
**Kabul edilebilir ama gereksiz.** Mutant kopyaya `.git` almamanın gerekçesi maliyet;
oysa `git init -q && git add -A && git commit -m x` mutant başına ~0.1 sn (kendi
ölçümün: 2 000 dosyalı depoda 0.14 sn). H9 dört ayrı `subprocess` koşan, en çok dış
bağımlılığı olan kapı — mutantsız bırakılacak **son** kapı olmalıydı.

**7. "Taze depoda defterler `git add` edilmemişse H9 ÖLÇÜLEMEDİ desin."**
**Katılıyorum, seçim doğru.** Kırmızı yapmak her yeni projeyi ilk dakikasında durdururdu
ve bu tam da E-4'te (devral'da kırmızı sel) öğrendiğin dersin tekrarı olurdu. **Ama**
`?` satırının çıkış koduna hiç yansımaması (madde 8) bu seçimin bedelini görünmez
kılıyor; ikisi birlikte düzeltilmeli.

**8. "`kapi` kapsam boşluğunda exit 0 verir; `kapi && dagit` eksik kapsamda dağıtır."**
**Çizgi doğru yerde DEĞİL — ama senin düşündüğün yerde de değil.** 3'e çevirmek yanlış
olurdu (haklısın: her yeni proje ilk dakikada durur). Doğru çözüm **üçüncü bir çıkış
değil, ikinci bir sözleşme**: kapsamı çıkış koduna değil, **makine okunur çıktıya**
koy (`--json`), ve isteyen CI'ya `--kapsam-zorunlu` bayrağını ver. Bugünkü hâlin gerçek
sorunu `kapi && dagit`'in dağıtım yapması değil — **kullanıcının bunu ancak Türkçe bir
cümleyi okuyarak öğrenebilmesi.** Bir kapı aracının en kritik ayrımı, çıktısının en az
ayrıştırılabilir yerinde duruyor.

**9. "Kilit inode kimliği yarışı daraltır, kapatmaz (20/20 yeniden kullanım)."**
**Ölçümün doğru, sonucun eksik.** Kabul edilebilir **değil**, çünkü kapatması çok ucuz:
kilit dosyasına 8 baytlık rastgele bir jeton yaz, bırakırken jetonu karşılaştır (3 satır,
`st_ctime_ns`'e gerek yok, Windows'ta da çalışır). "Bu turda yapmadım" savunulabilir bir
sıralama kararıydı; ama B4-1 aynı işlevin **başka** bir kusurunu ortaya çıkardı — ikisi
birlikte düzeltilmeli, çünkü `kilit_al`/`kilit_birak` zaten açılacak.

**Ve koşucusu olmayan dört ölçüm — hangi ağırlığı vermeliyim?**
Sorduğun için açık cevap: **sıfır kanıt ağırlığı, pozitif dürüstlük ağırlığı.**
Doğrulanamayan bir sayı, denetim raporunda **bulgu da değildir, kanıt da**; onu "beyan"
diye işaretlemen doğru ve bu işaretleme senin lehine bir davranış kaydıdır — ama sayının
kendisi karara giremez. Somut öneri: bu dört ölçümü rapordan **çıkarma**, ama şu iki
sınıfa ayır: (a) *ucuz ve paketlenebilir* — "kayıpsızlık 50×" ve "normal hafta 11 adım"
20'şer satırlık senaryolar, `t_y42`'ye eklenmeli, bu turda eklenmemesi için sebep yok;
(b) *pahalı ve paketlenemez* — "2 330 senaryo traceback avı" ve "2 000 dosyalı depo" bir
**fuzzing/benchmark** işidir, `t_y42`'ye değil ayrı bir `bench/` klasörüne ait ve orada
kalabilir. Yani cevabım: dördünden ikisini bir sonraki turda **koşucuya çevir**, kalan
ikisini "ölçüm değil, geliştirici notu" olarak etiketle.

---

## 7. KIRAMADIKLARIM

Bu bölüm bulgular kadar önemli — neyin gerçekten sınandığını gösteriyor.

1. **`basliksal()` hızlı yolu — kıramadım.** Senin 30 000 rastgele dizeni yeterli
   bulmadım; bağımsız bir referans uygulama yazıp **tüm Unicode kod noktalarını**
   (1 112 064 kod noktası × 3 biçim = **3 336 192 dize**) taradım.
   Sonuç: **0 fark.** Eşdeğerlik iddian doğru; ASCII kısayolu anlambilimi bozmuyor
   (NFKD saf-ASCII üzerinde birim işlem, birleşen işaretler zaten ASCII dışı).
2. **`kural_desenleri()` önbelleği — kıramadım.** Anahtar `tuple(isaretler)`, türev yalnız
   girdiye bağlı, 32'de temizleniyor; yanlış paylaşım üretecek bir yol bulamadım.
3. **`--siki` — kıramadım.** Taze `kur`'da temiz, 3 tur + `karar` + `emekli` sonrasında
   temiz, ve elle eklenen tek satırı **tek başına** gösteriyor:
   `[H1] 1 satir BEYANSIZ EKLENMIS (--siki)`. B-4′ gerçekten kapanmış.
4. **Eşzamanlı `derle` — kıramadım.** 8 paralel `derle`: 1 × exit 0, 7 × exit 2, kalan
   kilit **0**, kalan fragman **0**, kapı YEŞİL. Kayıp güncelleme üretemedim.
5. **Defter tip karışıklığı sınıfı — büyük ölçüde sağlam.** 210 denemenin **205'i** temiz
   hata verdi; delik tek alanda (B4-2). `defter_liste` şema doğrulaması iş görüyor.
6. **`M-KACIS` / `cli_yol_coz` — kıramadım.** `--hedef=../../../X`, mutlak yol, symlink,
   ara-dizin symlink: hepsi reddedildi, dış dosya bayt-birebir aynı kaldı. Sabotajda
   (S9) doğru şekilde `KAÇTI` diyor.
7. **`M-KILIT` (kilit sahipliği) — kıramadım.** Başkasının kilidini silmeyi başaramadım;
   S10 sabotajı testin gerçekten o kolu ölçtüğünü gösteriyor.
8. **`M-H0d` / `M-AKLAMA` / `M-H0t` — kıramadım.** Silinmiş, 0-baytlık ve zaman-tahrifli
   zincirlerin üçünde de aklama yolu kapalı; S4/S5/S8 sabotajları da bunu doğruluyor.
9. **H8'in ana yolu — kıramadım.** Blok **içindeki** değişiklik yakalanıyor; okunamaz
   dosyayla gizleme denemesi de `[H8] KORUNAN dosya OKUNAMADI` + exit 1 veriyor
   (yani `kapi_yalit`'in `?` koluna kaçmıyor). Yalnız sınır kuyruğu delik (B4-6).
10. **CRLF — kırılmıyor.** Windows satır sonlarında `kapi` doğru ölçüyor (`oku()`
    evrensel satır sonu kullanıyor); yalnız `derle` sessizce LF'e çeviriyor (§3.5 notu).
11. **Paket bütünlüğü — doğrulandı.** `.skill` içindeki `scripts/hafiza.py`'nin SHA256'sı
    beyanla ve klasördeki dosyayla birebir aynı.

---

## 8. DÜZELTME SIRASI

Sıra, "en çok zarar / en az değişiklik" oranına göre.

| Sıra | Bulgu | Neden bu sırada | Tahmini boyut |
|---|---|---|---|
| **1** | **B4-1** kilit sızıntısı | Tek satır; projeyi kalıcı yazmaya kapatan **tek** kusur. Aynı dokunuşta madde 9'un jetonunu da ekle | 1 + 3 satır |
| **2** | **B4-3** yarıda kesilen `derle` | Kurtarılamaz durum üretiyor. Doğru düzeltme sıralama değil **atomiklik**: `yaz()` → geçici dosya + `os.replace`; canlı yazımı beyandan **önce** kesinleşsin | ~20 satır, `yaz()` + `cmd_derle` |
| **3** | **B4-2** `kapi`'nin istisna sınırı | Hüküm kaybı + gerçek kırmızının gizlenmesi. İki parça: (a) `zincir_dogrula`'da `halka`/`onceki` tip doğrulaması, (b) `cmd_kapi`'de `except BaseException` → kısmi rapor + 1/3 kuralı | ~15 satır |
| **4** | **B4-4** izin hatası teşhisi | Tek yeni `except` dalı (ENOSPC'in kardeşi); B4-3'ün mesajını da düzeltir | ~10 satır |
| **5** | **B4-6** H8 sınır kuyruğu | Sessiz geçen gerçek bir tahrif yolu. `re.escape(son) + r"[^\n]*"` + `KORUNDU:` çıktısına korunan aralığı yaz | ~5 satır |
| **6** | **B4-5** kök dışına iz dosyası | İlke ihlali; izi `<kok>/arsiv/hafiza/` altına yaz, yazılamazsa yalnız stderr | ~8 satır |
| **7** | **B4-7** `devral` yanlış-blok | Giriş kapısını tıkıyor. Ya taramayı `hafiza_dizini` adaylarıyla sınırla, ya bayat kilitleri say ama **durdurma**, listele ve `--zorla` iste | ~15 satır |
| **8** | **B4-8** ölçüm hatası → 1 | Sözleşme tutarlılığı; B4-2 ile aynı yerde düzeltilir | ~5 satır |
| **9** | **B4-9 / B4-10 / B4-11** | Kozmetik + performans; birlikte | ~15 satır |
| **10** | **Test borcu** | §4'ün 16 maddesinden en az 1, 2, 3, 6, 8, 9 — çünkü yukarıdaki düzeltmelerin **ısırdığını** ancak bunlar kanıtlar | — |

**Bir sonraki turda beklediğim:** düzeltmelerin kendisi değil, **düzeltmelerin ısırma
kanıtı**. Bu turda ölçtüğüm iki eksik mutant (S3, S7) tam da "düzeltme yapıldı ama
ölçülmedi" sınıfının kalıntısı.

---

## 9. SON SORUNA CEVAP

> *"§3.6'yı üreten yöntem (beyan-gerçek karşılaştırması + düşman belge okuması) senin
> turunda da işe yarar mı, yoksa ben yalnız kendi kör noktalarımın kolay olanlarını mı
> buluyorum?"*

**Yöntem işe yarıyor — ama tek başına kullanınca sistematik olarak aynı yarıyı bulup
öbür yarıyı kaçırıyor.** Bunu tahmin olarak değil, bu turun kendi verisiyle söylüyorum:

- **Beyan-gerçek karşılaştırması** bu turda benim de en verimli aracımdı ve bulgularımın
  yarısını üretti (B4-1, B4-2, B4-4, B4-5, B4-8 — hepsi "belge X diyor, kod Y yapıyor").
  Yani yöntem senin kör noktana özgü değil, gerçekten güçlü. Bunu §3.2'de bir tabloya
  döktüm: **yedi ayrışma** buldum, sen bir tane (A-2) bulmuştun. Fark yöntemde değil,
  **kapsamda**: sen çıkış kodu sözleşmesine baktın, ben belgedeki **her** davranış
  cümlesini tek tek koştum.
- **Kaçırdığın sistematik şey belge değil, ORTAM.** B4-1, B4-3, B4-4 — üçü de yalnız
  konteynerinin **veremediği** koşullarda (root olmayan kullanıcı, dolu disk) ortaya
  çıkıyor. Sen bunu biliyordun ve dürüstçe "ÖLÇEMEDİM" yazdın; ama "ölçemedim" dedikten
  sonra **ölçebilecek bir ortam kurmadın**. `useradd` ve `mount -t tmpfs` toplam iki
  komut. Kör noktan bir düşünce hatası değil, **bir ortam eksiği** — ve bu, belge
  okuyarak asla bulunamaz.
- **Yöntemin kendi sınırı:** düşman belge okuması, kodun **söylediği** ile yaptığını
  karşılaştırır. Kodun hiç söylemediği şeyi (B4-6'nın `.*?` cimriliği, B4-11'in çift
  çağrısı) göremez. Onun için ikinci bir yöntem gerekir ve o da bu turda işe yaradı:
  **korumayı sabote et, testin bunu fark ettiğini gör** — S3 ve S7 böyle çıktı. Sen bu
  yöntemi biliyorsun ve *yeni* testlere uygulamışsın; **eskilere uygulamamışsın.** Asıl
  boşluk orada.

Özetle: yöntem doğru, kapsam dar. Bir sonraki turda önce ortamı çeşitlendir (root
olmayan kullanıcı, dolu disk, salt-okunur bağlama, mümkünse bir Windows koşumu), sonra
sabotajı **36 mutantın tamamına** otomatik uygula. İkisi de bir gecelik iştir ve bu
raporun bulgularının çoğunu senin bulmanı sağlardı.

---

**Karar tekrar: DÜZELT.** Sistem mimari olarak sağlam, doktrini nadiren görülen bir
olgunlukta ve `--siki`, `cli_yol_coz`, zincir aklama savunması, eşzamanlı `derle`, hızlı
yol eşdeğerliği gibi zor kısımlar gerçekten kırılmıyor. Ama üç YÜKSEK bulgunun ikisi
**veri/erişim kaybı**, biri **hüküm kaybı** ve üçü de aracın en çok iddia ettiği yerde:
"kapatamadığımı ölçerim, ölçemediğimi söylerim". Bu üçü kapanınca ve ısırma kanıtları
gelince kararım **KUR** olur.
