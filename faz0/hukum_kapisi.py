#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HUKUM KAPISI — "kosucu hukmunu BASTI mi?" (yesil tike anlam iade eder)

NEYI OLCER — VE NEYI OLCMEZ
  OLCER : beklenen hukum satirlarinin ciktida VAR olup olmadigini.
  OLCMEZ: o hukumlerin yesil olup olmadigini. Bu ayrim bilinclidir.
          Bu kapinin yakaladigi sinif "hukum KAYBOLDU"dur, "hukum kirmizi" degil.

NEDEN VAR (Y-2, olculdu: CI run #2 / f6f7fde)
  capraz.yml'de her adim `continue-on-error: true` ile kosuyordu (Faz 0'da
  bilerek). windows-latest py3.11 ve py3.13'te t_y42 58 senaryonun TAMAMINI
  kostu, sonra rapor dongusunun ILK satirinda UnicodeEncodeError ile coktu ve
  58 hukmun tamami basilmadan kayboldu. GitHub bunu yuttu: is YESIL gorundu,
  API'de adimin `conclusion` alani bile "success" dondu (continue-on-error
  gercek sonucu `outcome`ta saklar). Yani capraz olcumun 1/3'u kordu ve bu
  korluk YESIL TIK olarak raporlaniyordu.

  Bu kapi `continue-on-error` OLMADAN kosar. Bir kosucunun hukmu kaybolursa is
  KIRMIZI olur. Faz 0'in "olc, duzeltme" bayragi digersadimlarda kalabilir;
  hukmun VARLIGI pazarlik konusu degildir.

BEKLENEN HUKUMLER
  t_y3   : SONUC: 20/20 senaryo TEMIZ HATA veriyor
  isir(1): SONUC: 34/34 kosulan mutant ISIRIYOR      (derle ONCESI)
  isir(2): SONUC: 36/36 kosulan mutant ISIRIYOR      (derle SONRASI)
  t_y42  : SONUC: N gecti - M kaldi - K olculemedi
  Desenler kasten ASCII'dir: koruma `errors="replace"` ile devreye girdiginde
  '-' ayraci '?' olarak basilabilir; kapi bu yuzden ayracin kendisine bakmaz.

KULLANIM
  python3 faz0/hukum_kapisi.py hukum.log
  python3 faz0/hukum_kapisi.py hukum.log --bekle=t_y3,isir1,isir2,t_y42

CIKIS KODLARI
  0  beklenen her hukum BASILDI
  1  en az bir hukum KAYIP -> olcum kayboldu, is KIRMIZI
  2  kullanim hatasi / log okunamadi
"""
import os
import re
import sys


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

BEKLENEN = [
    ("t_y3", "t_y3   — 20 temiz hata senaryosu",
     re.compile(r"^SONUC: 20/20 senaryo TEMIZ HATA", re.M)),
    ("isir1", "isir   — derle ONCESI mutant kosumu",
     re.compile(r"^SONUC: 34/34 kosulan mutant ISIRIYOR", re.M)),
    ("isir2", "isir   — derle SONRASI TAM kosum",
     re.compile(r"^SONUC: 36/36 kosulan mutant ISIRIYOR", re.M)),
    ("t_y42", "t_y42  — 58 davranis senaryosu",
     re.compile(r"^SONUC: \d+ gecti", re.M)),
]


def main(argv):
    if len(argv) < 2:
        print("kullanim: hukum_kapisi.py <log dosyasi> [--bekle=a,b,c]")
        return 2
    p = argv[1]
    istenen = None
    for a in argv[2:]:
        if a.startswith("--bekle="):
            istenen = {s.strip() for s in a.split("=", 1)[1].split(",") if s.strip()}
    if not os.path.isfile(p):
        print("HUKUM KAPISI: log dosyasi YOK: %s" % p)
        print("  Bu da bir kayiptir: kosucular hic kosmamis ya da cikti hic yakalanmamis.")
        return 1
    with open(p, encoding="utf-8", errors="replace") as f:
        metin = f.read()

    print("=" * 78)
    print("HUKUM KAPISI — kosucular hukmunu BASTI mi?")
    print("  log      : %s (%d bayt)" % (p, len(metin.encode("utf-8", "replace"))))
    print("=" * 78)

    kayip = []
    for anahtar, ad, desen in BEKLENEN:
        if istenen is not None and anahtar not in istenen:
            print("  ATLANDI    %-38s | --bekle listesinde yok" % ad)
            continue
        m = desen.search(metin)
        if m:
            satir = metin[m.start():metin.find("\n", m.start())
                          if metin.find("\n", m.start()) != -1 else len(metin)]
            print("  BASILDI    %-38s | %s" % (ad, satir.strip()[:60]))
        else:
            print("  KAYIP      %-38s | hukum satiri ciktida YOK" % ad)
            kayip.append(ad)

    print("-" * 78)
    if kayip:
        print("SONUC: %d HUKUM KAYIP — olcum kayboldu, is KIRMIZI." % len(kayip))
        print("  Kaybolan bir hukum 'gecti' DEGILDIR; 'olculemedi'dir (doktrin 2).")
        print("  Ilk bakilacak yer: UnicodeEncodeError (Y-2 sinifi) ve zaman asimi.")
        return 1
    print("SONUC: beklenen her hukum BASILDI.")
    print("  NOT: bu kapi hukumlerin YESIL oldugunu SOYLEMEZ, sadece KAYBOLMADIGINI.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
