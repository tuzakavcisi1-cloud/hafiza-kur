---
name: hafiza-kur
description: >-
  Bir projeye kalıcı HAFIZA + DOSYALAMA + ARŞİVLEME düzenini kurar ve işletir (v2).
  Kullanıcı "hafıza düzenini kur", "arşivleme sistemi kur", "bu projeye hafıza kur",
  "dosya düzeni kur", "proje hafızası", "canlı hafıza", "karar günlüğü", "ADR",
  "karar kaydı", "emekliye ayır", "hafızayı derle", "hafıza kapısı", "kapıyı koş",
  "devir notu", "oturum protokolü", "dosyalar şişti", "hangi dosya nereye",
  "eski sürümleri arşivle" dediğinde YA DA yeni bir proje/klasör bağlanıp orada
  `.hafizarc` / `PROJE_HAFIZA.md` bulunmadığında DEVREYE GİR. Ayrıca her oturum
  AÇILIŞINDA ve KAPANIŞINDA protokolü uygular. İlke: hiçbir satır silinmez, taşınır;
  "kaybolmadı" bir iddia değil TEST SONUCUDUR; ölçülmeyen şeye "temiz" denmez.
---

# Hafıza ve Arşivleme Düzeni — v2

Bu skill bir projeye, **büyüdükçe bozulmayan** bir hafıza + dosyalama düzeni kurar ve
onu her oturumda işletir. İki kaynaktan doğdu: sahada denenmiş bir sistem (ölçülen
bütünlük, kendi kapısını koşan araçlar, mutant kanıtı) ve sektörün olgun pratikleri
(ADR, saklama planı, log-compaction, fragman modeli, checkpoint).

---

## 0. ÜÇ CÜMLELİK FELSEFE

1. **LOG ile DURUM ayrıdır.** Log tam ve ekle-only'dir, nadiren okunur. Durum kompakt
   ve türetilmiştir, sürekli okunur.
2. **Hiçbir satır SİLİNMEZ, TAŞINIR** — byte-birebir, beyanla, ve taşıyan araç kendi
   kapısını koşar; kapı kırmızıysa taşımayı geri alır.
3. **"Kaybolmadı" bir iddia değil TEST SONUCUDUR.** Kapı ölçer; ölçemediğine
   "ÖLÇEMİYORUM" der — sessiz PASS yoktur.

---

## 1. HANGİ KADEME?

Önce bunu belirle, sonra kur.

| | **HAFİF** | **KAPILI** |
|---|---|---|
| Ne zaman | Kod/depo olmayan işler: hukuk dosyası, strateji, araştırma, yazı | Depo/git olan projeler; uzun ömürlü, çok oturumlu işler |
| İçerik | Klasör düzeni + canlı hafıza + karar dosyaları + saklama planı + oturum protokolü | Hepsi + `hafiza.py` motoru + H0–H15 kapıları + mutant kanıtı |
| Zorlayıcı | İnsan/ajan disiplini | Otomatik kapı + git hook |
| Kurulum | Şablonları elle aç (`references/sablonlar.md`) | `python hafiza.py kur --kok=<dizin>` |

Kararsızsan: **kod varsa KAPILI, yoksa HAFİF.** Hafif'ten Kapılı'ya sonradan geçilebilir
(aynı dosya adları kullanılır).

---

## 2. KURULUM (KAPILI) — `kur` mu `devral` mı?

| Proje | Komut |
|---|---|
| Yeni / boş | `kur` |
| İlerlemiş, hafıza sistemi **yok** | **`devral`** |
| İlerlemiş, **başka bir hafıza sistemi var** | **`devral`** |

> ⛔ **Mevcut hafıza sistemi olan bir projede `kur` KOŞMA.** Ölçüldü: zinciri kırar,
> ikinci çıpa doğurur ve eski sistemin dizin kapısını kırmızıya düşürür.
> `devral` mevcut sisteme dokunmaz, v2'yi ayrı ad alanında (`arsiv/hafiza/v2`) kurar,
> yapılandırmayı diskteki gerçekten türetir ve canlı dosyayı önce yedekler.
> Ayrıntı: `references/devir.md`.

