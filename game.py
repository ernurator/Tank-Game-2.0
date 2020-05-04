import pygame
from enum import Enum
import random
#pylint: disable=no-member

pygame.init()
pygame.mixer.init()


##########################################    Upload files    ##########################################


screen = pygame.display.set_mode((800, 640))
icon = pygame.image.load('res/war.png')
pygame.display.set_icon(icon)
pygame.display.set_caption('Tanks 2D')

background = pygame.image.load('res/ground.jpg')
wall_image = pygame.image.load('res/wall.png')
box_image = pygame.image.load('res/box.png')

sound_col = pygame.mixer.Sound('res/collision.wav')
sound_col.set_volume(0.2)

sound_shoot = pygame.mixer.Sound('res/shoot.wav')
sound_shoot.set_volume(0.2)

font = pygame.font.SysFont('Courier', 24, bold=True)
big_font = pygame.font.SysFont('Courier', 36, bold=True)
small_font = pygame.font.SysFont('Courier', 16, bold=True)

class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4


##########################################    Bullet    ##########################################


class Bullet:

    def __init__(self, tank):
        sound_shoot.play()
        self.tank = tank
        # self.color = tank.color
        self.width = 4
        self.height = 8
        self.direction = tank.direction
        self.speed = int(tank.speed * 3.75)
        self.lifetime = 0
        self.destroytime = 3  # seconds
        if tank.direction == Direction.RIGHT:
            self.x = tank.x + 3*tank.width//2
            self.y = tank.y + tank.width//2
            self.height, self.width = self.width, self.height
        
        if tank.direction == Direction.LEFT:
            self.x = tank.x - tank.width//2
            self.y = tank.y + tank.width//2
            self.height, self.width = self.width, self.height
        
        if tank.direction == Direction.UP:
            self.x = tank.x + tank.width//2
            self.y = tank.y - tank.width//2

        if tank.direction == Direction.DOWN:
            self.x = tank.x + tank.width//2
            self.y = tank.y + 3*tank.width//2
        
    def draw(self):
        # pygame.draw.ellipse(screen, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.ellipse(screen, (0, 0, 0), (self.x, self.y, self.width, self.height))

        
    def move(self, sec):
        self.lifetime += sec

        if self.direction == Direction.RIGHT:
            self.x += int(self.speed * sec)
        
        if self.direction == Direction.LEFT:
            self.x -= int(self.speed * sec)
        
        if self.direction == Direction.UP:
            self.y -= int(self.speed * sec)

        if self.direction == Direction.DOWN:
            self.y += int(self.speed * sec)
        self.draw()


##########################################    Tanks    ##########################################


max_lifes = 10


