# FAZ 0 — ÖLÇ, DÜZELTME

**Amaç:** v2.5.0 düzeltme turuna başlamadan önce **kırmızı listeyi ölçmek**.
Bu fazda `hafiza.py`'nin **tek satırına dokunulmaz**.

Gerekçe — Fable 5, 4. tur denetimi §9:

> *"Kör noktan bir düşünce hatası değil, **bir ortam eksiği** — ve bu, belge okuyarak
> asla bulunamaz. `useradd` ve `mount -t tmpfs` toplam iki komut."*

Üç YÜKSEK bulgunun üçü de (B4-1, B4-3, B4-4) yalnız üreticinin konteynerinin
**veremediği** koşullarda görünüyor: root olmayan kullanıcı, dolu disk, salt-okunur dosya.

---

## Dosyalar ve nereye konacakları

```
<depo kökü>/
├── .github/workflows/capraz.yml
├── faz0/
│   ├── ortam_olcum.sh          <-- ortam sınıfı ölçümü (Linux, root ister)
│   ├── win_kill_probu.py       <-- Y-1 hipotezi probu (Windows)
│   └── sabotaj.py              <-- otomatik sabotaj / kapsam envanteri
└── skill/scripts/
    ├── hafiza.py               <-- MOTOR, DOKUNULMADI
    ├── t_y3.py
    └── t_y42.py
```

Motor `skill/scripts/` altında yaşar ve **ikinci bir kopyası yoktur** — `.skill`
paketi `skill/` dizininden üretilir (`paketle.sh`). `capraz.yml`, `ortam_olcum.sh`
ve `sabotaj.py` içindeki varsayılan yollar bu düzene göredir.

---

## Ne ölçüyor

| İş | Ne | Neden |
|---|---|---|
| `kanit` | {ubuntu, windows, macos} × {3.11, 3.13} = **6 koşum**; `t_y3` · `isir` (taze + `derle` sonrası) · `t_y42` | "Windows/macOS ÖLÇÜLMEDİ" başlığını kapatır. Kod okuması 11 kontrolün **8'inde temiz** dedi — iddia doğruydu ama kanıtsızdı. |
| `win_kill_probu` | Windows'ta `os.kill(pid, 0)` **varlık sınıyor mu, ateş mi ediyor** | **Y-1 hipotezi.** bpo-14480 CLOSED-REJECTED; Victor Stinner: *"0 has no special meaning on Windows… already means two things: `signal.CTRL_C_EVENT` and the int 0."* Fable bunu ✔ verdi ama §3.5'te *"ölçmedim, ölçemedim"* diyor. Bu prob meseleyi bitirir. |
| `ortam` | B4-1 (tmpfs 600k dolu disk) · B4-3 (canlı 0444) · B4-4 (root olmayan kullanıcı × 4 senaryo) | Üç YÜKSEK'in **regresyon kapısı**. |
| `kalite` | ruff · mypy · bandit | Geliştirme bağımlılığı; `hafiza.py` bunları import etmez, **sıfır bağımlılık bozulmaz**. Bugün: ruff 30 gerçek bulgu (0,054 sn), mypy 1 hata, bandit 20 LOW. |

---

## Ölçüm aracı önce KENDİNİ kanıtladı

Kör kapı protokolü buraya da uygulandı. `ortam_olcum.sh`, **v2.4.1'e karşı koşuldu**:

```
  disk bosaldiktan sonra kalan .kilit sayisi: 1
  >>> B4-1 URETILDI: kilit sizdi, proje kalici yazmaya kapali.

  duzeltme + yeniden derle SONRASI [H1] bulgu sayisi: 2 · kalan fragman: 0
  >>> B4-3 URETILDI: kirmizi KALICI, arac ici cikis yok.

    muhur  arsiv/hafiza   exit=3  ARAC-KUSURU(yanlis)
    not    gunluk         exit=3  ARAC-KUSURU(yanlis)
    karar  kararlar       exit=3  ARAC-KUSURU(yanlis)
    kur    .              exit=3  ARAC-KUSURU(yanlis)
  yanlis teshis sayisi: 4 / 4
  >>> B4-4 URETILDI

  uretilebilen bulgu: 3 · olculemeyen: 0
  HUKUM: en az bir YUKSEK bulgu HALA URETILEBILIYOR.        exit=1
```

**Sabotaj sınaması** (aynı komutlar, `chmod` YOK — yani kusur yok):

```
    muhur  exit=0  ortam-teshisi/temiz
    not    exit=0  ortam-teshisi/temiz
    karar  exit=0  ortam-teshisi/temiz
    kur    exit=0  ortam-teshisi/temiz
```

Dedektör hep "üretildi" demiyor; **gerçekten ölçüyor**. Kör kapı değil.

