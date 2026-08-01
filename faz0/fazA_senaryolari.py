#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FAZ A SENARYOLARI — B4-5 · B4-6 · B4-10 · B4-11 duzeltmeleri ISIRIYOR MU?

HER DUZELTMEYE AYRI SENARYO, HER SENARYOYA AYRI SABOTAJ.
  Bir senaryo iki kol kosar:
    TEMIZ   : duzeltilmis hafiza.py    -> beklenen davranis GORULMELI
    SABOTAJ : duzeltme sokulmus kopya  -> ESKI KUSUR yeniden URETILMELI
  Yalnizca ikisi de tutarsa senaryo ISIRDI der. Sabotaj kolu KUSURU yeniden
  uretemiyorsa senaryo komsu bir sinifi olcuyordur ve hukmu yoktur (CLAUDE.md:
  "her yeni testi SABOTAJLA sina").

NEDEN AYRI DOSYA
  t_y42 DAVRANIS kanitlarinin defteridir ve 58 senaryosu v2.4.1'de DENETLENDI.
  Faz A duzeltmeleri denetlenmemis yeni baytlardir; kendi defterlerinde dogar,
  yesillendikten sonra t_y42'ye tasinip tasinmayacagi AYRI bir karardir.

CIKIS KODLARI (proje sozlesmesi)
  0 her senaryo ISIRDI · 1 en az biri KACTI · 2 en az biri OLCULEMEDI
  3 ARAC KUSURU (senaryolar kurulamadi)
"""
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile


def _cikti_kodlamasini_guvenceye_al():   # Y-2 KORUMASI
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
KAYNAK = os.path.join(KOK, "skill", "scripts", "hafiza.py")

SONUC = []
SINIRLAR = []


class SenaryoKurulamadi(Exception):
    pass


def kayit(ad, isirdi, ayrinti):
    SONUC.append((ad, isirdi, ayrinti))


# --------------------------------------------------------------- SABOTAJLAR
# Her biri: (ad, fonksiyon) — metni alir, ESKI (kusurlu) hale dondurur.

def sab_b411(m):
    eski = '_zh = [x for x in _zincir_hukumleri if not x.startswith("~")]'
    yeni = '_zh = [x for x in zincir_dogrula(y) if not x.startswith("~")]'
    return _degistir(m, eski, yeni, "B4-11")


def sab_b46(m):
    eski = 'return re.search(re.escape(bas) + r".*?" + re.escape(son) + r"[^\\n]*", metin, re.S)'
    yeni = 'return re.search(re.escape(bas) + r".*?" + re.escape(son), metin, re.S)'
    return _degistir(m, eski, yeni, "B4-6")


def sab_b45(m):
    eski = "    kok = _IZ_KOK[0]\n    if not kok or not os.path.isdir(kok):\n        return []"
    yeni = ("    return [os.path.join(os.getcwd(), \"hafiza_hata_izi.txt\")]  # SABOTAJ: v2.4.1 davranisi\n"
            "    kok = _IZ_KOK[0]\n    if not kok or not os.path.isdir(kok):\n        return []")
    return _degistir(m, eski, yeni, "B4-5")


def sab_b410_stdin(m):
    eski = "        govde = _stdin_oku()"
    yeni = "        govde = sys.stdin.read()"
    return _degistir(m, eski, yeni, "B4-10/stdin")


def sab_b410_mesaj(m):
    # Bicimlendirme argumanlari (%d, %r) AYNI kalir; yalniz metin v2.4.1'e doner.
    eski = '"Fragman govdesi COK KISA: %d karakter (en az 3). Verdigin: %r\\n"'
    yeni = '"Bos fragman yazilmaz. --metin ver ya da stdin\'den boru et. %d%.0r\\n"'
    return _degistir(m, eski, yeni, "B4-10/mesaj")


def _degistir(metin, eski, yeni, etiket):
    if metin.count(eski) != 1:
        raise SenaryoKurulamadi(
            "%s sabotaji: hedef metin %d kez gecti (1 olmali). Duzeltme "
            "tasindiysa SABOTAJ DA TASINMALI." % (etiket, metin.count(eski)))
    return metin.replace(eski, yeni, 1)


# --------------------------------------------------------------- ALTYAPI

def motor_kur(hedef, sabotaj=None, ek_yama=None):
    """hafiza.py'yi hedefe kopyalar; sabotaj verilirse duzeltmeyi geri alir."""
    try:
        os.makedirs(hedef, exist_ok=True)
        metin = open(KAYNAK, encoding="utf-8").read()
        if ek_yama:
            metin = ek_yama(metin)
        if sabotaj:
            metin = sabotaj(metin)
        p = os.path.join(hedef, "hafiza.py")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(metin)
        os.chmod(p, os.stat(p).st_mode | stat.S_IWUSR)
    except OSError as e:
        raise SenaryoKurulamadi("motor kurulamadi: %s" % e)
    return p


