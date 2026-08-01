#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Y-2 MUTANTI — "cikti kodlamasi korumasi" GERCEKTEN isiriyor mu?

NEYI OLCER
  t_y42.py ve t_y3.py'ye Faz A-0'da eklenen `_cikti_kodlamasini_guvenceye_al()`
  korumasini SOKER ve kosucuyu tek-baytli bir kod sayfasi altinda kosar.
  Koruma gercekten isiriyorsa mutant kopya COKER ve hukum satirini BASAMAZ.
  Isirmiyorsa mutant KACAR -> kapi kordur.

NEDEN GEREKLI (olculdu, CI run #2 / f6f7fde)
  windows-latest py3.11 ve py3.13'te t_y42 58 senaryonun TAMAMINI kostu
  (91 sn / 110 sn) ve rapor dongusunun ILK satirinda coktu:
      t_y42.py:1586  UnicodeEncodeError: 'charmap' codec can't encode
                     character '\\u0131' in position 67
  58 hukmun tamami basilmadan kayboldu, `continue-on-error` yuttu, is YESIL
  kaldi. Yani capraz olcumun 1/3'u (Windows) davranis kanitlari acisindan
  KORDU ve bu korluk YESIL TIK olarak gorunuyordu.

KOD SAYFASI SECIMI TESADUFI DEGIL (kosucularin ciktisi tarandi):
      U+0131 'i'(noktasiz)  cp1252=YOK  cp1254=VAR  cp850=VAR  cp437=YOK
      U+2014 em-dash        cp1252=VAR  cp1254=VAR  cp850=YOK  cp437=YOK
  -> t_y42 kolu cp1252 ile olculur (noktasiz i orada yok; CI'daki gercek kusur).
  -> t_y3  kolu cp850  ile olculur (t_y3'un ciktisinda noktasiz i YOK, em-dash
     VAR; cp1252'de sansla ayakta kalir. Sansa dayali ayaktalik "temiz" degildir,
     bu yuzden t_y3 kendi kirilma noktasiyla olculur.)

OLU TUZAK KONTROLU
  Ayni mutant cp1254 (Turkce Windows) altinda KACAR — cunku noktasiz i orada
  vardir. Bu bir kusur degil, olcumun SINIRIDIR ve boyle raporlanir. Onur'un
  kendi Turkce Windows'unda kusurun gorunmemesinin sebebi de tam olarak budur.

CIKIS KODLARI (projenin sozlesmesi)
  0  kurulan her mutant ISIRDI
  1  en az bir mutant KACTI  -> koruma kor
  2  en az bir mutant OLCULEMEDI (kurulamadi / atlandi)
  3  ARAC KUSURU (mutant kurulamadi, hukum verilemez)

KULLANIM
  python3 faz0/y2_mutant.py           # tam olcum  (~3 dk, t_y42 3 kez kosar)
  python3 faz0/y2_mutant.py --hizli   # yalniz t_y3 kollari (~10 sn)
                                      # t_y42 kollari OLCULEMEDI sayilir, PASS degil
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile


def _cikti_kodlamasini_guvenceye_al():
    """Bu betigin KENDI raporu da ayni sinifta kaybolmasin diye."""
    for akis in (sys.stdout, sys.stderr):
        try:
            akis.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            try:
                akis.reconfigure(errors="replace")
            except Exception:
                pass


_cikti_kodlamasini_guvenceye_al()

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KAYNAK = os.path.join(KOK, "skill", "scripts")

# Korumanin cagri satiri. Mutant TAM OLARAK bunu soker.
CAGRI = "_cikti_kodlamasini_guvenceye_al()"
ISARET = "# Y-2 KORUMASI"

SONUC = []          # (ad, isirdi: True/False/None, ayrinti)


def kayit(ad, isirdi, ayrinti):
    SONUC.append((ad, isirdi, ayrinti))


class MutantKurulamadi(Exception):
    pass


def hazirla(hedef, sok):
    """skill/scripts'i hedefe kopyalar. sok=True ise Y-2 korumasini kaldirir."""
    os.makedirs(hedef, exist_ok=True)
    for ad in ("hafiza.py", "t_y3.py", "t_y42.py"):
        shutil.copy2(os.path.join(KAYNAK, ad), os.path.join(hedef, ad))
    if not sok:
        return
    for ad in ("t_y3.py", "t_y42.py"):
        p = os.path.join(hedef, ad)
        with open(p, encoding="utf-8") as f:
            metin = f.read()
        # 1) modul duzeyindeki CAGRI satirini sok
        yeni, n = re.subn(
            r"(?m)^" + re.escape(CAGRI) + r"\s*" + re.escape(ISARET) + r".*$",
            "pass  # MUTANT: Y-2 korumasi sokuldu",
            metin,
        )
        if n != 1:
            raise MutantKurulamadi(
                "%s icinde '%s   %s' cagri satiri bulunamadi (n=%d). "
                "Koruma tasindiysa MUTANT DA TASINMALI." % (ad, CAGRI, ISARET, n)
            )
        # 2) govdedeki reconfigure'lari da etkisizlestir ki koruma gercekten olsun
        yeni = yeni.replace("akis.reconfigure(", "_MUTANT_NOOP(")
        yeni = yeni.replace(
            "import os, sys",
            "def _MUTANT_NOOP(*a, **k):\n    raise RuntimeError('mutant')\nimport os, sys",
            1,
        )
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(yeni)
        # 3) sabotaj gercekten oturdu mu -> KANIT
        with open(p, encoding="utf-8") as f:
            k = f.read()
        if "akis.reconfigure(" in k or (CAGRI + "   " + ISARET) in k:
            raise MutantKurulamadi("%s: sabotaj oturmadi, koruma hala ayakta" % ad)


def kos(betik, dizin, kod_sayfasi, saniye=900):
    ortam = dict(os.environ)
    ortam["PYTHONIOENCODING"] = kod_sayfasi
    ortam.pop("PYTHONUTF8", None)          # -X utf8 / PYTHONUTF8 olcumu bosa cikarirdi
    ortam["PYTHONUTF8"] = "0"
    r = subprocess.run(
        [sys.executable, betik],
        cwd=dizin, capture_output=True, timeout=saniye,
        env=ortam,
    )
    cikti = (r.stdout or b"").decode("utf-8", "replace") + \
            (r.stderr or b"").decode("utf-8", "replace")
    return r.returncode, cikti


HUKUM_DESENI = {
    "t_y42.py": re.compile(r"^SONUC: \d+ gecti", re.M),
    "t_y3.py": re.compile(r"^SONUC: \d+/\d+ senaryo TEMIZ HATA", re.M),
}


def olc(ad, betik, kod_sayfasi, temiz_dizin, mutant_dizin):
    """Once TEMIZ kopyanin hukmunu basabildigini, sonra MUTANTIN basamadigini olcer."""
    try:
        rc_t, ct = kos(betik, temiz_dizin, kod_sayfasi)
    except subprocess.TimeoutExpired:
        kayit(ad, None, "TEMIZ kopya zaman asimina ugradi — olculemedi")
        return
    temiz_hukum = bool(HUKUM_DESENI[betik].search(ct))
    if not (rc_t == 0 and temiz_hukum):
        kayit(ad, None,
              "TEMIZ kopya %s altinda hukum BASAMADI (exit=%d, hukum=%s) — "
              "koruma calismiyor ya da baska bir kusur var; mutant anlamsiz"
              % (kod_sayfasi, rc_t, temiz_hukum))
        return
    try:
        rc_m, cm = kos(betik, mutant_dizin, kod_sayfasi)
    except subprocess.TimeoutExpired:
        kayit(ad, None, "MUTANT zaman asimina ugradi — olculemedi")
        return
    mutant_hukum = bool(HUKUM_DESENI[betik].search(cm))
    coktu = ("UnicodeEncodeError" in cm)
    isirdi = (not mutant_hukum) and rc_m != 0
    kayit(ad, isirdi,
          "TEMIZ: exit=%d hukum=VAR | MUTANT: exit=%d hukum=%s%s"
          % (rc_t, rc_m, "VAR" if mutant_hukum else "YOK",
             " (UnicodeEncodeError)" if coktu else ""))


def olu_tuzak(betik, kod_sayfasi, mutant_dizin):
    """Mutantin OLU oldugu ortami olcer. Hukum degil, olcumun SINIRIDIR."""
    try:
        rc, c = kos(betik, mutant_dizin, kod_sayfasi)
    except subprocess.TimeoutExpired:
        return "%s @ %s: zaman asimi" % (betik, kod_sayfasi)
    var = bool(HUKUM_DESENI[betik].search(c))
    return ("%s @ %s: mutant exit=%d hukum=%s -> mutant bu kod sayfasinda %s"
            % (betik, kod_sayfasi, rc, "VAR" if var else "YOK",
               "OLU (kacar)" if var else "canli (isirir)"))


def main():
    hizli = "--hizli" in sys.argv
    print("=" * 78)
    print("Y-2 MUTANTI — cikti kodlamasi korumasi isiriyor mu?")
    print("  python  : %s" % sys.version.split()[0])
    print("  kaynak  : %s" % KAYNAK)
    print("  mod     : %s" % ("HIZLI (yalniz t_y3)" if hizli else "TAM"))
    print("=" * 78)

    gecici = tempfile.mkdtemp(prefix="y2_")
    temiz = os.path.join(gecici, "temiz")
    mutant = os.path.join(gecici, "mutant")
    try:
        try:
            hazirla(temiz, sok=False)
            hazirla(mutant, sok=True)
        except MutantKurulamadi as e:
            print("\nARAC KUSURU: %s" % e)
            print("Hukum VERILEMEZ. Bu bir kapi hukmu degil, mutantin kendi kusurudur.")
            return 3

        olc("t_y3  @ cp850  (em-dash orada YOK)", "t_y3.py", "cp850", temiz, mutant)
        if hizli:
            kayit("t_y42 @ cp1252 (noktasiz i orada YOK)", None,
                  "--hizli ile ATLANDI — PASS DEGIL, OLCULEMEDI")
            notlar = ["--hizli: olu tuzak olcumu de atlandi"]
        else:
            olc("t_y42 @ cp1252 (noktasiz i orada YOK)", "t_y42.py", "cp1252",
                temiz, mutant)
            notlar = [olu_tuzak("t_y42.py", "cp1254", mutant)]

        print()
        isiran = kacan = olculemeyen = 0
        for ad, isirdi, ayrinti in SONUC:
            if isirdi is None:
                d = "OLCULEMEDI"; olculemeyen += 1
            elif isirdi:
                d = "ISIRDI    "; isiran += 1
            else:
                d = "KACTI     "; kacan += 1
            print("  %s %-42s | %s" % (d, ad, ayrinti))

        print()
        print("OLCUMUN SINIRI (hukum degil):")
        for n in notlar:
            print("  - %s" % n)

        print()
        print("-" * 78)
        print("SONUC: %d isirdi - %d kacti - %d olculemedi (toplam %d)"
              % (isiran, kacan, olculemeyen, len(SONUC)))
        if kacan:
            return 1
        if olculemeyen:
            return 2
        return 0
    finally:
        shutil.rmtree(gecici, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
