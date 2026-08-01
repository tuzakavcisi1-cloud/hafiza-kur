#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FAZ 0 — OTOMATIK SABOTAJ / KAPSAM ENVANTERI URETECI

Fable 5, 4. tur denetimi §3.6:
  "Sabotaj olceklenmiyor: elle yapiliyor ve yalniz YENI testlere uygulanmis.
   Olceklenmesi zor degil ... tam katalog bir gecelik isidir ve KAPSAM
   ENVANTERINI OTOMATIK URETIR."
ve §9:
  "Sen bu yontemi biliyorsun ve YENI testlere uygulamissin; ESKILERE
   uygulamamissin. Asil bosluk orada."

NE YAPAR
--------
`hafiza.py` icindeki HER `fail(...)` cagrisini (bugun 60 adet) TEK TEK devre disi
birakir ve her seferinde `isir` kosar:

  * Devre disi birakinca EN AZ BIR mutant "KACTI" diyorsa
        -> o fail() KAPSAMLI: onu olcen bir mutant var.            [KAPSAMLI]
  * Devre disi birakinca HICBIR SEY degismiyorsa (isir yine 36/36)
        -> o fail() KAPSAMSIZ: hicbir mutant onu olcmuyor.         [KAPSAMSIZ]
           Yarin o satir silinse `isir` FARK ETMEZ. Kapsam envanteri budur.
  * Sabotajli surum cokuyorsa                                      [OLCULEMEDI]

Yani bu betik "kor kapi protokolu"nu kapilarin KENDISINE degil, kapilarin
KANITLARINA uygular: bir mutantin var olmasi, dogru sinifi olctugu anlamina gelmez.

ONEMLI: `hafiza.py` DEGISTIRILMEZ. Salt-okunur girdidir; her sabotaj gecici bir
KOPYA uzerinde yapilir ve kopya sonunda silinir.

KULLANIM
--------
    python3 faz0/sabotaj.py --motor skill/scripts/hafiza.py [--is 4] [--json rapor.json]
    python3 faz0/sabotaj.py --motor skill/scripts/hafiza.py --sadece 5      # hizli deneme

