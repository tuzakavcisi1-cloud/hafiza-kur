#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Y-3 PROBU — kirik boru HUKMU nerede ve NASIL kaybediyor?

NEDEN VAR (olculdu, CI run #3 ve #4)
  `kapi` KIRMIZI (borusuz exit 1) iken `| head` eklenince:
      run #3  windows py3.11 -> [120, 120, 120]
      run #3  windows py3.13 -> [  3,   3,   3]
      run #4  windows py3.11 -> [  1,   1,   1]   <-- DUZELMEDI, MASKELENDI
      run #4  windows py3.13 -> [  3,   3,   3]
      her kosumda linux/macos -> [  1,   1,   1]
  run #4'te Y-3'e HIC dokunulmadi; tek fark SURUM dizesinin "2.4.1" -> "2.5.0-dev"
  olmasi, yani `kapi` ciktisinin ILK SATIRININ 4 BAYT UZAMASIYDI. Dort bayt, boru
  kopma noktasini tampon sinirinin obur tarafina itti. `_KirikBoruyaDayanikliAkis`
  docstring'i bunu zaten yaziyordu: "davranis cikti BOYUTUNA bagliydi."
  Yani Y-3 DETERMINIST DEGIL ve "GECTI" gormek "kapandi" DEMEK DEGILDIR.

  Iki cikis kodu iki AYRI mekanizmaya isaret ediyor:
    120 = CPython'un Py_FinalizeEx'i basarisiz oldugunda ZORLADIGI koddur
          (yorumlayici KAPANISINDA stdout flush'i cokuyor)
    3   = hafiza.py'nin kendi ARAC KUSURU kodu; `_guvenli_calistir`in
          `except BrokenPipeError` dali. Yani istisna sarmalayiciyi ASIP
          main()'in DISINA cikiyor.
  Tek bir duzeltme ikisini de kapatmayabilir. Once mekanizma OLCULMELIDIR.

NEDEN MEVCUT TESTLER BUNU GOREMEDI
  t_y42'nin "Y-2" senaryosu alt sureci `stderr=subprocess.DEVNULL` ile kosuyor.
  Oysa "Exception ignored in: ..." ve ham traceback O KANALA basilir.
  CLAUDE.md 3: "Bir kanali DEVNULL'a atan test, o kanaldaki sinifi OLCEMEZ."
  Bu prob stderr'i OKUR.

BU BETIK KODA DOKUNMAZ. Olcer ve rapor eder.
Cikis kodu:  0 = bu ortamda hukum boruya bagli DEGIL (tuzak yok)
             1 = hukum boruya BAGLI (tuzak var) — mekanizma raporda
             2 = OLCULEMEDI (prob kendi coktu / hafiza.py bulunamadi)
"""
import os
import re
import subprocess
import sys
import tempfile

CIZGI = "-" * 78


def _cikti_kodlamasini_guvenceye_al():
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
MOTOR = os.path.join(KOK, "skill", "scripts", "hafiza.py")
PY = sys.executable
BULGULAR = []       # ARACIN kusuru — hukmu belirler
ORTAM = []          # ORTAMIN gercegi — hukum DEGIL (bkz. win_kill_probu dersi)
SINIRLAR = []       # olculemeyenler


def yaz(s=""):
    print(s, flush=True)


def boruyu_kopar(argv, oku_satir, ortam=None, cwd=None):
    """Komutu calistirir, stdout'tan oku_satir satir okur, boruyu KAPATIR.
    `head -n` taklidi. stderr DEVNULL DEGIL: teshis mesajlari oradadir."""
    pr = subprocess.Popen(
        argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=cwd, env=ortam,
    )
    try:
        for _ in range(oku_satir):
            if not pr.stdout.readline():
                break
    finally:
        try:
            pr.stdout.close()
        except OSError:
            pass
    hata = pr.stderr.read() or b""
    pr.stderr.close()
    pr.wait()
    return pr.returncode, hata.decode("utf-8", "replace")


# ---------------------------------------------------------------------------
# KOL A — SAF PYTHON TEMELI (hafiza.py YOK)
#   Amac: "bu ortamda Python'un KENDISI ne yapiyor?" sorusunu aracin
#   kusurundan AYIRMAK. Arac duzelse de bu kol degismez; degisirse ortam degismistir.
# ---------------------------------------------------------------------------
SAF = (
    "import sys\n"
    "for i in range(%d):\n"
    "    print('satir %%06d ' %% i + 'x' * 60)\n"
    "sys.exit(7)\n"
)

SAF_KORUMALI = (
    "import os, sys\n"
    "class S:\n"
    "    def __init__(s, a): s._a = a\n"
    "    def write(s, t):\n"
    "        try: return s._a.write(t)\n"
    "        except (BrokenPipeError, ValueError, OSError):\n"
    "            s._a = open(os.devnull, 'w'); return len(t)\n"
    "    def flush(s):\n"
    "        try: s._a.flush()\n"
    "        except (BrokenPipeError, ValueError, OSError):\n"
    "            s._a = open(os.devnull, 'w')\n"
    "    def __getattr__(s, n): return getattr(s._a, n)\n"
    "sys.stdout = S(sys.stdout)\n"
    "for i in range(%d):\n"
    "    print('satir %%06d ' %% i + 'x' * 60)\n"
    "sys.exit(7)\n"
)

SAF_KORUMALI_FD = SAF_KORUMALI.replace(
    "sys.exit(7)\n",
    "try: sys.stdout.flush()\n"
    "except Exception: pass\n"
    "try:\n"
    "    _dn = os.open(os.devnull, os.O_WRONLY); os.dup2(_dn, 1)\n"
    "except Exception: pass\n"
    "sys.exit(7)\n",
)


def kol_a():
    yaz("[A] SAF PYTHON — hukum (exit 7) boruya bagli mi? hafiza.py YOK")
    for ad, kod in (("ciplak         ", SAF),
                    ("sarmalayicili  ", SAF_KORUMALI),
                    ("sarmalayici+fd ", SAF_KORUMALI_FD)):
        satirlar = []
        for n in (2000, 20000):
            rc, err = boruyu_kopar([PY, "-c", kod % n], 1)
            ignored = "Exception ignored" in err
            satirlar.append("%d satir -> exit=%s%s" % (n, rc, " (Exception ignored)" if ignored else ""))
            if ad.strip() == "ciplak" and rc != 7:
                # HUKUM DEGIL: ciplak Python'un korumamasi BEKLENEN durumdur —
                # `_KirikBoruyaDayanikliAkis`in var olma sebebi tam da budur.
                # Bunu bulgu saymak, aracin kusuru olmayan bir seyi ona yuklerdi
                # (y2_mutant'in run #3'te dustugu hatanin aynisi: iki ayri soruyu
                # tek hukumde birlestirmek).
                ORTAM.append(
                    "ciplak Python exit 7'yi KORUMUYOR (%s donuyor, %d satir). "
                    "Beklenen: hukmu koruma isi TAMAMEN aracin uzerindedir." % (rc, n))
            if ad.strip() == "sarmalayicili" and rc != 7:
                BULGULAR.append(
                    "SARMALAYICI YETMIYOR: yalniz write/flush sarmak exit 7'yi korumuyor "
                    "(%s, %d satir). Kayip YAZMA katmaninda degil, KAPANIS katmanindadir." % (rc, n))
            if ad.strip() == "sarmalayici+fd" and rc != 7:
                BULGULAR.append(
                    "fd->devnull DE YETMIYOR: exit 7 hala korunmuyor (%s, %d satir). "
                    "Onerilen Y-3 duzeltmesi bu ortamda TEK BASINA yeterli DEGIL." % (rc, n))
        yaz("    %s : %s" % (ad, "  |  ".join(satirlar)))
    yaz()


# ---------------------------------------------------------------------------
# KOL B — HAFIZA.PY: gercek komut, stderr OKUNUR
# ---------------------------------------------------------------------------
def kirmizi_proje():
    """kapi'yi KIRMIZI yapan taze proje kurar; kok yolunu doner."""
    d = tempfile.mkdtemp(prefix="boru_")
    kok = os.path.join(d, "p")
    os.makedirs(kok)
    r = subprocess.run([PY, "-X", "utf8", MOTOR, "kur", "--kok=" + kok, "--ad", "BORU"],
                       capture_output=True)
    if r.returncode != 0:
        raise RuntimeError("kur basarisiz: " + (r.stderr or b"").decode("utf-8", "replace")[:200])
    p = os.path.join(kok, "PROJE_HAFIZA.md")
    with open(p, encoding="utf-8") as f:
        L = f.read().split("\n")
    i = next((i for i, s in enumerate(L) if s.startswith("## GUNCEL") or "GÜNCEL" in s), 2)
    L = L[:i + 2] + ["- PAZARLIKSIZ: kural %d yanlis evde duruyor." % n
                     for n in range(200)] + L[i + 2:]
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))
    return kok


