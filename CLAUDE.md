# hafiza-kur — KALICI PROTOKOL

Bu dosya bu deponun **SABİT ÇERÇEVE**'sidir: nadiren değişir, rotasyona girmez.
Cowork projesindeki "proje talimatı" bunun bir **kopyasıdır**; ikisi ayrışırsa
**BU DOSYA geçerlidir** (projeler yerelde saklanır, bulut senkronu yoktur ve
Claude Code'da çalışmaz).

> **Buraya ne GİRMEZ:** sürüm numarası, faz, bulgu sayısı, "şu an neredeyiz".
> Onların evi DEVİR notudur. Değişen bilgi buraya yazılırsa bayatlar — ve bu,
> aracın kendi H12 kapısının yakaladığı hatanın ta kendisi olur.

---

## 0. NE BU PROJE

Taşınabilir bir **proje hafızası KAPI SİSTEMİ**: tek dosyalık saf Python motoru
(`skill/scripts/hafiza.py`, stdlib, sıfır bağımlılık) + bir Claude skill paketi.
Motor bir projenin hafıza dosyalarını yönetir ve kapılarla **ÖLÇER**.

**Ürünün tek gerçek vaadi ÖLÇÜLEBİLİRLİKTİR** — hız, zekâ ya da özellik değil.
Bir değişiklik bu vaadi zayıflatıyorsa, getirdiği kolaylık ne olursa olsun,
yanlış değişikliktir.

## 1. ÜÇ CÜMLELİK DOKTRİN (pazarlığa kapalı)

1. **Ölçülmeyen kapının hükmü YOKTUR.** Bir kapının var olması ısırdığı anlamına
   gelmez; ısırdığı **mutantla** kanıtlanır.
2. **Ölçülemeyene "temiz" DENMEZ.** `ÖLÇÜLEMEDİ` ayrı bir hükümdür, PASS değildir,
   ve çıkış kodu bile bunu ayırır.
3. **Bazı hamleler önlenemez.** Hedef **engellemek** değil, **GİZLENEMEZ KILMAK**.

## 2. OTURUM AÇILIŞI (sırası pazarlıksız)

1. **En son DEVİR notunu oku.** Güncel sürüm, faz ve açık işler ORADADIR.
   Sohbet geçmişini ve Cowork proje hafızasını **kanıt sayma**.
2. `denetim/` dizinini tara — en yeni tarihli rapor açık iş listesidir.
3. `git status` temiz mi + son CI koşumu ne diyor.
4. **Beyana GÜVENME, kendin koş:**
   ```
   cd skill/scripts
   python3 hafiza.py isir --kok=<taze proje>     # mutant kanıtı
   python3 t_y3.py                               # temiz hata kanıtları
   python3 t_y42.py                              # davranış kanıtları (~13 dk)
   sha256sum hafiza.py
   ```
   Belgedeki her sayıyı kendi koşumunla doğrula, **sonra** konuş.
5. Kod/içerik yazmadan **ÖNCE** tasarımı işaretlenebilir şıklarla sun, onay bekle.

## 3. BEDELİ ÖDENMİŞ DERSLER (13 denetim turu)

- Bir düzeltmenin **ne kapattığı değil, NE AÇTIĞI** ölçülür.
  `os._exit(0)` tek satırdı: 1 YÜKSEK kapattı, **3 YÜKSEK doğurdu**.
- **Her düzeltmeye AYRI mutant/senaryo.** Mutantsız düzeltme denetimde kör kalır.
- **Her yeni testi SABOTAJLA sına:** koruduğunu iddia ettiği şeyi kapat; test
  `KAÇTI` demeli. Demiyorsa komşu bir sınıfı ölçüyordur.
- Bir korumanın **DERİNLİĞİ ile KAPSAMI ayrı iki sorudur.**
- Bir kanalı `DEVNULL`'a atan test, o kanaldaki sınıfı **ölçemez**.
- **Belge de bir arayüzdür ve yalan söyleyebilir.** Yazdığın her sözleşme maddesi
  için bir senaryo yaz; yoksa madde bir dilek olur.
- Bir sınıf **SINIRDA** kapanır, tek tek yüzeyler sarılarak değil.
- **Sayı bağlamsız beyan edilmez** ("36/36" yalnız `derle` koşulmuş projede doğru).
- **Örtüşen tespit körlüğü maskeler.** İki kapı aynı mutantı yakalıyorsa, mutant
  ikisini de ölçüyor sanılır; oysa birini hiç ölçmüyor olabilir.
- Kör nokta çoğu zaman bir düşünce hatası değil, bir **ORTAM eksiğidir.**
  Ölçemiyorsan ölçebilecek ortamı **KUR**: root olmayan kullanıcı, dolu disk,
  salt-okunur bağlama, Windows, macOS.
- **"Bitti" bu projede iki kez erken söylendi.** Paketledikten SONRA bir tur daha koş.
  Yöntem: (a) beyan-gerçek karşılaştırması, (b) düşman belge okuması.

## 4. KIRMIZI ÇİZGİLER

- **Bir denetim turu SÜRERKEN koda dokunma** — denetçi tam o baytları ölçüyor.
- **ADDITIVE kal:** mevcut kapıyı, mutantı ya da korumayı **kanıtsız sökme**.
- **Sıfır bağımlılık kırılmaz.** Geliştirme araçları (ruff/mypy/bandit/CI) serbest;
  `hafiza.py`'nin **çalışma zamanı** import'u stdlib dışına çıkamaz.
- **Determinizm kırılmaz:** ANN yasak · uzak gömme API'si yasak · indeks asla
  otorite değil (silinip yeniden üretilince bit-bit aynı çıkmalı).
- **Diskteki dosya/dizin adlarına ASLA Türkçe diyakritik koyma.** macOS'ta
  HFS+ NFD'ye zorluyor, APFS normalize etmiyor → aynı ad iki farklı bayt dizisi →
  çıpa zinciri Linux↔macOS arasında kırılır. Mevcut ASCII tercihi **bilinçlidir**.
- **Çevrilmez:** `.hafizarc` anahtarları · `_CIPA.json` ve `_ZINCIR.jsonl` alan
  adları · diskteki dosya adları. Çevirmek zinciri kırar.
- **`.gitattributes`'taki `* -text` gevşetilemez** — gerekçesi dosyanın içinde.

## 4.1 GIT — İŞ BÖLÜMÜ VE ORTAM TUZAĞI

**PUSH VE COMMIT ONUR'DADIR.** Ajan depoyu hazırlar, dosyaları yazar, CI
sonuçlarını okur — ama `git commit` / `git push` **koşmaz**. Onur koşar.

**Cowork'ün yerel VM mount'unda dosya SİLİNEMİYOR.** Bu yüzden bağlı klasördeki
depoda **hiçbir `git` komutu koşma** — `git status` dahil. Her koşum
`.git/index.lock` bırakır ve bir sonraki komutu bloke eder; kilit de silinemez.

Bu, projenin **kendi B4-1 bulgusunun birebir aynısıdır**: sızan bir kilit,
kalıcı olarak yazmaya kapanan bir ağaç, ve araç içi çıkış yok. Aracı yazarken
düştüğümüz tuzağa aracı kullanırken de düşüyoruz — bu tesadüf değil, sınıfın
kendisi.

**Yapılacaklar:**
- Depo durumunu **git'siz** oku: `find`, `ls`, dosya okuma.
- Yapılandırma gerekiyorsa `.git/config` gibi dosyaları **düz metin** yaz,
  `git config` çağırma.
- Silinmesi gereken dosyayı `_to_delete/` altına **taşı** ve Onur'a söyle.
- Git işi gerekiyorsa **komutu yaz, Onur koşsun.**

## 5. ALINMIŞ KARARLAR

Yeniden tartışma; değiştirmek istiyorsan **gerekçeyle** aç ve bir ADR yaz.

| Konu | Karar |
|---|---|
| Semantik arama / embedding | **HAYIR.** Yol: determinist geri getirme (Türkçe normalizasyon `ı/İ/ğ/ş/ç` katlama + prefix genişletme · FTS5/BM25, saf-Python yedekli · RRF k=60) ve asıl özgün parça olan **geri getirmeyi ÖLÇEN KAPI** (altın küme, recall@k, PR bloklar). |
| Proje-ötesi hafıza | **DAR.** Yeni altyapı yazma; Claude Code'un mevcut `~/.claude/CLAUDE.md` + `rules/` + `autoMemoryDirectory` mekanizmalarını **kur ve denetle**. 3. projede tekrar etmeyen bilgi global'e çıkmaz. Global katmanda müşteri/kişi adı ve hukuk dosyası detayı **yasak** (KVKK, amaçla sınırlılık). |
| Depo | **PUBLIC** (CI ücretsiz ve limitsiz olsun diye) ama **YAYIN YOK** — PyPI yok, marketplace yok, duyuru yok. *"Public repo" ≠ "yayın".* |
| Dil | **İngilizce kanonik komut + Türkçe alias.** Mesajlar çevrilebilir; komut ve bayrak adları **API'dir** (Git'in porselen/boru tesisatı ayrımı). |
| Mimari | **Tek dosya KALIR.** Bölünecek olan **fonksiyonlardır** (hedef: hiçbir fonksiyon >80 satır, hiçbiri CC >20). |
| Sürüm | Çıkış kodu sözleşmesi kırıcı değiştiyse **minor artar** — yama sürümü olamaz. |

