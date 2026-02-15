#!/bin/bash
set -e

echo "🔄 Esperando a PostgreSQL..."
while ! pg_isready -h db -U fran_user > /dev/null 2>&1; do
    sleep 1
done
echo "✅ PostgreSQL listo"

echo "🔄 Ejecutando migraciones..."
python manage.py migrate --noinput

echo "🔄 Colectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Inicialización completa"

exec "$@"
