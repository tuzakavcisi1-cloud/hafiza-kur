# Bağımsız Denetim — Bulgular ve Kapatılışları (v2.0.0 → v2.4.0)

Bu skill yayımlanmadan önce **bağımsız denetçilere** verildi. Toplam **on iki tur** koşuldu
(üçüncü denetçinin üç turu dâhil yedi tur dış denetçilerle, beş tur kendi düşman
ajanlarımızla — ikisi paketleme doğrulamasından SONRA); her turda düzeltmeler yapıldı ve düzeltmelerin kendisi yeniden
kırılmaya çalışıldı.

Bu belge her turun ne bulduğunu, ne yapıldığını ve kapandığının **nasıl ölçüldüğünü**
kaydeder. Kalıcı ders en altta.

> **Neden bu kadar tur?** Çünkü ilk üç turda aynı hatayı üç kez yaptım: bilinen yüzeyleri
> tek tek sarıp "sınıf kapandı" dedim. Bir sınıf ancak **sınırda** kapanır. Bu belge,
> o dersin kanıt defteridir.

---

## 1. TUR — 13 bulgu (v2.0.0 → v2.1.0)

Denetçi 42 senaryo koştu, iki doğrulayıcı ajanla çapraz teyit yaptı. Kararı: `DÜZELT`.

| # | Bulgu | Ne yapıldı | Kapandığı nasıl ölçüldü |
|---|---|---|---|
| **1** | Baseline-sonrası eklenen içerik H1/H1-KOVA kapsamı dışındaydı; silinince tüm kapılar sessiz geçiyordu | `derle` ve `bloklastir` canlıya ekledikleri her satırı `_YENI_SATIRLAR.txt` **ve** `_KOVA.json/ek_canli`'ya yazar | Senaryo birebir tekrarlandı: blok eklendi → yeşil; silindi → **H1 "2 satır KAYIP" + H1-KOVA "3 satır CANLIDAN KAÇMIŞ"**. Mutant **M-H1b** |
| **2** | Zincir hash'i `tur`/`gerekce`/`t`/`ek` alanlarını kapsamıyordu → denetim izi izsiz tahrif edilebiliyordu | Halka artık kaydın tamamını (yalnız `halka` hariç) hash'ler | Gerekçe "TAHRİF EDİLMİŞ" yapıldı → **"zincir halka KIRIK", exit 1**. Mutant **M-H0b** |
| **3** | `isir`, emoji başlıklı/devralınmış projelerde sahte "KAPI KÖR" veriyordu | Mutantlar sabit başlık aramayı bıraktı; `MutantKurulamadi` ayrı sınıf oldu ve **ayrı raporlanıyor** | Emoji başlıklı devralınmış projede `isir` → **20/20 ISIRDI, 0 sahte KÖR** |
| **4** | H4 aday regex'i ASCII'ydi → Türkçe adlı ölü bağlantılar sessizce atlanıyordu | Regex `\w` (Unicode) oldu, uzantı sınırı 10'a çıktı | `belgeler/müşteri_görüşme_kaydı.md` → yakalanıyor. Mutant **M-H4b** |
| **5** | `cmd_kur` mevcut sistemi kod seviyesinde korumuyordu | `kur` başında v1 izi taraması; bulursa durur ve `devral`'a yönlendirir | v1'li projede `kur` → **"ZATEN bir hafıza sistemi var … Doğru komut: devral"** |
| **6** | Kapanmamış/iç içe blok sayımdan düşüyordu | H10'a blok yapısı kontrolü eklendi | Kapanmamış blok → **"BOZUK BLOK YAPISI"**. Mutant **M-H10b** |
| **7** | H4, aynı adlı dosyayı ağaçta herhangi bir yerde bulunca "taşınmış" deyip geçiyordu | "Taşınmış" hükmü artık **dizin bağlamı** ister | İlgisiz `a/b/c/AYARLAR.md` → **"aynı adlı başka dosya var ama yol tutmuyor"** |
| **8** | H12/H14 gelecek tarihe kördü | Gelecek tarih doğrudan reddediliyor | Tarih `2099-01-01` → **"'Son güncelleme' GELECEKTE — geçersiz"**. Mutant **M-H12b** |
| **9** | H14 `mtime`'a bakıyordu; clone sonrası yanlış kırmızı | git varsa içerik tarihi kullanılıyor | Yanlış-pozitif kaynağı kalktı — **ama yan etkisi 2. turda çıktı (§3.1)** |
| **10** | H13 alt-dizge eşleşmesi yapıyordu (`test ⊂ kontestan`) | Kelime sınırı deseni H13'e taşındı | — |
| **11** | Bozuk `.hafizarc` → ham Python traceback | `json.loads` ve `re.compile` sarıldı | **Yalnız iki vaka kapandı; SINIF 2. turda yeniden açıldı (Y-3)** |
| **12** | Windows'ta `isir`'ın `✓`/`✗` çıktıları cp1254'te yok → `UnicodeEncodeError` | Program başında `stdout`/`stderr` UTF-8'e reconfigure | Windows'ta `-X utf8` **olmadan**, çıktı dosyaya yönlendirilerek koşuldu → **hata yok, 20/20** |
| **13** | Baseline satırını düzeltmenin araç-destekli yolu yok | **Bilinçli açık bırakıldı** — aşağıya bakınız | — |

