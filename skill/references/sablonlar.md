# Şablonlar (BETİKSİZ kullanım — elle açılacak dosyalar)

Motor kullanılmayan projelerde bu dosyaları elle aç. Adlar betikli kullanımla **aynıdır**,
böylece sonradan `hafiza.py kur` çalıştırıldığında var olanları bozmaz, üstüne oturur.

---

## `PROJE_HAFIZA.md`

```markdown
# <PROJE ADI> — CANLI HAFIZA
> Bu dosya bir SNAPSHOT'tır: gunluk/ fragmanlarından ve kararlar/ dosyalarından türetilir.
> Her oturum başında OKU. Buraya doğrudan yeni bilgi yazılmaz.
> Son güncelleme: YYYY-AA-GG · Tavan: 60 KB

## DEVRALAN MODELE İLK TALİMAT
<!-- blok konu="acilis-protokolu" guncel="YYYY-AA-GG" kaynak="-" -->
1. Bu dosyayı baştan sona oku.
2. Açılış kapısını koş (betikli kullanımda `hafiza.py kapi`). Yeşil görmeden başlama.
3. `git status` temiz mi bak.
4. SONRAKİ ADIM'daki ilk işten devam et.
5. Yazmadan önce tasarımı işaretlenebilir şıklarla sun, kapsamı onaylat.
<!-- /blok -->

## GÜNCEL DURUM
<!-- blok konu="genel-durum" guncel="YYYY-AA-GG" kaynak="-" -->
- ...
<!-- /blok -->

## SONRAKİ ADIM
<!-- blok konu="sonraki-adim" guncel="YYYY-AA-GG" kaynak="-" -->
- ...
<!-- /blok -->

## AÇIK KARARLAR / BLOKERLER
<!-- blok konu="acik-kararlar" guncel="YYYY-AA-GG" kaynak="-" -->
- ...
<!-- /blok -->

## SABİT ÇERÇEVE (nadiren değişir)
> Kalıcı kuralların EVİ burasıdır. Başka bölümde yaşayan kural rotasyona girer ve
> bir sonraki temizlikte görünmez olur.

## KIRMIZI ÇİZGİLER / AÇIK KAPILAR
> Asla ihlal edilmeyecekler + bilinçli olarak açık bırakılanlar.

## KARAR GÜNLÜĞÜ (en yeni en üstte)
> Burada yalnız ÖZET + `kararlar/NNNN-....md` LİNKİ durur. Gerekçe ADR'de yaşar.

### YYYY-AA-GG
- ... → `kararlar/0001-....md`

## ARŞİV DİZİNİ
- `arsiv/hafiza/HAFIZA_01.md` — ...
```

---

## `kararlar/NNNN-kebab-baslik.md` (ADR)

```markdown
---
no: 0001
baslik: <kısa karar başlığı>
durum: onerildi        # onerildi | kabul | reddedildi | yerine-gecildi
tarih: YYYY-AA-GG
konu: <konu-slug>
yerini-aldigi: -
yerine-gecen: -
---

# 0001 — <başlık>

## Bağlam
Hangi problem? Hangi kısıt? Neden şimdi?

## Karar
Etken cümle, birinci çoğul: "... yapacağız."

## Değerlendirilen alternatifler
| Seçenek | Artı | Eksi | Neden seçilmedi |
|---|---|---|---|

## Bedeller (consequences)
Bu kararın bize neye mal olduğu — olumlu ve olumsuz.
**Boş bırakma: bedelsiz karar yoktur.**

## Doğrulama
Bu kararın TUTTUĞU nasıl ölçülür? Hangi test/komut/gözlem?
Ölçülemiyorsa bunu açıkça yaz.
```

**Kurallar:** numaralar ardışık ve tekrarsızdır, asla yeniden kullanılmaz.
`durum: kabul` olduktan sonra ADR **düzenlenmez** — fikir değişirse yeni ADR açılır,
eskisi `durum: yerine-gecildi` + `yerine-gecen: NNNN` olur ve yenisinde
`yerini-aldigi: NNNN` yazar (bağlantı **çift yönlüdür**).

---

## `SAKLAMA_PLANI.md`

