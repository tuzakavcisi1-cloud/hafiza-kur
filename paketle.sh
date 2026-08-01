#!/usr/bin/env bash
# =============================================================================
# skill/ -> hafiza-kur.skill
#
# Paket, `skill/` dizininin zip'idir. Motorun İKİNCİ BİR KOPYASI YOKTUR:
# `skill/scripts/hafiza.py` tek gerçek kaynaktır (H5 doktrini — "aktif sürüm
# hangisi" sorusunun iki cevabı olamaz).
#
# Paketin içindeki SHA256, SKILL.md'de beyan edilenle TUTMAK ZORUNDADIR.
# Bu betik onu ölçer ve tutmuyorsa DURUR.
# =============================================================================
set -eu

KOK="$(cd "$(dirname "$0")" && pwd)"
cd "$KOK"

[ -d skill ] || { echo "HATA: skill/ yok"; exit 2; }
command -v zip >/dev/null || { echo "HATA: zip komutu yok"; exit 2; }

GERCEK="$(python3 -c "import hashlib;print(hashlib.sha256(open('skill/scripts/hafiza.py','rb').read()).hexdigest().upper())")"
BEYAN="$(grep -oE '[0-9A-F]{64}' skill/SKILL.md | head -1 || true)"

echo "hafiza.py SHA256"
echo "  gercek: $GERCEK"
echo "  beyan : ${BEYAN:-YOK (SKILL.md icinde SHA256 bulunamadi)}"

if [ -n "${BEYAN:-}" ] && [ "$GERCEK" != "$BEYAN" ]; then
  echo
  echo "DURDU: SKILL.md'deki SHA256 beyani motorla TUTMUYOR."
  echo "  Once beyani guncelle (ya da motoru geri al). Paket uretilmedi."
  echo "  -- 'belge de bir arayuzdur ve yalan soyleyebilir' (A-2'nin dersi)"
  exit 1
fi

rm -f hafiza-kur.skill
( cd skill && zip -q -r -X "../hafiza-kur.skill" . -x '.*' -x '*/.*' -x '*/deneme/*' -x '*/__pycache__/*' )

echo
echo "PAKET: $KOK/hafiza-kur.skill"
unzip -l hafiza-kur.skill | tail -n +4 | head -n -2 | awk '{print "  " $4}'
