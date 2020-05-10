import pygame
from enum import Enum
import random
import pika
import uuid
import json
from threading import Thread
from collections import deque
#pylint: disable=no-member

pygame.init()
pygame.mixer.init()


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

    def __init__(self, x, y, speed, color, width, name, direction=Direction.RIGHT, health=max_lifes, score=0, d_right=pygame.K_RIGHT, d_left=pygame.K_LEFT, d_up=pygame.K_UP, d_down=pygame.K_DOWN, fire=pygame.K_SPACE):
        self.x = x
        self.y = y
        self.speed = speed
        self.countdown = 0
        self.power_up = False
        self.color = color
        self.width = width
        self.name = name
        self.txt = small_font.render(str(name), True, (0, 0, 0))
        self.lifes = health
        self.score = score
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

    def set_values(self, x, y, direction, health, score):
        self.x = x
        self.y = y
        self.lifes = health
        self.score = score
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


##########################################    Collisions    ##########################################


def checkCollisions(bullet):
    global tanks, walls
    pos = pygame.Rect(bullet.x, bullet.y, bullet.width, bullet.height)
    for i in range(len(walls)):
        if pos.colliderect(pygame.Rect(walls[i].coord, walls[i].image.get_size())):
            # wall_sound.play(fade_ms=1700)
            del walls[i]
            return True

    for i in range(len(tanks)):
        dist_x = bullet.x - tanks[i].x
        dist_y = bullet.y - tanks[i].y
        if -bullet.width <= dist_x <= tanks[i].width and -bullet.height <= dist_y <= tanks[i].width and bullet.tank != tanks[i]:
            explosion_sound.play()
            bullet.tank.score += 1
            tanks[i].lifes -= 1
            if tanks[i].lifes <= 0:
                del tanks[i]
            return True
    return False


##########################################    RPC    ##########################################


class RpcClient():

    def __init__(self):
        self.credentials = pika.PlainCredentials('dar-tanks', password='5orPLExUYnyVYZg48caMpX')
        self.parameters = pika.ConnectionParameters('34.254.177.17', 5672, 'dar-tanks', self.credentials)
        self.connection = pika.BlockingConnection(self.parameters)

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True, auto_delete=True)
        self.callback_queue = result.method.queue
        self.channel.exchange_declare('X:routing.topic', 'topic', durable=True)

        self.channel.queue_bind(exchange='X:routing.topic', queue=self.callback_queue)
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, key, msg=''):
        self.response = None
        self.corr_id = str(uuid.uuid4())

        self.channel.basic_publish(
            exchange='X:routing.topic',
            routing_key=key,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id),
            body=msg
        )
        while self.response is None:
            self.connection.process_data_events()
        return json.loads(self.response)


##########################################    Room Events    ##########################################


class StateEvents(Thread):
    def __init__(self, room):
        Thread.__init__(self)
        self.room = room

    def run(self):
        credentials = pika.PlainCredentials('dar-tanks', password='5orPLExUYnyVYZg48caMpX')
        parameters = pika.ConnectionParameters('34.254.177.17', 5672, 'dar-tanks', credentials)
        connection = pika.BlockingConnection(parameters)

        channel = connection.channel()

        result = channel.queue_declare(queue='', exclusive=True, auto_delete=True)
        events_queue = result.method.queue
        channel.exchange_declare('X:routing.topic', 'topic', durable=True)

        channel.queue_bind(exchange='X:routing.topic', queue=events_queue, routing_key=f'event.state.{self.room}')

        def on_response(ch, method, props, body):
            global buffer, room_is_ready, stop_thread
            if stop_thread:
                raise Exception('Consumer thread is killed')
            buffer.append(json.loads(body))
            room_is_ready = True

        channel.basic_consume(
            queue=events_queue,
            on_message_callback=on_response,
            auto_ack=True)
        try:
            channel.start_consuming()
        except Exception as e:
            print(e)


##########################################    Init    ##########################################


gamemode = ''
repeat = True
game_over = False
tanks = []
bullets = []
walls = []
winner = ''
losers = []
kicked = []
buffer = deque()
stop_thread = False
room_is_ready = False

