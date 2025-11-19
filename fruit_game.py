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
            new_fruit = {
                "x": random.randint(0, max(max_x, 100)),
                "y": 0,
                "img": self.heart_falling_img if is_heart else (self.bomb_img if is_bomb else random.choice(self.fruit_imgs)),
                "is_bomb": is_bomb,
                "is_heart": is_heart
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
                    # Atrapar fruta
                    self.score_sound.play()
                    self.score += 1
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
    
    def update_bucket_position(self, nose_x, nose_y, frame_width, frame_height):
        """Actualiza la posición de la cesta basándose en la posición de la nariz"""
        if nose_x is not None and nose_y is not None:
            # Mapear la posición de la nariz al tamaño del frame
            self.bucket_x = int(nose_x * frame_width) - 40  # Centrar la cesta
            # Subir la cesta por encima de la nariz para colocarla en la cabeza
            # Ajuste proporcional: aproximadamente 25% de la altura del frame
            offset_y = int(frame_height * 0.25)
            self.bucket_y = int(nose_y * frame_height) - offset_y
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
        
        # === PANEL IZQUIERDO: Puntuación ===
        cv2.putText(canvas, 'SCORE', (20, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, f'{self.score}', (40, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3, cv2.LINE_AA)
        
        # Velocidad
        cv2.putText(canvas, 'SPEED', (20, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, f'{self.fruit_speed:.1f}', (40, 250), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 2, cv2.LINE_AA)
        
        # === PANEL DERECHO: Vidas ===
        right_panel_x = self.panel_width + w + 20
        cv2.putText(canvas, 'VIDAS', (right_panel_x, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Dibujar corazones verticalmente en el panel derecho
        for i in range(self.lives):
            y_heart = 120 + i * 60
            if y_heart < total_height - 30:
                heart_rgba = pygame.surfarray.array3d(self.heart_img)
                heart_alpha = pygame.surfarray.array_alpha(self.heart_img)
                
                # Escalar corazones más grandes para el panel
                heart_size = 40
                heart_large = pygame.transform.scale(self.heart_img, (heart_size, heart_size))
                heart_rgba = pygame.surfarray.array3d(heart_large)
                heart_alpha = pygame.surfarray.array_alpha(heart_large)
                
                heart_bgr = cv2.cvtColor(np.transpose(heart_rgba, (1, 0, 2)), cv2.COLOR_RGB2BGR)
                alpha = np.transpose(heart_alpha)
                
                alpha_normalized = alpha.astype(float) / 255.0
                alpha_3ch = np.stack([alpha_normalized] * 3, axis=2)
                
                x_heart_pos = right_panel_x + 40
                roi = canvas[y_heart:y_heart+heart_size, x_heart_pos:x_heart_pos+heart_size]
                blended = (heart_bgr * alpha_3ch + roi * (1 - alpha_3ch)).astype(np.uint8)
                canvas[y_heart:y_heart+heart_size, x_heart_pos:x_heart_pos+heart_size] = blended
        
        return canvas
    
    def draw_start_screen(self):
        """Dibuja la pantalla de inicio con fondo negro (sin cámara)"""
        h = self.window_height
        w = self.window_width
        
        # Crear fondo completamente negro con proporción 16:9
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Centrar todo en el canvas completo
        center_x = w // 2
        
        # Título
        cv2.putText(canvas, 'FRUIT CATCHER', (center_x - 200, 250), 
                   cv2.FONT_HERSHEY_SIMPLEX, 3.0, (255, 255, 255), 5)
        cv2.putText(canvas, 'Camera Edition', (center_x - 150, 320), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        
        # Instrucciones
        cv2.putText(canvas, 'Presiona ESPACIO para comenzar', (center_x - 300, 450), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(canvas, 'Mueve tu cabeza para mover la cesta', (center_x - 300, 500), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        cv2.putText(canvas, 'Atrapa frutas y evita bombas!', (center_x - 250, 550), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        
        cv2.putText(canvas, 'Presiona ESC para salir', (center_x - 150, 700), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        return canvas
    
    def draw_game_over_screen(self):
        """Dibuja la pantalla de game over con fondo negro (sin cámara)"""
        h = self.window_height
        w = self.window_width
        
        # Crear fondo completamente negro con proporción 16:9
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Centrar todo en el canvas completo
        center_x = w // 2
        
        # Game Over
        cv2.putText(canvas, 'GAME OVER', (center_x - 200, 250), 
                   cv2.FONT_HERSHEY_SIMPLEX, 3.0, (255, 255, 255), 5)
        
        # Puntuaciones
        cv2.putText(canvas, f'Tu puntuacion: {self.score}', (center_x - 200, 400), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        cv2.putText(canvas, f'Mejor puntuacion: {self.highest_score}', (center_x - 250, 450), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        
        # Instrucciones
        cv2.putText(canvas, 'Presiona ESPACIO para reintentar', (center_x - 300, 600), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(canvas, 'Presiona ESC para salir', (center_x - 200, 650), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
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
                    
                    # Obtener posición de la nariz si hay detección
                    nose_x = None
                    nose_y = None
                    if result.pose_landmarks:
                        for person_landmarks in result.pose_landmarks:
                            # Landmark 0 es la nariz
                            nose = person_landmarks[0]
                            nose_x = nose.x
                            nose_y = nose.y
                    
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
                    
                    # Ajustar coordenadas de la nariz al frame recortado
                    if nose_x is not None and nose_y is not None:
                        # Convertir coordenadas normalizadas (0-1) a píxeles del frame original
                        nose_x_pixel = nose_x * w_original
                        nose_y_pixel = nose_y * h_original
                        
                        # Ajustar al frame recortado
                        nose_x_adjusted = (nose_x_pixel - start_x) / frame.shape[1]
                        nose_y_adjusted = (nose_y_pixel - start_y) / frame.shape[0]
                        
                        # Asegurar que las coordenadas estén dentro del rango válido
                        nose_x_adjusted = max(0.0, min(1.0, nose_x_adjusted))
                        nose_y_adjusted = max(0.0, min(1.0, nose_y_adjusted))
                    else:
                        nose_x_adjusted = None
                        nose_y_adjusted = None
                    
                    # Escalar el frame para que ocupe toda la altura de la ventana
                    h_before_scale = frame.shape[0]
                    w_before_scale = frame.shape[1]
                    scale_factor = 1.0
                    
                    if h_before_scale != self.window_height:
                        scale_factor = self.window_height / h_before_scale
                        new_width = int(w_before_scale * scale_factor)
                        frame = cv2.resize(frame, (new_width, self.window_height), interpolation=cv2.INTER_LINEAR)
                    
                    # Actualizar posición de la cesta con dimensiones escaladas
                    if nose_x_adjusted is not None and nose_y_adjusted is not None:
                        self.update_bucket_position(nose_x_adjusted, nose_y_adjusted, frame.shape[1], frame.shape[0])
                    
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
