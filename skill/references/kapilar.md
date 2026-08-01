# Kapılar — H0…H15

Her kapı bir **acı çekilmiş dersin** kalıcı hâlidir. "Şunu bir daha yapmayalım"
demek yetmez; ölçen bir kapı olmadan aynı hata geri gelir.

---

## H0 — ÇIPA
**Ölçer:** `arsiv/hafiza/_KAYNAK.md`'nin SHA'sı `_CIPA.json`'daki değerle aynı mı; ve
defterlerin halka zinciri (`_ZINCIR.jsonl`) tutarlı mı.

**Neden:** Snapshot **kanıt tabanıdır** — H1'in tüm ölçümü ona dayanır. Snapshot'ı
bozuk canlıya uyacak şekilde düzenleyen bir oturum, H1'i yeşil yakardı. Aynı şey beyan
defterleri için de geçerli: `_DUZELTMELER.json`'a satır eklemek, snapshot'taki herhangi
bir satırı "yasal" biçimde yeniden yazdırabilirdi.

**Boş zincir ≠ sağlam zincir (v2.4):** eskiden `_ZINCIR.jsonl` 0 bayta indirildiğinde
döngü hiç dönmüyor, kapı hiçbir bulgu üretmiyordu — yani zinciri **silmek** onu
kurcalamaktan daha güvenliydi. Artık boş/genesis'siz zincir kendi başına bulgudur:
"defter-SHA doğrulaması YAPILAMIYOR; bu hâl 'sağlam' SAYILMAZ". İlk halkanın
`onceki` alanı `GENESIS` değilse "zincirin BAŞI kesilmiş olabilir" denir.

**Zaman damgası meşruiyeti (v2.4):** halkanın `t` alanı hash'e giriyordu ama
**hiçbir yerde denetlenmiyordu** — hash'i yeniden hesaplayabilen biri geçmişi
istediği tarihe koyabiliyordu. Artık `t` geleceğe (>2 gün) ya da bir öncekinin
gerisine (>2 gün) düşerse ötülür. Tolerans 2 gün, çünkü UTC−12…UTC+14 aralığı
26 saat eder; timezone taşıyan bir damga naif yerel zamana çevrilir (aksi hâlde
`TypeError` kapının tamamını düşürüyordu).

**Sınır (dürüstlük):** zincir depo-içidir. Tutarlı biçimde N dosyayı birden düzenleyen
bir aktörü durduramaz. Yaptığı, maliyeti 1 hamleden N tutarlı hamleye çıkarmak ve
**tutarsız** hamleyi ısırmaktır.

**Sınır 2 (v2.4'te açıkça yazıldı):** çıpayı **yeniden kurmak** engellenemez —
dosya tabanlı bir şemada `.hafizarc`'ı silip `devral` koşan biri her zaman yeni bir
başlangıç noktası yaratabilir. Üç kez "engelleme" denendi, üçü de ya atlatıldı ya da
meşru v1→v2 geçişini tamamen kilitledi. Kabul edilen doktrin: **önleme, GİZLENEMEZ
KIL.** `devral` tüm ağacı önceki-kurulum izleri için tarar, bulduklarını canlı
hafızaya kalıcı bir `ÇAPA DEVRİ` bloğu olarak yazar (bloğu silmek `[H1] KAYIP`
yakar) ve halkaya `onceki_kurulum_izi` alanı düşer.

---

## H1 — BÜTÜNLÜK
**Ölçer:** (canlı ∪ arşiv) anlamlı satırları ⊇ snapshot'ın çok-kümesi **+ baseline-sonrası
beyan edilmiş satırlar**. Eksik = FAIL. Beyan edilmiş düzeltmeler (`_DUZELTMELER.json`) ve
yeni satırlar (`_YENI_SATIRLAR.txt`) hesaba katılır.

**Kapsam (önemli):** çıpa yalnız `kur`/`devral` anında donar. Bir zamanlar bu, kurulumdan
**sonra** eklenen her satırın kapsam dışında kalması demekti — silinince hiçbir kapı
ötmüyordu. Artık `derle` ve `bloklastir` canlıya ekledikleri her satırı iki deftere birden
yazar (`_YENI_SATIRLAR.txt` → H1 bekler, `_KOVA.json`/`ek_canli` → H1-KOVA canlıda durmasını
bekler). Meşru çıkış yolları `emekli` ve `derle` sıkıştırmasıdır; ikisi de taşımayı beyan eder.

**Üretilen blok istisnası:** canlıdaki `<!-- v2-arsiv-dizini -->` alt bloğu muhasebeye
girmez — her derlemede yeniden hesaplanan türev veridir (bayt sayıları değişir). Tamamen
silinirse H6 kırmızı yanar.

**Neden:** "Hiçbir şey kaybolmadı" cümlesini bir **test sonucuna** çevirir. Özetleme
en sinsi kayıp biçimidir: bir satırı özetlemek orijinali siler ve kimse fark etmez.

**Not:** *anlamlı satır* = boş olmayan **her** satır — başlıklar ve kod-bloğu içi dahil.
Başlıkları "yapısal" sayıp dışarıda bırakmak, bir başlığın sessizce silinmesine izin verir.

**`--siki` modu:** arşivleme anında *fazlalık* da FAIL olur. Normal modda fazlalık
meşru büyümedir, çünkü checkpoint kuralı her oturum hafızaya yazmayı emreder.

---

## H1-KOVA — YERLEŞİM KÖRLÜĞÜ
**Ölçer:** snapshot'ta "CANLI" kovasındaki bir satır hâlâ canlıda mı (beyan edilmiş
taşımalar düşülerek).

