import pygame
import os

pygame.init()

# Dimensiones de la ventana del juego
screen_width = 700
screen_height = 500
screen_bg_color = (172, 209, 175)   # verde claro

game_caption = "Fruit Catcher - Camera Edition"

# Obtener el directorio base del script
base_dir = os.path.dirname(__file__)

# Imágenes de frutas
apple = pygame.image.load(os.path.join(base_dir, "imgs/apple.png"))
banana = pygame.image.load(os.path.join(base_dir, "imgs/banana.png"))
watermelon = pygame.image.load(os.path.join(base_dir, "imgs/watermelon.png"))
strawberry = pygame.image.load(os.path.join(base_dir, "imgs/strawberry.png"))
fruit_list = [apple, banana, strawberry, watermelon]

# Imágenes de bomba, corazón, cesta y botones
bomb_img = pygame.image.load(os.path.join(base_dir, "imgs/bomb.png"))
heart_img = pygame.image.load(os.path.join(base_dir, "imgs/heart.png"))
bucket_img = pygame.image.load(os.path.join(base_dir, "imgs/bucket.png"))
return_to_menu = pygame.image.load(os.path.join(base_dir, "imgs/return_to_menu.png"))

# Imágenes de control de volumen
volume = pygame.image.load(os.path.join(base_dir, "imgs/volume.png"))
mute = pygame.image.load(os.path.join(base_dir, "imgs/mute.png"))

# Sonidos
game_song = os.path.join(base_dir, "sounds/game_song.mp3")
bomb_sound = os.path.join(base_dir, "sounds/bomb.mp3")
score_sound = os.path.join(base_dir, "sounds/coin.mp3")
lost_life_sound = os.path.join(base_dir, "sounds/lost_life.mp3")

rules_text = [
    "1. Mueve tu cabeza para mover la cesta.",
    "2. Atrapa frutas para ganar puntos.",
    "3. Evita las bombas! Pierdes una vida si atrapas una.",
    "4. Perder una fruta también te cuesta una vida.",
    "5. El juego termina cuando pierdes todas las vidas.",
]
