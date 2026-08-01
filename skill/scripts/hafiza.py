#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hafiza.py — PROJE HAFIZA DUZENI v2 · tasinabilir tek-dosya motor (yalniz Python stdlib)

FELSEFE (uc cumle):
  1. LOG ile DURUM ayridir. Log tam ve append-only'dir; durum kompakt ve turetilmistir.
  2. Hicbir satir SILINMEZ, TASINIR — byte-birebir, beyanla, ve arac kendi kapisini kosar.
  3. "Kaybolmadi" bir iddia degil TEST SONUCUDUR. Kapi olcer; olcemedigini "OLCEMIYORUM" der.

ALT KOMUTLAR
  kur      Bir projeye duzeni kurar (idempotent; var olani BOZMAZ).
  not      gunluk/ altina bir fragman yazar (paralel oturum cakismasi yok).
  derle    Fragmanlari canli hafizaya isler, sonra arsive tasir.
  emekli   Canli hafizadan satir blogunu arsive TASIR (byte-birebir, geri alinabilir).
  karar    Yeni ADR (karar dosyasi) acar; --yerine ile eskisini "yerine gecildi" yapar.
  muhur    Beyan defterlerindeki bilincli degisikligi zincire muhurler (gerekce ZORUNLU).
  kapi     H0..H13 kapilarini kosar. FAIL -> exit 1.
  isir     Kapinin gercekten ISIRDIGINI mutantla kanitlar (kor kapi protokolu).

