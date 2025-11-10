#!/bin/bash

# Script de instalación rápida para Fruit Catcher Camera Edition

echo "🍎 Instalando Fruit Catcher Camera Edition..."
echo ""

# Verificar si conda está instalado
if ! command -v conda &> /dev/null
then
    echo "❌ Conda no está instalado. Por favor instala Conda primero:"
    echo "   https://www.anaconda.com/docs/getting-started/miniconda/install"
    exit 1
fi

echo "✅ Conda encontrado"

# Crear entorno
echo ""
echo "📦 Creando entorno conda IPM..."
conda create -n IPM python=3.12 -y

# Activar entorno
echo ""
echo "🔄 Activando entorno..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate IPM

# Instalar dependencias
echo ""
echo "📥 Instalando dependencias..."
pip install -r requirements.txt

# Descargar modelos
echo ""
echo "🤖 Descargando modelos de MediaPipe..."
python download_models.py

echo ""
echo "✅ ¡Instalación completada!"
echo ""
echo "Para ejecutar el juego:"
echo "  1. conda activate IPM"
echo "  2. python fruit_game.py"
echo ""
echo "¡Disfruta el juego! 🎮🍎"
