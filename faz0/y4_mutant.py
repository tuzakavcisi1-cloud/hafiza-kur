#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Y-4 MUTANTI — OLCUM ARACI, OLCEMEDIGI HALI "KACTI" DIYE RAPORLUYOR MU?

NEYI OLCER
  `faz0/y2_mutant.py`'nin HUKUM SOZLESMESINI olcer. Olculen sey bir kapi degil,
  bir OLCUM ARACIDIR. Sozlesme (y2_mutant.py bas kismi):
      0  kurulan her mutant ISIRDI
      1  en az bir mutant KACTI  -> koruma kor
      2  en az bir mutant OLCULEMEDI
      3  ARAC KUSURU (mutant kurulamadi, hukum verilemez)

NEDEN GEREKLI (bu oturumda OLCULDU, beyan degil)
  Kaynak agaci salt-okunur oldugunda (cp ile kopyalanmis ro mount'tan gelen
  dosyalar; paketten acilmis skill; CI cache) y2_mutant `hazirla()` icinde ham
  PermissionError traceback'i basip **exit 1** verdi. Sozlesmede 1 = "MUTANT
  KACTI = koruma kor". Yani OLCULEMEYEN hal, GERCEK KIRMIZIDAN ayirt edilemez
  bicimde raporlandi. Bu SAHTE KIRMIZI'dir ve sahte kirmizi, gercek kirmiziyi
  degersizlestirdigi icin sahte yesilden daha ucuz degildir: bir sonraki oturum
  var olmayan bir kapi korlugunu kovalar.

  Projenin kendi dersi: "Korumayi urune koydun; OLCUM ARACINA koydun mu?" (Y-2).
  Y-4 ayni dersin ikinci yarisi: **hukum sozlesmesini** urune koydun; olcum
  aracina koydun mu?

IKI KOL — her biri AYRI bir kod yolunu olcer
  [A] SALT-OKUNUR KAYNAK   -> copy2 izin bitlerini tasir, mutant kopya yazilamaz.
      Duzeltme: kopyalanan dosyaya S_IWUSR eklenir (KAYNAGA dokunulmaz).
      Olcut: TEMIZ surum OLCUM YAPABILMELI; chmod sokulmus surum ARAC KUSURU
      (exit 3) demeli — yani duzeltme olmadan bu ortamda olcum YOKTUR.
  [B] YAZILAMAYAN TMPDIR   -> mkdtemp / open OSError atar.
      Duzeltme: her OSError MutantKurulamadi'ya cevrilir (exit 3).
      Olcut: TEMIZ surum exit 3 + "ARAC KUSURU" + HAM TRACEBACK YOK;
      except'leri sokulmus surum ham traceback + exit 1 (ESKI KUSUR) uretmeli.

KAPSAM (bilincli sinir, olcumun eksigi degil)
  y2_mutant `--hizli` ile kosulur. Olculen sey HUKUM SOZLESMESIDIR, Y-2 tuzaginin
  kendisi degil; tam kosum bu probu 4 kat uzatir ve tek bir yeni bit olcmez.

CIKIS KODLARI (y2_mutant ile AYNI sozlesme — bilerek)
  0  her kol ISIRDI      1  en az bir kol KACTI      2  en az bir kol OLCULEMEDI
  3  ARAC KUSURU (bu probun kendisi kurulamadi)

KULLANIM
  python3 faz0/y4_mutant.py
