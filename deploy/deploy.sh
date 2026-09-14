#!/usr/bin/env bash
# Redeploy Locus on the VM: pull latest main, rebuild backend + frontend, restart services.
# Run with sudo: sudo /home/pawanpatrapp/Locus/deploy/deploy.sh
set -euo pipefail

APP_DIR="/home/pawanpatrapp/Locus"
APP_USER="pawanpatrapp"
UV="/home/pawanpatrapp/.local/bin/uv"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this with sudo." >&2
  exit 1
fi

echo "==> Pulling latest code"
sudo -u "$APP_USER" -H git -C "$APP_DIR" pull --ff-only

echo "==> Syncing backend dependencies"
sudo -u "$APP_USER" -H bash -c "cd $APP_DIR/backend && $UV sync"

echo "==> Running database migrations"
sudo -u "$APP_USER" -H bash -c "cd $APP_DIR/backend && $UV run alembic upgrade head"

echo "==> Installing frontend dependencies"
sudo -u "$APP_USER" -H bash -c "cd $APP_DIR/frontend && npm ci"

echo "==> Building frontend"
sudo -u "$APP_USER" -H bash -c "cd $APP_DIR/frontend && npm run build"

echo "==> Restarting services"
systemctl restart locus-backend locus-celery locus-frontend

echo "==> Done. Status:"
systemctl --no-pager status locus-backend locus-celery locus-frontend | grep -E "●|Active:"
