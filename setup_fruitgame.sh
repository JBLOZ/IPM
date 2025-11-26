#!/usr/bin/env bash
set -e

echo "============================================="
echo "  INICIO DE INSTALACION FRUIT GAME"
echo "============================================="

PYTHON_CMD=""
for cmd in python3.11 python3 python py; do
    if command -v $cmd &>/dev/null; then
        version=$($cmd --version 2>&1)
        echo "$cmd version detectada: $version"
        if echo "$version" | grep -q "3.11"; then
            PYTHON_CMD=$cmd
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "[ERROR] Python 3.11 no encontrado."
    echo "Descarga e instala Python 3.11 manualmente desde:"
    echo "https://www.python.org/downloads/release/python-3118/"
    echo "Asegúrate de añadir Python al PATH durante la instalación."
    exit 1
fi

echo "[OK] Usando: $PYTHON_CMD"
echo "============================================="
echo "  CREANDO ENTORNO VIRTUAL..."
echo "============================================="
$PYTHON_CMD -m venv venv
source venv/Scripts/activate || source venv/bin/activate

echo "[OK] Entorno virtual activado."
echo "============================================="
echo "  ACTUALIZANDO PIP..."
echo "============================================="
$PYTHON_CMD -m pip install --upgrade pip

echo "============================================="
echo "  INSTALANDO DEPENDENCIAS..."
echo "============================================="
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Ocurrió un problema al instalar las dependencias."
    exit 1
fi

echo "============================================="
echo "  DESCARGANDO MODELOS..."
echo "============================================="
# Ejecutar directamente el script de descarga de modelos
python download_models.py

if [ $? -ne 0 ]; then
    echo "[ERROR] Ocurrió un problema al descargar los modelos."
    exit 1
fi

echo "============================================="
echo "  INSTALACION COMPLETADA"
echo "============================================="
echo "Activa el entorno virtual con: source venv/Scripts/activate (desde la gitbash en Windows) o source venv/bin/activate (en Linux/Mac)"
echo "Para lanzar el juego ejecuta: python fruit_game.py"
echo "============================================="