```
python araclar/hafiza/hafiza.py devral      --kok="<proje kökü>" --ad "<Proje Adı>"
python araclar/hafiza/hafiza.py bloklastir  --kok="<proje kökü>"            # kuru prova
python araclar/hafiza/hafiza.py bloklastir  --kok="<proje kökü>" --uygula   # geriye dönük blok
```

`bloklastir`, devralınan projedeki **mevcut** bölümleri geriye dönük blok işaretine alır —
böylece sistem "bugünden itibaren" değil, eski içerik için de çalışır. İçeriğe dokunmaz,
yalnız görünmez işaret satırı ekler; kural evi bölümlerini ve karar günlüğünü **asla**
bloklamaz; kapı kırmızıysa işlemi geri alır.

### Sıfırdan kurulum

```
# 1) motoru projeye kopyala
#    <proje>/araclar/hafiza/hafiza.py

# 2) kur (idempotent — var olanı BOZMAZ)
python araclar/hafiza/hafiza.py kur --kok="<proje kökü>" --ad "<Proje Adı>"

# 3) kapıyı koş — YEŞİL görmeden işe başlama
python araclar/hafiza/hafiza.py kapi --kok="<proje kökü>"

# 4) kapının gerçekten ısırdığını KANITLA (bir kereye mahsus, sonra her büyük değişimde)
python araclar/hafiza/hafiza.py isir --kok="<proje kökü>"
```

`kur` şunları üretir: `.hafizarc` · `PROJE_HAFIZA.md` · `CLAUDE.md` · `SAKLAMA_PLANI.md` ·
`KONULAR.md` · `kararlar/` · `gunluk/` · `arsiv/hafiza/` (çıpa + defterler + zincir) ·
`arsiv/<tür>/`.

Kurulumdan sonra **`.hafizarc`'ı projeye göre ayarla**: `tavan_kb`, `bayatlik_gun`,
`arsiv_turleri`, `kanonik_artefakt` (varsa tek doğru sürüm dosyası deseni).

---

## 3. GÜNLÜK KULLANIM — dört komut

```
hafiza.py not    --konu <konu> --tur durum|sonraki|karar|bulgu|ders|devir --metin "..."
hafiza.py derle
hafiza.py karar  --baslik "..." [--yerine <no>]
hafiza.py emekli <bas>-<son> --not "neden"
```

**Yeni bilgi doğrudan `PROJE_HAFIZA.md`'ye YAZILMAZ.** Canlı hafıza bir *snapshot*'tır.
Bilgi önce `not` ile bir fragmana yazılır, sonra `derle` onu canlıya işler ve fragmanı
arşive taşır. Bunun üç kazancı var: paralel oturum/alt-ajan çakışması biter, her canlı
bloğun kaynağı bellidir, ve "bu tur hiçbir şey kaydedilmedi" ölçülebilir hale gelir.

---

## 4. OTURUM PROTOKOLÜ (her oturumda, istisnasız)

### Açılış
1. `PROJE_HAFIZA.md`'yi baştan sona oku. **Sohbet geçmişini hafıza sayma.**
2. `hafiza.py kapi` koş. **YEŞİL görmeden işe başlama.** Kırmızıysa önce onu çöz.
3. `git status` temiz mi bak.
4. `SONRAKİ ADIM`'daki ilk işten devam et.
5. Kod/içerik yazmadan **önce** tasarımı işaretlenebilir şıklarla sun, kapsamı onaylat.

### Sırasında
6. Her büyük adım bitiminde `hafiza.py not` ile fragman yaz (checkpoint). Adımı
   **yarıda kesme**; ölçüm ve karar yalnız adım aralarında alınır.
7. Kalıcı bir kural doğduysa evi `SABİT ÇERÇEVE`'dir — başka bölüme yazma (H7 yakalar).
8. Geri döndürmesi zor bir karar aldıysan `hafiza.py karar` ile ADR aç; canlı hafızaya
   yalnız **link** koy, gerekçeyi ADR'de yaz.