**Neden:** H1 tek başına **kör**dür. Bir kural satırını canlıdan arşive sessizce taşırsan
birleşim çok-kümesi değişmez → H1 yeşil yanar. Ama sonraki oturum o kuralı **hiç görmez**,
çünkü arşivi tam okumak yasaktır. Bayt korunur, görünürlük ölür. Bu kapı olmadan
sistemin en büyük açığı buydu.

---

## H2 — ŞİŞME
**Ölçer:** canlı hafıza ≤ `tavan_kb`.

**Neden:** Uzun bağlam ölçülebilir biçimde zararlıdır — girdi uzadıkça model başarımı
düşer, ve "şişkin talimat dosyası" gerçek kuralların yok sayılmasına yol açar. Tavan,
"her şeyi canlıda tut" refleksine karşı fiziksel bir sınırdır.

**Dikkat:** H1 ile H2 birlikte bir **kilitlenme** üretebilir — silemezsin (H1), şişer
(H2). Çıkış yolu emekliliktir: satır silinmez, taşınır.

---

## H3 — ZORUNLU BÖLÜMLER
**Ölçer:** `.hafizarc`'taki başlıklar canlıda var mı.

**Neden:** Bölüm yoksa o bilgi türü hiç yazılmaz. "Açık kararlar" başlığı olmayan bir
hafızada açık karar biriktiği fark edilmez.

---

## H4 — ÖLÜ BAĞLANTI
**Ölçer:** belgede tam-yol olarak geçen her dosya diskte var mı.

**Neden:** Hafıza olmayan bir dosyaya yönlendirirse, sonraki oturum onu arar, bulamaz ve
ya durur ya uydurur. (Bu kapı bir kez, henüz yazılmamış bir dosyaya verilen referansı
yakaladı — yazılmadan referans verilmişti.)

**Yanlış-pozitif önlemi:** yalnız *tamamı yol olan* backtick içerikleri sayılır;
`` `hafiza.py kapi` `` bir komuttur, yol değil.

---

## H5 — SÜRÜM TEKİLLİĞİ
**Ölçer:** `kanonik_artefakt` deseni, karar günlüğü dışında birden fazla farklı adla
geçiyor mu.

**Neden:** "Aktif sürüm hangisi" sorusunun iki cevabı olamaz. Karar günlüğü tarihsel
olduğu için muaftır; geri kalan her yerde tek ad geçerlidir.

**Tasarım notu:** kapı "aktif" kelimesini aramaz, **yapıya** bakar — yoksa eşanlamlı bir
kelime (güncel/çalışılan/son) kapıyı atlatırdı.

---

## H6 — ARŞİV DİZİNİ
**Ölçer:** `arsiv/hafiza/HAFIZA_*.md` ↔ canlıdaki `ARŞİV DİZİNİ` bölümü **çift yönlü**
eşleşiyor mu.

**Neden:** Arşiv, dizini olmayan bir arşivse yok hükmündedir. Arşivcilerin *finding aid*
kavramı budur: her öğeyi tek tek indekslemeden, üst seviyeleri indeksle, aşağı in.

---

## H7 — KURAL YERLEŞİMİ
**Ölçer:** kalıcı kural işareti taşıyan satırlar (`PAZARLIKSIZ`, `MUTLAK KURAL`,
`KIRMIZI ÇİZGİ`…) yalnız kural evi bölümlerinde mi.

