# Klasör Düzeni ve Adlandırma

## 1. İlke: KÖK = YALNIZ AKTİF OLAN

Proje kökünde yalnızca **şu an üzerinde çalışılan** şeyler durur. Kapanmış her tur,
eski her sürüm, biten her belge `arsiv/` altına **taşınır**.

Neden: kök dizin bir projenin ilk okunan sayfasıdır. 80 dosyalık bir kökte, hangisinin
güncel olduğunu kimse (ne insan ne ajan) bilemez; bilemeyince yanlış dosyayı okur ve
yanlış dosyayı okuduğunu fark etmez. Bu, sessiz hataların en pahalı kaynağıdır.

**Silme yok, yalnız taşıma.** Tek istisna adı açıkça geçici olan dosyalardır
(`_gecici_*`, `*.tmp`, `scratch/`) — bunlar `SAKLAMA_PLANI.md`'de "0 saklama" satırıyla
ilan edilmiştir.

---

## 2. Düzen

```
<proje kökü>/
  PROJE_HAFIZA.md        CANLI DURUM — türetilmiş snapshot, tavanlı, her oturum okunur
  CLAUDE.md              KALICI PROTOKOL — her oturumda yüklenir, nadiren değişir
  SAKLAMA_PLANI.md       Neyin ne kadar saklanacağı — ÖNCEDEN yazılır
  KONULAR.md             Anahtar sözlüğü (canlı blokların `konu` etiketleri)
  .hafizarc              Yapılandırma (tavan, bayatlık, arşiv türleri…)

  kararlar/              ADR — geri döndürmesi zor kararlar, değişmez, numaralı
    0000-DIZIN.md        (üretilir) bugün geçerli olanların listesi
    0001-....md
  gunluk/                Fragman kutusu — derlenmeyi bekleyen notlar
    2026-07-28-1930-genel-durum.md

  arsiv/
    hafiza/              Emekli hafıza satırları + kanıt tabanı + defterler
      _KAYNAK.md         ÇIPA: kurulum anındaki canlı hafıza (kanıt tabanı)
      _CIPA.json         çıpanın SHA'sı
      _ZINCIR.jsonl      defterlerin halka zinciri (mühür geçmişi)
      _TASINMA.jsonl     beyan edilmiş canlı→arşiv taşımaları
      _DUZELTMELER.json  beyan edilmiş satır düzeltmeleri (+ eski değerlerin geçmişi)
      _YENI_SATIRLAR.txt beyan edilmiş yeni yapısal satırlar
      _KOVA.json         snapshot satırının nerede yaşayacağı (CANLI / ARSIV)
      _KORUNAN.json      hash'lenmiş korunan bloklar
      HAFIZA_01.md       emekli edilmiş satırlar (byte-birebir)
      gunluk/            derlenmiş fragmanlar
    gorev/  test/  kanit/  bulgu/  tasarim/  taslak/     ← kapanmış tur belgeleri

  araclar/hafiza/hafiza.py    motor
```

`arsiv/` alt türleri projeye göre değişir; `.hafizarc` içindeki `arsiv_turleri`
listesinden gelir. **Kullanılan her tür `SAKLAMA_PLANI.md`'de geçmelidir** (H13).

Hukuk/strateji projesi için tipik türler: `dilekce`, `karar`, `mutalaa`, `delil`,
`yazisma`, `taslak`. Araştırma projesi için: `kaynak`, `veri`, `analiz`, `taslak`.

---

## 3. Adlandırma kuralları

| Tür | Kalıp | Örnek |
|---|---|---|
| Tur/sürüm belgesi | `<TUR>_<konu>_v<surum>.md` | `GOREV_v0.49.md`, `TEST_v0.49.md` |
| Karar (ADR) | `NNNN-kebab-baslik.md` | `0007-capacitor-secimi.md` |
| Fragman | `YYYY-AA-GG-SSDD-konu.md` | `2026-07-28-1930-genel-durum.md` |
| Arşiv hafıza | `HAFIZA_<dönem>.md` | `HAFIZA_01.md`, `HAFIZA_v0.40+.md` |
| Geçici | `_gecici_*` | `_gecici_hesap.xlsx` |