### Kapanış
9. `hafiza.py derle` → `hafiza.py kapi`.
10. Tavan zorlanıyorsa `hafiza.py emekli` ile eski blokları arşive taşı.
11. Kullanıcı yeni oturuma geçeceğini söylediyse **tek seferde kopyalanabilir DEVİR
    NOTU**nu kod bloğu içinde yaz: proje/klasör · aktif sürüm · son yapılan · yarım kalan ·
    sıradaki ilk iş (adım adım) · açık kararlar/blokerler · ilgili dosyalar · uyarılar.

---

## 5. KAPILAR — ne ölçülüyor

`H0` çıpa (snapshot SHA + halka zinciri) · `H1` bütünlük (kayıp satır yok) ·
`H1-KOVA` yerleşim (canlıda olması gereken canlıda) · `H2` şişme (tavan) ·
`H3` zorunlu bölümler · `H4` ölü bağlantı · `H5` sürüm tekilliği ·
`H6` arşiv dizini çift yönlü · `H7` kural yerleşimi · `H8` korunan bloklar ·
`H9` git izlenirliği · `H10` konu tekilliği (anahtar bazlı sıkıştırma) ·
`H11` karar bütünlüğü (ADR) · `H12` bayatlık ve sapma · `H13` saklama planı ·
`H14` disiplin (proje ilerledi mi, hafıza ilerledi mi) ·
`H15` **politika** (kapıların kendisi gevşetildi mi) ·
`H-LINK` dosya kimliği (defterler proje ağacının dışında da adlandırılmış mı).

Ayrıntı ve her kapının **neden var olduğu**: `references/kapilar.md`.

