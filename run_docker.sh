#!/bin/bash

set -e

echo "Iniciando Padelhub con Docker..."
echo ""

# Verificar que estamos en la raíz del proyecto
if [ ! -f "docker/docker-compose.dev.yml" ]; then
    echo "Error: Debes ejecutar este script desde la raíz del proyecto"
    exit 1
fi

# Verificar que Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "Error: Docker no está instalado"
    echo "Instala Docker desde: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar que Docker Compose está disponible
if ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose no está disponible"
    exit 1
fi

# Configurar variables de entorno
echo "Configurando .env..."
cp .env.docker.example .env

# Crear .moduleignore si no existe
if [ ! -f ".moduleignore" ]; then
    echo "webhook" > .moduleignore
fi

# Detener MariaDB local si está corriendo
if systemctl is-active --quiet mariadb 2>/dev/null; then
    echo "MariaDB local está corriendo. Deteniéndolo..."
    sudo systemctl stop mariadb
fi

# Verificar y liberar puertos ocupados
PORTS_TO_CHECK=(5000 80 3306 4444)
for PORT in "${PORTS_TO_CHECK[@]}"; do
    if sudo lsof -ti:$PORT &>/dev/null; then
        echo "Liberando puerto $PORT..."
        sudo kill -9 $(sudo lsof -ti:$PORT) 2>/dev/null || true
    fi
done

# Detener contenedores previos
echo "Limpiando contenedores previos..."
docker compose -f docker/docker-compose.dev.yml down 2>/dev/null || true

# Levantar contenedores
echo "Levantando contenedores..."
docker compose -f docker/docker-compose.dev.yml up -d --build

echo ""
echo "Esperando a que los servicios estén listos..."

# Esperar a que MariaDB esté listo
echo "Esperando MariaDB..."
COUNTER=0
MAX_WAIT=60
until docker exec mariadb_container mariadb -u root -ppadelhubdb_root_password -e "SELECT 1" >/dev/null 2>&1; do
    sleep 2
    COUNTER=$((COUNTER + 2))
    if [ $COUNTER -ge $MAX_WAIT ]; then
        echo "Error: MariaDB no se inició en $MAX_WAIT segundos"
        echo "Ver logs: docker logs mariadb_container"
        exit 1
    fi
    echo -n "."
done
echo ""

# Esperar a que Flask esté listo
echo "Esperando Flask..."
COUNTER=0
MAX_WAIT=90
until docker logs web_app_container 2>&1 | grep -q "Running on"; do
    sleep 3
    COUNTER=$((COUNTER + 3))
    if [ $COUNTER -ge $MAX_WAIT ]; then
        echo "Flask tardó más de lo esperado"
        docker logs web_app_container --tail 20
        break
    fi
    echo -n "."
done
echo ""

echo ""
echo "Despliegue completado!"
echo ""
echo "Accede a la aplicación: http://localhost"
echo ""
echo "Para detener: ./stop_docker.sh"
echo "Ver logs: docker compose -f docker/docker-compose.dev.yml logs -f web"
echo ""
