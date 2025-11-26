# Fruit Catcher - Retro Edition

[Ver video del juego](https://www.youtube.com/watch?v=NOrhn-qOLtM)

## Descripción
Fruit Catcher es un juego interactivo diseñado para fomentar el movimiento y la coordinación. Es ideal para personas con movilidad reducida, ya que ofrece distintos modos de juego que permiten jugar utilizando diferentes partes del cuerpo, como la cabeza o las manos. El juego utiliza la cámara para detectar movimientos y controlar la cesta que atrapa frutas.

## Reglas del Juego
- **Objetivo:** Atrapa tantas frutas como puedas para obtener la mayor puntuación posible.
- **Frutas:** Cada fruta tiene un valor diferente:
  - Banana: 5 puntos
  - Manzana: 10 puntos
  - Fresa: 15 puntos
  - Sandía: 20 puntos
- **Bombas:** Evita las bombas. Si atrapas una, pierdes una vida.
- **Vidas:**
  - Comenzarás con 3 vidas.
  - Si no atrapas una fruta o atrapas una bomba, pierdes una vida.
  - Si tienes 2 vidas o menos, existe una probabilidad del 2% de que caiga un corazón que te permitirá recuperar una vida (hasta un máximo de 3).
- **Velocidad:** La velocidad de caída de las frutas aumenta cada vez que atrapas una fruta.

## Modos de Juego
El juego ofrece tres modos de control:
1. **Control con la cabeza:** Mueve la cabeza para controlar la posición de la cesta.
2. **Control con la mano derecha:** Usa tu mano derecha para mover la cesta.
3. **Control con la mano izquierda:** Usa tu mano izquierda para mover la cesta.

## Instalación y Ejecución
### Requisitos
- Una cámara web funcional
- Sistema operativo compatible con Bash (Linux, Mac o Git Bash en Windows)

### Instalación y Ejecución
1. Clona este repositorio:
   ```bash
   git clone https://github.com/JBLOZ/IPM.git
   cd IPM
   ```
2. Ejecuta el script de instalación:
   ```bash
   bash setup_fruitgame.sh
   ```
   Este script realizará las siguientes acciones automáticamente:
   - Detectará si tienes Python 3.11 instalado. Si no está disponible se instalará automáticamente, si falla la instalación te indicará como instalarlo manualmente.
   - Creará un entorno virtual (venv).
   - Activará el entorno virtual.
   - Instalará las dependencias listadas en `requirements.txt`.

3. Una vez completado, el sistema estará listo para ejecutar el juego. Para iniciarlo, sigue estos pasos:
   ```bash
   source venv/bin/activate  # En Linux/Mac
   source venv/Scripts/activate  # En Windows (Git Bash)
   python fruit_game.py
   ```

## Estructura del Proyecto
- **`fruit_game.py`**: Contiene la lógica principal del juego.
- **`settings.py`**: Define configuraciones y constantes utilizadas en el juego, como imágenes y sonidos.
- **`config.py`**: Contiene configuraciones específicas, como la ruta al modelo de MediaPipe.
- **`requirements.txt`**: Lista de dependencias necesarias para ejecutar el juego.
- **`setup_fruitgame.sh`**: Script para configurar y ejecutar el juego.
- **`models/`**: Carpeta que contiene los modelos de MediaPipe necesarios para la detección de poses.
- **`imgs/`**: Carpeta con las imágenes utilizadas en el juego.
- **`sounds/`**: Carpeta con los efectos de sonido y música del juego.
- **`README.md`**: Este archivo, que explica cómo instalar, ejecutar y entender el proyecto.
