import sys
import cv2
import mediapipe as mp
import numpy as np
import pygame
import random
import time
from settings import *
from config import config

class FruitCatcherGame:
    def __init__(self):
        # Inicializar Pygame
        pygame.init()
        pygame.mixer.init()
        
        # Inicializar display para poder usar convert_alpha()
        pygame.display.set_mode((1, 1))
        
        # Cargar música y sonidos
        pygame.mixer.music.load(game_song)
        pygame.mixer.music.set_volume(0.5)
        
        self.bomb_sound = pygame.mixer.Sound(bomb_sound)
        self.score_sound = pygame.mixer.Sound(score_sound)
        self.lost_life_sound = pygame.mixer.Sound(lost_life_sound)
        
        # Escalar imágenes - frutas más grandes y convertir a RGBA para transparencia
        self.bucket_img = pygame.transform.scale(bucket_img.convert_alpha(), (80, 80))
        self.fruit_imgs = [pygame.transform.scale(img.convert_alpha(), (60, 60)) for img in fruit_list]
        # Definir nombres y valores por tipo de fruta (en el mismo orden que `fruit_list` en `settings.py`)
        # Orden en `settings.py`: apple, banana, strawberry, watermelon
        self.fruit_types = [
            {"name": "Manzana", "img": self.fruit_imgs[0], "value": 10},
            {"name": "Banana", "img": self.fruit_imgs[1], "value": 5},
            {"name": "Fresa", "img": self.fruit_imgs[2], "value": 15},
            {"name": "Sandia", "img": self.fruit_imgs[3], "value": 20},
        ]
        self.bomb_img = pygame.transform.scale(bomb_img.convert_alpha(), (60, 60))
        self.heart_img = pygame.transform.scale(heart_img.convert_alpha(), (30, 30))
        self.heart_falling_img = pygame.transform.scale(heart_img.convert_alpha(), (60, 60))  # Corazón para atrapar
        self.return_to_menu_img = pygame.transform.scale(return_to_menu, (30, 30))
        self.volume_img = pygame.transform.scale(volume, (30, 30))
        self.mute_img = pygame.transform.scale(mute, (30, 30))
        
        # Dimensiones fijas para proporción 16:9
        # La cámara central debe mantener proporción 6:9 (más ancha)
        self.camera_width = 720  # Ancho de la cámara (proporción 6)
        self.camera_height = 1080  # Alto de la cámara (proporción 9)
        
        # Ventana total en proporción 16:9
        # Altura = altura de la cámara
        self.window_height = self.camera_height  # 1080
        # Ancho = altura * (16/9)
        self.window_width = int(self.window_height * 16 / 9)  # 1920
        
        # Calcular el ancho de los paneles laterales para centrar la cámara
        total_side_space = self.window_width - self.camera_width
        self.panel_width = total_side_space // 2  # 600 cada lado
        
        # Variables del juego
        self.is_mute = False
        self.game_started = False
        self.game_over = False
        self.return_to_menu = False
        
        # Fuentes
        self.font = pygame.font.SysFont(None, 36)
        self.header_font = pygame.font.SysFont(None, 72)
        self.small_font = pygame.font.SysFont(None, 24)
        
        # Variables de frutas
        self.created_fruits = []
        self.last_fruit_time = 0
        self.base_fruit_interval = 1000  # ms - intervalo base
        self.fruit_interval = 1000  # ms - intervalo actual (se ajusta dinámicamente)
        self.fruit_speed = 3
        self.max_fruit_speed = 25  # Velocidad máxima
        self.speed_increment = 0.5  # Incremento de velocidad por fruta atrapada
        
        # Variables del jugador
        self.bucket_x = 325  # posición inicial
        self.score = 0
        self.lives = 3
        self.highest_score = 0
        # Modo de juego: 1=cabeza, 2=mano derecha, 3=mano izquierda
        self.play_mode = 1
        
        # MediaPipe setup
        BaseOptions = mp.tasks.BaseOptions
        PoseLandmarker = mp.tasks.vision.PoseLandmarker
        PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode
        
        self.options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=config.model_path),
            running_mode=VisionRunningMode.VIDEO,
            num_poses=1
        )
        
        self.mp_pose = mp.solutions.pose
        self.PoseLandmarker = mp.tasks.vision.PoseLandmarker
        
    def reset_game(self):
        """Reinicia el juego a su estado inicial"""
        self.created_fruits = []
        self.last_fruit_time = 0
        self.bucket_x = 325
        self.bucket_y = 200  # Posición vertical de la cesta (en la cabeza)
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.return_to_menu = False
        self.fruit_speed = 3  # Reiniciar velocidad
        
    def create_new_fruit(self, frame_width):
        """Crea nuevas frutas, bombas o corazones que caen"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_fruit_time >= self.fruit_interval:
            # Determinar qué tipo de objeto cae
            rand_val = random.random()
            
            # Corazones solo aparecen si el jugador tiene 2 vidas o menos
            if rand_val < 0.02 and self.lives <= 2:  # 2% probabilidad de corazón (solo si lives <= 2)
                is_heart = True
                is_bomb = False
            elif rand_val < 0.22:  # 20% probabilidad de bomba
                is_heart = False
                is_bomb = True
            else:  # 78% probabilidad de fruta
                is_heart = False
                is_bomb = False
            
            max_x = frame_width - 60
            # Seleccionar fruta (si no es bomba/ corazón) y guardar su nombre/valor
            if is_heart:
                chosen_img = self.heart_falling_img
                chosen_name = "Corazón"
                chosen_value = 0
            elif is_bomb:
                chosen_img = self.bomb_img
                chosen_name = "Bomba"
                chosen_value = 0
            else:
                chosen_type = random.choice(self.fruit_types)
                chosen_img = chosen_type["img"]
                chosen_name = chosen_type["name"]
                chosen_value = chosen_type["value"]

            new_fruit = {
                "x": random.randint(0, max(max_x, 100)),
                "y": 0,
                "img": chosen_img,
                "is_bomb": is_bomb,
                "is_heart": is_heart,
                "name": chosen_name,
                "value": chosen_value,
            }
            self.created_fruits.append(new_fruit)
            self.last_fruit_time = current_time
            
    def update_fruits(self, frame_height):
        """Actualiza la posición de las frutas y verifica colisiones"""
        # Ajustar el intervalo de frutas según la velocidad para mantener densidad similar
        # A mayor velocidad, menor intervalo (más frutas)
        speed_ratio = self.fruit_speed / 5.0  # Ratio respecto a velocidad inicial
        self.fruit_interval = max(500, int(self.base_fruit_interval / speed_ratio))  # Mínimo 300ms
        
        for fruit in self.created_fruits[:]:
            fruit["y"] += self.fruit_speed
            
            # Verificar colisión
            if self.check_collision(fruit):
                if fruit["is_bomb"]:
                    self.bomb_sound.play()
                    self.lives -= 1
                    self.lost_life_sound.play()
                elif fruit.get("is_heart", False):
                    # Atrapar corazón: recuperar vida (máximo 3 vidas)
                    if self.lives < 3:
                        self.lives += 1
                        self.score_sound.play()
                else:
                    # Atrapar fruta: sumar su valor
                    self.score_sound.play()
                    added = fruit.get("value", 1)
                    self.score += added
                    # Incrementar velocidad progresivamente hasta el máximo
                    if self.fruit_speed < self.max_fruit_speed:
                        self.fruit_speed += self.speed_increment
                self.created_fruits.remove(fruit)
            # Verificar si la fruta salió de la pantalla
            elif fruit["y"] > frame_height:
                self.created_fruits.remove(fruit)
                # Solo perder vida si es una fruta (no bomba ni corazón)
                if not fruit["is_bomb"] and not fruit.get("is_heart", False):
                    self.lost_life_sound.play()
                    self.lives -= 1
                    
        # Verificar game over
        if self.lives <= 0:
            self.game_over = True
            if self.score > self.highest_score:
                self.highest_score = self.score
                
    def check_collision(self, fruit):
        """Verifica si una fruta colisiona con la cesta"""
        bucket_rect = pygame.Rect(self.bucket_x, self.bucket_y, 80, 80)
        fruit_rect = pygame.Rect(fruit["x"], fruit["y"], 60, 60)
        return bucket_rect.colliderect(fruit_rect)
    
    def update_bucket_position(self, x_norm, y_norm, frame_width, frame_height, mode=None):
        """Actualiza la posición de la cesta basándose en coordenadas normalizadas.
        mode: 1=cabeza, 2=mano derecha, 3=mano izquierda
        """
        if x_norm is not None and y_norm is not None:
            # Mapear la posición normalizada al tamaño del frame
            self.bucket_x = int(x_norm * frame_width) - 40  # Centrar la cesta
            # Ajustar verticalmente según el modo
            if mode == 1 or mode is None:
                # Cabeza: colocar la cesta encima de la nariz (como antes)
                offset_y = int(frame_height * 0.25)
                self.bucket_y = int(y_norm * frame_height) - offset_y
            else:
                # Mano: colocar la cesta centrada en la palma.
                # Usamos la coordenada de la muñeca/palma y colocamos la
                # cesta de modo que su centro vertical coincida con la palma.
                bucket_h = 80
                self.bucket_y = int(y_norm * frame_height) - (bucket_h // 2)

            # Limitar dentro de los bordes
            self.bucket_x = max(0, min(self.bucket_x, frame_width - 80))
            self.bucket_y = max(0, min(self.bucket_y, frame_height - 80))
    
    # --- RETRO 80s CONSTANTS ---
    NEON_PINK = (180, 105, 255)      # Hot Pink (BGR)
    NEON_CYAN = (255, 255, 0)        # Cyan (BGR)
    NEON_GREEN = (50, 255, 50)       # Lime Green (BGR)
    NEON_YELLOW = (0, 255, 255)      # Bright Yellow (BGR)
    NEON_PURPLE = (255, 0, 255)      # Magenta/Purple (BGR)
    GRID_COLOR = (50, 0, 50)         # Dark Purple for grid
    
    # Precomputed masks
    crt_mask = None
    
    def _init_crt_masks(self, width, height):
        """Precalcula las máscaras para el efecto CRT"""
        # 1. Scanlines (lineas horizontales oscuras)
        scanline_mask = np.ones((height, width, 3), dtype=np.float32)
        scanline_mask[1::2, :] = 0.75  # Oscurecer lineas alternas
        
        # 2. Vignette (oscurecer bordes)
        X_result, Y_result = np.meshgrid(np.linspace(-1, 1, width), np.linspace(-1, 1, height))
        distance_map = np.sqrt(X_result**2 + Y_result**2)
        vignette_mask = 1 - np.clip(distance_map - 0.4, 0, 1) * 0.6
        vignette_mask = np.stack([vignette_mask] * 3, axis=2)
        
        # Combinar ambas máscaras en una sola
        self.crt_mask = (scanline_mask * vignette_mask).astype(np.float32)

    def draw_neon_text(self, img, text, pos, font_scale, color, thickness=2, font=cv2.FONT_HERSHEY_TRIPLEX):
        """Dibuja texto con efecto de brillo neon"""
        x, y = pos
        # Glow effect (thick dark outline/shadow)
        cv2.putText(img, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)
        # Inner bright core
        cv2.putText(img, text, (x, y), font, font_scale, (255, 255, 255), 1, cv2.LINE_AA)

    def apply_crt_effect(self, canvas):
        """Aplica efecto de scanlines y viñeta usando máscara precalculada"""
        h, w = canvas.shape[:2]
        
        # Inicializar máscara si no existe o si cambió el tamaño
        if self.crt_mask is None or self.crt_mask.shape[:2] != (h, w):
            self._init_crt_masks(w, h)
            
        # Aplicar efectos usando multiplicación rápida
        # Convertir canvas a float, multiplicar por mascara, y volver a uint8
        # Optimizacion: cv2.multiply maneja uint8 * float si se usa correctamente, 
        # pero aquí lo más rápido y seguro en Python puro es:
        
        return cv2.multiply(canvas, self.crt_mask, dtype=cv2.CV_8U)

    def draw_game_overlay(self, frame):
        """Dibuja los elementos del juego sobre el frame de la cámara con diseño vertical"""
        h, w = frame.shape[:2]
        
        # El frame ya viene recortado a proporción 6:9 y escalado desde el loop principal
        
        # Crear canvas con proporción 16:9
        total_width = self.window_width
        total_height = self.window_height
        
        # Crear canvas negro (fondo retro)
        canvas = np.zeros((total_height, total_width, 3), dtype=np.uint8)
        
        # Dibujar Grid Retro en el fondo (paneles laterales)
        grid_size = 40
        # Lineas verticales
        for x in range(0, total_width, grid_size):
            cv2.line(canvas, (x, 0), (x, total_height), self.GRID_COLOR, 1)
        # Lineas horizontales
        for y in range(0, total_height, grid_size):
            cv2.line(canvas, (0, y), (total_width, y), self.GRID_COLOR, 1)
            
        # Colocar el frame de la cámara en el centro
        # Dibujar borde neon alrededor de la camara
        cv2.rectangle(canvas, 
                     (self.panel_width - 5, 0), 
                     (self.panel_width + w + 5, h), 
                     self.NEON_PURPLE, -1)
        
        canvas[0:h, self.panel_width:self.panel_width+w] = frame
        
        # Dibujar frutas usando el canal alfa (ajustando posición X)
        for fruit in self.created_fruits:
            fruit_surface = fruit["img"]
            
            y_pos = int(fruit["y"])
            x_pos = int(fruit["x"]) + self.panel_width  # Ajustar para el panel izquierdo
            
            if 0 <= y_pos < h - 60 and self.panel_width <= x_pos < self.panel_width + w - 60:
                # Obtener array RGBA
                fruit_rgba = pygame.surfarray.array3d(fruit_surface)
                fruit_alpha = pygame.surfarray.array_alpha(fruit_surface)
                
                # Transponer y convertir RGB a BGR
                fruit_bgr = cv2.cvtColor(np.transpose(fruit_rgba, (1, 0, 2)), cv2.COLOR_RGB2BGR)
                alpha = np.transpose(fruit_alpha)
                
                # Normalizar alpha a rango 0-1
                alpha_normalized = alpha.astype(float) / 255.0
                alpha_3ch = np.stack([alpha_normalized] * 3, axis=2)
                
                # Extraer región de interés del canvas
                roi = canvas[y_pos:y_pos+60, x_pos:x_pos+60]
                
                # Mezclar usando alpha blending
                blended = (fruit_bgr * alpha_3ch + roi * (1 - alpha_3ch)).astype(np.uint8)
                canvas[y_pos:y_pos+60, x_pos:x_pos+60] = blended
    
        # Dibujar cesta usando el canal alfa (ajustando posición X)
        y_pos = int(self.bucket_y)
        x_pos = int(self.bucket_x) + self.panel_width  # Ajustar para el panel izquierdo
        
        if 0 <= y_pos < h - 80 and self.panel_width <= x_pos < self.panel_width + w - 80:
            bucket_rgba = pygame.surfarray.array3d(self.bucket_img)
            bucket_alpha = pygame.surfarray.array_alpha(self.bucket_img)
            
            bucket_bgr = cv2.cvtColor(np.transpose(bucket_rgba, (1, 0, 2)), cv2.COLOR_RGB2BGR)
            alpha = np.transpose(bucket_alpha)
            
            alpha_normalized = alpha.astype(float) / 255.0
            alpha_3ch = np.stack([alpha_normalized] * 3, axis=2)
            
            roi = canvas[y_pos:y_pos+80, x_pos:x_pos+80]
            blended = (bucket_bgr * alpha_3ch + roi * (1 - alpha_3ch)).astype(np.uint8)
            canvas[y_pos:y_pos+80, x_pos:x_pos+80] = blended
        
        # === PANEL IZQUIERDO: Puntuación y Vidas ===
        left_x = 40
        
        # Titulo SCORE
        self.draw_neon_text(canvas, 'SCORE', (left_x, 60), 1.0, self.NEON_CYAN)
        # Valor SCORE
        self.draw_neon_text(canvas, f'{self.score:05d}', (left_x, 120), 1.5, self.NEON_PINK)

        # Vidas debajo de la puntuación
        self.draw_neon_text(canvas, 'LIVES', (left_x, 200), 1.0, self.NEON_CYAN)
        
        for i in range(self.lives):
            y_heart = 240 + i * 50
            if y_heart < total_height - 30:
                heart_size = 30
                heart_large = pygame.transform.scale(self.heart_img, (heart_size, heart_size))
                heart_rgba = pygame.surfarray.array3d(heart_large)
                heart_alpha = pygame.surfarray.array_alpha(heart_large)
                heart_bgr = cv2.cvtColor(np.transpose(heart_rgba, (1, 0, 2)), cv2.COLOR_RGB2BGR)
                alpha = np.transpose(heart_alpha)
                alpha_normalized = alpha.astype(float) / 255.0
                alpha_3ch = np.stack([alpha_normalized] * 3, axis=2)
                x_heart_pos = left_x + 10
                roi = canvas[y_heart:y_heart+heart_size, x_heart_pos:x_heart_pos+heart_size]
                blended = (heart_bgr * alpha_3ch + roi * (1 - alpha_3ch)).astype(np.uint8)
                canvas[y_heart:y_heart+heart_size, x_heart_pos:x_heart_pos+heart_size] = blended

        # Mostrar la velocidad
        self.draw_neon_text(canvas, 'SPEED', (left_x, 420), 0.8, self.NEON_CYAN)
        # Barra de velocidad retro
        bar_width = 150
        bar_height = 20
        fill_width = int((self.fruit_speed / self.max_fruit_speed) * bar_width)
        cv2.rectangle(canvas, (left_x, 450), (left_x + bar_width, 450 + bar_height), (50, 50, 50), -1) # Fondo barra
        cv2.rectangle(canvas, (left_x, 450), (left_x + fill_width, 450 + bar_height), self.NEON_YELLOW, -1) # Relleno
        cv2.rectangle(canvas, (left_x, 450), (left_x + bar_width, 450 + bar_height), (255, 255, 255), 2) # Borde

        # === LISTA DE PUNTUACIONES POR FRUTA ===
        self.draw_neon_text(canvas, 'VALUES', (left_x, 520), 0.8, self.NEON_CYAN)
        
        start_y = 560
        row_h = 50
        for idx, ftype in enumerate(self.fruit_types):
            y_row = start_y + idx * row_h
            if y_row + 40 >= total_height:
                break
            # Dibujar icono
            icon_size = 36
            icon = pygame.transform.scale(ftype["img"], (icon_size, icon_size))
            icon_rgba = pygame.surfarray.array3d(icon)
            icon_alpha = pygame.surfarray.array_alpha(icon)
            icon_bgr = cv2.cvtColor(np.transpose(icon_rgba, (1, 0, 2)), cv2.COLOR_RGB2BGR)
            alpha = np.transpose(icon_alpha)
            alpha_normalized = alpha.astype(float) / 255.0
            alpha_3ch = np.stack([alpha_normalized] * 3, axis=2)
            x_icon = left_x
            roi = canvas[y_row:y_row+icon_size, x_icon:x_icon+icon_size]
            blended = (icon_bgr * alpha_3ch + roi * (1 - alpha_3ch)).astype(np.uint8)
            canvas[y_row:y_row+icon_size, x_icon:x_icon+icon_size] = blended

            # Texto
            text_x = x_icon + icon_size + 15
            self.draw_neon_text(canvas, f'{ftype["value"]} PTS', (text_x, y_row + 26), 0.6, self.NEON_GREEN)
        
        # Aplicar efecto CRT final
        return self.apply_crt_effect(canvas)
    
    def draw_start_screen(self):
        """Dibuja la pantalla de inicio con estilo retro"""
        h = self.window_height
        w = self.window_width
        
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Grid de fondo
        grid_size = 50
        for x in range(0, w, grid_size):
            cv2.line(canvas, (x, 0), (x, h), self.GRID_COLOR, 1)
        for y in range(0, h, grid_size):
            cv2.line(canvas, (0, y), (w, y), self.GRID_COLOR, 1)

        center_x = w // 2

        # Title
        title = 'FRUIT CATCHER'
        (t_w, t_h), _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_TRIPLEX, 3.0, 5)
        self.draw_neon_text(canvas, title, (center_x - t_w // 2, 250), 3.0, self.NEON_PINK, 5)

        # Subtitle
        subtitle = 'RETRO EDITION'
        (s_w, s_h), _ = cv2.getTextSize(subtitle, cv2.FONT_HERSHEY_TRIPLEX, 1.5, 3)
        self.draw_neon_text(canvas, subtitle, (center_x - s_w // 2, 320), 1.5, self.NEON_CYAN, 3)

        # Blinking "INSERT COIN" (Press Space)
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            msg = 'PRESS SPACE TO START'
            (m_w, m_h), _ = cv2.getTextSize(msg, cv2.FONT_HERSHEY_TRIPLEX, 1.2, 2)
            self.draw_neon_text(canvas, msg, (center_x - m_w // 2, 500), 1.2, self.NEON_YELLOW, 2)

        # Instructions
        instr1 = 'MOVE HEAD TO CONTROL BUCKET'
        instr2 = 'AVOID BOMBS!'
        (i1_w, _), _ = cv2.getTextSize(instr1, cv2.FONT_HERSHEY_TRIPLEX, 0.8, 2)
        (i2_w, _), _ = cv2.getTextSize(instr2, cv2.FONT_HERSHEY_TRIPLEX, 0.8, 2)
        
        self.draw_neon_text(canvas, instr1, (center_x - i1_w // 2, 600), 0.8, self.NEON_GREEN)
        self.draw_neon_text(canvas, instr2, (center_x - i2_w // 2, 650), 0.8, self.NEON_GREEN)

        # Exit
        exit_msg = 'PRESS ESC TO EXIT'
        (e_w, _), _ = cv2.getTextSize(exit_msg, cv2.FONT_HERSHEY_TRIPLEX, 0.7, 1)
        self.draw_neon_text(canvas, exit_msg, (center_x - e_w // 2, 800), 0.7, (200, 200, 200))

        # Modes
        m_start_y = 860
        modes = [
            "1. HEAD CONTROL",
            "2. RIGHT HAND",
            "3. LEFT HAND"
        ]
        for i, mode_text in enumerate(modes):
            color = self.NEON_GREEN if self.play_mode == (i+1) else (100, 100, 100)
            (mw, _), _ = cv2.getTextSize(mode_text, cv2.FONT_HERSHEY_TRIPLEX, 0.8, 2)
            self.draw_neon_text(canvas, mode_text, (center_x - mw // 2, m_start_y + i*40), 0.8, color)
        
        return self.apply_crt_effect(canvas)
    
    def draw_game_over_screen(self):
        """Dibuja la pantalla de game over retro"""
        h = self.window_height
        w = self.window_width
        
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Grid
        grid_size = 50
        for x in range(0, w, grid_size):
            cv2.line(canvas, (x, 0), (x, h), self.GRID_COLOR, 1)
        for y in range(0, h, grid_size):
            cv2.line(canvas, (0, y), (w, y), self.GRID_COLOR, 1)
        
        center_x = w // 2

        # GAME OVER
        title = 'GAME OVER'
        (t_w, t_h), _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_TRIPLEX, 3.0, 5)
        self.draw_neon_text(canvas, title, (center_x - t_w // 2, 250), 3.0, (0, 0, 255), 5) # Red Neon

        # Scores
        score_text = f'SCORE: {self.score}'
        best_text = f'HIGH SCORE: {self.highest_score}'
        
        (sc_w, _), _ = cv2.getTextSize(score_text, cv2.FONT_HERSHEY_TRIPLEX, 1.5, 3)
        (b_w, _), _ = cv2.getTextSize(best_text, cv2.FONT_HERSHEY_TRIPLEX, 1.5, 3)
        
        self.draw_neon_text(canvas, score_text, (center_x - sc_w // 2, 400), 1.5, self.NEON_CYAN)
        self.draw_neon_text(canvas, best_text, (center_x - b_w // 2, 460), 1.5, self.NEON_YELLOW)

        # Retry
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            retry = 'PRESS SPACE TO RETRY'
            (r_w, _), _ = cv2.getTextSize(retry, cv2.FONT_HERSHEY_TRIPLEX, 1.2, 2)
            self.draw_neon_text(canvas, retry, (center_x - r_w // 2, 600), 1.2, self.NEON_GREEN)

        return self.apply_crt_effect(canvas)
    
    def run(self):
        """Loop principal del juego"""
        win_name = "Fruit Catcher - Camera Edition"
        with self.PoseLandmarker.create_from_options(self.options) as landmarker:
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                print("Error: No se pudo abrir la cámara")
                return
            
            # Configurar resolución de la cámara con proporción 6:9
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
            
            # Configurar FPS a 30
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps == 0:
                fps = 30  # Forzar 30 FPS si la cámara no devuelve un valor válido
            
            frame_ms = int(1000 / fps)
            timestamp = 0
            
            # Reproducir música
            if not self.is_mute:
                pygame.mixer.music.play(-1)
            
            # Configurar ventana con proporción 16:9
            cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(win_name, self.window_width, self.window_height)
            
            while True:
                canvas = None
                if self.game_started and not self.game_over:
                    # Leer y procesar frame de cámara solo durante el juego
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Voltear frame horizontalmente
                    frame = cv2.flip(frame, 1)
                    
                    # Convertir a formato MediaPipe
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                    
                    # Detectar pose
                    result = landmarker.detect_for_video(mp_image, timestamp)
                    timestamp += frame_ms
                    
                    # Obtener posición de la nariz y muñecas si hay detección
                    nose_x = None
                    nose_y = None
                    left_wrist_x = None
                    left_wrist_y = None
                    right_wrist_x = None
                    right_wrist_y = None
                    if result.pose_landmarks:
                        for person_landmarks in result.pose_landmarks:
                            # Landmark 0 es la nariz
                            try:
                                nose = person_landmarks[0]
                                nose_x = nose.x
                                nose_y = nose.y
                            except Exception:
                                nose_x = None
                                nose_y = None
                            # Landmarks 15 y 16 son muñecas (left=15, right=16)
                            try:
                                lw = person_landmarks[15]
                                left_wrist_x = lw.x
                                left_wrist_y = lw.y
                            except Exception:
                                left_wrist_x = None
                                left_wrist_y = None
                            try:
                                rw = person_landmarks[16]
                                right_wrist_x = rw.x
                                right_wrist_y = rw.y
                            except Exception:
                                right_wrist_x = None
                                right_wrist_y = None
                    
                    # Recortar frame a proporción 6:9 ANTES de procesar el juego
                    h_original, w_original = frame.shape[:2]
                    target_aspect = 6 / 9  # Proporción 6:9 (más ancha que 9:14)
                    current_aspect = w_original / h_original
                    
                    start_x = 0
                    start_y = 0
                    
                    if current_aspect > target_aspect:
                        # Frame es más ancho, recortar los lados
                        new_width = int(h_original * target_aspect)
                        start_x = (w_original - new_width) // 2
                        frame = frame[:, start_x:start_x+new_width]
                    else:
                        # Frame es más alto, recortar arriba y abajo
                        new_height = int(w_original / target_aspect)
                        start_y = (h_original - new_height) // 2
                        frame = frame[start_y:start_y+new_height, :]
                    
                    # Ajustar coordenadas de nariz y muñecas al frame recortado
                    def adjust_norm_coords(norm_x, norm_y):
                        if norm_x is None or norm_y is None:
                            return None, None
                        x_pixel = norm_x * w_original
                        y_pixel = norm_y * h_original
                        adj_x = (x_pixel - start_x) / frame.shape[1]
                        adj_y = (y_pixel - start_y) / frame.shape[0]
                        adj_x = max(0.0, min(1.0, adj_x))
                        adj_y = max(0.0, min(1.0, adj_y))
                        return adj_x, adj_y

                    nose_x_adjusted, nose_y_adjusted = adjust_norm_coords(nose_x, nose_y)
                    left_wrist_x_adjusted, left_wrist_y_adjusted = adjust_norm_coords(left_wrist_x, left_wrist_y)
                    right_wrist_x_adjusted, right_wrist_y_adjusted = adjust_norm_coords(right_wrist_x, right_wrist_y)
                    
                    # Escalar el frame para que ocupe toda la altura de la ventana
                    h_before_scale = frame.shape[0]
                    w_before_scale = frame.shape[1]
                    scale_factor = 1.0
                    
                    if h_before_scale != self.window_height:
                        scale_factor = self.window_height / h_before_scale
                        new_width = int(w_before_scale * scale_factor)
                        frame = cv2.resize(frame, (new_width, self.window_height), interpolation=cv2.INTER_LINEAR)
                    
                    # Actualizar posición de la cesta con dimensiones escaladas según modo seleccionado
                    chosen_x = None
                    chosen_y = None
                    if self.play_mode == 1:
                        chosen_x, chosen_y = nose_x_adjusted, nose_y_adjusted
                    elif self.play_mode == 2:
                        # Player selected 'mano derecha' — use the LEFT wrist adjusted
                        # because the camera image is mirrored; this makes the
                        # basket follow the player's real right hand on screen.
                        chosen_x, chosen_y = left_wrist_x_adjusted, left_wrist_y_adjusted
                    elif self.play_mode == 3:
                        # Player selected 'mano izquierda' — use the RIGHT wrist adjusted
                        chosen_x, chosen_y = right_wrist_x_adjusted, right_wrist_y_adjusted

                    if chosen_x is not None and chosen_y is not None:
                        self.update_bucket_position(chosen_x, chosen_y, frame.shape[1], frame.shape[0], mode=self.play_mode)
                    
                    # Crear y actualizar frutas con el ancho del frame escalado
                    self.create_new_fruit(frame.shape[1])
                    self.update_fruits(frame.shape[0])
                    
                    # Dibujar overlay del juego
                    canvas = self.draw_game_overlay(frame)
                else:
                    # Pantallas de inicio o game over, sin cámara
                    if not self.game_started:
                        canvas = self.draw_start_screen()
                    else:
                        canvas = self.draw_game_over_screen()
                
                # Simplemente mostrar el canvas sin intentar obtener el tamaño de la ventana
                # (compatible con todas las versiones de OpenCV)
                display_frame = canvas
                
                # Mostrar frame
                
                # Calcular y mostrar FPS
                current_ticks = cv2.getTickCount()
                fps_calc = cv2.getTickFrequency() / (current_ticks - timestamp_fps_start) if 'timestamp_fps_start' in locals() else 30.0
                timestamp_fps_start = current_ticks
                
                cv2.putText(display_frame, f"FPS: {int(fps_calc)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow(win_name, display_frame)
                
                # Manejar teclas
                key = cv2.waitKey(1) & 0xFF

                if key == 27:  # ESC
                    break
                elif key == 32:  # ESPACIO
                    if not self.game_started:
                        self.game_started = True
                        self.reset_game()
                    elif self.game_over:
                        self.reset_game()
                        self.game_over = False  # Asegurar que no esté en game over
                # Selección de modo en pantalla de inicio (1,2,3)
                elif not self.game_started and key in (ord('1'), ord('2'), ord('3')):
                    sel = int(chr(key))
                    if sel in (1, 2, 3):
                        self.play_mode = sel
                elif key == ord('m') or key == ord('M'):  # Mute/Unmute
                    self.is_mute = not self.is_mute
                    if self.is_mute:
                        pygame.mixer.music.stop()
                    else:
                        pygame.mixer.music.play(-1)
            
            cap.release()
            cv2.destroyAllWindows()
            pygame.quit()

if __name__ == "__main__":
    game = FruitCatcherGame()
    game.run()