def kol_b(kok):
    ortam = dict(os.environ, PYTHONIOENCODING="utf-8")
    rc0 = subprocess.run([PY, "-X", "utf8", MOTOR, "kapi", "--kok=" + kok],
                         capture_output=True, env=ortam).returncode
    yaz("[B] HAFIZA.PY — `kapi` borusuz exit=%d (KIRMIZI bekleniyor)" % rc0)
    if rc0 == 0:
        SINIRLAR.append("kapi borusuz 0 dondu — proje KIRMIZI degil, B kolu anlamsiz")
        yaz("    proje KIRMIZI olmadi; bu kol OLCULEMEDI")
        yaz()
        return None
    kodlar, izler = [], []
    for n in (1, 3, 5, 20):
        rc, err = boruyu_kopar([PY, "-X", "utf8", MOTOR, "kapi", "--kok=" + kok], n, ortam)
        kodlar.append(rc)
        etiket = []
        if "Exception ignored" in err:
            etiket.append("Exception-ignored")
        if "Traceback" in err:
            etiket.append("TRACEBACK")
        m = re.search(r"(BrokenPipeError|OSError|ValueError)[^\n]{0,60}", err)
        if m:
            etiket.append(m.group(0).strip()[:58])
        izler.append("head -%-2d exit=%-4s %s" % (n, rc, " ".join(etiket) or "stderr temiz"))
    for s in izler:
        yaz("    " + s)
    if any(k != rc0 for k in kodlar):
        BULGULAR.append(
            "HUKUM BORUYA BAGLI: borusuz=%d ama boruyla %s. Gercek KIRMIZI hukum "
            "kayboluyor ve yerine baska bir kod geciyor." % (rc0, kodlar))
    if 120 in kodlar:
        BULGULAR.append(
            "MEKANIZMA-120: CPython Py_FinalizeEx basarisiz -> cikis kodu 120'ye "
            "ZORLANIYOR. Kayip YORUMLAYICI KAPANISINDA; write/flush sarmak yetmez, "
            "fd kapanistan ONCE devnull'a cevrilmelidir.")
    if 3 in kodlar:
        BULGULAR.append(
            "MEKANIZMA-3: istisna sarmalayiciyi ASIP main()'in disina cikiyor ve "
            "`_guvenli_calistir`in `except BrokenPipeError` dali exit 3 (ARAC KUSURU) "
            "veriyor. Hukum HESAPLANMIS olsa bile atiliyor.")
    yaz()
    return rc0