"""
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile


def _cikti_kodlamasini_guvenceye_al():   # Y-2 KORUMASI (bu prob da hukum basar)
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
Y2 = os.path.join(KOK, "faz0", "y2_mutant.py")

# Mutantin sokecegi tam metinler. Tasinirlarsa MUTANT DA TASINMALI.
CHMOD_SATIRI = "os.chmod(h, os.stat(h).st_mode | stat.S_IWUSR)"
EXCEPT_DESENI = re.compile(r"except OSError as e:")

SONUC = []
SINIRLAR = []


class ProbKurulamadi(Exception):
    pass


def kayit(ad, isirdi, ayrinti):
    SONUC.append((ad, isirdi, ayrinti))


def y2_kopyala(hedef, sok_chmod=False, sok_except=False):
    """y2_mutant.py + kaynak agacini hedefe kurar. sok_* duzeltmeyi geri alir."""
    try:
        os.makedirs(os.path.join(hedef, "faz0"), exist_ok=True)
        os.makedirs(os.path.join(hedef, "skill", "scripts"), exist_ok=True)
        for ad in ("hafiza.py", "t_y3.py", "t_y42.py"):
            h = os.path.join(hedef, "skill", "scripts", ad)
            shutil.copy2(os.path.join(KAYNAK, ad), h)
            os.chmod(h, os.stat(h).st_mode | stat.S_IWUSR)
        metin = open(Y2, encoding="utf-8").read()
    except OSError as e:
        raise ProbKurulamadi("kaynak kurulamadi: %s" % e)

    if sok_chmod:
        yeni, n = re.subn(re.escape(CHMOD_SATIRI),
                          "pass  # MUTANT: Y-4 chmod duzeltmesi sokuldu", metin)
        if n != 1:
            raise ProbKurulamadi(
                "chmod satiri bulunamadi (n=%d) — duzeltme tasindiysa MUTANT DA "
                "TASINMALI." % n)
        metin = yeni
    if sok_except:
        # OSError'i YAKALAMAYAN bir istisna sinifiyla degistir: ham traceback
        # yeniden ortaya cikmali. Bu, ESKI kusurun birebir taklididir.
        metin, n = EXCEPT_DESENI.subn("except ZeroDivisionError as e:", metin)
        if n < 3:
            raise ProbKurulamadi(
                "OSError yakalayan dal sayisi beklenenden az (n=%d, >=3 bekleniyor)"
                % n)
    p = os.path.join(hedef, "faz0", "y2_mutant.py")
    try:
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(metin)
    except OSError as e:
        raise ProbKurulamadi("y2_mutant kopyasi yazilamadi: %s" % e)
    return p


def kos_y2(kok_dizin, tmpdir=None, saniye=900):
    ortam = dict(os.environ)
    if tmpdir:
        for k in ("TMPDIR", "TMP", "TEMP"):
            ortam[k] = tmpdir
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(kok_dizin, "faz0", "y2_mutant.py"), "--hizli"],
            cwd=kok_dizin, capture_output=True, timeout=saniye, env=ortam)
    except subprocess.TimeoutExpired:
        return None, "ZAMAN ASIMI"
    return r.returncode, (r.stdout or b"").decode("utf-8", "replace") + \
                         (r.stderr or b"").decode("utf-8", "replace")


def salt_okunur_yap(dizin):
    for kk, _dd, ff in os.walk(dizin):
        for f in ff:
            p = os.path.join(kk, f)
            os.chmod(p, os.stat(p).st_mode & ~0o222)


def kol_a(taban):
    """SALT-OKUNUR KAYNAK: duzeltme olmadan olcum YAPILAMAZ."""
    ad = "A  salt-okunur kaynak agaci"
    try:
        temiz = os.path.join(taban, "a_temiz")
        y2_kopyala(temiz)
        salt_okunur_yap(os.path.join(temiz, "skill", "scripts"))
        rc_t, ct = kos_y2(temiz)

        mut = os.path.join(taban, "a_mutant")
        y2_kopyala(mut, sok_chmod=True)
        salt_okunur_yap(os.path.join(mut, "skill", "scripts"))
        rc_m, cm = kos_y2(mut)
    except ProbKurulamadi as e:
        kayit(ad, None, "prob kurulamadi: %s" % e)
        return

    temiz_olcebildi = (rc_t in (0, 2)) and ("SONUC:" in ct) and ("Traceback" not in ct)
    mutant_durustu = (rc_m == 3) and ("ARAC KUSURU" in cm) and ("Traceback" not in cm)
    isirdi = temiz_olcebildi and mutant_durustu
    kayit(ad, isirdi,
          "TEMIZ: exit=%s olcum=%s | chmod SOKULU: exit=%s ARAC-KUSURU=%s traceback=%s"
          % (rc_t, "VAR" if "SONUC:" in ct else "YOK", rc_m,
             "VAR" if "ARAC KUSURU" in cm else "YOK",
             "VAR" if "Traceback" in cm else "yok"))


def kol_b(taban):
    """EKSIK KAYNAK DOSYASI: OSError -> exit 3, ham traceback YOK.

    ILK KURULUM YANLISTI, KAYDA GECIYOR: bu kol once TMPDIR'i salt-okunur yaparak
    OSError uretmeye calisti. Uretemedi — CPython'un `_get_default_tempdir()`
    aday dizinleri sirayla DENER ve yazamadigini sessizce ATLAR, /tmp'ye duser.
    Yani "salt-okunur TMPDIR" bir OSError ortami DEGILDIR ve o kurulumla alinan
    'KACTI' hukmu araci degil PROBUN KENDI KURULUMUNU olcuyordu.
    Determinist ortam: kaynak agacinda t_y42.py YOK (eksik/bozuk paket) ->
    shutil.copy2 FileNotFoundError (OSError) atar."""
    ad = "B  eksik kaynak dosyasi (sahte kirmizi)"
    try:
        temiz = os.path.join(taban, "b_temiz")
        y2_kopyala(temiz)
        os.remove(os.path.join(temiz, "skill", "scripts", "t_y42.py"))
        rc_t, ct = kos_y2(temiz)

        mut = os.path.join(taban, "b_mutant")
        y2_kopyala(mut, sok_except=True)
        os.remove(os.path.join(mut, "skill", "scripts", "t_y42.py"))
        rc_m, cm = kos_y2(mut)
    except (ProbKurulamadi, OSError) as e:
        kayit(ad, None, "prob kurulamadi: %s" % e)
        return

    temiz_durust = (rc_t == 3) and ("ARAC KUSURU" in ct) and ("Traceback" not in ct)
    mutant_yalan = ("Traceback" in cm) and (rc_m == 1)
    isirdi = temiz_durust and mutant_yalan
    kayit(ad, isirdi,
          "TEMIZ: exit=%s ARAC-KUSURU=%s traceback=%s | except SOKULU: exit=%s traceback=%s"
          % (rc_t, "VAR" if "ARAC KUSURU" in ct else "YOK",
             "VAR" if "Traceback" in ct else "yok", rc_m,
             "VAR" if "Traceback" in cm else "yok"))


def main():
    print("=" * 78)
    print("Y-4 MUTANTI — olcum araci olcemedigini 'kacti' diye raporluyor mu?")
    print("  python  : %s" % sys.version.split()[0])
    print("  olculen : %s" % Y2)
    print("  kapsam  : y2_mutant --hizli (olculen sey HUKUM SOZLESMESI)")
    print("=" * 78)
    if os.geteuid() == 0 if hasattr(os, "geteuid") else False:
        SINIRLAR.append("ROOT olarak kosuluyor: salt-okunur izinler ISIRMAZ, "
                        "kol B buyuk olasilikla OLCULEMEDI dusecek")
    try:
        taban = tempfile.mkdtemp(prefix="y4_")
    except OSError as e:
        print("\nARAC KUSURU: gecici dizin acilamadi: %s" % e)
        return 3
    try:
        kol_a(taban)
        kol_b(taban)

        print()
        isiran = kacan = olculemeyen = 0
        for ad, isirdi, ayrinti in SONUC:
            if isirdi is None:
                d = "OLCULEMEDI"; olculemeyen += 1
            elif isirdi:
                d = "ISIRDI    "; isiran += 1
            else:
                d = "KACTI     "; kacan += 1
            print("  %s %-38s | %s" % (d, ad, ayrinti))
        if SINIRLAR:
            print()
            print("OLCUMUN SINIRI (hukum degil):")
            for n in SINIRLAR:
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
        for kk, dd, ff in os.walk(taban):
            for x in dd + ff:
                try:
                    os.chmod(os.path.join(kk, x), 0o755)
                except OSError:
                    pass
        shutil.rmtree(taban, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