**Denetimin kendisinin ortaya çıkardığı iki ek kusur** (ikisi de düzeltildi): tarih damgası
satırı bozuluyordu (artık tarih *yerinde* değiştiriliyor); üretilen arşiv-dizini bloğu H1
muhasebesine giriyor ve her derlemede sahte "KAYIP" üretiyordu (artık muhasebe dışı).

---

## 2. TUR — Y-1…Y-11 + §3.1

Denetçi bu kez **düzeltmelerin ürettiği yeni kusurları** aradı ve buldu.

| # | Bulgu | Ne yapıldı |
|---|---|---|
| **Y-1** 🔴 | `bloklastir` geri-alması `_KOVA.json`'u geri almıyordu → **kalıcı kırmızı kilidi** ("geri alındı" der ama almamıştır) | Yedek sözlüğüne `y.kova` eklendi |
| **Y-2** | Türkçe anlamsal kırmızı-çizgi başlıkları (`Değişmeyenler`, `Anayasa`, `Yasaklar`, `Taviz…`) sıkıştırılabiliyordu | `KURAL_EVI_ANAHTARLARI` genişletildi + gövdede işaret arayan anlamsal ağ |
| **Y-3** | Bulgu 11 **sınıf olarak açıktı**: 8 ayrı yüzey hâlâ ham traceback veriyordu | Merkezî `defter_yukle`/`defter_liste`/`jsonl_yukle`/`tamsayi`; `oku()` UTF-8 hatası; `zincir_dogrula` alan kontrolü — **ama bu da yetmedi, 3. turda `main()` sınırına taşındı** |
| **Y-4** | `derle`nin yazdığı `kaynak=` yolu sabitti → `devral`'ın **tam hedef kitlesinde** yanlıştı | Yol `rc["hafiza_dizini"]`'nden türetiliyor |
| **Y-5** | Politika dosyaları zincir yükünde değildi → kapılar sessizce gevşetilebiliyordu | `POLITIKA_DOSYALARI` zincire girdi + yeni **H15** kapısı |
| **Y-6** | `ASLA` varsayılan `kural_isaretleri`'nde yoktu | Eklendi. Mutant **M-H7b** |
| **Y-7** | Aynı-dakika + aynı-konu ikinci fragman, arşivdekini `shutil.move` ile **eziyordu** | `_bos_ad()` hem `gunluk/`'e hem arşive bakıyor |
| **Y-8** | H10 backtick içi blok örneğini gerçek blok sanıyordu | `kod_disi()` — **3. ve 4. turda iki kez daha düzeltildi** |
| **Y-9** | `derle` damga güncellemesi ilk 14 satırla sınırlıydı | Tüm dosya taranıyor (H12 ile tutarlı) |
| **Y-10** | `25.07.2026` (Türkçe yazım) iki tazelik kapısını da ÖLÇEMİYORUM'a düşürüyordu | Ayrıştırıcıya `DD.MM.YYYY` / `DD/MM/YYYY` eklendi |
| **Y-11** | `kademe` ölü yapılandırmaydı | Bayrak ve alan tamamen kaldırıldı |
| **§3.1** | Bulgu 9'un düzeltmesi **yeni bir kör nokta** doğurmuştu: commitlenmemiş çalışma H14'e görünmüyordu | Kirli/temiz ayrımı: `git status --porcelain` + tek toplu `git log` (yan fayda: 2000 dosyada ~5 sn → 0.13 sn) |

