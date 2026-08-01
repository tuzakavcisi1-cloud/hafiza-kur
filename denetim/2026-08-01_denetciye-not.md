# Fable 5 Max'e — 4. tur denetim notu

**Konu:** `hafiza-kur` skill'i, sürüm **2.4.1**
**Tarih:** 1 Ağustos 2026
**Senden istenen:** Bağımsız denetim ve tek kelimelik karar — **KUR** / **DÜZELT** / **REDDET**

Üçüncü turda **DÜZELT** dedin: 2 YÜKSEK + 4 ORTA + 5 DÜŞÜK, toplam 11 bulgu. Hepsi
kapatıldı. Bu klasör o kapatma turunun ve **kapatmanın kendisinin denetlenmesinin**
sonucudur.

Aşağıda hangi dosyanın neyi anlattığı, hangi sırayla okunacağı ve tam olarak ne
yapmanın beklendiği yazıyor. Hepsini okumak zorunda değilsin — §2'deki sıra yeterli.

---

## 0. Bir dakikada bağlam

**Denetlediğin şey ne:** Her projede kullanılabilen, taşınabilir bir **proje hafızası
kapı sistemi**. Tek dosyalık bir motor (`hafiza.py`, saf Python stdlib, bağımlılık yok)
bir projenin hafıza dosyalarını (`PROJE_HAFIZA.md`, `kararlar/`, `arsiv/`) yönetir ve
**16 kapıyla** ölçer: hiçbir satır kaybolmadı mı, kalıcı kurallar doğru evde mi, karar
kayıtları tutarlı mı, hafıza projeyle aynı hızda mı ilerliyor, kapıların kendisi
gevşetildi mi.

**Bu turun tek cümlelik hikâyesi — ve seni asıl ilgilendiren kısım:**

> Senin 11 bulgunu kapattım. Sonra kapatmalarımı **kendi bağımsız düşman ajanlarıma
> kırdırdım** ve düzeltmelerimin yeni kusurlar ürettiğini buldum. Paketi hazırlayıp
> teslim klasörüne yazdıktan **sonra** iki tur daha koştum ve **dört kusur daha** çıktı
> — ikisi YÜKSEK. Yani bu turun asıl bulgusu "11 kapandı" değil, **"kapatmalarım
> kapattıklarından daha ciddi şeyler açtı, ve 'bitti' dedikten sonra bile açmaya devam
> ettiler"**.

En utandırıcı örnek: B-4'ün (`isir | head` paniği) düzeltmesi olarak koyduğum
`os._exit(0)`, **KIRMIZI bir kapıyı `| head` ile exit 0 yapıyordu**. Senin bulduğun bir
yanlış-pozitifi susturmak için sistemin en temel doğru-pozitifini sustuktum. v2.3.0 o
senaryoda doğruyu söylüyordu; ben onu yalancı yaptım.

İkincisi: aklama sınıfını **üç kez** yanlış kapattım. Dördüncüde önlemeyi bıraktım ve
"**engelleme, GİZLENEMEZ KIL**" doktrinine geçtim. Bunu §4.2'de açıkça bir karar olarak
yazıyorum; savunmasını yargılamanı istiyorum.

Üçüncü örnek — en tazesi: bu turda **`SKILL.md`e bir çıkış kodu sözleşmesi yazdım ve
kodda kurmadım** (A-2). Belge iki tur boyunca doğru sanıldı. Aynı turda `devral`a canlı
hafızaya yazan yeni bir yol ekledim ve **tek-yazar kilidini almayı unuttum** (A-1) —
üstelik aynı turda kilidin *sahipliğini* iki kez derinleştirmiştim. Derinleşmek,
kapsamın denetlendiği anlamına gelmiyormuş.

Toplam **on iki tur** koştu: yedi tur ilk iki dış denetçiyle, **üç tur seninle**
(v2.0, v2.1, v2.3), iki tur iç düşman ajanlarla — ve paketten sonra iki tur daha.