# ---------------------------------------------------------------------------
# KOL C — TAMPON YARISI: cikti BOYUTU hukmu degistiriyor mu?
#   run #4'un tesadufi yesilini kayda gecirir.
# ---------------------------------------------------------------------------
def kol_c(kok, rc0):
    if rc0 is None:
        yaz("[C] TAMPON YARISI — B kolu olculemedigi icin ATLANDI")
        yaz()
        return
    yaz("[C] TAMPON YARISI — ilk satiri N bayt uzatinca hukum degisiyor mu?")
    ortam = dict(os.environ, PYTHONIOENCODING="utf-8")
    kodlar = {}
    for dolgu in (0, 4, 64, 512, 4096):
        o = dict(ortam)
        o["HAFIZA_BORU_PROBU_DOLGU"] = "x" * dolgu     # motor okumaz; ortami buyutur
        rc, _ = boruyu_kopar([PY, "-X", "utf8", MOTOR, "kapi", "--kok=" + kok], 1, o)
        kodlar[dolgu] = rc
    yaz("    dolgu->exit : %s" % ", ".join("%d->%s" % (k, v) for k, v in kodlar.items()))
    farkli = len(set(kodlar.values())) > 1
    if farkli:
        BULGULAR.append(
            "TAMPON YARISI KANITLANDI: ayni proje, ayni komut, YALNIZ cikti/ortam boyutu "
            "degisti ve cikis kodu degisti (%s). Yani bu kusurun 'GECTI' gorunmesi "
            "duzeltmenin degil, boyut tesadufunun sonucu olabilir." % kodlar)
    else:
        SINIRLAR.append(
            "tampon yarisi bu ortamda URETILEMEDI (tum dolgularda exit %s). "
            "run #4'te py3.11'de gozlenen degisim burada yeniden uretilemedi; "
            "OLCULEMEDI, 'yok' DEMEK DEGIL." % list(kodlar.values())[0])
    yaz()


