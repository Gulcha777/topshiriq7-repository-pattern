#!/usr/bin/env bash
# Butun loyihani ketma-ket ishga tushiradi.
set -e
cd "$(dirname "$0")"
pip install -q -r requirements.txt
[ -f .env ] || cp .env.example .env

for m in demo_repository demo_transaction demo_cache demo_sqli; do
  echo "=== python -m app.$m ==="
  python -m app.$m
  echo
done
echo "=== pytest ==="
python -m pytest -q
