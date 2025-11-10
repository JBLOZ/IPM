# 🍎 Fruit Catcher - Camera Edition

## Juego de Frutas con Control por Cámara usando MediaPipe

Este proyecto combina el juego clásico **Fruit Catcher** con **visión por computador** utilizando MediaPipe. El jugador controla una cesta moviendo su cabeza frente a la cámara para atrapar frutas y evitar bombas.

![Fruit Catcher Camera Edition](https://github.com/user-attachments/assets/1c51471e-8b4b-4f56-bd25-9cebfacb2af2)

## 🎮 Características del Juego

- **Control por Cámara**: Mueve tu cabeza para controlar la cesta
- **Seguimiento de Pose**: Utiliza MediaPipe Pose Landmarker para rastrear la posición de tu cabeza
- **Atrapa Frutas**: Gana puntos atrapando manzanas, plátanos, fresas y sandías
- **Evita Bombas**: Pierdes una vida si atrapas una bomba
- **Sistema de Vidas**: Comienza con 3 vidas
- **Efectos de Sonido**: Música de fondo y efectos de sonido para acciones del juego
- **Puntuación Máxima**: El juego guarda tu mejor puntuación

## 📋 Prerequisitos

Tener instalado **Conda**, [instalar aquí](https://www.anaconda.com/docs/getting-started/miniconda/install).

## 🚀 Instalación

### 1. Crear un entorno de conda:
```bash
conda create -n IPM python=3.12
conda activate IPM
```

### 2. Instalar las dependencias necesarias:
```bash
cd IPM
pip install -r requirements.txt
```

Las dependencias incluyen:
- MediaPipe (visión por computador)
- OpenCV (procesamiento de video)
- Pygame (gráficos y sonidos del juego)
- NumPy (operaciones numéricas)

### 3. Descargar pesos del modelo MediaPipe:
```bash
python download_models.py
```

Este script descarga automáticamente los modelos de **Pose Landmarker** necesarios para el seguimiento de la pose.

## 🎯 Cómo Jugar

### Ejecutar el juego:
```bash
python fruit_game.py
```

### Controles:
- **ESPACIO**: Iniciar el juego / Reintentar después de Game Over
- **M**: Activar/Desactivar música
- **ESC**: Salir del juego

### Mecánicas del Juego:
1. **Posiciónate frente a la cámara** de modo que tu cara sea visible
2. **Mueve tu cabeza** hacia la izquierda o derecha para mover la cesta
3. **Atrapa frutas** 🍎🍌🍓🍉 para ganar puntos
4. **Evita bombas** 💣 o perderás una vida
5. **No dejes caer frutas** o también perderás una vida
6. El juego termina cuando pierdes todas las vidas (❤️❤️❤️)

## 🎨 Recursos del Juego

### Imágenes (`imgs/`):
- Frutas: manzana, plátano, fresa, sandía
- Bomba
- Cesta
- Corazones (vidas)
- Controles de volumen

### Sonidos (`sounds/`):
- Música de fondo del juego
- Efecto de sonido de moneda (atrapar fruta)
- Efecto de sonido de bomba
- Efecto de sonido de perder vida

## 🔧 Configuración

Puedes ajustar la configuración del juego en `config.py`:
- `fruit_speed`: Velocidad de caída de las frutas
- `fruit_interval`: Intervalo de creación de frutas (milisegundos)
- `bomb_probability`: Probabilidad de aparición de bombas (0.0 - 1.0)
- `initial_lives`: Número de vidas al inicio

## 📁 Estructura del Proyecto

```
IPM/
├── fruit_game.py          # Juego principal con integración de cámara
├── app.py                 # Juego original de ejemplo de MediaPipe
├── settings.py            # Configuración de recursos del juego
├── config.py              # Configuración general del proyecto
├── download_models.py     # Script para descargar modelos
├── requirements.txt       # Dependencias del proyecto
├── README_FRUIT_GAME.md   # Esta documentación
├── models/                # Modelos de MediaPipe
│   ├── pose_landmarker_lite.task
│   ├── pose_landmarker_full.task
│   └── pose_landmarker_heavy.task
├── imgs/                  # Recursos gráficos
│   ├── apple.png
│   ├── banana.png
│   ├── strawberry.png
│   ├── watermelon.png
│   ├── bomb.png
│   ├── bucket.png
│   ├── heart.png
│   ├── volume.png
│   └── mute.png
└── sounds/                # Recursos de audio
    ├── game_song.mp3
    ├── coin.mp3
    ├── bomb.mp3
    └── lost_life.mp3
```

## 🛠️ Tecnologías Utilizadas

- **Python 3.12**
- **MediaPipe**: Framework de visión por computador de Google
- **OpenCV**: Procesamiento de video en tiempo real
- **Pygame**: Motor de juego 2D y sistema de audio
- **NumPy**: Operaciones matriciales y manejo de imágenes

## 📊 Rendimiento

El juego está optimizado para funcionar en tiempo real:
- Detección de pose a 30 FPS
- Renderizado del juego a 120 FPS (limitado por el juego)
- Latencia mínima en el control

## 🎓 Propósito Educativo

Este proyecto combina:
- **Interacción Persona-Máquina (IPM/HCI)** basada en visión por computador
- **Aprendizaje Automático** con modelos preentrenados
- **Desarrollo de Videojuegos** con Pygame
- **Procesamiento de Video en Tiempo Real**

Es ideal para:
- Aprender sobre interfaces naturales de usuario
- Experimentar con visión por computador
- Desarrollar aplicaciones de rehabilitación o gamificación
- Explorar la integración de IA en videojuegos

## 🎯 Otros Proyectos con MediaPipe

MediaPipe ofrece otros modelos que puedes utilizar:
- **Hand Landmarker**: [Documentación](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker?hl=es-419)
- **Face Landmarker**: [Documentación](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/index?hl=es-419)
- **Holistic Landmarker**: [Documentación](https://ai.google.dev/edge/mediapipe/solutions/vision/holistic_landmarker?hl=es-419)

## 🐛 Solución de Problemas

### La cámara no se abre:
```bash
# Verificar permisos de cámara en tu sistema
# Asegurarte de que ninguna otra aplicación esté usando la cámara
```

### Errores de importación de Pygame:
```bash
pip install --upgrade pygame
```

### El tracking es inexacto:
- Asegúrate de tener buena iluminación
- Mantén tu cara visible y centrada en la cámara
- Prueba con el modelo `pose_landmarker_heavy.task` para mayor precisión

### Los sonidos no funcionan:
```bash
# En macOS, verifica los permisos de audio
# En Linux, asegúrate de tener instalado SDL_mixer
sudo apt-get install libsdl2-mixer-2.0-0
```

## 📝 Créditos

- **Juego Original Fruit Catcher**: [nberdi/Fruit-Catcher](https://github.com/nberdi/Fruit-Catcher)
- **MediaPipe**: Google LLC
- **Integración y Modificación**: Creado como proyecto educativo de IPM

## 📧 Contacto

Para preguntas o sugerencias sobre este proyecto, puedes contactar al autor original del juego base:
- berdinauryzbek@gmail.com
- [LinkedIn](https://www.linkedin.com/in/nauryzbekberdi/)

---

¡Disfruta jugando y aprendiendo sobre visión por computador! 🎮🍎🤖