## 6. DEPO DÜZENİ

```
skill/                  <- .skill paketinin TEK GERÇEK KAYNAĞI
  SKILL.md
  references/*.md       <- kapilar · denetim-yaniti · devir · duzen · protokol · sablonlar
  scripts/              <- MOTOR BURADA YAŞAR, başka kopyası YOKTUR
    hafiza.py · t_y3.py · t_y42.py
faz0/                   <- ölçüm altyapısı (koda dokunmaz)
  ortam_olcum.sh        <- root olmayan kullanıcı · dolu disk · salt-okunur
  win_kill_probu.py     <- os.kill(pid,0) Windows davranışı
  sabotaj.py            <- her fail() tek tek kapatılır -> kapsam envanteri
denetim/                <- denetim turlarının defteri (tarih önekli)
.github/workflows/      <- capraz.yml: 3 platform × 2 Python + ortam + kalite
paketle.sh              <- skill/ -> hafiza-kur.skill
```

**Motorun ikinci bir kopyası ASLA olmaz** (H5'in kendi doktrini: "aktif sürüm
hangisi" sorusunun iki cevabı olamaz). Paket `paketle.sh` ile `skill/`'ten üretilir.

## 7. KAPSAM DIŞI

Tuzak Avcısı uygulama/içerik geliştirmesi · TSK ve gelir hukuku · Reels-bülten
operasyonu. Bunlar **ayrı projelerdir**, buraya karıştırılmaz.

## 8. OTURUM KAPANIŞI

İstenmese de, kopyalanabilir **DEVİR notunu kod bloğu içinde** yaz:
sürüm/durum · son yapılan · yarım kalan · sıradaki ilk iş (adım adım) · açık
kararlar/blokerler · ilgili dosyalar · uyarılar.

**Cowork proje hafızası bunun yerine geçmez.** O bir rahatlık katmanıdır;
kanıt katmanı DEVİR notudur.