**Neden:** Kalıcı bir kural rotasyona giren bir bölümde yaşarsa, usulünce emekli edilir
ve görünmez olur. Kuralın ölümü bir hata değil, **doğru işleyen bir temizliğin yan
etkisi** olur — bu yüzden yerleşim kuralı gerekir.

Bu maddenin literatürde bilinen bir karşılığı yok; sahada acı çekilerek bulundu.

**Başarım notu (v2.4):** bu kapı her satır için Türkçe normalizasyon + `re.compile`
koşuyordu; 300 000 satırlık bir hafızada kapı **17 sn** sürüyordu ve maliyet
girdiyle doğrusal büyüyordu. Normalizasyon `str.maketrans` tablosuna + ASCII hızlı
yoluna, desen derlemesi süreç-ömürlü bir önbelleğe alındı: **4,1 sn**. Eşdeğerlik
körlemesine iddia edilmedi — 30 000 rastgele dize ve tüm kod-noktası taramasıyla
eski/yeni çıktılar karşılaştırıldı: **0 fark**.

---

## H8 — KORUNAN BLOKLAR
**Ölçer:** `_KORUNAN.json`'da kayıtlı blokların hash'i tutuyor mu.

**Neden:** Bazı bloklar (protokol metinleri, kırmızı çizgiler) yanlışlıkla
değiştirilmemelidir. Bilinçli değiştirdiysen kapı kırmızı yanar — **doğrusu budur**:
"beyan et ya da kır". Beyan yolu: `hafiza.py korunan ... --gerekce "..."`.

---

## H9 — GİT İZLENİRLİĞİ
**Ölçer:** git varsa; zincir, çıpa ve canlı hafıza **izleniyor mu** (`git ls-files`).
Git yoksa `ÖLÇEMİYORUM` der — sessiz PASS vermez.

**Neden:** Depo-içi zincirin ötesinde gerçek bir içerik-adresli tarih yalnız git'tir.
Ama `.gitignore`'a takılmış bir zincir git'te **yok** demektir; o zaman zincir tarih
değil, yalnızca bir dosyadır.

**Boşluk (açıkça):** bu kapının otomatik mutantı yoktur, çünkü mutant kopyasına `.git`
alınmıyor. Elle sınanır: `git rm --cached <zincir>` → kapı kırmızı yanmalı.

---

## H10 — KONU TEKİLLİĞİ
**Ölçer:** her `konu` etiketi canlıda en fazla bir blokta mı · her konu `KONULAR.md`
sözlüğünde tanımlı mı · **blok yapısı sağlam mı** (kapanmamış ya da iç içe blok = FAIL).

Yapı kontrolü sonradan eklendi: kapanmamış bir blok, blok sayımından tamamen düşüyordu —
yani aynı konuda birikme sessizce mümkündü.

**Neden:** Anahtar bazlı sıkıştırmanın kapısı budur. Aynı konuda beş blok birikirse
hepsi "meşru" görünür ama dördü bayattır ve hangisinin geçerli olduğu belirsizdir.
Sözlük zorunluluğu, konu adlarının zamanla dağılmasını (`durum`, `genel-durum`,
`guncel-durum`) engeller.

---

## H11 — KARAR BÜTÜNLÜĞÜ (ADR)
**Ölçer:** numaralar tekrarsız ve boşluksuz mu · `yerine-gecen` ↔ `yerini-aldigi`
çift yönlü tutarlı mı · `durum: kabul` olan ADR'nin gövdesi gerçekten doldurulmuş mu ·
canlı hafıza var olmayan ya da **yerine geçilmiş** bir karara link veriyor mu.

**Neden:** ADR koleksiyonunun bilinen zayıflığı, kararların *tarihini* verip sistemin
*bugünkü halini* vermemesidir. Bu kapı o boşluğu kapatır: canlı hafıza bayat bir karara
link veremez, ve "kabul" damgası boş bir gövdeye vurulamaz (bedelleri yazılmamış karar
karar değildir).

---

## H12 — BAYATLIK VE SAPMA
**Ölçer:** (a) `Son güncelleme` tarihi `bayatlik_gun`'den eski mi; (b) bir konuda canlı
bloktan **daha yeni** bir fragman/ADR var mı; (c) derlenmeyi bekleyen fragman var mı.

**Neden:** Canlı dosyanın türetilmiş olması gerekiyordu ama serbest metinde tam otomatik
yeniden üretim mümkün değil. Bunun yerine **sapma alarmı** kurulur: kaynak canlıdan
yeniyse, canlı yalan söylüyordur.