**Kendi bulduğumuz iki kusur** (normal hafta simülasyonunda çıktı, denetçinin iki turunda da
çıkmamıştı): (a) `derle` eski bloğu yalnız *tür*den türeyen bölümde arıyordu, H10 ise konu
tekilliğini **tüm dosyada** ölçüyordu → en sıradan kullanım (`--konu=sonraki-adim`,
varsayılan tür) ikinci blok doğuruyor ve kapı kırmızı yanıyordu; (b) Y-5'in `KONULAR.md`'yi
zincire sokması, aracın **kendi meşru komutunu** (`not --yeni-konu`) zincir kırıcı yapıyordu.

---

## 3–7. TURLAR — sınıfların gerçekten kapatılması

Bu turlarda iki bağımsız denetçi paralel koştu: biri **ham traceback / çökme sınıfını**
(2 300+ senaryo), diğeri **mantık ve kapı körlüğünü** avladı.

### Kapatılan sınıflar

**Ham traceback ve çökme.** 32 kanonik senaryo + 2 300 otomatik senaryo. Sırasıyla:
`oku()`'ya düzenli-dosya kontrolü (dizin/FIFO/soket/kırık link — **FIFO süresiz asılıyordu**);
`_json_coz()` ile `RecursionError` ve 4300+ haneli sayı `ValueError`'ı; defter alanlarının
**tip** doğrulaması (`TypeError` kaynağı); `.hafizarc` yol alanlarının içerik doğrulaması;
`yol_on_kontrol()` ile beklenen dizin/dosya tiplerinin sınırda kontrolü; ve nihayet
`main()` çevresinde **son ağ** — hiçbir istisna kullanıcıya ham traceback olarak gitmiyor,
tam iz `hafiza_hata_izi.txt`'ye yazılıyor. Son ölçüm: **2 330 senaryo, 0 ham traceback,
0 son-ağ, 0 asılma.**

**Yalan güvence.** Son ağ önce "Dosyalarına DOKUNULMADI" diyordu; ölçüldü ki 5 senaryoda
**7 dosyaya kadar değişmişti**. Bu ham traceback'ten daha zararlıydı — kullanıcı geri alma
yapmaz. Mesaj artık hiçbir şey vaat etmiyor: *"işlem YARIDA kesildi, dosyaların DEĞİŞMİŞ
OLABİLİR"*.

**Rapor yutulması.** Rapor sonda basıldığı için tek bir bozuk bayt **16 kapının çıktısını
birden** yutuyordu. `cmd_kapi` ikiye ayrıldı: gövde ölçer, sarmalayıcı ne olursa olsun
o ana kadar toplananı basar ve `[KAPI] ÖLÇÜM YARIDA KESİLDİ` bulgusu ekler.

**`derle`nin yıkıcılığı.** "Tüm dosyada ara" düzeltmesinin ilk hâli, kapanmamış bir blok
işaretinden sonraki ilk kapanışa kadar **her şeyi** (`## KIRMIZI ÇİZGİLER` bölümü ve
`PAZARLIKSIZ` kuralları dâhil) arşive taşıyordu — `emekli` aynı işi açıkça reddederken.
Üç katman eklendi: H10'a "blok başlık sınırını aşamaz" kuralı; `derle`nin işe başlamadan
yapı doğrulaması; ve `emekli`nin kalıcı-kural korumasının `derle` sıkıştırmasına da konması.

**Blok sözdiziminin iki farklı tanımı.** `gizli_blok_satirlari` satır başına bakarken
`canli_bloklar`/H10/`derle` satırın herhangi bir yerine bakıyordu; bu ayrışma sessiz
gizlemeye izin veriyordu. Kök çözüm: **blok işareti sütun 0'a çıpalandı** — böylece
girinti eşiği sezgisi de gereksizleşti. Buna karşılık girintili işaretler artık hiçbir
yerde blok sayılmadığı için ayrı bir ölçüm eklendi (`girintili_isaretler`), yoksa
`devral` yolunda sessiz çift blok doğuyordu.

**Proje dışına yazma.** Kırık sembolik link üzerinden `derle`/`muhur` zinciri **proje
dışına yazıyordu ve kapı yeşil kalıyordu** (`os.path.exists()` kırık linkte `False` döner).
Sonra ara-dizin symlink'i, hardlink ve kapsam dışı arşiv hedefleri bulundu. Kapatıldı:
`lexists` + `realpath` tabanlı kaçış kontrolü, tüm defter/arşiv/politika dosyalarını
kapsayan liste, ve hardlink için `(st_dev, st_ino)` sayımı.