def kos(motor, arglar, cwd=None, ortam_ek=None, saniye=180, girdi=None):
    o = dict(os.environ)
    o["PYTHONIOENCODING"] = "utf-8"
    if ortam_ek:
        o.update(ortam_ek)
    try:
        r = subprocess.run([sys.executable, motor] + arglar,
                           cwd=cwd, capture_output=True, timeout=saniye,
                           env=o, input=girdi)
    except subprocess.TimeoutExpired:
        return None, "ZAMAN ASIMI (%d sn)" % saniye
    return r.returncode, (r.stdout or b"").decode("utf-8", "replace") + \
                         (r.stderr or b"").decode("utf-8", "replace")


def proje_kur(motor, kok):
    os.makedirs(kok, exist_ok=True)
    rc, c = kos(motor, ["kur", "--kok=" + kok])
    if rc != 0:
        raise SenaryoKurulamadi("proje kurulamadi (exit=%s): %s" % (rc, c[-300:]))
    return kok


# --------------------------------------------------------------- SENARYOLAR

def s_b411(taban):
    """B4-11: zincir_dogrula `kapi` basina KAC KEZ cagriliyor?

    Olcut SAYIDIR, SURE DEGIL: sure makineye baglidir (bkz. B-6 dersi), cagri
    sayisi degildir. Ayrica kapinin HUKMU iki kolda AYNI kalmalidir — bir
    performans duzeltmesinin olcumu degistirmedigi de olculur."""
    ad = "B4-11 zincir_dogrula tek kez cagriliyor"
    sayac_yama = lambda m: _degistir(
        m,
        "def zincir_dogrula(y):\n    hata = []",
        "def zincir_dogrula(y):\n"
        "    open(os.environ['ZD_SAYAC'], 'a', encoding='utf-8').write('1\\n')\n"
        "    hata = []",
        "ZD sayaci")
    try:
        sonuclar = {}
        for kol, sab in (("temiz", None), ("sabotaj", sab_b411)):
            d = os.path.join(taban, "b411_" + kol)
            motor = motor_kur(d, sabotaj=sab, ek_yama=sayac_yama)
            kok = proje_kur(motor, os.path.join(d, "p"))
            sayac = os.path.join(d, "sayac.txt")
            open(sayac, "w").close()
            rc, c = kos(motor, ["kapi", "--kok=" + kok],
                        ortam_ek={"ZD_SAYAC": sayac})
            n = len([x for x in open(sayac, encoding="utf-8").read().split("\n") if x.strip()])
            sonuclar[kol] = (n, rc, "SONUC:" in c)
    except (SenaryoKurulamadi, OSError) as e:
        kayit(ad, None, "kurulamadi: %s" % e)
        return
    t_n, t_rc, t_h = sonuclar["temiz"]
    s_n, s_rc, s_h = sonuclar["sabotaj"]
    isirdi = (t_n == 1) and (s_n == 2) and (t_rc == s_rc) and t_h and s_h
    kayit(ad, isirdi,
          "TEMIZ: %d cagri exit=%s hukum=%s | SABOTAJ: %d cagri exit=%s (hukum ayni mi: %s)"
          % (t_n, t_rc, "VAR" if t_h else "YOK", s_n, s_rc, t_rc == s_rc))