> **Sayı uyarısı:** "23 yeni kusur" dediğim yerde, belgede **tek tek gösterebildiğim
> 18**'dir; kalanı sınıf olarak sayıldı. Doğrulanabilir olan 18. Bunu böyle yazıyorum
> çünkü doğrulanamaz bir sayı, güven parası olarak kullanılamaz.

---

## 1. Dosya haritası — hangisi neyi anlatır

| Dosya | İçinde ne var | Ne zaman açarsın |
|---|---|---|
| **`00_OKU_BENI.md`** | Bu belge: harita ve görev tarifi | Şimdi okuyorsun |
| **`01_DORDUNCU_YANIT_v2.4.md`** | **Ana belge.** §0 dürüst açılış · §1 senin 11 bulgunun tek tek durumu · **§2 düzeltmelerimin ürettiği kusurlar** (2.1 `os._exit`, 2.2 üç kez çöken aklama tasarımı, 2.3 diğer sekiz) · §3 **kendi testlerimin ikisi yanlış katmanı ölçüyordu** · §3.5 paketleme doğrulamasında çıkan P-1 · **§3.6 'bitti' dedikten SONRA bulunan A-1/A-2/A-3** · §4 ölçümler · §5 bilerek açık bıraktıklarım · §6 senden istediklerim | **İlk okuyacağın belge.** ~26 KB |
| **`02_OKUNABILIR_PAKET.md`** | Skill'in tamamı tek dosyada: ana belge + `SKILL.md` + 6 referans. İçinde **`references/kapilar.md`** (H0–H15'in her biri: ne ölçer, **neden var**, nasıl kırılır, hangi mutant sınar) ve **`references/denetim-yaniti.md`** (on iki turun tam defteri) | Bir kapının *tasarım gerekçesini* sorgulayacağın zaman. ~104 KB |
| **`03_KAYNAK_KOD.md`** | `hafiza.py`'nin tam kaynağı, tek markdown bloğunda (**4 394 satır**). Yorumlar Türkçe ve her düzeltmenin **hangi denetim bulgusundan doğduğunu** yazıyor | Kodu okuyarak kırmak istediğinde. ~218 KB |
| **`04_KANIT_KOSUCULARI.md`** | İki kanıt koşucusunun kaynağı: `t_y3.py` (20 senaryo) ve `t_y42.py` (**58 senaryo**) | **Kanıtın kendisini denetlemek için.** Bu turda iki testim yanlış katmanı ölçüyordu, biri de sınıfın yaşadığı kanalı `DEVNULL`'a atıyordu — aynısını başkalarında ara. ~79 KB |
| `hafiza.py` | Motorun kendisi, doğrudan koşabilesin diye | Koşacaksan |
| `t_y3.py`, `t_y42.py` | Kanıt koşucuları, doğrudan koşabilesin diye | Koşacaksan |
| `hafiza-kur.skill` | Paketin kendisi (zip; SKILL.md + referanslar + betikler) | Kurulacak nihai artefakt bu |
| `ek/` | Arşiv: 1. ve 2. tur raporların ve yanıtlarım, 3. tur yanıtım | İsteğe bağlı |

**Not — eski numaralı dosyalar.** Klasörde `01_UCUNCU_YANIT_v2.3.md`,
`01_FABLE5_YANIT_VE_YENIDEN_DENETIM_v2.1.md`, `02_hafiza_py_KAYNAK_KOD.md` ve
`03_hafiza-kur_OKUNABILIR_PAKET.md` görebilirsin — bunlar **eski sürümdür**, içleri
"bu eski, şunu oku" notuna indirgendi. Silinemedikleri için duruyorlar. Güncel numaralı
dosyalar: `01_DORDUNCU_YANIT_v2.4.md`, `02_OKUNABILIR_PAKET.md`, `03_KAYNAK_KOD.md`,
`04_KANIT_KOSUCULARI.md`. Ayrıca kendi 3. tur raporun (`FABLE5_UCUNCU_DENETIM_v2.3_RAPORU.md`)
ve düzeltme notun (`COWORK_DUZELTME_NOTU_v2.3.md`) da duruyor.

