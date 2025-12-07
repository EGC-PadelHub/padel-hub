#!/bin/bash

# ---------------------------------------------------------------------------
# Script para detener Padelhub con Docker
# Universidad de Sevilla - EGC
# ---------------------------------------------------------------------------

echo "🛑 Deteniendo Padelhub (Docker)..."
echo "----------------------------------------"

# Verificar que estamos en la raíz del proyecto
if [ ! -f "docker/docker-compose.dev.yml" ]; then
    echo "❌ Error: Debes ejecutar este script desde la raíz del proyecto"
    exit 1
fi

echo ""
echo "Opciones:"
echo "  1. Detener contenedores (mantener volúmenes/datos)"
echo "  2. Detener y eliminar todo (incluye base de datos)"
echo "  3. Solo pausar (más rápido para reiniciar)"
echo ""
read -p "Selecciona una opción (1/2/3) [1]: " -n 1 -r
echo
echo ""

case $REPLY in
    2)
        echo "🗑️  Deteniendo y eliminando contenedores + volúmenes..."
        docker compose -f docker/docker-compose.dev.yml down -v
        echo "⚠️  Base de datos eliminada. En el próximo inicio se recreará desde cero."
        ;;
    3)
        echo "⏸️  Pausando contenedores..."
        docker compose -f docker/docker-compose.dev.yml stop
        echo "ℹ️  Para reiniciar: docker compose -f docker/docker-compose.dev.yml start"
        ;;
    *)
        echo "🛑 Deteniendo contenedores..."
        docker compose -f docker/docker-compose.dev.yml down
        echo "ℹ️  Volúmenes conservados. En el próximo inicio se usará la misma BD."
        ;;
esac

# Liberar puertos si siguen ocupados
echo ""
echo "🧹 Limpiando puertos..."
PORTS_TO_CLEAN=(5000 80 3306 4444 5900 5901)
for PORT in "${PORTS_TO_CLEAN[@]}"; do
    if sudo lsof -ti:$PORT &>/dev/null; then
        sudo kill -9 $(sudo lsof -ti:$PORT) 2>/dev/null || true
    fi
done

echo ""
echo "✅ Operación completada"
echo ""
echo "Ver contenedores activos: docker ps"
echo "Ver todos los contenedores: docker ps -a"
echo "Ver volúmenes: docker volume ls"