def _korunan_kur(motor, kok, kuyruklu=True):
    """Isaretli blok kurar. kuyruklu=True ise `son` isaretinden SONRA ayni
    satirda metin birakir — B4-6'nin tam olarak olcmedigi bolge."""
    p = os.path.join(kok, "CLAUDE.md")
    govde = ("# PROTOKOL\n"
             "Bu blok korunacaktir.\n"
             "SONISARET" + (" bu kuyruk kuralin GOVDESIDIR ve degistirilemez.\n"
                            if kuyruklu else "\n") +
             "Blok disi metin.\n")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(govde)
    rc, c = kos(motor, ["korunan", "--kok=" + kok, "--dosya=CLAUDE.md",
                        "--bas=# PROTOKOL", "--son=SONISARET",
                        "--gerekce=B4-6 sinir kuyrugu senaryosu icin korunan blok"])
    if rc != 0:
        raise SenaryoKurulamadi("korunan beyani basarisiz (exit=%s): %s" % (rc, c[-300:]))
    return p


def s_b46(taban):
    """B4-6: `son` isaretinin SATIR KUYRUGU degistirilince H8 isiriyor mu?"""
    ad = "B4-6 H8 kuyruk tahrifini yakaliyor (M-H8c)"
    try:
        sonuclar = {}
        for kol, sab in (("temiz", None), ("sabotaj", sab_b46)):
            d = os.path.join(taban, "b46_" + kol)
            motor = motor_kur(d, sabotaj=sab)
            kok = proje_kur(motor, os.path.join(d, "p"))
            p = _korunan_kur(motor, kok)
            # SADECE kuyrugu degistir; blok govdesine ve isaretlere DOKUNMA.
            s = open(p, encoding="utf-8").read()
            s = s.replace("SONISARET bu kuyruk kuralin GOVDESIDIR ve degistirilemez.",
                          "SONISARET KURAL IPTAL EDILDI, istedigini yap.")
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(s)
            rc, c = kos(motor, ["kapi", "--kok=" + kok])
            sonuclar[kol] = (rc, "[H8]" in c or "H8]" in c or "KORUNAN blok DEGISMIS" in c)
    except (SenaryoKurulamadi, OSError) as e:
        kayit(ad, None, "kurulamadi: %s" % e)
        return
    t_rc, t_h8 = sonuclar["temiz"]
    s_rc, s_h8 = sonuclar["sabotaj"]
    isirdi = (t_rc == 1 and t_h8) and (s_rc == 0 and not s_h8)
    kayit(ad, isirdi,
          "TEMIZ: exit=%s H8=%s | SABOTAJ (cimri kapsam): exit=%s H8=%s"
          % (t_rc, "ISIRDI" if t_h8 else "SESSIZ", s_rc, "ISIRDI" if s_h8 else "SESSIZ"))


def s_b46_gecis(taban):
    """B4-6 GECIS: v2.4.1 kapsamiyla beyan edilmis kayit ASILSIZ TAHRIFLE
    suclanmiyor; ayri ve dogru hukum veriliyor."""
    ad = "B4-6 gecis: eski kapsamli beyan 'tahrif' diye suclanmiyor"
    try:
        d = os.path.join(taban, "b46g")
        motor = motor_kur(d)
        kok = proje_kur(motor, os.path.join(d, "p"))
        _korunan_kur(motor, kok)
        # Defteri v2.4.1 kapsamina GERI al: sha'yi kuyruksuz metinden hesapla.
        rcp = os.path.join(kok, ".hafizarc")
        h = json.load(open(rcp, encoding="utf-8")).get("hafiza_dizini", "arsiv/hafiza")
        dp = os.path.join(kok, h.replace("/", os.sep), "_KORUNAN.json")
        d_json = json.load(open(dp, encoding="utf-8"))
        metin = open(os.path.join(kok, "CLAUDE.md"), encoding="utf-8").read()
        m = re.search(re.escape("# PROTOKOL") + r".*?" + re.escape("SONISARET"), metin, re.S)
        import hashlib
        d_json["bloklar"][0]["sha"] = hashlib.sha256(
            m.group(0).encode("utf-8")).hexdigest().upper()
        with open(dp, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(d_json, ensure_ascii=False, indent=1) + "\n")
        rc, c = kos(motor, ["kapi", "--kok=" + kok])
    except (SenaryoKurulamadi, OSError, KeyError, IndexError) as e:
        kayit(ad, None, "kurulamadi: %s" % e)
        return
    gecis = "KAPSAMI GENISLEDI" in c
    asilsiz = "KORUNAN blok DEGISMIS (beyansiz)" in c
    isirdi = (rc == 1) and gecis and not asilsiz
    kayit(ad, isirdi,
          "exit=%s · gecis hukmu=%s · asilsiz 'DEGISMIS' suclamasi=%s"
          % (rc, "VAR" if gecis else "YOK", "VAR" if asilsiz else "yok"))