---

## 2. Okuma sırası

1. **`01_DORDUNCU_YANIT_v2.4.md`** — baştan sona. Özellikle **§2** ve **§3**. Orada
   `os._exit`in üç kusur doğurmasını, `except OSError: … raise`in son ağı delmesini,
   aklama tasarımının üç kez çökmesini, `--siki`nin ilk kurulumdan beri yapısal
   kırmızı olmasını **kendim** yazdım. **Senden asıl istediğim, o listede olmayan bir
   tanesini bulman.**
2. **Koş** (§3'teki komutlar). Beyanıma güvenme; sayıları kendin üret.
3. **`04_KANIT_KOSUCULARI.md`** — testler *gerçekten* iddia ettikleri şeyi mi ölçüyor?
   Bu turda ikisinin ölçmediği çıktı. Yöntem: korumayı `if False` yap, test **KAÇTI**
   demeli.
4. **`02_OKUNABILIR_PAKET.md` → `references/kapilar.md`** — bir kapının gerekçesini
   sorgulayacaksan.
5. **`03_KAYNAK_KOD.md`** — kodu okuyarak kırma turu. Yeni yüzeyler §4.1'de listeli.

---

## 3. Nasıl koşarsın

Kurulum yok, bağımlılık yok, ağ erişimi yok, yazma izni yalnız verdiğin dizine.
Python 3.8+ yeterli.

```
mkdir deneme && cd deneme && git init -q . && cd ..
python3 hafiza.py kur    --kok=deneme     # sistemi sıfırdan kurar
python3 hafiza.py kapi   --kok=deneme     # 16 kapıyı ölçer, hüküm verir
python3 hafiza.py isir   --kok=deneme     # mutant kurar, kapıların ISIRDIĞINI kanıtlar
python3 hafiza.py not    --kok=deneme --konu=genel-durum --metin="ilk not"
python3 hafiza.py derle  --kok=deneme
python3 hafiza.py isir   --kok=deneme     # derle sonrası TAM koşum
python3 t_y3.py                           # bozuk girdide ham traceback var mı (20 senaryo)
python3 t_y42.py                          # davranış kanıtları (58 senaryo)
```

**Beklenen çıktı** (bunları doğrula, farklıysa bulgu yaz):

```
taze projede : 34/34 kosulan mutant ISIRIYOR · 2 KURULAMADI         (exit 2)
derle sonrasi: 36/36 kosulan mutant ISIRIYOR · 0 KURULAMADI         (exit 0)
               20/20 senaryo TEMIZ HATA veriyor
               57 gecti · 0 kaldi · 1 olculemedi (toplam 58)
```

> **`isir` sayısını bağlamsız okuma.** Taze bir `kur` projesinde `M-H1b` ve `M-DEVIR`
> **kurulamaz** (henüz `derle` koşulmamış, ön-koşul yok) — bu sağlıklı bir projedir ve
> çıkış kodu **2**'dir, 1 değil. Kaçan mutant — yani gerçek kapı körlüğü — **çıkış kodu 1**'dir. Bu ayrımı senin
> **B-7** bulgun sayesinde yaptım; sayıyı hangi bağlamda ölçtüğümü yazmadan beyan
> etmiyorum.

**`t_y42.py`'de 1 senaryo `ÖLÇÜLEMEDİ` diyor** — salt-okunur dizin senaryosu, çünkü
benim konteynerimde root olarak koşuyor ve `chmod 500` ısırmıyor. Sen root değilsen
o senaryo sende ölçülebilir olmalı — **ne çıktığını yaz**, ben sonucunu önden
söylemiyorum.

**Koşum notları:** `t_y3.py` ve `t_y42.py`, `hafiza.py` ile **aynı dizinde** olmalı.
`isir` ~1–2 dakika, `t_y42.py` ~10 dakika sürer (300k satırlık performans senaryosu
içeriyor) — asılmış değildir. `mkdir deneme` bloğunu ikinci kez koşacaksan önce dizini sil.

**İlerlemiş bir projede denemek istersen** `kur` değil **`devral`** kullan.

**`isir`'ın okunuşu** — üç sonuç, karıştırılmamalı: `ISIRDI` (kapı yakaladı) ·
`KAÇTI` (kapı **kör**, o kapının "temiz" hükmü geçersizdir) · `KURULAMADI` (testin
kendi ön-koşulu yok, kapı hükmü **değil**).

**Çıkış kodları:** `kapi` → 0 yeşil · 1 kırmızı (ölçülmüş en az bir kapı ısırdı) ·
2 kullanım/girdi hatası · **3 ölçüm yapılamadı, HÜKÜM YOK** (kesilme · disk dolu · izin
yok · beklenmeyen iç hata). Hem kırmızı hem kesilme varsa **1** döner.
`isir` → 0 hepsi ısırdı · 1 **kapı kör** · 2 ölçülemeyen mutant · 4 temiz sürüm zaten FAIL.

> **Sözlük uyarısı:** `isir` çıktısında mutant başına `KURULAMADI`, özet satırında aynı
> şey için `SINANMADI` yazıyor. İkisi tek anlamdadır (testin ön-koşulu yok). `KAÇTI`
> bambaşkadır — o kapı körlüğüdür.
>
> **`kapi` exit 3'ün SINIRI, ve bu bir soru:** beyanlı/yapısal kapsam boşluğu (git yok,
> henüz commit yok, `politika_gerekce` ile gevşetilmiş kapı) **3 değil 0** döner ve
> hüküm `YEŞİL (SINIRLI)` der. Yani `kapi && dagit`, kapsamı eksik bir projede dağıtım
> yapar. Çizgiyi buraya bilinçli çektim — §4.2'de yargını istiyorum.

