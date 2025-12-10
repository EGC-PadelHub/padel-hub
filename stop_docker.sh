#!/bin/bash

echo "Deteniendo Padelhub (Docker)..."
echo ""

# Verificar que estamos en la raíz del proyecto
if [ ! -f "docker/docker-compose.dev.yml" ]; then
    echo "Error: Debes ejecutar este script desde la raíz del proyecto"
    exit 1
fi

# Detener contenedores
echo "Deteniendo contenedores..."
docker compose -f docker/docker-compose.dev.yml down

# Liberar puertos
PORTS_TO_CLEAN=(5000 80 3306 4444 5900 5901)
for PORT in "${PORTS_TO_CLEAN[@]}"; do
    if sudo lsof -ti:$PORT &>/dev/null; then
        sudo kill -9 $(sudo lsof -ti:$PORT) 2>/dev/null || true
    fi
done

echo ""
echo "Contenedores detenidos"
echo ""