**Sınır:** bu bir garanti değil, bir alarmdır. PostgreSQL'in checkpoint garantisiyle
(durum logdan yeniden üretilebilir) karıştırılmamalıdır.

---

## H13 — SAKLAMA PLANI
**Ölçer:** `SAKLAMA_PLANI.md` var mı, en az üç seri tanımlı mı, ve dolu olan her
`arsiv/<tür>` klasörü planda geçiyor mu.

**Neden:** Emeklilik kararı **anında ve sezgiyle** değil, **önceden ve seri düzeyinde**
verilir — arşivcilerin *appraisal + retention schedule* yöntemi budur. Plansız bir seri,
er ya da geç ya sonsuza kadar birikir ya da yanlışlıkla silinir.

---

## H14 — DİSİPLİN (proje ilerledi mi, hafıza ilerledi mi)
**Ölçer:** proje dosyalarındaki en yeni değişiklik tarihi ile canlı hafızanın
`Son güncelleme` tarihini karşılaştırır. Fark `hafiza_gecikme_gun`'ü aşarsa FAIL.
(`arsiv/`, `gunluk/`, `.git`, `node_modules` hariç tutulur.)

**Neden:** Bu sistemin en büyük açığı "unutmak"tı — çalışılır, hiçbir kayıt bırakılmaz,
hiçbir kapı kırmızı yanmaz. H14 unutmayı **ölçülebilir** hale getirir: proje ilerlemiş
ama hafıza ilerlememişse kapı durdurur. `hafiza_gecikme_gun: 0` ile kapatılabilir —
kapatıldığı da raporda "bilinçli" diye yazılır.

**Kardeşi:** `derle` fragmansız çalıştırıldığında artık **hata** verir (eskiden sessiz
uyarıydı). Bilinçli boş tur için `--bos-serbest`.

---

## ISIRMA KANITI (kör kapı protokolü)

`hafiza.py isir`, her kapı için geçici bir kopyada bilerek bir açık üretir ve kapının
yakaladığını kanıtlar; ayrıca temiz sürümde **yanlış-pozitif olmadığını** gösterir.

| Mutant | Ne sökülür |
|---|---|
| M-H0 | snapshot kurcalanır |
| M-H1 | canlıdan bir satır silinir |
| M-H1K | canlıdan arşive **beyansız** taşınır |
| M-H2 | dosya tavanın üstüne şişirilir |
| M-H3 | zorunlu başlık silinir |
| M-H4 | olmayan dosyaya referans eklenir |
| M-H5 | iki farklı kanonik artefakt adı yazılır |
| M-H6 | dizinde olmayan arşiv dosyası yaratılır |
| M-H7 | kalıcı kural yanlış bölüme konur |
| M-H8 | korunan blok sessizce değiştirilir |
| M-H10 | aynı konuda ikinci blok açılır |
| M-H11 | ADR numara boşluğu yaratılır |
| M-H12 | tarih 2000'e çekilir |
| M-H13 | saklama planı silinir |
| M-H14 | proje dosyası bugün değişir, hafıza 10 gün geriye alınır |
| M-H1b | **baseline-sonrası** eklenmiş bir blok silinir (bağımsız denetimin bulduğu ana açık) |
| M-H0b | zincir kaydının *gerekçe* ve *tarih* alanı tahrif edilir (hash artık bunları kapsıyor) |
| M-H10b | kapanmamış blok işareti bırakılır |
| M-H12b | tarih **geleceğe** çekilir (iki tazelik kapısını birden susturuyordu) |
| M-H4b | **Türkçe adlı** ölü bağlantı eklenir |
| M-H15a | `kural_isaretleri` boşaltılır (H7 ve `emekli` koruması fiilen kapanır) |
| M-H15b | `tavan_kb` şişirilir (H2 fiilen kapanır) |
| M-H15c | `KONULAR.md` silinir (konu sözlüğü disiplini kapanır) |
| M-H0c | politika dosyası (`.hafizarc`) mühürsüz değiştirilir |
| M-H7b | `ASLA` işaretli kural rotasyona giren bölüme konur |
| M-H10c | kapanmamış kod çiti bırakılır (blokları yutardı) |
| M-H10d | aynı konuda ikinci blok açılıp kod çitiyle **gizlenir** (sessiz çift blok) |
| M-H14b | mutant kopyada taze git deposu kurulur, **Türkçe adlı** dosyada commitlenmemiş değişiklik bırakılır |
| M-H8b | korunan blok tahrif edilip dosyanın başına **bozulmamış bir kopya** konur |
| M-H0d | zincir **0 bayta** indirilir + bir defter tahrif edilir (silmek kurcalamaktan güvenliydi) |
| M-H0t | son halkanın zaman damgası **geleceğe** alınır ve hash yeniden hesaplanır |

