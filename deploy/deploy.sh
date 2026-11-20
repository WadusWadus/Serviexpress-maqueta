#!/usr/bin/env bash
# Actualiza SERVIEXPRESS en el VPS (MAQUETA-SPEC 12.9): git pull → pip install → migrate → collectstatic → reinicio.
# Uso, en el VPS:  ~/serviexpress/deploy/deploy.sh
set -euo pipefail
cd "$(dirname "$0")/.."

set -a; source .env; set +a

git pull --ff-only
venv/bin/pip install --quiet -r requirements.txt
venv/bin/python manage.py migrate --noinput
venv/bin/python manage.py collectstatic --noinput --clear
venv/bin/python manage.py check --deploy --fail-level ERROR

# Reiniciar gunicorn necesita sudo (pide la clave del usuario).
sudo systemctl restart serviexpress
systemctl is-active serviexpress
echo "SERVIEXPRESS actualizado."
