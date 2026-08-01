# Oturum Protokolü, Devir ve Çok-Ajan Kullanımı

## 1. Açılış — beş adım, sırası pazarlıksız

1. **Hafızayı oku.** `PROJE_HAFIZA.md` baştan sona. En tepedeki devir notu + en son
   karar günlüğü maddesi, önceki oturumun özetidir.
   **Sohbet geçmişini hafıza sayma** — sohbet sıkıştırılır, dosya sıkışmaz.
2. **Kapıyı koş.** `hafiza.py kapi`. **YEŞİL görmeden işe başlama.** Kırmızıysa önce onu
   çöz; kırmızıyla çalışmak "normalleşmiş kırmızı" üretir ve bir süre sonra gerçek bir
   bozukluk da aynı görünür.
3. **`git status`** temiz mi bak (varsa).
4. **`SONRAKİ ADIM`'dan devam et.** Yeni bir iş açma; yarım kalanı bitir.
5. **Yazmadan önce tasarımı onaylat.** Kod/içerik üretmeden önce planı işaretlenebilir
   şıklarla sun, kapsamı ve kararları kullanıcıya kilitlet.

---

## 2. Çalışma sırasında

**Checkpoint kuralı.** Her büyük adım bitiminde bir fragman yaz:
```
hafiza.py not --konu <konu> --tur durum --metin "..."
```
Fragman yazmak ucuzdur; yazmamak pahalıdır. Oturum her an kesilebilir.

**İşi yarıda kesme.** Ölçüm ve "devam mı, dur mu" kararı yalnız **adım aralarında**
alınır. Adım = atomik iş birimi (bir kapı koşumu, bir yapı turu, bir dosya yazımı,
bir rapor bölümü).

**Kalıcı kural doğduysa** evi `SABİT ÇERÇEVE`'dir. Başka bölüme yazma.

**Geri döndürmesi zor bir karar aldıysan** ADR aç:
```
hafiza.py karar --baslik "..." --konu <konu>
```
ADR'de **bedeller** bölümü boş bırakılmaz — bedelsiz karar yoktur. Kabul edilince
`durum: kabul` yap; o andan sonra ADR **düzenlenmez**, yalnızca yerine geçilir.

**Canlı hafızaya kararın metnini yazma, yolunu yaz.** Canlı dosya yol taşır, metin
taşımaz. Ayrıntıya ihtiyaç duyan onu açar.

---

## 3. Kapanış

```
hafiza.py derle          # fragmanlar canlıya işlenir, arşive taşınır
hafiza.py kapi           # yeşil olmalı
hafiza.py emekli ...     # tavan zorlanıyorsa
```

Sonra **devir notu**. Kullanıcı yeni oturuma geçeceğini belirttiğinde (ya da oturum
sağlığı sarı/kırmızıya döndüğünde), istemesini beklemeden, **tek seferde
kopyalanabilir**, kod bloğu içinde, kendi kendine yeten bir not yaz:

```
proje/klasör + aktif sürüm/durum
son yapılan
yarım kalan
sıradaki ilk iş (adım adım)
açık kararlar / blokerler
ilgili dosyalar
uyarılar
```

Hafıza dosyası olan projelerde not **ayrıca hafızaya da** yazılır; kopyalanabilir
sohbet bloğu her durumda zorunludur.

---

## 4. Renk kodu (oturum sağlığı)

| Renk | Anlam | Davranış |
|---|---|---|
| 🟢 YEŞİL | bol yer var | normal çalış |
| 🟠 TURUNCU | eşiğe yaklaşıldı | eldeki adımı **bitir**; yeni büyük adım **açma**; checkpoint + devir notu yaz; kullanıcıya "yeni oturum öneririm" de. Karar kullanıcınındır. |
| 🔴 KIRMIZI | eşik aşıldı | eldeki adım küçükse bitir, büyükse **en yakın güvenli noktada** kapat (üretilmiş dosyaları diske yaz, adımı böl). Yeni adım açılmaz. Checkpoint + devir notu **her koşulda** yazılır. |

Kırmızıda notu yazmadan işe inat etmek, **işi de kaydı da** kaybetmektir: oturum her an
kesilebilir ya da sessizce sıkıştırılabilir.

---

## 5. Çok-ajan / paralel çalışma

Fragman modeli tam da bunun için var: her ajan/oturum **kendi dosyasını** yazar,
kimse aynı satırlar için yarışmaz, `derle` sonunda hepsini toplar.

Kurallar:
- Alt ajanlar canlı hafızaya **doğrudan yazmaz**; yalnız `gunluk/` altına fragman yazar.
- Alt ajandan dönen çıktı **yoğunlaştırılmış özet** olmalıdır, ham döküm değil.
- İşi ancak bağlam **gerçekten izole edilebiliyorsa** böl. Aynı işin ardışık fazlarını
  farklı ajanlara bölmek "telefon oyunu" üretir: her devirde bağlam kaybolur.
- Çok-ajan kullanımı belirgin biçimde daha pahalıdır; kapsamlılık gerçekten gerekmiyorsa
  tek ajanla kal.

---

## 6. BETİKSİZ kullanımde protokol (betiksiz)

Motor yoksa aynı disiplin elle yürütülür:

| Komut yerine | Elle karşılığı |
|---|---|
| `not` | `gunluk/YYYY-AA-GG-SSDD-konu.md` dosyası aç, frontmatter yaz |
| `derle` | Fragmanı ilgili bölüme işle; **eski bloğu silme, `arsiv/hafiza/HAFIZA_01.md` sonuna kopyala**; fragmanı `arsiv/hafiza/gunluk/`'e taşı |
| `karar` | `kararlar/NNNN-baslik.md` aç; eskisini `durum: yerine-gecildi` + `yerine-gecen: NNNN` yap |
| `emekli` | Satırları **kes-yapıştır değil, kopyala** → arşive ekle → canlıdan sil → `_TASINMA.jsonl`'e satır yaz |
| `kapi` | `references/kapilar.md`'deki listeyi elle geç; ölçemediğine **ÖLÇÜLMEDİ** yaz |

Betiksiz kullanımda en kolay ihlal edilen kural budur: **"eski bloğu silme, taşı."**
Elle çalışırken silmek bir tuşluk, taşımak üç adımlıktır — bu yüzden betikli (motorlu) kullanıma
geçmek uzun ömürlü projelerde her zaman kazandırır.

---

## 7. Bu skill'i kullanan ajana: sık yapılan üç hata

1. **Canlı hafızaya doğrudan yazmak.** Cazip ve hızlıdır; ama kaynak-türev ilişkisini
   koparır ve H12 sapma alarmını anlamsızlaştırır. Önce `not`, sonra `derle`.
2. **Kapıyı koşmadan "tamam" demek.** Koşulmayan kapı yok hükmündedir. Bir aracın
   "başarıyla tamamlandı" demesi kapının yeşil olduğu anlamına gelmez.
3. **Bir kapının ısırdığını görüp sınıfı kapalı ilan etmek.** Mutant yalnız mutasyona
   uğrattığın satırı kanıtlar. Kapsama iki adımdır: önce envanter, sonra her biri için
   ayrı mutant.