**H8 sahte kopya.** Korunan bloğu tahrif edip dosyanın başına bozulmamış bir kopya
koymak H8'i **tamamen atlatıyordu** — projenin en sert vaadi ("kırmızı çizgi dosyası
mühürlüdür") üç satırla çürütülüyordu. İşaret çifti artık tam 1/1 kez geçmek zorunda.
Mutant **M-H8b**, sabotaj testiyle bu sınıfı ölçtüğü doğrulanarak eklendi.

**Eş zamanlı yazma.** İki oturum aynı anda `derle` koşarsa canlı hafızada **kayıp
güncelleme** oluşuyordu (13 denemenin 2'sinde üretildi). `arsiv/hafiza/.kilit` (O_EXCL)
ile tek yazar kilidi eklendi; çıkışta her yoldan bırakılıyor.

### Düzeltmelerin ürettiği ve geri alınan üç hata

Bunları ayrıca yazıyorum, çünkü "düzelttim" demenin ne kadar kolay olduğunu gösteriyorlar:

1. **Halka silme → ters halka → hibrit.** Önce körlemesine son satır siliniyordu (paralel
   oturumun meşru halkasını silebiliyordu). Sonra kimlikle silindi — bu kez halka ortada
   kalmışsa hash bağı **kalıcı** koptu ve `muhur` onaramadı. Sonra hep ters halka atıldı —
   bu kez kullanıcının o andaki *hatalı* durumu mühürlendi ve hatasını düzeltince kırmızı
   yandı. Doğrusu ikisinin birleşimi: halka hâlâ sonuncuysa geri sar, değilse ters halka.
2. **Kural işareti son-eki.** Önce `ASLA` işareti `Aslan Yatirim` satırını kural sayıyordu.
   "Yalnız büyük harf yazımda son-ek serbest" dedim — bu kez Türkçenin en doğal yazımı
   (`…bu pazarlıksızdır.`) **kaçırıldı**, yani koruma deliği açıldı. "İşaret ≥6 harfse
   serbest" dedim — bu kez `YASAKTIR` kaçtı, `zorunlu tutuldu` fazladan korundu. Doğrusu
   üçüncüsü: ekin kendisi **sonlu bir Türkçe çekim eki kümesinden** gelmeli.
3. **Gizli blok hükmü.** Önce her gizli blok satırı FAIL yapıldı — bu, hafıza dosyasının
   kendi biçimini belgelemesini yasakladı. Şimdi ayrım var: konu **çakışması** varsa FAIL
   (tehlikeli), yoksa `ÖLÇÜLEMEDİ` (belge örneği; iş durmaz ama hüküm "kapsam tam değildir"
   der).

---

## 8. TUR — B-1…B-11 (v2.3.0 → v2.4.0)

Üçüncü bir bağımsız denetçi, önceki iki denetçinin raporlarını **okumadan** koştu ve
2 HIGH + 4 MEDIUM + 5 LOW bulgu getirdi. Kararı: `DÜZELT`. Her bulgu önce **bizim
tarafımızdan yeniden üretildi**, sonra kapatıldı; her birine ayrı mutant ya da senaryo
yazıldı.

| # | Bulgu | Ne yapıldı | Kanıt |
|---|---|---|---|
| **B-1** 🔴 | `_ZINCIR.jsonl` 0 bayta indirilince döngü hiç dönmüyor, kapı **hiçbir bulgu üretmiyordu** → zinciri silmek kurcalamaktan güvenliydi | Boş/genesis'siz zincir kendi başına bulgu; "sağlam SAYILMAZ" hükmü | Mutant **M-H0d** + komut sınaması **M-AKLAMA** |
| **B-2/B-3** 🔴 | `emekli --hedef=../../../tmp/x.md` proje **dışına yazıyor**, `korunan --dosya=/etc/passwd` **dışını okuyup hash'liyordu** | Tüm CLI yol argümanları tek kapıdan: `cli_yol_coz()` (NUL reddi, `\` normalizasyonu, `realpath` kök karşılaştırması) | Komut sınaması **M-KACIS** |
| **B-4** 🟠 | `kapi \| head` → ham `BrokenPipeError`; davranış **çıktı boyutuna** bağlıydı | `_KirikBoruyaDayanikliAkis`: kırık boru yazma katmanında yutulur, komut kendi hükmünü verir | `t_y42` `t_g4`, `t_h1`–`t_h3` |
| **B-5/B-9** 🟠 | `kilit_birak` **başkasının** kilidini siliyordu; `.kilit` dizin olduğunda ham traceback | Kilit oluşturulurken inode saklanır; bırakırken inode + pid doğrulanır; bayat kilit **teşhis** edilir, silinmez | Komut sınaması **M-KILIT** |
| **B-6** 🟠 | H7, 300 000 satırda **17 sn** sürüyordu (satır başına normalizasyon + `re.compile`) | `str.maketrans` tablosu + ASCII hızlı yolu + süreç-ömürlü desen önbelleği → **4,1 sn** | 30 000 rastgele dize + tam kod-noktası taraması → **0 fark** |
| **B-7** 🟡 | `isir` taze projede exit 1 (kurulamayan mutant ile kaçan mutant aynı koda katlanıyordu) | Çıkış kodları ayrıldı: 0/1/2/4, çıktıda da yazılıyor | `t_y42` `t_g7` |
| **B-8** 🟡 | `bayatlik_gun` ölçülemediğinde itiraf yoktu | `ÖLÇÜLEMEDİ` hükmü + neden | `t_y42` `t_g8` |
| **B-10** 🟡 | `derle` kapı kırmızıyken bile 0 dönüyordu | Geri alma sonrası exit 1 | `t_y42` `t_g10` |
| **B-11** 🟡 | Halkanın `t` alanı hash'e giriyor ama **denetlenmiyordu** | Gelecek/geriye akan damga ötülür (±2 gün tolerans, tz normalizasyonu) | Mutant **M-H0t** |

### 9.–10. TUR — düzeltmelerin ürettiği kusurlar (kendi düşman ajanlarımız)

Bu iki tur dış denetçiye gitmeden koşuldu ve **23 yeni kusur** çıkardı; 6'sı HIGH,
1'i CRITICAL. Hepsi B-1…B-11 düzeltmelerinin **yan ürünüydü**. En pahalıları:

1. **`os._exit(0)`** (B-4'ün ilk hâli) üç HIGH doğurdu: kırmızı kapı `| head` ile 0
   dönüyordu (sahte yeşil), `derle` iş ortasında 0 dönüyordu (yarım durum "başarı"),
   ve `atexit` atlandığı için kilit sızıyordu. Çözüm: çıkış kodunu değil, **yazma
   katmanını** değiştirmek.
2. **`except OSError: … raise`** (B-4'ün ENOSPC kolu) son ağı deldi: çıplak `raise`
   bir sonraki `except`'e düşmez, tüm `try`dan çıkar. EROFS/EACCES/ELOOP/EIO yeniden
   ham traceback veriyordu. ENOSPC `except BaseException` **içine** alındı.
3. **Aklama tasarımı üç kez çöktü.** `_CIPA.json`'a çıpalamak → `rm _CIPA.json && kur`
   akladı. `.hafizarc`'a çıpalamak → `rm .hafizarc && devral` akladı **ve hata mesajı
   tarifi öğretti**. Sabit yollu yetim kontrolü → üç yoldan atlatıldı **ve** meşru
   v1→v2 geçişini kilitledi. Dördüncü tasarım önlemeyi bıraktı: **gizlenemez kıl.**
4. **ENOSPC pid'siz kilit** projeyi kalıcı olarak yazmaya kapatıyordu; düzeltmesi bir
   yarış açtı; inode saklaması onu kapattı.
5. **Timezone taşıyan `t`** (B-11'in ilk hâli) `TypeError` ile **kapının tamamını**
   düşürüyordu — hiç hüküm çıkmıyordu.
6. **`--siki` ilk kurulumdan itibaren yapısal olarak kırmızıydı**: araç ürettiği
   `<!-- /blok -->`, arşiv iskeleti ve `<!-- emekli -->` satırlarını beyan etmiyordu.
   58 yanlış-pozitifin altında **gerçek bir enjeksiyon** saklanabiliyordu; üstelik
   `fazla` listesi sessizce kırpılıyordu. Artık araç-üretimi satırlar beyan edilir,
   kırpma duyurulur, enjeksiyon **tek bulgu** olarak çıkar.
7. **`korunan` ham kullanıcı yolu saklıyordu** → mutlak yerel yollar sürüm kontrolüne
   sızıyor, proje taşınamaz hâle geliyor, aynı dosya için 4 kayıt oluşuyordu.
8. **O-2 mtime dedektörü haksız suçluyordu** — "git kirli diyor" kanıt değildir
   (defterler `derle` sonrası zaten kirlidir). Sinyale indirildi, hüküm vermiyor.

**İki kendi testimiz yanlış katmanı ölçüyordu** ve sabotaj sınamasıyla yakalandı:
`M-KILIT`in ilk hâli alt süreçte `muhur` koşuyordu — o süreç kilidi hiç almadığı için
sahiplik dalı hiç çalışmadı; `M-H0e` bir kapı mutantıydı ama aklama bir **yazma-tarafı**
davranışıdır. İkisi de yeniden yazıldı. **Yeni bir test, ölçtüğünü iddia ettiği korumayı
`if False` yapınca KAÇTI demiyorsa, o testi yazmamış sayılırsın.**

### 11.–12. TUR — paketleme doğrulamasından SONRA (P-1, A-1, A-2, A-3)

Paket hazırlandıktan ve teslim klasörüne yazıldıktan **sonra** iki iç denetim turu daha
koşuldu (biri beyan-gerçek karşılaştırması, biri düşman belge okuması). Dört kusur daha
çıktı. Sırayı ayrıca yazıyorum, çünkü **bulunuş anı da bir veridir**: bunlar "bitti"
dedikten sonra bulundu.

| # | Bulgu | Ne yapıldı | Kanıt |
|---|---|---|---|
| **A-1** 🔴 | `kur` ve `devral` tek-yazar kilidini **hiç almıyordu**. v2.4 `devral`a canlıya yazan yeni bir yol ekledi (`ÇAPA DEVRİ`) ve o yolu kilit disiplininin dışında bıraktı: başkasının kilidi dururken `devral` exit 0 verip canlıyı değiştiriyordu | İkisi de `kilit_al` alır; `devral` ayrıca **ağaçtaki her** `.kilit`i sayar (kilidini yeni ad alanında aldığı için eskiyi göremiyordu) | Komut sınaması **M-KILITK**, sabotajda KAÇIYOR |
| **A-2** 🔴 | Bu turda belgeye yazdığım çıkış kodu sözleşmesi **kodda yoktu**: `exit 3` yalnız ENOSPC'deydi; ölçüm yarıda kesilince **1** (gerçek kırmızıyla aynı), beklenmeyen iç hata/izin hatası **2** (kullanım hatasıyla aynı) | Kod söze uyduruldu: kesilme ve iç hata → **3**; hem kırmızı hem kesilme varsa **1** | Senaryo `t_a2` (dört hali birden ölçer), sabotajda KALDI |
| **A-3** 🟠 | Kırık boru yalnız **stdout**'ta yutuluyordu; tüketicisi kapanmış stderr'de `not` exit 2 verip fragmanı hiç yazmıyordu. Kendi testlerim göremiyordu (`stderr=DEVNULL`) | `sys.stderr` de sarıldı | Senaryo `t_a3`, sabotajda KALDI |
| **P-1** 🟡 | Commitsiz git deposunda H9 "okunamadı" diye **yanlış teşhis** koyuyordu | Sebep ayrıştırıldı; hüküm değişmedi | Senaryo `t_p1`, sabotajda KALDI |

**Aynı turda düzeltilen üç beyan hatası** (kod değil, dürüstlük):

1. **Performans temeli geri çekildi.** "17.07 sn → 4.13 sn (4,1×)" beyanı aynı makinede
   **yeniden üretilemedi**. Yeniden ölçüm (300k satır, iki koşum): v2.3.0 ASCII ~10,0 sn ·
   Türkçe ~12,1 sn; v2.4.1 ASCII ~3,7 sn · Türkçe ~5,9 sn. Yani hızlanma **2,7× (ASCII) /
   2,0× (Türkçe)**. Eski rakam geri çekildi.
2. **Performans testi kendi lehine kuruluydu.** 300 000 satırın **hepsi ASCII**'ydi —
   yani tam olarak düzeltmenin *eklediği* hızlı yolu ölçüyordu. Bu bir **Türkçe** hafıza
   aracı. Test iki kola bölündü, eşik Türkçe kola göre kondu, ve artık kapının
   **tamamlandığı** da doğrulanıyor (yarıda kesilen ölçüm de hızlı biter).
3. **Darboğaz atfı yanlıştı.** "Asıl darboğaz senin işaret ettiğin desen derleme değil"
   demiştim; iki iyileştirme tek tek geri alınıp ölçüldü: desen önbelleği **2,09 sn**,
   `basliksal` hızlı yolu **1,23 sn** kazandırıyor. Denetçinin teşhisi benimkinden
   **daha güçlüydü**; cümle düzeltildi.

**Ve bir iddia daraltıldı:** "inode saklaması yarışı kapattı" → ölçüldü, aynı dizinde
silinen kilidin inode'u **20/20 yeniden kullanılıyor**. Pencere **daraldı, kapanmadı**.
Bu artık böyle yazılıyor ve denetçiye açık soru olarak bırakıldı.

### Paketleme doğrulamasında çıkan kusur (P-1)

Paketi kurup **sıfırdan** doğrularken, B listesinde olmayan bir kusur çıktı: `git init`
yapılmış ama **henüz commit atılmamış** bir depoda H9 `"git deposu okunamadi"` diyordu.
Depo pekâlâ okunuyordu; yalnızca tarihi boştu (`git log` boş depoda sıfırdan farklı
döner). Yanlış teşhis, kullanıcıyı **olmayan** bir izin/bozulma sorununu aramaya
yollar — ve bu, tam olarak B-8'in ("ölçülemediğini itiraf et") sınıfıdır: itiraf
vardı ama **sebep yanlıştı**.

Düzeltme hükmü değiştirmedi (iki hâl de `ÖLÇÜLEMEDİ` kolunda kalır, kapı yeşil):
yalnız sebep ayrıştırıldı — `git rev-parse --git-dir` başarılıysa "HENÜZ COMMIT YOK",
değilse gerçek `stderr` satırıyla "OKUNAMADI". Senaryo kanıtı `t_p1`, sabotaj
sınamasından geçti (koruma `if False` yapılınca **KALDI**).

> **Açık bırakılan soru (denetçiye):** taze bir depoda defterler henüz `git add`
> edilmemişse H9'un **kırmızı** yanması mı doğru olurdu? Bugün ölçülemedi diyor.
> Kırmızıya çevirmek her yeni projeyi ilk dakikasında durdurur; ölçülemedi demek
> ise "izlenmiyor" hâlini ilk commit'e kadar gizler. Bilinçli olarak **ölçülemedi**
> seçildi ve burada yazıldı.

---

## Açık bırakılan madde (bilinçli)

**Bulgu 13 — baseline satırı düzeltme aracı yok.** Şablondaki bir yazım hatasını düzeltmek
H1 + H1-KOVA'yı kırar ve elle defter cerrahisi gerektirir. Kapatılmadı, çünkü otomatik bir
"baseline düzeltme" komutu tam olarak kapının engellemek için var olduğu şeyi kolaylaştırır.
Bugünkü yol: `_DUZELTMELER.json`'a beyan + `muhur`, ya da `emekli`. **Bunu bilerek katı
bırakıyoruz.**

**H9'un otomatik mutantı yok** (mutant kopyasına `.git` alınmıyor). Elle sınanır. H14'ün
git kolu için **M-H14b** mutant kopyada kendi deposunu kurar.

---

## Son ölçüm (v2.4.1)

| Ölçüm | Sonuç |
|---|---|
| Isırma kanıtı (`isir`) | **36/36 ısırıyor** (`derle` koşulmuş projede) · taze `kur` projesinde 34/34 + 2 KURULAMADI |
| Sabotaj sınaması | 10 yeni sınamanın 10'u da korumasız hâlde **KAÇTI/KALDI** verdi |
| Ham traceback avı | **2 330 senaryo · 0 traceback · 0 çökme · 0 asılma** |
| Senaryo kanıtları (`t_y42.py`) | **57 geçti · 0 kaldı · 1 ölçülemedi** (root olarak koşulduğu için) — toplam 58 |
| Temiz hata kanıtları (`t_y3.py`) | **20/20 temiz hüküm** |
| Kayıpsızlık | 50× aynı konu derlendi → **50/50 satır korundu** |
| Normal hafta simülasyonu | 11 adım · **0 yanlış-pozitif** |
| Performans | 2 000 dosyalı git deposunda `kapi` **0.14 sn** · 300 000 satırda **ASCII ~3,5 sn / TÜRKÇE ~6 sn** (v2.3.0: ~10 / ~12 sn) |
| Bağımsız denetçi kararı | 1. ve 2. denetçi **KUR** · 3. denetçi v2.3.0 için **DÜZELT** → v2.4.1 dördüncü tur denetimini bekliyor |

> **Beyan (v2.4.0):** `hafiza.py` 4 394 satır ·
> SHA256 `738849C086512C7485048C58570EEDCA045E21550EF9BE357197FF577126F300`.
> `t_y3.py` 199 satır · `t_y42.py` 1 590 satır.
> Bu skill **üçüncü denetçinin dördüncü tur onayı gelmeden** "denetimden geçti"
> diye sunulmaz.

---

## Kalıcı ders

Denetim, K-7 dersinin ("testi de sına") **üç kez yarım öğrenildiğini** gösterdi:

1. Mutantların sabit *yol* kullanması düzeltilmişti, sabit *başlık* kullanması düzeltilmemişti.
2. Bilinen traceback yüzeyleri tek tek sarıldı ve "sınıf kapandı" denildi; sekiz yüzey
   daha vardı, sonra otuz iki tane daha.
3. `kod_disi` üç kez düzeltildi; her seferinde "bu sefer tam" sanıldı.

**Kural:** bir sınıf, tek tek yüzeyler sarılarak kapanmaz — **sınırda** kapanır. Traceback
sınıfı `main()`'de kapandı; blok sözdizimi sınıfı tek bir tanıma (sütun 0) çıpalanarak
kapandı; kaçış sınıfı `realpath` tabanlı tek kontrolde kapandı.

**İkinci kural:** bir test aracının kendi varsayımları da envantere girer. Mutant bir şey
"bulamadığında" bu iki farklı şey olabilir — kapı kör, ya da **test kurulamadı**. İkisini
ayırmayan bir rapor, ikisini de yanlış anlatır. Bu yüzden `isir` üç sonuç verir:
`ISIRDI` · `KAÇTI` · `KURULAMADI (test hatası, kapı hükmü değil)`.

**Üçüncü kural — bu turda öğrenildi:** bir düzeltmenin *ürettiği* kusur, kapattığından
daha tehlikeli olabilir. "Dosyalarına DOKUNULMADI" yalanı, kapattığı ham traceback'ten
daha zararlıydı. Her düzeltme için sorulacak soru "kapandı mı" değil, **"ne açtı"**.

**Dördüncü kural — 8.–10. turda öğrenildi:** bazı hamleler **önlenemez**; dosya tabanlı
bir şemada diske tam yetkisi olan biri her zaman yeni bir başlangıç noktası yaratabilir.
Önlemeye üç kez çalışıldı, üçü de ya atlatıldı ya da meşru kullanımı kilitledi. Doğru
hedef **engellemek değil, GİZLENEMEZ KILMAK**tır: iz tüm ağaçta aranır, bulgu çıpanın
içine kalıcı olarak yazılır, silinmesi başka bir kapıyı ötçer.

**Beşinci kural:** bir testin ısırması, **doğru sınıfı** ölçtüğü anlamına gelmez.
Ölçüt: testin ölçtüğünü iddia ettiği korumayı devre dışı bırak; test KAÇTI demiyorsa
komşu bir sınıfı ölçüyordur. Bu turda iki test bu süzgeçte elendi ve yeniden yazıldı.

**Yedinci kural — 11.–12. turda öğrenildi:** bir korumanın **derinliği** ile
**kapsamı** ayrı iki sorudur. B-5'te kilidin sahipliğini iki kez derinleştirdim
(pid → pid+inode) ve kilidi *alan komut kümesini* hiç sormadım; aynı turda o kümenin
dışında kalan yeni bir yazma yolu açtım. Derinleşmek, kapsamın denetlendiği anlamına
gelmez.

**Sekizinci kural:** bir testin girdisi, düzeltmenin **kendi lehine** seçilmiş olabilir.
Performans testinin 300 000 satırı tamamen ASCII'ydi — yani düzeltmenin *eklediği* hızlı
yolu ölçüyordu; oysa bu bir Türkçe hafıza aracı. Test kendi sonucunu üretiyorsa ölçüm
değildir. Aynı sınıf: bir kanalı `DEVNULL`'a atan test o kanaldaki sınıfı ölçemez (A-3).

**Dokuzuncu kural:** **belge de bir arayüzdür ve o da yalan söyleyebilir.** A-2'de
kodun sözleşmesini belgeye yazdım ve kodda kurmadım; belge iki tur boyunca doğru
sanıldı. Yazdığın her sözleşme maddesi için bir senaryo yaz — yoksa madde bir dilek olur.

**Altıncı kural:** mutant sayısı **bağlamsız beyan edilmez**. "36/36 ısırıyor" yalnız
`derle` koşulmuş projede doğrudur; taze `kur` projesinde iki mutantın ön-koşulu yoktur
ve sonuç `34/34 + 2 KURULAMADI`'dır. İkisi de sağlıklıdır — ama hangisinin ölçüldüğü
yazılmadan sayı bir iddiadır, ölçüm değil.