def main():
    yaz(CIZGI)
    yaz("Y-3 PROBU — kirik boru HUKMU kaybediyor mu?")
    yaz("platform : %s" % sys.platform)
    yaz("python   : %s" % sys.version.split()[0])
    yaz("motor    : %s" % MOTOR)
    yaz(CIZGI)
    if not os.path.isfile(MOTOR):
        yaz("hafiza.py bulunamadi. SONUC: OLCULEMEDI (exit 2)")
        return 2
    kol_a()
    kok = None
    try:
        kok = kirmizi_proje()
        rc0 = kol_b(kok)
        kol_c(kok, rc0)
    except Exception as e:                                   # noqa: BLE001
        yaz("PROB KOL B/C COKTU: %s: %s" % (type(e).__name__, e))
        SINIRLAR.append("B/C kollari kosulamadi: %s" % type(e).__name__)
    finally:
        if kok:
            import shutil
            shutil.rmtree(os.path.dirname(kok), ignore_errors=True)

    yaz(CIZGI)
    yaz("BULGULAR (ARACIN kusuru — hukmu belirler)")
    if BULGULAR:
        for b in BULGULAR:
            yaz("  * " + b)
    else:
        yaz("  (yok — bu ortamda hukum boruya bagli DEGIL)")
    if ORTAM:
        yaz()
        yaz("ORTAM GERCEGI (hukum DEGIL)")
        for o in ORTAM:
            yaz("  - " + o)
    if SINIRLAR:
        yaz()
        yaz("OLCUMUN SINIRI (hukum degil)")
        for s in SINIRLAR:
            yaz("  - " + s)
    yaz(CIZGI)
    if BULGULAR:
        yaz("SONUC: HUKUM BORUYA BAGLI — tuzak bu ortamda VAR. (exit 1)")
        yaz("  Not: bu bir ORTAM+ARAC olcumudur. Y-3 duzeltmesi tuttuysa B kolundaki")
        yaz("  tum kodlar borusuz koda ESIT olmalidir.")
        return 1
    yaz("SONUC: hukum boruya bagli degil — bu ortamda tuzak YOK. (exit 0)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:                                   # noqa: BLE001
        yaz("PROB KENDISI COKTU: %s: %s" % (type(e).__name__, e))
        yaz("SONUC: OLCULEMEDI (exit 2)")
        sys.exit(2)
