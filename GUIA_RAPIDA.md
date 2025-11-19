# 🎮 Guía Rápida - Fruit Catcher Camera Edition

## ⚡ Inicio Rápido

### 1. Instalar todo de una vez:

```bash
cd IPM
./install.sh
```

### 2. O instalar manualmente:

# Crear entorno
conda create -n IPM python=3.12
conda activate IPM

# Instalar dependencias
pip install -r requirements.txt

# Descargar modelos
python download_models.py

### 3. Ejecutar el juego:

```bash
conda activate IPM
python fruit_game.py
```

## 🎯 Cómo Jugar

### Controles del Teclado:

- **ESPACIO** → Iniciar juego / Reiniciar
- **M** → Silenciar/Activar música
- **ESC** → Salir

### Controles con la Cabeza:

- **Mueve tu cabeza a la IZQUIERDA** → La cesta se mueve a la izquierda
- **Mueve tu cabeza a la DERECHA** → La cesta se mueve a la derecha

### Reglas:

✅ Atrapa **FRUTAS** = +1 punto 🍎🍌🍓🍉
❌ Atrapa **BOMBAS** = -1 vida 💣
❌ Dejas caer **FRUTAS** = -1 vida
💔 **0 vidas** = GAME OVER

## 💡 Consejos

### Para un mejor rendimiento:

1. **Iluminación**: Asegúrate de tener buena luz en tu cara
2. **Posición**: Colócate a 50-80 cm de la cámara
3. **Fondo**: Un fondo despejado ayuda al tracking
4. **Movimientos**: Mueve solo la cabeza, no todo el cuerpo

### Si el tracking no funciona bien:

```python
# Edita config.py y cambia:
self.model_path = os.path.join(os.path.dirname(__file__), 'models/pose_landmarker_heavy.task')
# Por el modelo más pesado pero más preciso
```

## 🎚️ Ajustar Dificultad

Edita `config.py`:

```python
# MÁS FÁCIL
self.fruit_speed = 2              # Más lento
self.fruit_interval = 1500        # Menos frutas
self.bomb_probability = 0.1       # Menos bombas
self.initial_lives = 5            # Más vidas

# MÁS DIFÍCIL
self.fruit_speed = 5              # Más rápido
self.fruit_interval = 500         # Más frutas
self.bomb_probability = 0.3       # Más bombas
self.initial_lives = 2            # Menos vidas
```

## 🆘 Solución de Problemas

### Error: "No module named 'pygame'"

```bash
conda activate IPM
pip install pygame
```

### Error: "No se pudo abrir la cámara"

- Cierra otras aplicaciones que usen la cámara (Zoom, Teams, etc.)
- Verifica permisos de cámara en Configuración del Sistema

### Error: "No such file or directory: 'models/pose_landmarker_full.task'"

```bash
python download_models.py
```

### El juego va muy lento

- Cierra otras aplicaciones
- Cambia a `pose_landmarker_lite.task` en `config.py`

### Las frutas/bombas no aparecen

- Verifica que las carpetas `imgs/` y `sounds/` estén en la carpeta IPM
- Comprueba que todas las imágenes existan:

```bash
ls imgs/
ls sounds/
```

## 📊 Puntuaciones Típicas

- **Principiante**: 0-10 puntos
- **Intermedio**: 11-30 puntos
- **Avanzado**: 31-50 puntos
- **Experto**: 51+ puntos

## 🎨 Personalización

### Cambiar las frutas o bombas:

1. Reemplaza las imágenes en `imgs/`
2. Mantén los mismos nombres de archivo
3. Formato recomendado: PNG con transparencia
4. Tamaño recomendado: 100x100 px

### Cambiar los sonidos:

1. Reemplaza los archivos en `sounds/`
2. Mantén los mismos nombres de archivo
3. Formato: MP3
4. Mantén volúmenes similares

### Cambiar colores del juego:

Edita `settings.py`:

```python
screen_bg_color = (172, 209, 175)  # RGB - Verde claro
# Prueba otros colores:
# Azul: (135, 206, 235)
# Rosa: (255, 182, 193)
# Morado: (216, 191, 216)
```

## 🏆 Desafíos

1. **Speedrun**: ¿Cuántos puntos en 1 minuto?
2. **Sin bombas**: ¿Puedes evitar TODAS las bombas?
3. **Perfecto**: ¿Puedes atrapar TODAS las frutas sin fallar ninguna?
4. **Estatua**: ¿Puedes jugar moviendo SOLO la cabeza?

## 📚 Más Información

- Documentación completa: `README_FRUIT_GAME.md`
- Juego original: https://github.com/nberdi/Fruit-Catcher
- MediaPipe: https://ai.google.dev/edge/mediapipe/solutions/guide

---

¡Diviértete y buena suerte! 🍀🎮