Toplam **31 kapı mutantı**. Bunlara ek olarak beş **komut sınaması** vardır — bunlar
kapı mutantı değildir, çünkü ölçtükleri şey bir kapının hükmü değil, bir komutun
**yazma-tarafı davranışıdır**:

| Komut sınaması | Ne ölçer |
|---|---|
| M-KACIS | CLI yol argümanı (`emekli --hedef`, `korunan --dosya`) proje ağacının **dışına** çıkabiliyor mu |
| M-KILIT | `kilit_birak` **başkasının** kilidini siliyor mu (pid + inode sahipliği) |
| M-AKLAMA | zincir silinip/boşaltılıp yeniden kurulduğunda tahrif **hâlâ görünür mü** |
| M-DEVIR | `.hafizarc` silinip `devral` koşulduğunda yeniden çapalama **gizlenebiliyor mu** |
| M-KILITK | kilit **KAPSAMI**: `kur` ve `devral` tek-yazar kilidini alıyor mu |

> **Neden ayrı kategori:** M-AKLAMA önce bir kapı mutantı olarak yazılmıştı ve
> sabotaj altında bile ısırıyordu — çünkü kapı zaten "zincir yok" diyordu; ölçtüğü
> sınıf aklamanın kendisi değildi. Aklama bir **yazma-tarafı** davranışıdır; ölçütü
> "çıkış kodu ne" değil, "tahrif hâlâ görünüyor mu"dur. Aynı şekilde M-KILIT'in ilk
> hâli alt süreçte `muhur` koşuyordu — o süreç kilidi hiç **almadığı** için sahiplik
> dalı hiç çalışmıyordu ve sınama sabotaj altında da ısırıyordu. İkisi de yeniden
> yazıldı.

**Sabotaj sınaması (her yeni test için zorunlu):** testin ölçtüğünü iddia ettiği
korumayı `if False` yaparak devre dışı bırak; mutant **KAÇTI** demeli. Demiyorsa o
test kendi sınıfını değil, komşu bir sınıfı ölçüyordur. v2.4'ün altı yeni sınamasının
altısı da bu süzgeçten geçirildi.

**`isir` çıkış kodları (v2.4):** `0` hepsi ısırdı · `1` **KAPI KÖR** (kaçan mutant var)
· `2` ölçülemeyen mutant var (testin ön-koşulu sağlanmadı — kapı hükmü değil) ·
`4` temiz sürüm zaten FAIL veriyor. Eskiden 1 ve 2 tek koda katlanıyordu; taze bir
`kur` projesinde M-H1b kurulamadığı için (henüz `derle` koşulmamış) sağlıklı proje
`isir && ...` diyen CI sarmalayıcısında başarısız etiketleniyordu.

**Kural:** bir mutant kaçarsa, o kapının "temiz" hükmü geçersizdir — sonuç `ÖLÇÜLMEDİ`
olur, "temiz" olmaz. Ve **bir kapının mutantı diğerlerini kapsamaz**: kapsama iki ayrı
adımdır — önce envanter (neyin ölçüldüğünü listele), sonra her biri için ayrı mutant.

**Sayım dürüstlüğü:** "36/36 ısırıyor" yalnızca `derle` koşulmuş bir projede geçerlidir.
Taze bir `kur` projesinde M-H1b ve M-DEVIR ön-koşulsuz kalır; sonuç `34/34 + 2
KURULAMADI` olur ve çıkış kodu 2'dir. İkisi de sağlıklıdır; **hangi bağlamda ölçüldüğü
yazılmadan mutant sayısı beyan edilmez.**


---

## H15 — POLİTİKA (kapıların kendisi gevşetildi mi)

