#!/bin/sh
# Arranque del contenedor: migraciones, configuración base (opcional) y servidor.
set -e
# Sin DATABASE_URL se usaría SQLite dentro del contenedor y los datos se perderían en cada despliegue
if [ -z "$DATABASE_URL" ]; then
  echo "Falta DATABASE_URL (la dirección de la base PostgreSQL)." >&2
  exit 1
fi
alembic upgrade head
# CARGAR_CONFIG_BASE=1: agrega las unidades, estados y tipos sugeridos que falten
# (datos/base.json). No duplica ni pisa lo que ya existe.
if [ "${CARGAR_CONFIG_BASE:-0}" = "1" ]; then
  python -m app.atributos.instalacion "${ORGANIZACION_POR_DEFECTO:-1}"
fi
# PORT lo define la plataforma (Render, Railway, Cloud Run); 8000 en local
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers \
  --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-127.0.0.1}"
