#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FAZ 0 — Y-1 PROBU:  os.kill(pid, 0) Windows'ta VARLIK SINAR mi, yoksa ATES mi eder?

HIPOTEZ (belge kanitli, olcum yok):
  hafiza.py:723 `_surec_yasiyor` bayat kilit teshisi icin `os.kill(pid, 0)` kullaniyor
  ve `except (OSError, AttributeError)` ile korunmus — yani yazar bir ISTISNA bekliyor.
  Windows'ta ise:
    * bpo-14480 "os.kill on Windows should accept zero as signal" -> CLOSED-REJECTED.
      Victor Stinner: "0 has no special meaning on Windows ... 0 unfortunately already
      means two things as it is: signal.CTRL_C_EVENT and the int 0."
    * Brian Curtin: "we currently take all integers to be passed to TerminateProcess
      ... and two signals to pass to GenerateConsoleCtrlEvent."
    * Microsoft, GenerateConsoleCtrlEvent: "CTRL+C signals cannot be limited to a
      specific process group -- broadcast to all processes sharing the console."
  Yani cagri ISTISNA ATMAYABILIR ve VARLIK SINAMAZ.

NEDEN ONEMLI:
  Bu kod yolu tam olarak KILIT CAKISMASI aninda kosuyor — yani oteki hafiza.py
  YAZMA ORTASINDAYKEN. En kotu hal: bayat kilit teshisi, teshis ettigi yaziciyi
  yarida kesiyor; kilidin var olma sebebi olan KAYIP GUNCELLEME'yi kilidin kendisi
  uretiyor.

BU BETIK KODA DOKUNMAZ. Yalniz olcer ve rapor eder.
Cikis kodu:  0 = hipotez CURUTULDU (kod guvende)  ·  1 = hipotez DOGRULANDI (kusur)
             2 = OLCULEMEDI
"""
import os
import subprocess
import sys
import time

CIZGI = "-" * 78


def yaz(s=""):
    print(s, flush=True)


def cocuk_baslat():
    """Uzun uyuyan bir cocuk surec baslat. Kendi konsolumuzu PAYLASIR —
    CTRL_C_EVENT yayin hipotezini olcebilmek icin bu kasitlidir."""
    return subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def yasiyor_mu(p):
    return p.poll() is None


def main():
    yaz(CIZGI)
    yaz("FAZ 0 — Y-1 PROBU: os.kill(pid, 0)")
    yaz("platform : %s" % sys.platform)
    yaz("python   : %s" % sys.version.split()[0])
    yaz(CIZGI)

    if sys.platform != "win32":
        yaz("Bu prob yalniz Windows icin anlamlidir. POSIX'te os.kill(pid,0) tanimli")
        yaz("bir varlik sinamasidir. Burada OLCULEMEDI.")
        yaz("SONUC: OLCULEMEDI (platform win32 degil)")
        return 2

    bulgular = []

    # --- 1) YASAYAN bir surec uzerinde ---------------------------------------
    yaz("[1] YASAYAN surec uzerinde os.kill(pid, 0)")
    cocuk = cocuk_baslat()
    time.sleep(1.0)
    onceden_yasiyor = yasiyor_mu(cocuk)
    yaz("    cocuk pid          : %d" % cocuk.pid)
    yaz("    cagridan ONCE canli: %s" % onceden_yasiyor)

    istisna = None
    try:
        os.kill(cocuk.pid, 0)
        yaz("    os.kill(pid, 0)    : ISTISNA ATMADI  <-- dikkat")
    except Exception as e:  # noqa: BLE001 — olcum betigi, sinifi bilerek genis
        istisna = e
        yaz("    os.kill(pid, 0)    : %s: %s" % (type(e).__name__, e))

    time.sleep(1.5)
    sonradan_yasiyor = yasiyor_mu(cocuk)
    yaz("    cagridan SONRA canli: %s" % sonradan_yasiyor)
    if not sonradan_yasiyor:
        yaz("    cocuk cikis kodu    : %s" % cocuk.returncode)

    try:
        cocuk.kill()
    except Exception:
        pass

    # --- HUKUM 1 -------------------------------------------------------------
    if onceden_yasiyor and not sonradan_yasiyor:
        bulgular.append(
            "KANITLANDI: os.kill(pid, 0) YASAYAN sureci OLDURDU. "
            "Bu bir varlik sinamasi degil, bir SILAH."
        )
    elif istisna is None:
        bulgular.append(
            "KISMEN KANITLANDI: cagri istisna ATMADI. hafiza.py `except (OSError, "
            "AttributeError)` bekliyor; o dal HIC calismiyor demektir. "
            "_surec_yasiyor'un None (OLCULEMEDI) donme yolu Windows'ta KAPALI."
        )
    else:
        bulgular.append(
            "CURUTULDU (bu kolda): cagri %s atti; hafiza.py'nin bekledigi dal calisiyor."
            % type(istisna).__name__
        )

    yaz()

    # --- 2) OLU bir pid uzerinde ---------------------------------------------
    yaz("[2] OLU pid uzerinde os.kill(pid, 0)  (teshisin 'pid BAYAT' kolu)")
    olu = cocuk_baslat()
    olu_pid = olu.pid
    olu.kill()
    olu.wait(timeout=10)
    time.sleep(0.5)
    yaz("    olu pid            : %d (sonlandirildi)" % olu_pid)
    try:
        os.kill(olu_pid, 0)
        yaz("    os.kill(pid, 0)    : ISTISNA ATMADI  <-- OLU pid icin de atmiyor")
        bulgular.append(
            "KANITLANDI: OLU bir pid icin de istisna atmiyor. Yani teshis "
            "'pid YASIYOR' der — YANLIS KESINLIK. Bayat kilit asla temizlenemez."
        )
    except Exception as e:  # noqa: BLE001
        yaz("    os.kill(pid, 0)    : %s: %s" % (type(e).__name__, e))
        yaz("    -> bu kolda teshis dogru calisabilir")

    yaz()
    yaz(CIZGI)
    yaz("BULGULAR")
    for b in bulgular:
        yaz("  * " + b)
    yaz(CIZGI)

    kusur = any(b.startswith(("KANITLANDI", "KISMEN")) for b in bulgular)
    if kusur:
        yaz("SONUC: HIPOTEZ DOGRULANDI — Y-1 gercek bir kusurdur. (exit 1)")
        return 1
    yaz("SONUC: HIPOTEZ CURUTULDU — kod bu kolda guvende. (exit 0)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        yaz("PROB KENDISI COKTU: %s: %s" % (type(e).__name__, e))
        yaz("SONUC: OLCULEMEDI (exit 2)")
        sys.exit(2)
