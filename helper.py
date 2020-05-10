import pygame
#pylint: disable=no-member

pygame.init()
pygame.mixer.init()

clock = pygame.time.Clock()
FPS = 60

##########################################    Upload files    ##########################################


screen = pygame.display.set_mode((800, 640))
icon = pygame.image.load('res/icon.png')

pygame.display.set_icon(icon)
pygame.display.set_caption('Tanks 2D')

# background = pygame.image.load('res/')
poster = pygame.image.load('res/poster.jpg')
wall_image = pygame.image.load('res/wall.png')
box_image = pygame.image.load('res/box.tga')

explosion_sound = pygame.mixer.Sound('res/explosion.ogg')
explosion_sound.set_volume(0.2)

shoot_sound = pygame.mixer.Sound('res/bullet.ogg')
shoot_sound.set_volume(0.1)

button_sound = pygame.mixer.Sound('res/button.wav')
button_sound.set_volume(0.2)

# wall_sound = pygame.mixer.Sound('res/walls.ogg')
# wall_sound.set_volume(0.1)

font = pygame.font.SysFont('Courier', 24, bold=True)
big_font = pygame.font.SysFont('Courier', 56, bold=True)
small_font = pygame.font.SysFont('Courier', 16, bold=True)