class Tank:

    def __init__(self, x, y, speed, color, d_right=pygame.K_RIGHT, d_left=pygame.K_LEFT, d_up=pygame.K_UP, d_down=pygame.K_DOWN, fire=pygame.K_SPACE):
        self.x = x
        self.y = y
        self.speed = speed
        self.countdown = 0
        self.power_up = False
        self.color = color
        self.width = 32
        self.lifes = max_lifes
        self.score = 0
        self.direction = Direction.RIGHT
        self.is_static = True
        self.fire_key = fire
        
        self.KEY = {d_right: Direction.RIGHT, d_left: Direction.LEFT, d_up: Direction.UP, d_down: Direction.DOWN}

    def draw(self):
        tank_c = (self.x + self.width // 2, self.y + self.width // 2)
        # dynamic = tuple(int(i * self.lifes / max_lifes) for i in self.color)
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.width))
        pygame.draw.circle(screen, self.color, tank_c, self.width // 2)
        pygame.draw.circle(screen, (0, 0, 0), tank_c, self.width // 2 - 1, 1)

        if self.direction == Direction.RIGHT:
            pygame.draw.line(screen, self.color, tank_c, (self.x + 3*self.width//2, self.y + self.width//2), 4)
        
        if self.direction == Direction.LEFT:
            pygame.draw.line(screen, self.color, tank_c, (self.x - self.width//2, self.y + self.width//2), 4)
        
        if self.direction == Direction.UP:
            pygame.draw.line(screen, self.color, tank_c, (self.x + self.width//2, self.y - self.width//2), 4)

        if self.direction == Direction.DOWN:
            pygame.draw.line(screen, self.color, tank_c, (self.x + self.width//2, self.y + 3*self.width//2), 4)


    def changeDirection(self, direction):
        self.direction = direction

    def move(self, sec, box):
        global tanks, walls
        if self.countdown > 0:
            self.countdown -= sec
        if self.power_up and self.countdown <= 0:
            self.power_up = False
            self.speed = self.speed // 2

        if not self.is_static:
            dx = 0
            dy = 0
            change = int(self.speed * sec)
            if self.direction == Direction.RIGHT:
                dx = change
                if self.x + dx > screen.get_size()[0]:
                    dx = -self.x - self.width
            
            if self.direction == Direction.LEFT:
                dx = -change
                if self.x + dx < -self.width:
                    dx = -self.x + screen.get_size()[0]
            
            if self.direction == Direction.UP:
                dy = -change
                if self.y + dy < -self.width:
                    dy = -self.y + screen.get_size()[1]

            if self.direction == Direction.DOWN:
                dy = change
                if self.y + dy > screen.get_size()[1]:
                    dy = -self.y - self.width

            # Other tanks
            future_pos = pygame.Rect(self.x + dx, self.y + dy, self.width, self.width)
            if not any([future_pos.colliderect(pygame.Rect(tank.x, tank.y, tank.width, tank.width)) 
                        for tank in tanks if self != tank]):
                    self.x, self.y = self.x + dx, self.y + dy

            # Walls
            for i in range(len(walls)):
                if future_pos.colliderect(pygame.Rect(walls[i].coord, walls[i].image.get_size())):
                    del walls[i]
                    self.lifes -= 1
                    break

            # Power box
            if future_pos.colliderect(pygame.Rect(box.coord, box.image.get_size())) and box.is_active:
                box.is_active = False
                self.speed *= 2
                self.countdown = 5
                self.power_up = True

        self.draw()


########################################## Walls ##########################################


class Wall:
    
    def __init__(self, coord):
        self.image = wall_image
        self.coord = coord
    
    def draw(self):
        screen.blit(self.image, self.coord)


########################################## Power box ##########################################


class Box:
    def __init__(self):
        self.image = box_image
        self.is_active = False
        self.wait = 0
        self.newBox()

    def newBox(self):
        global free_spaces
        self.reload = 7 + random.random() * 5 # 7 - 12 seconds
        self.coord = random.choice(free_spaces)
    
    def draw(self):
        screen.blit(self.image, self.coord)


########################################## Buttons ##########################################


class Button:

    def __init__(self, text, button_x, button_y, font, txt_col, colour, func, size='auto',
                 color_per=(74, 72, 70)):
        global screen
        self.text = text
        self.button_x = button_x
        self.button_y = button_y
        self.font = font
        self.txt = font.render(str(text), True, txt_col)
        self.txt_col = txt_col
        self.colour = colour
        self.color_per = color_per
        self.run = func
        w, h = self.txt.get_size()
        self.button_w = size[0] if size != 'auto' else w + 8
        self.button_h = size[1] if size != 'auto' else h + 8
        self.txt_x = button_x + self.button_w // 2 - w // 2
        self.txt_y = button_y + self.button_h // 2 - h // 2

    def draw(self):
        # self.txt = self.font.render(str(self.text), True, self.txt_col)
        pygame.draw.rect(screen, self.colour, (self.button_x, self.button_y, self.button_w, self.button_h))
        pygame.draw.rect(screen, self.color_per, (self.button_x, self.button_y, self.button_w, self.button_h), 2)
        screen.blit(self.txt, (self.txt_x, self.txt_y))


##########################################    Collisions    ##########################################


def checkCollisions(bullet):
    global tanks, walls
    pos = pygame.Rect(bullet.x, bullet.y, bullet.width, bullet.height)
    for i in range(len(walls)):
        if pos.colliderect(pygame.Rect(walls[i].coord, walls[i].image.get_size())):
            del walls[i]
            return True
            
    for i in range(len(tanks)):
        dist_x = bullet.x - tanks[i].x
        dist_y = bullet.y - tanks[i].y
        if -bullet.width <= dist_x <= tanks[i].width and -bullet.height <= dist_y <= tanks[i].width and bullet.tank != tanks[i]:
            sound_col.play()
            bullet.tank.score += 1
            tanks[i].lifes -= 1
            if tanks[i].lifes <= 0: del tanks[i]
            return True
    return False


##########################################    Init    ##########################################


menuloop = True
mainloop = True
gamemode = ''
repeat = True
game_over = False
tanks = []
bullets = []
walls = []
free_spaces = []
winner = ''

clock = pygame.time.Clock()
FPS = 60


##########################################    Menu loop    ##########################################


def start(txt):
    global menuloop
    menuloop = False
    if txt == 'Single player': return 's'
    if txt == 'Multiplayer': return 'm'
    if txt == 'Autoplay': return 'a'


def menu():
    global clock, menuloop, gamemode
    hello_text = 'Tanks 2D'
    hello_text = big_font.render(hello_text, True, (50, 50, 50))
    buttons = []
    single = Button('Single player', 100, 500, font, (0, 0, 0), (10, 200, 10), start)
    buttons.append(single)
    multi = Button('Multiplayer', 330, 500, font, (0, 0, 0), (10, 200, 10), start)
    buttons.append(multi)
    auto = Button('Autoplay', 550, 500, font, (0, 0, 0), (10, 200, 10), start)
    buttons.append(auto)
    
    menuloop = True
    while menuloop:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menuloop = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    menuloop = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for button in buttons:
                    if button.button_x <= pos[0] <= button.button_x + button.button_w and (
                            button.button_y <= pos[1] <= button.button_y + button.button_h):
                        gamemode = button.run(button.text)
                
        screen.fill((255 ,255, 255))
        screen.blit(hello_text, (screen.get_size()[0] // 2 - hello_text.get_size()[0] // 2, 200))
        for button in buttons:
            button.draw()

        pygame.display.flip()


##########################################    Restart loop    ##########################################


def again(winner=''):
    global repeat
    screen.fill((255, 255, 255))
    if winner != '':
        text = font.render('Congrats! Winner: ', True, (10, 10, 10))
        x = screen.get_size()[0] // 2 - text.get_size()[0] // 2 - winner.width // 2
        y = screen.get_size()[1] // 2 - text.get_size()[1] // 2 - winner.width // 2
        winner.x = text.get_size()[0] + x
        winner.y = y
        winner.draw()
    else:
        text = font.render("It's a draw!", True, (10, 10, 10))
        x = screen.get_size()[0] // 2 - text.get_size()[0] // 2
        y = screen.get_size()[1] // 2 - text.get_size()[1] // 2

    text1 = font.render('Press R to play again', True, (200, 200, 200))
    x1 = screen.get_size()[0] // 2 - text1.get_size()[0] // 2
    y1 = y + text.get_size()[1] + 10
    screen.blit(text, (x, y))
    screen.blit(text1, (x1, y1))
    pygame.display.flip()
    
    rep_loop = True
    while rep_loop:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                rep_loop = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    rep_loop = False
                if event.key == pygame.K_r:
                    rep_loop = False
                    repeat = True


##########################################    Main loop    ##########################################


def single():
    global mainloop, clock, bullets, tanks, walls, winner, game_over
    spawnpoints = []
    with open('res/maps/map1.txt') as map:
        lines = map.readlines()
        i = 0
        for line in lines:
            j = 0
            for symb in line:
                if symb == '#':
                    walls.append(Wall([j*32, i*32]))
                elif symb == '@':
                    spawnpoints.append([j*32, i*32])
                elif symb == '_':
                    free_spaces.append([j*32, i*32])
                j += 1
            i += 1


    tank1 = Tank(spawnpoints[0][0], spawnpoints[0][1], 800//6, (3, 102, 6), fire=pygame.K_RETURN)
    tank2 = Tank(spawnpoints[1][0], spawnpoints[1][1], 800//6, (135, 101, 26), pygame.K_d, pygame.K_a, pygame.K_w, pygame.K_s)
    # tank3 = Tank(100, 100, 800//6, (0, 0, 0xff), pygame.K_h, pygame.K_f, pygame.K_t, pygame.K_g, pygame.K_2)
    # tank4 = Tank(100, 200, 800//6, (0xff, 255, 0), pygame.K_l, pygame.K_j, pygame.K_i, pygame.K_k, pygame.K_3)

    tanks += [tank1, tank2]
    box = Box()

    mainloop = True
    while mainloop:
        millis = clock.tick(FPS)
        seconds = millis / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                mainloop = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    mainloop = False
                for tank in tanks:
                    if event.key == tank.fire_key:
                        bullets.append(Bullet(tank))

        pressed = pygame.key.get_pressed()
        for tank in tanks:
            # print(tank.direction)
            stay = True
            for key in tank.KEY.keys():
                if pressed[key]:
                    tank.changeDirection(tank.KEY[key])
                    tank.is_static = False
                    stay = False
            if stay:
                tank.is_static = True
                
        screen.fill((255 ,255, 255))
        # screen.blit(background, (0, 0))
        for wall in walls:
            wall.draw()

        if box.is_active: box.draw()
        elif box.wait < box.reload: box.wait += seconds
        else:
            box.newBox()
            box.wait = 0
            box.is_active = True

        for i in range(len(tanks)):
            tanks[i].move(seconds, box)
            if tanks[i].lifes <= 0:
                del tanks[i]
                break

        for i in range(len(bullets)):
            bullets[i].move(seconds)
            if checkCollisions(bullets[i]) or bullets[i].lifetime > bullets[i].destroytime:
                del bullets[i]
                break

        for i in range(len(tanks)):
            txt = small_font.render(f'Tank {i + 1}: {tanks[i].lifes} lifes, {tanks[i].score} points', True, (0, 0, 0))
            screen.blit(txt, (5, i*txt.get_size()[1] + 5))

        pygame.display.flip()

        if len(tanks) == 0:
            winner = ''
            game_over = True
            mainloop = False
        if len(tanks) == 1:
            winner = tanks[0]
            game_over = True
            mainloop = False


##########################################    Game launch    ##########################################


while repeat:
    repeat = False
    gamemode = ''
    game_over = False
    tanks = []
    bullets = []
    walls = []
    free_spaces = []
    winner = ''
    menu()
    if gamemode == 's': single()
    # ...
    if game_over: again(winner)

pygame.quit()
