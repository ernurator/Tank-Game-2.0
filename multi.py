import pygame
import random
import pika
import json
from threading import Thread
from collections import deque
from helper import screen, clock, FPS, big_font, font, small_font, shoot_sound, explosion_sound
from rpc_client import RpcClient
#pylint: disable=no-member


buffer = deque()
stop_thread = False
room_is_ready = False


##########################################    Room Events    ##########################################

class StateEvents(Thread):
    def __init__(self, room):
        super().__init__()
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


##########################################    Drawings    ##########################################


def drawScoreboard(name, tanks):
    global screen
    pygame.draw.rect(screen, (225, 235, 250), (1000, 0, 200, 800))
    pygame.draw.line(screen, (0, 0, 0), (1000, 0), (1000, 800), 2)
    info_text = font.render('Leaderboard', True, (0, 0, 0))
    screen.blit(info_text, (1100 - info_text.get_size()[0] // 2, 10)) ####

    tanks.sort(key=lambda x: x['score'], reverse=True)
    prev_y = 10 + info_text.get_size()[1]
    for tank in tanks:
        t_name = 'You' if tank['id'] == name else tank['id']
        score_text = small_font.render(f"{t_name}: {tank['score']}, {tank['health']} lifes", True, (0, 0, 0))
        screen.blit(score_text, (1100 - score_text.get_size()[0] // 2, prev_y + 10)) ####
        prev_y += score_text.get_size()[1]


def draw_tank(name, x, y, id, width, height, direction, **kwargs):
        tank_c = (x + width // 2, y + height // 2)
        color = (255, 0, 0) if id == name else (0, 255, 0)
        pygame.draw.rect(screen, color, (x, y, width, width))
        pygame.draw.circle(screen, color, tank_c, width // 2)
        pygame.draw.circle(screen, (0, 0, 0), tank_c, width // 2 - 1, 1)

        if direction == 'RIGHT':
            pygame.draw.line(screen, color, tank_c, (tank_c[0] + width, tank_c[1]), 4)

        if direction == 'LEFT':
            pygame.draw.line(screen, color, tank_c, (tank_c[0] - width, tank_c[1]), 4)

        if direction == 'UP':
            pygame.draw.line(screen, color, tank_c, (tank_c[0], tank_c[1] - width), 4)

        if direction == 'DOWN':
            pygame.draw.line(screen, color, tank_c, (tank_c[0], tank_c[1] + width), 4)

        txt = small_font.render('You' if id == name else id, True, (0, 0, 0))
        screen.blit(txt, (tank_c[0] - txt.get_size()[0] // 2, y + width + 2))


def draw_bullet(name, x, y, owner, width, height, **kwargs):
        color = (255, 0, 0) if owner == name else (0, 0, 0)
        pygame.draw.rect(screen, color, (x, y, width, height))


##########################################    Multiplayer    ##########################################


def multi():
    global clock, screen, buffer, stop_thread, room_is_ready
    screen = pygame.display.set_mode((1200, 800))
    buffer = deque()
    stop_thread = False
    room_is_ready = False

    rpc = RpcClient()
    rpc_response = {}
    for i in range(1, 11):
        # request = json.dumps({'roomId': f'room-{i}'})
        rpc_response = rpc.room_register(f'room-{i}')
        if rpc_response.get('status', 200) == 200: break
        else: print(rpc_response)
    room, name = rpc_response['roomId'], rpc_response['tankId']
    room_state = StateEvents(room)
    room_state.start()

    KEYS = {
        pygame.K_w: 'UP',
        pygame.K_a: 'LEFT',
        pygame.K_d: 'RIGHT',
        pygame.K_s: 'DOWN'
    }

    FIRE_KEY = pygame.K_SPACE

    bullets = 0

    winner = ''
    lost = False
    kicked = False
    game_over = False
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
                if event.key == FIRE_KEY:
                    rpc_response = rpc.fire()
                if event.key in KEYS:
                    direction = KEYS[event.key]
                    rpc_response = rpc.turn_tank(direction)

        if not room_is_ready:
            wait_text = 'Loading...'
            wait_text = big_font.render(wait_text, True, (50, 50, 50))
            screen.fill((255, 255, 255))
            text_rect = wait_text.get_rect(center=(screen.get_size()[0] // 2, screen.get_size()[1] // 2))
            screen.blit(wait_text, text_rect)
            pygame.display.flip()
            continue

        if len(buffer) != 0:
            screen.fill((201, 175, 135))
            cur_state = buffer.popleft()

            remaining_time = cur_state.get('remainingTime', 0)
            text = font.render(f'Remaining time: {remaining_time}', True, (0, 0, 0))
            text_rect = text.get_rect(center=(500, 50))
            screen.blit(text, text_rect)

            drawScoreboard(name, cur_state['gameField']['tanks'])
            for tank in cur_state['gameField']['tanks']:
                draw_tank(name, **tank)

            for bullet in cur_state['gameField']['bullets']:
                draw_bullet(name, **bullet)
            if len(cur_state['gameField']['bullets']) > bullets: shoot_sound.play(maxtime=1600)
            bullets = len(cur_state['gameField']['bullets'])

            if cur_state['hits']: explosion_sound.play()

            for removed in cur_state['losers']:
                if removed['tankId'] == name:
                    lost = True
                    mainloop = False
                    game_over = True

            for removed in cur_state['kicked']:
                if removed['tankId'] == name:
                    kicked = True
                    mainloop = False
                    game_over = True

            if cur_state['winners']:
                mainloop = False
                game_over = True
                winner = cur_state['winners']

        # add time, make normal wining (not one)

        pygame.display.flip()

    stop_thread = True
    room_state.join()
    screen = pygame.display.set_mode((800, 640))
    return game_over, winner, lost, kicked
