import pygame
from enum import Enum
import random
from helper import screen, wall_image, box_image, small_font, shoot_sound
#pylint: disable=no-member

class Direction(Enum):
    UP = 'UP'
    DOWN = 'DOWN'
    LEFT = 'LEFT'
    RIGHT = 'RIGHT'


##########################################    Bullet    ##########################################


class Bullet:

    def __init__(self, tank):
        shoot_sound.play(maxtime=1600)
        self.tank = tank
        self.color = (0, 0, 0)
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

        self.size = [self.width, self.height]

    def draw(self):
        pygame.draw.ellipse(screen, self.color, (self.x, self.y, self.width, self.height))

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

    def __init__(self, x, y, speed, color, width, name, direction=Direction.UP, d_right=pygame.K_RIGHT, d_left=pygame.K_LEFT, d_up=pygame.K_UP, d_down=pygame.K_DOWN, fire=pygame.K_SPACE):
        self.x = x
        self.y = y
        self.speed = speed
        self.countdown = 0
        self.power_up = False
        self.color = color
        self.width = width
        self.size = [self.width, self.width]
        self.name = name
        self.txt = small_font.render(str(name), True, (0, 0, 0))
        self.lifes = max_lifes
        self.score = 0
        self.direction = direction
        self.is_static = True
        self.fire_key = fire

        self.KEY = {d_right: Direction.RIGHT, d_left: Direction.LEFT,
                    d_up: Direction.UP, d_down: Direction.DOWN}

    def draw(self):
        tank_c = (self.x + self.width // 2, self.y + self.width // 2)
        # dynamic = tuple(int(i * self.lifes / max_lifes) for i in self.color)
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.width))
        pygame.draw.circle(screen, self.color, tank_c, self.width // 2)
        pygame.draw.circle(screen, (0, 0, 0), tank_c, self.width // 2 - 1, 1)

        if self.direction == Direction.RIGHT:
            pygame.draw.line(screen, self.color, tank_c, (tank_c[0] + self.width, tank_c[1]), 4)

        if self.direction == Direction.LEFT:
            pygame.draw.line(screen, self.color, tank_c, (tank_c[0] - self.width, tank_c[1]), 4)

        if self.direction == Direction.UP:
            pygame.draw.line(screen, self.color, tank_c, (tank_c[0], tank_c[1] - self.width), 4)

        if self.direction == Direction.DOWN:
            pygame.draw.line(screen, self.color, tank_c, (tank_c[0], tank_c[1] + self.width), 4)

        screen.blit(self.txt, (tank_c[0] - self.txt.get_size()[0] // 2, self.y + self.width + 2))

    def changeDirection(self, direction):
        self.direction = direction

    def move(self, sec, box, tanks):
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

            # Power box
            if future_pos.colliderect(pygame.Rect(box.coord, box.size)) and box.is_active:
                box.is_active = False
                self.speed *= 2
                self.countdown = 5
                self.power_up = True

        self.draw()


##########################################    Walls    ##########################################


class Wall:

    def __init__(self, coord):
        self.image = wall_image
        self.size = self.image.get_size()
        self.coord = coord

    def draw(self):
        screen.blit(self.image, self.coord)


##########################################    Power box    ##########################################


class Box:
    def __init__(self, interval, free_spaces):
        self.interval = interval
        self.spaces = free_spaces
        self.images = []
        self.size = [32, 32]
        for i in range(box_image.get_size()[1] // self.size[1]):
            for j in range(box_image.get_size()[0] // self.size[0]):
                self.images.append(box_image.subsurface(j*self.size[0], i*self.size[1], self.size[0], self.size[1]))
        self.cur_image = 0
        self.is_active = False
        self.wait = 0
        self.newBox()

    def newBox(self):
        self.reload = 7 + random.random() * 5  # 7 - 12 seconds
        self.coord = random.choice(self.spaces)

    def draw(self):
        screen.blit(self.images[self.cur_image], self.coord)


##########################################    Buttons    ##########################################


class Button:

    def __init__(self, text, button_x, button_y, font, txt_col, colour, act_colour, func, size='auto',
                 color_per=(74, 72, 70)):
        global screen
        self.is_active = False
        self.text = text
        self.button_x = button_x
        self.button_y = button_y
        self.font = font
        self.txt = font.render(str(text), True, txt_col)
        self.txt_col = txt_col
        self.colour = colour
        self.act_colour = act_colour
        self.color_per = color_per
        self.run = func
        w, h = self.txt.get_size()
        self.button_w = size[0] if size != 'auto' else w + 8
        self.button_h = size[1] if size != 'auto' else h + 8
        self.txt_x = button_x + self.button_w // 2 - w // 2
        self.txt_y = button_y + self.button_h // 2 - h // 2

    def draw(self):
        # self.txt = self.font.render(str(self.text), True, self.txt_col)
        colour = self.colour if not self.is_active else self.act_colour
        pygame.draw.rect(screen, colour, (self.button_x, self.button_y, self.button_w, self.button_h))
        pygame.draw.rect(screen, self.color_per, (self.button_x, self.button_y, self.button_w, self.button_h), 2)
        screen.blit(self.txt, (self.txt_x, self.txt_y))