KOK COZUMU (sessiz varsayim YOK):
  --kok=<dizin>  >  ortam degiskeni HAFIZA_KOK  >  yukari dogru .hafizarc araniyor
  Hicbiri yoksa: HATA (cwd'ye sessizce dusulmez).
"""

import argparse
import datetime as _dt
import errno as _errno
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import traceback as _tb
import unicodedata

SURUM = "2.5.0-dev"   # Faz A basladi. 2.4.1 DENETLENMIS bir bayt kumesidir (Fable 4.
# tur tam onu olctu); baytlar degistigi anda ayni numarayi tasimak YALAN olur ve
# "aktif surum hangisi" sorusunun iki cevabi olur (H5 doktrini). "-dev" soneki
# bilincli: depo PUBLIC ama YAYIN YOK; numara Faz F bitince "2.5.0" olur.
                  # sonrasi ic denetim: P-1 (H9 yanlis teshis), A-1 (kilit KAPSAMI),
                  # A-2 (cikis kodu sozlesmesi), A-3 (stderr kirik boru)
RC_AD = ".hafizarc"

# ---------------------------------------------------------------- yardimcilar

def duzenli_dosya(p):
    """Yalniz DUZENLI dosya okunur. Dizin/FIFO/soket/kirik link okunmaya kalkisilirsa
    ya ham traceback ya da (FIFO'da) SONSUZA KADAR ASILMA olur — ikisi de kabul edilemez."""
    try:
        st = os.stat(p)                       # link'i izler: kirik link -> OSError
    except OSError:
        return False
    return stat.S_ISREG(st.st_mode)

def oku(p):
    # FABLE Y-3: UTF-8 olmayan bir dosya ham UnicodeDecodeError traceback'i uretiyordu.
    # IKINCI TUR (bagimsiz denetim): UnicodeDecodeError TEK basina yetmiyordu —
    # dizin/FIFO/kirik link/izin hatasi hala ham traceback (FIFO'da ASILMA) veriyordu.
    if not duzenli_dosya(p):
        if os.path.isdir(p):
            oldur("DUZENLI DOSYA BEKLENIYORDU, DIZIN BULUNDU: %s" % p)
        oldur("OKUNAMIYOR (duzenli dosya degil ya da erisilemiyor): %s\n"
              "  Dizin, FIFO, soket ya da kirik sembolik link olabilir." % p)
    try:
        with open(p, encoding="utf-8", errors="strict") as f:
            return f.read()
    except UnicodeDecodeError as e:
        oldur("DOSYA UTF-8 DEGIL: %s\n"
              "  Bayt %d cozulemedi (%s).\n"
              "  Bu sistem UTF-8 sarttir (Turkce karakterler icin). Dosyayi UTF-8'e cevir:\n"
              "  Not Defteri > Farkli Kaydet > Kodlama: UTF-8  ·  VS Code > sag alt > Reopen with Encoding."
              % (p, e.start, e.reason))
    except OSError as e:
        oldur("DOSYA OKUNAMADI: %s\n  %s" % (p, e))

def yaz(p, s):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)

def satirlar(p):
    return oku(p).split("\n")

def sha(b):
    if isinstance(b, str):
        b = b.encode("utf-8")
    return hashlib.sha256(b).hexdigest().upper()

def sha_dosya(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest().upper()

def norm(s):
    """Karsilastirma normalizasyonu: NFC + sag bosluk kirpma. Icerik DEGISTIRILMEZ."""
    return unicodedata.normalize("NFC", s).rstrip()

def anlamli(s):
    """ANLAMLI SATIR = bos olmayan HER satir (basliklar ve fence-ici DAHIL)."""
    return norm(s) != ""

def anlamli_satirlar(p):
    return [norm(s) for s in satirlar(p) if anlamli(s)]


def _uretilen_haric(L):
    """URETILEN blok (v2 arsiv dizini) H1/H1-KOVA muhasebesinin DISINDADIR.
    Gerekce: o satirlar icerik degil, her `derle`de yeniden hesaplanan turevdir
    (bayt sayilari degisir). Muhasebeye alinirsa her derleme sahte bir 'KAYIP' uretir.
    Icerik kaybi riski YOK: blok tamamen silinse H6 (arsiv dizini) kirmizi yanar."""
    out, ic = [], False
    for s in L:
        d = s.strip()
        if d == V2BAS:
            ic = True; continue
        if d == V2SON:
            ic = False; continue
        if not ic:
            out.append(s)
    return out


def icerik_satirlari(p):
    return [norm(s) for s in _uretilen_haric(satirlar(p)) if anlamli(s)]

def cok_kume(liste):
    d = {}
    for s in liste:
        d[s] = d.get(s, 0) + 1
    return d

def ck_ekle(d, s):
    d[s] = d.get(s, 0) + 1

def ck_sil(d, s):
    if d.get(s, 0) > 0:
        d[s] -= 1
        if d[s] == 0:
            del d[s]
        return True
    return False

def ck_fark(a, b):
    """a'da olup b'de olmayanlar (coklukla)."""
    out = []
    for s, n in a.items():
        k = n - b.get(s, 0)
        if k > 0:
            out.extend([s] * k)
    return out

AYLAR = {"ocak": 1, "subat": 2, "mart": 3, "nisan": 4, "mayis": 5, "haziran": 6,
         "temmuz": 7, "agustos": 8, "eylul": 9, "ekim": 10, "kasim": 11, "aralik": 12}

def tarih_coz(s):
    """ISO (2026-07-28) VEYA Turkce ('25 Temmuz 2026', '25 Temmuz 2026' kalin/yildizli) okur.
    Cozemezse None doner — 'olcemiyorum' demek icin."""
    s = s.strip().strip("*").strip()
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    m = re.search(r"(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(\d{4})", s)
    if m:
        ay = AYLAR.get(slug(m.group(2)).replace("-", ""))
        if ay:
            try:
                return _dt.date(int(m.group(3)), ay, int(m.group(1)))
            except ValueError:
                return None
    # FABLE Y-10: '25.07.2026' / '25/07/2026' — Turkiye'de EN DOGAL yazim.
    # Cozulemeyince H12 ve H14 birlikte 'OLCEMIYORUM'a dusuyordu: sessiz PASS degil
    # (bu iyi) ama en dogal yazim iki tazelik kapisini birden kore ceviriyordu.
    # GUN-ONCE varsayilir (TR/AB yazimi); ay>12 ise ABD yazimi olarak ikinci deneme yapilir.
    m = re.search(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", s)
    if m:
        a1, a2, yil = int(m.group(1)), int(m.group(2)), int(m.group(3))
        for gun, ay in ((a1, a2), (a2, a1)):
            try:
                return _dt.date(yil, ay, gun)
            except ValueError:
                continue
        return None
    return None

# SIRA ONEMLIDIR ve tarih_coz ile AYNI olmalidir. BAGIMSIZ DENETIM: DD.MM.YYYY deseni
# eklenince "> Son guncelleme: surum 1.2.2026 · 2026-07-01" satirinda SURUM belirteci
# once eslesiyor, `derle` onu bugunun tarihiyle EZIYOR ve GERCEK damgayi eski birakiyordu
# (yani Y-9'un kapatmaya calistigi kusuru geri getiriyordu). Cozum: her deseni AYRI
# derle, tarih_coz'un sirasiyla dene, ILK COZULEBILENI kullan.
TARIH_DESENLERI = [
    re.compile(r"\*{0,2}\d{4}-\d{2}-\d{2}\*{0,2}"),
    re.compile(r"\*{0,2}\d{1,2}\s+[A-Za-zÇĞİÖŞÜçğıöşü]+\s+\d{4}\*{0,2}"),
    re.compile(r"\*{0,2}\d{1,2}[./]\d{1,2}[./]\d{4}\*{0,2}"),
]

def tarih_belirteci_bul(metin):
    """tarih_coz'un GERCEKTEN cozecegi ilk belirteci dondurur (match nesnesi)."""
    for desen in TARIH_DESENLERI:
        for m in desen.finditer(metin):
            if tarih_coz(m.group(0)) is not None:
                return m
    return None


def tarih_damgasini_guncelle(satir, yeni_tarih):
    """'Son güncelleme' satirindaki TARIHI yerinde degistirir; satirin geri kalanina
    DOKUNMAZ. (Eski surum ilk bosluksuz belirteci degistiriyordu ve
    '> Son güncelleme: **25 Temmuz 2026** · Güncelleyen: X' satirini BOZUYORDU.)"""
    m = re.search(r"Son g[uü]ncelleme:\s*", satir)
    if not m:
        return satir
    bas, kalan = satir[:m.end()], satir[m.end():]
    m2 = tarih_belirteci_bul(kalan)     # H12'nin OKUDUGU belirtecin AYNISI degistirilir
    if not m2:
        return bas + yeni_tarih + ((" " + kalan) if kalan and not kalan[0].isspace() else kalan)
    return bas + kalan[:m2.start()] + yeni_tarih + kalan[m2.end():]


def bugun():
    return _dt.date.today().isoformat()

def simdi_damga():
    return _dt.datetime.now().strftime("%Y-%m-%d-%H%M")

def slug(s):
    s = unicodedata.normalize("NFKD", s)
    tr = {"ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
          "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"}
    s = "".join(tr.get(c, c) for c in s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    # BAGIMSIZ DENETIM: cok uzun bir --baslik dosya adina donunce ham
    # "OSError: [Errno 36] File name too long" veriyordu. Dosya sistemi siniri 255;
    # onek ("0001-") ve uzanti icin pay birakilir.
    if len(s) > 120:
        s = s[:120].rstrip("-")
    return s or "konu"

def kok_bul(arg):
    if arg:
        k = os.path.abspath(arg)
        if not os.path.isdir(k):
            oldur("--kok yolu YOK: " + k)
        return k
    if os.environ.get("HAFIZA_KOK"):
        k = os.path.abspath(os.environ["HAFIZA_KOK"])
        if not os.path.isdir(k):
            oldur("HAFIZA_KOK yolu YOK: " + k)
        return k
    d = os.path.abspath(os.getcwd())
    while True:
        if os.path.isfile(os.path.join(d, RC_AD)):
            return d
        ust = os.path.dirname(d)
        if ust == d:
            break
        d = ust
    oldur("Kok BELIRSIZ. --kok=<dizin> ver ya da HAFIZA_KOK tanimla ya da "
          + RC_AD + " bulunan bir dizinde kos. Sessizce cwd'ye DUSULMUYOR.")

SON_HATA = [""]          # kapi yalitimi icin: oldur()'un son mesaji

def oldur(msg, kod=2):
    SON_HATA[0] = msg
    sys.stderr.write("HATA: " + msg + "\n")
    sys.exit(kod)

def kapi_yalit(O, etiket, fn, *args, **kw):
    """BAGIMSIZ DENETIM: tek bir arsiv dosyasindaki tek bozuk bayt, ILGISIZ 15 kapinin
    da olcumunu iptal ediyordu (oku() -> oldur() -> SystemExit). Aracin kendi ilkesi
    "olcemedigine OLCEMIYORUM der" ve bu KAPI BASINA bir hukumdur. Bu sarmalayici
    olcumu yalitir: basarisiz kapi OLCULEMEDI olur, digerleri RAPORLANIR."""
    SON_HATA[0] = ""
    try:
        return True, fn(*args, **kw)
    except SystemExit:
        ilk = (SON_HATA[0] or "okunamadi").split("\n")[0]
        O.append("%s: OLCULEMEDI — %s" % (etiket, ilk[:150]))
        return False, None

VARSAYILAN_RC = {
    "surum": SURUM,
    "canli": "PROJE_HAFIZA.md",
    "kural_evi_dosya": "CLAUDE.md",
    "tavan_kb": 60,
    "bayatlik_gun": 30,
    "zorunlu_bolumler": [
        "## GUNCEL DURUM", "## SONRAKI ADIM", "## ACIK KARARLAR",
        "## SABIT CERCEVE", "## KIRMIZI CIZGILER", "## KARAR GUNLUGU", "## ARSIV DIZINI"
    ],
    "kural_evi_bolumleri": ["## SABIT CERCEVE", "## KIRMIZI CIZGILER"],
    "kural_isaretleri": ["PAZARLIKSIZ", "MUTLAK KURAL", "KIRMIZI CIZGI", "ASLA"],
    "arsiv_turleri": ["gorev", "test", "kanit", "bulgu", "tasarim", "taslak"],
    "kanonik_artefakt": "",
    "hafiza_gecikme_gun": 2,
    "hafiza_dizini": "arsiv/hafiza",
    "ek_arsiv_dosyalari": [],
}

def rc_oku(kok):
    p = os.path.join(kok, RC_AD)
    if not os.path.isfile(p):
        oldur(RC_AD + " yok — once: python hafiza.py kur --kok=<dizin>")
    d = dict(VARSAYILAN_RC)
    kullanici = _json_coz(RC_AD, oku(p))
    if not isinstance(kullanici, dict):
        oldur("%s bir JSON nesnesi olmali (su an: %s)" % (RC_AD, type(kullanici).__name__))
    d.update(kullanici)
    # Y-3: yapilandirma SINIRDA dogrulanir. Iki ayri zarar vardi:
    #  - sayisal alan metin olursa (tavan_kb: "abc") kapinin ortasinda ham ValueError,
    #  - liste alani metin olursa (kural_isaretleri: "ASLA") for dongusu KARAKTER
    #    geziyordu; kapi cokmuyor ama YANLIS olcuyordu — bu daha kotusu.
    # bayatlik_gun=0 MESRUDUR (en KATI ayar: "her gun guncelle"); hafiza_gecikme_gun=0
    # de bilincli kapatmadir. Ikisine de 1 dayatmak, DUN gecerli bir .hafizarc'i BUGUN
    # kullanilamaz yapardi — bagimsiz denetimde regresyon olarak olculdu.
    for alan, en_az in (("tavan_kb", 1), ("bayatlik_gun", 0), ("hafiza_gecikme_gun", 0)):
        d[alan] = tamsayi(d.get(alan), "%s > %s" % (RC_AD, alan), en_az=en_az)
    for alan in ("zorunlu_bolumler", "kural_evi_bolumleri", "kural_isaretleri",
                 "arsiv_turleri", "ek_arsiv_dosyalari"):
        if not isinstance(d.get(alan), list):
            oldur("%s > %s bir LISTE olmali (su an: %s). Ornek: \"%s\": [\"...\"]\n"
                  "  Metin yazilirsa kapi CAKMAZ ama harf harf gezer — sessizce yanlis olcer."
                  % (RC_AD, alan, type(d.get(alan)).__name__, alan))
        for e in d[alan]:
            if not isinstance(e, str):
                oldur("%s > %s icinde metin-olmayan oge var: %r" % (RC_AD, alan, e))
    for alan in ("canli", "kural_evi_dosya", "hafiza_dizini", "kanonik_artefakt"):
        if not isinstance(d.get(alan), str):
            oldur("%s > %s bir METIN olmali (su an: %s)"
                  % (RC_AD, alan, type(d.get(alan)).__name__))
    if not d["canli"].strip():
        oldur("%s > canli BOS olamaz (canli hafiza dosyasinin adi)" % RC_AD)
    # YOL alanlarinin ICERIGI de sinirda dogrulanir: mutlak yol / '..' / NUL bayti,
    # os.listdir icinde ham FileNotFoundError / ValueError uretiyordu (olculdu).
    for alan in ("canli", "kural_evi_dosya", "hafiza_dizini"):
        v = d[alan]
        if "\x00" in v:
            oldur("%s > %s NUL bayti iceriyor — gecersiz yol." % (RC_AD, alan))
        if os.path.isabs(v) or (len(v) > 1 and v[1] == ":"):
            oldur("%s > %s MUTLAK yol olamaz (proje kokune GORE olmali): %r"
                  % (RC_AD, alan, v))
        if ".." in v.replace("\\", "/").split("/"):
            oldur("%s > %s '..' iceremez (proje kokunun disina cikamaz): %r"
                  % (RC_AD, alan, v))
    if not d["hafiza_dizini"].strip().strip("/\\"):
        oldur("%s > hafiza_dizini BOS olamaz (ornek: \"arsiv/hafiza\")" % RC_AD)
    # politika gerekceleri: H15 "bilincliyse gerekce yaz" diyor — o gerekcenin
    # OKUNDUGU yer burasi (yoksa mesaj YERINE GETIRILEMEYEN bir talimat olurdu).
    if not isinstance(d.get("politika_gerekce", {}), dict):
        oldur("%s > politika_gerekce bir NESNE olmali (ornek: "
              "{\"tavan_kb\": \"devralinan dosya 2 MB\"})" % RC_AD)
    d.setdefault("politika_gerekce", {})
    return d

# ------------------------------------------------------- beyan defterleri (Y-3)
#
# FABLE Y-3 — HAM TRACEBACK SINIFI.
# Defterler (_KOVA / _DUZELTMELER / _KORUNAN / _CIPA / _TASINMA / _ZINCIR) ELLE
# duzenlenebilen dosyalardir; birinin bozulmasi cok muhtemeldir. Bozulunca program
# ham Python traceback'i veriyordu. Bunun iki zarari var:
#   (1) Hukum yanlis okunuyor: traceback "ARAC bozuk" der, oysa dogru hukum
#       "DEFTER bozuk, elle duzelt"tir.
#   (2) Bir denetimde ham traceback "bu arac olgun degil" delili sayilir.
# Bu yuzden BUTUN defter okumalari tek kapidan gecer ve BICIM de dogrulanir.
# Defterler denetim izidir: burada asla otomatik onarim yapilmaz, yalniz temiz hata.

def defter_hata(ad, mesaj):
    oldur("DEFTER BOZUK — %s\n  %s\n"
          "  Defterler DENETIM IZIDIR; bu arac onlari otomatik ONARMAZ.\n"
          "  Yol: elle duzelt ya da surum kontrolunden geri al, sonra:\n"
          "       python hafiza.py muhur \"defter elle duzeltildi: <neden>\"" % (ad, mesaj))

def _json_coz(ad, metin):
    """IKINCI TUR DERSI: json.loads YALNIZ JSONDecodeError atmaz.
    Asiri ic-ice girdi -> RecursionError; 4300+ haneli sayi -> ValueError (Py3.11+).
    Ikisi de bagimsiz denetimde ham traceback uretti. Hepsi burada kapanir."""
    try:
        return json.loads(metin)
    except json.JSONDecodeError as e:
        defter_hata(ad, "gecersiz JSON — satir %d, sutun %d: %s" % (e.lineno, e.colno, e.msg))
    except RecursionError:
        defter_hata(ad, "JSON COK DERIN IC ICE — ayristirilamadi (makul olmayan derinlik).")
    except ValueError as e:
        defter_hata(ad, "JSON degeri islenemedi: %s" % e)

def defter_yukle(p, bos):
    """JSON defterini temiz hatayla yukler. Yoksa `bos`in KOPYASINI dondurur."""
    ad = os.path.basename(p)
    if not os.path.isfile(p):
        return json.loads(json.dumps(bos))
    v = _json_coz(ad, oku(p))           # oku(): UTF-8 / dizin / FIFO hatasini temizler
    if not isinstance(v, type(bos)) or isinstance(v, bool) != isinstance(bos, bool):
        defter_hata(ad, "en ust duzey %s olmali, %s bulundu."
                    % (type(bos).__name__, type(v).__name__))
    return v

def _tip_adi(t):
    return "/".join(x.__name__ for x in (t if isinstance(t, tuple) else (t,)))

def defter_liste(p, anahtar, alan_tipleri):
    """{anahtar: [ {...} ]} defterini yukler; her kaydin alanlarini VE TIPLERINI dogrular.

    IKINCI TUR DERSI: alanin VAR olmasi yetmiyordu. `_KORUNAN.json > dosya: 5` gibi
    yanlis TIPLI bir alan, os.path.join / re.escape / unicodedata.normalize icinde
    ham TypeError traceback'i uretiyordu. Sema sinirda dogrulanir."""
    ad = os.path.basename(p)
    d = defter_yukle(p, {anahtar: []})
    kayitlar = d.get(anahtar, [])
    if not isinstance(kayitlar, list):
        defter_hata(ad, "'%s' bir liste olmali, %s bulundu." % (anahtar, type(kayitlar).__name__))
    for i, k in enumerate(kayitlar, 1):
        if not isinstance(k, dict):
            defter_hata(ad, "'%s' icindeki %d. kayit nesne degil (%s)."
                        % (anahtar, i, type(k).__name__))
        for alan, tip in alan_tipleri.items():
            if alan not in k:
                defter_hata(ad, "'%s' icindeki %d. kayitta zorunlu alan yok: %s"
                            % (anahtar, i, alan))
            if not isinstance(k[alan], tip) or isinstance(k[alan], bool):
                defter_hata(ad, "'%s' icindeki %d. kayitta '%s' alani %s olmali, %s bulundu."
                            % (anahtar, i, alan, _tip_adi(tip), type(k[alan]).__name__))
    d[anahtar] = kayitlar
    return d

def metin_listesi(deger, ad, alan):
    """Bir listenin TUM ogeleri metin mi? (norm()/join() TypeError'lerinin kaynagi)"""
    if not isinstance(deger, list):
        defter_hata(ad, "'%s' bir liste olmali, %s bulundu." % (alan, type(deger).__name__))
    for i, e in enumerate(deger, 1):
        if not isinstance(e, str):
            defter_hata(ad, "'%s' icindeki %d. oge metin degil (%s): %r"
                        % (alan, i, type(e).__name__, e))
    return deger

def jsonl_yukle(p, zorunlu_alanlar, atla_bos=True):
    """Satir-basina-JSON defterini temiz hatayla yukler."""
    ad = os.path.basename(p)
    if not os.path.isfile(p):
        return []
    cikti = []
    for n, s in enumerate(oku(p).split("\n"), 1):
        if not s.strip():
            if atla_bos:
                continue
        k = _json_coz("%s (%d. satir)" % (ad, n), s)
        if not isinstance(k, dict):
            defter_hata(ad, "%d. satir bir nesne degil (%s)." % (n, type(k).__name__))
        eksik = [alan for alan in zorunlu_alanlar if alan not in k]
        if eksik:
            defter_hata(ad, "%d. satirda zorunlu alan yok: %s" % (n, ", ".join(eksik)))
        cikti.append(k)
    return cikti

def kok_disina_mi(kok, p0):
    """Yol PROJE AGACININ DISINA mi cikiyor? (realpath tabanli, ara bilesenler dahil)

    BAGIMSIZ DENETIM 4. TUR — uc ayri kacis olculdu:
      K-1 HARDLINK: islink() False, realpath proje icini gosterir; tek ayirt edici
          olcut st_nlink > 1'dir (ayni inode disarida da adlandirilmis).
      K-2 ARA DIZIN: link 'arsiv'te, 'arsiv/hafiza'da degil -> islink(yaprak) False.
          Bu yuzden 'islink(d) and _kacis(d)' YANLISTI; kosul yalniz kacis olmali.
      K-3 realpath zaten ara bilesenleri cozer; onemli olan LISTEYE almaktir.

    FABLE 3. TUR · B-2/B-3: bu islev yol_on_kontrol'un ICINDE kapali bir yardimciydi,
    yani YALNIZ .hafizarc'tan tureyen yollara uygulanabiliyordu. CLI'dan gelen
    --hedef / --dosya / --canli hicbir zaman buradan gecmiyordu ve `emekli --hedef`
    proje agacinin DISINA kalici yaziyordu (kapi YESIL, exit 0). Modul duzeyine
    cikarildi ki TEK bir kacis tanimi olsun ve her yol ayni kapidan gecsin."""
    try:
        g = os.path.realpath(p0)
        k = os.path.realpath(kok)
    except OSError:
        return True
    return not (g == k or g.startswith(k + os.sep))

def cli_yol_coz(kok, deger, arg_adi, taban=None):
    """CLI'dan gelen HER yol argumaninin gectigi TEK KAPI.

    FABLE 3. TUR DERSI: 4. turda kacis sinifini symlink/hardlink icin kapatip
    CLI argumani icin acik birakmisim; denetci "baktigin vektoru kapattin, SINIFI
    degil" dedi ve haklıydı. Bu yuzden duzeltme tek tek yuzeylere degil, bir
    GECIDE yapildi: yeni bir yol argumani eklendiginde de buradan gecmek zorunda.

    Reddedilenler: NUL bayti · proje agacinin disina cikan her yol (mutlak yol,
    `../` ile tirmanma, symlink ile disari baglanan yol). Kabul: kok-goreli
    (ya da `taban`-goreli) ve realpath'i kok agacinda kalan yollar."""
    if deger is None:
        return None
    if "\x00" in deger:
        oldur("%s NUL bayti iceriyor — gecersiz yol." % arg_adi)
    # D-1: POSIX'te '\\' dosya adinda MESRU bir karakterdir; yalniz Windows'ta ayractir.
    ham = deger.replace("\\", "/") if os.sep == "\\" else deger
    parcalar = [x for x in ham.split("/") if x not in ("", ".")]
    if os.path.isabs(deger) or (len(deger) > 1 and deger[1] == ":"):
        tam = deger                       # mutlak: oldugu gibi coz, asagida reddedilir
    else:
        tam = os.path.join(taban or kok, *parcalar) if parcalar else (taban or kok)
    if kok_disina_mi(kok, tam):
        oldur("%s PROJE AGACININ DISINA cikiyor: %s\n"
              "  Cozumlenen yol: %s\n"
              "  Kok           : %s\n"
              "  Hafiza ve denetim izi proje agacinin DISINDA yasayamaz; disari yazmak\n"
              "  ya da disaridan okumak bu araca YASAKTIR (mutlak yol ve '..' dahil)."
              % (arg_adi, deger, os.path.realpath(tam), os.path.realpath(kok)))
    return tam

def kok_goreli(kok, tam):
    """Deftere YAZILACAK kanonik bicim: proje kokune GORELI, '/' ayracli.

    IC DENETIM (O-5): `korunan` kullanicinin verdigi HAM metni (`/mutlak/yol/X.md`,
    `./X.md`, `a/../X.md`) deftere yaziyordu. Sonuclari: (a) proje tasininca H8
    "KORUNAN dosya yok" diyor ve proje tasinamaz/klonlanamaz hale geliyor,
    (b) _KORUNAN.json surum kontrolune YEREL MUTLAK YOL siziyor, (c) tekillestirme
    ham metne baktigi icin AYNI dosya icin dort ayri korunan blok acilabiliyor."""
    try:
        rel = os.path.relpath(os.path.realpath(tam), os.path.realpath(kok))
    except (OSError, ValueError):
        rel = tam
    # D-1: ayrac cevirisi yalniz Windows'ta; POSIX'te '\\' dosya adinin PARCASIDIR.
    return rel.replace("\\", "/") if os.sep == "\\" else rel

def yol_on_kontrol(y, dizinler=(), dosyalar=(), sessiz=False):
    """Beklenen DIZIN gercekten dizin mi, beklenen DOSYA gercekten duzenli dosya mi?

    BAGIMSIZ DENETIM 2. TUR: bu kontrol yokken `arsiv/hafiza` silinmis/dosya yapilmis,
    `gunluk` dosya, `_ZINCIR.jsonl` DIZIN gibi hallerde arac os.listdir/os.makedirs/
    open icinde patliyor ve "BEKLENMEYEN DURUM — ARAC KUSURU" diyordu. Oysa hukum
    "PROJE YAPISI bozuk"tur. Ayrica _ZINCIR.jsonl bir FIFO ise append SONSUZA KADAR
    ASILIYORDU — burada yakalanir."""
    cok_adli = []

    def _kacis(p0):
        """TEK TANIM: modul duzeyindeki kok_disina_mi'ye baglidir (B-2/B-3)."""
        return kok_disina_mi(y.kok, p0)

    _ic_ad_onbellek = {}

    def _proje_ici_ad_sayisi(dev, ino):
        """Proje agacinda ayni inode'u tasiyan ad sayisi (bir kez taranir)."""
        if not _ic_ad_onbellek:
            _ic_ad_onbellek["_"] = {}
            # BAGIMSIZ DENETIM 6. TUR: hariç tutulan dizinlerdeki (.git/node_modules)
            # proje ICI bir ad, "proje DISINDA ad var" diye YANLIS etiketleniyordu.
            # Sayim, proje agacinin TAMAMINI gezmelidir — burada aradigimiz sey
            # "kac ad proje icinde", dizinin turu onemli degil.
            for r0, d0, f0 in os.walk(y.kok):
                for f in f0:
                    try:
                        st0 = os.lstat(os.path.join(r0, f))
                    except OSError:
                        continue
                    if stat.S_ISREG(st0.st_mode) and st0.st_nlink > 1:
                        k0 = (st0.st_dev, st0.st_ino)
                        _ic_ad_onbellek["_"][k0] = _ic_ad_onbellek["_"].get(k0, 0) + 1
        return _ic_ad_onbellek["_"].get((dev, ino), 0)

    def _cok_adli(p0):
        """Ayni icerik PROJE DISINDA da adlandirilmis mi?

        BAGIMSIZ DENETIM 5. TUR (ENGELLEYICI): ilk halim yalnizca st_nlink > 1'e
        bakiyordu — yani "baska ad var mi" diye soruyordu, oysa sorulmasi gereken
        "proje DISINDA ad var mi". Sonuc: `cp -al` / `rsync --link-dest` ile alinmis
        siradan bir yedek, ORIJINAL projede HER komutu exit 2 ile durduruyordu.
        Dogru olcum: proje agacindaki ayni inode adlarini say; sayi st_nlink'e esitse
        disarida ad YOKTUR."""
        try:
            st = os.stat(p0)
        except OSError:
            return False
        if not stat.S_ISREG(st.st_mode) or st.st_nlink <= 1:
            return False
        return _proje_ici_ad_sayisi(st.st_dev, st.st_ino) < st.st_nlink
    for d in dizinler:
        if os.path.lexists(d):
            if not os.path.isdir(d):
                oldur("DIZIN OLMASI GEREKEN YOL DIZIN DEGIL: %s\n"
                      "  Bir dosya, kirik link ya da link dongusu kaplamis olabilir.\n"
                      "  Tasi ya da sil, sonra komutu yinele." % d)
            if _kacis(d):
                oldur("DIZIN PROJE DISINA BAGLI: %s -> %s\n"
                      "  Hafiza ve denetim izi proje agacinin DISINDA yasayamaz "
                      "(surum kontrolu kapsamaz, sessizce yok olabilir)." % (d, os.path.realpath(d)))
    for f in dosyalar:
        # os.path.exists() KIRIK LINK ve LINK DONGUSU icin False doner — bagimsiz
        # denetimde bu delik uzerinden `derle`/`muhur` zinciri PROJE DISINA yazdi ve
        # kapi YESIL kaldi. lexists() ikisini de gorur.
        if not os.path.lexists(f):
            continue
        if _kacis(f):
            oldur("DEFTER/DOSYA PROJE DISINA BAGLI: %s -> %s\n"
                  "  Denetim izi proje agacinin DISINDA tutulamaz." % (f, os.path.realpath(f)))
        if _cok_adli(f):
            # BAGIMSIZ DENETIM 5. TUR: bunu OLDURUCU yapmak asiriydi — `cp -al` /
            # `rsync --link-dest` ile alinmis SIRADAN bir yedek, orijinal projede her
            # komutu durduruyordu. Disarida bir ad olmasi bir GERCEKTIR (yazma oraya da
            # islenir), ama hafiza disiplininin ihlali DEGILDIR. Dogru davranis:
            # RAPORLA, DURDURMA. Kapi bunu bulgu yapar; yazan komut uyarir ve devam eder.
            cok_adli.append(f)
        if not duzenli_dosya(f):
            oldur("DUZENLI DOSYA OLMASI GEREKEN YOL BOYLE DEGIL: %s\n"
                  "  Dizin, FIFO, soket, kirik link ya da link dongusu olabilir. "
                  "Bu yol YAZILAMAZ." % f)
    if cok_adli and not sessiz:
        sys.stderr.write(
            "UYARI: %d dosyanin proje DISINDA da bir adi var (hardlink). Bu dosyalara\n"
            "  yazmak oradaki adi da degistirir (ornek: 'cp -al' ile alinmis bir yedek).\n"
            "  Islem SURUYOR; olcum icin: python hafiza.py kapi\n  - %s\n"
            % (len(cok_adli), "\n  - ".join(os.path.relpath(x, y.kok).replace("\\", "/")
                                             for x in cok_adli[:4])))
    return cok_adli

def _korunacak_dosyalar(y, rc=None):
    """yol_on_kontrol'e verilecek TAM dosya listesi. K-3: eskiden yalniz 9 sabit defter
    ve canli vardi; HAFIZA_*.md arsiv hedefleri, politika dosyalari ve ek_arsiv_dosyalari
    kapsam disindaydi ve `emekli --hedef` disariya yaziyordu."""
    d = [y.zincir, y.kova, y.duzelt, y.tasinma, y.korunan, y.cipa, y.snap,
         y.yeni, y.canli, y.kural, y.plan, y.konular]
    if os.path.isdir(y.h):
        try:
            d += [os.path.join(y.h, f) for f in sorted(os.listdir(y.h))
                  if re.match(r"^HAFIZA_.*\.md$|^_BLOKLASTIRMA_ONCESI_.*\.md$", f)]
        except OSError:
            pass
    # bugun yazilacak bloklastirma yedegi henuz YOKKEN de kapsanmali
    d.append(os.path.join(y.h, "_BLOKLASTIRMA_ONCESI_%s.md" % bugun()))
    for rel in (rc or {}).get("ek_arsiv_dosyalari", []):
        if isinstance(rel, str):
            d.append(_yol(y.kok, rel))
    return tuple(d)

KILIT = [None, None]        # [yol, inode] — inode: B-7 (yaris penceresi)

def kilit_al(y):
    """Yazan komutlar icin TEK YAZAR kilidi.

    BAGIMSIZ DENETIM 7. TUR (ORTA-YUKSEK): hicbir yazma komutunda kilit yoktu; iki
    oturum ayni anda `derle` kosunca ikisi de canliyi okuyup ayri ayri yaziyor,
    ikinci yazim birincinin blogunu EZIYORDU -> H1 'KAYIP' + kalici kirmizi
    (13 denemenin 2'sinde uretildi). `derle` oturum kapanisinin standart komutu
    oldugu icin bu olagan bir senaryo."""
    os.makedirs(y.h, exist_ok=True)
    p = os.path.join(y.h, ".kilit")
    rel = os.path.relpath(p, y.kok).replace("\\", "/")
    # FABLE 3. TUR · B-9: `.kilit` bir DIZIN ise once alakasiz "DUZENLI DOSYA
    # BEKLENIYORDU" sonra "BASKA YAZMA ISLEMI SURUYOR" basiliyordu; os.remove bir
    # dizini silemedigi icin kilit KALICI oluyor ve tani YANLIS yonlendiriyordu.
    # Tek, dogru hukum:
    if os.path.isdir(p) and not os.path.islink(p):
        oldur("KILIT YOLU BIR DIZIN: %s\n"
              "  Bu bir kilit degil; arac onu ne alabilir ne birakabilir "
              "(kalici kilit).\n"
              "  Elle kaldir (icini bosaltip dizini sil), sonra: python hafiza.py kapi"
              % rel)
    try:
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        sahip = ""
        try:
            sahip = oku(p).strip()[:120]
        except SystemExit:
            pass
        # FABLE 3. TUR · B-5 kardesi: "islem yoksa sil" tavsiyesi kullaniciyi
        # bayat kilit silmeye itiyordu ama BAYAT MI degil mi olculmuyordu.
        # Olcup soyluyoruz; SILMIYORUZ (pid yeniden kullanimi yanlis devralma uretir).
        oldur("BASKA BIR YAZMA ISLEMI SURUYOR (kilit: %s)\n"
              "  %s\n"
              "  Tani: %s\n"
              "  Ayni anda iki yazma, canli hafizada KAYIP GUNCELLEME uretir.\n"
              "  Oteki islem bittiginde yeniden dene."
              % (rel, sahip, _kilit_tanisi(sahip, rel)))
    # B4-1 (Fable 4. tur, YUKSEK) — SAHIPLIK, O_EXCL BASARILI OLUR OLMAZ KAYDEDILIR.
    # Eskiden bu iki atama asagidaki `with` blogundan SONRAYDI. ENOSPC gibi bir hal
    # yazmayi (ya da kapanistaki flush'i) dusurdugunde sahiplik HIC kaydedilmiyordu;
    # atexit'teki `kilit_birak` ilk satirinda `if not p: return` ile cikiyor, dosya
    # KALIYOR ve proje KALICI olarak yazmaya kapaniyordu — arac ici cikis yolu yok.
    # Olculdu: faz0/ortam_olcum.sh B4-1 kolu ("disk bosaldiktan sonra kalan .kilit: 1").
    # Sira artik dogru: once SAHIPLENIR, sonra yazilir. Yazma duserse kilit BIZIMDIR
    # ve birakilir.
    KILIT[0] = p
    # IC DENETIM (B-7): "pid yoksa bizimdir" kurali, BASKA bir surecin O_EXCL ile
    # actigi ama pid'ini HENUZ yazmadigi kilidi de silebiliyordu (mikrosaniyelik
    # pencere; aracin kendi tavsiyesi 'kilidi elle sil' oldugu icin senaryo gercekci).
    # Artik olusturdugumuz dosyanin KIMLIGINI (inode) sakliyoruz; birakirken ayni
    # dosya degilse dokunmuyoruz. `stat(p)` DEGIL `fstat(fd)`: yol yeniden cozulurse
    # araya baska bir dosya girebilir; fd elimizdeki dosyanin ta kendisidir.
    try:
        KILIT[1] = os.fstat(fd).st_ino
    except OSError:
        KILIT[1] = None
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write("pid=%d · %s · komut: %s\n"
                % (os.getpid(), _dt.datetime.now().isoformat(timespec="seconds"),
                   " ".join(sys.argv[1:])[:100]))
    return p

def agactaki_kilitler(kok):
    """Proje agacindaki TUM `.kilit` dosyalarini bulur (goreli yollar).

    A-1'IN KENARI (v2.4.1): `devral` kilidini YENI ad alaninda alir
    (`arsiv/hafiza/v2/.kilit`); dolayisiyla ESKI ad alanindaki bir yazari
    (`arsiv/hafiza/.kilit`) GOREMEZ — oysa ikisi de AYNI canli hafiza dosyasina
    yazar. `kilit_al`i tek bir yola baglamak SINIFI degil O YOLU kapatir.
    Sinir: agactaki her kilit. (`devral` zaten tum agaci `onceki_kurulum_izleri`
    icin tariyor; bu tarama ek maliyet getirmez.)"""
    bulunan = []
    haric = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}
    try:
        for r0, d0, f0 in os.walk(kok):
            d0[:] = [d for d in d0 if d not in haric]
            for f in f0:
                if f == ".kilit":
                    bulunan.append(os.path.relpath(os.path.join(r0, f), kok)
                                   .replace("\\", "/"))
    except OSError:
        pass                      # tarayamiyorsak "yok" DEMEYIZ; cagiran yeri okur
    return sorted(bulunan)


def _kilit_pid(metin):
    """Kilit dosyasindaki pid (yoksa None)."""
    m = re.search(r"pid=(\d+)", metin or "")
    return int(m.group(1)) if m else None

def _surec_yasiyor_win(pid):
    """Windows'ta pid canliligi. os.kill(pid, 0) BURADA VARLIK SINAMAZ.

    Y-1 (Faz A, dokunus 1) — OLCULDU (CI run #2, faz0/win_kill_probu.py, win32
    py3.11): os.kill(pid, 0) hem YASAYAN hem OLU pid icin ISTISNA ATMADI.
    Sebep: Windows'ta `signal.CTRL_C_EVENT == 0`'dir; cagri bir varlik sinamasi
    degil Ctrl+C YAYINI denemesidir (bpo-14480 CLOSED-REJECTED). Cagri zararsiz
    (olculdu: cocuk surec hayatta kaldi) ama HICBIR SEY OLCMEZ — asagidaki POSIX
    dalinin `except (OSError, AttributeError)` kolu Windows'ta HIC calismaz ve
    teshis HER ZAMAN "pid YASIYOR" der. Sonucu: bayat kilit asla taninamaz,
    B4-1'in sizan kilidi Windows'ta temizlenemez, ve arac kullaniciya kendinden
    emin bicimde YANLIS seyi soyler.

    ctypes STDLIB'dir; CLAUDE.md 4'teki sifir-bagimlilik cizgisi korunur.
    Donusler — 'bilmiyorum' ile 'yok' BILEREK ayrilir (doktrin 2):
      handle + STILL_ACTIVE           -> True   surec VAR ve calisiyor
      handle + baska cikis kodu       -> False  surec BITMIS (handle acik kalmis)
      ERROR_ACCESS_DENIED (5)         -> True   surec VAR, erisemiyoruz
      ERROR_INVALID_PARAMETER (87)    -> False  boyle bir pid YOK
      baska hata / ctypes yok         -> None   OLCULEMEDI

    BILINEN SINIR (olculmedi): STILL_ACTIVE 259'dur ve 259 ayni zamanda gecerli
    bir cikis kodudur. Tam 259 ile cikmis bir surec 'yasiyor' gorunur. Nadir;
    daha genis cozum (job object / surec baslangic zamani) bu turun disinda."""
    try:
        import ctypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.OpenProcess.restype = ctypes.c_void_p     # 64-bit handle c_int'e SIGMAZ
        k32.OpenProcess.argtypes = (ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong)
        k32.CloseHandle.argtypes = (ctypes.c_void_p,)
        h = k32.OpenProcess(0x1000, False, pid)       # QUERY_LIMITED_INFORMATION
        if not h:
            _hata = ctypes.get_last_error()
            if _hata == 5:                            # ERROR_ACCESS_DENIED
                return True
            if _hata == 87:                           # ERROR_INVALID_PARAMETER
                return False
            return None
        try:
            k32.GetExitCodeProcess.argtypes = (ctypes.c_void_p,
                                               ctypes.POINTER(ctypes.c_ulong))
            _kod = ctypes.c_ulong(0)
            if k32.GetExitCodeProcess(h, ctypes.byref(_kod)):
                return _kod.value == 259              # STILL_ACTIVE
            return None
        finally:
            k32.CloseHandle(h)
    except Exception:                                 # noqa: BLE001
        return None                                   # OLCULEMEDI — 'yok' DEMEYIZ


def _surec_yasiyor(pid):
    """pid hala calisiyor mu? Olcemiyorsak None doneriz — 'yok' DEMEYIZ."""
    if pid is None:
        return None
    if sys.platform == "win32":
        return _surec_yasiyor_win(pid)
    try:
        os.kill(pid, 0)                       # POSIX: sinyal yollamadan varlik sinamasi
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True                           # baskasinin sureci: VAR
    except (OSError, AttributeError):
        return None                           # kisitli ortam: OLCEMIYORUZ

def _kilit_yasi(metin):
    """Kilit dosyasindaki zaman damgasindan yas (saniye); cozulemezse None."""
    m = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", metin or "")
    if not m:
        return None
    try:
        return (_dt.datetime.now() - _dt.datetime.fromisoformat(m.group(1))).total_seconds()
    except ValueError:
        return None

def _kilit_tanisi(sahip, rel):
    pid = _kilit_pid(sahip)
    yasiyor = _surec_yasiyor(pid)
    if pid is None:
        return ("kilit dosyasinda pid YOK — yarim yazilmis (ornegin disk dolarken) ya da "
                "elle olusturulmus. Sahibi belirlenemedigi icin BU KILIT BAYAT SAYILIR: "
                "%s dosyasini sil, sonra `python hafiza.py kapi` ile durumu OLC." % rel)
    if yasiyor is True:
        # O-3: elimizdeki zaman damgasini KULLAN. pid yeniden kullanimi siradan bir
        # olaydir (kutu yeniden basladi, konteyner yeniden kuruldu); "YASIYOR, BEKLE"
        # demek kullaniciyi SONSUZA KADAR bekletebilirdi.
        yas = _kilit_yasi(sahip)
        if yas is not None and yas > 3600:
            return ("pid %d su an yasiyor gorunuyor AMA kilit %.1f saat once yazilmis — "
                    "bu araci hicbir komutu o kadar surmez. Buyuk olasilikla pid YENIDEN "
                    "KULLANILMIS (kutu/konteyner yeniden basladi). Islemin surdugunden "
                    "emin degilsen %s dosyasini sil." % (pid, yas / 3600.0, rel))
        return "pid %d YASIYOR — gercekten suren bir islem var, BEKLE" % pid
    if yasiyor is False:
        return ("pid %d ARTIK YOK — bu kilit BAYAT (cokme kalintisi). Silmen guvenli: "
                "%s dosyasini sil, sonra `python hafiza.py kapi` ile durumu OLC. "
                "Arac OTOMATIK silmez: pid yeniden kullanimi yanlis devralma uretebilir "
                "ve kilit tam da kayip guncellemeyi onlemek icin var." % (pid, rel))
    return ("pid %d icin canlilik OLCULEMEDI (bu platformda sinanamiyor) — "
            "islemin bittiginden EMINSEN kilidi elle sil" % pid)

def kilit_birak():
    """FABLE 3. TUR · B-5: eskiden kosulsuz os.remove yapiyordu. Kilit bayat sanilip
    elle silinir ve yerine YENI bir yazicinin kilidi konursa, bu surecin atexit'i
    O YENI YAZICININ kilidini siliyordu — yani kilidin var olus nedeni (tek yazar)
    tam da yaris aninda cokuyordu. Artik SAHIPLIK dogrulanir: dosyadaki pid benim
    pid'im degilse DOKUNULMAZ."""
    p, ino = KILIT[0], KILIT[1]
    KILIT[0] = KILIT[1] = None
    if not p:
        return
    try:
        if not os.path.isfile(p):
            return
        if ino is not None and os.stat(p).st_ino != ino:
            return                            # B-7: bu ARTIK bizim actigimiz dosya degil
        with open(p, encoding="utf-8", errors="replace") as f:
            icerik = f.read()
        # BAGIMSIZ DENETIM (v2.4 ic tur) · Y-4: kosul "pid benim degilse dokunma"
        # idi; ama ENOSPC gibi bir hal `kilit_al`in O_EXCL ile ACTIGI dosyaya pid
        # YAZAMADAN dusururse icerik BOS kalir ve pid None olur -> KENDI biraktigimiz
        # kilidi bir daha SILEMEZ, proje KALICI olarak yazmaya kapanirdi (olculdu).
        # Dogru kural: KILIT[0] doluysa bu dosyayi BIZ olusturduk (O_EXCL). Yalniz
        # icinde BASKA bir pid varsa dokunmayiz; pid yoksa bizimdir, sileriz.
        _p = _kilit_pid(icerik)
        if _p is not None and _p != os.getpid():
            return                            # BASKASININ kilidi — dokunma
        os.remove(p)
    except OSError:
        pass

def zincir_butunlugu_sart(y):
    """Yazmadan ONCE: zincir VAR ve BOS DEGIL mi?

    KENDI BULDUGUMUZ, B-1'IN KARDESI (denetci yalniz 0-bayta indirmeyi olcmustu):
    zinciri SILMEK de ayni aklamayi yapiyordu. Silinmis zincirde `muhur` yeni bir
    GENESIS halkasi yaziyor, o halkanin yuku TAHRIF EDILMIS dosyalarin SHA'larini
    kapsiyor ve tahrif mesru bir zincirle KALICI olarak temize cikiyordu.

    IC DENETIM (Y-5): ILK duzeltmem capayi `_CIPA.json`'a baglamisti — yani saldirgan
    TEK BIR `rm _CIPA.json` ile sarti atlatip `kur` kosarak her tahrifi akliyordu,
    ustelik zincirde KESINTI BILE BIRAKMADAN. Ayni sinifin ucuncu kiligi. Dogru capa
    `.hafizarc`: proje "kurulu" oldugunu ORADA beyan eder ve orasi zincir yukunun
    (politika:.hafizarc) parcasidir — silinmesi de kacamak degil, AYRI bir bulgudur.
    Artik UC dosyanin tutarliligi birlikte aranir: .hafizarc varsa _CIPA.json da
    _ZINCIR.jsonl de VAR ve DOLU olmalidir."""
    if not os.path.isfile(os.path.join(y.kok, RC_AD)):
        return                                  # henuz kurulmamis: ilk halka yazilacak
    if not os.path.isfile(y.cipa):
        oldur("_CIPA.json YOK ama proje KURULU (%s duruyor).\n"
              "  Cipa H1'in KANIT TABANIDIR; yoklugunda yazmak, o ana kadarki her\n"
              "  degisikligi olculemez kilar. Yazan komutlar DURUR.\n"
              "  Yol: dosyayi surum kontrolunden/yedekten geri al.\n"
              "  Gercekten kaybolduysa bu bir VERI KAYBIDIR; arac onu 'onarmaz'."
              % RC_AD)
    if os.path.isfile(y.zincir):
        with open(y.zincir, encoding="utf-8", errors="replace") as f:
            if not f.read().strip():
                oldur("_ZINCIR.jsonl BOS — genesis halkasi yok.\n"
                      "  Bos bir zincirin uzerine YAZMAK, o ana kadarki tahrifi mesru\n"
                      "  gosterir; bu yuzden yazan komutlar DURUR.\n"
                      "  Once olc: python hafiza.py kapi   (H0 bulgusunu oku)\n"
                      "  Sonra: zinciri yedekten geri al ya da elle incele.")
        return
    if True:
        oldur("_ZINCIR.jsonl YOK ama proje KURULU (_CIPA.json duruyor).\n"
              "  Silinmis bir zincirin uzerine yeni halka yazmak, o ana kadarki her\n"
              "  tahrifi MESRU gosterir; bu yuzden yazan komutlar DURUR.\n"
              "  Yol: dosyayi surum kontrolunden/yedekten geri al.\n"
              "  Denetim izi gercekten kaybolduysa bu bir VERI KAYBIDIR ve arac onu\n"
              "  'onarmaz'. Kaybi kabul edip yeniden baslamak SENIN kararindir; bunu\n"
              "  hafiza dosyasina ELINLE yazip yeni bir dizinde kurmak zorundasin.\n"
              "  (Bu mesaj bilerek bir 'kurtarma komutu' TARIF ETMEZ: tarif edilen her\n"
              "  kacamak, kapinin engellemek icin var oldugu seyi kolaylastirir.)")

def zincir_on_kontrol(y, rc=None):
    """BAGIMSIZ DENETIM: bozuk bir zincirde `derle` ONCE canliyi yaziyor, fragmani
    arsive tasiyor, SONRA zincir_halka icinde oluyordu — yarim is + muhursuz durum.
    Yazan her komut, ISE BASLAMADAN zincirin okunabilirligini dogrular."""
    yol_on_kontrol(y, dizinler=(y.h, y.gunluk, y.gunluk_ars, y.kararlar),
                   dosyalar=_korunacak_dosyalar(y, rc))
    if not os.path.isdir(y.h):
        oldur("HAFIZA DIZINI YOK: %s\n"
              "  Kurulum eksik ya da dizin silinmis. Once: python hafiza.py kur --kok=<dizin>\n"
              "  (Devralinmis projede: python hafiza.py devral --kok=<dizin>)" % y.h)
    zincir_butunlugu_sart(y)                    # B-1 + kardesi (silinmis zincir)
    if os.path.isfile(y.zincir):
        jsonl_yukle(y.zincir, ["halka"])        # bozuksa temiz hatayla DURUR

def _bos_ad(dizin, ad, *ayrica):
    """FABLE Y-7: fragman logu APPEND-ONLY olmali. Ayni-dakika + ayni-konu ikinci fragman,
    hem gunluk/'te hem ARSIVDE cakisabilir; ikisine de bakilir. '-2', '-3' eki verilir."""
    kok_ad, uzanti = os.path.splitext(ad)
    dizinler = [dizin] + [d for d in ayrica if d]
    aday, n = ad, 2
    while any(os.path.exists(os.path.join(d, aday)) for d in dizinler):
        aday = "%s-%d%s" % (kok_ad, n, uzanti)
        n += 1
        if n > 9999:
            oldur("fragman adi cakismasi cozulemedi: " + ad)
    return aday

def tamsayi(deger, ad, en_az=None):
    """CLI/defter kaynakli tamsayiyi ValueError traceback'i vermeden cozer."""
    try:
        n = int(str(deger).strip())
    except (TypeError, ValueError):
        oldur("%s bir TAM SAYI olmali (verilen: %r)" % (ad, deger))
    if en_az is not None and n < en_az:
        oldur("%s en az %d olmali (verilen: %d)" % (ad, en_az, n))
    return n

# ---------------------------------------------------------------- yollar

def _yol(kok, rel):
    """BAGIMSIZ DENETIM (yanlis-pozitif): .hafizarc dogrulamasi TERS BOLUYU kabul
    ediyordu (`..` kontrolu \\ ve / ikisini de bakiyor) ama yol kurulumu yalniz "/"
    ile boluyordu -> Windows tarzi "arsiv\\hafiza" dogrulamadan gecip sonra
    FileNotFoundError uretiyordu. Iki ayrac da burada normallestirilir."""
    parcalar = [x for x in rel.replace("\\", "/").split("/") if x not in ("", ".")]
    return os.path.join(kok, *parcalar) if parcalar else kok

class Y:
    def __init__(self, kok, rc):
        self.kok = kok
        self.canli = _yol(kok, rc["canli"])
        self.kural = _yol(kok, rc["kural_evi_dosya"])
        self.h = _yol(kok, rc.get("hafiza_dizini", "arsiv/hafiza"))
        self.gunluk = os.path.join(kok, "gunluk")
        self.gunluk_ars = os.path.join(self.h, "gunluk")
        self.kararlar = os.path.join(kok, "kararlar")
        self.plan = os.path.join(kok, "SAKLAMA_PLANI.md")
        self.konular = os.path.join(kok, "KONULAR.md")
        self.snap = os.path.join(self.h, "_KAYNAK.md")
        self.cipa = os.path.join(self.h, "_CIPA.json")
        self.zincir = os.path.join(self.h, "_ZINCIR.jsonl")
        self.tasinma = os.path.join(self.h, "_TASINMA.jsonl")
        self.duzelt = os.path.join(self.h, "_DUZELTMELER.json")
        self.yeni = os.path.join(self.h, "_YENI_SATIRLAR.txt")
        self.kova = os.path.join(self.h, "_KOVA.json")
        self.korunan = os.path.join(self.h, "_KORUNAN.json")

def arsiv_dosyalari(kok, y, rc):
    """H1 birlesimine giren TUM arsiv dosyalari: v2'nin kendi HAFIZA_*.md'leri
    + devralinan eski arsivler (ek_arsiv_dosyalari)."""
    out = [os.path.join(y.h, f) for f in sorted(os.listdir(y.h))
           if re.match(r"^HAFIZA_.*\.md$", f)] if os.path.isdir(y.h) else []
    for rel in rc.get("ek_arsiv_dosyalari", []):
        p = os.path.join(kok, *rel.split("/"))
        if os.path.isfile(p) and p not in out:
            out.append(p)
    return out


DEFTERLER = ["_CIPA.json", "_TASINMA.jsonl", "_DUZELTMELER.json",
             "_YENI_SATIRLAR.txt", "_KOVA.json", "_KORUNAN.json"]

# FABLE Y-5: politika dosyalari hicbir butunluk kapisinin kapsaminda DEGILDI.
# `.hafizarc`'i gevsetmek (kural_isaretleri=[] , tavan_kb=99999) butun kapilari
# susturuyordu ve zincir bunu gormuyordu. Artik zincir yukune giriyorlar.
POLITIKA_DOSYALARI = [RC_AD, "KONULAR.md", "SAKLAMA_PLANI.md"]

# ---------------------------------------------------------------- zincir

def zincir_halka(y, tur, gerekce, ek=None):
    """Defterlerin o anki durumunu halka olarak zincire ekler."""
    onceki = "GENESIS"
    if os.path.isfile(y.zincir):
        # Y-3: bozuk son halka burada ham traceback veriyordu; artik temiz hata.
        kayitlar = jsonl_yukle(y.zincir, ["halka"])
        if kayitlar:
            onceki = kayitlar[-1]["halka"]
    yuk = {}
    for d in DEFTERLER:
        p = os.path.join(y.h, d)
        yuk[d] = sha_dosya(p) if os.path.isfile(p) else "-"
    yuk["_KAYNAK.md"] = sha_dosya(y.snap) if os.path.isfile(y.snap) else "-"
    for pd in POLITIKA_DOSYALARI:
        pp = os.path.join(y.kok, pd)
        yuk["politika:" + pd] = sha_dosya(pp) if os.path.isfile(pp) else "-"
    kayit = {"t": _dt.datetime.now().isoformat(timespec="seconds"),
             "tur": tur, "gerekce": gerekce, "yuk": yuk, "onceki": onceki}
    if ek:
        kayit["ek"] = ek
    # Fable Bulgu 2: gerekce/tur/zaman/ek HASH'E GIRMIYORDU -> denetim izi izsiz tahrif
    # edilebiliyordu. Artik halka, kaydin TAMAMINI (halka alani haric) kapsar.
    kayit["halka"] = sha(onceki + json.dumps({k: v for k, v in kayit.items() if k != "halka"},
                                             sort_keys=True, ensure_ascii=False))
    with open(y.zincir, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")
    return kayit["halka"]

def zincir_dogrula(y):
    hata = []
    if not os.path.isfile(y.zincir):
        return ["_ZINCIR.jsonl YOK — defterler cipasiz"]
    sat = [s for s in oku(y.zincir).split("\n") if s.strip()]
    # ===== FABLE 3. TUR · B-1 [YUKSEK] =====================================
    # Zincirin SILINMESI yakalaniyordu, 0 BAYTA INMESI yakalanmiyordu:
    # bos dosyada dongu hic donmuyor, `son` None kaliyor ve defter-SHA
    # karsilastirmasi TUMDEN atlaniyordu -> beyansiz defter tahrifi "saglam"
    # sayiliyor, ardindan `muhur` onu KALICI olarak akliyordu. Yani
    # "denetim izi izsiz tahrif edilemez" vaadi tek bir truncate ile cokuyordu.
    # Mesru bir projede bos zincir IMKANSIZDIR: `kur`/`devral` daima genesis
    # halkasini yazar. Dolayisiyla bos zincir = kismi yazma / cokme / kasit.
    if not sat:
        return ["_ZINCIR.jsonl BOS — genesis halkasi yok (kismi yazma ya da tahrif "
                "suphesi). Defter-SHA dogrulamasi YAPILAMIYOR; bu hal 'saglam' "
                "SAYILMAZ. Yedekten geri al ya da zinciri elle incele."]
    # Ilk halka gercekten genesis mi? Bastan N halka kesilirse (onceki bagi
    # 'GENESIS' olmayan bir halkayla baslarsa) bunu ayrica soyle.
    try:
        _ilk = json.loads(sat[0])
        if isinstance(_ilk, dict) and _ilk.get("onceki") != "GENESIS":
            hata.append("zincir GENESIS ile BASLAMIYOR (ilk halkanin onceki='%s') — "
                        "zincirin BASI kesilmis olabilir" % str(_ilk.get("onceki"))[:24])
    except ValueError:
        pass                      # bozuk JSON asagidaki dongude zaten raporlanir
    onceki = "GENESIS"
    son = None
    _onceki_t = None                          # B-11: halka zamanlarinin monotonlugu
    for i, s in enumerate(sat, 1):
        # Y-3: burada oldur() KULLANILMAZ — bu bir KAPI olcumudur, bulgu dondurur.
        try:
            k = json.loads(s)
        except Exception:
            hata.append("zincir halka %d bozuk JSON" % i)
            return hata
        if not isinstance(k, dict):
            hata.append("zincir halka %d bir nesne degil (%s) — defter tahrif edilmis"
                        % (i, type(k).__name__))
            return hata
        bek = sha(onceki + json.dumps({kk: vv for kk, vv in k.items() if kk != "halka"},
                                      sort_keys=True, ensure_ascii=False))
        if "halka" not in k:
            hata.append("zincir halka %d ALANSIZ ('halka' yok) — kayit tahrif edilmis" % i)
        elif k.get("halka") != bek:
            hata.append("zincir halka %d KIRIK (yeniden yazim suphesi)" % i)
        if k.get("onceki") != onceki:
            hata.append("zincir halka %d onceki-baglantisi KIRIK" % i)
        # FABLE 3. TUR · B-11: halkanin `t` alani hash'e giriyor (2. tur duzeltmesi)
        # ama MESRUIYETI hic olculmuyordu: son halkanin t'sini gelecege alip hash'i
        # yeniden hesaplamak H0'dan gecerdi. Zaman, denetim izinin bir parcasidir:
        # gelecege gidemez ve GERIYE akamaz.
        _t = k.get("t")
        if isinstance(_t, str) and _t:
            try:
                _td = _dt.datetime.fromisoformat(_t.replace("Z", "+00:00"))
            except ValueError:
                hata.append("zincir halka %d zaman damgasi cozulemedi ('%s')" % (i, _t[:24]))
            else:
                # IC DENETIM (O-1): saat dilimli (aware) bir `t`, naive now() ile
                # karsilastirilinca TypeError atiyor ve KAPI HIC HUKUM VEREMIYORDU.
                # Zincir anahtarsiz oldugu icin yazma erisimi olan biri tek halkaya
                # '+03:00' koyup kapiyi tumden felce ugratabilirdi. Yerel saate cevir.
                if _td.tzinfo is not None:
                    _td = _td.astimezone().replace(tzinfo=None)
                # 2 GUNLUK pay: saat dilimi yayilimi UTC-12..UTC+14 = 26 SAAT,
                # yani 1 gun YETMEZ (paylasilan bir depoda yanlis-pozitif uretirdi).
                if _td > _dt.datetime.now() + _dt.timedelta(days=2):
                    hata.append("zincir halka %d zaman damgasi GELECEKTE (%s) — "
                                "halka tahrif edilmis ya da saat bozuk" % (i, _t[:19]))
                if _onceki_t is not None and _td < _onceki_t - _dt.timedelta(days=2):
                    hata.append("zincir halka %d zaman damgasi GERIYE akiyor (%s < %s) — "
                                "halka yeniden yazilmis olabilir"
                                % (i, _t[:19], _onceki_t.isoformat(timespec="seconds")[:19]))
                _onceki_t = _td
        # 'halka' yoksa hasari TEK halkaya hapset: dogru degeri kullan, sonrakiler
        # kendi baslarina olculsun (yoksa tek eksik alan butun zinciri sahte-kirmizi yapar).
        onceki = k.get("halka") or bek
        son = k
    if son:
        yukum = son.get("yuk")
        if not isinstance(yukum, dict):
            hata.append("zincir son halkada 'yuk' yok/bozuk — defter SHA'lari olculemiyor")
            yukum = {}
        _son_t = None
        _st = son.get("t")
        if isinstance(_st, str) and _st:
            try:
                _son_t = _dt.datetime.fromisoformat(_st.replace("Z", "+00:00"))
                if _son_t.tzinfo is not None:
                    _son_t = _son_t.astimezone().replace(tzinfo=None)
            except ValueError:
                _son_t = None
        _gec = []
        for d, h in yukum.items():
            p = (os.path.join(y.kok, d.split(":", 1)[1]) if d.startswith("politika:")
                 else os.path.join(y.h, d))
            simdi = sha_dosya(p) if os.path.isfile(p) else "-"
            if simdi != h:
                hata.append("defter MUHURSUZ degismis: %s (muhurle: hafiza.py muhur \"gerekce\")" % d)
            elif _son_t is not None and os.path.isfile(p):
                # IC DENETIM (O-2): zincir ANAHTARSIZDIR — yazma erisimi olan biri
                # `yuk`u guncelleyip `halka`yi YENIDEN HESAPLAYABILIR ve hash denetimi
                # bunu goremez (mimari sinir; belgede yaziyor). Ama KULLANILMAYAN bir
                # kanit vardi: dosyanin mtime'i son halkanin t'sinden SONRAYSA, o dosya
                # muhurlendikten SONRA degismis ve halka geriye donuk yeniden yazilmis
                # demektir. Bu, yeniden-hesaplamayi TEK BASINA kanitlamaz ama en yaygin
                # kiligini gorunur kilar. Tolerans 2 gun (saat dilimi/kayma).
                try:
                    _mt = _dt.datetime.fromtimestamp(os.path.getmtime(p))
                except OSError:
                    continue
                if _mt > _son_t + _dt.timedelta(days=2):
                    _gec.append((d, _mt))
        if _gec:
            # KANIT GUCUNE GORE AYIR — yoksa KLON/ZIP yanlis-pozitifi uretir:
            # `git clone` ya da zip acmak TUM mtime'lari "simdi"ye ceker; halka t'si
            # eski kalir ve butun defterler sahte-kirmizi yanardi. Bu, Fable 1. turda
            # H14'te bulunan sinifin ta kendisi — ayni tuzaga ikinci kez dusmuyoruz.
            # git VARSA: dosya gercekten KIRLI mi diye sor (gercek delil).
            # git YOKSA: mtime tek basina kirmizi yakmak icin YETMEZ -> OLCEMIYORUM.
            # IC DENETIM (B-5): ilk halim git "KIRLI" diyorsa FAIL veriyordu. Ama
            # defterler `derle` sonrasi commit edilmedigi icin ZATEN daima kirlidir;
            # yani teyit HICBIR kanit gucu tasimiyordu ve dedektor saf
            # "mtime > halka_t" haline dusuyordu. Olculdu: dosyayi BIREBIR AYNI
            # baytlarla yeniden kaydetmek (editor, senkron, cp) kapiyi kirmiziya
            # cekiyordu — asilsiz tahrif suclamasi. mtime TEK BASINA hicbir zaman
            # hukum degildir; her zaman ISARET (OLCEMIYORUM) olarak raporlanir.
            hata.append("~%d defterin mtime'i son halkadan YENI ama SHA'si tutuyor "
                        "(%s). Bu, halkanin geriye donuk yeniden hesaplandigina ISARET "
                        "OLABILIR; ama dosyayi ayni icerikle yeniden kaydetmek, klon, "
                        "zip ya da senkron da mtime tazeler. TEK BASINA HUKUM DEGILDIR. "
                        "Suphe duyuyorsan surum kontrolune bak; bilincliyse: "
                        "hafiza.py muhur \"...\""
                        % (len(_gec), ", ".join(d for d, _ in _gec[:3])))
    return hata

# ---------------------------------------------------------------- blok/fragman

# SATIR BASINA CIPALI. Bagimsiz denetimin ucuncu turunun dersi: ayni dosyada IKI FARKLI
# "blok satiri" tanimi vardi (biri satirin herhangi bir yerinde arar, digeri satir basina
# bakar) ve bu ayrisma tam da 1. turdaki sessiz-gizleme kusurunu uretiyordu. Bu duzende
# gercek blok isareti HER ZAMAN satir basindadir (`derle` ve `bloklastir` boyle yazar);
# satir ortasindaki ya da girintili bir isaret bir ORNEKTIR, blok degildir. Tek tanim,
# tek davranis: kod citi girintisi gibi kirilgan sezgilere gerek kalmaz.
BLOK_BAS = re.compile(r"^<!--\s*blok\s+(.*?)-->")
BLOK_SON = re.compile(r"^<!--\s*/blok\s*-->")

def oznitelik_coz(s):
    d = {}
    for m in re.finditer(r'(\w+)=("([^"]*)"|(\S+))', s):
        d[m.group(1)] = m.group(3) if m.group(3) is not None else m.group(4)
    return d

KOD_CITI = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
KOD_ICI = re.compile(r"`[^`\n]*`")

def _cit(s):
    """Bir satir KOD CITI mi? (kar, uzunluk, bilgi_metni) ya da None.

    BAGIMSIZ DENETIM 2. TUR:
      - Girinti siniri 3'ten 8'e cikarildi: CommonMark'ta LISTE ICINDEKI cit girintilidir
        ve eski sinir onu gormuyordu -> belge ornegi GERCEK blok sanilip `derle`
        gercek icerigi ornegin ICINE yaziyordu. Fazladan gizlemek zararsizdir cunku
        gizlenen her gercek blok satiri `gizli_blok_satirlari` ile RAPORLANIR.
      - Ayni isaret satirin devaminda TEKRAR geciyorsa (```kod```) bu bir cit degil,
        SATIR ICI koddur; eskiden cit sayilip "KAPANMAMIS KOD CITI" yanlis-pozitifi
        uretiyordu."""
    m = KOD_CITI.match(s)
    if not m or len(m.group(1)) > 8:
        return None
    kar, uz, kuyruk = m.group(2)[0], len(m.group(2)), m.group(3)
    if kar * 3 in kuyruk:                 # ```kod``` — satir ici kod
        return None
    return kar, uz, kuyruk

def kod_disi(L):
    """Markdown KOD bolgelerini bosaltilmis satir listesi dondurur (satir sayisi korunur).

    FABLE Y-8: `<!-- blok konu="x" -->` gibi ORNEK satirlar gercek blok saniliyordu;
    bu duzenin kendi belgeleri bu sozdizimini gosterdigi icin meta-projede yanlis-pozitif.

    BAGIMSIZ DENETIM (2. tur) — ilk uygulamam KIRILGANDI: cit sayisini tek/cift
    saymak yetmiyordu. CommonMark kurallari uygulanir:
      - acilis citi <=3 bosluk girintili olabilir; ~~~ ve ``` AYRI cit turleridir,
      - kapanis citi AYNI karakterden ve EN AZ acilis kadar uzun olmali, bilgi metni almaz,
      - acilis citinden UZUN olmayan ic citler kod icinde kalir (ic ice ornekler).
    Yine de sozdizimi tam degildir; bu yuzden GIZLENEN blok satirlari ayrica sayilir
    (`gizli_blok_satirlari`) ve H10 bunu RAPORLAR — sessiz gizleme MUMKUN DEGIL."""
    out, acik = [], None       # acik = (karakter, uzunluk)
    for s in L:
        m = _cit(s)
        if m:
            kar, uz, kuyruk = m
            if acik is None:
                acik = (kar, uz)
                out.append(""); continue
            if kar == acik[0] and uz >= acik[1] and not kuyruk.strip():
                acik = None
                out.append(""); continue
            # acik bir citin icindeki farkli/kisa cit: kod icerigidir
            out.append(""); continue
        out.append("" if acik is not None else KOD_ICI.sub("", s))
    return out

def gizli_blok_satirlari(L):
    """Kod bolgesi yuzunden OLCUM DISI kalan gercek blok-sozdizimi satirlari.

    Kritik: 'cit sayisi cift, demek ki guvendeyiz' YANLISTI (denetimde olculdu:
    iki ayri fragmandaki birer cit, aralarindaki GERCEK blogu gizliyordu ve
    kapi sessiz kaliyordu). Dogru olcum sayma degil, KARSILASTIRMADIR:
    ham metinde blok isareti olup kod-disi metinde OLMAYAN her satir gizlenmistir."""
    Lk = kod_disi(L)
    gizli = []
    for i, s in enumerate(L, 1):
        ham = bool(BLOK_BAS.search(s) or BLOK_SON.search(s))
        gor = bool(BLOK_BAS.search(Lk[i - 1]) or BLOK_SON.search(Lk[i - 1]))
        if ham and not gor:
            gizli.append((i, s.strip()[:80]))
    return gizli

GIRINTILI_ISARET = re.compile(r"^[\s\ufeff\u200b\u00a0]+<!--\s*/?\s*blok\b")

def girintili_isaretler(L):
    """Sutun 0'da OLMAYAN blok-benzeri isaretler.

    BAGIMSIZ DENETIM 4. TUR (YUKSEK): sozdizimini sutun 0'a cipalamak iki tanim
    sorununu cozdu ama YENI bir sessizlik acti — DEVRALINAN, elle bakilmis bir
    hafizada isaretler girintiliyse hicbir yerde blok sayilmiyor, `derle` mevcut
    blogu bulamiyor ve IKINCI blok doguyordu; kapi yesildi. Gizleme olcumu
    "ham != kod_disi" karsilastirmasina dayandigi icin bunu goremiyordu.
    Bu yuzden AYRI bir olcum: girintili isaret VARSA soylenir."""
    return [(i, s.rstrip()[:80]) for i, s in enumerate(L, 1) if GIRINTILI_ISARET.match(s)]

def gizli_konu_cakismasi(L):
    """Gizlenen bloklardan HANGILERI gorunur bir blokla AYNI konuyu tasiyor?

    Ayrim onemli: kod citi icindeki bir ornek zararsizdir (belge). TEHLIKELI olan,
    gizlenen blogun konusunun CANLIDA da bulunmasidir — o zaman H10'un olctugu
    "bir konu icin tek blok" kurali sessizce delinmis olur. Ilk tur bulgusu buydu."""
    Lk = kod_disi(L)
    gorunen = set()
    for s in Lk:
        m = BLOK_BAS.search(s)
        if m:
            gorunen.add(oznitelik_coz(m.group(1)).get("konu"))
    cakisan = []
    for i, s in enumerate(L, 1):
        m = BLOK_BAS.search(s)
        if m and not BLOK_BAS.search(Lk[i - 1]):
            k = oznitelik_coz(m.group(1)).get("konu")
            if k in gorunen:
                cakisan.append((i, k))
    return cakisan

def kod_citi_dengesiz(L):
    """Kapanmamis acilis citi kaldi mi? (kod_disi ile AYNI kurallari kullanir)"""
    acik = None
    for s in L:
        m = _cit(s)
        if m:
            kar, uz, kuyruk = m
            if acik is None:
                acik = (kar, uz)
            elif kar == acik[0] and uz >= acik[1] and not kuyruk.strip():
                acik = None
    return acik is not None

def canli_bloklar(y):
    """[(bas_satir_no, son_satir_no, oznitelikler)] — 1 tabanli, kapsayici."""
    L = kod_disi(satirlar(y.canli))
    out, acik = [], None
    for i, s in enumerate(L, 1):
        m = BLOK_BAS.search(s)
        if m:
            acik = (i, oznitelik_coz(m.group(1)))
            continue
        if BLOK_SON.search(s) and acik:
            out.append((acik[0], i, acik[1]))
            acik = None
    return out

FM = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)

def fragman_coz(p):
    t = oku(p)
    m = FM.match(t)
    if not m:
        return None, t
    meta = {}
    for line in m.group(1).split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)

# ---------------------------------------------------------------- ADR

ADR_AD = re.compile(r"^(\d{4})-[a-z0-9-]+\.md$")

def adr_listesi(y):
    out = []
    if not os.path.isdir(y.kararlar):
        return out
    for f in sorted(os.listdir(y.kararlar)):
        m = ADR_AD.match(f)
        if not m:
            continue
        meta, govde = fragman_coz(os.path.join(y.kararlar, f))
        out.append({"no": int(m.group(1)), "dosya": f, "meta": meta or {}, "govde": govde})
    return out

# ---------------------------------------------------------------- sablonlar

SAB_CANLI = """# {ad} — CANLI HAFIZA
> Bu dosya bir SNAPSHOT'tır: gunluk/ fragmanlarından ve kararlar/ dosyalarından TÜRETİLİR.
> Her oturum başında OKU. Kaynak değil, özet olduğu için buraya YENİ BİLGİ yazılmaz —
> önce `hafiza.py not`, sonra `hafiza.py derle`.
> Son guncelleme: {t} · Tavan: {tavan} KB

## DEVRALAN MODELE İLK TALİMAT
<!-- blok konu="acilis-protokolu" guncel="{t}" kaynak="-" -->
1. Bu dosyayı baştan sona oku. Sohbet geçmişini hafıza sayma.
2. `hafiza.py kapi` koş. YEŞİL görmeden işe BAŞLAMA.
3. `git status` temiz mi bak.
4. SONRAKİ ADIM'daki ilk işten devam et.
5. Kod/içerik yazmadan ÖNCE tasarımı işaretlenebilir şıklarla sun; kapsamı onaylat.
6. Her büyük adım sonunda `hafiza.py not` ile fragman yaz (checkpoint).
7. Oturum kapanırken: `hafiza.py derle` → `hafiza.py kapi` → devir notu.
<!-- /blok -->

## GÜNCEL DURUM
<!-- blok konu="genel-durum" guncel="{t}" kaynak="-" -->
- (boş — ilk fragmanı yaz: hafiza.py not --konu genel-durum --tur durum)
<!-- /blok -->

## SONRAKİ ADIM
<!-- blok konu="sonraki-adim" guncel="{t}" kaynak="-" -->
- (boş)
<!-- /blok -->

## AÇIK KARARLAR / BLOKERLER
<!-- blok konu="acik-kararlar" guncel="{t}" kaynak="-" -->
- (boş)
<!-- /blok -->

## SABİT ÇERÇEVE (nadiren değişir)
> Kalıcı kuralların EVİ burasıdır. Bir kural başka bölümde yaşarsa rotasyona girer ve
> bir sonraki temizlikte görünmez olur (H7 bunu yakalar).

## KIRMIZI ÇİZGİLER / AÇIK KAPILAR
> Asla ihlal edilmeyecekler + bilinçli olarak açık bırakılanlar.

## KARAR GÜNLÜĞÜ (en yeni en üstte)
> Burada yalnızca ÖZET + karar dosyasına LİNK durur. Gerekçe kararlar/ içinde yaşar.

## ARŞİV DİZİNİ
"""

SAB_PLAN = """# SAKLAMA PLANI (retention schedule)
> Emeklilik kararı BOYUTA göre değil DEĞERE göre verilir; ve ANINDA değil ÖNCEDEN.
> Arşivcilerin kuralı: karar belge belge değil, SERİ düzeyinde ve peşinen verilir.
> Az sayıda geniş kova tut ("big bucket") — 50 ince seri yönetilemez.

| Seri | Tetikleyici | Saklama | Tasfiye eylemi |
|---|---|---|---|
| KIRMIZI ÇİZGİ / kalıcı kural | — | süresiz | ASLA emekli olmaz (H7 korur) |
| KARAR (ADR) | yerine geçildiğinde | süresiz | `kararlar/` içinde KALIR; yalnız `durum` alanı güncellenir |
| GÜNCEL DURUM | her derleme | 1 sürüm | üzerine yazılır; önceki hâli karar günlüğüne özetlenir |
| TUR BELGESİ (gorev/test/kanit/bulgu) | tur kapanınca | süresiz | `arsiv/<tur>/` altına TAŞINIR (silinmez) |
| OTURUM FRAGMANI | derlendiğinde | süresiz | `arsiv/hafiza/gunluk/` altına TAŞINIR |
| CANLI HAFIZA BLOĞU | aynı konuda yeni blok gelince | süresiz | `hafiza.py emekli` ile arşive TAŞINIR (byte-birebir) |
| GEÇİCİ / SCRATCH | iş bitince | 0 | SİLİNEBİLİR — tek istisna budur ve adı açıkça geçici olmalıdır |

## Kural
Bu tabloda KARŞILIĞI OLMAYAN bir dosya türü üretilirse, önce bu tabloya satır eklenir.
"Plansız seri" H13 kapısını kırar.
"""

SAB_KONULAR = """# KONULAR (anahtar sözlüğü)
> Canlı hafızadaki her blok bir `konu` taşır. Kural: BİR KONU İÇİN CANLIDA EN FAZLA BİR BLOK.
> Aynı konuda ikinci blok gelirse eskisi emekli edilir (Kafka log-compaction mantığı:
> "her anahtar için son değeri tut"). Böylece "eski ama tek" bilgi kaybolmaz,
> "yeni ama tekrarlanmış" bilgi birikmez.
> Konu EKLEMEK serbest; SİLMEK yasak (silinen konu adı geri kullanılamaz).

| konu | ne anlatır |
|---|---|
| acilis-protokolu | oturum başlangıç adımları |
| genel-durum | projenin bugünkü hâli |
| sonraki-adim | sıradaki iş |
| acik-kararlar | bekleyen kararlar / blokerler |
"""

SAB_ADR = """---
no: {no:04d}
baslik: {baslik}
durum: onerildi
tarih: {t}
konu: {konu}
yerini-aldigi: {yerini}
yerine-gecen: -
---

# {no:04d} — {baslik}

## Bağlam
(Hangi problem? Hangi kısıt? Neden şimdi?)

## Karar
(Etken cümle, birinci çoğul: "... yapacağız.")

## Değerlendirilen alternatifler
| Seçenek | Artı | Eksi | Neden seçilmedi |
|---|---|---|---|

## Bedeller (consequences)
(Bu kararın bize NEYE mal olduğu — olumlu ve olumsuz. Boş bırakma; bedelsiz karar yoktur.)

## Doğrulama
(Bu kararın TUTTUĞU nasıl ölçülür? Hangi test/komut/gözlem? Ölçülemezse bunu yaz.)
"""

SAB_RC = """{{
  "surum": "{s}",
  "ad": "{ad}",
  "canli": "PROJE_HAFIZA.md",
  "kural_evi_dosya": "CLAUDE.md",
  "tavan_kb": 60,
  "bayatlik_gun": 30,
  "zorunlu_bolumler": ["## GUNCEL DURUM", "## SONRAKI ADIM", "## ACIK KARARLAR",
                       "## SABIT CERCEVE", "## KIRMIZI CIZGILER", "## KARAR GUNLUGU",
                       "## ARSIV DIZINI"],
  "kural_evi_bolumleri": ["## SABIT CERCEVE", "## KIRMIZI CIZGILER"],
  "kural_isaretleri": ["PAZARLIKSIZ", "MUTLAK KURAL", "KIRMIZI CIZGI", "ASLA"],
  "arsiv_turleri": ["gorev", "test", "kanit", "bulgu", "tasarim", "taslak"],
  "kanonik_artefakt": ""
}}
"""

# ---------------------------------------------------------------- kur

def cmd_kur(a):
    kok = os.path.abspath(a.kok or os.getcwd())
    if not os.path.isdir(kok):
        oldur("kok yok: " + kok)
    # Fable Bulgu 5: belge "mevcut sistemde kur KOSMA" diyordu ama arac kendini korumuyordu.
    # Artik v1 izleri kod seviyesinde taranir ve `kur` DURUR.
    izler = []
    eski_h = os.path.join(kok, "arsiv", "hafiza")
    if os.path.isdir(eski_h):
        izler = [f for f in os.listdir(eski_h)
                 if re.match(r"^_KAYNAK.*\.md$|^_ZINCIR\.jsonl$|^HAFIZA_.*\.md$|^_KOVA\.json$", f)]
    if izler and not os.path.isfile(os.path.join(kok, RC_AD)):
        oldur("Bu projede ZATEN bir hafiza sistemi var (%s: %s).\n"
              "  `kur` onu BOZAR (zincire yabanci halka ekler, ikinci cipa dogurur).\n"
              "  Dogru komut: python hafiza.py devral --kok=\"%s\""
              % (os.path.relpath(eski_h, kok).replace("\\", "/"), ", ".join(sorted(izler)[:4]), kok))
    ad = a.ad or os.path.basename(kok.rstrip(os.sep)) or "PROJE"
    rc_p = os.path.join(kok, RC_AD)
    yeni_kurulum = not os.path.isfile(rc_p)
    if yeni_kurulum:
        yaz(rc_p, SAB_RC.format(s=SURUM, ad=ad))
    rc = rc_oku(kok)
    y = Y(kok, rc)
    # `kur` da yol tiplerini dogrular: dizin yerinde dosya/kirik link varsa os.makedirs
    # ham FileExistsError veriyordu (bagimsiz denetim).
    yol_on_kontrol(y, dizinler=(y.h, y.gunluk, y.gunluk_ars, y.kararlar),
                   dosyalar=_korunacak_dosyalar(y, rc))
    # A-1 (PAKETLEME SONRASI IC DENETIM, v2.4.1): `kur` ve `devral` tek-yazar
    # kilidini HIC almiyordu. B-5'te kilidin SAHIPLIGINI derinlestirirken
    # KAPSAMINI denetlemedim — kendi yazdigim "yuzey sarma" hatasi. `kur`
    # idempotent tazelemede canliya/deftere yazar ve zincire halka atar; baska
    # bir oturum ayni anda `derle` kosuyorsa kayip guncelleme sinifi geri gelir.
    kilit_al(y)
    # `kur` idempotent TAZELEME de yapar ve sonunda zincire halka yazar; silinmis/bos
    # zincirde bu, aklama yoluna donusurdu. Ayni sart burada da gecerli — AMA yalniz
    # TAZELEMEDE: ilk kurulumda .hafizarc bu satirdan hemen ONCE yazildigi icin sart
    # "kurulu ama cipasiz" sanip ILK KURULUMU bloklardi (kendi olctugumuz regresyon).
    if not yeni_kurulum:
        zincir_butunlugu_sart(y)

    for d in [y.h, y.gunluk, y.gunluk_ars, y.kararlar]:
        os.makedirs(d, exist_ok=True)
    for t in rc["arsiv_turleri"]:
        os.makedirs(os.path.join(kok, "arsiv", t), exist_ok=True)

    if not os.path.isfile(y.canli):
        yaz(y.canli, SAB_CANLI.format(ad=ad, t=bugun(), tavan=rc["tavan_kb"]))
    if not os.path.isfile(y.plan):
        yaz(y.plan, SAB_PLAN)
    if not os.path.isfile(y.konular):
        yaz(y.konular, SAB_KONULAR)
    if not os.path.isfile(y.kural):
        yaz(y.kural, "# %s — KALICI PROTOKOL\n"
                     "> Bu dosya her oturumda yüklenir.\n"
                     "> BUDAMA TESTİ: bir satırı silmek modelin hata yapmasına yol açmıyorsa, KES.\n" % ad)

    # cipa: canli dosyanin O ANKI hali kanit tabanidir
    if not os.path.isfile(y.snap):
        shutil.copyfile(y.canli, y.snap)
    if not os.path.isfile(y.cipa):
        yaz(y.cipa, json.dumps({"dosya": "_KAYNAK.md", "sha": sha_dosya(y.snap),
                                "tarih": bugun(), "surum": SURUM},
                               ensure_ascii=False, indent=2) + "\n")
    # kova: snapshot satirlarinin nerede yasayacagi
    if not os.path.isfile(y.kova):
        L = satirlar(y.snap)
        kv = {"satirlar": {str(i + 1): "CANLI" for i, s in enumerate(L) if anlamli(s)}}
        yaz(y.kova, json.dumps(kv, ensure_ascii=False, indent=1) + "\n")
    for p, ilk in [(y.duzelt, '{\n  "duzeltmeler": []\n}\n'),
                   (y.yeni, ";; Beyan edilen YENI satirlar (yorum oneki ';;')\n"),
                   (y.tasinma, ""), (y.korunan, '{\n  "bloklar": []\n}\n')]:
        if not os.path.isfile(p):
            yaz(p, ilk)
    if not os.path.isfile(os.path.join(y.h, "HAFIZA_01.md")):
        _ars = ["# ARŞİV 01 — emekli edilmiş hafıza satırları",
                "> Buraya YALNIZ `hafiza.py emekli` ve `hafiza.py derle` yazar. Elle düzenleme YASAK."]
        yaz(os.path.join(y.h, "HAFIZA_01.md"), "\n".join(_ars) + "\n")
        _beyan_yeni_satirlar(y, _ars, "kurulum: arsiv iskeleti (arac uretti)")

    # arsiv dizini bolumunu tazele
    _arsiv_dizini_tazele(y)

    if not os.path.isfile(y.zincir):
        zincir_halka(y, "GENESIS", "kurulum")
    else:
        zincir_halka(y, "KURULUM", "hafiza.py kur (idempotent tazeleme)")

    print("KURULDU: " + kok)
    print("  canli hafiza  : " + rc["canli"])
    print("  cipa SHA      : " + sha_dosya(y.snap)[:16] + "...")
    print("\nSonraki: python %s kapi --kok=\"%s\"" % (os.path.basename(__file__), kok))

def _arsiv_dizini_tazele(y):
    if not os.path.isfile(y.canli):
        return
    dosyalar = sorted(f for f in os.listdir(y.h) if re.match(r"^HAFIZA_.*\.md$", f))
    L = satirlar(y.canli)
    try:
        i = next(i for i, s in enumerate(L) if s.startswith("#") and bas_eslesir(s, "ARSIV DIZINI"))
    except StopIteration:
        return
    j = i + 1
    while j < len(L) and not L[j].startswith("## "):
        j += 1
    hd = os.path.relpath(y.h, os.path.dirname(y.canli)).replace("\\", "/")
    yeni = [V2BAS, "> Bu alt blok `hafiza.py derle` tarafından üretilir; elle düzenleme H6'yı kırar."]
    for f in dosyalar:
        p = os.path.join(y.h, f)
        yeni.append("- `%s/%s` — %d satır, %d B" %
                    (hd, f, len(anlamli_satirlar(p)), os.path.getsize(p)))
    yeni.append(V2SON)
    # YIKICI DEGIL: yalniz KENDI alt blogumuzu yonetiriz. Devralinan bir projede
    # kullanicinin kendi dizin satirlari (v1 arsivini anlatan) OLDUGU GIBI KALIR.
    try:
        b = next(k for k in range(i, j) if L[k].strip() == V2BAS)
        e = next(k for k in range(b, j) if L[k].strip() == V2SON)
        L = L[:b] + yeni + L[e + 1:]
    except StopIteration:
        L = L[:j] + [""] + yeni + [""] + L[j:]
    yaz(y.canli, "\n".join(L))

def bas_anahtar(s):
    """Baslik ESLESME anahtari: emoji/noktalama/bosluk atilir, Turkce ASCII'ye duser.
    '## 📚 ARŞİV DİZİNİ' ve '## ARSIV DIZINI' AYNI anahtari verir.
    (Bu duzeltme, ilerlemis bir projede susluu basligin SESSIZCE bulunamamasi
     kusurundan sonra eklendi — sessiz bulunamama, kirmizi yanmaktan tehlikelidir.)"""
    return re.sub(r"[^A-Z0-9]", "", basliksal(s))

def bas_eslesir(satir, hedef):
    a, b = bas_anahtar(satir), bas_anahtar(hedef)
    return bool(b) and b in a

DOSYA_UZANTILARI = {
    "md", "txt", "rst", "json", "jsonl", "yml", "yaml", "toml", "ini", "cfg", "csv", "tsv",
    "py", "mjs", "js", "ts", "tsx", "jsx", "sh", "ps1", "bat", "sql", "ipynb",
    "html", "htm", "css", "xml", "svg", "gradle", "properties", "kt", "java", "c", "h",
    "pdf", "docx", "xlsx", "pptx", "doc", "xls", "ppt", "png", "jpg", "jpeg", "webp", "gif",
    "zip", "apk", "aab", "jks", "keystore", "p12", "pem", "skill", "plugin", "log", "bundle",
    "properties", "gitignore", "env", "lock", "jsonl", "mermaid", "epub", "psd", "ai", "sketch",
    "odt", "ods", "rtf", "tex", "bib", "vue", "svelte", "rb", "go", "rs", "php", "cs", "swift",
}

V2BAS = "<!-- v2-arsiv-dizini -->"
V2SON = "<!-- /v2-arsiv-dizini -->"


# SONLU Turkce cekim eki kumesi (basliksal() ile ASCII buyuk harfe indirgenmis hali).
# BAGIMSIZ DENETIM 7. TUR: once "buyuk harfse serbest" dedim (Turkcenin dogal yazimini
# KACIRDI), sonra "isaret >=6 harfse serbest" dedim (kisa isaretlerde 'YASAKTIR'i
# kacirdi, uzun isaretlerde 'zorunlu tutuldu'yu FAZLADAN korudu). Dogrusu ucuncusu:
# ekin KENDISI sonlu bir kumeden gelmeli. Boylece 'ASLAN' de 'zorunlu tutuldu' da
# disarida kalir, 'YASAKTIR' ve 'PAZARLIKSIZDIR' iceride.
TURKCE_EKLER = set("""
DIR TIR DUR TUR DIRLER TIRLER DURLER TURLER
DI TI DU TU DIR'DIR
LAR LER LARI LERI LARIN LERIN LARDIR LERDIR LARDAN LERDEN
IN UN NIN NUN E A YE YA I U YI YU
DAN DEN TAN TEN DA DE TA TE
CA CE CASINA CESINE
IMIZ IMIZDIR IMIZDAN LARIMIZ LERIMIZ LARIMIZDIR
SI SU SIDIR SUDUR SINI SUNU
IZ SINIZ
""".split())

_KURAL_DESEN_ONBELLEK = {}

def kural_desenleri(isaretler):
    """Isaret listesini BIR KEZ derlenmis desenlere cevirir (onbellekli).

    FABLE 3. TUR · B-6: H7 her canli satir icin kural_isareti_var cagiriyordu; o da
    her cagrida her isaret icin basliksal() + re.escape() + re.compile() yapiyordu.
    Yani sabit bir veri (rc['kural_isaretleri']) satir basina yeniden hesaplaniyordu:
    300k satirlik canli hafizada `kapi` 17 sn suruyor, ~80 MB'ta ASILIYORDU.
    Desenler girdi degil SABIT oldugu icin bir kez derlenir."""
    anahtar = tuple(isaretler)
    d0 = _KURAL_DESEN_ONBELLEK.get(anahtar)
    if d0 is None:
        d0 = []
        for im in isaretler:
            d = re.sub(r"\s+", " ", basliksal(im))
            d0.append((im, re.compile(r"(?<![A-Z0-9_])"
                                      + re.escape(d).replace("\\ ", r"\s+")
                                      + r"(?![_0-9])")))
        if len(_KURAL_DESEN_ONBELLEK) > 32:
            _KURAL_DESEN_ONBELLEK.clear()      # sinirsiz buyume yok
        _KURAL_DESEN_ONBELLEK[anahtar] = d0
    return d0

def kural_isareti_var(metin, isaretler, desenler=None):
    """Kalici kural isareti taramasi — TEK yer, TEK kural.

    BAGIMSIZ DENETIM: kelime siniri lookaround'u yuzunden 'PAZARLIKSIZDIR' ve
    'MUTLAK  KURAL' (cift bosluk) KORUMASIZ kaliyordu. Artik bosluklar tekillestirilir
    ve SON-EK serbesttir (Turkce cekim: -DIR, -TIR, -LARI...). Yanlis tarafa hata
    yapiyoruz: fazladan korumak zararsiz, korumayi kacirmak KURAL KAYBIDIR.

    `desenler` verilirse yeniden derleme yapilmaz (B-6; sicak dongulerde zorunlu)."""
    h = re.sub(r"\s+", " ", basliksal(metin))
    for im, desen in (desenler if desenler is not None else kural_desenleri(isaretler)):
        for m in desen.finditer(h):
            son = m.end()
            kuyruk = ""
            while son < len(h) and (h[son].isalpha() or h[son] == "'"):
                kuyruk += h[son]; son += 1
            if not kuyruk:
                return im                      # tam kelime: 'ASLA', 'PAZARLIKSIZ'
            # SON-EK KURALI — 6. tur denetiminin iki bulgusunun ORTASI:
            #   'ASLA' isareti 'Aslan Yatirim' satirini kural sayiyordu (yanlis-pozitif).
            #   Sonra "yalniz BUYUK HARF yazimda son-ek serbest" dedim; bu kez Turkcenin
            #   EN DOGAL yazimi ('...bu pazarliksizdir.') KACIRILDI — koruma deligi.
            # Ayirt edici olcut buyuk-harf degil, ISARETIN UZUNLUGU:
            #   KISA isaret (<=5) tam kelime olmali  -> 'ASLA' evet, 'ASLAN' hayir.
            #   UZUN isaret (>=6) sinirli cekim eki alabilir -> 'PAZARLIKSIZDIR' evet.
            # Uzun bir isaretin baska bir kelimenin ici olmasi pratikte olanaksiz.
            # Turkce kesme isareti ozel adlarda eki AYIRIR: "MUTLAK KURAL'DIR"
            if kuyruk.replace("'", "") in TURKCE_EKLER:
                return im
    return None

# FABLE 3. TUR · B-6: basliksal() satir basina cagriliyor ve her cagrida iki ayri
# generator + NFKD normalize + unicodedata.combining calistiriyordu; 100k satirlik
# canlida `kapi` suresinin YARISINDAN COGU buradaydi (profil: 3.3 sn / 5.8 sn).
# Anlambilim AYNEN korunur; yalniz sicak yol ucuzlatilir:
#   1) Turkce harf esleme sozlugu str.translate tablosuna cevrildi (C hizinda),
#   2) ASCII olan satirlarda NFKD/combining adimlari HIC calistirilmaz (cogu satir).
_TR_TABLO = str.maketrans({"ı": "i", "İ": "I", "ş": "s", "Ş": "S", "ğ": "g", "Ğ": "G",
                           "ü": "u", "Ü": "U", "ö": "o", "Ö": "O", "ç": "c", "Ç": "C"})

def basliksal(s):
    """Baslik karsilastirmasi: Turkce -> ASCII, buyuk harf. '## GÜNCEL' == '## GUNCEL'."""
    s = s.translate(_TR_TABLO)
    if not s.isascii():                       # yalniz gerektiginde pahali yol
        s = unicodedata.normalize("NFKD", s)
        if not s.isascii():
            s = "".join(c for c in s if not unicodedata.combining(c))
    return s.upper().strip()

# ---------------------------------------------------------------- not / derle

def cmd_not(a):
    kok = kok_bul(a.kok); rc = rc_oku(kok); y = Y(kok, rc)
    zincir_on_kontrol(y, rc)  # yarim is birakma: bozuk zincirde ISE BASLAMA
    kilit_al(y)               # tek yazar: es zamanli derle KAYIP GUNCELLEME uretiyordu
    konu = slug(a.konu)
    tur = a.tur
    if tur not in ("durum", "karar", "bulgu", "ders", "devir", "sonraki"):
        oldur("--tur soylardan biri olmali: durum|karar|bulgu|ders|devir|sonraki")
    govde = a.metin
    if not govde and not sys.stdin.isatty():
        govde = sys.stdin.read()
    if not govde or len(govde.strip()) < 3:
        oldur("Bos fragman yazilmaz. --metin ver ya da stdin'den boru et.")

    # ANAHTAR SOZLUGU DISIPLINI: bilinmeyen konu sessizce dogmaz.
    if os.path.isfile(y.konular):
        bilinen = set(re.findall(r"^\|\s*([a-z0-9-]+)\s*\|", oku(y.konular), re.M))
        bilinen -= {"konu"}
        bilinen = {b for b in bilinen if set(b) != {"-"}}
        if konu not in bilinen:
            if not a.yeni_konu:
                oldur("Bilinmeyen konu: '%s'.\n"
                      "  Ya mevcut bir konu kullan (%s)\n"
                      "  ya da sozluge ekle: --yeni-konu \"bu konu neyi anlatir\""
                      % (konu, ", ".join(sorted(bilinen)[:8])))
            t = oku(y.konular).rstrip("\n")
            yaz(y.konular, t + "\n| %s | %s |\n" % (konu, a.yeni_konu.strip()))
            # Y-5 DUZELTMESININ URETTIGI KUSUR (kendi olctugumuz): KONULAR.md zincir
            # yukune girince, ARACIN KENDI MESRU komutu (--yeni-konu) zinciri kiriyor
            # ve kapi "defter MUHURSUZ degismis" diyordu. Politika degisikligi zincire
            # GIRMELI — ama BEYANLA. Bu yuzden burada kendi halkamizi ATIYORUZ.
            zincir_halka(y, "KONU", "konu sozlugune eklendi: %s — %s"
                         % (konu, a.yeni_konu.strip()[:80]))
            print("KONU SOZLUGE EKLENDI: " + konu + " (zincire islendi)")
    os.makedirs(y.gunluk, exist_ok=True)
    # Fable Y-7: cakisma ARSIVE karsi da aranmali; yoksa ayni-dakika+ayni-konu ikinci
    # fragman derlenirken arsivdeki ilkini eziyordu (log append-only DEGILDI).
    ad = _bos_ad(y.gunluk, "%s-%s.md" % (simdi_damga(), konu), y.gunluk_ars)
    p = os.path.join(y.gunluk, ad)
    yaz(p, "---\nkonu: %s\ntur: %s\ntarih: %s\noturum: %s\n---\n\n%s\n"
        % (konu, tur, bugun(), a.oturum or "-", govde.strip()))
    print("FRAGMAN: " + os.path.relpath(p, kok))

BOLUM_HEDEF = {"durum": "## GUNCEL DURUM", "sonraki": "## SONRAKI ADIM",
               "karar": "## KARAR GUNLUGU", "bulgu": "## ACIK KARARLAR",
               "ders": "## SABIT CERCEVE", "devir": "## GUNCEL DURUM"}

def _bolum_araligi(L, baslik):
    try:
        i = next(i for i, s in enumerate(L) if s.startswith("#") and bas_eslesir(s, baslik))
    except StopIteration:
        return None, None
    j = i + 1
    while j < len(L) and not L[j].startswith("## "):
        j += 1
    return i, j

def cmd_derle(a):
    kok = kok_bul(a.kok); rc = rc_oku(kok); y = Y(kok, rc)
    zincir_on_kontrol(y, rc)  # yarim is birakma: bozuk zincirde ISE BASLAMA
    kilit_al(y)               # tek yazar: es zamanli derle KAYIP GUNCELLEME uretiyordu
    if not os.path.isdir(y.gunluk):
        # FABLE 3. TUR · B-10: dizin YOKLUGU "fragman yok" ile ayni sayilip exit 0
        # veriliyordu — bozuk bir kurulum SESSIZ BASARI gibi gorunuyordu. Bos bir
        # gunluk/ ile silinmis bir gunluk/ ayni sey degildir.
        oldur("FRAGMAN DIZINI YOK: %s\n"
              "  Bu bir 'fragman yazilmadi' hali DEGIL, BOZUK KURULUMDUR (dizin "
              "silinmis ya da hic olusmamis).\n"
              "  Onar: python hafiza.py kur --kok=\"%s\"   (idempotenttir, mevcut "
              "icerige dokunmaz)\n"
              "  NOT: denetim izi (_ZINCIR.jsonl / _CIPA.json) da kayipsa `kur` de DURUR "
              "— once onlari geri al.\n"
              "  Sonra olc: python hafiza.py kapi" % (y.gunluk, kok))
    frg = sorted(f for f in os.listdir(y.gunluk) if f.endswith(".md"))
    if not frg:
        print("HATA: bu turda HIC FRAGMAN YAZILMAMIS.")
        print("  Calisildiysa kayit birakilmalidir: hafiza.py not --konu <konu> --tur durum --metin \"...\"")
        print("  Gercekten kaydedilecek bir sey yoksa: hafiza.py derle --bos-serbest")
        return 0 if a.bos_serbest else 1
    L = satirlar(y.canli)
    # BAGIMSIZ DENETIM (YUKSEK): `derle` canli dosyayi YENIDEN YAZAR. Blok yapisi bozuk
    # ya da bir blok kod bolgesinde gizliyken bunu yapmak, KIRMIZI CIZGILER bolumunun
    # sessizce arsive tasinmasiyla sonuclandi. Kural: yapi belirsizse DOKUNMA.
    _bozuk = []
    _acik = None
    for _n, _s in enumerate(kod_disi(L), 1):
        if _s.startswith("## ") and _acik is not None:
            _bozuk.append("satir %d: blok (satir %d) baslik sinirini asiyor" % (_n, _acik))
        if BLOK_BAS.search(_s):
            if _acik is not None:
                _bozuk.append("satir %d: onceki blok (satir %d) kapanmadan yeni blok" % (_n, _acik))
            _acik = _n
        elif BLOK_SON.search(_s):
            if _acik is None:
                _bozuk.append("satir %d: acilmamis blok kapatiliyor" % _n)
            _acik = None
    if _acik is not None:
        _bozuk.append("satir %d: blok ACIK KALDI" % _acik)
    _gizli0 = ["satir %d: konu '%s' hem gizli hem canli" % g for g in gizli_konu_cakismasi(L)]
    _gizli0 += ["satir %d: GIRINTILI blok isareti (sutun 0'da degil)" % g[0]
                for g in girintili_isaretler(L)]
    if _bozuk or _gizli0:
        sys.stderr.write("HATA: CANLI HAFIZANIN BLOK YAPISI BOZUK — `derle` DOKUNMADI.\n")
        for _b in (_bozuk[:5] + _gizli0[:5]):
            sys.stderr.write("  - %s\n" % _b)
        sys.stderr.write(
            "  Fragmanlar gunluk/ altinda DURUYOR (kaybolmadi); yapiyi duzeltip yeniden kos.\n"
            "  Olcum : python hafiza.py kapi\n"
            "  Cikis : satirlari ELLE degistirme/silme — cipa'daki satir degisir ve H1\n"
            "          'KAYIP' der. Devralinmis eski/girintili bloklar icin dogru yol:\n"
            "            python hafiza.py emekli <bas>-<son> --not \"eski blok arsive tasindi\"\n"
            "          (kapi yesillenince derle yeniden kosulur)\n")
        return 1
    islenen, eklenen_satirlar = [], []
    for f in frg:
        p = os.path.join(y.gunluk, f)
        meta, govde = fragman_coz(p)
        if not meta or "konu" not in meta:
            print("ATLANDI (frontmatter yok): " + f); continue
        konu, tur = slug(meta["konu"]), meta.get("tur", "durum")
        hedef = BOLUM_HEDEF.get(tur, "## GUNCEL DURUM")
        i, j = _bolum_araligi(L, hedef)
        # KENDI BULDUGUMUZ KUSUR (Fable'in iki turunda da cikmadi, normal hafta
        # simulasyonunda cikti) — SIKISTIRMA KAPSAMI ILE KAPI KAPSAMI AYRISMISTI:
        #   `derle` ayni konudaki eski blogu YALNIZ tur'den turetilen bolumde ariyordu;
        #   H10 ise konu tekilligini TUM DOSYADA olcuyor.
        # Sonuc: `not --konu=sonraki-adim` (varsayilan tur=durum) yazan bir kullanici,
        # hicbir kurali cignemeden GUNCEL DURUM'a IKINCI bir 'sonraki-adim' blogu
        # aldiriyor ve kapi kirmizi yaniyordu. Bu, sistemin en sik kullanilan yolunda
        # YANLIS-POZITIF demektir; kullaniciyi elle blok cerrahisine iter (tam da
        # onlemek icin var oldugumuz sey). Artik arama TUM DOSYADA yapilir ve blok
        # BULUNDUGU YERDE guncellenir (kullanicinin yerlesimi korunur).
        # Y-8: tarama KOD DISI metinde yapilir (belgelerdeki ornek blok satiri gercek
        # blok sanilirsa `derle` yanlis araligi ezerdi). Satir sayisi korunur -> indisler gecerli.
        # BAGIMSIZ DENETIM — YUKSEK: "tum dosyada ara" ilk halinde YIKICIYDI. Kapanmamis
        # bir blok isaretinden sonra gelen ILK <!-- /blok --> bulunuyordu; aradaki HER SEY
        # (KIRMIZI CIZGILER bolumu, PAZARLIKSIZ kurallar dahil) "eski blok" sayilip
        # arsive tasiniyordu. `emekli` kalici kural tasimayi ACIKCA reddederken `derle`
        # ayni isi denetimsiz yapiyordu — ayni ilkenin iki uygulamasi celisiyordu.
        # Kural: bulunan kapanis, ARADA BASKA BIR BLOK ACILMADAN gelmis olmali.
        Lk = kod_disi(L)
        eski = None
        for k in range(len(L)):
            m = BLOK_BAS.search(Lk[k])
            if m and oznitelik_coz(m.group(1)).get("konu") == konu:
                s, ic_ice = k + 1, False
                while s < len(L) and not BLOK_SON.search(Lk[s]):
                    if BLOK_BAS.search(Lk[s]):
                        ic_ice = True; break
                    s += 1
                if ic_ice or s >= len(L):
                    print("ATLANDI (konu '%s' blogu KAPANMAMIS / IC ICE — once H10'u duzelt): %s"
                          % (konu, f))
                    eski = "BOZUK"
                    break
                eski = (k, s); break
        if eski == "BOZUK":
            continue
        if eski is None and i is None:
            print("ATLANDI (bolum yok: %s): %s" % (hedef, f)); continue
        # FABLE Y-4: yol SABITTI; devral projesinde fragman gercekte
        # <hafiza_dizini>/gunluk/ altinda oldugu icin "her blogun kaynagi bellidir"
        # vaadi devral'in TAM HEDEF KITLESINDE kiriliyordu (ve hicbir kapi gormuyordu).
        _gunluk_yolu = "%s/gunluk/%s" % (
            "/".join(x for x in rc.get("hafiza_dizini", "arsiv/hafiza")
                     .replace("\\", "/").split("/") if x not in ("", ".")), f)
        blok = ['<!-- blok konu="%s" guncel="%s" kaynak="%s" -->'
                % (konu, meta.get("tarih", bugun()), _gunluk_yolu)]
        # BAGIMSIZ DENETIM 4. TUR (YUKSEK): fragman govdesinde '## ' varsa `derle` blogu
        # yaziyor, ardindan kapi onu "baslik sinirini asiyor" diye BOZUK ilan ediyordu —
        # yani arac KENDI ciktisini reddediyor, proje kilitleniyordu. Blok bir BOLUMUN
        # ICINDE yasar; govdede ikinci duzey baslik yapisal olarak zaten yanlistir.
        # Icerik SILINMEZ, bir duzey INDIRILIR ve kullaniciya soylenir.
        _govde = govde.strip().split("\n")
        _govde_kod = kod_disi(_govde)     # kod citi icindeki ornekler DEGISTIRILMEZ
        _indirilen = 0
        for _gi, _gs in enumerate(_govde):
            if (_gs.startswith("## ") and not _gs.startswith("### ")
                    and _govde_kod[_gi].startswith("## ")):
                _govde[_gi] = "#" + _gs; _indirilen += 1
        if _indirilen:
            print("  NOT: %s icinde %d adet '## ' baslik '### ' yapildi "
                  "(blok bir BOLUMUN icinde yasar; icerik korundu)." % (f, _indirilen))
        # BAGIMSIZ DENETIM 6. TUR: govdede KAPANMAMIS bir kod citi varsa blogun
        # KAPANIS isareti kod bolgesine dusuyor, arac KENDI yazdigi yapiyi bozuk
        # ilan ediyor ve `derle` bir daha calismiyordu (YENI-4 ile ayni sinif).
        # Icerik SILINMEZ: cit KAPATILIR ve kullaniciya soylenir.
        if kod_citi_dengesiz(_govde):
            # BAGIMSIZ DENETIM 7. TUR: kapatici SABIT 3 karakterdi; 4-backtick acilisi
            # 3-backtick ile "kapatiliyor" ve kilit geri geliyordu. _cit()'in kendi
            # kurali: kapanis AYNI karakterden ve EN AZ acilis kadar uzun olmali.
            # Bu yuzden ACIK citi ayni durum makinesiyle bulup onu kullaniyoruz.
            _acik0 = None
            for _gs in _govde:
                _c = _cit(_gs)
                if _c:
                    if _acik0 is None:
                        _acik0 = (_c[0], _c[1])
                    elif _c[0] == _acik0[0] and _c[1] >= _acik0[1] and not _c[2].strip():
                        _acik0 = None
            _kapanis = (_acik0[0] * _acik0[1]) if _acik0 else "```"
            _govde.append(_kapanis)
            print("  NOT: %s icinde KAPANMAMIS kod citi vardi; blok yazilirken KAPATILDI "
                  "(icerik korundu, blok yapisi bozulmasin diye)." % f)
        blok += _govde
        blok += ["<!-- /blok -->"]
        if eski:
            # BAGIMSIZ DENETIM (ORTA-YUKSEK): `emekli` KALICI KURAL tasimayi ACIKCA
            # reddederken, `derle`nin sikistirmasi ayni satirlari denetimsiz arsive
            # tasiyordu — ayni ilkenin iki uygulamasi CELISIYORDU ve iki yanda da kapi
            # yesildi. Ayni koruma buraya da konur; ihlalde fragman ATLANIR.
            _kural = None
            for _s0 in L[eski[0]:eski[1] + 1]:
                _im = kural_isareti_var(_s0, rc["kural_isaretleri"])
                if _im:
                    _kural = (_im, _s0.strip()[:80]); break
            if _kural:
                print("ATLANDI (konu '%s' blogunda KALICI KURAL var — isaret: %s):\n"
                      "  %s\n"
                      "  Sikistirma bu blogu arsive tasirdi; kalici kural tasinamaz.\n"
                      "  Once kurali SABIT CERCEVE'ye tasi, sonra yeniden derle."
                      % (konu, _kural[0], _kural[1]))
                continue
            # ANAHTAR BAZLI SIKISTIRMA: eski blok SILINMEZ, arsive TASINIR + BEYAN EDILIR.
            # (Yoksa H1 "KAYIP" derdi — ve hakli olurdu.)
            _arsive_tasi(y, L[eski[0]:eski[1] + 1],
                         "konu '%s' guncellendi — onceki blok emekli (log-compaction)" % konu)
            L = L[:eski[0]] + blok + L[eski[1] + 1:]
        else:
            L = L[:i + 1] + [""] + blok + L[i + 1:]
        eklenen_satirlar.extend(blok)
        islenen.append(f)
    if eklenen_satirlar:
        _canli_ekle_beyan(y, eklenen_satirlar,
                          "derleme: canliya eklenen bloklar (baseline-sonrasi kapsam)")
    # son guncelleme damgasi — snapshot'ta DONMUS satir oldugu icin BEYAN EDILIR
    # Fable Y-9: eskiden yalniz ilk 14 satira bakiliyordu. Damga asagi kayarsa `derle`
    # sessizce guncellemeyi birakiyor, H12/H14 zamanla YANLIS-KIRMIZI yaniyordu.
    # H12 tum dosyayi tariyor; `derle`nin daha dar bakmasi tutarsizdi. Artik ikisi de tam dosya.
    for k, s in enumerate(L):
        if s.startswith("> Son guncelleme:") or s.startswith("> Son güncelleme:"):
            yeni_s = tarih_damgasini_guncelle(s, bugun())
            if norm(yeni_s) != norm(s) and os.path.isfile(y.snap):
                for si, ss in enumerate(satirlar(y.snap), 1):
                    if ss.startswith("> Son g"):
                        _beyan_duzeltme(y, si, norm(ss), norm(yeni_s),
                                        "derleme: son guncelleme damgasi (yapisal, her turda zorunlu)")
                        break
            L[k] = yeni_s
            break
    yaz(y.canli, "\n".join(L))
    os.makedirs(y.gunluk_ars, exist_ok=True)
    for f in islenen:
        # Fable Y-7: `not` cakismayi yalniz gunluk/'te kontrol ediyordu; ayni-dakika+ayni-konu
        # ikinci fragman, ARSIVDEKI ilkini shutil.move ile SESSIZCE eziyordu. Satir kaybi yok
        # (icerik kompaksiyonla canlida/arsivde yasiyor) ama aracin kendi "log append-only"
        # ilkesi ihlal oluyordu ve HICBIR KAPI bunu gormuyordu. Artik hedefte de ad aranir.
        shutil.move(os.path.join(y.gunluk, f), os.path.join(y.gunluk_ars, _bos_ad(y.gunluk_ars, f)))
    _arsiv_dizini_tazele(y)
    zincir_halka(y, "DERLE", "derleme: %d fragman islendi" % len(islenen))
    print("DERLENDI: %d fragman islendi ve arsive tasindi." % len(islenen))
    kod, cikti = _kapi_kos(kok)
    print(cikti.strip())
    if kod != 0:
        print("\n! Kapi FAIL — derleme geri ALINMADI (derleme yikici degil). Bulguyu duzelt.")
    return 0 if kod == 0 else 1

# ---------------------------------------------------------------- emekli

def cmd_emekli(a):
    kok = kok_bul(a.kok); rc = rc_oku(kok); y = Y(kok, rc)
    zincir_on_kontrol(y, rc)  # yarim is birakma: bozuk zincirde ISE BASLAMA
    kilit_al(y)               # tek yazar: es zamanli derle KAYIP GUNCELLEME uretiyordu
    m = re.match(r"^(\d+)-(\d+)$", a.aralik or "")
    if not m:
        oldur("Aralik <bas>-<son> bicimindedir (1 tabanli, kapsayici).")
    bas = tamsayi(m.group(1), "aralik baslangici", en_az=1)
    son = tamsayi(m.group(2), "aralik sonu", en_az=1)
    if not a.not_:
        oldur("Gerekcesiz emeklilik YASAK: --not \"neden emekli ediliyor\"")
    # Y-3: hic HAFIZA_*.md yokken bu satir ham IndexError veriyordu.
    if a.hedef:
        hedef_ad = a.hedef
    else:
        adaylar = sorted(f for f in (os.listdir(y.h) if os.path.isdir(y.h) else [])
                         if re.match(r"^HAFIZA_.*\.md$", f))
        if not adaylar:
            oldur("Emeklilik hedefi YOK: %s icinde HAFIZA_*.md bulunamadi.\n"
                  "  Ya --hedef=<dosya> ver, ya once bir arsiv dosyasi ac "
                  "(ornek: %s/HAFIZA_2026-Q3.md)."
                  % (y.h, os.path.relpath(y.h, kok).replace("\\", "/")))
        hedef_ad = adaylar[-1]
    # FABLE 3. TUR · B-2 [YUKSEK]: --hedef hicbir konum denetiminden gecmiyordu;
    # `--hedef=../../../KURBAN.md` proje agacinin DISINDAKI bir dosyaya KALICI
    # yaziyor, kapi YESIL ve exit 0 oluyordu (olculdu). Ajanlara talimat verilen
    # bir araçta enjekte edilmis tek bir --hedef, hafizayi disari sizdirabilirdi.
    hedef = cli_yol_coz(kok, hedef_ad, "--hedef", taban=y.h)
    # IC DENETIM (B-6): kacis kapisi yalniz AGAC DISINI kapatmisti; agac ICINDE
    # --hedef CANLI DOSYANIN KENDISI olabiliyordu. Sonuc: satir "arsive tasindi" diye
    # _TASINMA.jsonl'e yaziliyor ama aslinda ayni dosyanin sonuna gidiyor — denetim izi
    # YALAN soyluyor ve sonraki butun H1-KOVA muhasebesi o yalana dayaniyor. Kapi da
    # gormuyordu (hedefte "var" cunku ayni dosya). Hedef bir ARSIV dosyasi olmalidir.
    _hg = os.path.realpath(hedef)
    _yasak = {os.path.realpath(x) for x in
              (y.canli, y.kural, y.plan, y.konular, y.snap, y.cipa, y.zincir,
               y.kova, y.duzelt, y.tasinma, y.korunan, y.yeni)}
    if _hg in _yasak:
        oldur("--hedef bir ARSIV dosyasi olmali; verilen yol canli hafiza ya da bir "
              "DEFTER: %s\n"
              "  Bu hedefe 'tasima' yapmak, denetim izine YALAN yazardi (satir arsive "
              "gitmis gibi kaydedilir, oysa ayni dosyada kalir).\n"
              "  Ornek: --hedef=HAFIZA_01.md" % hedef_ad)
    if not _hg.startswith(os.path.realpath(y.h) + os.sep):
        oldur("--hedef HAFIZA DIZININDE olmali (%s): %s"
              % (os.path.relpath(y.h, kok).replace("\\", "/"), hedef_ad))
    if not os.path.isfile(hedef):
        oldur("hedef arsiv dosyasi yok: " + hedef_ad)

    yedek = {p: oku(p) for p in [y.canli, hedef, y.tasinma]}
    L = satirlar(y.canli)
    if bas < 1 or son > len(L) or bas > son:
        oldur("aralik disi (dosyada %d satir var)" % len(L))
    kesit = L[bas - 1:son]
    tasinan = [norm(s) for s in kesit if anlamli(s)]
    if not tasinan:
        oldur("secilen aralikta anlamli satir yok")

    # kalici kural emekli edilemez (H7 ile ayni ilke, ONCEDEN engelle)
    for s in tasinan:
        isaret = kural_isareti_var(s, rc["kural_isaretleri"])
        if isaret:
            oldur("KALICI KURAL emekli edilemez (isaret: %s). Evi SABIT CERCEVE'dir.\n"
                  "  Satir: %s" % (isaret, s[:90]))

    yeni_canli = L[:bas - 1] + L[son:]
    yaz(y.canli, "\n".join(yeni_canli))
    _isaret = "<!-- emekli %s · %s -->" % (bugun(), a.not_)
    with open(hedef, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n" + _isaret + "\n")
        f.write("\n".join(kesit).rstrip() + "\n")
    _beyan_yeni_satirlar(y, [_isaret], "emekli: arsiv isaret satiri (arac uretti)")
    with open(y.tasinma, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"t": _dt.datetime.now().isoformat(timespec="seconds"),
                            "hedef": hedef_ad, "not": a.not_, "satirlar": tasinan},
                           ensure_ascii=False) + "\n")
    _halka = zincir_halka(y, "EMEKLI", a.not_, ek={"hedef": hedef_ad, "adet": len(tasinan)})
    _arsiv_dizini_tazele(y)

    kod, cikti = _kapi_kos(kok)
    if kod != 0:
        for p, icerik in yedek.items():
            yaz(p, icerik)
        _zincir_geri_al(y, _halka, "emeklilik kapi FAIL nedeniyle geri alindi")
        sys.stderr.write(cikti + "\n")
        oldur("KAPI FAIL — emeklilik GERI ALINDI (dosyalar eski haline dondu).", 1)
    print("EMEKLI EDILDI: %d satir -> %s (kapi YESIL)" % (len(tasinan), hedef_ad))

def _zincir_geri_al(y, halka, gerekce):
    """Geri alinan islemin zincir izini kapatir. UC deneme, uc ders:

      1) Korlemesine SON satiri sil -> paralel bir oturumun MESRU halkasi silinebiliyordu.
      2) Halkayi KIMLIGIYLE sil -> halka ORTADA kalmissa hash bagi KALICI koptu; `muhur`
         onaramiyordu, proje kilitleniyordu.
      3) Her zaman TERS HALKA at -> zincir saglam kaliyor ama ters halka, kullanicinin
         O ANDAKI (hatali) durumunu muhurluyor; hatasini duzeltince kapi kirmizi yaniyordu.

    Dogrusu ikisinin BIRLESIMI: halka HALA SONUNCUYSA (yani araya kimse yazmamis)
    guvenle geri sarilir — islem hic olmamis gibi. Aradan yazan olmussa SILINMEZ,
    ters halka atilir; orada kirmizi yanmasi DOGRUDUR (gercekten olagandisi bir sey oldu)."""
    if os.path.isfile(y.zincir):
        sat = [s for s in oku(y.zincir).split("\n") if s.strip()]
        if sat:
            try:
                sonuncu = json.loads(sat[-1]).get("halka")
            except ValueError:
                sonuncu = None
            if sonuncu == halka:
                yaz(y.zincir, "\n".join(sat[:-1]) + ("\n" if sat[:-1] else ""))
                return
    sys.stderr.write("UYARI: geri alinan halkanin USTUNE baska halka yazilmis "
                     "(paralel oturum?). Zincir SILINMIYOR; ters halka atiliyor.\n")
    zincir_halka(y, "GERI_ALMA", gerekce, ek={"geri_alinan": halka})

def _kapi_kos(kok):
    # -X utf8 ZORUNLU: Windows'ta cocuk surecin stdout kodlamasi varsayilan olarak cp1254'tur;
    # biz utf-8 okudugumuz icin '·' ve '—' bozuk cikardi (Windows sinamasinda olculdu).
    ortam = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.abspath(__file__), "kapi", "--kok=" + kok],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=ortam)
    return r.returncode, (r.stdout or "") + (r.stderr or "")

