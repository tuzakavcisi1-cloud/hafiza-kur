# İlerlemiş Bir Projeye Uygulama — `devral`

## 1. `kur` mu, `devral` mı?

| Proje | Komut | Neden |
|---|---|---|
| Yeni / boş | `kur` | Kurulacak bir şey yok, sıfırdan doğar |
| İlerlemiş, ama hafıza sistemi **yok** | `devral` | Yapılandırma diskteki gerçekten türetilsin; ilk gün kırmızı seli olmasın |
| İlerlemiş, **başka bir hafıza sistemi var** | `devral` | Mevcut sisteme dokunulmaz; v2 ayrı ad alanında yaşar |

**Mevcut sistemi olan bir projede `kur` KOŞMA.** Ölçüldü, üç somut hasar veriyor:
zincir kırılıyor (v2 halkası v1 zincirine ekleniyor), ikinci çıpa doğuyor, ve yeni bir
arşiv dosyası eski sistemin dizin kapısını kırmızıya düşürüyor.

---

## 2. `devral` ne yapar

```
python araclar/hafiza/hafiza.py devral --kok="<proje kökü>" --ad "<Proje Adı>"
```

**Keşif (yazmadan önce ölçer):**
- Canlı hafıza dosyasını bulur (yoksa oluşturur).
- Mevcut bir hafıza sistemi var mı bakar (`_KAYNAK*`, `_ZINCIR.jsonl`, `HAFIZA_*.md`).
  Varsa v2 için ayrı bir ad alanı seçer: `arsiv/hafiza/v2`.
- Canlı dosyadaki **gerçek** bölüm başlıklarını süslemeleriyle birlikte okur
  (`## 📚 ARŞİV DİZİNİ` gibi) ve `zorunlu_bolumler`e onları yazar.
- `arsiv/` altındaki **gerçek** klasörleri arşiv türü olarak alır.
- Kural işareti zaten geçen bölümleri `kural_evi_bolumleri` olarak önerir — böylece ilk
  koşum bir H7 seline dönmez.
- Tavanı mevcut boyutun %20 üstünde başlatır (ilk gün H2 kırmızı olmasın).
- Devralınan eski `HAFIZA_*.md` dosyalarını `ek_arsiv_dosyalari`na yazar — böylece H1
  bütünlük hesabı onları da sayar.

**Yazım (yıkıcı değil):**
- Canlı dosyayı önce `_DEVIR_ONCESI_<tarih>.md` olarak **yedekler**.
- Canlı dosyaya tek ekleme yapar: `ARŞİV DİZİNİ` bölümüne kendi işaretli alt bloğu
  (`<!-- v2-arsiv-dizini -->` … `<!-- /v2-arsiv-dizini -->`). Senin kendi dizin
  satırlarına **dokunmaz**.
- v2 ad alanında çıpayı, defterleri ve **taze bir zinciri** kurar. Eski sistemin
  hiçbir dosyasına yazmaz.

**Rapor:**
- Kapıyı salt-okuma koşar ve triyajlı bir devir raporu basar: hangi bulgu yapılandırma,
  hangisi gerçek.

---

## 3. Devirden sonra ilk gün — beklenen tablo

**İlk koşumda kırmızı görmek normaldir.** Kapılar mevcut dağınıklığı ölçüyor; hasar
raporlamıyorlar. Sıra:

1. **`[H4]` bulgular** — hafıza olmayan bir dosyaya gönderiyor. Ya yolu düzelt ya satırı
   güncelle. `TAŞINMIŞ (ölü değil)` notları **bulgu değildir**: dosya arşivde bulundu.
2. **`[H7]` bulgular** — kalıcı bir kural rotasyona giren bölümde yaşıyor. İki çıkış:
   ya kuralı `SABİT ÇERÇEVE`'ye taşı, ya o bölümü `.hafizarc`'ta `kural_evi_bolumleri`ne
   ekle. Birincisi doğru, ikincisi hızlı.
3. **`[H10]`** — bloklara `konu` etiketi eklerken `KONULAR.md` sözlüğüne de ekle.
4. **`[H13]`** — plansız seri varsa `SAKLAMA_PLANI.md`'ye satır ekle.
5. Kapı yeşillenince `isir` koş: kapıların gerçekten ısırdığını kanıtla.

Yeşil olmadan `emekli` ve `derle` **koşma** — ikisi de kapıyı kendi koşar ve kırmızıda
işi geri alır; boşuna uğraşmış olursun.

---

## 4. İki sistem yan yana yaşarken

Devir sonrası eski sisteminin kapısı (varsa) çalışmaya devam eder; v2 onun dosyalarına
dokunmaz. Bu geçiş dönemi için iki kural:

- **Tek yazıcı ilkesi.** Bir dosyaya iki sistem birden yazmaz. Devirden sonra canlı
  hafızayı v2 yönetir; eski araçlarla ona yazma.