**Çıkış kodu sözleşmesi:** `0` üç bulgunun üçü de kapanmış (v2.5.0 hedefi) ·
`1` en az biri hâlâ üretilebiliyor (v2.4.1'in bugünkü hâli) · `2` **ÖLÇÜLEMEDİ** —
"kapandı" demek yasak.

---

## OTOMATİK SABOTAJ — koşuldu, sonuç aşağıda

`faz0/sabotaj.py`, `hafiza.py`'deki **60 `fail()` çağrısını tek tek** devre dışı bırakıp
her seferinde `isir` koşar. Hüküm: *"bu satır silinse `isir` fark eder mi?"*

`hafiza.py` **değiştirilmez** — her sabotaj geçici bir kopya üzerinde yapılır.

**Aracın kendini kanıtlaması.** 21 `fail()` için doğru mutantı buldu:

```
  +  #16  satir 2881   H2    KAPSAMLI   M-H2
  +  #17  satir 2891   H3    KAPSAMLI   M-H3
  +  #25  satir 3020   H7    KAPSAMLI   M-H7,M-H7b
  +  #33  satir 3103   H10   KAPSAMLI   M-H10c
  +  #56  satir 3297   H15   KAPSAMLI   M-H15a,M-H15b
  +  #60  satir 3426   H14   KAPSAMLI   M-H14,M-H14b
```

Her mutant kendi kapısına düştü. Kör dedektör değil.

**Sonuç: 21 KAPSAMLI · 39 KAPSAMSIZ · 0 ÖLÇÜLEMEDİ.**

| Kapı | Kapsamlı | **Kapsamsız** | | Kapı | Kapsamlı | **Kapsamsız** |
|---|---|---|---|---|---|---|
| H0 | 1 | **2** | | H10 | 4 | **2** |
| **H1** | **0** | **6** | | H11 | 1 | **10** |
| H1-KOVA | 1 | **2** | | H12 | 2 | **2** |
| H2 | 1 | **1** | | H13 | 1 | **2** |
| H3 | 1 | 0 | | H14 | 1 | **1** |
| H4 | 1 | **1** | | H15 | 2 | 0 |
| H5 | 1 | **1** | | H9 | 0 | **1** |
| H6 | 1 | **3** | | H-LINK | 0 | **1** |
| H7 | 1 | 0 | | H8 | 2 | **3** |

### 🔴 En ciddi bulgu — **H1'in ısırdığına dair kanıt YOK**

`fail()` çağrılarını **grup hâlinde** kapatınca (yöntemin sınırını sınamak için):

```
H1    6 fail() TAMAMI kapatildi -> exit=0 · KACAN: HICBIRI
H11  11 fail() TAMAMI kapatildi -> exit=1 · KACAN: M-H11
H8    5 fail() TAMAMI kapatildi -> exit=1 · KACAN: M-H8,M-H8b
```

H11 ve H8 beklendiği gibi davrandı. **H1 davranmadı.**

`H1`'in **altı raporlama dalının tamamı** silinse, `isir` yine **36/36 · exit 0** diyor.
Yani `M-H1` (canlıdan bir satır silinir) mutantı H1'i **hiç ölçmüyor** — muhtemelen
`H1-KOVA` onu zaten yakaladığı için mutant ısırıyor ve kredi iki kapıya birden yazılıyor.

Bu, aracın **merkezî iddiasını** taşıyan kapı: *"hiçbir satır kaybolmadı"*.
Ve aracın kendi doktrini şunu diyor:

> *"Isırmayan kapının 'temiz' hükmü geçersizdir."*

**Dürüstlük sınırı:** bu bulgu H1'in bugün **bozuk olduğunu göstermez** — H1 çalışıyor.
Gösterdiği şey, H1'in ısırdığının **kanıtlanmamış** olduğu. Aynı şey, örtüşen tespitin
körlüğü maskelemesi anlamına gelir.

**Önerilen mutant (HİPOTEZ — doğrulanmadı):** `M-H1c` — canlıdan değil, **arşiv**
dosyasından (`arsiv/hafiza/HAFIZA_*.md`) beyansız bir satır sil. H1 birleşim
çok-kümesine baktığı için ısırmalı; H1-KOVA yalnız CANLI kovasına baktığı için
görmemeli. Ön denemede yön doğrulandı (`[H1] 2 satir KAYIP` ötüyor) ama **temiz
izole bir gösterim üretilemedi** — proje zaten FAIL durumundaydı. Faz F'de
kurulmadan önce izole edilmeli.

### Yöntemin sınırı (açıkça)

Bu araç şunu ölçer: **"bu `fail()` satırı silinse `isir` fark eder mi?"**
Şunu ölçmez: *"bu kapı test edilmiş mi?"* Bir dal gerçekten kapsamlı ama **fazlalıklı**
olabilir; tek başına kapatınca mutant yine yakalanır. Bu yüzden grup sabotajı
(yukarıdaki üç satır) ayrıca koşulmalıdır — `H1` tam da böyle çıktı.

---

## Bilerek böyle

**`continue-on-error: true` her adımda.** Bu fazın amacı yeşil almak değil,
**kırmızı listeyi görmek**. Liste çıkıp Faz A–F kapandıktan sonra bu bayrak kaldırılır
ve `ortam` işi gerçek bir kapıya dönüşür.

**`t_y42`'nin `B-6` senaryosu CI runner'ında büyük olasılıkla `KALDI` diyecek**
(300k satırda `kapi < 8 sn`). Bu bir **kod** kusuru değil, **test** kusurudur:
kalibrasyonsuz mutlak duvar saati. Fable'ın makinesinde 10,09 sn, bende 4,10 sn,
üreticide ~6 sn — yani sonuç makineye bağlı ve beyan yeniden üretilemiyor.
Faz F'de referans işe oranlanacak; o zamana kadar bu bir **beklenen kırmızı**.

**Public repo şart.** GitHub-hosted runner'lar public repo'da ücretsiz ve
dakika limitsizdir — windows ve macOS dahil. Private repo'da aylık 2.000 dakika
kotası var ve çarpanlar Windows 2x, macOS 10x; üçlü matris × iki Python sürümü
kotayı hızla yakar. **"Public repo" ≠ "yayın"** — PyPI yok, marketplace yok,
duyuru yok.