**Ölçer:** `.hafizarc`'ta kapıları fiilen kapatan bir ayar var mı — `kural_isaretleri`
boş (H7 ve `emekli` koruması ölür), `tavan_kb > 1000` (H2 ölür), `zorunlu_bolumler` boş
(H3 ölür), `KONULAR.md` yok (H10'un yarısı ölmüş olur).

**Neden:** Bir kapı sistemi ancak kendi ayarlarını da ölçüyorsa bir şey ifade eder.
Aksi hâlde en ucuz kaçış yolu kapıyı kırmak değil, **eşiği sonsuza çekmek** olurdu —
ve bu hiçbir yerde görünmezdi.

**Kaçış yolu (bilinçli ve GÖRÜNÜR):** gerçekten gerekiyorsa `.hafizarc`'a
`"politika_gerekce": {"tavan_kb": "en az 15 karakter gerekçe"}` yazılır. O zaman kapı
kırmızı yanmaz ama hüküm satırı `SONUC: YESIL (SINIRLI) — … N ŞEY ÖLÇÜLMEDİ` der ve
gevşeklik `?` satırında `ARTIK ÖLÇMÜYOR` diye listelenir. Gerekçe `.hafizarc`'ta olduğu
için zincire girer: mühürsüz değiştirilirse H0 yakalar. Yani gevşeklik **gizlenemez,
itiraf edilir**.

`devral` çok büyük bir hafıza devraldığında bu gerekçeyi **kendisi yazar** (tavan
dosyaya göre kurulduğu için) — böylece devir ilk gün kilitlenmez, ama gevşeklik yine
raporda durur.

---

## H-LINK — DOSYA KİMLİĞİ

**Ölçer:** defterlerden/arşivden herhangi biri proje ağacının **dışında** da bir ada
sahip mi (sembolik link ya da hardlink).

**Neden:** Denetim izi proje ağacının dışında yaşarsa sürüm kontrolü onu kapsamaz ve
sessizce yok olabilir. Sembolik link **reddedilir** (yazma engellenir). Hardlink
**raporlanır ama engellenmez** — `cp -al` / `rsync --link-dest` ile alınmış sıradan bir
yedek projeyi kilitlememelidir; ama o dosyalara yazmanın dışarıdaki adı da değiştirdiği
söylenir.

---

## TEK YAZAR KİLİDİ

`derle` / `emekli` / `bloklastir` / `not` / `karar` / `muhur` / `korunan` işe başlarken
`arsiv/hafiza/.kilit` dosyasını `O_EXCL` ile açar. İki oturum aynı anda `derle`
koştuğunda ikisi de canlıyı okuyup ayrı ayrı yazıyor ve ikinci yazım birincinin bloğunu
eziyordu (bağımsız denetimde 13 denemenin 2'sinde üretildi: `[H1] KAYIP` + kalıcı
kırmızı). Kilit meşgulse temiz hata verilir; çıkışta hangi yoldan olursa olsun bırakılır.

**KAPSAM (v2.4.1) — sahiplikten önce gelen soru.** Yukarıdaki liste kilidi *alan*
komutları sayar; v2.4'e kadar `kur` ve `devral` bu listede **yoktu**. v2.4 `devral`a
canlı hafızaya yazan yeni bir yol ekledi (`ÇAPA DEVRİ` bloğu, kodda `CAPA DEVRI`) ve
o yolu kilit disiplininin dışında bıraktı. Ölçüldü: başkasına ait bir kilit dururken
`devral` exit 0 veriyor ve canlı hafızayı değiştiriyordu — aynı kilit altında `not` ve
`muhur` duruyor. Yani B-5'te kilidin **sahipliği** derinleştirilirken **kapsamı** hiç
denetlenmedi; aracın kendi doktrininin ihlali. Artık ikisi de kilit alır. Ayrıca
`devral` kilidini **yeni** ad alanında (`arsiv/hafiza/v2`) aldığı için **eski** ad
alanındaki bir yazarı göremiyordu — oysa ikisi de aynı canlı dosyaya yazar; bu yüzden
`devral` ağaçtaki **her** `.kilit`i sayar. Mutant: **M-KILITK**.

**Sahiplik (v2.4):** `kilit_birak` eskiden yolu görünce siliyordu — kendi kilidini mi
sildiğine bakmıyordu. Sonuç: A süreci kilidi alır, B `atexit`'te **A'nın** kilidini
siler, üçüncü bir süreç girer ve kilidin varlık sebebi ortadan kalkar. Artık kilit
oluşturulurken **inode**'u saklanır; bırakırken hem inode hem dosyadaki pid doğrulanır,
ikisinden biri tutmuyorsa dosyaya **dokunulmaz**.

**Bayat kilit teşhisi (v2.4):** "kilit meşgul" demek yetmiyordu — kullanıcı çökmüş bir
süreçten kalan kilidi silmeye mi cesaret edeceğini bilemiyordu. Artık hüküm satırı
"pid YAŞIYOR" / "pid BAYAT, silmen güvenli" / "ÖLÇÜLEMEDİ" der; kilit 1 saatten eskiyse
"pid yeniden kullanılmış olabilir" uyarısı düşülür. Kilidi **araç silmez** — teşhis eder,
kararı insana bırakır. `.kilit`in dosya değil **dizin** olduğu hâl de tek bir temiz
hükümle ayrılır (eskiden `IsADirectoryError` ham traceback'e düşüyordu).

**ENOSPC kenar durumu:** disk dolu olduğunda kilit dosyası oluşuyor ama pid satırı
yazılamıyordu; pid'siz kilidi hiçbir süreç sahiplenemediği için proje **kalıcı olarak**
yazmaya kapanıyordu. Pid yoksa kilidi biz oluşturmuşuzdur (`O_EXCL` başkasınınkini
açamaz) — o hâlde silmek güvenlidir. Bu düzeltme bir yarış açtı (başkasının henüz pid
yazmamış kilidi); inode saklaması onu **daralttı, kapatmadı** — ölçüldü: aynı
dizinde silinen kilidin inode'u 20 denemenin 20'sinde yeniden kullanılıyor. Gerçek
kapanış için `(st_dev, st_ino, st_ctime_ns)` üçlüsü ya da kilit dosyasına yazılan
rastgele bir jeton gerekir; bu **bilinçli olarak açık** bırakıldı ve denetçiye soruldu.

---

## ÇIKIŞ KODU SÖZLEŞMESİ (v2.4)

Bir kapı sistemi ancak **çıkış kodu güvenilirse** otomasyona konabilir. v2.4'te üç
ayrı yerde çıkış kodu yalan söylüyordu; hepsi kapatıldı.

| Komut | Kod | Anlamı |
|---|---|---|
| `kapi` | 0 | YEŞİL (ya da beyanlı YEŞİL-SINIRLI) |
| `kapi` | 1 | KIRMIZI — en az bir kapı ısırdı |
| `kapi` | 2 | kullanım/girdi hatası (temiz hata, ham traceback değil) |
| `kapi` | 3 | **ölçüm yapılamadı, HÜKÜM YOK** (ölçüm yarıda kesildi · disk dolu · izin yok · beklenmeyen iç hata) |
| `derle` | 0 | iş **tamamlandı** ve kapı yeşil |
| `derle` | 1 | iş yapıldı ama kapı kırmızı → değişiklik geri alındı |
| `isir` | 0 / 1 / 2 / 4 | yukarıdaki `isir` bölümüne bak |

**Hem kırmızı hem kesilme varsa `kapi` 1 döner** — ölçülmüş bir kırmızı, eksik
kapsamdan daha acildir ve sarmalayıcının onu görmesi gerekir. Bulgunun tamamı
kesilmeden ibaretse 3 döner.

> **Buradaki sınır açıkça çizilidir:** beyanlı/yapısal kapsam boşluğu (git yok, henüz
> commit yok, `politika_gerekce`) exit **3 değil 0**'dır ve hüküm `YEŞİL (SINIRLI)`
> der. Yani `kapi && dagit`, kapsamı eksik bir projede dağıtım yapar. Bunu exit 3'e
> çevirmek her yeni projeyi ilk dakikasında durdururdu; bugünkü seçim bilinçlidir ve
> dördüncü tur denetçisine soruldu.

**Kırık boru (SIGPIPE):** `hafiza.py kapi | head` gibi sıradan bir kullanım
`BrokenPipeError` ham traceback'i üretiyordu — üstelik **çıktı boyutuna bağlı olarak**,
yani rapor kısa olduğunda görünmüyordu. İlk düzeltme `os._exit(0)` idi ve **üç yeni
yüksek kusur** doğurdu: kırmızı kapı `| head` ile 0 dönüyordu (sahte yeşil), `derle`
işin ortasında 0 dönüyordu (yarım durum "başarı"), ve `os._exit` `atexit`'i atladığı
için kilit sızıyordu. Doğru çözüm çıkış kodunu değiştirmek değil, kırık boruyu **yazma
katmanında yutmaktır**: `_KirikBoruyaDayanikliAkis` yazmayı `devnull`'a düşürür, komut
kendi işini bitirir ve **kendi hükmünü** verir.

> Bu, bu turun en pahalı dersidir: **bir düzeltmenin ne kapattığı değil, NE AÇTIĞI
> ölçülür.** `os._exit(0)` tek satırdı, bir HIGH bulguyu kapattı ve üç HIGH bulgu
> doğurdu.

**stderr de sarılır (v2.4.1).** İlk sarmalayıcı yalnız `sys.stdout`a takılmıştı; oysa
kodda sekiz ayrı `sys.stderr.write(` var ve bunlardan biri (`yol_on_kontrol`un hardlink
uyarısı) açıkça "işlem SÜRÜYOR" diyen bir NOT'tur. Ölçüldü: tüketicisi kapanmış bir
stderr'de `not` komutu exit 0 yerine **exit 2** veriyor ve fragmanı **hiç yazmıyordu** —
yani "raporla, durdurma" diyen bir uyarı komutu tümden iptal ediyordu. Aynı sınıf, öteki
akışta. Üstelik testler bunu göremiyordu: `t_y42`nin ilgili senaryoları `stderr=DEVNULL`
ile koşuyordu. **Ders: bir sınıfı kapattığını iddia eden test, sınıfın yaşadığı kanalı
kapatıyorsa hiçbir şey ölçmüyordur.**

---

## DOKTRİN: ÖNLEME → **GİZLENEMEZ KIL**

Dosya tabanlı bir hafıza sisteminde bazı hamleler **önlenemez**. Diske tam yetkisi
olan biri `.hafizarc`'ı silip yeniden `devral` koşabilir, zinciri sıfırlayabilir,
kendi çıpasını kurabilir. Bunu engellemeye çalışmak v2.4'te üç kez denendi:

1. Çıpayı `_CIPA.json`'a bağlamak → `rm _CIPA.json && kur` her şeyi akladı.
2. Çıpayı `.hafizarc`'a bağlamak → `rm .hafizarc && devral` her şeyi akladı; üstelik
   hata mesajının kendisi tarifi öğretiyordu.
3. Sabit yollu "yetim kurulum" kontrolü → üç ayrı yoldan atlatıldı **ve** meşru v1→v2
   geçişini tamamen kilitledi (`kur` "devral kullan" diyor, `devral` "yetim v2" diyor —
   kapalı döngü).

Kabul edilen doktrin: **engelleme, GÖRÜNÜR KIL.** `devral` artık tüm ağacı önceki
kurulum izleri için tarar (`_CIPA.json`, `_ZINCIR.jsonl`, `_KOVA.json`, `_KAYNAK*.md`,
`HAFIZA_*.md`, canlıdaki `gunluk/` kaynaklı bloklar), bulduklarını canlı hafızaya
kalıcı bir `ÇAPA DEVRİ` bloğu olarak **yedeklemeden önce** yazar (böylece blok çıpaya
girer; sonradan silinirse `[H1] KAYIP` ötçer) ve DEVİR halkasına `onceki_kurulum_izi`
alanı düşer.

Aynı ilke `mtime` sinyalleri için de geçerlidir: bir bulgu **kanıt taşımıyorsa** hüküm
vermez. `~` önekli zincir bulguları `cmd_kapi` içinde `O` (ÖLÇÜLEMEDİ) koluna gider,
`fail()` değil — çünkü "git kirli diyor" bir kanıt değildir (defterler `derle` sonrası
zaten kirlidir) ve aynı baytlarla yeniden yazılan bir dosya kapıyı haksız yere
kırmızıya düşürüyordu.

---

## CLI YOL KAPISI (v2.4)

`emekli --hedef`, `korunan --dosya`, `devral --canli` kullanıcı yolunu **doğrudan**
kabul ediyordu: `--hedef=../../../tmp/x.md` proje ağacının dışına dosya yazıyor,
`--dosya=/etc/passwd` ağaç dışını okuyup hash'liyordu. Tek tek sarmalamak yerine
sınıf **sınırda** kapatıldı: her CLI yol argümanı `cli_yol_coz()` kapısından geçer —
NUL baytı reddi, Windows `\` normalizasyonu, `realpath` ile kök karşılaştırması.
Ağaç dışına çıkan argüman **temiz hatayla** durur.

Yan etki olarak iki şey daha kapandı: `korunan` kayıtları artık **köke göreli** yolla
saklanır (mutlak yerel yol sürüm kontrolüne sızıyor ve projeyi taşınamaz hâle
getiriyordu; aynı dosya için 4 ayrı kayıt oluşuyordu), ve `emekli --hedef` **canlı
dosyanın kendisi** olamaz (olabildiğinde `_TASINMA.jsonl` yalan kaydediyordu).