- **Emeklilik tek yerden.** Devirden sonra emekli edilen satırlar v2'nin arşivine gider.
  Eski arşiv dosyaları okunur ama yazılmaz (`ek_arsiv_dosyalari` salt-okuma sayılır).

Eski sistemi tamamen kapatmaya karar verdiğinde: eski kapıyı doğrulama zincirinden
çıkar, eski defterleri `arsiv/` altında **bırak** (silme), ve `.hafizarc`'taki
`hafiza_dizini`'ni sadeleştirmek istersen dosyaları taşımadan önce çıpayı yeniden kur.

---

## 5. Ölçülmüş örnek

Gerçek bir projenin (54,5 KB, 170 satır, 11 bölüm, emoji başlıklı, mevcut v1 sistemi olan)
canlı hafızası bir replikaya taşındı ve `devral` koşuldu:

| Ölçüm | Sonuç |
|---|---|
| v1 dosyaları (çıpa, zincir, 4 defter) | **MD5 birebir korundu** — hiçbirine dokunulmadı |
| v1 `arsiv/hafiza/` içeriği | yeni dosya eklenmedi; yalnız `v2/` alt klasörü doğdu |
| Canlı hafızada değişiklik | **6 satır**: yalnız işaretli v2 dizin alt bloğu (yedek alındıktan sonra) |
| H0, H1, H2, H3, H6, H7, H10–H13 | ilk koşumda **yeşil** (yapılandırma diskten türetildiği için) |
| H4 | replikada 19 bulgu — **hepsi replika artefaktı**; dosyaların 19/19'u gerçek projede mevcut (8'i kökte, 11'i arşiv/alt klasörlerde → "TAŞINMIŞ" notu) |

Yani bu profildeki bir projede devir, canlı hafızaya altı satır ekleyip geri kalan her
şeyi olduğu yerde bırakıyor.

---

## 6. Geriye dönük tamamlama — `bloklastir`

`devral` tek başına sistemi **bugünden itibaren** çalıştırır: yeni yazdıkların bloklu
doğar, mevcut bölümler bloksuz kalır. Bu, anahtar bazlı sıkıştırmanın (H10) ve sapma
alarmının (H12) eski içeriğe uygulanmaması demektir.

`bloklastir` bu boşluğu kapatır:

```
hafiza.py bloklastir              # KURU PROVA — hiçbir şey yazılmaz, plan gösterilir
hafiza.py bloklastir --uygula     # uygular
```

**Ne yapar:** her uygun bölümün başına ve sonuna görünmez bir işaret satırı **ekler**.
Konu adını başlıktan türetir, `KONULAR.md`'ye yazar, eklenen satırları
`_YENI_SATIRLAR.txt`'ye beyan eder (çıpa sıfırlanmaz), sonra kapıyı koşar.

**Ne yapmaz:** hiçbir satırı silmez, taşımaz, yeniden yazmaz. İçerik byte-birebir aynı kalır.

**Asla bloklamadığı bölümler:** kural evi (`SABİT ÇERÇEVE`, `KIRMIZI ÇİZGİLER`, başlığında
`KURAL`/`PROTOKOL`/`TALİMAT`/`DEĞİŞMEZ`/`ZORUNLU`/`İLKE`/`SINIR` geçen her bölüm),
`KARAR GÜNLÜĞÜ` (kronolojik, ekle-only) ve `ARŞİV DİZİNİ` (üretilen). Gerekçe: bloklamak
o bölümü sıkıştırmaya açar; bir gün aynı konuda yeni blok gelirse **eski blok arşive
taşınır** — kalıcı kural için bu kabul edilemez. Kasıtlı olarak fazladan atlar:
gereksiz atlamak zararsız (bölüm olduğu gibi kalır), gereksiz bloklamak tehlikeli.

**Güvenlik ağı:** önce yedek (`_BLOKLASTIRMA_ONCESI_<tarih>.md`), sonra kapı; kapı
kırmızıysa **her şey geri alınır**. Bu bizzat ölçüldü: bir denemede H14 kırmızı yandı,
işlem geri alındı ve dosya byte-birebir eski hâline döndü.

**Ölçülmüş sonuç (gerçek hafıza dosyası, 11 bölüm):** 4 bölüm bloklandı, 7 bölüm atlandı
(5'i kural evi, 2'si kapalı bölüm). İşaret satırları çıkarıldığında içerik **birebir aynı**
(179 satır = 179 satır). Kapı yeşil, 15/15 mutant ısırıyor.

**Granülerlik uyarısı:** bloklama bölüm düzeyindedir. Bir bölüm çok geniş bir konuyu
kapsıyorsa, o konuda küçük bir güncelleme geldiğinde **bölümün tamamı** arşive taşınır
(veri kaybı değil — byte-birebir arşive gider — ama canlı dosyadan çıkar). Bölümlerin
dar olması işine gelir; gerekiyorsa uygulamadan önce bölümleri böl.