# ---------------------------------------------------------------- karar (ADR)

def cmd_karar(a):
    kok = kok_bul(a.kok); rc = rc_oku(kok); y = Y(kok, rc)
    zincir_on_kontrol(y, rc)  # yarim is birakma: bozuk zincirde ISE BASLAMA
    kilit_al(y)               # tek yazar: es zamanli derle KAYIP GUNCELLEME uretiyordu
    os.makedirs(y.kararlar, exist_ok=True)
    mevcut = adr_listesi(y)
    no = (max([k["no"] for k in mevcut]) + 1) if mevcut else 1
    baslik = a.baslik
    if not baslik:
        oldur("--baslik zorunlu")
    konu = slug(a.konu) if a.konu else slug(baslik)
    yerini = "-"
    if a.yerine:
        # Y-3: `--yerine=abc` ham ValueError veriyordu.
        yerine_no = tamsayi(a.yerine, "--yerine", en_az=1)
        eski = [k for k in mevcut if k["no"] == yerine_no]
        if not eski:
            oldur("--yerine ile verilen karar yok: %s (mevcut: %s)"
                  % (a.yerine, ", ".join("%04d" % k["no"] for k in mevcut) or "hic karar yok"))
        yerini = "%04d" % yerine_no
    ad = "%04d-%s.md" % (no, slug(baslik))
    p = os.path.join(y.kararlar, ad)
    yaz(p, SAB_ADR.format(no=no, baslik=baslik, t=bugun(), konu=konu, yerini=yerini))
    if a.yerine:
        ep = os.path.join(y.kararlar, eski[0]["dosya"])
        t = oku(ep)
        t = re.sub(r"^durum:.*$", "durum: yerine-gecildi", t, count=1, flags=re.M)
        t = re.sub(r"^yerine-gecen:.*$", "yerine-gecen: %04d" % no, t, count=1, flags=re.M)
        yaz(ep, t)
        print("YERINE GECILDI: %s -> %s" % (eski[0]["dosya"], ad))
    _karar_dizini_yaz(y)
    print("KARAR: kararlar/" + ad)
    print("  Doldur: Baglam · Karar · Alternatifler · BEDELLER · Dogrulama")
    print("  Kabul edince: durum: kabul  (kabul edilmis ADR bir daha DUZENLENMEZ)")

