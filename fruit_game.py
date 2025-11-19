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
            {"name": "Sandía", "img": self.fruit_imgs[3], "value": 20},
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
    
    def draw_game_overlay(self, frame):
        """Dibuja los elementos del juego sobre el frame de la cámara con diseño vertical"""
        h, w = frame.shape[:2]
        
        # El frame ya viene recortado a proporción 6:9 y escalado desde el loop principal
        
        # Crear canvas con proporción 16:9
        total_width = self.window_width
        total_height = self.window_height
        
        # Crear canvas negro
        canvas = np.zeros((total_height, total_width, 3), dtype=np.uint8)
        
        # Colocar el frame de la cámara en el centro
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
        left_x = 20
        cv2.putText(canvas, 'SCORE', (left_x, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, f'{self.score}', (left_x + 20, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3, cv2.LINE_AA)

        # Vidas debajo de la puntuación
        cv2.putText(canvas, 'VIDAS', (left_x, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
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
                x_heart_pos = left_x + 40
                roi = canvas[y_heart:y_heart+heart_size, x_heart_pos:x_heart_pos+heart_size]
                blended = (heart_bgr * alpha_3ch + roi * (1 - alpha_3ch)).astype(np.uint8)
                canvas[y_heart:y_heart+heart_size, x_heart_pos:x_heart_pos+heart_size] = blended

        # Mostrar la velocidad (un poco más abajo a la derecha del panel izquierdo)
        cv2.putText(canvas, 'SPEED', (left_x, 420), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, f'{self.fruit_speed:.1f}', (left_x + 20, 460), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2, cv2.LINE_AA)

        # === LISTA DE PUNTUACIONES POR FRUTA (debajo de vidas y puntuacion) ===
        cv2.putText(canvas, 'PUNTUACIONES', (left_x, 520), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        # Dibujar cada fruta con su icono y valor
        start_y = 560
        row_h = 48
        for idx, ftype in enumerate(self.fruit_types):
            y_row = start_y + idx * row_h
            if y_row + 40 >= total_height:
                break
            # Dibujar icono (pequeño)
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

            # Texto con el nombre y puntos
            text_x = x_icon + icon_size + 10
            cv2.putText(canvas, f'{ftype["name"]}: {ftype["value"]} pts', (text_x, y_row + 26), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 220, 220), 2, cv2.LINE_AA)
        
        return canvas
    
    def draw_start_screen(self):
        """Dibuja la pantalla de inicio con fondo negro (sin cámara)"""
        h = self.window_height
        w = self.window_width
        
        # Crear fondo completamente negro con proporción 16:9
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Centrar todo en el canvas completo
        center_x = w // 2

        # Title centered
        title = 'FRUIT CATCHER'
        title_scale = 3.0
        title_thick = 5
        (t_w, t_h), t_base = cv2.getTextSize(title, cv2.FONT_HERSHEY_SIMPLEX, title_scale, title_thick)
        cv2.putText(canvas, title, (center_x - t_w // 2, 250), cv2.FONT_HERSHEY_SIMPLEX, title_scale, (255, 255, 255), title_thick)

        # Subtitle centered
        subtitle = 'Camera Edition'
        sub_scale = 1.5
        sub_thick = 3
        (s_w, s_h), s_base = cv2.getTextSize(subtitle, cv2.FONT_HERSHEY_SIMPLEX, sub_scale, sub_thick)
        cv2.putText(canvas, subtitle, (center_x - s_w // 2, 320), cv2.FONT_HERSHEY_SIMPLEX, sub_scale, (255, 255, 255), sub_thick)

        # Instrucciones (centred). We'll highlight the key words.
        instr_scale = 1.0
        instr_thick = 2
        instr_full = 'Presiona ESPACIO para comenzar'
        # Split so we can color the key
        prefix = 'Presiona '
        key = 'ESPACIO'
        suffix = ' para comenzar'
        (p_w, p_h), _ = cv2.getTextSize(prefix, cv2.FONT_HERSHEY_SIMPLEX, instr_scale, instr_thick)
        (k_w, k_h), _ = cv2.getTextSize(key, cv2.FONT_HERSHEY_SIMPLEX, instr_scale, instr_thick)
        (u_w, u_h), _ = cv2.getTextSize(suffix, cv2.FONT_HERSHEY_SIMPLEX, instr_scale, instr_thick)
        total_w = p_w + k_w + u_w
        start_x = center_x - total_w // 2
        y_instr = 450
        cv2.putText(canvas, prefix, (start_x, y_instr), cv2.FONT_HERSHEY_SIMPLEX, instr_scale, (255, 255, 255), instr_thick)
        cv2.putText(canvas, key, (start_x + p_w, y_instr), cv2.FONT_HERSHEY_SIMPLEX, instr_scale, (50, 205, 50), instr_thick)
        cv2.putText(canvas, suffix, (start_x + p_w + k_w, y_instr), cv2.FONT_HERSHEY_SIMPLEX, instr_scale, (255, 255, 255), instr_thick)

        # Other instructions centered using measured text widths
        other1 = 'Mueve tu cabeza para mover la cesta'
        other2 = 'Atrapa frutas y evita bombas!'
        o_scale = 0.9
        o_thick = 2
        (o1_w, o1_h), _ = cv2.getTextSize(other1, cv2.FONT_HERSHEY_SIMPLEX, o_scale, o_thick)
        (o2_w, o2_h), _ = cv2.getTextSize(other2, cv2.FONT_HERSHEY_SIMPLEX, o_scale, o_thick)
        cv2.putText(canvas, other1, (center_x - o1_w // 2, 500), cv2.FONT_HERSHEY_SIMPLEX, o_scale, (255, 255, 255), o_thick)
        cv2.putText(canvas, other2, (center_x - o2_w // 2, 550), cv2.FONT_HERSHEY_SIMPLEX, o_scale, (255, 255, 255), o_thick)

        # Exit instruction with highlighted key
        exit_prefix = 'Presiona '
        exit_key = 'ESC'
        exit_suffix = ' para salir'
        (ep_w, ep_h), _ = cv2.getTextSize(exit_prefix, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        (ek_w, ek_h), _ = cv2.getTextSize(exit_key, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        (es_w, es_h), _ = cv2.getTextSize(exit_suffix, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        total_exit_w = ep_w + ek_w + es_w
        start_exit_x = center_x - total_exit_w // 2
        y_exit = 700
        cv2.putText(canvas, exit_prefix, (start_exit_x, y_exit), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(canvas, exit_key, (start_exit_x + ep_w, y_exit), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 191, 255), 2)
        cv2.putText(canvas, exit_suffix, (start_exit_x + ep_w + ek_w, y_exit), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        # --- Opciones de modo de juego (1/2/3) ---
        mode1 = '1. Cabeza (cesta en la cabeza)'
        mode2 = '2. Mano derecha (cesta en mano derecha)'
        mode3 = '3. Mano izquierda (cesta en mano izquierda)'
        m_scale = 0.7
        m_thick = 2
        (m1_w, _), _ = cv2.getTextSize(mode1, cv2.FONT_HERSHEY_SIMPLEX, m_scale, m_thick)
        (m2_w, _), _ = cv2.getTextSize(mode2, cv2.FONT_HERSHEY_SIMPLEX, m_scale, m_thick)
        (m3_w, _), _ = cv2.getTextSize(mode3, cv2.FONT_HERSHEY_SIMPLEX, m_scale, m_thick)
        # Draw each centered and highlight selected
        m_start_y = 760
        # mode 1
        color1 = (0, 255, 0) if self.play_mode == 1 else (200, 200, 200)
        cv2.putText(canvas, mode1, (center_x - m1_w // 2, m_start_y), cv2.FONT_HERSHEY_SIMPLEX, m_scale, color1, m_thick)
        # mode 2
        color2 = (0, 255, 0) if self.play_mode == 2 else (200, 200, 200)
        cv2.putText(canvas, mode2, (center_x - m2_w // 2, m_start_y + 34), cv2.FONT_HERSHEY_SIMPLEX, m_scale, color2, m_thick)
        # mode 3
        color3 = (0, 255, 0) if self.play_mode == 3 else (200, 200, 200)
        cv2.putText(canvas, mode3, (center_x - m3_w // 2, m_start_y + 68), cv2.FONT_HERSHEY_SIMPLEX, m_scale, color3, m_thick)
        
        return canvas
    
    def draw_game_over_screen(self):
        """Dibuja la pantalla de game over con fondo negro (sin cámara)"""
        h = self.window_height
        w = self.window_width
        
        # Crear fondo completamente negro con proporción 16:9
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Centrar todo en el canvas completo
        center_x = w // 2

        # Game Over title centered
        title = 'GAME OVER'
        title_scale = 3.0
        title_thick = 5
        (t_w, t_h), _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_SIMPLEX, title_scale, title_thick)
        cv2.putText(canvas, title, (center_x - t_w // 2, 250), cv2.FONT_HERSHEY_SIMPLEX, title_scale, (255, 255, 255), title_thick)

        # Scores centered
        score_text = f'Tu puntuacion: {self.score}'
        best_text = f'Mejor puntuacion: {self.highest_score}'
        (sc_w, sc_h), _ = cv2.getTextSize(score_text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)
        (b_w, b_h), _ = cv2.getTextSize(best_text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)
        cv2.putText(canvas, score_text, (center_x - sc_w // 2, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        cv2.putText(canvas, best_text, (center_x - b_w // 2, 450), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)

        # Instructions with highlighted keys
        instr_scale = 1.0
        instr_thick = 2
        # Retry line: highlight ESPACIO
        prefix = 'Presiona '
        key = 'ESPACIO'
        suffix = ' para reintentar'
        (p_w, _), _ = cv2.getTextSize(prefix, cv2.FONT_HERSHEY_SIMPLEX, instr_scale, instr_thick)
        (k_w, _), _ = cv2.getTextSize(key, cv2.FONT_HERSHEY_SIMPLEX, instr_scale, instr_thick)
        (s_w, _), _ = cv2.getTextSize(suffix, cv2.FONT_HERSHEY_SIMPLEX, instr_scale, instr_thick)
        total_w = p_w + k_w + s_w
        start_x = center_x - total_w // 2
        y_retry = 600
        cv2.putText(canvas, prefix, (start_x, y_retry), cv2.FONT_HERSHEY_SIMPLEX, instr_scale, (255, 255, 255), instr_thick)
        cv2.putText(canvas, key, (start_x + p_w, y_retry), cv2.FONT_HERSHEY_SIMPLEX, instr_scale, (50, 205, 50), instr_thick)
        cv2.putText(canvas, suffix, (start_x + p_w + k_w, y_retry), cv2.FONT_HERSHEY_SIMPLEX, instr_scale, (255, 255, 255), instr_thick)

        # Exit line: highlight ESC
        e_prefix = 'Presiona '
        e_key = 'ESC'
        e_suffix = ' para salir'
        (ep_w, _), _ = cv2.getTextSize(e_prefix, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
        (ek_w, _), _ = cv2.getTextSize(e_key, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
        (es_w, _), _ = cv2.getTextSize(e_suffix, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
        total_e_w = ep_w + ek_w + es_w
        start_ex = center_x - total_e_w // 2
        y_exit = 650
        cv2.putText(canvas, e_prefix, (start_ex, y_exit), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(canvas, e_key, (start_ex + ep_w, y_exit), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 191, 255), 2)
        cv2.putText(canvas, e_suffix, (start_ex + ep_w + ek_w, y_exit), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        return canvas
    
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
