import pygame
import random
from helper import screen, clock, FPS, big_font, font, small_font, shoot_sound, explosion_sound
from rpc_client import RpcClient
from room_events import RoomEvents
from tank_drawings import draw_tank, draw_bullet, drawScoreboard
from tank_ai import AI
#pylint: disable=no-member, too-many-function-args


def autoplay():
    global clock, screen
    screen = pygame.display.set_mode((1000, 600))

    rpc = RpcClient()
    rpc_response = {}
    for i in range(1, 31):
        rpc_response = rpc.room_register(f'room-{i}')
        if rpc_response.get('status', 200) == 200: break
        else: print(rpc_response)
    room, name = rpc_response['roomId'], rpc_response['tankId']
    room_state = RoomEvents(room)
    room_state.start()

    ai = AI(name)

    counter = 0
    seconds = 0

    winner = ''
    lost = False
    kicked = False
    game_over = False
    mainloop = True
    while mainloop:
        millis = clock.tick(FPS)
        seconds += millis / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                mainloop = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    mainloop = False
                    game_over = True

        if not room_state.ready:
            wait_text = 'Loading...'
            wait_text = big_font.render(wait_text, True, (50, 50, 50))
            screen.fill((255, 255, 255))
            text_rect = wait_text.get_rect(center=(screen.get_size()[0] // 2, screen.get_size()[1] // 2))
            screen.blit(wait_text, text_rect)

        elif room_state.response:
            screen.fill((201, 175, 135))
            cur_state = room_state.response
            tanks = cur_state['gameField']['tanks']
            bullets = cur_state['gameField']['bullets']

            ai.start(tanks, bullets)
            if ai.fire:
                rpc_response = rpc.fire()
                ai.fire = False
                ai.last_action = seconds
            if ai.turn_direction:
                print(ai.turn_direction)
                rpc_response = rpc.turn_tank(ai.turn_direction)
                ai.turn_direction = ''
                ai.last_action = seconds
            if ai.last_action + 10 < seconds:
                ai.turn_direction = random.choice(ai.directions)

            remaining_time = cur_state.get('remainingTime', 0)
            text = font.render(f'Remaining time: {remaining_time}', True, (0, 0, 0))
            text_rect = text.get_rect(center=(400, 50))
            screen.blit(text, text_rect)

            drawScoreboard(name, tanks, room)
            for tank in tanks:
                draw_tank(seconds, name, **tank)

            for bullet in bullets:
                draw_bullet(name, **bullet)
            if len(bullets) > counter: shoot_sound.play(maxtime=1600)
            counter = len(bullets)

            if room_state.new and cur_state['hits']:
                room_state.new = False
                explosion_sound.play()

            if next((x for x in cur_state['losers'] if x['tankId'] == name), None):
                lost = True
                mainloop = False
                game_over = True

            elif next((x for x in cur_state['kicked'] if x['tankId'] == name), None):
                kicked = True
                mainloop = False
                game_over = True

            elif cur_state['winners']:
                mainloop = False
                game_over = True
                win_text = 'Congrats! Score: {}. Winner(-s): '.format(cur_state["winners"][0]["score"])
                winner = win_text + ', '.join(map(lambda i: i['tankId'] if i['tankId'] != name else 'You', cur_state['winners']))

            elif next((x for x in room_state.winners if x['tankId'] == name), None):
                mainloop = False
                game_over = True
                win_text = 'Congrats! Score: {}. Winner(-s): '.format(room_state.winners[0]["score"])
                winner = win_text + ', '.join(map(lambda i: i['tankId'] if i['tankId'] != name else 'You', room_state.winners))

            elif not next((x for x in tanks if x['id'] == name), None):
                lost = True
                mainloop = False
                game_over = True

        pygame.display.flip()

    room_state.kill = True
    room_state.join()
    screen = pygame.display.set_mode((800, 640))
    return game_over, winner, lost, kicked