def _karar_dizini_yaz(y):
    ks = adr_listesi(y)
    sat = ["# KARAR DIZINI (uretilir — elle duzenleme)", "",
           "> `durum: kabul` olanlar BUGUN GECERLI olan kararlardir.", ""]
    sat.append("| No | Baslik | Durum | Konu | Yerine gecen |")
    sat.append("|---|---|---|---|---|")
    for k in ks:
        m = k["meta"]
        sat.append("| [%04d](%s) | %s | %s | %s | %s |" %
                   (k["no"], k["dosya"], m.get("baslik", "-"), m.get("durum", "-"),
                    m.get("konu", "-"), m.get("yerine-gecen", "-")))
    yaz(os.path.join(y.kararlar, "0000-DIZIN.md"), "\n".join(sat) + "\n")

# ---------------------------------------------------------------- muhur

def cmd_muhur(a):
    kok = kok_bul(a.kok); rc = rc_oku(kok); y = Y(kok, rc)
    zincir_on_kontrol(y, rc)  # yarim is birakma: bozuk zincirde ISE BASLAMA
    kilit_al(y)               # tek yazar: es zamanli derle KAYIP GUNCELLEME uretiyordu
    if not a.gerekce or len(a.gerekce.strip()) < 15:
        oldur("GEREKCESIZ MUHUR YASAK (en az 15 karakter).")
    h = zincir_halka(y, "MUHUR", a.gerekce.strip())
    print("MUHURLENDI: " + h[:16] + "...")

# ---------------------------------------------------------------- beyan yardimcisi

def _beyan_duzeltme(y, snap_no, eski, yeni, gerekce):
    d = defter_liste(y.duzelt, "duzeltmeler", {"satir": (int, str), "eski": str, "yeni": str})
    for kayit in d["duzeltmeler"]:
        if kayit["satir"] == snap_no:
            if norm(kayit.get("yeni", "")) == norm(yeni):
                return
            kayit.setdefault("gecmis", []).append(kayit["yeni"])
            kayit["yeni"] = yeni
            kayit["gerekce"] = gerekce
            yaz(y.duzelt, json.dumps(d, ensure_ascii=False, indent=1) + "\n")
            return
    d["duzeltmeler"].append({"satir": snap_no, "eski": eski, "yeni": yeni,
                             "gerekce": gerekce, "gecmis": []})
    yaz(y.duzelt, json.dumps(d, ensure_ascii=False, indent=1) + "\n")

def _beyan_yeni_satirlar(y, satir_listesi, gerekce):
    """Aracin KENDI urettigi (canliya AIT OLMAYAN) satirlari `_YENI_SATIRLAR.txt`'ye
    beyan eder. IC DENETIM (B-4): `kur`/`devral`in yazdigi arsiv iskeleti hicbir yerde
    beyan edilmiyordu ve --siki modda daha ILK kurulumdan itibaren sahte-pozitif
    uretiyordu. Bu satirlar CANLIDA olmayacagi icin `ek_canli`ya YAZILMAZ."""
    yeni = [norm(x) for x in satir_listesi if anlamli(x)]
    if not yeni:
        return
    with open(y.yeni, "a", encoding="utf-8", newline="\n") as f:
        f.write(";; %s — %s\n" % (bugun(), gerekce))
        for x in yeni:
            f.write(x + "\n")

def _canli_ekle_beyan(y, yeni_satirlar, gerekce):
    """FABLE BULGU 1'IN KAPATILMASI.

    Eskiden: cipa yalniz `kur`/`devral` aninda donuyordu. Kurulumdan SONRA eklenen her
    satir H1 ve H1-KOVA kapsaminin DISINDAYDI -> silinince BUTUN KAPILAR SESSIZ GECIYORDU.
    Uzun omurlu bir projede canli icerigin neredeyse tamami kurulumdan sonra eklenir;
    yani sistemin merkezi vaadi ('kaybolmadi bir TEST SONUCUDUR') icerigin cogunlugu
    icin gecerli DEGILDI.

    Artik: canliya eklenen her satir iki deftere birden yazilir —
      _YENI_SATIRLAR.txt -> H1 (birlesim) o satiri BEKLER
      _KOVA.json/ek_canli -> H1-KOVA o satirin CANLIDA durmasini BEKLER
    Beyansiz silinirse H1 'KAYIP', canlidan arsive beyansiz tasinirsa H1-KOVA 'KACMIS' der.
    Mesru cikis yollari: `emekli` ve `derle` sikistirmasi (ikisi de _TASINMA.jsonl'e beyan eder)."""
    yeni_satirlar = [norm(s) for s in yeni_satirlar if anlamli(s)]
    if not yeni_satirlar:
        return
    snap_ms = cok_kume(anlamli_satirlar(y.snap)) if os.path.isfile(y.snap) else {}
    # snapshot'ta ZATEN varsa "yeni" diye beyan etme (H1 bunu kayip-maskeleme sayar)
    beyan = [s for s in yeni_satirlar if s not in snap_ms]
    if beyan:
        with open(y.yeni, "a", encoding="utf-8", newline="\n") as f:
            f.write(";; %s — %s\n" % (bugun(), gerekce))
            for s in beyan:
                f.write(s + "\n")
    kv = defter_yukle(y.kova, {"satirlar": {}})
    metin_listesi(kv.get("ek_canli", []), "_KOVA.json", "ek_canli")
    kv.setdefault("ek_canli", []).extend(yeni_satirlar)
    yaz(y.kova, json.dumps(kv, ensure_ascii=False, indent=1) + "\n")


def _arsive_tasi(y, kesit, not_metni, hedef_ad=None):
    """Canlidan cikarilan satirlari arsive EKLER + _TASINMA.jsonl'e BEYAN EDER."""
    tasinan = [norm(s) for s in kesit if anlamli(s)]
    if not tasinan:
        return None
    hedef_ad = hedef_ad or sorted(f for f in os.listdir(y.h)
                                  if re.match(r"^HAFIZA_.*\.md$", f))[-1]
    _isaret = "<!-- emekli %s · %s -->" % (bugun(), not_metni)
    with open(os.path.join(y.h, hedef_ad), "a", encoding="utf-8", newline="\n") as f:
        f.write("\n" + _isaret + "\n")
        f.write("\n".join(kesit).rstrip() + "\n")
    _beyan_yeni_satirlar(y, [_isaret], "derle: arsiv isaret satiri (arac uretti)")
    with open(y.tasinma, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"t": _dt.datetime.now().isoformat(timespec="seconds"),
                            "hedef": hedef_ad, "not": not_metni, "satirlar": tasinan},
                           ensure_ascii=False) + "\n")
    return hedef_ad



# ---------------------------------------------------------------- BLOKLASTIR

# Bloklastirmaya KAPALI bolumler:
#  - kural evi: kalici kural ASLA sikistirilmaz (H7 ile ayni ilke)
#  - karar gunlugu: kronolojik ekle-only, anahtar bazli sikistirma uygulanmaz
#  - arsiv dizini: uretilen bolum
KAPALI_BOLUM = ["KARAR GUNLUGU", "ARSIV DIZINI"]

# Bir bolumun basligi bunlardan BIRINI iceriyorsa, .hafizarc ne derse desin
# ASLA bloklastirilmaz. Gerekce: bloklastirmak o bolumu anahtar-bazli sikistirmaya
# acar; bir gun ayni konuda yeni blok gelirse ESKI blok arsive tasinir. Kirmizi
# cizgi/kalici kural icin bu KABUL EDILEMEZ — gorunurlugu olur (H7 dersi).
# Yanlis tarafa hata yapmayi tercih ediyoruz: fazladan atlamak zararsiz (bolum
# oldugu gibi kalir), fazladan bloklamak tehlikeli.
KURAL_EVI_ANAHTARLARI = ["KIRMIZICIZGI", "SABITCERCEVE", "KURAL", "PROTOKOL",
                         "TALIMAT", "DEGISMEZ", "ZORUNLU", "ILKE", "SINIR",
                         # FABLE Y-2: anlamca kirmizi-cizgi olan Turkce basliklar liste
                         # disindaydi ve BLOKLANACAK sayiliyordu.
                         "DEGISMEYEN", "ANAYASA", "YASAK", "TAVIZ", "ODUN",
                         "PAZARLIKSIZ", "MUTLAK", "ASLA", "DOKUNULMAZ", "SART",
                         "AKIT", "TAAHHUT", "GARANTI", "SOZLESME"]

