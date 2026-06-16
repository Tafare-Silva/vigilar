#!/usr/bin/env bash
# Script de deploy — executa no servidor como usuário "vigilar"
# Uso: ./deploy/deploy.sh

set -euo pipefail

APP_DIR="/home/vigilar/app"
VENV="$APP_DIR/.venv"
PYTHON="$VENV/bin/python"
PIP="$VENV/bin/pip"

echo "==> Atualizando código..."
git -C "$APP_DIR" pull origin main

echo "==> Instalando/atualizando dependências..."
$PIP install -r "$APP_DIR/requirements.txt" --quiet

echo "==> Rodando migrações..."
$PYTHON "$APP_DIR/manage.py" migrate --noinput

echo "==> Coletando arquivos estáticos..."
$PYTHON "$APP_DIR/manage.py" collectstatic --noinput --clear

echo "==> Reiniciando serviços..."
sudo systemctl restart vigilar vigilar-celery vigilar-celery-beat

echo "==> Status dos serviços:"
sudo systemctl status vigilar vigilar-celery vigilar-celery-beat --no-pager -l

echo ""
echo "Deploy concluído!"
