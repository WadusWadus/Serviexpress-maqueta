#!/usr/bin/env bash
# Respaldo diario de la base SQLite, conservando 7 días (MAQUETA-SPEC 12.8; demostración de RNF16).
# Se programa con cron:  15 3 * * * /home/wadus/serviexpress/deploy/respaldo.sh
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p respaldos
# .backup de sqlite3 sería ideal, pero el VPS no tiene el cliente; Python trae el mismo mecanismo.
venv/bin/python - <<'PY'
import sqlite3, datetime
origen = sqlite3.connect("db.sqlite3")
destino = sqlite3.connect(f"respaldos/db-{datetime.date.today():%Y-%m-%d}.sqlite3")
origen.backup(destino)
destino.close(); origen.close()
PY
find respaldos -name "db-*.sqlite3" -mtime +7 -delete