def cmd_bloklastir(a):
    """Devralinan bir projedeki MEVCUT bolumleri geriye donuk blok isaretine alir.

    ICERIGE DOKUNMAZ: yalnizca her bolumun basina/sonuna gorunmez isaret satiri EKLER.
    Hicbir satir silinmez, tasinmaz, yeniden yazilmaz. Eklenen satirlar
    _YENI_SATIRLAR.txt'ye BEYAN EDILIR (cipa/baseline SIFIRLANMAZ).
    Once KURU PROVA calisir; --uygula verilmedikce diske hicbir sey yazilmaz.
    """
    kok = kok_bul(a.kok); rc = rc_oku(kok); y = Y(kok, rc)
    zincir_on_kontrol(y, rc)  # yarim is birakma: bozuk zincirde ISE BASLAMA
    kilit_al(y)               # tek yazar: es zamanli derle KAYIP GUNCELLEME uretiyordu
    L = satirlar(y.canli)
    kapali = [basliksal(x) for x in KAPALI_BOLUM] + [bas_anahtar(x) for x in rc["kural_evi_bolumleri"]]

    # bolumleri cikar
    bolumler = []
    for i, s in enumerate(L):
        if s.startswith("## "):
            j = i + 1
            while j < len(L) and not L[j].startswith("## "):
                j += 1
            bolumler.append((i, j, s.rstrip()))

    plan, atlanan = [], []
    kullanilan = set()
    Lk = kod_disi(L)          # Y-8: ornek/belge satirlari gercek blok sayilmasin
    for i, j, bas in bolumler:
        govde = [k for k in range(i + 1, j) if anlamli(L[k])]
        if any(BLOK_BAS.search(Lk[k]) for k in range(i, j)):
            atlanan.append((bas, "zaten bloklu")); continue
        if any(k in bas_anahtar(bas) for k in [bas_anahtar(x) for x in KAPALI_BOLUM]):
            atlanan.append((bas, "kapali bolum (kronolojik/uretilen)")); continue
        if any(bas_anahtar(x) == bas_anahtar(bas) for x in rc["kural_evi_bolumleri"]):
            atlanan.append((bas, "KURAL EVI (yapilandirma) — asla sikistirilmaz")); continue
        if any(k in bas_anahtar(bas) for k in KURAL_EVI_ANAHTARLARI):
            atlanan.append((bas, "KURAL EVI (baslik anahtari) — asla sikistirilmaz")); continue
        # ANLAMSAL AG (kelime listesi sonlu ve atlatilabilir): govdesinde kural isareti
        # GECEN her bolum de kural evi sayilir. Yanlis tarafa hata yapiyoruz: fazladan
        # atlamak zararsiz, fazladan bloklamak tehlikeli.
        govde_metni = "\n".join(L[i + 1:j])
        isaretli = [im for im in rc["kural_isaretleri"]
                    if re.search(r"(?<![A-Z0-9_])" + re.escape(basliksal(im)) + r"(?![A-Z0-9_])",
                                 basliksal(govde_metni))]
        if isaretli:
            atlanan.append((bas, "KURAL EVI (govdede '%s' isareti) — asla sikistirilmaz"
                            % isaretli[0])); continue
        if not govde:
            atlanan.append((bas, "bos")); continue
        ham = re.sub(r"^#+\s*", "", bas)
        ham = re.sub(r"[\(\u2014\u2013-].*$", "", ham).strip() or ham
        konu = "-".join(slug(ham).split("-")[:4]) or "bolum"
        n = 2
        while konu in kullanilan:
            konu = "%s-%d" % (konu[:36], n); n += 1
        kullanilan.add(konu)
        plan.append({"bas": bas, "i": i, "j": j, "konu": konu, "satir": len(govde)})

    print("=== BLOKLASTIRMA — %s ===" % ("UYGULAMA" if a.uygula else "KURU PROVA (hicbir sey yazilmadi)"))
    print("\nBLOKLANACAK (%d bolum):" % len(plan))
    for p0 in plan:
        print("  %-52s -> konu=%-28s (%d satir)" % (p0["bas"][:52], p0["konu"], p0["satir"]))
    print("\nATLANAN (%d bolum):" % len(atlanan))
    for b, n0 in atlanan:
        print("  %-52s -- %s" % (b[:52], n0))
    if not plan:
        print("\nYapilacak is yok."); return 0
    if not a.uygula:
        print("\nUygulamak icin: hafiza.py bloklastir --uygula")
        print("NOT: konu adlari baslikitan turetildi. Yanlis buldugun varsa ONCE bolum basligini")
        print("     duzelt ya da uyguladiktan sonra blok satirindaki konu= degerini elle degistir")
        print("     (ve KONULAR.md'yi guncelle).")
        return 0

    # --- UYGULA ---
    yedek = os.path.join(y.h, "_BLOKLASTIRMA_ONCESI_%s.md" % bugun())
    shutil.copyfile(y.canli, yedek)
    # FABLE Y-1: geri-alma yedegi _KOVA.json'u KAPSAMIYORDU. `_canli_ekle_beyan` kapidan
    # ONCE ek_canli'ya yaziyordu; kapi FAIL'de canli geri aliniyor ama kova geri alinmiyordu
    # -> proje, asil sorun cozuldukten SONRA BILE kalici kirmizida kaliyordu, ve arac
    # "dosyalar eski haline dondu" diye YANLIS rapor veriyordu. Yedek artik TUM yazilan
    # dosyalari kapsar (yazdigin her dosyayi yedekle kurali).
    onceki = {p0: oku(p0) for p0 in [y.canli, y.yeni, y.konular, y.kova]}
    eklenen = []
    for p0 in sorted(plan, key=lambda x: -x["i"]):      # SONDAN basa: indeksler kaymasin
        bas_satir = '<!-- blok konu="%s" guncel="%s" kaynak="devir" -->' % (p0["konu"], bugun())
        son_satir = "<!-- /blok -->"
        son = p0["j"]
        while son > p0["i"] + 1 and not anlamli(L[son - 1]):
            son -= 1                                    # sondaki bos satirlar blogun DISINDA kalsin
        L = L[:son] + [son_satir] + L[son:]
        L = L[:p0["i"] + 1] + [bas_satir] + L[p0["i"] + 1:]
        eklenen += [bas_satir, son_satir]
    yaz(y.canli, "\n".join(L))
    _canli_ekle_beyan(y, eklenen,
                      "bloklastirma: yalniz ISARET satiri eklendi, icerik degismedi")
    kt = oku(y.konular).rstrip("\n")
    bilinen = set(re.findall(r"^\|\s*([a-z0-9-]+)\s*\|", kt, re.M))
    for p0 in plan:
        if p0["konu"] not in bilinen:
            kt += "\n| %s | %s (devirde bloklastirildi) |" % (p0["konu"], p0["bas"].lstrip("# ").strip()[:60])
    yaz(y.konular, kt + "\n")
    _halka = zincir_halka(y, "BLOKLASTIRMA",
                          "devralinan bolumler geriye donuk bloklandi (%d)" % len(plan))

    kod, cikti = _kapi_kos(kok)
    if kod != 0:
        for p0, ic in onceki.items():
            yaz(p0, ic)
        _zincir_geri_al(y, _halka, "bloklastirma kapi FAIL nedeniyle geri alindi")
        sys.stderr.write(cikti + "\n")
        oldur("KAPI FAIL — bloklastirma GERI ALINDI (dosyalar eski haline dondu). Yedek: %s"
              % os.path.relpath(yedek, kok), 1)
    print("\nUYGULANDI: %d bolum bloklandi · yedek: %s" % (len(plan), os.path.relpath(yedek, kok)))
    print(cikti.strip())
    return 0

# ---------------------------------------------------------------- DEVRAL

ONCEKI_IZ_ADLARI = ("_CIPA.json", "_ZINCIR.jsonl", "_KOVA.json", "_KAYNAK.md",
                    "_DUZELTMELER.json", "_TASINMA.jsonl", "_KORUNAN.json")

def onceki_kurulum_izleri(kok, canli_p=None):
    """Bu dizinde DAHA ONCE bir hafiza kurulumu olduguna dair TUM izler.

    UCUNCU TASARIM (ilk ikisi denetimde kirildi):
      1. deneme — capa `_CIPA.json`'a baglandi: tek `rm _CIPA.json` ile asildi.
      2. deneme — `devral`a SABIT YOLLU ("arsiv/hafiza", ".../v2") yetim kontrolu:
         uc ayri yoldan asildi (`rm -rf`, `mv`, ozel `hafiza_dizini`) VE mesru bir v1
         devralmasini TAMAMEN kilitledi (kur ve devral birbirini gosteren kapali dongu).

    KABUL: yazma erisimi olan biri HER capayi silebilir; bunu dosya tabanli bir duzende
    ENGELLEMEK mumkun degil. O yuzden artik ENGELLEMIYORUZ — GORUNMEZ KILINMASINI
    engelliyoruz. Iz TUM AGACTA (sabit yolda degil) aranir; bulunan her sey yeni
    zincirin GENESIS halkasina ve CANLI HAFIZAYA kalici olarak yazilir. Saldirganin
    izi silmesi icin korumaya calistigi metnin KENDISINI bozmasi gerekir."""
    izler = []
    haric = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}
    for r0, d0, f0 in os.walk(kok):
        d0[:] = [d for d in d0 if d not in haric]
        for f in f0:
            if f in ONCEKI_IZ_ADLARI or re.match(r"^_KAYNAK.*\.md$|^HAFIZA_.*\.md$", f):
                izler.append(os.path.relpath(os.path.join(r0, f), kok).replace("\\", "/"))
    # Canli hafizanin KENDISI de iz tasir: `derle`nin yazdigi blok isaretleri
    # kaynak= alaniyla eski hafiza dizinini gosterir. Dosyalar silinse de bu kalir.
    if canli_p and os.path.isfile(canli_p):
        try:
            for m in re.finditer(r'kaynak="([^"]+)"', oku(canli_p)):
                if "/gunluk/" in m.group(1):
                    izler.append("canli hafizada blok kaynagi: " + m.group(1))
                    break
        except SystemExit:
            pass
    return sorted(set(izler))

def cmd_devral(a):
    """ILERLEMIS bir projeyi v2'ye DEVRALIR (kurulum degil, devir).

    Farki: (1) mevcut sistemi TANIR ve ona DOKUNMAZ — ikinci cipa/zincir acmaz,
    v1 defterlerine yazmaz; kendi ad alanini kullanir. (2) Yapilandirmayi diskteki
    GERCEKTEN turetir (basliklar, arsiv turleri, tavan) — varsayimla ilk gun kirmizi
    seli uretmez. (3) Canli dosyayi ONCE yedekler. (4) Sonunda TRIYAJLI devir raporu verir.
    """
    kok = os.path.abspath(a.kok or os.getcwd())
    if not os.path.isdir(kok):
        oldur("kok yok: " + kok)
    if os.path.isfile(os.path.join(kok, RC_AD)):
        oldur(RC_AD + " ZATEN VAR — bu proje kurulu/devralinmis. Devir bir kez yapilir.")
    # IC DENETIM (Y-6): `.hafizarc` silinip `devral` kosularak her tahrif aklaniyordu.
    # `devral` yalnizca .hafizarc'in YOKLUGUNA bakiyordu; oysa diskte bir v2 KURULUMU
    # (cipa + zincir + kova) duruyorsa bu "devralinacak eski sistem" DEGIL, YETIM
    # KALMIS BIR v2'dir ve uzerine yeni capa atmak aklamadir.
    print("=== DEVIR — kesif ===")
    # 1) canli hafiza dosyasi
    # Fable (kozmetik): os.listdir SIRASIZDIR — ayni projede iki kosuda FARKLI dosya
    # secilebiliyordu. Artik: once PROJE_HAFIZA.md, sonra alfabetik (determinist).
    adaylar = sorted(f for f in os.listdir(kok) if f.upper().endswith("HAFIZA.MD")
                     or f.upper() in ("PROJE_HAFIZA.MD", "MEMORY.MD", "HAFIZA.MD"))
    adaylar.sort(key=lambda f: (f.upper() != "PROJE_HAFIZA.MD", f.upper()))
    if a.canli is None and len(adaylar) > 1:
        print("  ! birden cok aday: %s -> '%s' secildi (--canli ile degistirebilirsin)"
              % (", ".join(adaylar), adaylar[0]))
    canli_ad = a.canli or (adaylar[0] if adaylar else "PROJE_HAFIZA.md")
    # B-2/B-3 ile ayni gecit: --canli de kok agacinda kalmak zorunda.
    canli_p = cli_yol_coz(kok, canli_ad, "--canli")
    if os.path.lexists(canli_p) and not duzenli_dosya(canli_p):
        oldur("CANLI HAFIZA YOLU DUZENLI DOSYA DEGIL: %s\n"
              "  Dizin, FIFO, kirik link ya da link dongusu olabilir. "
              "--canli ile baska bir dosya ver ya da yolu duzelt." % canli_p)
    yeni_dosya = not os.path.isfile(canli_p)
    print("  canli hafiza      : %s%s" % (canli_ad, "  (YOK — olusturulacak)" if yeni_dosya else ""))

    # 2) mevcut hafiza sistemi var mi?
    eski_h = os.path.join(kok, "arsiv", "hafiza")
    eski_izler = []
    if os.path.isdir(eski_h):
        # Fable (kozmetik): `kur`un iz deseni _KOVA.json'u iceriyordu, `devral`inki
        # icermiyordu -> yalniz _KOVA.json kalmis bir v1, "sistem yok" sanilabiliyordu.
        eski_izler = [f for f in os.listdir(eski_h)
                      if re.match(r"^_KAYNAK.*\.md$|^_ZINCIR\.jsonl$|^HAFIZA_.*\.md$"
                                  r"|^_KOVA\.json$|^_CIPA\.json$", f)]
    devralinan = bool(eski_izler)
    hdir_rel = "arsiv/hafiza/v2" if devralinan else "arsiv/hafiza"
    print("  mevcut sistem     : %s" % ("VAR (%d iz) — DOKUNULMAYACAK" % len(eski_izler) if devralinan else "yok"))
    print("  v2 ad alani       : %s" % hdir_rel)
    # AKLAMA GORUNURLUGU (B-1): TUM agacta onceki kurulum izi ara. Bulunanlar
    # engellenmez — GENESIS halkasina ve CANLI HAFIZAYA kalici olarak yazilir.
    tum_izler = onceki_kurulum_izleri(kok, canli_p)
    if tum_izler:
        print("  ! ONCEKI KURULUM IZI: %d (yeni capa bunu KAYDA GECIRECEK)" % len(tum_izler))
        for _i in tum_izler[:4]:
            print("      - %s" % _i)
        if len(tum_izler) > 4:
            print("      … +%d iz daha" % (len(tum_izler) - 4))

    # 3) basliklar (SUSLEMELERIYLE BIRLIKTE, birebir)
    basliklar = []
    if not yeni_dosya:
        basliklar = [s.rstrip() for s in satirlar(canli_p) if s.startswith("## ")]
    print("  bulunan bolum     : %d" % len(basliklar))

    # 4) arsiv turleri (diskten)
    turler = []
    ars = os.path.join(kok, "arsiv")
    if os.path.isdir(ars):
        turler = sorted(d for d in os.listdir(ars)
                        if os.path.isdir(os.path.join(ars, d)) and d != "hafiza")
    print("  arsiv turleri     : %s" % (", ".join(turler) if turler else "(yok)"))

    # 5) devralinan eski arsiv dosyalari (H1 birlesimine girecek)
    ek = []
    for r0, d0, f0 in os.walk(ars if os.path.isdir(ars) else kok):
        d0[:] = [d for d in d0 if d not in (".git", "node_modules", "__pycache__")]
        for f in f0:
            if re.match(r"^HAFIZA_.*\.md$", f):
                rel = os.path.relpath(os.path.join(r0, f), kok).replace("\\", "/")
                # Fable (kozmetik): duz startswith 'arsiv/hafiza-eski/...' yolunu da
                # v2 ad alani sanardi. Dizin SINIRI arayarak karsilastir.
                if not (rel == hdir_rel or rel.startswith(hdir_rel + "/")):
                    ek.append(rel)
    print("  devralinan arsiv  : %d dosya" % len(ek))

    # 6) kural evi tahmini: kural isareti ZATEN gecen bolumler
    isaretler = VARSAYILAN_RC["kural_isaretleri"]
    kural_evi, mevcut_bolum = [], None
    if not yeni_dosya:
        for s in satirlar(canli_p):
            if s.startswith("## "):
                mevcut_bolum = s.rstrip()
            elif mevcut_bolum and any(basliksal(i) in basliksal(s) for i in isaretler):
                if mevcut_bolum not in kural_evi:
                    kural_evi.append(mevcut_bolum)
    if not yeni_dosya:
        for s in satirlar(canli_p):
            if s.startswith("## ") and any(k in bas_anahtar(s) for k in KURAL_EVI_ANAHTARLARI):
                if s.rstrip() not in kural_evi:
                    kural_evi.append(s.rstrip())
    print("  kural evi bolumu  : %d (isaretten + baslik anahtarindan)" % len(kural_evi))

    # 7) tavan: mevcut boyutun uzerinde bir yerden basla (ilk gun H2 kirmizi olmasin)
    bayt = os.path.getsize(canli_p) if not yeni_dosya else 0
    tavan = max(60, int((bayt / 1024.0) * 1.20) + 5)
    # BAGIMSIZ DENETIM: cok buyuk bir hafizayi devralinca tavan 1000'i asiyor ve H15
    # aninda "POLITIKA GEVSETILMIS" diyordu; cikis yolu da yoktu (emekli kapi kirmizi
    # oldugu icin hep geri aliyordu). Artik devir, gevsekligi KENDI BEYAN EDER.
    politika_gerekce = {}
    if tavan > 1000:
        politika_gerekce["tavan_kb"] = (
            "devralinan canli hafiza %.0f KB idi; tavan devir aninda buna gore kuruldu. "
            "Kucultme yolu: hafiza.py emekli ... — kuculdukce tavani da dusur." % (bayt / 1024.0))
    print("  canli boyut/tavan : %.1f KB / %d KB%s"
          % (bayt / 1024.0, tavan, "  (H15'e BEYAN yazildi)" if politika_gerekce else ""))

    rc = {
        "surum": SURUM, "ad": a.ad or os.path.basename(kok.rstrip(os.sep)),
        "canli": canli_ad,
        "kural_evi_dosya": "CLAUDE.md", "tavan_kb": tavan, "bayatlik_gun": 30,
        # BAGIMSIZ DENETIM 6. TUR: hic '## ' baslik yoksa VARSAYILANA dusuluyor ve
        # dosyada OLMAYAN 6 bolum birden isteniyordu -> devral'in kendi sozu ("varsayimla
        # ilk gun kirmizi seli uretmez") ihlal. Baslik yoksa ZORUNLU BOLUM DE YOKTUR;
        # eksikleri asagida devral'in KENDISI ekler.
        "zorunlu_bolumler": basliklar or [],
        "kural_evi_bolumleri": kural_evi or VARSAYILAN_RC["kural_evi_bolumleri"],
        "kural_isaretleri": isaretler,
        "arsiv_turleri": turler or VARSAYILAN_RC["arsiv_turleri"],
        "kanonik_artefakt": "",
        "politika_gerekce": politika_gerekce,
        "hafiza_dizini": hdir_rel,
        "ek_arsiv_dosyalari": sorted(ek),
    }
    y = Y(kok, rc)
    # `devral` yol tiplerini hic dogrulamiyordu (bagimsiz denetim: canli dosya DIZIN ya da
    # link dongusu -> ham IsADirectoryError/OSError).
    # SIRA ONEMLI: yol dogrulamasi kilitten ONCE kosar, cunku kilit_al()
    # os.makedirs(y.h) yapar — y.h bir dosya/kirik link ise ham FileExistsError
    # uretirdi ve bu dogrulamanin verdigi TEMIZ hukum kaybolurdu.
    yol_on_kontrol(y, dizinler=(y.h, y.gunluk, y.gunluk_ars, y.kararlar),
                   dosyalar=_korunacak_dosyalar(y, rc))
    # A-1 (PAKETLEME SONRASI IC DENETIM, v2.4.1): v2.4 `devral`a CANLI HAFIZAYA
    # yazan YENI bir yol ekledi (CAPA DEVRI blogu) ve o yolu kilit disiplininin
    # DISINDA birakti. Olculdu: kilit baskasindayken `devral` exit 0 veriyor ve
    # canli hafizayi degistiriyordu — ayni kilit altinda `not`/`muhur` duruyor.
    # Kilit .hafizarc YAZILMADAN once alinir; aksi halde yaris penceresi kalir.
    # AYRICA (A-1'in kenari): `devral` kilidini YENI ad alaninda alacagi icin
    # ESKI ad alanindaki bir yazari goremez; agactaki her kilit sayilir.
    for _k in agactaki_kilitler(kok):
        _kp = os.path.join(kok, *_k.split("/"))
        _sahip = ""
        try:
            _sahip = oku(_kp).strip()[:120]
        except SystemExit:
            pass
        oldur("BASKA BIR YAZMA ISLEMI SURUYOR (kilit: %s)\n"
              "  %s\n"
              "  Tani: %s\n"
              "  `devral` canli hafizaya YAZAR (CAPA DEVRI blogu); ayni anda iki "
              "yazma KAYIP GUNCELLEME uretir.\n"
              "  Oteki islem bittiginde yeniden dene."
              % (_k, _sahip, _kilit_tanisi(_sahip, _k)))
    kilit_al(y)
    yaz(os.path.join(kok, RC_AD), json.dumps(rc, ensure_ascii=False, indent=2) + "\n")
    os.makedirs(y.h, exist_ok=True)
    os.makedirs(y.gunluk, exist_ok=True)
    os.makedirs(y.gunluk_ars, exist_ok=True)
    os.makedirs(y.kararlar, exist_ok=True)

    print("\n=== DEVIR — yazim ===")
    if yeni_dosya:
        yaz(canli_p, SAB_CANLI.format(ad=rc["ad"], t=bugun(), tavan=tavan))
        print("  canli hafiza olusturuldu")
    else:
        yed = os.path.join(y.h, "_DEVIR_ONCESI_%s.md" % bugun())
        shutil.copyfile(canli_p, yed)
        print("  YEDEK: %s" % os.path.relpath(yed, kok))

    # ZORUNLU BOLUMLER: devral, diskte OLMAYAN bir bolumu ISTEMEZ — eksikse KENDI EKLER.
    # BAGIMSIZ DENETIM 6. TUR: hic '## ' basligi olmayan eski bir hafizada devral
    # varsayilana dusuyor ve ilk gun 7 bulgulu kirmizi sel uretiyordu; oysa devral'in
    # sozu tam tersi. Artik iskelet EKLENIR ve rc gercege uydurulur.
    L = satirlar(canli_p)
    # 'Son guncelleme' satiri H12/H14'un CIPASIDIR; yoksa iki tazelik kapisi da olcemez.
    # Bu bir ICERIK degil, ISKELET satiridir — devral eksikse ekler.
    if not any(re.search(r"Son g[uü]ncelleme:", x) for x in L):
        _ek = "> Son guncelleme: %s" % bugun()
        _i0 = 1 if (L and L[0].startswith("# ")) else 0
        L = L[:_i0] + [_ek] + L[_i0:]
        print("  'Son guncelleme' satiri EKLENDI (H12/H14 cipasi)")
    _eklenen_bolum = []
    for _b in VARSAYILAN_RC["zorunlu_bolumler"]:
        if _bolum_araligi(L, _b)[0] is None:
            L += ["", _b, ""]
            _eklenen_bolum.append(_b)
    if _eklenen_bolum or not os.path.isfile(canli_p) or "\n".join(L) != oku(canli_p):
        yaz(canli_p, "\n".join(L))
        rc["zorunlu_bolumler"] = rc["zorunlu_bolumler"] + _eklenen_bolum
        yaz(os.path.join(kok, RC_AD), json.dumps(rc, ensure_ascii=False, indent=2) + "\n")
        print("  eksik zorunlu bolum EKLENDI (%d): %s"
              % (len(_eklenen_bolum), ", ".join(b0[3:] for b0 in _eklenen_bolum[:4])))

    for p0, ilk in [(y.duzelt, '{\n  "duzeltmeler": []\n}\n'),
                    (y.yeni, ";; Beyan edilen YENI satirlar (yorum oneki \';;\')\n"),
                    (y.tasinma, ""), (y.korunan, '{\n  "bloklar": []\n}\n')]:
        if not os.path.isfile(p0):
            yaz(p0, ilk)
    if not [f for f in (os.listdir(y.h) if os.path.isdir(y.h) else [])
            if re.match(r"^HAFIZA_.*\.md$", f)]:
        _ars = ["# ARŞİV 01 (v2) — devirden sonra emekli edilen satırlar",
                "> Buraya YALNIZ `hafiza.py emekli` ve `hafiza.py derle` yazar."]
        yaz(os.path.join(y.h, "HAFIZA_01.md"), "\n".join(_ars) + "\n")
        _beyan_yeni_satirlar(y, _ars, "devir: arsiv iskeleti (arac uretti)")
    _arsiv_dizini_tazele(y)

    # CAPA DEVRI kaydi CIPADAN ONCE yazilir: boylece satir CIPAYA girer ve silinmesi
    # H1 "KAYIP" verir. Saldirgan bu satiri yok etmek icin korumaya calistigi metnin
    # KENDISINI bozmak zorunda kalir. Engelleyemedigimiz seyi GIZLENEMEZ kiliyoruz.
    if tum_izler:
        _L = satirlar(canli_p)
        _blok = ["", "<!-- capa-devri %s -->" % bugun(),
                 "> **CAPA DEVRI (%s):** bu dizinde onceki bir hafiza kurulumunun %d izi "
                 "bulundu ve YENI bir capa atildi. Yeni denetim izi bu tarihten ONCESINI "
                 "KAPSAMAZ; oncesi icin surum kontrolune bak."
                 % (bugun(), len(tum_izler)),
                 "<!-- /capa-devri -->"]
        _i0 = _bolum_araligi(_L, "## GUNCEL DURUM")[0]
        _L = (_L[:_i0] + _blok + _L[_i0:]) if _i0 is not None else (_L + _blok)
        yaz(canli_p, "\n".join(_L))
        print("  CAPA DEVRI canli hafizaya KALICI olarak yazildi (cipaya girer)")

    # CIPA: devir anindaki canli hafiza = bundan sonra KAYBOLMAYACAK taban
    shutil.copyfile(canli_p, y.snap)
    yaz(y.cipa, json.dumps({"dosya": "_KAYNAK.md", "sha": sha_dosya(y.snap),
                            "tarih": bugun(), "surum": SURUM, "devir": True},
                           ensure_ascii=False, indent=2) + "\n")
    Lsnap = satirlar(y.snap)
    yaz(y.kova, json.dumps({"satirlar": {str(i + 1): "CANLI"
                                         for i, s in enumerate(Lsnap) if anlamli(s)}},
                           ensure_ascii=False, indent=1) + "\n")
    if not os.path.isfile(y.plan):
        plan = SAB_PLAN
        if turler:
            plan += "\n## Bu projede tespit edilen seriler\n\n"
            for t0 in turler:
                n = len(os.listdir(os.path.join(ars, t0)))
                plan += "- `arsiv/%s` — %d dosya · tur kapaninca TASINIR, silinmez\n" % (t0, n)
        yaz(y.plan, plan)
    if not os.path.isfile(y.konular):
        yaz(y.konular, SAB_KONULAR)
    if not os.path.isfile(y.kural):
        yaz(y.kural, "# %s — KALICI PROTOKOL\n> Bu dosya her oturumda yüklenir.\n" % rc["ad"])
    _dnot = "ilerlemis proje devralindi (%s)" % hdir_rel
    if tum_izler:
        _dnot += (" — DIKKAT: bu dizinde ONCEKI bir kurulumun %d izi vardi; "
                  "yeni capa ONCEKI DENETIM IZINI KAPSAMAZ" % len(tum_izler))
    zincir_halka(y, "DEVIR", _dnot,
                 ek={"onceki_kurulum_izi": tum_izler[:20]} if tum_izler else None)
    print("  cipa + defterler + zincir kuruldu (%s)" % hdir_rel)

    print("\n=== DEVIR RAPORU — kapi (salt okuma) ===")
    kod, cikti = _kapi_metni(kok)
    print(cikti.strip())
    print("\n=== TRIYAJ ===")
    print("  Bu ilk kosumda KIRMIZI gormek NORMALDIR: kapilar mevcut daginikligi olcuyor.")
    print("  Sirayla:")
    print("   1. [H4] bulgular: hafiza olmayan bir dosyaya gonderiyor -> ya yolu duzelt ya satiri guncelle.")
    print("      'TASINMIS' notlari bulgu DEGILDIR (dosya arsivde bulundu).")
    print("   2. [H7] bulgular: kalici kural rotasyona giren bolumde yasiyor -> ya kurali")
    print("      SABIT CERCEVE'ye tasi, ya o bolumu .hafizarc'ta kural_evi_bolumleri'ne ekle.")
    print("   3. [H10] KONULAR.md tanimsiz: bloklara konu etiketi eklenirken sozluge de ekle.")
    print("   4. [H13] plansiz seri: SAKLAMA_PLANI.md'ye satir ekle.")
    print("  Mevcut sisteme (v1) DOKUNULMADI: eski cipa, zincir ve defterler oldugu gibi duruyor.")
    print("\n  Kapi yesillenince: python hafiza.py isir --kok=\"%s\"" % kok)
    return 0

# ---------------------------------------------------------------- korunan

