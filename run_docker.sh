#!/bin/bash

# ---------------------------------------------------------------------------
# Script para ejecutar Padelhub con Docker
# Universidad de Sevilla - EGC
# ---------------------------------------------------------------------------

set -e

echo "🐳 Iniciando Padelhub con DOCKER..."
echo "----------------------------------------"

# Verificar que estamos en la raíz del proyecto
if [ ! -f "docker/docker-compose.dev.yml" ]; then
    echo "❌ Error: Debes ejecutar este script desde la raíz del proyecto"
    exit 1
fi

# Verificar que Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker no está instalado"
    echo "   Instala Docker desde: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar que Docker Compose está disponible
if ! docker compose version &> /dev/null; then
    echo "❌ Error: Docker Compose no está disponible"
    exit 1
fi

# Configurar variables de entorno para Docker
echo "📝 Configurando .env para Docker..."
cp .env.docker.example .env
echo "✅ Variables de entorno configuradas para Docker"

# Verificar .moduleignore
if [ ! -f ".moduleignore" ]; then
    echo "⚠️  Creando .moduleignore..."
    echo "webhook" > .moduleignore
fi

# Detener servicios conflictivos
echo ""
echo "🔍 Verificando servicios conflictivos..."

# Detener MariaDB local si está corriendo
if sudo systemctl is-active --quiet mariadb 2>/dev/null; then
    echo "⚠️  MariaDB local está corriendo. Deteniéndolo..."
    sudo systemctl stop mariadb
    echo "✅ MariaDB local detenido"
fi

# Verificar y liberar puertos ocupados
PORTS_TO_CHECK=(5000 80 3306 4444)
for PORT in "${PORTS_TO_CHECK[@]}"; do
    if sudo lsof -ti:$PORT &>/dev/null; then
        echo "⚠️  Puerto $PORT ocupado. Liberándolo..."
        sudo kill -9 $(sudo lsof -ti:$PORT) 2>/dev/null || true
        sleep 1
    fi
done

# Detener contenedores existentes que puedan interferir
echo "🧹 Limpiando contenedores previos..."
docker compose -f docker/docker-compose.dev.yml down 2>/dev/null || true
sleep 2

# Preguntar si hacer rebuild
echo ""
echo "Opciones de inicio:"
echo "  1. Inicio rápido (usa caché)"
echo "  2. Rebuild completo (más lento, usa si cambiaste requirements.txt)"
echo ""
read -p "Selecciona una opción (1/2) [1]: " -n 1 -r
echo
echo ""

if [[ $REPLY =~ ^[2]$ ]]; then
    echo "🔨 Construyendo imágenes desde cero..."
    docker compose -f docker/docker-compose.dev.yml build --no-cache
fi

echo "🚀 Levantando contenedores..."
docker compose -f docker/docker-compose.dev.yml up -d --build

echo ""
echo "⏳ Esperando a que los servicios estén listos..."

# Esperar a que MariaDB esté listo (máximo 60 segundos)
echo "   📊 Esperando MariaDB..."
COUNTER=0
MAX_WAIT=60
until docker exec mariadb_container mariadb -u root -ppadelhubdb_root_password -e "SELECT 1" >/dev/null 2>&1; do
    sleep 2
    COUNTER=$((COUNTER + 2))
    if [ $COUNTER -ge $MAX_WAIT ]; then
        echo ""
        echo "❌ Error: MariaDB no se inició en $MAX_WAIT segundos"
        echo "   Ver logs: docker logs mariadb_container"
        exit 1
    fi
    echo -n "."
done
echo ""
echo "   ✅ MariaDB listo"

# Esperar a que Flask esté listo (máximo 90 segundos)
echo "   🎾 Esperando Flask..."
COUNTER=0
MAX_WAIT=90
until docker logs web_app_container 2>&1 | grep -q "Running on"; do
    sleep 3
    COUNTER=$((COUNTER + 3))
    if [ $COUNTER -ge $MAX_WAIT ]; then
        echo ""
        echo "⚠️  Flask tardó más de lo esperado. Mostrando logs..."
        docker logs web_app_container --tail 30
        break
    fi
    echo -n "."
done
echo ""
echo "   ✅ Flask listo"

# Mostrar logs finales
echo ""
echo "📋 Logs del contenedor web (últimas líneas):"
echo "----------------------------------------"
docker logs web_app_container --tail 15

echo ""
echo "✅ ¡Despliegue completado!"
echo "----------------------------------------"
echo "🌐 Accede a: http://localhost"
echo "📊 Base de datos: localhost:3306"
echo "🧪 Selenium Hub: http://localhost:4444"
echo "🔍 VNC Chrome: vnc://localhost:5900 (pass: secret)"
echo "🔍 VNC Firefox: vnc://localhost:5901 (pass: secret)"
echo ""
echo "📝 Comandos útiles:"
echo "   Ver logs:        docker compose -f docker/docker-compose.dev.yml logs -f web"
echo "   Entrar al bash:  docker exec -it web_app_container bash"
echo "   Reiniciar:       docker compose -f docker/docker-compose.dev.yml restart web"
echo "   Detener todo:    docker compose -f docker/docker-compose.dev.yml down"
echo "   Ver estado:      docker compose -f docker/docker-compose.dev.yml ps"
echo ""
echo "🛑 Para detener: ./stop_docker.sh o docker compose -f docker/docker-compose.dev.yml down"
echo "----------------------------------------"

# Preguntar si quiere ver logs
echo ""
read -p "¿Ver logs en tiempo real? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker compose -f docker/docker-compose.dev.yml logs -f web
fi
