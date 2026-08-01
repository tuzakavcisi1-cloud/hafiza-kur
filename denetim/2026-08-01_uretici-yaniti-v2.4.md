# Dördüncü Yanıt — `hafiza-kur` v2.3.0 → v2.4.1

**Tarih:** 1 Ağustos 2026
**Motor:** `scripts/hafiza.py` · **4 394 satır** · saf Python stdlib
**SHA256:** `738849C086512C7485048C58570EEDCA045E21550EF9BE357197FF577126F300`
*(v2.3.0 idi: `B92CBAC009CD56DDA14D96B572FD23433F1AD53E8AE26BC13DA4E5440F5D5B8B`)*

---

## 0. Önce dürüst kısım

Senin 11 bulgunu kapattım. **Sonra kendi bağımsız denetçilerimle iki tur daha koştum ve
kapatmalarımın 15 + 8 yeni kusur ürettiğini buldum.** Altısı YÜKSEK, biri KRİTİK'ti.

Yani bu turun asıl hikâyesi "11 bulgu kapatıldı" değil:

> **Düzeltmelerim, kapattıklarından daha ciddi şeyler açtı — ve bunu ancak düzeltmeleri
> ayrıca kırdırınca gördüm.** Senin ikinci raporunda yazdığın soru ("kapandı mı değil,
> ne açtı") bu turda somut olarak dört kez karşılığını buldu.

En utandırıcı örnek: B-4'ün (`isir | head` paniği) düzeltmesi olarak koyduğum
`os._exit(0)`, **KIRMIZI bir kapıyı `| head` ile exit 0 yapıyordu.** Yani senin bulduğun
bir yanlış-pozitifi susturmak için, sistemin en temel doğru-pozitifini sustuktum. Aynı
düzeltme `derle | head`'i "yarım iş = başarı" hâline getirdi. v2.3.0 o senaryoda
**doğruyu söylüyordu**; ben onu yalancı yaptım.

İkinci örnek, bu projenin dördüncü kez tekrarladığı ders: aklama sınıfını **üç kez**
yanlış kapattım (önce `_CIPA.json` çıpası → tek `rm` ile aşıldı; sonra `devral`'a sabit
yollu kontrol → üç yoldan aşıldı **ve meşru v1 devralmasını tümden kilitledi**).

---

## 1. Senin 11 bulgunun durumu

| # | Bulgu | Durum | Kapanış ölçümü |
|---|---|---|---|
| **B-1** 🔴 | 0-bayt `_ZINCIR.jsonl` sahte "sağlam" | **KAPANDI** | Senaryon birebir: `[H0] _ZINCIR.jsonl BOS — genesis halkasi yok`, FAIL exit 1; `muhur` artık **duruyor** (aklama yolu kapalı). Mutant `M-H0d`, sabotajda KAÇIYOR |
| **B-2** 🔴 | `emekli --hedef` kök dışına yazıyor | **KAPANDI** | `--hedef=../../../KURBAN.md` → `HATA: --hedef PROJE AGACININ DISINA cikiyor`, dış dosya byte-birebir aynı. Mutant `M-KACIS` |
| **B-3** | `korunan --dosya` kök dışından okuyor | **KAPANDI** | Aynı geçit; `_KORUNAN.json`'a dış yol girmiyor |
| **B-4** | `isir\|head` sahte panik | **KAPANDI — ama ilk düzeltmem yıkıcıydı** | §2.1 |
| **B-5** | `kilit_birak` sahiplik doğrulamıyor | **KAPANDI** | Mutant `M-KILIT` (ilk yazdığım hâli sahte ısırıyordu — §3) |
| **B-6** | Büyük `canli` → `kapi` asılıyor | **KAPANDI** | 300k satır: ASCII **~10,0 → ~3,7 sn**, Türkçe **~12,1 → ~5,9 sn** (§3.6'da eski "17.07 → 4.13" beyanı geri çekildi). İki darboğaz vardı: **senin işaret ettiğin desen derleme (~2,1 sn)** ve satır başına `basliksal()` (~1,2 sn); ikisi de kapatıldı |
| **B-7** | Taze projede `isir` exit 1 | **KAPANDI** | Çıkış kodları ayrıştı: 0 / 1 (kör kapı) / 2 (ölçülemeyen mutant) / 4 (temiz sürüm zaten FAIL) ve çıktıda belgeleniyor |
| **B-8** | `bayatlik_gun` itiraf üretmiyor | **KAPANDI** | `bayatlik_gun` **ve** `hafiza_gecikme_gun` H15 beyan kapısında |
| **B-9** | `.kilit` dizinken çift mesaj | **KAPANDI** | Tek hüküm: `KILIT YOLU BIR DIZIN` |
| **B-10** | `derle`, `gunluk/` yoksa exit 0 | **KAPANDI** | `BOZUK KURULUM` + exit≠0; boş `gunluk/` hâlâ ayrı hüküm |
| **B-11** | Halka `t` denetlenmiyor | **KAPANDI** | Gelecek + geriye akış yakalanıyor (hash yenilense de). Mutant `M-H0t` |

**Kapsam envanterinden kapatılanlar:** boş/truncate zincir · CLI yol kaçışı · performans ·
SIGPIPE · kilit sahipliği + kilit-dizin · halka zaman damgası. **Kapatılmayanlar:**
disk-dolu/torn yazma (kısmen: ENOSPC artık kurtarılabilir hüküm veriyor), izin/salt-okunur
(bu konteynerde root olduğu için **ÖLÇEMEDİM** — senaryo `t_y42`'de var, ortam elverirse
ölçüyor).

---

## 2. Düzeltmelerimin ÜRETTİĞİ kusurlar (asıl bölüm)

### 2.1 — `os._exit(0)`: bir yanlış-pozitifi susturmak için üç doğru-pozitifi sustuktum

| # | Ne oldu | Ölçüm |
|---|---|---|
| Y-2 | **KIRMIZI kapı `\| head` ile exit 0** — üstelik çıktı boyutuna bağlı (küçük raporda 1, 8 KB üstünde 0). `if kapi \| head; then dagit; fi` diyen CI kırmızı kapıda dağıtım yapardı | 120 bulgulu proje: borusuz exit 1, `\| head -5` exit 0 |
| Y-3 | **`derle \| head` yarım işi "başarı" sayıyordu**: arşive yazılmış, canlıya işlenmemiş, zincire halka atılmamış → `[H0] defter MUHURSUZ degismis` → kullanıcı H0'ın tavsiyesiyle `muhur` → tahrif **kalıcı aklandı** | 80 fragmanlı proje, exit 0, `HAFIZA_01.md` 139 B → 1167 B |
| Y-4 | `os._exit` `atexit`'i atlıyordu → **kilit sızıntısı** | `derle\|head` sonrası `.kilit` duruyor |
| Y-1 | `except OSError ... raise` ayrı dalı, **son ağı deldi**: `raise` sonraki dala düşmez, TRY'dan çıkar. `EROFS/EACCES/ELOOP/EIO` → **ham traceback geri geldi**, exit 1 (kapı FAIL ile aynı kod) | Salt-okunur dosya sisteminde `muhur` → tam traceback |

**Düzeltme (v2.4.0):** `os._exit` kaldırıldı. `main()` başında
`sys.stdout = _KirikBoruyaDayanikliAkis(sys.stdout)` — kırık boru **yazma katmanında**
yutulup devnull'a düşülüyor, komut kendi işini bitiriyor ve **kendi hükmünü** veriyor.
ENOSPC artık `except BaseException` dalının **içinde** ele alınıyor; sınırdan `raise` yok.

**Ölçüm:** KIRMIZI kapı `head -1/-3/-5` → hepsi exit 1 (borusuzla aynı) · `derle|head` →
iş tamamlanıyor, kalan fragman 0, kapı YEŞİL, kilit sızıntısı yok · `>/dev/full` → exit 3
+ temiz mesaj · 200k satırlık çıktı + erken kapatılan boru → kapanışta gürültü yok.

### 2.2 — Aklama sınıfını üç kez yanlış kapattım

| Deneme | Ne yaptım | Nasıl kırıldı |
|---|---|---|
| 1 | Çıpayı `_CIPA.json`'a bağladım | `rm _CIPA.json && kur` → her tahrif aklandı, **zincirde kesinti bile yok** |
| 2 | `devral`'a sabit yollu ("arsiv/hafiza", ".../v2") yetim kontrolü | **Üç bypass:** `rm -rf`, `mv`, özel `hafiza_dizini` (hiçbir defter silinmeden). **Ve meşru v1 devralmasını tümden kilitledi** — `kur` "devral kullan" diyor, `devral` "yetim v2" diyor, kapalı döngü |
| **3 (v2.4.0)** | **Kabul:** yazma erişimi olan biri her çıpayı silebilir; bunu dosya tabanlı bir düzende **engellemek mümkün değil**. O yüzden **engellemiyorum — görünmez kılınmasını engelliyorum** | — |

**Bugünkü tasarım:** `onceki_kurulum_izleri(kok, canli_p)` **tüm ağacı** tarar (sabit yol
yok) ve ek olarak canlı hafızadaki blok `kaynak="…/gunluk/…"` alanlarını okur — defterler
silinse bile bu iz kalır. Bulunan her iz (a) DEVİR halkasının `ek` alanına, (b) **canlı
hafızaya kalıcı bir `CAPA DEVRI` bloğu** olarak yazılır, ve (c) bu blok **çıpadan önce**
yazıldığı için snapshot'a girer: silinmesi `[H1] KAYIP` verir. Yani saldırganın izi yok
etmesi için korumaya çalıştığı metnin kendisini bozması gerekir.

`.hafizarc` **dururken** çıpa/zincir silmek hâlâ **engelleniyor** (o gerçekten bozuk bir
durum, kaçamak değil). Meşru v1 devralması yeniden çalışıyor.

**Ölçüm:** `rm -rf hafiza dizini` · `mv hafiza dizini` · `hiçbir defter silinmeden` — üç
kılıkta da iz bulunuyor ve `CAPA DEVRI` hem canlıya hem çıpaya hem zincire yazılıyor.
Mutant **`M-DEVIR`**; sabotajda KAÇIYOR. Meşru v1 devralması: `devral exit=0`, kapı
YEŞİL, v1 dosyalarına dokunulmuyor.

### 2.3 — Diğer sekiz regresyon

| # | Ne açtım | Nasıl kapattım |
|---|---|---|
| Y-4' | ENOSPC, `kilit_al`'ın `O_EXCL` ile açtığı dosyaya pid yazamadan düşerse **kendi kilidimizi bir daha silemiyorduk** → proje kalıcı yazmaya kapalı | `kilit_birak`: pid **yoksa** dosya bizimdir (O_EXCL ile biz açtık), silinir. Yalnız **başka** bir pid varsa dokunulmaz |
| B-7' | O düzeltme, başka sürecin pid'ini henüz yazmadığı kilidi silebiliyordu (mikrosaniyelik pencere) | Kilidin **inode**'u oluşturulurken saklanıyor; bırakırken aynı dosya değilse dokunulmuyor |
| O-1 | Saat dilimli (`+03:00`) halka `t`'si **kapıyı tümden çökertiyordu** (aware vs naive `TypeError`) — zincir anahtarsız olduğu için tek halkayla kapı felce uğratılabilirdi | `fromisoformat(...replace("Z","+00:00"))` + aware ise yerel saate çevir |
| O-2 | mtime dedektörünün "git de KIRLI diyor" teyidi **hiçbir kanıt gücü taşımıyordu** (defterler `derle` sonrası zaten hep kirli) → dosyayı **birebir aynı baytlarla** kaydetmek asılsız tahrif suçlaması üretiyordu | Teyit kaldırıldı; mtime **her zaman** `~` işareti (ÖLÇÜLEMEDİ), asla tek başına FAIL |
| O-5 | `korunan` kullanıcının HAM yolunu deftere yazıyordu → proje taşınınca `[H8] KORUNAN dosya yok`, `_KORUNAN.json`'a yerel mutlak yol sızıyor, aynı dosya için 4 ayrı kayıt | `kok_goreli()` ile kanonik göreli yol; tekilleştirme de kanonik yol üzerinden |
| B-3' | `M-H11` sabit `0009` yazıyordu → **8 ADR'li sıradan bir projede sahte "KAPI KOR" + exit 1** | Numara `max+2`: her zaman gerçek boşluk |
| B-4' | `--siki` **ilk `kur`dan itibaren kırmızıydı** (aracın kendi yazdığı `<!-- /blok -->`, arşiv iskeleti, `<!-- emekli -->` satırları hiç beyan edilmiyordu) → gerçek bir enjeksiyon 58 sahte-pozitifin altında kayboluyordu; ayrıca `fazla` listesi **sessizce kırpılıyordu** | Araç-üretimi satırlar `_YENI_SATIRLAR.txt`'ye beyan ediliyor; `ek_canli` beyanları `fazla`dan düşülüyor; kırpma artık `… +N satır daha` diyor |
| B-6' | `--hedef` ağaç **içinde** canlı dosyanın kendisi olabiliyordu → `_TASINMA.jsonl` "arşive taşındı" diye **yalan** yazıyor, sonraki tüm H1-KOVA muhasebesi o yalana dayanıyor | `--hedef` hafıza dizininde olmalı ve canlı/defter olamaz |

---

## 3. Testlerin kendisinde bulunan iki kusur

Senin "kanıt koşucuları sahte mi" sorunu haklıydı; iki testim **yanlış katmanı ölçüyordu**
ve sabotaj testiyle yakalandı:

- **`M-KILIT` ilk hâli sahte ısırıyordu:** yalnız alt-süreçte `muhur` koşuyordu, o da
  kilidi hiç *alamadığı* için `kilit_birak`'ın sahiplik dalı hiç çalışmıyordu. Sahiplik
  kontrolünü `if False` yapınca mutant **yine ISIRDI** dedi. Düzeltilmiş hâli yarısını
  gerçekten kuruyor (A alır → B devralır → A çıkar).
- **`M-H0e` yanlış katmandaydı:** aklama bir *yazma* davranışı, kapı hükmü değil; kapı
  zaten "zincir YOK" diyordu, dolayısıyla sabotajda da ısırıyordu. Komut sınamasına
  (`M-AKLAMA`) çevrildi ve ölçütü "çıkış kodu" değil **"tahrif hâlâ görünüyor mu"** yapıldı.

Bu yüzden bu turda eklenen **her yeni test için sabotaj koşusu** var: ilgili korumayı
`if False` yapıp mutantın KAÇTI dediğini gösteriyorum. Altısı da geçiyor.

---

## 3.5 Paketleme doğrulamasında çıkan kusur — P-1

Bu belgeyi yazdıktan **sonra**, paketi sıfırdan kurup doğrularken B listesinde olmayan
bir kusur daha çıktı. Belgeyi geriye dönük "hep biliyordum" diye düzenlemek yerine
buraya ayrı bir başlıkla yazıyorum, çünkü bulunuş sırası da bir veri:

**Ne:** `git init` yapılmış ama **henüz commit atılmamış** bir depoda H9
`"git deposu okunamadi"` diyordu. Depo pekâlâ okunuyordu; yalnızca tarihi boştu
(`git log` boş depoda sıfırdan farklı döner). Yani araç, olmayan bir izin/bozulma
sorununu işaret ediyordu. Bu senin **B-8**'inin sınıfı: itiraf vardı, **sebep yanlıştı**.

**Ne yaptım:** hükmü değiştirmedim — iki hâl de `ÖLÇÜLEMEDİ` kolunda kalıyor, kapı
yeşil. Yalnız sebebi ayrıştırdım: `git rev-parse --git-dir` başarılıysa
"HENÜZ COMMIT YOK — ilk commit'ten sonra ölçülür", değilse gerçek `stderr` satırıyla
"OKUNAMADI: …".

**Ne açtı:** hükümde değişiklik olmadığı için davranışsal yüzey açılmadı; tek yeni
şey fazladan bir `git rev-parse` çağrısı (yalnız `git log` başarısız olduğunda, yani
ömürde birkaç kez). Ölçtüm: taze depoda doğru sebep, `.git/HEAD` bozulmuş depoda
gerçek `stderr`, ikisinde de exit 0 ve `? H9` kolu.

**Kanıt:** senaryo `t_p1`; sabotaj koşumunda (`if _rg.returncode == 0` → `if False`)
**KALDI** diyor — yani kendi sınıfını ölçüyor.

**Sana açık bıraktığım soru:** taze bir depoda defterler henüz `git add` edilmemişse
H9'un **kırmızı** yanması mı doğru olurdu? Kırmızıya çevirmek her yeni projeyi ilk
dakikasında durdurur; "ölçülemedi" demek ise "izlenmiyor" hâlini ilk commit'e kadar
gizler. Bilinçli olarak ölçülemedi seçtim. Karar senin.

---

## 3.6 "Bitti" dedikten SONRA bulunan dört kusur — A-1, A-2, A-3 (+P-1)

Paketi hazırlayıp teslim klasörüne yazdıktan **sonra** iki iç denetim turu daha koştum
(biri beyan-gerçek karşılaştırması, biri düşman belge okuması). Dört kusur daha çıktı.
Bulunuş sırasını olduğu gibi bırakıyorum, çünkü **ne zaman bulunduğu da bir veridir**:
bunlar "bitti" dedikten sonra bulundu.

### A-1 🔴 — `kur` ve `devral` tek-yazar kilidini HİÇ almıyordu

`kilit_al` çağrısı olan komutlar: `not`, `derle`, `emekli`, `karar`, `muhur`, `korunan`,
`bloklastir`. **Olmayanlar: `kur` ve `devral`.** Ve bu turda `devral`a canlı hafızaya
yazan **yeni** bir yol ekledim (`ÇAPA DEVRİ` bloğu — kodda `CAPA DEVRI`) ve o yolu
kilit disiplininin dışında bıraktım.

**Kanıt:** kilidi başka bir pid'e ait bırakıp koştum → `devral` **exit 0**, canlı hafıza
**değişti**. Aynı kilit altında `not` ve `muhur` exit 2 ile duruyor.

**Bu neyin tekrarı olduğunu söyleyeyim:** senin B-5'in kilidin **sahipliğini** sordu; ben
onu iki kez derinleştirdim (pid → pid+inode) ve kilidi *alan komut kümesini* hiç
sormadım. Yani aynı turda hem korumayı derinleştirdim hem kapsamının dışına yeni bir
delik açtım. Bu, bu belgenin üç yerinde alıntıladığım kendi kuralımın ihlali.

**Ne yaptım:** ikisi de `kilit_al` alıyor. `devral`da sıra önemli — yol doğrulaması
kilitten **önce** koşar (aksi hâlde `kilit_al`ın `os.makedirs`'i temiz hükmü yutardı),
kilit `.hafizarc` **yazılmadan** alınır (aksi hâlde yarış penceresi kalır).

**Düzeltme NE AÇTI:** bir kenar buldum ve onu da kapattım — `devral` kilidini **yeni**
ad alanında alır (`arsiv/hafiza/v2`), dolayısıyla **eski** ad alanındaki
(`arsiv/hafiza/.kilit`) bir yazarı göremiyordu; oysa ikisi de aynı canlı dosyaya yazar.
Kilidi tek bir yola bağlamak sınıfı değil o yolu kapatır. Artık `devral` ağaçtaki
**her** `.kilit`i sayar (zaten tüm ağacı `onceki_kurulum_izleri` için tarıyor, ek
maliyet yok). Meşru `devral` hâlâ exit 0, kapı yeşil, kilit sızıntısı yok.

**Kanıt:** komut sınaması **`M-KILITK`**; sabotajda (iki `kilit_al` ve ağaç taraması
devre dışı) **KAÇTI ✗** diyor.

### A-2 🔴 — Bu turda BELGEYE yazdığım çıkış kodu sözleşmesi KODDA yoktu

`SKILL.md`e ve okuma notuna şunu yazdım: *"`kapi` ölçemediğini exit 3 ile söyler …
3 ölçüm yapılamadı (disk dolu, izin yok, beklenmeyen iç hata)"*. Kodda `sys.exit(3)`
**tek bir yerde** ve **yalnız ENOSPC** dalında.

**Ölçüm:**

| Hâl | Beyan | Gerçek (v2.4.0) |
|---|---|---|
| ölçüm yarıda kesildi (bozuk defter, UTF-8 olmayan dosya) | 3 | **1** — gerçek kırmızıyla aynı kod |
| beklenmeyen iç hata / izin hatası | 3 | **2** — kullanım hatasıyla aynı kod |
| disk dolu | 3 | 3 ✓ |

Yani `kapi || dur` diyen bir sarmalayıcı "ölçemedim"i "kırmızı" sanıyordu; ve bu, senin
§4.1'de bana sorduğum sorunun ta kendisiydi — cevabı **evet**ti.

**Ne yaptım (Onur'un kararı: kodu söze uydur):** kesilme ve beklenmeyen iç hata → **3**.
Kırık boru son çaresi de 2 → **3** (hüküm bilinmiyor). `2` artık yalnız `oldur()`un
verdiği **temiz kullanım/girdi hükmüdür**.

**Bilinçli sınır:** hem gerçek bir kapı bulgusu hem kesilme varsa **1** döner — ölçülmüş
bir kırmızı, eksik kapsamdan daha acildir.

**Düzeltmenin AÇMADIĞI ama açıkta bıraktığı şey — sana soruyorum:** *beyanlı/yapısal*
kapsam boşluğu (git yok, henüz commit yok, `politika_gerekce`) hâlâ **exit 0** ve hüküm
`YEŞİL (SINIRLI)`. Yani `kapi && dagit`, kapsamı eksik bir projede dağıtım yapar. Bunu
3'e çevirmek her yeni projeyi ilk dakikasında durdururdu ve `politika_gerekce`nin
"kapı kırmızı yanmaz" tasarımıyla çelişirdi. Bugünkü çizgi bilinçli — **doğru yerde mi?**

**Kanıt:** senaryo **`t_a2`** dört hali birden ölçer (temiz=0 · yalnız-kesilme=3 ·
kırmızı+kesilme=1 · kullanım hatası=2); sabotajda **KALDI**.

### A-3 🟠 — Kırık boru yalnız stdout'ta yutuluyordu

`_KirikBoruyaDayanikliAkis` yalnız `sys.stdout`a takılmıştı. Kodda sekiz ayrı
`sys.stderr.write(` var; bunlardan biri `yol_on_kontrol`un hardlink uyarısı ve yorumunda
açıkça *"İşlem SÜRÜYOR"* diyor.

**Ölçüm:** proje dışında hardlink'li bir defter varken, tüketicisi **kapatılmış** bir
stderr'de `not` komutu exit 0 yerine **exit 2** veriyor ve **fragmanı hiç yazmıyordu**.
Yani "raporla, durdurma" diyen bir uyarı komutu tümden iptal ediyordu — Y-2/Y-3'ün ta
kendisi, sadece öteki akışta.

**Daha kötüsü:** bunu kanıtlayan testim sınıfı göremiyordu — `t_y42`nin Y-2/Y-3
senaryoları `stderr=subprocess.DEVNULL` ile koşuyordu. **Bir kanalı çöpe atan test o
kanaldaki sınıfı ölçemez.**

**Ne yaptım:** `sys.stderr` de sarıldı. **Kanıt:** senaryo **`t_a3`** (açık stderr ve
`os.close(2)` ile kapatılmış stderr, fragman sayımıyla birlikte); sabotajda **KALDI**.

### Ve üç BEYAN hatası (kod değil, dürüstlük)

1. **Performans temelini geri çekiyorum.** "17.07 sn → 4.13 sn" **yeniden üretilemedi**.
   Aynı makinede yeniden ölçüm (300k satır, iki koşum): v2.3.0 ASCII ~10,0 sn / Türkçe
   ~12,1 sn · v2.4.1 ASCII ~3,7 sn / Türkçe ~5,9 sn. Hızlanma 4,1× değil **2,7× (ASCII)
   / 2,0× (Türkçe)**.
2. **Performans testim kendi lehime kuruluydu.** 300 000 satırın **hepsi ASCII**'ydi —
   yani tam olarak benim *eklediğim* hızlı yolu ölçüyordu. Bu bir **Türkçe** hafıza
   aracı; hedef kullanıcının yazmadığı girdiyle "kapandı" demek, ölçümü iddiaya
   uydurmaktır. Test iki kola bölündü, eşik Türkçe kola göre kondu (`< 8 sn`), ve artık
   kapının **tamamlandığı** da doğrulanıyor — yarıda kesilen bir ölçüm de hızlı biter.
3. **Darboğaz atfım yanlıştı.** "Asıl darboğaz senin işaret ettiğin desen derleme değil"
   demiştim. İki iyileştirme tek tek geri alınıp ölçüldü: **desen önbelleği 2,09 sn**,
   `basliksal` hızlı yolu **1,23 sn**. Senin teşhisin benimkinden **daha güçlüydü**.

**Ve bir iddia daraltıldı:** "inode saklaması yarışı kapattı" → ölçüldü, aynı dizinde
silinen kilidin inode'u **20/20 yeniden kullanılıyor**. Pencere **daraldı, kapanmadı**.
Gerçek kapanış `(st_dev, st_ino, st_ctime_ns)` ya da kilit dosyasına yazılan rastgele
bir jeton ister; §5'e açık madde olarak eklendi.

---

## 4. Bugünkü ölçümler

| Ölçüm | Sonuç |
|---|---|
| Isırma kanıtı (`isir`) | **36/36** (derle'li proje) · taze projede 34/34 + 2 KURULAMADI · temiz projede 0 yanlış-pozitif |
| Yeni testler | `M-H0d` · `M-H0t` · `M-KACIS` · `M-KILIT` · `M-AKLAMA` · `M-DEVIR` · `M-KILITK` · `t_p1` · `t_a2` · `t_a3` — **onu da sabotajda KAÇIYOR/KALIYOR** |
| Senaryo kanıtları (`t_y42.py`) | **57 geçti · 0 kaldı · 1 ölçülemedi** (salt-okunur senaryosu; konteynerde root) — toplam 58 |
| Temiz hata kanıtları (`t_y3.py`) | **20/20** |
| Kayıpsızlık | 50× aynı konu derlendi → **50/50** *(koşucu pakette YOK — beyanım)* |
| Normal hafta simülasyonu | 11 adım · **0 yanlış-pozitif** *(koşucu pakette YOK — beyanım)* |
| Performans | 300k satır `kapi` **ASCII ~3,5 sn · TÜRKÇE ~6 sn** (v2.3.0: ~10 / ~12 sn) — `t_y42` B-6 ile koşulabilir · 2 000 dosyalı git deposu **0.14 sn** *(koşucu pakette YOK)* |
| `isir` çıkış kodları | 0 / 1 (kör kapı) / 2 (ölçülemeyen) / 4 (temiz sürüm FAIL) — çıktıda belgeli |
| `kapi` çıkış kodları | 0 yeşil · 1 kırmızı · 2 kullanım hatası · **3 ölçüm yapılamadı** — dördü de senaryoyla ölçülü (`t_a2`) |

---

## 5. Bilerek açık bıraktıklarım

1. **Yeniden çıpalama engellenemez.** Yazma erişimi olan biri `.hafizarc`'ı silip
   `devral` koşabilir. Yaptığım şey bunu **görünür ve kalıcı** kılmak (iz taraması +
   canlıya + çıpaya + zincire kayıt). Gerçek çözüm depo-dışı bir tarih (git); bunu
   `references/kapilar.md`'de açıkça yazıyorum, "kapattım" demiyorum.
2. **Zincir anahtarsızdır.** `yuk`'u güncelleyip `halka`yı yeniden hesaplamak hash
   denetiminden geçer. mtime dedektörü bunun **en yaygın kılığını** görünür kılar ama
   **hüküm vermez** (işaret). Bu mimari sınır ilk turdan beri belgede.
3. **`.hafizarc` var + `_CIPA.json` yok → yazma kapalı, araç içi kurtarma yok.** Bilinçli
   fail-closed. Git'siz bir projede kazara silme projeyi yazmaya kapatır; kurtarma yolu
   sürüm kontrolü. Otomatik bir "onar" komutu tam da kapının engellemek için var olduğu
   şeyi kolaylaştırırdı.
4. **İzin/salt-okunur senaryosu bu ortamda ÖLÇÜLEMEDİ** (konteyner root). Senaryo
   `t_y42`'de duruyor ve uygun ortamda kendini ölçüyor; "geçti" demiyorum, `ÖLÇÜLEMEDİ` diyor.
5. **H9'un otomatik mutantı yok** (mutant kopyasına `.git` alınmıyor).
6. **Kilit inode kimliği yarışı DARALTIR, kapatmaz.** Ölçüldü: aynı dizinde silinen
   kilidin inode'u 20/20 yeniden kullanılıyor. Kapanış için `st_ctime_ns` ya da jeton
   gerekir; bu turda yapmadım.
7. **Beyanlı/yapısal kapsam boşluğu `kapi`yi exit 0'da bırakır** (git yok, henüz commit
   yok, `politika_gerekce`). `kapi && dagit` kapsamı eksik projede dağıtım yapar. Bunu
   3'e çevirmek her yeni projeyi ilk dakikasında durdururdu — çizgiyi burada çektim,
   yargını istiyorum.
8. **Dört ölçümün koşucusu pakette YOK:** "2 330 senaryo ham traceback avı",
   "kayıpsızlık 50×", "normal hafta 11 adım", "2 000 dosyalı git deposu". Bunlar benim
   koşumlarım ve **sen doğrulayamazsın**. §6 tablosunda işaretledim; koşucuları
   paketlemek sonraki turun işi.
9. **"23 yeni kusur" sayısı belgeden doğrulanamıyor.** §2'de 12'si tek tek yazılı,
   §3'te 2 test kusuru, §3.5–3.6'da 4 tane daha = 18. Kalan 5'i sınıf olarak sayıldı
   ama tek tek yazılmadı. Sayıyı geri çekmiyorum ama **doğrulanamaz olduğunu** söylüyorum;
   doğrulanabilir olan 18'dir.

---

## 6. Senden istediğim (dördüncü tur)

1. **§2'yi kır.** Bu turda düzeltmelerimin 23 kusur ürettiğini iki iç denetçiyle buldum.
   Üçüncüsünün de bulacağını varsayıyorum — **§2'de listelemediğim** birini bul.
2. **Özellikle yeni yüzeyler:** `_KirikBoruyaDayanikliAkis`, `onceki_kurulum_izleri` +
   `CAPA DEVRI` bloğu (canlıya yazan yeni bir yol — H1/H3/H10 ile çakışıyor mu?),
   `cli_yol_coz` geçidi, kilit inode kimliği, `--siki`nin yeni beyan mantığı.
3. **Testleri denetle.** İki testimin yanlış katmanı ölçtüğünü sabotajla buldum. Kalan
   36 mutant + 58 senaryodan **başka hangisi sahte ısırıyor?** Sabotaj yöntemini
   istediğin teste uygula.
4. **Kapsam envanteri:** 36 mutant + 58 senaryo hangi sınıfı hâlâ ölçmüyor?
5. **§5'teki dokuz bilinçli açığı yargıla.** Özellikle (1): "engelleyemediğini görünür
   kıl" savunulabilir bir güvenlik duruşu mu, yoksa kendimi kandırmak mı? Ve (7):
   kapsam boşluğu ile kırmızı arasındaki çizgiyi doğru yere mi çektim?
6. **Bir tur önce "bitti" demiştim.** Paketten sonra iki tur daha koştum ve dört kusur
   daha çıktı (§3.6) — ikisi YÜKSEK. Bu, bu belgedeki "bitti" kelimesinin ne kadar
   değerli olduğunu gösteriyor. **Sana asıl sorum:** §3.6'yı üreten yöntem (beyan-gerçek
   karşılaştırması + düşman belge okuması) senin turunda da işe yarar mı, yoksa ben
   yalnız kendi kör noktalarımın kolay olanlarını mı buluyorum?

Kararını yine tek kelimeyle ver: **KUR** · **DÜZELT** · **REDDET**.
