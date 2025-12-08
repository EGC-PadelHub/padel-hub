#!/bin/bash

# ---------------------------------------------------------------------------
# Script para ejecutar Padelhub en modo local (desarrollo)
# Universidad de Sevilla - EGC
# ---------------------------------------------------------------------------

set -e

echo "🎾 Iniciando Padelhub en modo LOCAL..."
echo "----------------------------------------"

# Verificar que estamos en la raíz del proyecto
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Debes ejecutar este script desde la raíz del proyecto"
    exit 1
fi

# Configurar variables de entorno para LOCAL
echo "📝 Configurando .env para ejecución LOCAL..."
cp .env.local.example .env
echo "✅ Variables de entorno configuradas para LOCAL"

# Detener servicios conflictivos
echo ""
echo "🔍 Verificando servicios conflictivos..."

# Detener contenedores Docker si están corriendo
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "web_app_container\|mariadb_container"; then
    echo "⚠️  Contenedores Docker corriendo. Deteniéndolos..."
    docker compose -f docker/docker-compose.dev.yml down 2>/dev/null || true
    echo "✅ Contenedores Docker detenidos"
fi

# Verificar y liberar puerto 5000
if sudo lsof -ti:5000 &>/dev/null; then
    echo "⚠️  Puerto 5000 ocupado. Liberándolo..."
    sudo kill -9 $(sudo lsof -ti:5000) 2>/dev/null || true
    sleep 1
    echo "✅ Puerto 5000 liberado"
fi

# Iniciar MariaDB local si no está corriendo
if ! sudo systemctl is-active --quiet mariadb 2>/dev/null; then
    echo "🔄 MariaDB local no está corriendo. Iniciándolo..."
    sudo systemctl start mariadb
    sleep 2
    
    if sudo systemctl is-active --quiet mariadb; then
        echo "✅ MariaDB local iniciado"
    else
        echo "❌ Error: No se pudo iniciar MariaDB local"
        echo "   Alternativa: usar MariaDB en Docker"
        echo "   docker run -d --name mariadb_local \\"
        echo "     -e MARIADB_ROOT_PASSWORD=padelhubdb_root_password \\"
        echo "     -e MARIADB_DATABASE=padelhubdb \\"
        echo "     -e MARIADB_USER=padelhubdb_user \\"
        echo "     -e MARIADB_PASSWORD=padelhubdb_password \\"
        echo "     -p 3306:3306 mariadb:12.0.2"
        exit 1
    fi
fi

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "📦 Activando entorno virtual..."
    source venv/bin/activate
else
    echo "⚠️  No se encontró entorno virtual en ./venv"
    echo "   Para crear uno: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Verificar que las dependencias están instaladas
if ! python -c "import flask" 2>/dev/null; then
    echo "📥 Instalando dependencias..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e .
fi

# Verificar conexión a MariaDB
echo "🔍 Verificando conexión a MariaDB..."
source .env

# Intentar conectar (con reintentos)
RETRIES=0
MAX_RETRIES=5
until mariadb -h "$MARIADB_HOSTNAME" -P "$MARIADB_PORT" -u "$MARIADB_USER" -p"$MARIADB_PASSWORD" -e "SELECT 1" 2>/dev/null; do
    RETRIES=$((RETRIES + 1))
    if [ $RETRIES -ge $MAX_RETRIES ]; then
        echo "❌ Error: No se puede conectar a MariaDB después de $MAX_RETRIES intentos"
        echo ""
        echo "Alternativa: usar MariaDB en Docker"
        echo "  docker run -d --name mariadb_local \\"
        echo "    -e MARIADB_ROOT_PASSWORD=padelhubdb_root_password \\"
        echo "    -e MARIADB_DATABASE=padelhubdb \\"
        echo "    -e MARIADB_USER=padelhubdb_user \\"
        echo "    -e MARIADB_PASSWORD=padelhubdb_password \\"
        echo "    -p 3306:3306 mariadb:12.0.2"
        exit 1
    fi
    echo "   Esperando MariaDB... intento $RETRIES/$MAX_RETRIES"
    sleep 2
done

echo "✅ Conexión a MariaDB exitosa"

# Verificar si la base de datos tiene tablas
TABLE_COUNT=$(mariadb -h "$MARIADB_HOSTNAME" -P "$MARIADB_PORT" -u "$MARIADB_USER" -p"$MARIADB_PASSWORD" -D "$MARIADB_DATABASE" -sse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$MARIADB_DATABASE';" 2>/dev/null || echo "0")

if [ "$TABLE_COUNT" -eq 0 ]; then
    echo "📊 Base de datos vacía. Ejecutando migraciones y seeders..."
    flask db upgrade
    rosemary db:seed -y
    echo "✅ Base de datos inicializada"
else
    echo "ℹ️  Base de datos ya tiene $TABLE_COUNT tablas"
    read -p "¿Ejecutar migraciones? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        flask db upgrade
    fi
fi

echo ""
echo "🚀 Iniciando servidor Flask..."
echo "----------------------------------------"
echo "📍 Accede a: http://localhost:5000"
echo "⚡ Modo: Desarrollo (hot reload activado)"
echo "🛑 Presiona Ctrl+C para detener"
echo "----------------------------------------"
echo ""

# Iniciar Flask
flask run --host=0.0.0.0 --port=5000 --reload --debug
