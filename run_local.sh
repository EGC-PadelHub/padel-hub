#!/bin/bash

set -e

echo "Iniciando Padelhub en modo LOCAL..."
echo ""

# Verificar que estamos en la raíz del proyecto
if [ ! -f "requirements.txt" ]; then
    echo "Error: Debes ejecutar este script desde la raíz del proyecto"
    exit 1
fi

# Configurar variables de entorno
echo "Configurando .env..."
cp .env.local.example .env

# Detener contenedores Docker si están corriendo
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "web_app_container\|mariadb_container"; then
    echo "Deteniendo contenedores Docker..."
    docker compose -f docker/docker-compose.dev.yml down 2>/dev/null || true
fi

# Liberar puerto 5000
if sudo lsof -ti:5000 &>/dev/null; then
    echo "Liberando puerto 5000..."
    sudo kill -9 $(sudo lsof -ti:5000) 2>/dev/null || true
fi

# Iniciar MariaDB local
if ! sudo systemctl is-active --quiet mariadb 2>/dev/null; then
    echo "Iniciando MariaDB local..."
    sudo systemctl start mariadb
    sleep 2
fi

# Activar entorno virtual
if [ -d "venv" ]; then
    echo "Activando entorno virtual..."
    source venv/bin/activate
else
    echo "Error: No se encontró entorno virtual en ./venv"
    echo "Para crear uno: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Instalar dependencias si es necesario
if ! python -c "import flask" 2>/dev/null; then
    echo "Instalando dependencias..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e .
fi

# Verificar conexión a MariaDB
echo "Verificando conexión a MariaDB..."
source .env

RETRIES=0
MAX_RETRIES=5
until mariadb -h "$MARIADB_HOSTNAME" -P "$MARIADB_PORT" -u "$MARIADB_USER" -p"$MARIADB_PASSWORD" -e "SELECT 1" 2>/dev/null; do
    RETRIES=$((RETRIES + 1))
    if [ $RETRIES -ge $MAX_RETRIES ]; then
        echo "Error: No se puede conectar a MariaDB"
        exit 1
    fi
    echo "Esperando MariaDB... intento $RETRIES/$MAX_RETRIES"
    sleep 2
done

# Ejecutar migraciones si la base de datos está vacía
TABLE_COUNT=$(mariadb -h "$MARIADB_HOSTNAME" -P "$MARIADB_PORT" -u "$MARIADB_USER" -p"$MARIADB_PASSWORD" -D "$MARIADB_DATABASE" -sse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$MARIADB_DATABASE';" 2>/dev/null || echo "0")

if [ "$TABLE_COUNT" -eq 0 ]; then
    echo "Base de datos vacía. Ejecutando migraciones..."
    flask db upgrade
    rosemary db:seed -y
else
    echo "Base de datos tiene $TABLE_COUNT tablas"
fi

echo ""
echo "Iniciando servidor Flask..."
echo "Accede a: http://localhost:5000"
echo ""

# Iniciar Flask
flask run --host=0.0.0.0 --port=5000 --reload --debug