**Numaralar asla yeniden kullanılmaz.** Bir ADR silinse bile numarası boş kalır —
çünkü o numaraya başka belgelerden link verilmiş olabilir.

**Sürüm numarası tek bir yerde kanoniktir** (`.hafizarc`'ta `kanonik_artefakt` ile
tanımlanır). Canlı hafızada, karar günlüğü dışında, birden fazla farklı sürüm adının
"aktif" gibi geçmesi H5'i kırar — çünkü hangisinin doğru olduğu belirsizleşir.

---

## 4. Kök temizliği — taşıma kuralı

Bir dosyayı arşive taşımadan önce üç soru:

1. **Bu dosyanın hâlâ okunması gerekiyor mu?** Hayırsa taşı.
2. **Aynı bilginin daha yenisi var mı?** Varsa eskisini taşı (anahtar bazlı sıkıştırma).
3. **`SAKLAMA_PLANI.md`'de karşılığı var mı?** Yoksa önce plana satır ekle.

Taşıma yaparken:
- Hedefte aynı adlı dosya varsa **üzerine yazma** — atla ve bildir.
- İçerik farklıysa **dokunma** — iki dosyanın SHA'sı farklıysa bu bir çakışmadır, sessizce
  çözülmez.
- Her taşımayı **logla** (hangi dosya, nereye, ne zaman).

---

## 5. Canlı hafızanın bölümleri (sabit)

```
# <PROJE> — CANLI HAFIZA
> Son güncelleme: YYYY-AA-GG

## DEVRALAN MODELE İLK TALİMAT     ← yeni oturumun ilk okuyacağı adımlar
## GÜNCEL DURUM                    ← bugün neredeyiz
## SONRAKİ ADIM                    ← sıradaki iş
## AÇIK KARARLAR / BLOKERLER       ← bekleyenler
## SABİT ÇERÇEVE                   ← KALICI KURALLARIN EVİ (rotasyona girmez)
## KIRMIZI ÇİZGİLER / AÇIK KAPILAR ← asla ihlal edilmeyecekler
## KARAR GÜNLÜĞÜ                   ← özet + kararlar/ linki (gerekçe orada)
## ARŞİV DİZİNİ                    ← (üretilir) hangi arşiv dosyasında ne var
```

**Neden kural evi ayrı:** kalıcı bir kural `GÜNCEL DURUM` içinde yaşarsa, o bölüm
rotasyona tabidir — bir sonraki temizlikte usulünce emekli edilir. Bayt korunur ama
**görünürlük ölür**: sonraki oturum o kuralı hiç görmez, çünkü arşivi baştan sona
okumak yasaktır. H7 tam olarak bunu yakalar.

---

## 6. Blok işaretleri (anahtar bazlı sıkıştırma)

Canlı hafızadaki her içerik bloğu görünmez bir işaretle sarılır:

```markdown
<!-- blok konu="genel-durum" guncel="2026-07-28" kaynak="arsiv/hafiza/gunluk/....md" -->
- İçerik burada.
<!-- /blok -->
```

Kural: **bir konu için canlıda en fazla BİR blok.** Aynı konuda yeni bilgi gelirse
eski blok arşive taşınır, yenisi yerine geçer. Bu, Kafka'nın log-compaction mantığıdır:
sıkıştırma kronolojiye göre değil **anahtara** göre yapılır. Sonuç: "eski ama tek olan"
bilgi hiç kaybolmaz, "yeni ama tekrarlanmış" bilgi hiç birikmez.

Kronolojik FIFO (en eskiyi at) bunun tam tersini yapar ve tehlikelidir: en eski blok
projenin hâlâ geçerli kırmızı çizgisi olabilirken, geçen haftaki blok çoktan geçersiz
olmuş olabilir.