def s_b45(taban):
    """B4-5 (M-IZDOSYA): cwd proje DISINDA iken cokme -> disarida dosya OLUSMAMALI."""
    ad = "B4-5 hata izi proje agacinin disina yazilmiyor"
    try:
        sonuclar = {}
        for kol, sab in (("temiz", None), ("sabotaj", sab_b45)):
            d = os.path.join(taban, "b45_" + kol)
            motor = motor_kur(d, sabotaj=sab)
            kok = proje_kur(motor, os.path.join(d, "p"))
            disari = os.path.join(d, "disari")     # PROJE AGACININ DISI
            os.makedirs(disari, exist_ok=True)
            # Cokme uret: hafiza dizinini salt-okunur yap -> kilit_al PermissionError
            hd = os.path.join(kok, "arsiv", "hafiza")
            eski_mod = os.stat(hd).st_mode
            os.chmod(hd, eski_mod & ~0o222)
            if os.access(hd, os.W_OK):
                kayit(ad, None, "salt-okunur etkisiz (root?) — cokme URETILEMEDI, "
                                "bu senaryo OLCULEMEDI, PASS DEGIL")
                os.chmod(hd, eski_mod)
                return
            rc, c = kos(motor, ["muhur", "--kok=" + kok,
                                "salt okunur dizinde muhurleme denemesi"], cwd=disari)
            os.chmod(hd, eski_mod)
            disarida = os.path.isfile(os.path.join(disari, "hafiza_hata_izi.txt"))
            # "Iceride" = proje agacinin HERHANGI bir yeri: hafiza dizini salt-okunur
            # oldugu icin (cokmenin sebebi bizzat o) iz koke dusebilir. Yalniz
            # arsiv/hafiza'ya bakmak, teshis kabiliyetini OLCMEDEN "yok" derdi.
            iceride = ""
            for _kk, _dd, _ff in os.walk(kok):
                if "hafiza_hata_izi.txt" in _ff:
                    iceride = os.path.relpath(_kk, kok) or "."
                    break
            sonuclar[kol] = (rc, disarida, iceride, "Traceback" in c)
    except (SenaryoKurulamadi, OSError) as e:
        kayit(ad, None, "kurulamadi: %s" % e)
        return
    t_rc, t_dis, t_ic, t_tb = sonuclar["temiz"]
    s_rc, s_dis, _s_ic, _s_tb = sonuclar["sabotaj"]
    # Olcut UC parcali: (a) disariya YAZILMAMALI (b) sabotaj kolu ESKI kusuru
    # yeniden uretmeli (c) teshis KAYBOLMAMALI — iz proje agacinda bir yerde olmali.
    isirdi = (not t_dis) and s_dis and (not t_tb) and bool(t_ic)
    kayit(ad, isirdi,
          "TEMIZ: disarida=%s · iz proje icinde=%s · exit=%s · ham-traceback=%s | "
          "SABOTAJ: disarida=%s exit=%s"
          % ("VAR" if t_dis else "yok", t_ic or "YOK", t_rc,
             "VAR" if t_tb else "yok", "VAR" if s_dis else "yok", s_rc))


