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
        self.return_to_menu_img = pygame.transform.scale(return_to_menu, (30, 30))
        self.volume_img = pygame.transform.scale(volume, (30, 30))
        self.mute_img = pygame.transform.scale(mute, (30, 30))
        
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
        self.fruit_interval = 1000  # ms
        self.fruit_speed = 3
        self.max_fruit_speed = 15  # Velocidad máxima
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
        """Crea nuevas frutas o bombas que caen"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_fruit_time >= self.fruit_interval:
            is_bomb = random.random() < 0.2  
            max_x = frame_width - 60
            new_fruit = {
                "x": random.randint(0, max(max_x, 100)),
                "y": 0,
                "img": self.bomb_img if is_bomb else random.choice(self.fruit_imgs),
                "is_bomb": is_bomb
            }
            self.created_fruits.append(new_fruit)
            self.last_fruit_time = current_time
            
    def update_fruits(self, frame_height):
        """Actualiza la posición de las frutas y verifica colisiones"""
        for fruit in self.created_fruits[:]:
            fruit["y"] += self.fruit_speed
            
            # Verificar colisión
            if self.check_collision(fruit):
                if fruit["is_bomb"]:
                    self.bomb_sound.play()
                    self.lives -= 1
                    self.lost_life_sound.play()
                else:
                    self.score_sound.play()
                    self.score += 1
                    # Incrementar velocidad progresivamente hasta el máximo
                    if self.fruit_speed < self.max_fruit_speed:
                        self.fruit_speed += self.speed_increment
                self.created_fruits.remove(fruit)
            # Verificar si la fruta salió de la pantalla
            elif fruit["y"] > frame_height:
                self.created_fruits.remove(fruit)
                if not fruit["is_bomb"]:
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
            # Subir la cesta 150 píxeles por encima de la nariz
            self.bucket_y = int(nose_y * frame_height) - 200
            # Limitar dentro de los bordes
            self.bucket_x = max(0, min(self.bucket_x, frame_width - 80))
            self.bucket_y = max(0, min(self.bucket_y, frame_height - 80))
    
    def draw_game_overlay(self, frame):
        """Dibuja los elementos del juego sobre el frame de la cámara"""
        h, w = frame.shape[:2]
        
        # Dibujar frutas usando el canal alfa
        for fruit in self.created_fruits:
            fruit_surface = fruit["img"]
            
            y_pos = int(fruit["y"])
            x_pos = int(fruit["x"])
            
            if 0 <= y_pos < h - 60 and 0 <= x_pos < w - 60:
                # Obtener array RGBA
                fruit_rgba = pygame.surfarray.array3d(fruit_surface)
                fruit_alpha = pygame.surfarray.array_alpha(fruit_surface)
                
                # Transponer y convertir RGB a BGR
                fruit_bgr = cv2.cvtColor(np.transpose(fruit_rgba, (1, 0, 2)), cv2.COLOR_RGB2BGR)
                alpha = np.transpose(fruit_alpha)
                
                # Normalizar alpha a rango 0-1
                alpha_normalized = alpha.astype(float) / 255.0
                alpha_3ch = np.stack([alpha_normalized] * 3, axis=2)
                
                # Extraer región de interés del frame
                roi = frame[y_pos:y_pos+60, x_pos:x_pos+60]
                
                # Mezclar usando alpha blending
                blended = (fruit_bgr * alpha_3ch + roi * (1 - alpha_3ch)).astype(np.uint8)
                frame[y_pos:y_pos+60, x_pos:x_pos+60] = blended
    
        # Dibujar cesta usando el canal alfa
        y_pos = int(self.bucket_y)
        x_pos = int(self.bucket_x)
        
        if 0 <= y_pos < h - 80 and 0 <= x_pos < w - 80:
            bucket_rgba = pygame.surfarray.array3d(self.bucket_img)
            bucket_alpha = pygame.surfarray.array_alpha(self.bucket_img)
            
            bucket_bgr = cv2.cvtColor(np.transpose(bucket_rgba, (1, 0, 2)), cv2.COLOR_RGB2BGR)
            alpha = np.transpose(bucket_alpha)
            
            alpha_normalized = alpha.astype(float) / 255.0
            alpha_3ch = np.stack([alpha_normalized] * 3, axis=2)
            
            roi = frame[y_pos:y_pos+80, x_pos:x_pos+80]
            blended = (bucket_bgr * alpha_3ch + roi * (1 - alpha_3ch)).astype(np.uint8)
            frame[y_pos:y_pos+80, x_pos:x_pos+80] = blended
        
        result = frame
        
        # Dibujar puntuación y vidas con fondo semi-transparente para mejor visibilidad
        cv2.putText(result, f'Score: {self.score}', (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3, cv2.LINE_AA)
        cv2.putText(result, f'Speed: {self.fruit_speed:.1f}', (10, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2, cv2.LINE_AA)
        
        # Dibujar corazones para vidas usando el canal alfa
        for i in range(self.lives):
            x_heart = 10 + i * 45
            if x_heart < result.shape[1] - 30 and 140 < result.shape[0] - 30:
                heart_rgba = pygame.surfarray.array3d(self.heart_img)
                heart_alpha = pygame.surfarray.array_alpha(self.heart_img)
                
                heart_bgr = cv2.cvtColor(np.transpose(heart_rgba, (1, 0, 2)), cv2.COLOR_RGB2BGR)
                alpha = np.transpose(heart_alpha)
                
                alpha_normalized = alpha.astype(float) / 255.0
                alpha_3ch = np.stack([alpha_normalized] * 3, axis=2)
                
                roi = result[140:170, x_heart:x_heart+30]
                blended = (heart_bgr * alpha_3ch + roi * (1 - alpha_3ch)).astype(np.uint8)
                result[140:170, x_heart:x_heart+30] = blended
        
        return result
    
    def draw_start_screen(self, frame):
        """Dibuja la pantalla de inicio sobre el frame"""
        overlay = frame.copy()
        
        # Fondo semi-transparente oscuro
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), 
                     (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)
        
        # Título - centrado para 1920x1080
        h, w = frame.shape[:2]
        cv2.putText(frame, 'FRUIT CATCHER', (int(w/2 - 300), 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 255, 255), 4)
        cv2.putText(frame, 'Camera Edition', (int(w/2 - 250), 280), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        
        # Instrucciones
        cv2.putText(frame, 'Presiona ESPACIO para comenzar', (int(w/2 - 400), 500), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        cv2.putText(frame, 'Mueve tu cabeza para mover la cesta', (int(w/2 - 420), 580), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(frame, 'Atrapa frutas y evita bombas!', (int(w/2 - 340), 650), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        cv2.putText(frame, 'Presiona ESC para salir', (int(w/2 - 250), 900), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        return frame
    
    def draw_game_over_screen(self, frame):
        """Dibuja la pantalla de game over sobre el frame"""
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # Fondo semi-transparente oscuro
        cv2.rectangle(overlay, (0, 0), (w, h), 
                     (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)
        
        # Game Over
        cv2.putText(frame, 'GAME OVER', (int(w/2 - 280), 250), 
                   cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 4)
        
        # Puntuaciones
        cv2.putText(frame, f'Tu puntuacion: {self.score}', (int(w/2 - 250), 450), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        cv2.putText(frame, f'Mejor puntuacion: {self.highest_score}', (int(w/2 - 320), 550), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        
        # Instrucciones
        cv2.putText(frame, 'Presiona ESPACIO para reintentar', (int(w/2 - 400), 750), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        cv2.putText(frame, 'Presiona ESC para salir', (int(w/2 - 280), 850), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        
        return frame
    
    def run(self):
        """Loop principal del juego"""
        with self.PoseLandmarker.create_from_options(self.options) as landmarker:
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                print("Error: No se pudo abrir la cámara")
                return
            
            # Configurar resolución fija de la cámara - 16:9
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps == 0:
                fps = 30
            
            frame_ms = int(1000 / fps)
            timestamp = 0
            
            # Reproducir música
            if not self.is_mute:
                pygame.mixer.music.play(-1)
            
            while cap.isOpened():
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
                
                # Lógica del juego
                if not self.game_started:
                    frame = self.draw_start_screen(frame)
                elif self.game_over:
                    frame = self.draw_game_over_screen(frame)
                else:
                    # Actualizar posición de la cesta (en la cabeza)
                    if nose_x is not None and nose_y is not None:
                        self.update_bucket_position(nose_x, nose_y, frame.shape[1], frame.shape[0])
                    
                    # Crear y actualizar frutas
                    self.create_new_fruit(frame.shape[1])
                    self.update_fruits(frame.shape[0])
                    
                    # Dibujar overlay del juego
                    frame = self.draw_game_overlay(frame)
                
                # Mostrar frame en ventana que puede ir a pantalla completa
                cv2.namedWindow("Fruit Catcher - Camera Edition", cv2.WINDOW_NORMAL)
                cv2.imshow("Fruit Catcher - Camera Edition", frame)
                
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
                        self.game_started = True
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
