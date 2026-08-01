#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Y-3 KANIT KOSUCUSU — ham traceback sinifi kapandi mi?

Her senaryo icin olculen sey TEK: cikti icinde "Traceback (most recent call last)"
gecmemeli VE cikis kodu sifirdisi olmali VE mesaj TEMIZ (taninabilir bir hukum) olmali.
"Temiz hata" = kullanici ne yapacagini biliyor; "traceback" = kullanici aracin coktugunu sanir.
"""
import os, sys, json, shutil, subprocess, tempfile

MOTOR = os.path.abspath(os.path.join(os.path.dirname(__file__), "hafiza.py"))
PY = sys.executable


def kos(args, kok):
    r = subprocess.run([PY, "-X", "utf8", MOTOR] + args + ["--kok=" + kok],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def taze_proje():
    d = tempfile.mkdtemp(prefix="y3_")
    kok = os.path.join(d, "p")
    os.makedirs(kok)
    k, c = kos(["kur"], kok)
    if k != 0:
        raise SystemExit("kur basarisiz:\n" + c)
    return kok


SONUC = []


def senaryo(ad, hazirla, komut, beklenen_parca):
    kok = taze_proje()
    try:
        hazirla(kok)
        k, c = kos(komut, kok)
        traceback_var = "Traceback (most recent call last)" in c
        temiz = beklenen_parca in c
        gecti = (not traceback_var) and temiz and k != 0
        SONUC.append((ad, gecti, k, traceback_var, temiz, c.strip().split("\n")[:4]))
    finally:
        shutil.rmtree(os.path.dirname(kok), ignore_errors=True)


def hd(kok):
    rc = json.load(open(os.path.join(kok, ".hafizarc"), encoding="utf-8"))
    return os.path.join(kok, *rc.get("hafiza_dizini", "arsiv/hafiza").split("/"))


def yaz(p, s, ham=False):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if ham:
        open(p, "wb").write(s)
    else:
        open(p, "w", encoding="utf-8", newline="\n").write(s)


# --- 1..4: bozuk JSON defterleri ------------------------------------------
for defter in ["_KOVA.json", "_DUZELTMELER.json", "_KORUNAN.json", "_CIPA.json"]:
    senaryo("bozuk JSON: " + defter,
            (lambda dd: lambda kok: yaz(os.path.join(hd(kok), dd), '{"bozuk": '))(defter),
            ["kapi"], "DEFTER BOZUK")

# --- 5: defter var ama en ust duzey tipi yanlis ---------------------------
senaryo("tip yanlis: _KOVA.json bir liste",
        lambda kok: yaz(os.path.join(hd(kok), "_KOVA.json"), '["a","b"]'),
        ["kapi"], "en ust duzey")

# --- 6: liste alani nesne degil -------------------------------------------
senaryo("_KORUNAN.json > bloklar liste degil",
        lambda kok: yaz(os.path.join(hd(kok), "_KORUNAN.json"), '{"bloklar": {"a":1}}'),
        ["kapi"], "bir liste olmali")

# --- 7: kayitta zorunlu alan yok ------------------------------------------
senaryo("_DUZELTMELER.json kaydinda 'eski' yok",
        lambda kok: yaz(os.path.join(hd(kok), "_DUZELTMELER.json"),
                        '{"duzeltmeler":[{"satir":3,"yeni":"x"}]}'),
        ["kapi"], "zorunlu alan yok")

# --- 8: _KOVA satirlar anahtari sayi degil --------------------------------
senaryo("_KOVA.json > satirlar anahtari sayi degil",
        lambda kok: yaz(os.path.join(hd(kok), "_KOVA.json"),
                        '{"satirlar":{"abc":"CANLI"}}'),
        ["kapi"], "TAM SAYI olmali")

# --- 9: _TASINMA.jsonl bozuk satir ----------------------------------------
senaryo("_TASINMA.jsonl bozuk satir",
        lambda kok: yaz(os.path.join(hd(kok), "_TASINMA.jsonl"), '{"satirlar":[]}\n{bozuk\n'),
        ["kapi"], "gecersiz JSON")

# --- 10: _ZINCIR.jsonl kaydinda 'halka' yok -------------------------------
def _halka_sil(kok):
    p = os.path.join(hd(kok), "_ZINCIR.jsonl")
    sat = [s for s in open(p, encoding="utf-8").read().split("\n") if s.strip()]
    k = json.loads(sat[-1]); k.pop("halka", None)
    sat[-1] = json.dumps(k, ensure_ascii=False)
    yaz(p, "\n".join(sat) + "\n")

senaryo("_ZINCIR.jsonl son kayitta 'halka' yok",
        _halka_sil, ["kapi"], "ALANSIZ")

# --- 11: _ZINCIR.jsonl son kayitta 'yuk' yok ------------------------------
def _yuk_sil(kok):
    p = os.path.join(hd(kok), "_ZINCIR.jsonl")
    sat = [s for s in open(p, encoding="utf-8").read().split("\n") if s.strip()]
    k = json.loads(sat[-1]); k.pop("yuk", None)
    sat[-1] = json.dumps(k, ensure_ascii=False)
    yaz(p, "\n".join(sat) + "\n")

senaryo("_ZINCIR.jsonl son kayitta 'yuk' yok",
        _yuk_sil, ["kapi"], "'yuk' yok/bozuk")

# --- 12: zincir kaydi nesne degil -----------------------------------------
senaryo("_ZINCIR.jsonl kaydi dizi",
        lambda kok: yaz(os.path.join(hd(kok), "_ZINCIR.jsonl"), '[1,2,3]\n'),
        ["kapi"], "bir nesne degil")

# --- 13: UTF-8 olmayan dosya ----------------------------------------------
senaryo("canli hafiza UTF-8 degil",
        lambda kok: yaz(os.path.join(kok, "PROJE_HAFIZA.md"),
                        "# BASLIK\n\xff\xfe bozuk bayt\n".encode("latin-1"), ham=True),
        ["kapi"], "UTF-8 DEGIL")

# --- 14: bozuk zincir uzerine muhur ---------------------------------------
senaryo("muhur — zincirin son satiri bozuk",
        lambda kok: open(os.path.join(hd(kok), "_ZINCIR.jsonl"), "a",
                         encoding="utf-8", newline="\n").write("{bozuk\n"),
        ["muhur", "elle duzeltme yapildi gerekce"], "gecersiz JSON")

# --- 15: emekli — hic HAFIZA_*.md yok -------------------------------------
def _arsiv_sil(kok):
    for f in os.listdir(hd(kok)):
        if f.startswith("HAFIZA_") and f.endswith(".md"):
            os.remove(os.path.join(hd(kok), f))

senaryo("emekli — hic HAFIZA_*.md yok",
        _arsiv_sil, ["emekli", "3-4", "--not=deneme gerekcesi burada"],
        "Emeklilik hedefi YOK")

# --- 16: karar --yerine=abc -----------------------------------------------
senaryo("karar --yerine=abc",
        lambda kok: None, ["karar", "--baslik=Deneme", "--yerine=abc"],
        "TAM SAYI olmali")

# --- 17: .hafizarc sayisal alan metin -------------------------------------
def _rc_boz(kok, alan, deger):
    p = os.path.join(kok, ".hafizarc")
    c = json.load(open(p, encoding="utf-8")); c[alan] = deger
    yaz(p, json.dumps(c, ensure_ascii=False, indent=1) + "\n")

senaryo(".hafizarc > tavan_kb metin",
        lambda kok: _rc_boz(kok, "tavan_kb", "abc"), ["kapi"], "TAM SAYI olmali")

# --- 18: .hafizarc liste alani metin (SESSIZ YANLIS OLCUM sinifi) ---------
senaryo(".hafizarc > kural_isaretleri metin (liste degil)",
        lambda kok: _rc_boz(kok, "kural_isaretleri", "ASLA"), ["kapi"], "bir LISTE olmali")

# --- 19: ADR on-bilgisinde yerine-gecen sayi degil ------------------------
def _adr_boz(kok):
    d = os.path.join(kok, "kararlar")
    os.makedirs(d, exist_ok=True)
    yaz(os.path.join(d, "0001-deneme.md"),
        "---\nno: 0001\nbaslik: Deneme\ndurum: kabul\nkonu: x\n"
        "yerine-gecen: abc\nyerini-aldigi: -\n---\n\n" + ("govde " * 60) + "\n")

senaryo("ADR yerine-gecen sayi degil", _adr_boz, ["kapi"], "SAYI DEGIL")

# --- 20: isir — bozuk defterli projede yalan 'ISIRDI' vermemeli -----------
kok = taze_proje()
try:
    yaz(os.path.join(hd(kok), "_KOVA.json"), '{"satirlar": ')
    k, c = kos(["isir"], kok)
    SONUC.append(("isir — bozuk _KOVA.json",
                  ("Traceback (most recent call last)" not in c)
                  and ("DEFTER BOZUK" in c) and ("ISIRDI" not in c) and k != 0,
                  k, "Traceback (most recent call last)" in c, "DEFTER BOZUK" in c,
                  c.strip().split("\n")[:4]))
finally:
    shutil.rmtree(os.path.dirname(kok), ignore_errors=True)

# --- rapor -----------------------------------------------------------------
print("=" * 78)
print("Y-3 — HAM TRACEBACK SINIFI")
print("=" * 78)
gecen = 0
for ad, ok, k, tb, temiz, ilk in SONUC:
    print("%-46s %s  (exit %s%s%s)" %
          (ad[:46], "TEMIZ" if ok else "KALDI", k,
           ", TRACEBACK!" if tb else "", "" if temiz else ", mesaj TUTMADI"))
    if not ok:
        for s in ilk:
            print("        | " + s[:110])
    gecen += 1 if ok else 0
print("-" * 78)
print("SONUC: %d/%d senaryo TEMIZ HATA veriyor" % (gecen, len(SONUC)))
sys.exit(0 if gecen == len(SONUC) else 1)