```markdown
# SAKLAMA PLANI (retention schedule)
> Emeklilik kararı boyuta göre değil DEĞERE göre; anında değil ÖNCEDEN verilir.
> Az sayıda geniş kova tut ("big bucket") — 50 ince seri yönetilemez.

| Seri | Tetikleyici | Saklama | Tasfiye eylemi |
|---|---|---|---|
| KIRMIZI ÇİZGİ / kalıcı kural | — | süresiz | ASLA emekli olmaz |
| KARAR (ADR) | yerine geçildiğinde | süresiz | `kararlar/` içinde kalır; yalnız `durum` güncellenir |
| GÜNCEL DURUM | her derleme | 1 sürüm | üzerine yazılır; öncekinin özeti karar günlüğüne |
| TUR BELGESİ | tur kapanınca | süresiz | `arsiv/<tür>/` altına TAŞINIR |
| OTURUM FRAGMANI | derlendiğinde | süresiz | `arsiv/hafiza/gunluk/` altına TAŞINIR |
| CANLI HAFIZA BLOĞU | aynı konuda yeni blok | süresiz | arşive TAŞINIR (byte-birebir) |
| GEÇİCİ / SCRATCH | iş bitince | 0 | SİLİNEBİLİR — tek istisna; adı açıkça geçici olmalı |

## Kural
Bu tabloda karşılığı olmayan bir dosya türü üretilirse, önce buraya satır eklenir.
```

---

## `KONULAR.md`

```markdown
# KONULAR (anahtar sözlüğü)
> Her canlı blok bir `konu` taşır. BİR KONU İÇİN CANLIDA EN FAZLA BİR BLOK.
> Aynı konuda yeni blok gelirse eskisi emekli edilir.
> Konu EKLEMEK serbest; SİLMEK yasak (silinen ad geri kullanılamaz).

| konu | ne anlatır |
|---|---|
| acilis-protokolu | oturum başlangıç adımları |
| genel-durum | projenin bugünkü hâli |
| sonraki-adim | sıradaki iş |
| acik-kararlar | bekleyen kararlar / blokerler |
```

---

## `gunluk/YYYY-AA-GG-SSDD-konu.md` (fragman)

```markdown
---
konu: genel-durum
tur: durum          # durum | sonraki | karar | bulgu | ders | devir
tarih: YYYY-AA-GG
oturum: 12
---

- Yazılacak içerik burada.
```

`tur` alanı fragmanın canlıda hangi bölüme gideceğini belirler:
`durum`/`devir` → GÜNCEL DURUM · `sonraki` → SONRAKİ ADIM · `karar` → KARAR GÜNLÜĞÜ ·
`bulgu` → AÇIK KARARLAR · `ders` → SABİT ÇERÇEVE.

---

## `CLAUDE.md` (kalıcı protokol)

```markdown
# <PROJE> — KALICI PROTOKOL
> Bu dosya her oturumda yüklenir.
> BUDAMA TESTİ: bir satırı silmek modelin hata yapmasına yol açmıyorsa, KES.

## Girmesi gerekenler
- Tahmin edilemeyen komutlar, varsayılandan sapan kurallar, ortam tuhaflıkları, tuzaklar.

## Girmemesi gerekenler
- Kodu/dosyaları okuyarak bulunabilecek her şey; standart konvansiyonlar;
  sık değişen bilgi (o canlı hafızaya gider); uzun referans dokümanı (link ver).
```

---

## `.gitignore` eklentisi (betikli kullanım)

```
# geçici / scratch
_gecici_*
*.tmp
scratch/

# ASLA yoksayma: bunlar kanıt tabanıdır
!arsiv/hafiza/_KAYNAK.md
!arsiv/hafiza/_CIPA.json
!arsiv/hafiza/_ZINCIR.jsonl
```

---

## Git hook (isteğe bağlı ama önerilir)

`.git/hooks/pre-commit`:

```sh
#!/bin/sh
python araclar/hafiza/hafiza.py kapi --kok="$(git rev-parse --show-toplevel)" || {
  echo "HAFIZA KAPISI KIRMIZI — commit durduruldu."
  exit 1
}
```

**Neden hook:** talimat bir tavsiyedir, hook deterministiktir. İstisnasız her seferinde
olması gereken şeyler talimata değil hook'a yazılır.