def s_b410_stdin(taban):
    """B4-10: kapanmayan boruya bagli `not` SURESIZ beklemiyor."""
    ad = "B4-10 stdin zaman asimi (asili kalma -> hukum)"
    try:
        sonuclar = {}
        for kol, sab in (("temiz", None), ("sabotaj", sab_b410_stdin)):
            d = os.path.join(taban, "b410s_" + kol)
            motor = motor_kur(d, sabotaj=sab)
            kok = proje_kur(motor, os.path.join(d, "p"))
            # stdin'i KAPANMAYAN bir boruya bagla: `sleep` in cikisi.
            uyuyan = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(60)"],
                stdout=subprocess.PIPE)
            try:
                o = dict(os.environ)
                o["HAFIZA_STDIN_ZAMAN_ASIMI"] = "3"
                o["PYTHONIOENCODING"] = "utf-8"
                try:
                    r = subprocess.run(
                        [sys.executable, motor, "not", "--kok=" + kok,
                         "--konu=genel-durum", "--tur=durum"],
                        stdin=uyuyan.stdout, capture_output=True, timeout=25, env=o)
                    rc = r.returncode
                    c = (r.stdout or b"").decode("utf-8", "replace") + \
                        (r.stderr or b"").decode("utf-8", "replace")
                except subprocess.TimeoutExpired:
                    rc, c = None, "ASILI KALDI (25 sn)"
            finally:
                uyuyan.kill()
                uyuyan.wait()
            sonuclar[kol] = (rc, "KAPANMADI" in c, c[:80])
    except (SenaryoKurulamadi, OSError) as e:
        kayit(ad, None, "kurulamadi: %s" % e)
        return
    t_rc, t_msg, _ = sonuclar["temiz"]
    s_rc, _s_msg, _ = sonuclar["sabotaj"]
    isirdi = (t_rc == 2 and t_msg) and (s_rc is None)
    kayit(ad, isirdi,
          "TEMIZ: exit=%s zaman-asimi-hukmu=%s | SABOTAJ: %s"
          % (t_rc, "VAR" if t_msg else "YOK",
             "ASILI KALDI (beklenen)" if s_rc is None else "exit=%s (asilmadi!)" % s_rc))


def s_b410_mesaj(taban):
    """B4-10: 1-2 karakterlik govde 'bos' DIYE reddedilmiyor."""
    ad = "B4-10 kisa govde 'bos' diye reddedilmiyor"
    try:
        sonuclar = {}
        for kol, sab in (("temiz", None), ("sabotaj", sab_b410_mesaj)):
            d = os.path.join(taban, "b410m_" + kol)
            motor = motor_kur(d, sabotaj=sab)
            kok = proje_kur(motor, os.path.join(d, "p"))
            rc, c = kos(motor, ["not", "--kok=" + kok, "--konu=genel-durum",
                                "--tur=durum", "--metin=sv"], girdi=b"")
            sonuclar[kol] = (rc, "COK KISA" in c, "Bos fragman" in c)
    except (SenaryoKurulamadi, OSError) as e:
        kayit(ad, None, "kurulamadi: %s" % e)
        return
    t_rc, t_kisa, t_bos = sonuclar["temiz"]
    _s_rc, s_kisa, s_bos = sonuclar["sabotaj"]
    isirdi = (t_rc == 2 and t_kisa and not t_bos) and (s_bos and not s_kisa)
    kayit(ad, isirdi,
          "TEMIZ: exit=%s 'COK KISA'=%s 'Bos fragman'=%s | SABOTAJ: 'Bos fragman'=%s"
          % (t_rc, "VAR" if t_kisa else "YOK", "VAR" if t_bos else "yok",
             "VAR" if s_bos else "YOK"))


def main():
    print("=" * 82)
    print("FAZ A SENARYOLARI — duzeltmeler ISIRIYOR mu? (her birine AYRI sabotaj)")
    print("  python : %s" % sys.version.split()[0])
    print("  motor  : %s" % KAYNAK)
    print("=" * 82)
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        SINIRLAR.append("ROOT: salt-okunur izinler ISIRMAZ — B4-5 senaryosu "
                        "buyuk olasilikla OLCULEMEDI duser")
    try:
        taban = tempfile.mkdtemp(prefix="fazA_")
    except OSError as e:
        print("\nARAC KUSURU: gecici dizin acilamadi: %s" % e)
        return 3
    try:
        for f in (s_b411, s_b46, s_b46_gecis, s_b45, s_b410_stdin, s_b410_mesaj):
            f(taban)
        print()
        isiran = kacan = olculemeyen = 0
        for ad, isirdi, ayrinti in SONUC:
            if isirdi is None:
                d = "OLCULEMEDI"; olculemeyen += 1
            elif isirdi:
                d = "ISIRDI    "; isiran += 1
            else:
                d = "KACTI     "; kacan += 1
            print("  %s %-48s | %s" % (d, ad, ayrinti))
        if SINIRLAR:
            print()
            print("OLCUMUN SINIRI (hukum degil):")
            for n in SINIRLAR:
                print("  - %s" % n)
        print()
        print("-" * 82)
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