def cmd_korunan(a):
    """H8: bir dosyadaki isaretli blogu KORUNAN ilan eder (hash'lenir).
    Blok bilincli degistiginde kapi KIRMIZI yanar — dogrusu budur: 'beyan et ya da kir'."""
    kok = kok_bul(a.kok); rc = rc_oku(kok); y = Y(kok, rc)
    zincir_on_kontrol(y, rc)  # yarim is birakma: bozuk zincirde ISE BASLAMA
    kilit_al(y)               # tek yazar: es zamanli derle KAYIP GUNCELLEME uretiyordu
    if not a.gerekce or len(a.gerekce.strip()) < 15:
        oldur("GEREKCESIZ KORUMA YASAK (en az 15 karakter).")
    # FABLE 3. TUR · B-3: B-2'nin OKUMA kardesi — --dosya da denetimsizdi;
    # proje disindaki bir dosya okunup dis yol _KORUNAN.json'a isleniyordu.
    p = cli_yol_coz(kok, a.dosya, "--dosya")
    if not os.path.isfile(p):
        oldur("dosya yok: " + a.dosya)
    dosya_ad = kok_goreli(kok, p)      # O-5: deftere KANONIK goreli yol yazilir
    _t = oku(p)
    if _t.count(a.bas) != 1 or _t.count(a.son) != 1:
        oldur("KORUNAN isaret cifti %s'te %d/%d kez geciyor (1/1 olmali).\n"
              "  Benzersiz olmayan isaretle koruma OLCULEMEZ: sahte bir kopya tahrifi gizler.\n"
              "  Daha benzersiz bir isaret sec (ornek: <!--KORU:PROTOKOL-BAS-->)."
              % (a.dosya, _t.count(a.bas), _t.count(a.son)))
    m = re.search(re.escape(a.bas) + r".*?" + re.escape(a.son), _t, re.S)
    if not m:
        oldur("blok bulunamadi: [%s .. %s]" % (a.bas, a.son))
    d = defter_liste(y.korunan, "bloklar", {"dosya": str, "bas": str, "son": str, "sha": str})
    d["bloklar"] = [b for b in d["bloklar"]
                    if not (kok_goreli(kok, os.path.join(kok, b["dosya"])) == dosya_ad
                            and b["bas"] == a.bas and b["son"] == a.son)]
    d["bloklar"].append({"dosya": dosya_ad, "bas": a.bas, "son": a.son,
                         "sha": sha(m.group(0)), "gerekce": a.gerekce.strip(),
                         "tarih": bugun()})
    yaz(y.korunan, json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    zincir_halka(y, "KORUNAN", a.gerekce.strip(), ek={"dosya": dosya_ad})
    print("KORUNDU: %s [%s .. %s] sha %s..." % (dosya_ad, a.bas[:20], a.son[:20], sha(m.group(0))[:16]))

# ---------------------------------------------------------------- KAPI

def cmd_kapi(a):
    """BAGIMSIZ DENETIM (ORTA-YUKSEK): rapor SONDA basildigi icin, olcumun herhangi
    bir yerindeki tek bir SystemExit (ornegin bozuk baytli TEK bir arsiv dosyasi)
    BUTUN kapilarin ciktisini yutuyordu — kullanici hangi kapinin yesil oldugunu
    goremiyordu. Artik govde ayri; ne olursa olsun O ANA KADAR TOPLANAN hukum basilir."""
    F, N, O = [], [], []          # FAIL, NOT, OLCEMIYORUM
    kesildi = None
    _KAPI_KOK[0] = ""
    try:
        _kapi_govde(a, F, N, O)
    except SystemExit as e:
        if isinstance(e.code, int) and e.code == 0:
            raise
        kesildi = (SON_HATA[0] or "olcum durdu").split("\n")[0]
        F.append("[KAPI] OLCUM YARIDA KESILDI: %s" % kesildi[:160])
        F.append("      -> Bundan SONRAKI kapilar KOSULMADI; hukumleri 'OLCULMEDI'dir.")
    print("=== HAFIZA KAPISI v%s === kok: %s" % (SURUM, _KAPI_KOK[0] or "?"))
    for n in N:
        print("  · " + n)
    for o in O:
        print("  ? " + o)
    if F:
        print("\nSONUC: FAIL (%d bulgu)" % len([x for x in F if x.startswith("[")]))
        for f in F:
            print("  " + f)
        # A-2 (PAKETLEME SONRASI IC DENETIM, v2.4.1): "olcum YARIDA KESILDI" bir
        # KAPI HUKMU DEGILDIR — kapilarin bir kismi HIC KOSMADI. Buna ragmen
        # exit 1 donuyordu, yani gercek bir kirmiziyla AYNI kod. `kapi || dur`
        # diyen bir sarmalayici "olcemedim"i "kirmizi" saniyordu; belgede ise
        # "3 = olcum yapilamadi" YAZIYORDU. Soz koda uydurulmadi, KOD SOZE
        # UYDURULDU (Onur'un karari).
        #   Gercek bir kapi bulgusu VARSA 1 doner: olculmus bir kirmizi,
        #   eksik kapsamdan daha acildir ve sarmalayici onu gormek zorundadir.
        #   Bulgunun TAMAMI kesilmeden ibaretse 3 doner: hukum YOK.
        if kesildi and not [x for x in F if x.startswith("[") and not x.startswith("[KAPI]")]:
            print("  -> HUKUM YOK: olcum tamamlanamadi (cikis kodu 3).")
            return 3
        return 1
    if O:
        print("\nSONUC: YESIL (SINIRLI) — olculen her sey gecti, ama %d SEY OLCULMEDI "
              "(yukarida '?' ile isaretli). Kapsam TAM DEGILDIR." % len(O))
    else:
        print("\nSONUC: YESIL — olculen her sey gecti.")
    return 0

_KAPI_KOK = [""]

def _kapi_govde(a, F, N, O):
    kok = kok_bul(a.kok); _KAPI_KOK[0] = kok
    rc = rc_oku(kok); y = Y(kok, rc)
    fail = lambda k, m: F.append("[%s] %s" % (k, m))
    siki = bool(a.siki)
    _cokad = yol_on_kontrol(y, dizinler=(y.h,), dosyalar=_korunacak_dosyalar(y, rc),
                            sessiz=True)
    if _cokad:
        fail("H-LINK", "%d dosyanin proje DISINDA da bir adi var (hardlink) — bu dosyalara "
                       "yazmak oradaki adi da degistirir; denetim izi disari sizabilir:" % len(_cokad))
        for _p0 in _cokad[:5]:
            F.append("      - " + os.path.relpath(_p0, kok).replace("\\", "/"))
        F.append("      -> Yedek amacliysa: 'cp -al' yerine 'cp -a' kullan (bagimsiz kopya).")
    if not os.path.isdir(y.h):
        fail("H6", "HAFIZA DIZINI YOK: %s — arsiv tabani kayip." % y.h)
        return

    if not os.path.isfile(y.canli):
        fail("H-", "CANLI HAFIZA YOK: %s — hicbir kapi olculemez." % y.canli)
        return

    # ---- H0 CIPA -------------------------------------------------------
    if not os.path.isfile(y.snap) or not os.path.isfile(y.cipa):
        fail("H0", "_KAYNAK.md / _CIPA.json yok — kanit tabani kayip")
    else:
        c = defter_yukle(y.cipa, {})
        s = sha_dosya(y.snap)
        if s != c.get("sha"):
            fail("H0", "CIPA BOZULDU: _KAYNAK.md SHA %s… != _CIPA.json %s…"
                 % (s[:16], str(c.get("sha"))[:16]))
            F.append("      -> Snapshot KANIT TABANIDIR; degisirse H1 olcumu ANLAMSIZDIR.")
        for h in zincir_dogrula(y):
            if h.startswith("~"):
                O.append("H0: " + h[1:])      # kanit YETERSIZ — hukum degil, isaret
            else:
                fail("H0", h)
        _zh = [x for x in zincir_dogrula(y) if not x.startswith("~")]
        N.append("H0: cipa %s · zincir %s" % ("saglam" if s == c.get("sha") else "BOZUK",
                 "saglam" if not _zh else "KIRIK"))

    # ---- H1 BUTUNLUK + KOVA --------------------------------------------
    if os.path.isfile(y.snap):
        snapL = satirlar(y.snap)
        if snapL and snapL[-1] == "":
            snapL.pop()
        bekle = cok_kume([norm(s) for s in _uretilen_haric(snapL) if anlamli(s)])
        snap0 = dict(bekle)
        duz = defter_liste(y.duzelt, "duzeltmeler", {"satir": (int, str), "eski": str, "yeni": str})["duzeltmeler"]
        for d in duz:
            e, n = norm(d["eski"]), norm(d["yeni"])
            if not ck_sil(bekle, e):
                fail("H1", "beyan edilen DUZELTME kaynagi snapshot'ta YOK (satir %s) — sahte duzeltme" % d["satir"])
            ck_ekle(bekle, n)
            if len(str(d.get("gerekce", ""))) < 10:
                fail("H1", "duzeltme %s GEREKCESIZ" % d["satir"])
        yeniler = []
        if os.path.isfile(y.yeni):
            yeniler = [norm(s) for s in satirlar(y.yeni) if s.strip() and not s.startswith(";;")]
        for s in yeniler:
            if s in snap0:
                fail("H1", "'YENI' diye beyan edilen satir snapshot'ta ZATEN VAR (kayip maskeleme suphesi): " + s[:70])
            ck_ekle(bekle, s)

        canliA = icerik_satirlari(y.canli)
        arsivP = arsiv_dosyalari(kok, y, rc)
        # Tek bozuk arsiv dosyasi H1'i dusurur ama DIGER kapilari dusurmemeli;
        # ustelik "hangi dosya" bilgisi kullaniciya lazim.
        arsivA, arsiv_okunamayan = [], []
        for p0 in arsivP:
            tamam, sat = kapi_yalit(O, "H1 (%s)" % os.path.relpath(p0, kok).replace("\\", "/"),
                                    anlamli_satirlar, p0)
            if tamam:
                arsivA.extend(sat)
            else:
                arsiv_okunamayan.append(os.path.relpath(p0, kok).replace("\\", "/"))
        if arsiv_okunamayan:
            fail("H1", "%d arsiv dosyasi OKUNAMADI — bu dosyalardaki satirlar 'KAYIP' "
                       "gorunebilir; once dosyalari duzelt: %s"
                 % (len(arsiv_okunamayan), ", ".join(arsiv_okunamayan[:3])))
        var = cok_kume(canliA + arsivA)
        eksik = ck_fark(bekle, var)
        fazla = ck_fark(var, bekle)
        if eksik:
            fail("H1", "%d satir KAYIP (snapshot'ta var, hicbir ciktida yok):" % len(eksik))
            for s in eksik[:5]:
                F.append("      - KAYIP: " + s[:100])
            if len(eksik) > 5:
                F.append("      … +%d satir daha" % (len(eksik) - 5))
        if fazla and siki:
            # IC DENETIM (B-4): `_canli_ekle_beyan` snapshot'ta ZATEN gecen satirlari
            # (kayip-maskeleme korumasi geregi) _YENI_SATIRLAR.txt'ye yazmaz; ama
            # `<!-- /blok -->` gibi YAPISAL satirlar her sablonda gectigi icin aracin
            # KENDI yazdigi her kapanis ebediyen "beyansiz" gorunuyordu. Sonuc: --siki
            # daha ILK `kur`dan itibaren kirmizi ve gercek bir enjeksiyon 58 sahte
            # pozitifin altinda KAYBOLUYORDU. Kova'ya BEYAN EDILMIS satirlar (ek_canli)
            # burada da dusulur — beyan beyandir, hangi deftere yazildigi onemli degil.
            _beyanli = cok_kume([norm(x) for x in
                                 (defter_yukle(y.kova, {"satirlar": {}}).get("ek_canli") or [])])
            fazla = ck_fark(cok_kume(fazla), _beyanli)
        if fazla and siki:
            fail("H1", "%d satir BEYANSIZ EKLENMIS (--siki):" % len(fazla))
            for s in fazla[:5]:
                F.append("      - FAZLA: " + s[:100])
            if len(fazla) > 5:
                # "SESSIZ KIRPMA YOK" ilkesi: eksik listesinde vardi, fazla'da YOKTU.
                F.append("      … +%d satir daha" % (len(fazla) - 5))
        elif fazla:
            N.append("H1: +%d yeni satir (mesru buyume; KAYIP yok)" % len(fazla))

        # KOVA — yerlesim korlugu
        if not os.path.isfile(y.kova):
            fail("H1-KOVA", "_KOVA.json YOK — yerlesim olculemiyor")
        else:
            kv = defter_yukle(y.kova, {"satirlar": {}})
            if not isinstance(kv.get("satirlar"), dict):
                if "satirlar" in kv:
                    defter_hata("_KOVA.json", "'satirlar' bir nesne olmali, %s bulundu."
                                % type(kv.get("satirlar")).__name__)
                kv["satirlar"] = {}
            metin_listesi(kv.get("ek_canli", []), "_KOVA.json", "ek_canli")
            L = list(snapL)
            for d in duz:
                i = tamsayi(d["satir"], "_DUZELTMELER.json > satir") - 1
                if 0 <= i < len(L) and norm(L[i]) == norm(d["eski"]):
                    L[i] = norm(d["yeni"])
            uretilen = set(_ur.strip() for _ur in [V2BAS, V2SON])
            ic_uretilen, uretilen_idx = False, set()
            for _i, _s in enumerate(L):
                _d = _s.strip()
                if _d == V2BAS:
                    ic_uretilen = True; uretilen_idx.add(_i); continue
                if _d == V2SON:
                    ic_uretilen = False; uretilen_idx.add(_i); continue
                if ic_uretilen:
                    uretilen_idx.add(_i)
            bek = list(kv.get("ek_canli", []))     # baseline-SONRASI beyan edilmis canli satirlar
            for i, k in kv["satirlar"].items():
                idx = tamsayi(i, "_KOVA.json > satirlar anahtari") - 1
                if idx in uretilen_idx:
                    continue
                if 0 <= idx < len(L) and str(k).startswith("CANLI") and anlamli(L[idx]):
                    bek.append(norm(L[idx]))
            bekC = cok_kume(bek)
            tasKayit = jsonl_yukle(y.tasinma, ["satirlar"])
            for r in tasKayit:
                metin_listesi(r.get("satirlar"), "_TASINMA.jsonl", "satirlar")
                if "hedef" in r and not isinstance(r["hedef"], str):
                    defter_hata("_TASINMA.jsonl", "'hedef' metin olmali, %s bulundu."
                                % type(r["hedef"]).__name__)
                for s in r.get("satirlar", []):
                    ck_sil(bekC, norm(s))
            kacan = ck_fark(bekC, cok_kume(canliA))
            if kacan:
                fail("H1-KOVA", "%d satir CANLIDA OLMALIYDI, YOK — BEYANSIZ TASINMA:" % len(kacan))
                for s in kacan[:5]:
                    F.append("      - CANLIDAN KACMIS: " + s[:100])
                F.append("      -> Tasimayi ARACLA yap: hafiza.py emekli <bas>-<son> --not \"...\"")
            for r in tasKayit:
                hp = os.path.join(y.h, r.get("hedef", ""))
                hMS = cok_kume(anlamli_satirlar(hp)) if os.path.isfile(hp) else {}
                yok = [s for s in r.get("satirlar", []) if norm(s) not in hMS]
                if yok:
                    fail("H1-KOVA", "beyan edilen tasima HEDEFTE YOK (%s): %d satir — sahte beyan"
                         % (r.get("hedef"), len(yok)))

    # ---- H2 SISME ------------------------------------------------------
    bayt = os.path.getsize(y.canli)
    tavan = rc["tavan_kb"] * 1024
    if bayt > tavan:
        fail("H2", "canli hafiza SISTI: %.1f KB > %d KB tavan — emekli et (hafiza.py emekli)"
             % (bayt / 1024.0, rc["tavan_kb"]))
    else:
        N.append("H2: %.1f / %d KB (%%%d dolu)" % (bayt / 1024.0, rc["tavan_kb"],
                                                   round(100.0 * bayt / tavan)))

    # ---- H3 BOLUM ------------------------------------------------------
    basliklar = [s for s in satirlar(y.canli) if s.startswith("#")]
    for b in rc["zorunlu_bolumler"]:
        if not any(bas_eslesir(x, b) for x in basliklar):
            fail("H3", "zorunlu bolum YOK: " + b)

    # ---- H4 OLU BAGLANTI -----------------------------------------------
    metin = oku(y.canli)
    # Yalniz TAM backtick icerigi bir yol ise aday sayilir: `hafiza.py kapi` bir KOMUTTUR, yol degil.
    aday = set()
    for ic in re.findall(r"`([^`\n]+)`", metin):
        ic = ic.strip()
        # Fable Bulgu 4: regex ASCII'ydi -> `belgeler/musteri.md` gibi TURKCE adli olu
        # baglantilar SESSIZCE atlaniyordu. Uzanti siniri da 6'ydi -> .keystore/.properties kaciyordu.
        if " " in ic or not re.fullmatch(r"[\w./\\-]+\.[A-Za-z0-9]{1,10}", ic, re.UNICODE):
            continue
        # UZANTI BEYAZ LISTESI: `location.href`, `path.join`, `q.token` KOD IFADESIDIR, yol degil.
        # (Alt-dizge/uzanti sezgisi bunlari yol saniyordu — gercek bir hafiza dosyasinda olculdu.)
        if ic.rsplit(".", 1)[-1].lower() not in DOSYA_UZANTILARI:
            continue
        # Yer tutucular yol degildir: GOREV_..._vX.md, KANIT_vN.md, <dosya>.md, NNNN-....md
        if re.search(r"(?:^|[^A-Za-z])v[XN](?:[^0-9]|$)|[<>*]|NNNN|YYYY|AAAA", ic):
            continue
        aday.add(ic.replace("\\", "/"))
    for ic in re.findall(r"\]\(([^)\s]+\.[A-Za-z0-9]{1,10})\)", metin):
        if not ic.startswith(("http://", "https://", "mailto:", "#")):
            aday.add(ic)
    eksik = [p for p in sorted(aday) if not os.path.exists(os.path.join(kok, p))]
    if eksik:
        # Tasinmis mi, yok mu? Ayni ADLA baska bir yerde duruyorsa bu OLU DEGIL, TASINMISTIR.
        havuz = {}
        for r0, d0, f0 in os.walk(kok):
            d0[:] = [d for d in d0 if d not in (".git", "node_modules", "__pycache__", ".venv")]
            for f in f0:
                havuz.setdefault(f, []).append(os.path.relpath(os.path.join(r0, f), kok).replace("\\", "/"))
        # SESSIZ KIRPMA YOK: hepsi siniflandirilir; ekranda kirpilan sayi ACIKCA yazilir.
        # (Eski surum eksik[:20] ile ilk 20'ye bakiyordu ve alfabetik siralama yuzunden
        #  gercek bir olu baglantiyi KACIRDI — bizzat mutant turunda olculdu.)
        # Fable Bulgu 7: yalniz basename eslesmesi "tasinmis" saymak, README.md/config.json
        # gibi yaygin adlarda kapiyi silahsizlandiriyordu. Artik BAGLAM araniyor:
        # ya arsiv altinda, ya da beyan edilen yolun bir dizin bileseni tutuyor.
        olu, tasinmis = [], []
        for p0 in eksik:
            adaylar = havuz.get(os.path.basename(p0)) or []
            beyan_dizin = set(x for x in os.path.dirname(p0).split("/") if x)
            iyi = None
            for c0 in adaylar:
                c_dizin = set(x for x in os.path.dirname(c0).split("/") if x)
                if c_dizin & {"arsiv", "archive"} or (beyan_dizin and beyan_dizin & c_dizin):
                    iyi = c0; break
            if iyi:
                tasinmis.append((p0, iyi))
            elif adaylar:
                olu.append((p0, "ayni adli baska dosya var ama yol tutmuyor: " + adaylar[0]))
            else:
                olu.append((p0, None))
        for p0, yer in tasinmis[:5]:
            N.append("H4: TASINMIS (olu degil): '%s' -> %s" % (p0, yer))
        if len(tasinmis) > 5:
            N.append("H4: … +%d tasinmis dosya daha (bulgu degil)" % (len(tasinmis) - 5))
        for p0, aciklama in olu[:10]:
            fail("H4", "OLU BAGLANTI: %s%s" % (p0, (" — " + aciklama) if aciklama else
                                               " (hicbir yerde yok)"))
        if len(olu) > 10:
            fail("H4", "… +%d OLU BAGLANTI daha (ekranda kirpildi, HEPSI sayildi)" % (len(olu) - 10))

    # ---- H5 SURUM TEKILLIGI --------------------------------------------
    ka = rc.get("kanonik_artefakt", "")
    if ka:
        try:
            re.compile(ka)
        except re.error as e:
            fail("H5", "kanonik_artefakt GECERSIZ regex (%s): %s" % (e, ka))
            ka = ""
    if ka:
        i, j = _bolum_araligi(satirlar(y.canli), "## KARAR GUNLUGU")
        L = satirlar(y.canli)
        disi = [(n + 1, s) for n, s in enumerate(L)
                if re.search(ka, s) and not (i is not None and i <= n < j)]
        adlar = set(m.group(0) for _, s in disi for m in re.finditer(ka, s))
        if len(adlar) > 1:
            fail("H5", "SURUM TEKILLIGI KIRIK — karar gunlugu disinda %d farkli artefakt: %s"
                 % (len(adlar), ", ".join(sorted(adlar))))
        elif not adlar:
            # BAGIMSIZ DENETIM 6. TUR: desen GLOB yazilirsa ('prototip_v*.html') gecerli
            # bir regex oldugu icin hata VERMEZ, hicbir seye uymaz ve H5 tek satir bile
            # basmadigi icin kapinin FIILEN KAPALI oldugu HICBIR YERDEN anlasilmazdi.
            # "Olctum ve gecti" ile "hicbir seye bakmadim" ayirt edilebilmeli.
            O.append("H5: kanonik_artefakt HICBIR SEYE UYMUYOR (%s) — surum tekilligi "
                     "FIILEN OLCULMUYOR. Glob mu yazdiniz? Bu alan REGEX'tir "
                     "(ornek: prototip_v[0-9.]+[.]html)." % ka)
        else:
            N.append("H5: %d artefakt esleşmesi · tek surum (%s)"
                     % (len(disi), list(adlar)[0][:40]))
    else:
        N.append("H5: kanonik_artefakt tanimsiz — uygulanmadi")

    # ---- H6 DIZIN ------------------------------------------------------
    arsivD = sorted(f for f in os.listdir(y.h) if re.match(r"^HAFIZA_.*\.md$", f))
    L6 = satirlar(y.canli)
    i, j = _bolum_araligi(L6, "## ARSIV DIZINI")
    if i is None:
        fail("H6", "ARSIV DIZINI bolumu yok")
    else:
        try:
            b6 = next(k for k in range(i, j) if L6[k].strip() == V2BAS)
            e6 = next(k for k in range(b6, j) if L6[k].strip() == V2SON)
            blok = "\n".join(L6[b6:e6 + 1])
        except StopIteration:
            blok = "\n".join(L6[i:j])
        for f in arsivD:
            if f not in blok:
                fail("H6", "arsiv dosyasi DIZINDE YOK: " + f)
        for f in re.findall(r"HAFIZA_[A-Za-z0-9._+-]+\.md", blok):
            if f not in arsivD:
                fail("H6", "DIZINDE var ama diskte YOK: " + f)

    # ---- H7 KURAL-YERLESIMI --------------------------------------------
    L = satirlar(y.canli)
    evler = []
    for b in rc["kural_evi_bolumleri"]:
        a1, a2 = _bolum_araligi(L, b)
        if a1 is not None:
            evler.append((a1, a2))
    # B-6: desenler BIR KEZ derlenir (satir basina degil) ve dongude yeniden kullanilir.
    _desenler = kural_desenleri(rc["kural_isaretleri"])
    for n, s in enumerate(L):
        if not anlamli(s) or s.lstrip().startswith("#"):
            continue          # BASLIK bir kural degildir ("## KIRMIZI ÇİZGİLER" kendini tetiklemesin)
        # TEK TANIM: emekli / derle / H7 ayni tarayiciyi kullanir. Ayrisirlarsa
        # "bir yerde korunan, baska yerde korunmayan kural" doguyor (denetimde olculdu).
        if kural_isareti_var(s, rc["kural_isaretleri"], _desenler):
            if not any(a1 <= n < a2 for a1, a2 in evler):
                fail("H7", "KALICI KURAL yanlis evde (satir %d) — rotasyona girer, gorunmez olur:\n"
                           "      %s" % (n + 1, s.strip()[:100]))

    # ---- H8 KORUNAN ----------------------------------------------------
    if os.path.isfile(y.korunan):
        kor = defter_liste(y.korunan, "bloklar", {"dosya": str, "bas": str, "son": str, "sha": str})["bloklar"]
        for b in kor:
            p = os.path.join(kok, b["dosya"])
            if not os.path.isfile(p):
                fail("H8", "KORUNAN dosya yok: " + b["dosya"]); continue
            tamam, t = kapi_yalit(O, "H8 (%s)" % b["dosya"], oku, p)
            if not tamam:
                fail("H8", "KORUNAN dosya OKUNAMADI: " + b["dosya"]); continue
            # BAGIMSIZ DENETIM 5. TUR (YUKSEK): olcum ILK eslesmeyi aliyordu. Korunan
            # blogu TAHRIF edip dosyanin BASINA bozulmamis bir KOPYA koymak H8'i
            # tamamen atlatiyordu (olculdu: tahrif edilmis kural dosyada dururken kapi
            # YESILDI). Kural evi dosyasi H1 kapsaminda olmadigi icin baska hicbir kapi
            # da gormuyordu. Isaret cifti BIR KEZ gecmelidir; birden coksa olcum BELIRSIZDIR.
            n_bas, n_son = t.count(b["bas"]), t.count(b["son"])
            if n_bas != 1 or n_son != 1:
                fail("H8", "KORUNAN isaret cifti %s'te %d/%d KEZ geciyor (1/1 olmali) — "
                           "olcum BELIRSIZ; sahte kopya ile blok tahrifi gizlenebilir."
                     % (b["dosya"], n_bas, n_son))
                continue
            m = re.search(re.escape(b["bas"]) + r".*?" + re.escape(b["son"]), t, re.S)
            if not m:
                fail("H8", "KORUNAN blok bulunamadi: %s [%s..%s]" % (b["dosya"], b["bas"][:24], b["son"][:24]))
            elif sha(m.group(0)) != b["sha"]:
                fail("H8", "KORUNAN blok DEGISMIS (beyansiz): %s — bilincliyse: hafiza.py muhur" % b["dosya"])
        N.append("H8: %d korunan blok" % len(kor))

    # ---- H9 GERCEK (git) -----------------------------------------------
    if shutil.which("git") and os.path.isdir(os.path.join(kok, ".git")):
        r = subprocess.run(["git", "-C", kok, "log", "--oneline", "-1"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode == 0:
            r2 = subprocess.run(["git", "-C", kok, "status", "--porcelain"],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
            kirli = len([x for x in (r2.stdout or "").split("\n") if x.strip()])
            # Izlenmeyen bir zincir/cipa GERCEK tarih degildir — git'in disinda kalmis demektir.
            izlenmeli = [os.path.relpath(y.zincir, kok).replace("\\", "/"),
                         os.path.relpath(y.snap, kok).replace("\\", "/"),
                         os.path.relpath(y.canli, kok).replace("\\", "/")]
            for rel in izlenmeli:
                r3 = subprocess.run(["git", "-C", kok, "ls-files", "--error-unmatch", rel],
                                    capture_output=True, text=True)
                if r3.returncode != 0:
                    fail("H9", "git'te IZLENMIYOR: %s — icerik-adresli tarih yok "
                               "(.gitignore'a mi takildi?)" % rel)
            N.append("H9: git var · son commit %s · calisma agacinda %d degisiklik"
                     % ((r.stdout or "").strip()[:40], kirli))
        else:
            # PAKETLEME DOGRULAMASI (v2.4.0, B listesinde YOKTU): `git log` HENUZ COMMIT
            # OLMAYAN bir depoda da sifirdan farkli doner. Eski mesaj bu hali "depo
            # okunamadi" diye rapor ediyordu — YANLIS TESHIS: depo pekala okunuyor,
            # yalnizca tarihi bos. Kullaniciyi olmayan bir izin/bozulma sorununu
            # aramaya yolluyordu. HUKUM DEGISMEDI (ikisi de OLCULEMEDI); yalniz
            # sebep dogru yaziliyor.
            _rg = subprocess.run(["git", "-C", kok, "rev-parse", "--git-dir"],
                                 capture_output=True, text=True,
                                 encoding="utf-8", errors="replace")
            if _rg.returncode == 0:
                O.append("H9: git deposu var ama HENUZ COMMIT YOK — izlenirlik "
                         "OLCULEMEDI (ilk commit'ten sonra olculur)")
            else:
                _sb = (r.stderr or _rg.stderr or "").strip().split("\n")[0][:120]
                O.append("H9: git deposu OKUNAMADI%s" % ((": " + _sb) if _sb else ""))
    else:
        O.append("H9: git YOK — icerik-adresli tarih OLCULEMIYOR (sessiz PASS verilmedi)")

    # ---- H10 KONU TEKILLIGI (anahtar bazli sikistirma) -----------------
    bl = canli_bloklar(y)
    say = {}
    for _, _, oz in bl:
        k = oz.get("konu", "?")
        say[k] = say.get(k, 0) + 1
    for k, n in sorted(say.items()):
        if n > 1:
            fail("H10", "KONU TEKILLIGI KIRIK: '%s' icin canlida %d blok var — "
                        "eskisini emekli et (her anahtar icin SON deger tutulur)" % (k, n))
    # Fable Bulgu 6: kapanmamis/ic-ice blok sayilmiyordu -> ayni konuda birikme SESSIZ kaliyordu.
    _ham = satirlar(y.canli)
    if kod_citi_dengesiz(_ham):
        fail("H10", "KAPANMAMIS KOD CITI — kod bolgesi dosyanin sonuna kadar uzuyor ve "
                    "icindeki BUTUN bloklar olcum disi kaliyor. Citi kapat.")
    # SESSIZ GIZLEME YASAK: cit dengeli olsa bile kod bolgesi gercek blok satirlarini
    # yutabilir (denetimde olculdu). Gizlenen her satir RAPORLANIR.
    _girintili = girintili_isaretler(_ham)
    if _girintili:
        fail("H10", "%d GIRINTILI blok isareti var — blok isareti SUTUN 0'da olmali; "
                    "girintili isaret hicbir olcume girmez (sessiz cift blok riski):"
             % len(_girintili))
        for _n0, _s0 in _girintili[:5]:
            F.append("      - satir %d: %s" % (_n0, _s0))
        F.append("      -> Yeni yazilan satirda: girintiyi kaldir (isareti sola daya).")
        F.append("      -> Devralinmis (cipa'daki) satirda ELLE DOKUNMA (H1 'KAYIP' der):")
        F.append("         python hafiza.py emekli <bas>-<son> --not \"eski blok arsive tasindi\"")
    _gizli = gizli_blok_satirlari(_ham)
    _cakisan = gizli_konu_cakismasi(_ham)
    if _cakisan:
        # TEHLIKELI hal: gizlenen blogun konusu CANLIDA da var -> konu tekilligi
        # sessizce delinmis olur (1. tur bulgusu tam olarak buydu).
        fail("H10", "%d gizli blok, CANLIDAKI bir blokla AYNI KONUYU tasiyor — konu "
                    "tekilligi SESSIZCE delinmis olur:" % len(_cakisan))
        for _n0, _k0 in _cakisan[:5]:
            F.append("      - satir %d: konu '%s' hem gizli hem canli" % (_n0, _k0))
        F.append("      -> Citi duzelt ya da ornegin konu adini degistir.")
    elif _gizli:
        # Konu cakismasi YOKSA: ya belge ornegi, ya tek basina gizlenmis bir blok.
        # Ikisi de VERI KAYBI degildir (H1 satirlari zaten sayar) ve ISI DURDURMAZ —
        # durdurmak, hafiza dosyasinin kendi bicimini belgelemesini yasaklardi.
        # Ama "olcume girmiyor" bir NOT degil, OLCEMIYORUM hukmudur: hukum satirinda
        # gorunmeli, yoksa "olculen her sey gecti" cumlesi kapsami abartir.
        O.append("H10: %d blok satiri KOD BOLGESINDE — o bloklar OLCULMEDI "
                 "(belge ornegi ise sorun yok; degilse citi duzelt): satir %s"
                 % (len(_gizli), ", ".join(str(g[0]) for g in _gizli[:5])))
    acik, hatali, asilan = None, [], None
    for _n, _s in enumerate(kod_disi(_ham), 1):
        if _s.startswith("## ") and acik is not None and asilan is None:
            asilan = (acik, _n, _s.strip()[:40])
        if BLOK_BAS.search(_s):
            if acik is not None:
                hatali.append("satir %d: onceki blok (satir %d) KAPANMADAN yeni blok aciliyor"
                              % (_n, acik))
            acik = _n; asilan = None
        elif BLOK_SON.search(_s):
            if acik is None:
                hatali.append("satir %d: acilmamis blok KAPATILIYOR" % _n)
            elif asilan:
                # BAGIMSIZ DENETIM (YUKSEK): kapanissiz bir blok + ILERIDEKI oksuz bir
                # kapanis, aradaki BOLUMLERI (KIRMIZI CIZGILER dahil) tek blok gosteriyordu;
                # `derle` hepsini arsive tasiyordu ve kapi ONCEDEN YESILDI. Blok bir
                # BASLIK sinirini asamaz — asiyorsa yapı bozuktur.
                hatali.append("satir %d: blok (satir %d) '%s' BASLIGINI asiyor — "
                              "kapanis isareti baskasina ait" % (_n, asilan[0], asilan[2]))
            acik = None; asilan = None
    if acik is not None:
        hatali.append("satir %d: blok ACIK KALDI (kapanis isareti yok)" % acik)
    for h0 in hatali[:5]:
        fail("H10", "BOZUK BLOK YAPISI — %s" % h0)
    N.append("H10: %d blok / %d ayrik konu" % (len(bl), len(say)))
    if os.path.isfile(y.konular):
        bilinen = set(re.findall(r"^\|\s*([a-z0-9-]+)\s*\|", oku(y.konular), re.M))
        bilinen -= {"konu"}
        bilinen = {b for b in bilinen if set(b) != {"-"}}
        for k in say:
            if k not in bilinen:
                fail("H10", "KONULAR.md'de tanimsiz konu: '%s' (once sozluge ekle)" % k)

    # ---- H11 KARAR BUTUNLUGU (ADR) -------------------------------------
    ks = adr_listesi(y)
    if ks:
        nolar = [k["no"] for k in ks]
        if len(set(nolar)) != len(nolar):
            fail("H11", "ADR numarasi TEKRAR ediyor — numara asla yeniden kullanilmaz")
        for beklenen, k in zip(range(1, len(ks) + 1), sorted(ks, key=lambda x: x["no"])):
            if k["no"] != beklenen:
                fail("H11", "ADR numara BOSLUGU: %04d bekleniyordu, %04d bulundu" % (beklenen, k["no"]))
                break
        harita = {k["no"]: k for k in ks}
        for k in ks:
            m = k["meta"]
            yg = m.get("yerine-gecen", "-")
            ya = m.get("yerini-aldigi", "-")
            # Y-3: ADR on-bilgisi ELLE yazilir; 'yerine-gecen: abc' ham ValueError veriyordu.
            # Burasi bir KAPI; cokmek yerine BULGU vermeli.
            if yg not in ("-", "", None):
                if not str(yg).strip().isdigit():
                    fail("H11", "%s: yerine-gecen SAYI DEGIL ('%s') — karar numarasi bekleniyor"
                         % (k["dosya"], yg))
                else:
                    t = harita.get(int(str(yg).strip()))
                    if not t:
                        fail("H11", "%s: yerine-gecen %s yok" % (k["dosya"], yg))
                    elif t["meta"].get("yerini-aldigi") != "%04d" % k["no"]:
                        fail("H11", "%s <-> %s: yerine-gecme baglantisi TEK YONLU" % (k["dosya"], t["dosya"]))
                    if m.get("durum") != "yerine-gecildi":
                        fail("H11", "%s: yerine-gecen dolu ama durum '%s'" % (k["dosya"], m.get("durum")))
            if ya not in ("-", "", None):
                if not str(ya).strip().isdigit():
                    fail("H11", "%s: yerini-aldigi SAYI DEGIL ('%s')" % (k["dosya"], ya))
                elif int(str(ya).strip()) not in harita:
                    fail("H11", "%s: yerini-aldigi %s yok" % (k["dosya"], ya))
            if m.get("durum") == "kabul" and len(k["govde"]) < 200:
                fail("H11", "%s: durum 'kabul' ama govde neredeyse bos (bedeller/alternatifler yazilmamis)" % k["dosya"])
        for m in re.findall(r"kararlar/(\d{4})-[a-z0-9-]+\.md", oku(y.canli)):
            t = harita.get(int(m))
            if not t:
                fail("H11", "canli hafiza olmayan bir karara link veriyor: %s" % m)
            elif t["meta"].get("durum") == "yerine-gecildi":
                fail("H11", "canli hafiza YERINE GECILMIS karara link veriyor: %s (guncelini yaz)" % m)
        N.append("H11: %d karar · %d kabul" % (len(ks), sum(1 for k in ks if k["meta"].get("durum") == "kabul")))
    else:
        N.append("H11: henuz karar dosyasi yok")

    # ---- H12 BAYATLIK --------------------------------------------------
    gun = rc["bayatlik_gun"]
    m = re.search(r"Son g[uü]ncelleme:\s*(.{0,40})", oku(y.canli))
    t_son = tarih_coz(m.group(1)) if m else None
    if t_son and t_son > _dt.date.today():
        fail("H12", "'Son guncelleme' GELECEKTE (%s) — gecersiz. Saat kaymasi ya da yazim hatasi; "
                    "bu hal iki tazelik kapisini birden susturur." % t_son.isoformat())
        t_son = None
    if t_son:
        d = (_dt.date.today() - t_son).days
        if d > gun:
            fail("H12", "canli hafiza %d gundur guncellenmemis (tavan %d gun)" % (d, gun))
        else:
            N.append("H12: son guncelleme %d gun once (%s)" % (d, t_son.isoformat()))
    elif m:
        O.append("H12: 'Son guncelleme' satiri var ama tarih COZULEMEDI (%r) — bayatlik OLCULEMIYOR"
                 % m.group(1).strip()[:30])
    else:
        fail("H12", "'Son guncelleme: ...' satiri yok — bayatlik olculemiyor")
    # sapma: bir konuda canli bloktan DAHA YENI fragman/karar var mi?
    en_yeni = {}
    for d0 in (y.gunluk, y.gunluk_ars):
        if os.path.isdir(d0):
            for f in os.listdir(d0):
                if f.endswith(".md"):
                    meta, _ = fragman_coz(os.path.join(d0, f))
                    if meta and meta.get("konu"):
                        k = slug(meta["konu"]); t = meta.get("tarih", "")
                        if t > en_yeni.get(k, ""):
                            en_yeni[k] = t
    for k in ks:
        kk = slug(k["meta"].get("konu", "")); t = k["meta"].get("tarih", "")
        if kk and t > en_yeni.get(kk, ""):
            en_yeni[kk] = t
    for _, _, oz in bl:
        k, g = oz.get("konu", "?"), oz.get("guncel", "")
        if k in en_yeni and en_yeni[k] > g:
            fail("H12", "CANLI BAYAT: '%s' blogu %s tarihli ama o konuda %s tarihli daha yeni "
                        "kayit var — derle (hafiza.py derle)" % (k, g or "?", en_yeni[k]))
    if os.path.isdir(y.gunluk):
        bekleyen = [f for f in os.listdir(y.gunluk) if f.endswith(".md")]
        if bekleyen:
            N.append("H12: %d fragman DERLENMEYI bekliyor" % len(bekleyen))

    # ---- H13 SAKLAMA PLANI ---------------------------------------------
    if not os.path.isfile(y.plan):
        fail("H13", "SAKLAMA_PLANI.md yok — emeklilik karari yaziya dokulmemis")
    else:
        pt = oku(y.plan)
        seriler = re.findall(r"^\|\s*([^|]+?)\s*\|", pt, re.M)
        seriler = [s for s in seriler if s and not set(s) <= set("-: ") and s.lower() != "seri"]
        if len(seriler) < 3:
            fail("H13", "SAKLAMA_PLANI.md'de anlamli seri yok (en az 3 bekleniyor)")
        else:
            N.append("H13: %d seri tanimli" % len(seriler))
        for t in rc["arsiv_turleri"]:
            d0 = os.path.join(kok, "arsiv", t)
            if os.path.isdir(d0) and os.listdir(d0):
                if not re.search(r"(?<![a-z0-9_])" + re.escape(t.lower()) + r"(?![a-z0-9_])",
                                 pt.lower()):
                    fail("H13", "PLANSIZ SERI: 'arsiv/%s' dolu ama SAKLAMA_PLANI'nda gecmiyor" % t)


    # ---- H15 POLITIKA (kapilarin kendisi gevsetildi mi) -----------------
    # BAGIMSIZ DENETIM DERSI: H15'in mesaji "bilincliyse gerekce yaz ve muhurle" diyordu
    # ama gerekceyi OKUYAN kod YOKTU -> yerine getirilemeyen talimat + kalici kirmizi
    # kilit (buyuk bir dosyayi `devral` eden proje disari cikamiyordu). Artik gerekce
    # GERCEKTEN okunur; ama gerekce zincire girdigi icin (politika:.hafizarc) BEYANSIZ
    # yazilamaz — muhursuz degistirilirse H0 yakalar. Yani gevseklik gizlenemez, ITIRAF EDILIR.
    pg = rc.get("politika_gerekce") or {}
    def _politika(anahtar, kosul, mesaj):
        if not kosul:
            return
        gerekce = str(pg.get(anahtar, "")).strip()
        if len(gerekce) >= 15:
            # BAGIMSIZ DENETIM: beyanli gevseklik NOT'a yazilinca nihai hukum
            # "YESIL — olculen her sey gecti" diyordu; oysa o kapi ARTIK OLCMUYOR.
            # Aracin kendi ilkesi: "olcemedigine OLCEMIYORUM der". Artik O'ya gider,
            # sayaca girer ve hukum satirinda gorunur.
            O.append("H15: '%s' BEYANLA GEVSETILDI -> bagli kapi(lar) ARTIK OLCMUYOR — %s"
                     % (anahtar, gerekce[:70]))
        else:
            fail("H15", mesaj + "\n"
                 "      Bilincliyse .hafizarc'a gerekce yaz (en az 15 karakter):\n"
                 "        \"politika_gerekce\": { \"%s\": \"neden\" }\n"
                 "      sonra: python hafiza.py muhur \"politika gerekcesi yazildi\"" % anahtar)
    _politika("kural_isaretleri", not rc.get("kural_isaretleri"),
              "POLITIKA GEVSETILMIS: kural_isaretleri BOS — H7 ve emekli kural korumasi FIILEN KAPALI.")
    _politika("tavan_kb", rc["tavan_kb"] > 1000,
              "POLITIKA GEVSETILMIS: tavan_kb=%s — H2 fiilen kapali." % rc["tavan_kb"])
    _politika("zorunlu_bolumler", not rc.get("zorunlu_bolumler"),
              "POLITIKA GEVSETILMIS: zorunlu_bolumler BOS — H3 fiilen kapali.")
    # FABLE 3. TUR · B-8: tavan_kb absurt degerde itiraf uretiyordu ama bayatlik_gun
    # ve hafiza_gecikme_gun uretmiyordu — ayni mekanizmanin KAPSAM bosluguydu.
    # Denetci "her gevsetme ayni beyan kapisindan gecmeli" dedi; haklı.
    _politika("bayatlik_gun", rc["bayatlik_gun"] > 3650,
              "POLITIKA GEVSETILMIS: bayatlik_gun=%s (>10 yil) — H12 fiilen kapali."
              % rc["bayatlik_gun"])
    _politika("hafiza_gecikme_gun", rc["hafiza_gecikme_gun"] > 3650,
              "POLITIKA GEVSETILMIS: hafiza_gecikme_gun=%s (>10 yil) — H14 fiilen kapali."
              % rc["hafiza_gecikme_gun"])
    if not os.path.isfile(y.konular):
        fail("H15", "KONULAR.md YOK — konu sozlugu disiplini kapali (H10'un yarisi olcmuyor).")
    _defter_bayt = sum(os.path.getsize(x) for x in
                       (y.kova, y.duzelt, y.tasinma, y.korunan, y.zincir)
                       if os.path.isfile(x))
    if _defter_bayt > 5 * 1024 * 1024:
        fail("H2", "DEFTERLER SISTI: %.1f MB (tavan 5 MB) — beyan defterleri her `derle` ile "
                   "buyur; arsivleme/kirpma gerekiyor." % (_defter_bayt / 1048576.0))
    else:
        N.append("H2: defterler %.0f KB" % (_defter_bayt / 1024.0))
    N.append("H15: politika %d kural isareti · tavan %s KB · gecikme %s gun%s"
             % (len(rc.get("kural_isaretleri") or []), rc.get("tavan_kb"),
                rc.get("hafiza_gecikme_gun"),
                (" · %d beyanli gevseklik" % len(pg)) if pg else ""))

    # ---- H14 DISIPLIN (proje ilerledi mi, hafiza ilerledi mi) -----------
    gecikme = rc["hafiza_gecikme_gun"]
    if gecikme <= 0:
        O.append("H14: hafiza_gecikme_gun=0 — disiplin kapisi KAPALI (bilincli)")
    elif not t_son:
        O.append("H14: hafiza tarihi cozulemedi — disiplin OLCULEMIYOR")
    else:
        haric = {".git", "node_modules", "__pycache__", ".venv", "arsiv", "gunluk", "dist", "build"}
        # Fable Bulgu 9: clone/checkout tum mtime'lari "simdi"ye ceker -> yanlis kirmizi.
        # Fable §3.1: ama HER dosyaya min(mtime, son-commit) uygulamak, COMMITLENMEMIS
        # calismayi da eski commit tarihine indiriyordu -> H14'un VAR OLUS NEDENI
        # ("calisildi, kayit birakilmadi") en yaygin halde sessizce kapaniyordu.
        # Dogru ayrim, dosyanin git'e gore DURUMU:
        #   KIRLI (degismis/izlenmeyen) -> mtime GERCEK calisma zamanidir, aynen kullan.
        #   TEMIZ  (izlenen, degismemis) -> mtime clone artefakti olabilir; ICERIK tarihi kullan.
        # Ayrica bu, dosya-basina `git log` cagrisini de bitirir (2000 dosyada ~5 sn -> 2 cagri).
        # BAGIMSIZ DENETIM — YUKSEK (bu kullanicida yuksek isabet): `git status --porcelain`
        # ASCII-DISI yollari C-kacisli olarak TIRNAKLAR ("\303\247al\304\261..."); onceki
        # ayristirma tirnagi atip kacisi cozmuyordu, dolayisiyla TURKCE ADLI her dosya
        # "temiz" sayilip mtime'i yok sayiliyordu -> Turkce adli dosyada calismak H14'e
        # GORUNMUYORDU. Cozum: -z (NUL ayrac) — git bu kipte HIC tirnaklamaz/kacislamaz.
        #
        # IKINCI KUSUR: .gitignore'lu dosyalar `git status`ta gorunmedigi icin "temiz"
        # sinifina dusuyor, `git log` de onlar icin bir sey dondurmuyordu -> mtime'lari
        # TAMAMEN devre disi kaliyordu (v2.1.0'a gore REGRESYON). Cozum: IZLENEN dosya
        # listesini ayrica al; izlenmeyen her dosya (ignore'lu dahil) mtime ile olculur.
        git_var = bool(shutil.which("git")) and os.path.isdir(os.path.join(kok, ".git"))
        kirli, izlenen = set(), set()
        if git_var:
            def _git_z(*args):
                r = subprocess.run(["git", "-C", kok] + list(args), capture_output=True)
                if r.returncode != 0:
                    return None
                return [x.decode("utf-8", "replace")
                        for x in (r.stdout or b"").split(b"\0") if x]
            durum = _git_z("status", "--porcelain", "-z", "-uall")
            izler = _git_z("ls-files", "-z")
            if durum is None or izler is None:
                git_var = False                          # git konusmuyorsa mtime'a don
            else:
                izlenen = set(izler)
                atla = False
                for oge in durum:
                    if atla:                             # 'R'/'C' kayitlarinin ESKI adi
                        atla = False; continue
                    if len(oge) > 3:
                        kirli.add(oge[3:])
                        if oge[0] in ("R", "C"):         # -z kipinde eski ad AYRI ogedir
                            atla = True
        adaylar = []                                     # (rel, mtime)
        for r0, d0, f0 in os.walk(kok):
            d0[:] = [d for d in d0 if d not in haric]
            for f in f0:
                if f in (os.path.basename(y.canli), RC_AD, "KONULAR.md", "SAKLAMA_PLANI.md",
                         os.path.basename(y.kural)):
                    continue
                if f.startswith(".") or f.endswith((".pyc", ".log", ".tmp")):
                    continue
                p0 = os.path.join(r0, f)
                try:
                    m0 = os.path.getmtime(p0)
                except OSError:
                    continue
                adaylar.append((os.path.relpath(p0, kok).replace("\\", "/"), m0))
        en_yeni_t, en_yeni_f = None, None
        temiz = []
        for rel0, m0 in adaylar:
            # TEMIZ sinifi = git'in IZLEDIGI ve degismemis dosya. Izlenmeyen (yeni ya da
            # .gitignore'lu) her dosya mtime ile olculur — orasi tam da "kayit birakilmayan
            # calismanin" yasadigi yer.
            if git_var and rel0 in izlenen and rel0 not in kirli:
                temiz.append(rel0)                       # icerik tarihi toplu sorulacak
                continue
            if en_yeni_t is None or m0 > en_yeni_t:      # kirli/izlenmeyen ya da git yok
                en_yeni_t, en_yeni_f = m0, rel0
        if temiz:
            # TEK cagri: bu dosyalardan HERHANGI birine dokunan EN YENI commit.
            # (Aradigimiz zaten maksimum oldugu icin dosya-basina sormaya gerek yok.)
            oba = 400                                    # komut satiri sinirina karsi obekleme
            for i0 in range(0, len(temiz), oba):
                obek = temiz[i0:i0 + oba]
                rg = subprocess.run(["git", "-C", kok, "log", "-1", "--format=%ct", "--"] + obek,
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
                if rg.returncode == 0 and (rg.stdout or "").strip().isdigit():
                    ct = int(rg.stdout.strip())
                    if en_yeni_t is None or ct > en_yeni_t:
                        en_yeni_t, en_yeni_f = ct, "(commit'li dosyalar)"
        if en_yeni_t is None:
            N.append("H14: karsilastirilacak proje dosyasi yok")
        else:
            d_proje = _dt.date.fromtimestamp(en_yeni_t)
            fark = (d_proje - t_son).days
            if fark < -gecikme:
                fail("H14", "hafiza tarihi proje dosyalarindan %d gun ILERIDE — tutarsiz." % (-fark))
            if fark > gecikme:
                fail("H14", "PROJE ILERLEDI, HAFIZA ILERLEMEDI: en yeni degisiklik %s (%s), "
                            "hafiza %s -> %d gun geride (tavan %d)."
                     % (d_proje.isoformat(), en_yeni_f, t_son.isoformat(), fark, gecikme))
                F.append("      -> Calisildi ama kayit birakilmadi. hafiza.py not ... sonra hafiza.py derle")
            else:
                N.append("H14: hafiza projeyle es (en yeni degisiklik %s, hafiza %s)"
                         % (d_proje.isoformat(), t_son.isoformat()))

    return

# ---------------------------------------------------------------- ISIRMA KANITI

def _kapi_metni(kok):
    # -X utf8 ZORUNLU: Windows'ta cocuk surecin stdout kodlamasi varsayilan olarak cp1254'tur;
    # biz utf-8 okudugumuz icin '·' ve '—' bozuk cikardi (Windows sinamasinda olculdu).
    ortam = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.abspath(__file__), "kapi", "--kok=" + kok],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=ortam)
    return r.returncode, (r.stdout or "") + (r.stderr or "")

class MutantKurulamadi(Exception):
    """Mutantin KENDISI kurulamadi (ör. beklenen bölüm yok). Bu, kapinin kör oldugu
    anlamina GELMEZ — testin kendi hatasidir ve AYRI raporlanir.
    (Fable Bulgu 3: eskiden StopIteration yutulup 'KACTI' -> sahte 'KAPI KOR' oluyordu.)"""


def cmd_isir(a):
    """KOR KAPI PROTOKOLU: her kapi icin bilerek bir mutant kur, kapinin ISIRDIGINI kanitla.
    Kirli kopyada YAKALAMALI, temiz surumde YAKALAMAMALI. Isirmayan kapi = OLCUM YOK."""
    import tempfile
    kok = kok_bul(a.kok); rc = rc_oku(kok); Y(kok, rc)

    kod, cikti = _kapi_metni(kok)
    if kod != 0:
        # O-4: bu, "KAPI KOR" ile ayni cikis koduna (1) katlaniyordu; oysa burada
        # ISIRMA HIC OLCULMEDI. Ayri kod: 4.
        print("UYARI: TEMIZ surum zaten FAIL veriyor — once onu duzelt, sonra isirma sina.")
        print("       (cikis kodu 4 = 'isirma OLCULMEDI'; kor kapi 1'dir.)")
        print(cikti)
        return 4

    kurulamayan = []

    def mutant(ad, kapi, degistir):
        tmp = tempfile.mkdtemp(prefix="hafiza_isir_")
        hedef = os.path.join(tmp, "p")
        shutil.copytree(kok, hedef, ignore=shutil.ignore_patterns(".git", "node_modules"))
        try:
            try:
                degistir(hedef)
            except (MutantKurulamadi, StopIteration, KeyError, FileNotFoundError,
                    ValueError, IndexError) as e:
                # Y-3: ValueError/IndexError de bir TEST KURULUM hatasidir (bozuk defter,
                # bos dizin vb.), KAPI HUKMU degildir. Ayri raporlanir.
                # NOT: oldur()'un SystemExit'i Exception DEGILDIR; bilerek buradan kacar —
                # gercek projenin defteri bozuksa `isir` "20/20 ISIRDI" dememeli, DURMALI.
                raise MutantKurulamadi("%s: %s" % (type(e).__name__, e))
            k, c = _kapi_metni(hedef)
            yakalandi = (k != 0) and (("[%s]" % kapi) in c or ("[%s-" % kapi) in c)
            return yakalandi, k, c
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def _komut(hedef, *argv):
        """Mutant kopyasinda gercek bir komut kosar; (cikis_kodu, cikti) doner."""
        r = subprocess.run([sys.executable, "-X", "utf8", os.path.abspath(__file__)]
                           + list(argv) + ["--kok=" + hedef],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        return r.returncode, (r.stdout or "") + (r.stderr or "")

    def komut_sinamasi(ad, dene):
        """FABLE 3. TUR: B-2/B-3 ve B-5 birer KAPI olcumu degil, KOMUT DAVRANISIDIR
        (kok disina yazma reddediliyor mu; kilit sahipligi doguru mu). Kapi mutanti
        cercevesine zorla sokmak 'kapi isirdi' yanilsamasi uretirdi. Bu yuzden ayri
        bir cerceve — ama AYNI sozlukle raporlanir: ISIRDI / KACTI / KURULAMADI."""
        tmp = tempfile.mkdtemp(prefix="hafiza_isir_k_")
        hedef = os.path.join(tmp, "p")
        shutil.copytree(kok, hedef, ignore=shutil.ignore_patterns(".git", "node_modules"))
        try:
            try:
                return dene(hedef, tmp)
            except (MutantKurulamadi, StopIteration, KeyError, FileNotFoundError,
                    ValueError, IndexError) as e:
                raise MutantKurulamadi("%s: %s" % (type(e).__name__, e))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def k_kacis(hedef, tmp):
        """M-KACIS — B-2/B-3: CLI yol argumani proje agacinin DISINA cikabiliyor mu?"""
        disarida = os.path.join(tmp, "KURBAN.md")
        yaz(disarida, "KURBAN-ORIJINAL\n")
        once = oku(disarida)
        cp = _canli(hedef)
        satir = "- kacis-mutanti-tasinabilir-satir"
        with open(cp, "a", encoding="utf-8", newline="\n") as f:
            f.write(satir + "\n")
        hd = _hdir(hedef)
        ars = [f for f in sorted(os.listdir(hd)) if re.match(r"^HAFIZA_.*\.md$", f)]
        if not ars:
            raise MutantKurulamadi("arsiv dosyasi yok")
        with open(os.path.join(hd, ars[0]), "a", encoding="utf-8", newline="\n") as f:
            f.write(satir + "\n")
        n = len(satirlar(cp)) - 1
        k1, c1 = _komut(hedef, "emekli", "--hedef=../../../KURBAN.md",
                        "--not=kacis mutanti kok disina yazma denemesi", "%d-%d" % (n, n))
        dis_sir = os.path.join(tmp, "DIS_SIR.md")
        yaz(dis_sir, "a BASLA gizli BITIS b\n")
        k2, c2 = _komut(hedef, "korunan", "--dosya=../DIS_SIR.md", "--bas=BASLA",
                        "--son=BITIS", "--gerekce=kacis mutanti kok disi okuma denemesi")
        yazma_engellendi = (k1 != 0) and (oku(disarida) == once)
        okuma_engellendi = (k2 != 0) and ("../DIS_SIR.md" not in
                                          (oku(os.path.join(hd, "_KORUNAN.json"))
                                           if os.path.isfile(os.path.join(hd, "_KORUNAN.json"))
                                           else ""))
        ok = yazma_engellendi and okuma_engellendi
        return ok, 0 if ok else 1, ("emekli --hedef: %s (exit %d)\nkorunan --dosya: %s (exit %d)\n%s%s"
                                    % ("REDDEDILDI" if yazma_engellendi else "KOK DISINA YAZDI", k1,
                                       "REDDEDILDI" if okuma_engellendi else "KOK DISINDAN OKUDU", k2,
                                       c1[:200], c2[:200]))

    def k_aklama(hedef, tmp):
        """M-AKLAMA — KENDI BULDUGUMUZ, B-1'IN KARDESI.

        Denetci yalniz zinciri 0 BAYTA indirmeyi olctu. Ama SILMEK de ayni aklamayi
        yapiyordu: kapi "zincir YOK" diye FAIL veriyor, kullanici `muhur` (ya da
        idempotent `kur`) kosunca YENI bir genesis halkasi yaziliyor ve o halkanin
        yuku TAHRIF EDILMIS dosyalarin SHA'larini kapsiyor -> tahrif MESRU bir
        zincirle KALICI temize cikiyor. Yani kapiyi duzeltmek yetmez; YAZMA tarafi
        da durmalidir. Bu bir kapi hukmu degil KOMUT davranisi oldugu icin kapi
        mutanti olarak yazilamaz: kapi mutanti sabotajda bile ISIRIYOR (olculdu),
        cunku kapi zaten 'zincir YOK' diyor — yani sinifi OLCMUYOR."""
        hd = _hdir(hedef)
        kp = os.path.join(hedef, "KONULAR.md")
        if not os.path.isfile(kp):
            raise MutantKurulamadi("KONULAR.md yok")
        with open(kp, "a", encoding="utf-8", newline="\n") as f:
            f.write("| kacak | beyansiz eklendi |\n")
        zp = os.path.join(hd, "_ZINCIR.jsonl")
        sonuc = []
        for ad, hazirla in (("SILINDI", lambda: os.remove(zp)),
                            ("0-BAYT", lambda: open(zp, "w").close())):
            yedek = oku(zp) if os.path.isfile(zp) else None
            hazirla()
            k1, c1 = _komut(hedef, "muhur", "aklama mutanti icin muhurleme denemesi")
            k2, c2 = _komut(hedef, "kur")
            # ASIL OLCUT cikis kodu DEGIL: "aklama denemelerinden SONRA tahrif hala
            # gorunuyor mu". Komut baska bir nedenle de dusebilir; onemli olan
            # KONULAR.md tahrifinin mesru bir zincirle temize CIKMAMIS olmasidir.
            k3, c3 = _kapi_metni(hedef)
            engellendi = (k3 != 0)
            sonuc.append((ad, engellendi, k1, k2, k3))
            if yedek is not None:
                yaz(zp, yedek)
        ok = all(e for _, e, _, _, _ in sonuc)
        return ok, 0 if ok else 1, " · ".join(
            "%s: tahrif %s (muhur=%d kur=%d kapi-sonrasi=%d)"
            % (a, "gorunur kaldi" if e else "AKLANDI", x, yy, z) for a, e, x, yy, z in sonuc)

    def k_devir(hedef, tmp):
        """M-DEVIR — IC DENETIM (B-1): `rm .hafizarc` + `devral` ile yeniden capalama.

        Bu ENGELLENEMEZ (yazma erisimi olan her capayi silebilir) ama GIZLENEMEZ
        olmalidir. Olculen: (a) arac onceki kurulum izini TUM AGACTA buluyor mu,
        (b) yeniden capalamayi CANLI HAFIZAYA kalici olarak yaziyor mu, (c) o kayit
        CIPAYA girmis mi (silinmesi H1 'KAYIP' versin), (d) GENESIS halkasinda mi.
        Uc ayri kilik denenir: dizini sil · dizini tasi · hicbir defteri silme."""
        # ON KOSUL: iz aranabilmesi icin projenin EN AZ BIR KEZ derlenmis olmasi gerek
        # (canli hafizadaki blok kaynak= alanlari izin son kalesi). Hic derlenmemis bir
        # projede `rm -rf` sonrasi geriye iz KALMAZ — bu bir KAPI KORLUGU DEGIL, test
        # on-kosulunun saglanmamasidir ve OYLE raporlanir.
        _canli_metin = oku(_canli(hedef)) if os.path.isfile(_canli(hedef)) else ""
        if not re.search(r'kaynak="[^"]*/gunluk/', _canli_metin):
            raise MutantKurulamadi("proje hic derlenmemis — canli hafizada blok kaynagi yok")
        sonuc = []
        for ad, hazirla in (("rm -rf", "sil"), ("mv", "tasi"), ("dokunma", None)):
            alt = os.path.join(tmp, "d_" + ad.replace(" ", "").replace("-", ""))
            shutil.copytree(hedef, alt)
            r2 = rc_oku(alt)
            y2 = Y(alt, r2)
            if hazirla == "sil":
                shutil.rmtree(y2.h, ignore_errors=True)
            elif hazirla == "tasi":
                shutil.move(y2.h, y2.h + "_yedek")
            os.remove(os.path.join(alt, RC_AD))
            k1, c1 = _komut(alt, "devral")
            canli = oku(os.path.join(alt, r2["canli"])) if os.path.isfile(
                os.path.join(alt, r2["canli"])) else ""
            r3 = rc_oku(alt) if os.path.isfile(os.path.join(alt, RC_AD)) else None
            snap = ""
            if r3:
                y3 = Y(alt, r3)
                if os.path.isfile(y3.snap):
                    snap = oku(y3.snap)
            gorunur = ("ONCEKI KURULUM IZI" in c1) and ("CAPA DEVRI" in canli) \
                      and ("CAPA DEVRI" in snap)
            sonuc.append((ad, gorunur))
        ok = all(g for _, g in sonuc)
        return ok, 0 if ok else 1, " · ".join(
            "%s: %s" % (a, "kayda gecti" if g else "GIZLENDI") for a, g in sonuc)

    def k_kilit(hedef, tmp):
        """M-KILIT — B-5: `kilit_birak` BASKASININ kilidini siliyor mu?

        DIKKAT — ilk yazdigim hali SAHTE ISIRIYORDU: yalnizca alt-surecte `muhur`
        kosuyordu, o da kilidi hic ALAMADIGI icin `kilit_birak`'in sahiplik dali
        HIC CALISMIYORDU. Sabotaj testinde (sahiplik kontrolu 'if False' yapilarak)
        mutant yine ISIRDI dedi -> yani sinifi olcmuyordu. Bu, aracin kendi
        'kor kapinin kor mutanti' dersinin test tarafindaki hali. Duzeltilmis hali
        yarisi GERCEKTEN kurar: A kilidi ALIR, B devralir, A cikar."""
        hd = _hdir(hedef)
        kp = os.path.join(hd, ".kilit")
        r2 = rc_oku(hedef)
        y2 = Y(hedef, r2)
        eski_kilit = KILIT[0]
        try:
            KILIT[0] = None
            kilit_al(y2)                                    # A kilidi ALDI
            yaz(kp, "pid=999999 · B surecinin kilidi · komut: derle\n")   # B devraldi
            once = oku(kp)
            kilit_birak()                                   # A cikiyor
            korundu = os.path.isfile(kp) and oku(kp) == once
            # (b) A KENDI kilidini birakabiliyor mu? (asiri koruma regresyonu)
            KILIT[0] = None
            if os.path.isfile(kp):
                os.remove(kp)
            kendi = kilit_al(y2)
            kilit_birak()
            kendini_birakti = not os.path.exists(kendi)
        finally:
            KILIT[0] = eski_kilit
        # (c) mesgul kilitte BAYAT/YASIYOR tanisi veriliyor mu?
        yaz(kp, "pid=999999 · B surecinin kilidi · komut: derle\n")
        k1, c1 = _komut(hedef, "muhur", "kilit sahipligi mutanti icin muhur denemesi")
        durdu = (k1 != 0) and ("BASKA BIR YAZMA ISLEMI SURUYOR" in c1)
        tani = ("BAYAT" in c1) or ("YASIYOR" in c1) or ("OLCULEMEDI" in c1)
        ok = korundu and kendini_birakti and durdu and tani
        return ok, 0 if ok else 1, (
            "B'nin kilidi korundu=%s · A kendi kilidini birakti=%s · mesgulde durdu=%s "
            "· tani=%s\n%s" % (korundu, kendini_birakti, durdu, tani, c1[:300]))

    def k_kilit_kapsam(hedef, tmp):
        """M-KILITK — A-1: kilit KAPSAMI. `kur` ve `devral` kilidi aliyor mu?

        NEDEN AYRI BIR SINAMA: M-KILIT kilidin SAHIPLIGINI olcer (baskasininkini
        siliyor muyuz). Bu ise KAPSAMI olcer (kilidi alan komut kumesi dogru mu).
        v2.4'te `devral`a CANLI HAFIZAYA yazan yeni bir yol eklendi (CAPA DEVRI
        blogu) ve o yol kilit disiplininin DISINDA birakildi — yani sahiplik
        derinlestirilirken kapsam denetlenmedi. Bu, aracin kendi doktrininin
        ihlali: 'bir sinif tek tek yuzeyler sarilarak degil, SINIRDA kapanir'.

        Olculen: baskasina ait bir kilit dururken (a) `devral` DURUYOR mu ve canli
        hafizayi DEGISTIRMIYOR mu, (b) `kur` DURUYOR mu. Ikisi de yazan komuttur."""
        sonuc = []
        # (a) devral — .hafizarc'i silip yetim v2 uzerinde kosulur (mesru devir yolu)
        alt = os.path.join(tmp, "kk_devral")
        shutil.copytree(hedef, alt)
        r2 = rc_oku(alt); y2 = Y(alt, r2)
        os.makedirs(y2.h, exist_ok=True)
        os.remove(os.path.join(alt, RC_AD))
        yaz(os.path.join(y2.h, ".kilit"),
            "pid=999999 · BASKA surecin kilidi · komut: derle\n")
        cp = os.path.join(alt, r2["canli"])
        once = sha_dosya(cp) if os.path.isfile(cp) else ""
        k1, c1 = _komut(alt, "devral")
        sonra = sha_dosya(cp) if os.path.isfile(cp) else ""
        d_durdu = (k1 != 0) and ("BASKA BIR YAZMA ISLEMI SURUYOR" in c1)
        d_yazmadi = (once == sonra)
        sonuc.append(("devral", d_durdu and d_yazmadi,
                      "exit=%d durdu=%s canli degismedi=%s" % (k1, d_durdu, d_yazmadi)))
        # (b) kur — kurulu proje uzerinde idempotent tazeleme de YAZAR
        alt2 = os.path.join(tmp, "kk_kur")
        shutil.copytree(hedef, alt2)
        r3 = rc_oku(alt2); y3 = Y(alt2, r3)
        os.makedirs(y3.h, exist_ok=True)
        yaz(os.path.join(y3.h, ".kilit"),
            "pid=999999 · BASKA surecin kilidi · komut: derle\n")
        k2, c2 = _komut(alt2, "kur")
        k_durdu = (k2 != 0) and ("BASKA BIR YAZMA ISLEMI SURUYOR" in c2)
        sonuc.append(("kur", k_durdu, "exit=%d durdu=%s" % (k2, k_durdu)))
        ok = all(g for _, g, _ in sonuc)
        return ok, 0 if ok else 1, " · ".join("%s: %s" % (a, d) for a, _, d in sonuc)

    def _canli(h):
        return os.path.join(h, rc["canli"])

    def _hdir(h):
        """Mutant kopyasindaki HAFIZA DIZINI — rc'den okunur.
        (Devralinan projede burasi 'arsiv/hafiza/v2'dir; sabit yazmak mutanti KOR yapar.
         Bu bizzat olculdu: M-H0 ve M-H6 devralinmis projede kacti.)"""
        r2 = json.loads(oku(os.path.join(h, RC_AD)))
        return os.path.join(h, *r2.get("hafiza_dizini", "arsiv/hafiza").split("/"))

    def m_h0(h):
        p = os.path.join(_hdir(h), "_KAYNAK.md")
        yaz(p, oku(p) + "\nSNAPSHOT KURCALANDI\n")

    def _canli_kova_satiri(h):
        """Snapshot'ta CANLI kovasinda olan ve HALEN canlida duran bir satir sec.
        Sabit baslik aramak KIRILGANDI (emoji/devir projelerinde StopIteration)."""
        hd = _hdir(h)
        kv = json.loads(oku(os.path.join(hd, "_KOVA.json")))["satirlar"]
        snap = satirlar(os.path.join(hd, "_KAYNAK.md"))
        canli = satirlar(_canli(h))
        canli_set = set(norm(x) for x in canli)
        for i, k in sorted(kv.items(), key=lambda x: int(x[0])):
            idx = int(i) - 1
            if not (0 <= idx < len(snap)) or not str(k).startswith("CANLI"):
                continue
            s = norm(snap[idx])
            if not anlamli(s) or "<!--" in s:
                continue
            if s in canli_set:
                return next(j for j, x in enumerate(canli) if norm(x) == s), canli
        raise MutantKurulamadi("CANLI kovasinda canlida duran uygun satir bulunamadi")

    def m_h1(h):
        idx, L = _canli_kova_satiri(h)
        yaz(_canli(h), "\n".join(L[:idx] + L[idx + 1:]))

    def m_kova(h):
        idx, L = _canli_kova_satiri(h)
        ar = os.path.join(_hdir(h), "HAFIZA_01.md")
        if not os.path.isfile(ar):
            adaylar = [f for f in os.listdir(_hdir(h)) if re.match(r"^HAFIZA_.*\.md$", f)]
            if not adaylar:
                raise MutantKurulamadi("hedef arsiv dosyasi yok")
            ar = os.path.join(_hdir(h), sorted(adaylar)[-1])
        with open(ar, "a", encoding="utf-8") as f:
            f.write("\n" + L[idx] + "\n")          # arsive KOYULDU ama BEYAN EDILMEDI
        yaz(_canli(h), "\n".join(L[:idx] + L[idx + 1:]))

    def m_h2(h):
        with open(_canli(h), "a", encoding="utf-8") as f:
            f.write("\n" + ("dolgu satiri " * 12 + "\n") * 5000)

    def m_h3(h):
        L = satirlar(_canli(h))
        hedef = None
        for b in rc["zorunlu_bolumler"]:
            if any(x.startswith("#") and bas_eslesir(x, b) for x in L):
                hedef = b; break
        if hedef is None:
            raise MutantKurulamadi("silinecek zorunlu bolum bulunamadi")
        yaz(_canli(h), "\n".join(s for s in L if not (s.startswith("#") and bas_eslesir(s, hedef))))

    def m_h4(h):
        with open(_canli(h), "a", encoding="utf-8") as f:
            f.write("\n- bkz `belgeler/ZZ_mutant_asla_var_olmayan_9f3a.md`\n")

    def m_h6(h):
        yaz(os.path.join(_hdir(h), "HAFIZA_99_HAYALET.md"), "# hayalet arsiv\n")

    def m_h7(h):
        L = satirlar(_canli(h))
        i = None
        for b in rc["zorunlu_bolumler"]:
            if any(bas_eslesir(b, x) for x in rc["kural_evi_bolumleri"]):
                continue
            j, _ = _bolum_araligi(L, b)
            if j is not None:
                i = j; break
        if i is None:
            raise MutantKurulamadi("kural evi DISINDA bir bolum bulunamadi")
        L.insert(i + 1, "> **PAZARLIKSIZ:** bu kural yanlis evde yasiyor.")
        yaz(_canli(h), "\n".join(L))

    def m_h10(h):
        L = satirlar(_canli(h))
        Lk = kod_disi(L)                  # Y-8: ornek satir gercek blok sayilmasin
        mevcut = None
        for k, s in enumerate(Lk):
            m0 = BLOK_BAS.search(s)
            if m0 and oznitelik_coz(m0.group(1)).get("konu"):
                mevcut = oznitelik_coz(m0.group(1))["konu"]; break
        if mevcut is None:
            raise MutantKurulamadi("canlida hic bloklu konu yok (bloklastir kosulmamis)")
        blok = ['<!-- blok konu="%s" guncel="%s" kaynak="-" -->' % (mevcut, bugun()),
                "- ikinci blok (ayni konu) — sikistirma kirilmali", "<!-- /blok -->"]
        yaz(_canli(h), "\n".join(L + [""] + blok))

    def m_h11(h):
        """IC DENETIM (B-3): sabit `0009` yaziliyordu. Projede zaten 8 karar varsa bu
        numara BOSLUGU DOLDURUYOR, hicbir kusur kurulmuyor ve `isir` bunu 'kacan mutant'
        sanip SAHTE 'KAPI KOR' + exit 1 veriyordu. Yani aracin kendi kanit mekanizmasi
        PROJE DURUMUNA bagliydi. Numara artik mevcut en buyugun IKI fazlasi: her zaman
        gercek bir bosluk."""
        d = os.path.join(h, "kararlar")
        os.makedirs(d, exist_ok=True)
        mevcut = [int(m.group(1)) for f in os.listdir(d)
                  for m in [re.match(r"^(\d{4})-", f)] if m]
        no = (max(mevcut) if mevcut else 0) + 2
        yaz(os.path.join(d, "%04d-numara-boslugu.md" % no),
            "---\nno: %04d\nbaslik: bosluk\ndurum: onerildi\ntarih: %s\nkonu: test\n"
            "yerini-aldigi: -\nyerine-gecen: -\n---\n\ngovde\n" % (no, bugun()))

    def m_h12(h):
        t = oku(_canli(h))
        yaz(_canli(h), re.sub(r"(Son g[uü]ncelleme:\s*)\S+", r"\g<1>2000-01-01", t, count=1))

    def m_h13(h):
        os.remove(os.path.join(h, "SAKLAMA_PLANI.md"))

    def m_h1b(h):
        """FABLE BULGU 1 mutanti: baseline-SONRASI eklenmis bir blogu sil."""
        L = satirlar(_canli(h))
        Lk = kod_disi(L)                  # Y-8
        bas = None
        for i, s in enumerate(Lk):
            m0 = BLOK_BAS.search(s)
            if m0 and "kaynak=\"arsiv" in s:
                bas = i; break
        if bas is None:
            raise MutantKurulamadi("derle ile eklenmis blok yok (once derle kosulmali)")
        son = bas
        while son < len(L) and not BLOK_SON.search(Lk[son]):
            son += 1
        yaz(_canli(h), "\n".join(L[:bas] + L[son + 1:]))

    def m_h0d(h):
        """M-H0d — FABLE 3. TUR · B-1: zinciri 0 BAYTA indir + bir defteri tahrif et.
        v2.3.0'da bu, kapiyi YESIL yapiyordu (bos zincir -> defter-SHA kontrolu
        tumden atlaniyordu) ve HICBIR MUTANT bu sinifi olcmuyordu: kor kapinin
        kor mutanti. Simdi H0 ISIRMALI."""
        kp = os.path.join(h, "KONULAR.md")
        if not os.path.isfile(kp):
            raise MutantKurulamadi("KONULAR.md yok")
        with open(kp, "a", encoding="utf-8", newline="\n") as f:
            f.write("| kacak | beyansiz eklendi |\n")
        open(os.path.join(_hdir(h), "_ZINCIR.jsonl"), "w").close()

    def m_h0t(h):
        """M-H0t — FABLE 3. TUR · B-11: son halkanin zaman damgasini GELECEGE al ve
        hash'i YENIDEN HESAPLA (yani hash denetiminden gecsin). Zaman mesruiyeti
        olculmuyorsa bu tahrif H0'dan sessizce gecerdi."""
        zp = os.path.join(_hdir(h), "_ZINCIR.jsonl")
        kayitlar = [json.loads(x) for x in oku(zp).split("\n") if x.strip()]
        if not kayitlar:
            raise MutantKurulamadi("zincir bos")
        k = kayitlar[-1]
        k["t"] = "2099-01-01T00:00:00"
        govde = {kk: vv for kk, vv in k.items() if kk != "halka"}
        k["halka"] = sha(k["onceki"] + json.dumps(govde, sort_keys=True, ensure_ascii=False))
        yaz(zp, "\n".join(json.dumps(x, ensure_ascii=False) for x in kayitlar) + "\n")

    def m_h0b(h):
        """FABLE BULGU 2 mutanti: zincir kaydinin GEREKCE/tarih alanini tahrif et."""
        zp = os.path.join(_hdir(h), "_ZINCIR.jsonl")
        kayitlar = [json.loads(x) for x in oku(zp).split("\n") if x.strip()]
        if not kayitlar:
            raise MutantKurulamadi("zincir bos")
        kayitlar[-1]["gerekce"] = "TAHRIF EDILMIS"
        kayitlar[-1]["t"] = "1999-01-01T00:00:00"
        yaz(zp, "\n".join(json.dumps(k, ensure_ascii=False) for k in kayitlar) + "\n")

    def m_h10b(h):
        """FABLE BULGU 6 mutanti: kapanmamis blok."""
        with open(_canli(h), "a", encoding="utf-8") as f:
            f.write('\n<!-- blok konu="genel-durum" guncel="%s" kaynak="-" -->\n- kapanmadi\n'
                    % bugun())

    def m_h12b(h):
        """FABLE BULGU 8 mutanti: GELECEK tarih (iki tazelik kapisini birden susturuyordu)."""
        cp = os.path.join(h, rc["canli"])
        L2 = satirlar(cp)
        for k, s in enumerate(L2):
            if "Son g" in s and "ncelleme" in s:
                L2[k] = tarih_damgasini_guncelle(s, "2099-01-01"); break
        yaz(cp, "\n".join(L2))

    def m_h4b(h):
        """FABLE BULGU 4 mutanti: TURKCE adli olu baglanti."""
        with open(_canli(h), "a", encoding="utf-8") as f:
            f.write("\n- bkz `belgeler/müşteri_görüşme_kaydı.md`\n")

    def m_h14(h):
        # proje dosyasi bugun degisti ama hafiza 10 gun once guncellenmis
        yaz(os.path.join(h, "yeni_calisma.txt"), "bugun uretilmis bir proje dosyasi\n")
        gecmis = (_dt.date.today() - _dt.timedelta(days=10)).isoformat()
        cp = os.path.join(h, rc["canli"])
        satir_listesi = satirlar(cp)
        for k, s in enumerate(satir_listesi):
            if "Son g" in s and "ncelleme" in s:
                satir_listesi[k] = "> Son guncelleme: " + gecmis
                break
        yaz(cp, "\n".join(satir_listesi))

    def m_h5(h):
        rp = os.path.join(h, RC_AD)
        c = json.loads(oku(rp)); c["kanonik_artefakt"] = "prototip_v[0-9.]+[.]html"
        yaz(rp, json.dumps(c, ensure_ascii=False, indent=2) + "\n")
        L = satirlar(_canli(h))
        i, _ = _bolum_araligi(L, "## GUNCEL DURUM")
        L.insert(i + 1, "- aktif surum prototip_v0.49.html; onceki prototip_v0.48.html")
        yaz(_canli(h), "\n".join(L))

    # --------- v2.2.0 mutantlari: ikinci denetim turunun (Y-*) her kapisi icin ayri ------
    # ILKE (denetcinin kendi sarti): bir duzeltme "kapandi" sayilmaz, ayri mutanti ISIRANA
    # kadar. Ve bir mutantin ISIRMASI YALNIZ o satiri kanitlar — sinifi degil.

    def m_h15a(h):
        """Y-5: kural_isaretleri BOSALTILDI -> H7 ve emekli korumasi FIILEN kapali."""
        rp = os.path.join(h, RC_AD)
        c = json.loads(oku(rp)); c["kural_isaretleri"] = []
        yaz(rp, json.dumps(c, ensure_ascii=False, indent=2) + "\n")

    def m_h15b(h):
        """Y-5: tavan_kb sisirildi -> H2 fiilen kapali."""
        rp = os.path.join(h, RC_AD)
        c = json.loads(oku(rp)); c["tavan_kb"] = 99999
        yaz(rp, json.dumps(c, ensure_ascii=False, indent=2) + "\n")

    def m_h15c(h):
        """Y-5: KONULAR.md silindi -> H10'un konu-sozlugu yarisi olcmuyor."""
        kp = os.path.join(h, "KONULAR.md")
        if not os.path.isfile(kp):
            raise MutantKurulamadi("KONULAR.md zaten yok")
        os.remove(kp)

    def m_h0c(h):
        """Y-5: POLITIKA dosyasi (.hafizarc) MUHURSUZ degisti -> zincir yuku gormeli.
        (Once zincir yuku yalniz defterleri kapsiyordu; politika sessizce gevsetilebiliyordu.)"""
        rp = os.path.join(h, RC_AD)
        c = json.loads(oku(rp)); c["bayatlik_gun"] = 3650
        yaz(rp, json.dumps(c, ensure_ascii=False, indent=2) + "\n")

    def m_h7b(h):
        """Y-6: 'ASLA' isaretli kural rotasyona giren bolumde -> H7 olcmeli."""
        L = satirlar(_canli(h))
        i, _ = _bolum_araligi(L, "## GUNCEL DURUM")
        if i is None:
            raise MutantKurulamadi("## GUNCEL DURUM bolumu yok")
        L.insert(i + 1, "- ASLA gercek MEB sorusu uygulamaya gomulmez.")
        yaz(_canli(h), "\n".join(L))

    def m_h10c(h):
        """Y-8'in ACTIGI kapiyi kapatan mutant: kapanmamis kod citi butun bloklari
        olcum disi birakirdi. H10 bunu gormeli (kor kapi birakmiyoruz)."""
        L = satirlar(_canli(h))
        i, _ = _bolum_araligi(L, "## GUNCEL DURUM")
        if i is None:
            raise MutantKurulamadi("## GUNCEL DURUM bolumu yok")
        L.insert(i + 1, "```")
        yaz(_canli(h), "\n".join(L))

    def m_h10d(h):
        """BAGIMSIZ DENETIM 1. TUR'UN TAM SINIFI: ayni konuda IKINCI bir blok eklenir,
        sonra biri KOD CITI icine alinarak gizlenir. Boylece H10'un olctugu 'bir konu
        icin tek blok' kurali SESSIZCE delinmis olur — kapi bunu gormeliydi, gormuyordu.
        (Tek basina gizlenmis bir blok VERI KAYBI degildir ve OLCULEMEDI sayilir;
         TEHLIKELI olan CAKISMADIR. Mutant tam da o sinifi sinar.)"""
        L = satirlar(_canli(h))
        Lk = kod_disi(L)
        ilk = next((i for i, s in enumerate(Lk) if BLOK_BAS.search(s)), None)
        if ilk is None:
            raise MutantKurulamadi("gizlenecek gercek blok bulunamadi")
        konu = oznitelik_coz(BLOK_BAS.search(Lk[ilk]).group(1)).get("konu")
        if not konu:
            raise MutantKurulamadi("blogun konusu yok")
        son = next((i for i in range(ilk + 1, len(Lk)) if BLOK_SON.search(Lk[i])), None)
        if son is None:
            raise MutantKurulamadi("blok kapanisi bulunamadi")
        ikizi = ['<!-- blok konu="%s" guncel="%s" kaynak="-" -->' % (konu, bugun()),
                 "- gizlenmis ikinci blok (konu tekilligi sessizce delinir)", "<!-- /blok -->"]
        yaz(_canli(h), "\n".join(L + [""] + ["```"] + ikizi + ["```"]))

    def m_h14b(h):
        """BAGIMSIZ DENETIM: H14'un GIT KOLU hic sinanmiyordu (mutant kopyasina .git
        alinmiyor) — bugunun en riskli degisikligi sifir mutant kapsamiyla giriyordu.
        Ustelik TURKCE ADLI dosyada kor kaldigi da boyle kacmisti. Mutant kopya icinde
        TAZE bir depo kurup TURKCE adli, COMMITLENMEMIS bir degisiklik birakiyoruz."""
        if not shutil.which("git"):
            raise MutantKurulamadi("git yok")
        ort = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        def g(*args):
            return subprocess.run(["git", "-C", h] + list(args), capture_output=True, env=ort)
        if g("init", "-q").returncode != 0:
            raise MutantKurulamadi("git init basarisiz")
        g("config", "user.email", "t@t"); g("config", "user.name", "t")
        yaz(os.path.join(h, "çalışma_notları.md"), "ilk icerik\n")
        g("add", "-A")
        if g("commit", "-q", "-m", "ilk").returncode != 0:
            raise MutantKurulamadi("git commit basarisiz")
        # commit'i geriye al, sonra COMMITLENMEMIS bir degisiklik birak
        eski = (_dt.datetime.now() - _dt.timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%S")
        subprocess.run(["git", "-C", h, "commit", "-q", "--amend", "--no-edit", "--date=" + eski],
                       capture_output=True,
                       env=dict(ort, GIT_AUTHOR_DATE=eski, GIT_COMMITTER_DATE=eski))
        yaz(os.path.join(h, "çalışma_notları.md"), "ilk icerik\nBUGUN eklendi, commit YOK\n")
        # hafizayi 60 gun geriye cek: proje BUGUN ilerledi, hafiza ilerlemedi
        gecmis = (_dt.date.today() - _dt.timedelta(days=60)).isoformat()
        cp = _canli(h)
        yaz(cp, "\n".join(tarih_damgasini_guncelle(s, gecmis) if s.startswith("> Son g") else s
                          for s in satirlar(cp)))

    def m_h8b(h):
        """BAGIMSIZ DENETIM 5. TUR (YUKSEK): korunan blogu TAHRIF edip dosyanin BASINA
        bozulmamis bir KOPYA koymak H8'i tamamen atlatiyordu — kapi YESIL kaliyor,
        tahrif edilmis kural dosyada duruyordu. M-H8 yalniz DOGRUDAN tahrifi siniyordu;
        SINIF acikti. Bu mutant sahte-kopya sinifini sinar."""
        kp = os.path.join(h, "CLAUDE.md")
        yaz(kp, oku(kp) + "\n<!--KORU:BAS-->\nkorunan protokol satiri\n<!--KORU:SON-->\n")
        r = subprocess.run([sys.executable, "-X", "utf8", os.path.abspath(__file__), "korunan",
                            "--kok=" + h, "--dosya=CLAUDE.md", "--bas=<!--KORU:BAS-->",
                            "--son=<!--KORU:SON-->", "--gerekce=sahte kopya sinamasi icin koruma"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        if r.returncode != 0:
            raise MutantKurulamadi(r.stderr.strip()[:120])
        t = oku(kp).replace("korunan protokol satiri", "SESSIZCE DEGISTIRILDI")
        # ...ve BASA bozulmamis bir KOPYA koy (eski surumde bu H8'i susturuyordu)
        yaz(kp, "<!--KORU:BAS-->\nkorunan protokol satiri\n<!--KORU:SON-->\n" + t)

    def m_h8(h):
        kp = os.path.join(h, "CLAUDE.md")
        yaz(kp, oku(kp) + "\n<!--KORU:BAS-->\nkorunan protokol satiri\n<!--KORU:SON-->\n")
        r = subprocess.run([sys.executable, "-X", "utf8", os.path.abspath(__file__), "korunan",
                            "--kok=" + h, "--dosya=CLAUDE.md", "--bas=<!--KORU:BAS-->",
                            "--son=<!--KORU:SON-->", "--gerekce=isirma sinamasi icin korunan blok"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        if r.returncode != 0:
            raise RuntimeError(r.stderr)
        yaz(kp, oku(kp).replace("korunan protokol satiri", "SESSIZCE DEGISTIRILDI"))

    sinamalar = [
        ("M-H0  cipa (snapshot kurcalandi)", "H0", m_h0),
        ("M-H1  butunluk (canli satir silindi)", "H1", m_h1),
        ("M-H1K kova (beyansiz canli->arsiv)", "H1-KOVA", m_kova),
        ("M-H2  sisme (tavan asildi)", "H2", m_h2),
        ("M-H3  bolum (zorunlu baslik silindi)", "H3", m_h3),
        ("M-H4  olu baglanti (yok dosya)", "H4", m_h4),
        ("M-H5  surum tekilligi (2 kanonik artefakt)", "H5", m_h5),
        ("M-H6  dizin (dizinsiz arsiv dosyasi)", "H6", m_h6),
        ("M-H7  kural evi (kural yanlis bolumde)", "H7", m_h7),
        ("M-H8  korunan blok (beyansiz degisim)", "H8", m_h8),
        ("M-H10 konu tekilligi (ayni konu 2 blok)", "H10", m_h10),
        ("M-H11 karar butunlugu (numara boslugu)", "H11", m_h11),
        ("M-H12 bayatlik (tarih 2000)", "H12", m_h12),
        ("M-H13 saklama plani (silindi)", "H13", m_h13),
        ("M-H14 disiplin (proje ilerledi, hafiza durdu)", "H14", m_h14),
        ("M-H1b baseline-SONRASI blok silindi", "H1", m_h1b),
        ("M-H0b zincir gerekcesi tahrif edildi", "H0", m_h0b),
        ("M-H10b kapanmamis blok", "H10", m_h10b),
        ("M-H12b GELECEK tarih", "H12", m_h12b),
        ("M-H4b Turkce adli olu baglanti", "H4", m_h4b),
        ("M-H15a politika: kural isaretleri bosaltildi", "H15", m_h15a),
        ("M-H15b politika: tavan_kb sisirildi", "H15", m_h15b),
        ("M-H15c politika: KONULAR.md silindi", "H15", m_h15c),
        ("M-H0c  politika dosyasi muhursuz degisti", "H0", m_h0c),
        ("M-H7b  'ASLA' kurali yanlis evde", "H7", m_h7b),
        ("M-H10c kapanmamis kod citi (bloklari yutar)", "H10", m_h10c),
        ("M-H10d DENGELI cit gercek blogu gizliyor", "H10", m_h10d),
        ("M-H14b git kolu: TURKCE adli commitsiz degisiklik", "H14", m_h14b),
        ("M-H8b  korunan blok: SAHTE KOPYA ile gizleme", "H8", m_h8b),
        ("M-H0d  zincir 0 BAYTA indirildi (tahrif maskeleme)", "H0", m_h0d),
        ("M-H0t  halka zamani GELECEGE alindi (hash yenilendi)", "H0", m_h0t),
    ]
    print("=== ISIRMA KANITI (kor kapi protokolu) ===")
    print("temiz surum: YESIL ✓ (yanlis-pozitif yok)\n")
    kacan = []
    for ad, kapi, fn in sinamalar:
        try:
            ok, k, c = mutant(ad, kapi, fn)
        except MutantKurulamadi as e:
            # TESTIN kendi hatasi — kapi hukmu DEGIL. Ayri raporlanir (Fable Bulgu 3).
            kurulamayan.append((ad, kapi, str(e)))
            print("  %-42s -> KURULAMADI (test hatasi, kapi hukmu degil)" % ad)
            continue
        except Exception as e:
            kurulamayan.append((ad, kapi, "beklenmeyen: %r" % (e,)))
            print("  %-42s -> KURULAMADI (beklenmeyen: %s)" % (ad, type(e).__name__))
            continue
        print("  %-42s -> %s" % (ad, "ISIRDI ✓" if ok else "KACTI ✗"))
        if not ok:
            kacan.append((ad, kapi, c[:400]))

    # ---- KOMUT SINAMALARI (kapi mutanti degil; komut davranisi) ----------
    komut_sinamalari = [
        ("M-KACIS CLI yol argumani kok DISINA (emekli/korunan)", "KACIS", k_kacis),
        ("M-KILIT kilit sahipligi (baskasinin kilidi)", "KILIT", k_kilit),
        ("M-AKLAMA silinmis/bos zincirle tahrif aklama", "AKLAMA", k_aklama),
        ("M-DEVIR yeniden capalama gizlenemiyor", "DEVIR", k_devir),
        ("M-KILITK kilit KAPSAMI (kur/devral kilit aliyor mu)", "KILIT", k_kilit_kapsam),
    ]
    for ad, etiket, fn in komut_sinamalari:
        try:
            ok, k, c = komut_sinamasi(ad, fn)
        except MutantKurulamadi as e:
            kurulamayan.append((ad, etiket, str(e)))
            print("  %-42s -> KURULAMADI (test hatasi, komut hukmu degil)" % ad)
            continue
        except Exception as e:
            kurulamayan.append((ad, etiket, "beklenmeyen: %r" % (e,)))
            print("  %-42s -> KURULAMADI (beklenmeyen: %s)" % (ad, type(e).__name__))
            continue
        print("  %-42s -> %s" % (ad, "ISIRDI ✓" if ok else "KACTI ✗"))
        if not ok:
            kacan.append((ad, etiket, c[:400]))

    if kurulamayan:
        print("\nKURULAMAYAN MUTANT (%d) — bunlar KAPI KORLUGU DEGIL, testin kendi eksigi:" % len(kurulamayan))
        for ad, kapi, sebep in kurulamayan:
            print("  %-42s [%s] %s" % (ad, kapi, sebep))
        print("  -> Bu kapilar bu projede SINANMADI; hukumleri 'OLCULMEDI'dir.")
    if kacan:
        print("\nSONUC: %d KAPI KOR — o kapilarin 'temiz' hukmu GECERSIZDIR." % len(kacan))
        for ad, kapi, c in kacan:
            print("\n--- %s (%s) ---\n%s" % (ad, kapi, c))
        return 1
    print("\n  %-42s -> SINANMADI (mutant kopyasina .git alinmiyor)" % "M-H9  git izlenirligi")
    kosulan = len(sinamalar) + len(komut_sinamalari) - len(kurulamayan)
    print("\nSONUC: %d/%d kosulan mutant ISIRIYOR · %d SINANMADI · H9 icin mutant YOK."
          % (kosulan, kosulan, len(kurulamayan)))
    # FABLE 3. TUR · B-7: "kurulamayan mutant" ile "kacan mutant" ayni cikis koduna
    # (1) katlaniyordu. Oysa ikisi TAMAMEN farkli hukumler: kacan mutant KAPI KORLUGU
    # (ciddi), kurulamayan mutant testin kendi on-kosulunun saglanmamasi. Taze bir
    # `kur` projesinde M-H1b kurulamaz (henuz `derle` kosulmamis) — bu SAGLIKLI bir
    # projedir, ama `isir && ...` diyen CI sarmalayicisi onu basarisiz etiketliyordu.
    # Artik: 0 = hepsi isirdi · 1 = KAPI KOR (kacan var) · 2 = olculemeyen mutant var.
    print("  CIKIS KODLARI: 0 hepsi isirdi · 1 KAPI KOR (kacan var) · "
          "2 olculemeyen mutant · 4 temiz surum zaten FAIL")
    if kurulamayan:
        return 2
    return 0

# ---------------------------------------------------------------- main

class _KirikBoruyaDayanikliAkis:
    """stdout sarmalayicisi: TUKETICI boruyu kapatinca komut COKMEZ, SUSAR.

    BAGIMSIZ DENETIM (v2.4 ic tur) — `os._exit(0)` UC ayri YUKSEK kusur uretti:
      (Y-2) `kapi | head`: rapor buyukse yazma ortasinda BrokenPipeError olusuyor,
            KIRMIZI kapi exit 0 donuyordu. Yani `| head` eklemek sahte YESIL uretiyor
            ve CI "dagitima uygun" saniyordu. Ustelik davranis cikti BOYUTUNA bagliydi.
      (Y-3) `derle | head`: yazma komutu is ORTASINDA olup exit 0 donuyordu; arsive
            yazilmis ama canliya islenmemis YARIM durum "basari" gorunuyordu.
      (Y-4) `os._exit` atexit'i atliyordu (kilit sizintisi; elle cagirarak kapatildi).
    Dogru cozum cikis kodunu degistirmek degil, kirik boruyu YAZMA KATMANINDA
    yutmaktir: komut kendi isini bitirir ve KENDI hukmunu (dogru cikis kodunu) verir.
    Boru koptuktan sonraki ciktiyi kimse okumuyor; sessizce devnull'a gider."""

    def __init__(self, akis):
        self._a = akis
        self._kirik = False

    def _dusur(self):
        self._kirik = True
        try:
            self._a = open(os.devnull, "w", encoding="utf-8")
        except OSError:
            self._a = None
        # Y-3 (Faz A, dokunus 2): boru koptugu ANDA alttaki fd'yi de devnull'a
        # cevir. Sebep: bu nesneyi degistirmek YETMIYOR — yorumlayici KAPANISTA
        # akislari yeniden flush eder ve o flush kopmus boruya giderse CPython
        # cikis kodunu 120'ye ZORLAR (Py_FinalizeEx basarisiz). Olculdu:
        # CI run #3, windows py3.11 -> `kapi | head` KIRMIZI iken [120,120,120].
        # fd devnull'a bakiyorsa kapanis flush'i artik patlayacak bir yere yazmaz.
        _bpe_sessizlestir()

    def write(self, s):
        if self._a is None:
            return len(s)
        try:
            return self._a.write(s)
        except (BrokenPipeError, ValueError):
            self._dusur(); return len(s)
        except OSError as e:
            if getattr(e, "errno", None) == _errno.EPIPE:
                self._dusur(); return len(s)
            raise

    def flush(self):
        if self._a is None:
            return
        try:
            self._a.flush()
        except (BrokenPipeError, ValueError):
            self._dusur()
        except OSError as e:
            if getattr(e, "errno", None) == _errno.EPIPE:
                self._dusur()
            else:
                raise

    def __getattr__(self, ad):
        return getattr(self._a, ad)

def _bpe_sessizlestir():
    """Yorumlayici kapanista stdout'u flush ederken ikinci bir hata basmasin."""
    try:
        _dn = os.open(os.devnull, os.O_WRONLY)
        os.dup2(_dn, sys.stdout.fileno())
    except (OSError, ValueError, AttributeError):
        pass


# Y-3: komutun HESAPLADIGI hukum. None = henuz hesaplanmadi.
# Boru koptugunda hukum ATILMAZ; `_guvenli_calistir` buradan geri alir.
_HUKUM = [None]


def _cikisi_guvenceye_al():
    """Y-3 (Faz A, dokunus 2) — hukum HESAPLANDIKTAN sonra, yorumlayici
    kapanisindan ONCE cagrilir. Bu noktadan sonra stdout'a yazilacak hicbir sey
    hukmu degistiremez; amac kapanistaki flush'in hukmu KAYBETTIRMESINI onlemek.

    Sira onemli: once FLUSH (boru saglamsa cikti gercekten gider; kopmussa
    sarmalayici yutar), SONRA fd devnull'a. Ters sirada bekleyen tampon
    devnull'a giderdi — yani kusuru duzeltirken CIKTIYI YUTARDIK."""
    for akis in (sys.stdout, sys.stderr):
        try:
            akis.flush()
        except Exception:                       # noqa: BLE001
            pass
    _bpe_sessizlestir()

def _cikti_kodlamasini_guvenceye_al():
    """Fable Bolum D: Windows'ta stdout konsol kod sayfasina (cp1254) duser ve
    ✓ / ✗ / → karakterleri orada YOKTUR -> yonlendirilmis ciktida UnicodeEncodeError
    ile COKER. reconfigure ile utf-8'e cekiyoruz; olmuyorsa errors='replace' ile
    en azindan cokmeyi engelliyoruz."""
    for akis in (sys.stdout, sys.stderr):
        try:
            akis.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            try:
                akis.reconfigure(errors="replace")
            except Exception:
                pass


def main():
    _cikti_kodlamasini_guvenceye_al()
    # Kirik boru artik YAZMA katmaninda yutulur; komut kendi hukmunu verir.
    if not isinstance(sys.stdout, _KirikBoruyaDayanikliAkis):
        sys.stdout = _KirikBoruyaDayanikliAkis(sys.stdout)
    # A-3 (PAKETLEME SONRASI IC DENETIM, v2.4.1): sarmalayici YALNIZ stdout'a
    # takilmisti. Oysa kodda 8 ayri `sys.stderr.write(` var ve bunlardan biri
    # (`yol_on_kontrol`un hardlink uyarisi) acikca "islem SURUYOR" diyen bir
    # NOT'tur. Olculdu: tuketicisi kapanmis bir stderr'de `not` komutu exit 0
    # yerine exit 2 veriyor ve FRAGMANI HIC YAZMIYORDU — yani "raporla,
    # durdurma" diyen bir uyari komutu tumden iptal ediyordu. Y-2/Y-3'un ta
    # kendisi, sadece oteki akista. Ustelik kendi testim bunu goremiyordu:
    # t_y42'nin Y-2/Y-3 senaryolari stderr=DEVNULL ile kosuyordu.
    if not isinstance(sys.stderr, _KirikBoruyaDayanikliAkis):
        sys.stderr = _KirikBoruyaDayanikliAkis(sys.stderr)
    ap = argparse.ArgumentParser(prog="hafiza.py",
                                 description="PROJE HAFIZA DUZENI v2 — tasinabilir motor")
    ap.add_argument("--kok", help="proje koku (yoksa HAFIZA_KOK ya da .hafizarc aranir)")
    alt = ap.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("kur", help="duzeni kurar (idempotent)")
    p.add_argument("--kok"); p.add_argument("--ad")
    p.set_defaults(fn=cmd_kur)

    p = alt.add_parser("devral", help="ilerlemis/mevcut sistemi olan projeyi v2'ye devralir")
    p.add_argument("--kok"); p.add_argument("--ad"); p.add_argument("--canli")
    p.set_defaults(fn=cmd_devral)

    p = alt.add_parser("bloklastir", help="devralinan bolumleri geriye donuk blok isaretine alir")
    p.add_argument("--kok"); p.add_argument("--uygula", action="store_true")
    p.set_defaults(fn=cmd_bloklastir)

    p = alt.add_parser("not", help="gunluk/ altina fragman yazar")
    p.add_argument("--kok"); p.add_argument("--konu", required=True)
    p.add_argument("--tur", default="durum")
    p.add_argument("--metin"); p.add_argument("--oturum")
    p.add_argument("--yeni-konu", dest="yeni_konu",
                   help="konu sozlukte yoksa: aciklamasiyla birlikte ekler")
    p.set_defaults(fn=cmd_not)

    p = alt.add_parser("derle", help="fragmanlari canliya isler, sonra arsive tasir")
    p.add_argument("--kok")
    p.add_argument("--bos-serbest", dest="bos_serbest", action="store_true",
                   help="hic fragman yoksa hata verme (bilincli bos tur)")
    p.set_defaults(fn=cmd_derle)

    p = alt.add_parser("emekli", help="canlidan arsive byte-birebir tasir (geri alinabilir)")
    p.add_argument("--kok"); p.add_argument("aralik")
    p.add_argument("--hedef"); p.add_argument("--not", dest="not_")
    p.set_defaults(fn=cmd_emekli)

    p = alt.add_parser("karar", help="yeni ADR acar")
    p.add_argument("--kok"); p.add_argument("--baslik", required=True)
    p.add_argument("--konu"); p.add_argument("--yerine")
    p.set_defaults(fn=cmd_karar)

    p = alt.add_parser("muhur", help="defter degisikligini zincire muhurler")
    p.add_argument("--kok"); p.add_argument("gerekce")
    p.set_defaults(fn=cmd_muhur)

    p = alt.add_parser("korunan", help="bir blogu KORUNAN ilan eder (H8)")
    p.add_argument("--kok"); p.add_argument("--dosya", required=True)
    p.add_argument("--bas", required=True); p.add_argument("--son", required=True)
    p.add_argument("--gerekce", required=True)
    p.set_defaults(fn=cmd_korunan)

    p = alt.add_parser("kapi", help="H0..H13 kapilarini kosar")
    p.add_argument("--kok"); p.add_argument("--siki", action="store_true")
    p.set_defaults(fn=cmd_kapi)

    p = alt.add_parser("isir", help="kapilarin isirdigini mutantla kanitlar")
    p.add_argument("--kok"); p.set_defaults(fn=cmd_isir)

    a = ap.parse_args()
    # Y-3: hukum ONCE hesaplanir ve KAYDEDILIR, sonra cikis guvenceye alinir,
    # EN SON cikilir. Eskiden tek satirdi (`sys.exit(a.fn(a) or 0)`) ve hukum
    # yorumlayici kapanisina kadar korumasiz kaliyordu.
    _HUKUM[0] = a.fn(a) or 0
    _cikisi_guvenceye_al()
    sys.exit(_HUKUM[0])


def _guvenli_calistir():
    """SON AG — BAGIMSIZ DENETIMIN IKINCI TURUNUN DERSI.

    Y-3'te "ham traceback sinifi kapandi" DEDIM; yanlisti. Bilinen yuzeyleri tek tek
    sarmak SINIFI kapatmaz — ayni ders (K-7 / L6351) ucuncu kez, farkli kilikta.
    Bir sinif ancak SINIRDA kapatilir. Burasi o sinir: hicbir istisna kullaniciya
    ham traceback olarak gitmez.

    Ama HATA YUTULMAZ: tam iz bir dosyaya yazilir, yolu ekranda soylenir. Ciplak
    'except' ile susmak, ham traceback'ten daha kotu olurdu."""
    try:
        main()
    except SystemExit:
        raise                                   # oldur()/sys.exit — zaten temiz hukum
    except KeyboardInterrupt:
        sys.stderr.write("\nIPTAL EDILDI (Ctrl-C). Yarim kalan islem olabilir; "
                         "once: python hafiza.py kapi\n")
        sys.exit(130)
    except BrokenPipeError:
        # SON CARE. Normalde buraya HIC gelinmez: stdout `_KirikBoruyaDayanikliAkis`
        # ile sarilidir ve yazma hatasini yutup devnull'a gecer, komut TAMAMLANIR.
        # Buraya gelinirse hukum BILINMIYOR demektir; 0 DONMEYIZ (asagiyi oku).
        _bpe_sessizlestir()
        # Y-3 (Faz A, dokunus 2): hukum HESAPLANMISSA boru onu DEGISTIREMEZ.
        # Olculdu (CI run #3/#4, windows py3.13): `kapi | head` KIRMIZI iken
        # [3,3,3] donuyordu — yani GERCEK bir bulgu "ARAC KUSURU"na cevriliyordu.
        # Ayni sinif Linux'ta sarmalayici sokulerek birebir uretildi
        # (faz0/boru_probu.py sabotaji): borusuz=1, boruyla [3,3,3,3].
        if _HUKUM[0] is not None:
            sys.exit(_HUKUM[0])
        # A-2 (v2.4.1): hukum GERCEKTEN bilinmiyor (komut daha bitmemisti) —
        # bu bir kullanim hatasi (2) degil, OLCUM YAPILAMADI halidir.
        sys.exit(3)
    except RecursionError:
        # json ayristiricisi asiri ic-ice girdide boyle atar
        try:
            oldur("GIRDI COK DERIN IC ICE — ayristirilamadi (defter ya da yapilandirma "
                  "makul olmayan derinlikte). Dosyayi yedekten geri al.")
        except SystemExit:
            raise
        except BaseException:
            sys.exit(2)             # stderr yazilamiyorsa bile TEMIZ cikis kodu
    except BaseException as _hata:
        # KENDI ACTIGIMIZ REGRESYON (bagimsiz denetim, v2.4 ic tur):
        # `except OSError: ... raise` ayri bir dal olarak yazilmisti; oradaki `raise`
        # bir SONRAKI dala DUSMEZ, TRY'DAN DISARI CIKAR. Sonuc: EROFS/EACCES/ELOOP/
        # EIO gibi butun OSError'lar ham traceback olarak kullaniciya gitti ve son
        # agin kendi sozu ("hicbir istisna ham traceback olarak gitmez") YALAN oldu.
        # Ders: son agin ICINDE dallan, sinirda ASLA `raise` etme.
        if isinstance(_hata, OSError) and getattr(_hata, "errno", None) == _errno.ENOSPC:
            try:
                sys.stderr.write(
                    "HATA: DISK DOLU (ENOSPC) — islem tamamlanamadi.\n"
                    "  Bu bir ARAC kusuru degil; yazacak yer kalmamis.\n"
                    "  DIKKAT: yazma YARIDA kalmis olabilir; bu mesaj hicbir sey "
                    "vaat ETMEZ.\n"
                    "  Yer acip once durumu OLC: python hafiza.py kapi\n")
            except BaseException:
                pass
            sys.exit(3)
        iz = _tb.format_exc()
        try:
            kayit_p = os.path.join(os.getcwd(), "hafiza_hata_izi.txt")
            with open(kayit_p, "w", encoding="utf-8", newline="\n") as f:
                f.write("hafiza.py %s · %s\nkomut: %s\n\n%s"
                        % (SURUM, _dt.datetime.now().isoformat(timespec="seconds"),
                           " ".join(sys.argv[1:]), iz))
        except OSError:
            kayit_p = None
        son = [s for s in iz.strip().split("\n") if s.strip()][-1]
        try:
            _yaz_hata(son, kayit_p)
        except BaseException:
            pass                    # stderr yazilamiyorsa bile TEMIZ cikis kodu ver
        # A-2 (v2.4.1): BEKLENMEYEN IC HATA ve IZIN HATASI (EACCES/EPERM/EROFS…)
        # buradan cikiyordu ve exit 2 — yani "kullanim hatasi" — veriyordu.
        # Belge ise "3 = olcum yapilamadi (disk dolu, IZIN YOK, beklenmeyen ic
        # hata)" diyordu. Uc halin ucu de ayni sinif: ISLEM TAMAMLANAMADI, HUKUM
        # YOK. 2 artik yalniz `oldur()`un verdigi TEMIZ KULLANIM/GIRDI hukmudur.
        sys.exit(3)

def _yaz_hata(son, kayit_p):
    sys.stderr.write(
            "HATA: BEKLENMEYEN DURUM — bu bir ARAC KUSURUDUR, senin dosyalarinin hukmu degil.\n"
            "  %s\n"
            "  DIKKAT: islem YARIDA kesildi. Dosyalarin DEGISMIS OLABILIR — bu mesaj\n"
            "  hicbir sey vaat ETMEZ. Ilk is: python hafiza.py kapi\n%s"
            % (son[:200],
               ("  Tam iz: %s\n" % kayit_p) if kayit_p else "  (iz dosyasi yazilamadi)\n"))

if __name__ == "__main__":
    import atexit
    atexit.register(kilit_birak)                # cikis yolu ne olursa olsun kilit birakilir
    _guvenli_calistir()