CIKIS KODU
----------
    0  her fail() kapsamli (hicbir kor nokta yok)
    1  en az bir KAPSAMSIZ fail() var  (v2.4.1'de beklenen)
    2  OLCULEMEDI / kurulum hatasi
"""
import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed

CIZGI = "-" * 78


# ---------------------------------------------------------------------------
# 1) fail() cagri yerlerini AST ile bul  (regex DEGIL: cok satirli cagrilar var)
# ---------------------------------------------------------------------------
def fail_cagrilari(kaynak):
    """[(no, lineno, col, end_lineno, end_col, etiket)] dondurur."""
    agac = ast.parse(kaynak)
    bulunan = []
    for d in ast.walk(agac):
        if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "fail":
            etiket = "?"
            if d.args and isinstance(d.args[0], ast.Constant) and isinstance(d.args[0].value, str):
                etiket = d.args[0].value
            bulunan.append(
                {
                    "lineno": d.lineno,
                    "col": d.col_offset,
                    "end_lineno": d.end_lineno,
                    "end_col": d.end_col_offset,
                    "kapi": etiket,
                }
            )
    bulunan.sort(key=lambda x: (x["lineno"], x["col"]))
    for i, b in enumerate(bulunan):
        b["no"] = i + 1
    return bulunan


def sabote_et(kaynak, hedef):
    """Tek bir fail(...) cagrisini `None` ile degistir. Kaynagi DEGISTIRMEZ."""
    satirlar = kaynak.split("\n")
    bas_i, son_i = hedef["lineno"] - 1, hedef["end_lineno"] - 1
    if bas_i == son_i:
        s = satirlar[bas_i]
        satirlar[bas_i] = s[: hedef["col"]] + "None" + s[hedef["end_col"] :]
    else:
        bas = satirlar[bas_i][: hedef["col"]] + "None"
        son = satirlar[son_i][hedef["end_col"] :]
        satirlar[bas_i] = bas + son
        # aradaki satirlari sil (sondan basa)
        del satirlar[bas_i + 1 : son_i + 1]
    yeni = "\n".join(satirlar)
    compile(yeni, "<sabotaj>", "exec")   # sozdizimi bozulduysa burada patlar
    return yeni


# ---------------------------------------------------------------------------
# 2) Tek bir sabotajı koş
# ---------------------------------------------------------------------------
def tek_kosum(args):
    kaynak, hedef, sablon_proje = args
    no = hedef["no"]
    gecici = tempfile.mkdtemp(prefix="sabotaj_%03d_" % no)
    try:
        try:
            bozuk = sabote_et(kaynak, hedef)
        except SyntaxError as e:
            return {**hedef, "hukum": "OLCULEMEDI", "sebep": "sozdizimi: %s" % e,
                    "kacan": 0, "exit": None, "kacanlar": []}

        motor = os.path.join(gecici, "hafiza.py")
        with open(motor, "w", encoding="utf-8", newline="\n") as f:
            f.write(bozuk)

        proje = os.path.join(gecici, "p")
        shutil.copytree(sablon_proje, proje, symlinks=True)

        try:
            p = subprocess.run(
                [sys.executable, motor, "isir", "--kok", proje],
                capture_output=True, text=True, timeout=300,
            )
        except subprocess.TimeoutExpired:
            return {**hedef, "hukum": "OLCULEMEDI", "sebep": "zaman asimi (300 sn)",
                    "kacan": 0, "exit": None, "kacanlar": []}

        cikti = (p.stdout or "") + (p.stderr or "")
        kacanlar = sorted(set(re.findall(r"(M-[A-Z0-9a-z_]+)\s+.*?KACTI", cikti)))
        if not kacanlar:
            kacanlar = sorted(set(m for m in re.findall(r"^\s*(M-\S+).*KACTI", cikti, re.M)))
        kacan = len(kacanlar)

        if "Traceback" in cikti:
            hukum, sebep = "OLCULEMEDI", "sabotajli surum cokuyor"
        elif kacan > 0:
            hukum, sebep = "KAPSAMLI", "%d mutant KACTI" % kacan
        else:
            hukum, sebep = "KAPSAMSIZ", "hicbir mutant fark etmedi (isir exit=%s)" % p.returncode

        return {**hedef, "hukum": hukum, "sebep": sebep, "kacan": kacan,
                "exit": p.returncode, "kacanlar": kacanlar}
    finally:
        shutil.rmtree(gecici, ignore_errors=True)


# ---------------------------------------------------------------------------
# 3) Sablon proje: `derle` kosulmus olmali (yoksa M-H1b / M-DEVIR kurulamaz)
# ---------------------------------------------------------------------------
def sablon_hazirla(motor, kok):
    os.makedirs(kok, exist_ok=True)
    subprocess.run(["git", "init", "-q", kok], check=False,
                   capture_output=True)
    ad = [sys.executable, motor]
    subprocess.run(ad + ["kur", "--kok", kok, "--ad", "Sabotaj"],
                   capture_output=True, check=False)
    subprocess.run(ad + ["not", "--kok", kok, "--konu=genel-durum",
                         "--metin=sabotaj sablonu icin ilk not"],
                   capture_output=True, check=False)
    subprocess.run(ad + ["derle", "--kok", kok], capture_output=True, check=False)
    p = subprocess.run(ad + ["isir", "--kok", kok], capture_output=True, text=True, check=False)
    ozet = ""
    for s in (p.stdout or "").split("\n"):
        if s.startswith("SONUC:"):
            ozet = s.strip()
    return p.returncode, ozet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--motor", default="skill/scripts/hafiza.py")
    ap.add_argument("--is", dest="isci", type=int, default=4, help="paralel isci sayisi")
    ap.add_argument("--sadece", type=int, default=0, help="yalniz ilk N fail() (hizli deneme)")
    ap.add_argument("--json", default="", help="raporu bu dosyaya JSON olarak yaz")
    a = ap.parse_args()

    motor = os.path.abspath(a.motor)
    if not os.path.isfile(motor):
        print("OLCULEMEDI: motor yok: %s" % motor)
        return 2
    kaynak = open(motor, encoding="utf-8").read()

    hedefler = fail_cagrilari(kaynak)
    if a.sadece:
        hedefler = hedefler[: a.sadece]

    print(CIZGI)
    print("OTOMATIK SABOTAJ — kapsam envanteri")
    print("motor      : %s" % motor)
    print("fail() sayi: %d  (kosulacak: %d)" % (len(fail_cagrilari(kaynak)), len(hedefler)))
    print(CIZGI)

    kok = tempfile.mkdtemp(prefix="sabotaj_sablon_")
    proje = os.path.join(kok, "sablon")
    rc, ozet = sablon_hazirla(motor, proje)
    print("SABLON (sabotajsiz temel kosum): exit=%s" % rc)
    print("  %s" % ozet)
    if rc != 0:
        print("OLCULEMEDI: temel kosum zaten temiz degil; sabotaj anlamsiz.")
        shutil.rmtree(kok, ignore_errors=True)
        return 2
    print(CIZGI)

    sonuclar = []
    try:
        with ProcessPoolExecutor(max_workers=a.isci) as ex:
            isler = {ex.submit(tek_kosum, (kaynak, h, proje)): h for h in hedefler}
            for fut in as_completed(isler):
                r = fut.result()
                sonuclar.append(r)
                im = {"KAPSAMLI": "+", "KAPSAMSIZ": "!", "OLCULEMEDI": "?"}[r["hukum"]]
                print("  %s  #%02d  satir %-5d  %-8s %-11s %s"
                      % (im, r["no"], r["lineno"], r["kapi"], r["hukum"],
                         ",".join(r["kacanlar"][:4]) or r["sebep"]))
                sys.stdout.flush()
    finally:
        shutil.rmtree(kok, ignore_errors=True)

    sonuclar.sort(key=lambda x: x["no"])
    kapsamli = [r for r in sonuclar if r["hukum"] == "KAPSAMLI"]
    kapsamsiz = [r for r in sonuclar if r["hukum"] == "KAPSAMSIZ"]
    olculemedi = [r for r in sonuclar if r["hukum"] == "OLCULEMEDI"]

    print(CIZGI)
    print("KAPSAM ENVANTERI")
    print("  KAPSAMLI   : %d" % len(kapsamli))
    print("  KAPSAMSIZ  : %d   <-- bu satirlar silinse `isir` FARK ETMEZ" % len(kapsamsiz))
    print("  OLCULEMEDI : %d" % len(olculemedi))
    if kapsamsiz:
        print()
        print("  KAPSAMSIZ fail() cagrilari (kapi -> satir):")
        for r in kapsamsiz:
            print("    %-8s satir %d" % (r["kapi"], r["lineno"]))
    print(CIZGI)

    if a.json:
        with open(a.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"motor": motor, "sonuclar": sonuclar}, f,
                      ensure_ascii=False, indent=2)
        print("JSON rapor: %s" % a.json)

    if olculemedi and not kapsamsiz:
        print("HUKUM: OLCULEMEDI kalemler var — 'tam kapsamli' DEMEK YASAK.")
        return 2
    if kapsamsiz:
        print("HUKUM: %d KOR NOKTA var." % len(kapsamsiz))
        return 1
    print("HUKUM: her fail() en az bir mutantla kapsanmis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