> **Bağımsız denetim (28 Tem – 1 Ağu 2026):** bu skill **üç** bağımsız denetçiye verildi
> ve **on iki tur** kırılmaya çalışıldı. İlk iki denetçi 13 + 12 + 32 bulgu getirdi ve
> ikisinin de son kararı **KUR** oldu. Üçüncü denetçi üç tur koştu; son turunda (v2.3.0)
> **DÜZELT** dedi (2 HIGH + 4 MEDIUM + 5 LOW). Onbir bulgunun tamamı v2.4.0'da kapatıldı;
> kapatma turunun kendisi iki iç düşman turuyla denendi ve **düzeltmelerin ürettiği
> kusurlar** çıktı — onlar da kapatıldı. Paketten sonra iki iç denetim turu daha koştu ve
> **dört kusur daha** buldu: P-1 (commitsiz git deposunda H9 **yanlış teşhis**),
> **A-1** (`kur`/`devral` tek-yazar kilidini hiç almıyordu — v2.4'ün canlıya yazan yeni
> yolu kilit disiplininin dışındaydı), **A-2** (belgeye yazdığım çıkış kodu sözleşmesi
> kodda yoktu), **A-3** (kırık boru yalnız stdout'ta yutuluyordu). Dördü de v2.4.1'de
> kapatıldı. Mutant sayısı 15 → 29 → 35 → **36**; senaryo kanıtı 0 → 32 → **58**;
> ham traceback avında **2 330 senaryo, 0 çökme**.
>
> ⚠️ **v2.4.1 dördüncü tur denetimini BEKLİYOR.** Üçüncü denetçinin onayı gelmeden bu
> skill "denetimden geçti" diye sunulmaz. Ayrıntı ve düzeltmelerin *ürettiği* kusurlar
> dâhil tam defter: `references/denetim-yaniti.md`.
>
> **Tek yazar kilidi:** yazan komutlar `arsiv/hafiza/.kilit` alır (`O_EXCL`). İki oturum
> aynı anda `derle` koşarsa canlı hafızada kayıp güncelleme oluyordu; artık ikincisi
> temiz hatayla bekletilir. Kilit **sahiplidir**: bırakırken inode + pid doğrulanır,
> başkasınınki silinmez. Bayat kilit silinmez, **teşhis edilir** ("pid YAŞIYOR" /
> "pid BAYAT, silmen güvenli" / "ÖLÇÜLEMEDİ") — kararı insan verir.
>
> **Kör kapı protokolü:** bir kapının var olması, ısırdığı anlamına gelmez.
> `hafiza.py isir` her kapı için bilerek bir mutant kurar ve yakaladığını kanıtlar;
> temiz sürümde yanlış-pozitif olmadığını da gösterir. **Isırmayan kapının "temiz"
> hükmü geçersizdir.** H9'un mutantı yoktur (mutant kopyasına `.git` alınmaz) — bu
> boşluk raporda açıkça yazılır, gizlenmez.
>
> **Sabotaj sınaması (her yeni test için zorunlu):** testin ölçtüğünü iddia ettiği
> korumayı devre dışı bırak; mutant **KAÇTI** demeli. Demiyorsa o test kendi sınıfını
> değil komşu bir sınıfı ölçüyordur — v2.4'te iki test bu süzgeçte elendi.
>
> **`isir` çıkış kodları:** `0` hepsi ısırdı · `1` **KAPI KÖR** · `2` ölçülemeyen mutant
> (testin ön-koşulu yok — kapı hükmü DEĞİL) · `4` temiz sürüm zaten FAIL. Sayı bağlamsız
> beyan edilmez: `derle` koşulmuş projede **36/36**, taze `kur` projesinde
> **34/34 + 2 KURULAMADI** (ikisi de sağlıklı). Çıktıda mutant başına `KURULAMADI`,
> özet satırında aynı şey için `SINANMADI` yazıyor — iki kelime tek anlamdadır.

---

## 6. PAZARLIKSIZ KURALLAR

- **Elle kopyala-yapıştır ile satır taşıma YASAK.** Yeniden yazım riski taşır; araç
  byte-birebir taşır ve beyan eder.
- **Gerekçesiz mühür/koruma/emeklilik YASAK.** Her bilinçli değişiklik nedenini yazar.
- **Kalıcı kural emekli edilemez.** Evi `SABİT ÇERÇEVE`'dir; araç bunu önceden reddeder.
- **Kabul edilmiş bir ADR düzenlenmez.** Yalnız `durum` alanı güncellenir; fikir
  değiştiyse yeni ADR açılır ve eskisi "yerine geçildi" olur.
- **Konu sözlüğü dışında blok doğmaz.** Yeni konu açmak serbest, silmek yasak.
- **Ölçülmeyene "temiz" denmez.** `ÖLÇÜLMEDİ` yaz; nasıl ölçüleceğini de yaz.
- **Boş tur yoktur.** Çalışıldıysa fragman yazılır; `derle` fragmansız çalışırsa HATA verir
  (bilinçli boş tur için `--bos-serbest`).
- **`SAKLAMA_PLANI.md`'de karşılığı olmayan dosya türü üretilmez** — önce plana satır ekle.

---

## 7. NE ZAMAN NE YAPILIR — hızlı tablo

| Durum | Yapılacak |
|---|---|
| Yeni bilgi/durum çıktı | `hafiza.py not` (fragman) → oturum sonunda `derle` |
| Geri döndürmesi zor karar alındı | `hafiza.py karar` → ADR'yi doldur → `durum: kabul` |
| Eski karardan vazgeçildi | `hafiza.py karar --yerine <no>` (eskisi silinmez) |
| Canlı hafıza tavanı zorluyor (H2) | `hafiza.py emekli <bas>-<son> --not "..."` |
| Aynı konuda iki blok uyarısı (H10) | Eskisini emekli et — anahtar başına tek blok |
| "Canlı bayat" uyarısı (H12) | `hafiza.py derle` |
| Tur/sürüm kapandı | Belgeyi `arsiv/<tür>/` altına **taşı** (silme) |
| Bir protokol bloğu bilinçli değişti | `hafiza.py korunan ... --gerekce "..."` |
| Defterlerden biri bilinçli değişti | `hafiza.py muhur "gerekçe"` |
| Yeni oturuma geçiliyor | `derle` → `kapi` → devir notu |
| Devir sonrası eski bölümleri de sisteme almak | `bloklastir` (önce kuru prova) |
| `[H14]` proje ilerledi, hafıza ilerlemedi | Çalışıldı ama kayıt bırakılmadı → `not` + `derle` |
| İlerlemiş bir projeye ilk kez uygulanıyor | `devral` (asla `kur`) → triyaj raporunu oku |

---

## 8. REFERANSLAR

- `references/denetim-yaniti.md` — bağımsız denetimin bulguları ve nasıl kapatıldıkları
- `references/devir.md` — ilerlemiş/mevcut sistemi olan projeye uygulama (`devral`)
- `references/duzen.md` — klasör düzeni, adlandırma, hangi dosya nereye, kök temizliği
- `references/kapilar.md` — H0–H15'in her biri: ne ölçer, neden var, nasıl kırılır
- `references/protokol.md` — oturum açılış/kapanış, devir notu, çok-ajan kullanımı
- `references/sablonlar.md` — BETİKSİZ kullanım için elle açılacak dosya şablonları
- `scripts/hafiza.py` — taşınabilir motor (yalnız Python stdlib; Windows/macOS/Linux).
  v2.4.1 · 4 394 satır · SHA256 `738849C086512C7485048C58570EEDCA045E21550EF9BE357197FF577126F300`
- `scripts/t_y3.py` — temiz-hata kanıtları (bozuk girdide ham traceback yok): 20 senaryo
- `scripts/t_y42.py` — davranış kanıtları (kapı mutantıyla ölçülemeyenler): 58 senaryo

---

## 9. SINIRLAR (dürüstlük bölümü — bunları müşteriye de söyle)

- **Halka zinciri depo-içidir.** Tutarlı biçimde birden çok dosyayı düzenleyen bir
  aktörü tek başına durduramaz; gerçek çözüm git gibi içerik-adresli bir tarihtir.
  Zincirin yaptığı, maliyeti bir hamleden N tutarlı hamleye çıkarmaktır.
- **Canlı dosya fragmanlardan tam otomatik yeniden üretilemez.** Serbest metinde bu
  garanti kurulamaz. Onun yerine **sapma tespiti** vardır (H12): bir konuda canlı bloktan
  daha yeni bir kayıt varsa kapı uyarır. Garanti değil, alarm.
- **Disiplin nihayetinde insana/ajana bağlıdır.** Fragman yazılmazsa sistem boş döner.
  Git hook bunu kısmen zorlar, tamamen değil.
- **Uzun hafıza her zaman iyi değildir.** Ölçümler, girdi uzadıkça model başarımının
  düştüğünü gösteriyor. Bu yüzden tavan vardır ve ayrıntı canlıda değil `kararlar/` ile
  `arsiv/` içinde yaşar: canlı dosya **yol taşır, metin taşımaz**.
- **Baseline satırını düzeltmenin araç-destekli yolu yok.** Şablondaki bir yazım hatasını
  düzeltmek H1'i kırar; yol ya `_DUZELTMELER.json`'a beyan + `muhur`, ya `emekli`.
  Bilinçli olarak katı bırakıldı: otomatik bir "baseline düzeltme" komutu, kapının
  engellemek için var olduğu şeyi kolaylaştırırdı.
- **Hardlink engellenmez, raporlanır.** Bir defterin proje dışında da adı varsa
  (`cp -al`, `rsync --link-dest` yedeği) kapı `[H-LINK]` der ama komutlar çalışmaya
  devam eder — yedek almak bir ihlal değildir, ama o dosyalara yazmak dışarıdaki adı da
  değiştirir ve bunu bilmelisin.
- **H9'un otomatik mutantı yok** (mutant kopyasına `.git` alınmaz); elle sınanır. H14'ün
  git kolu **M-H14b** ile sınanır (mutant kendi deposunu kurar).
- **Beyanlı gevşeklik gerçek bir kaçış deliğidir.** `politika_gerekce` ile bir kapıyı
  kapatabilirsin; kapı kırmızı yanmaz. Ama hüküm satırı `YEŞİL (SINIRLI) — N ŞEY
  ÖLÇÜLMEDİ` der ve gerekçe zincire girer. Gizlenemez, ama **kullanılabilir** — bunu
  bilerek böyle bıraktık: kaçış yolu olmayan kapı, kırılan kapıdır.
- **Yeniden çapalama ENGELLENEMEZ, yalnız GÖRÜNÜR KILINIR.** `.hafizarc`'ı silip
  `devral` koşan biri her zaman yeni bir başlangıç noktası yaratabilir — dosya tabanlı
  bir şemada bunun matematiksel bir çaresi yok. Üç kez engellemeye çalışıldı; üçü de ya
  atlatıldı ya meşru v1→v2 geçişini kilitledi. Bugünkü çözüm: `devral` tüm ağacı önceki
  kurulum izleri için tarar, bulduklarını canlı hafızaya kalıcı bir `ÇAPA DEVRİ` bloğu
  olarak yazar (silinirse `[H1] KAYIP` ötçer) ve halkaya `onceki_kurulum_izi` düşer.
  **Aklama mümkündür ama sessiz değildir.**
- **Kilidi ALAN komut kümesi kapsamdır, tek yol değildir.** v2.4'te `devral`a canlıya
  yazan yeni bir yol eklendi ve kilit alınmadı; ölçüldü, v2.4.1'de kapatıldı. `devral`
  ayrıca **ağaçtaki her `.kilit`e** bakar, çünkü kilidini yeni ad alanında alır ve eski
  ad alanındaki bir yazarı göremezdi. Kilit inode kimliği yarış penceresini **daraltır,
  kapatmaz** — ölçüldü: aynı dizinde silinen kilidin inode'u 20/20 yeniden kullanılıyor.
- **Kilit bayatsa araç silmez, teşhis eder.** Çökmüş bir süreçten kalan kilidi silme
  kararı insanındır; araç yalnız "pid yaşıyor mu" sorusunu cevaplar. 1 saatten eski
  kilitlerde "pid yeniden kullanılmış olabilir" uyarısı düşülür — yani teşhis de
  kesinlik iddia etmez.
- **`kapi` ölçemediğini exit 3 ile söyler — ama YALNIZ ölçüm çöktüğünde.**
  0 yeşil · 1 kırmızı (ölçülmüş en az bir kapı ısırdı) · 2 kullanım/girdi hatası
  (temiz hüküm) · **3 ölçüm yapılamadı, HÜKÜM YOK** (ölçüm yarıda kesildi · disk dolu ·
  izin yok · beklenmeyen iç hata). Hem kırmızı hem kesilme varsa **1** döner: ölçülmüş
  bir kırmızı, eksik kapsamdan daha acildir.
  **Ama dikkat — beyanlı/yapısal kapsam boşluğu exit 3 DEĞİLDİR:** git yok, henüz commit
  yok, `politika_gerekce` ile gevşetilmiş bir kapı → hüküm `YEŞİL (SINIRLI)` ve çıkış
  kodu **0**'dır. Bu bilinçli: beyanlı gevşeklik kapıyı kırmızı yakmaz. Sonucu şudur:
  `kapi && dagit` diyen bir CI, kapsamı eksik bir projede dağıtım yapar. Kapsamı da
  zorlamak istiyorsan çıktıdaki `?` satırlarını ayrıca kontrol etmelisin. Bu ayrımın
  doğru yerde çizilip çizilmediği dördüncü tur denetçisine açıkça soruldu.
- **Büyük hafızada kapı maliyeti doğrusaldır.** 300 000 satırda `kapi` ASCII içerikte
  ~3,5 sn, **Türkçe içerikte ~6 sn** sürer (v2.3.0'da sırasıyla ~10 ve ~12 sn idi).
  İki kolun ayrı ölçülmesinin sebebi şu: hızlandırma ASCII hızlı yoluna dayanıyor, yani
  yalnız ASCII ile ölçmek düzeltmenin kendi lehine kurulmuş bir sınavdır — bu araç
  Türkçe hafıza tutuyor. Tavan (H2) zaten bunu 60 KB civarında tutar; ama `devral` ile
  devralınan dev bir hafızada ilk koşum yavaştır — bu bir hata değil, ölçülmüş maliyet.