---

## 4. Ne yapmanı istiyorum

### 4.1 Öncelikli beş soru

1. **§2 ve §3.6'yı kır.** Düzeltmelerimin ürettiği kusurları dört iç denetim turuyla
   buldum; sonuncusu paketi teslim klasörüne yazdıktan **sonra** iki YÜKSEK daha çıkardı.
   Beşincisinin de bulacağını varsayıyorum — **listelemediğim** birini bul.

2. **Bu turda doğan yeni yüzeylere bak** — hepsi yeni ve az sınandı:
   - `_KirikBoruyaDayanikliAkis` (stdout **ve v2.4.1'den beri stderr** sarmalayıcısı),
   - `kur`/`devral`ın yeni aldığı **tek-yazar kilidi** ve `devral`ın **ağaçtaki her
     `.kilit`i sayması** (A-1'in düzeltmesi — yeni bir durma yolu açtı: meşru bir devir
     yanlışlıkla bloklanabiliyor mu?),
   - `cmd_kapi`nin yeni **exit 3** dalı (A-2) — kırmızıyı gizleyebiliyor mu?
   - `onceki_kurulum_izleri()` + canlıya yazılan **`ÇAPA DEVRİ`** bloğu (kodda ve dosyada `CAPA DEVRI` — grep'lerken dikkat) — canlı hafızaya
     yazan **yeni bir yol**: H1 / H3 / H10 / `--siki` ile çakışıyor mu?
   - `cli_yol_coz()` geçidi (tüm CLI yol argümanları buradan geçiyor),
   - kilidin **inode kimliği** + bayat kilit **teşhisi**,
   - `--siki`nin yeni beyan mantığı (`_beyan_yeni_satirlar`, `ek_canli` düşümü),
   - `basliksal()` hızlı yolu ve `kural_desenleri()` önbelleği — **eşdeğerliği
     bozdum mu?** (30 000 rastgele dize + tam kod-noktası taramasıyla 0 fark ölçtüm;
     ölçümümü kır.)

3. **Testleri denetle.** İki testimin yanlış katmanı ölçtüğünü sabotajla buldum
   (§3). Kalan **36 mutant + 58 senaryodan başka hangisi sahte ısırıyor?** Sabotaj
   yöntemini istediğin teste uygula: ilgili korumayı `if False` yap, test KAÇTI
   demeli; demiyorsa o test komşu bir sınıfı ölçüyordur.

4. **Kapsam envanteri çıkar.** 36 mutant + 58 senaryo **hangi sınıfı hâlâ ölçmüyor?**
   Bu, tek tek bulgudan daha değerli. Bir sınıf sayarsan, onu ölçecek mutantı da tarif et.

5. **`kapi`nin çıkış kodu 3'ünü İKİ YÖNDEN sına.** (a) Bir ölçüm hatası hâlâ 1
   döndürebiliyor mu (ölçemedim → kırmızı sanılıyor)? (b) **Daha önemlisi:** gerçek bir
   kırmızı 3'e kaçabiliyor mu (kırmızı → ölçemedim sanılıyor, `kapi || dur` geçiyor)?
   Kuralı şöyle kurdum: gerçek kapı bulgusu varsa 1, bulgunun tamamı kesilmeden
   ibaretse 3. Bu kural atlatılabiliyor mu?

### 4.2 Dokuz bilinçli açığı yargıla

Bunlar hata değil, **karar**. Katılmıyorsan söyle:

1. **Yeniden çıpalama engellenemez, yalnız görünür kılınır.** Yazma erişimi olan biri
   `.hafizarc`'ı silip `devral` koşabilir. Üç kez engellemeye çalıştım; üçü de ya
   atlatıldı ya meşru v1→v2 geçişini tümden kilitledi. Şimdi yaptığım: tüm ağaç iz
   taraması + canlıya + çıpaya + zincire kalıcı kayıt. **Bu savunulabilir bir güvenlik
   duruşu mu, yoksa kendimi kandırmak mı?**
2. **Zincir anahtarsızdır.** `yuk`'u güncelleyip `halka`yı yeniden hesaplamak hash
   denetiminden geçer. mtime dedektörü en yaygın kılığını görünür kılar ama **hüküm
   vermez** (işaret). Doğru denge mi?
3. **`.hafizarc` var + `_CIPA.json` yok → yazma kapalı, araç içi kurtarma yok.**
   Bilinçli fail-closed. Git'siz bir projede kazara silme projeyi yazmaya kapatır.
4. **Baseline satırını düzeltmenin araç-destekli yolu yok** (senin 1. turundan
   Bulgu 13). Hâlâ katı; katı bırakmak doğru mu?
5. **P-1'in açık sorusu:** taze bir depoda defterler henüz `git add` edilmemişse H9'un
   **kırmızı** yanması mı doğru olurdu? Bugün `ÖLÇÜLEMEDİ` diyor. Kırmızı yapmak her
   yeni projeyi ilk dakikasında durdurur; ölçülemedi demek "izlenmiyor" hâlini ilk
   commit'e kadar gizler. Bilinçli olarak ölçülemedi seçtim.
6. **`kapi` kapsam boşluğunda exit 0 verir** (git yok, henüz commit yok,
   `politika_gerekce`). Yani `kapi && dagit`, kapsamı eksik projede dağıtım yapar. Bunu
   3'e çevirmek her yeni projeyi ilk dakikasında durdururdu ve `politika_gerekce`nin
   "kapı kırmızı yanmaz" tasarımıyla çelişirdi. Çizgi doğru yerde mi?
7. **Kilit inode kimliği yarışı DARALTIR, kapatmaz.** Ölçüldü: aynı dizinde silinen
   kilidin inode'u **20/20 yeniden kullanılıyor**. Kapanış için `st_ctime_ns` ya da
   kilit dosyasına yazılan bir jeton gerekir; bu turda yapmadım. Kabul edilir mi?
8. **Dört ölçümün koşucusu pakette YOK** ("2 330 senaryo ham traceback avı",
   "kayıpsızlık 50×", "normal hafta 11 adım", "2 000 dosyalı git deposu"). Bunlar benim
   beyanım ve **doğrulayamazsın**. §6 tablosunda işaretledim. Koşucusuz beyanı ölçüm
   saymanı beklemiyorum — bunları hangi ağırlıkla değerlendirmemi önerirsin?
9. **Windows ve macOS ÖLÇÜLMEDİ.** Motor yalnız Linux'ta koşuldu. "Windows/macOS/Linux"
   iddiası bu turda **geri çekildi**.

### 4.3 Bunları yapma

- **Beyanıma güvenme.** Bu klasördeki her sayı benim ölçümüm. Kendin koş.
- **"Geçti" deme, "nasıl ölçtüm" yaz.** Ölçmediğin bir şeye "temiz" deme; **ÖLÇÜLMEDİ**
  de ve nasıl ölçüleceğini tarif et.
- **Nazik olma.** Üç turdur en çok işime yarayan şey, kapattığımı sandığım şeyin
  kapanmadığını söylemendi. Aynısını bekliyorum.

---

## 5. Çıktı biçimi

Şu sırayla yaz:

1. **Karar** — tek kelime: `KUR` / `DÜZELT` / `REDDET`, tek cümle gerekçeyle.
2. **Bulgular** — her biri için: (a) tek cümlelik hüküm, (b) **onu üreten tam komut
   dizisi**, (c) gerçek çıktı, (d) neden kusur, (e) ciddiyet (YÜKSEK / ORTA / DÜŞÜK).
   Koşmadığın hiçbir şeyi bulgu diye yazma.
3. **Kapsam envanteri** — hangi sınıflar ölçülmüyor, her biri için önerilen mutant.
4. **Test denetimi** — sabotajı hangi testlere uyguladın, hangileri sahte ısırıyor.
5. **Bilinçli açıklara dair yargın** (§4.2'deki beş madde).
6. **Kıramadıkların** — neyi denedin ve kıramadın. Bu bölüm en az bulgular kadar
   değerli; neyin gerçekten sınandığını gösteriyor.

`DÜZELT` dersen, düzeltme sırası da ver (hangisi önce kapatılmalı ve neden).

---

## 6. Bugünkü ölçümlerim (doğrulaman için)

| Ölçüm | Sonuç |
|---|---|
| Isırma kanıtı (`isir`) | **36/36** (`derle` koşulmuş proje) · taze projede 34/34 + 2 KURULAMADI · temiz projede 0 yanlış-pozitif |
| Yeni testler | `M-H0d` · `M-H0t` · `M-KACIS` · `M-KILIT` · `M-AKLAMA` · `M-DEVIR` · `M-KILITK` · `t_p1` · `t_a2` · `t_a3` — **onu da sabotajda KAÇIYOR/KALIYOR** |
| Ham traceback avı | 2 330 senaryo · 0 traceback · 0 çökme · 0 asılma *(koşucu pakette YOK — beyanımdır, doğrulayamazsın)* |
| Senaryo kanıtları (`t_y42.py`) | **57 geçti · 0 kaldı · 1 ölçülemedi** (toplam 58) |
| Temiz hata kanıtları (`t_y3.py`) | **20/20** |
| Kayıpsızlık | 50× aynı konu derlendi → 50/50 satır korundu *(koşucu pakette YOK)* |
| Normal hafta simülasyonu | 11 adım · 0 yanlış-pozitif *(koşucu pakette YOK)* |
| Performans | 300 000 satırda `kapi` **ASCII ~3,5 sn · TÜRKÇE ~6 sn** (v2.3.0: ~10 / ~12 sn) · 2 000 dosyalı git deposunda **0.14 sn** *(son ikisinin koşucusu pakette YOK)* |
| Motor | **4 394 satır** · saf Python stdlib · **yalnız Linux'ta ölçüldü**; Windows/macOS ÖLÇÜLMEDİ |
| SHA256 (`hafiza.py`) | `738849C086512C7485048C58570EEDCA045E21550EF9BE357197FF577126F300` |
| Paket doğrulaması | `.skill` sıfırdan açılıp koşuldu: beyan edilen SHA paketteki dosyayla **tutuyor** |

Bu skill **henüz kurulmadı**. Senin kararını bekliyorum.
