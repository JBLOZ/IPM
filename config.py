import os

class Config:
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), 'models/pose_landmarker_full.task')
        self.padding = 100
        self.game_time = 20     # Duración del juego en segundos (para el juego original)
        self.circle_time = 1    # Duración de cada circulo azul antes de que desaparezca (para el juego original)
        self.circle_time_radius = 15
        
        # Configuración para el juego de frutas
        self.fruit_game_width = 700
        self.fruit_game_height = 500
        self.fruit_speed = 3              # Velocidad de caída de las frutas
        self.fruit_interval = 1000        # Intervalo de creación de frutas (ms)
        self.bomb_probability = 0.2       # Probabilidad de que aparezca una bomba
        self.initial_lives = 3            # Vidas iniciales

config = Config()  # Instancia única