clock = pygame.time.Clock()
FPS = 60


##########################################    Menu loop    ##########################################


def start(txt):
    button_sound.play()
    if txt == 'Single player': return 's'
    if txt == 'Multiplayer': return 'm'
    if txt == 'Autoplay': return 'a'


def menu():
    global clock, gamemode
    hello_text = 'Tanks 2D'
    hello_text = big_font.render(hello_text, True, (50, 50, 50))
    buttons = []
    single = Button('Single player', 100, 500, font, (0, 0, 0), (10, 200, 10), (6, 128, 6), start)
    buttons.append(single)
    multi = Button('Multiplayer', 330, 500, font, (0, 0, 0), (10, 200, 10), (6, 128, 6), start)
    buttons.append(multi)
    auto = Button('Autoplay', 550, 500, font, (0, 0, 0), (10, 200, 10), (6, 128, 6), start)
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
            pos = pygame.mouse.get_pos()
            for button in buttons:
                dist_x = pos[0] - button.button_x
                dist_y = pos[1] - button.button_y
                if 0 <= dist_x <= button.button_w and 0 <= dist_y <= button.button_h:
                    button.is_active = True
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        gamemode = button.run(button.text)
                        menuloop = False
                else:
                    button.is_active = False

        screen.blit(poster, (-80, -80))
        screen.blit(hello_text, (screen.get_size()[0] // 2 - hello_text.get_size()[0] // 2, 80))
        for button in buttons:
            button.draw()

        pygame.display.flip()


##########################################    Restart loop    ##########################################


def again():
    global repeat, winner
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
    y1 = y + text.get_size()[1] + 25
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
    free_spaces = []
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
    tank1 = Tank(spawnpoints[0][0], spawnpoints[0][1], 800//6, (3, 102, 6), 32, 'Ера', fire=pygame.K_RETURN)
    tank2 = Tank(spawnpoints[1][0], spawnpoints[1][1], 800//6, (135, 101, 26), 32, 'name2', d_right=pygame.K_d, d_left=pygame.K_a, d_up=pygame.K_w, d_down=pygame.K_s)
    # tank3 = Tank(100, 100, 800//6, (0, 0, 0xff), pygame.K_h, pygame.K_f, pygame.K_t, pygame.K_g, pygame.K_2)
    # tank4 = Tank(100, 200, 800//6, (0xff, 255, 0), pygame.K_l, pygame.K_j, pygame.K_i, pygame.K_k, pygame.K_3)

    tanks += [tank1, tank2]
    box = Box(0.05, free_spaces)
    cycle = 0

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

        screen.fill((201, 175, 135))  # 225, 235, 250
        # screen.blit(background, (0, 0))
        for wall in walls:
            wall.draw()

        if box.is_active:
            box.draw()
            cycle += seconds
            if cycle >= box.interval:
                cycle = 0
                box.cur_image += 1
                box.cur_image %= len(box.images)
        elif box.wait < box.reload: box.wait += seconds
        else:
            box.newBox()
            box.wait = 0
            box.is_active = True

        for i in range(len(tanks)):
            tanks[i].move(seconds, box)
            txt = small_font.render(f'{tanks[i].name}: {tanks[i].lifes} lifes, {tanks[i].score} points', True, (0, 0, 0))
            screen.blit(txt, (5, i*txt.get_size()[1] + 5))
            if tanks[i].lifes <= 0:
                del tanks[i]
                break

        for i in range(len(bullets)):
            bullets[i].move(seconds)
            if checkCollisions(bullets[i]) or bullets[i].lifetime > bullets[i].destroytime:
                del bullets[i]
                break

        pygame.display.flip()

        if len(tanks) == 0:
            winner = ''
            game_over = True
            mainloop = False
        if len(tanks) == 1:
            winner = tanks[0]
            game_over = True
            mainloop = False


##########################################    Multiplayer    ##########################################


def multi():
    global clock, bullets, winner, game_over, screen, buffer, stop_thread, losers, kicked
    screen = pygame.display.set_mode((1200, 800))

    rpc = RpcClient()
    rpc_response = {}
    for i in range(1, 11):
        request = json.dumps({'roomId': f'room-{i}'})
        rpc_response = rpc.call('tank.request.register', request)
        if rpc_response.get('status', 200) == 200: break
        else: print(rpc_response)

    room, name, token = rpc_response['roomId'], rpc_response['tankId'], rpc_response['token']
    room_state = StateEvents(room)
    room_state.start()

    tanks = {}
    tanks[name] = Tank(0, 0, 0, (255, 0, 0), 31, 'You')

    bullets = 0
    mainloop = True
    while mainloop:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                mainloop = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    mainloop = False
                    game_over = True
                if tanks.get(name, '') != '':
                    if event.key == tanks[name].fire_key:
                        request = json.dumps({'token': token})
                        rpc_response = rpc.call('tank.request.fire', request)
                    for key in tanks[name].KEY.keys():
                        if event.key == key:
                            request = json.dumps({'token': token, 'direction': tanks[name].KEY[key].value})
                            rpc_response = rpc.call('tank.request.turn', request)

        if not room_is_ready:
            wait_text = 'Loading...'
            wait_text = big_font.render(wait_text, True, (50, 50, 50))
            screen.fill((255, 255, 255))
            screen.blit(wait_text, (screen.get_size()[0] // 2 - wait_text.get_size()[0] // 2, screen.get_size()[1] // 2 - wait_text.get_size()[1] // 2))
            pygame.display.flip()
            continue

        if len(buffer) != 0:
            screen.fill((201, 175, 135))
            cur_state = buffer.popleft()
            for tank in cur_state['gameField']['tanks']:
                colour = (255, 0, 0) if tank['id'] == name else (0, random.randint(100, 255), 0)
                if not tank['id'] in tanks.keys():
                    tanks[tank['id']] = Tank(tank['x'], tank['y'], 50, colour, tank['width'], tank['id'] if tank['id'] != name else 'You',
                                             Direction[tank['direction']], tank['health'], tank['score'])
                else:
                    tanks[tank['id']].set_values(tank['x'], tank['y'], Direction[tank['direction']], tank['health'], tank['score'])

            for tank in tanks.values():
                tank.draw()

            for bullet in cur_state['gameField']['bullets']:
                pygame.draw.rect(screen, (255, 0, 0) if bullet['owner'] == name else (0, 0, 0), (bullet['x'], bullet['y'], bullet['width'], bullet['height']))
            if len(cur_state['gameField']['bullets']) > bullets: shoot_sound.play(maxtime=1600)
            bullets = len(cur_state['gameField']['bullets'])

            if cur_state['hits']: explosion_sound.play()

            for removed in cur_state['losers']:
                losers.append(tanks[removed['tankId']])
                if removed['tankId'] == name:
                    mainloop = False
                    game_over = True
                try:
                    del tanks[removed['tankId']]
                except Exception as e:
                    print(e)

            for removed in cur_state['kicked']:
                kicked.append(tanks[removed['tankId']])
                if removed['tankId'] == name:
                    mainloop = False
                    game_over = True
                try:
                    del tanks[removed['tankId']]
                except Exception as e:
                    print(e)

            if cur_state['winners']:
                print(cur_state['winners'], tanks)
                mainloop = False
                game_over = True
                for winner_t in cur_state['winners']:
                    winner = tanks[winner_t['tankId']]

        # for tank in tanks.values():
        #     tank.draw()
        # draw info panel, make normal wining (not one), losing

        pygame.display.flip()

    stop_thread = True
    room_state.join()
    screen = pygame.display.set_mode((800, 640))


##########################################    Game launch    ##########################################


while repeat:
    repeat = False
    gamemode = ''
    game_over = False
    tanks = []
    bullets = []
    walls = []
    winner = ''
    losers = []
    kicked = []
    buffer = deque()
    room_is_ready = False
    stop_thread = False
    menu()
    if gamemode == 's': single()
    elif gamemode == 'm': multi()
    if game_over: again()

pygame.quit()
