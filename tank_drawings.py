import pygame
from helper import screen, font, small_font, tank_images
#pylint: disable=no-member, too-many-function-args

##########################################    Drawings    ##########################################


def drawScoreboard(name, tanks, room):
    global screen
    pygame.draw.rect(screen, (225, 235, 250), (800, 0, 200, 600))
    pygame.draw.line(screen, (0, 0, 0), (800, 0), (800, 600), 2)
    info_text = font.render('Leaderboard', True, (0, 0, 0))
    screen.blit(info_text, (900 - info_text.get_size()[0] // 2, 10))

    tanks.sort(key=lambda x: x['score'], reverse=True)
    prev_y = 10 + info_text.get_size()[1]
    for tank in tanks:
        t_name = 'You' if tank['id'] == name else tank['id']
        score_text = small_font.render("{}: {}, {} lifes".format(t_name, tank['score'], tank['health']), True, (0, 0, 0))
        screen.blit(score_text, (900 - score_text.get_size()[0] // 2, prev_y + 10))
        prev_y += score_text.get_size()[1]
    
    room_text = small_font.render(f"Room № {room[5:]}", True, (0, 0, 0))
    screen.blit(room_text, (900 - room_text.get_size()[0] // 2, screen.get_size()[1] - room_text.get_size()[1] - 10))


def draw_tank(seconds, name, x, y, id, width, height, direction, **kwargs):
        # tank_c = (x + width // 2, y + height // 2)
        color = (255, 0, 0) if id == name else (0, 255, 0)
        cur_image = int(seconds * 30) % len(tank_images)
        body = pygame.Surface((width, height))
        pygame.draw.rect(body, color, (0, 0, width, height))
        body.set_colorkey((255, 255, 255))
        body.blit(tank_images[cur_image], (0, 0))

        if direction == 'RIGHT':
            body = pygame.transform.rotate(body, -90)

        if direction == 'LEFT':
            body = pygame.transform.rotate(body, 90)

        if direction == 'UP':
            body = pygame.transform.rotate(body, 0)

        if direction == 'DOWN':
            body = pygame.transform.rotate(body, 180)

        screen.blit(body, (x, y))

        txt = small_font.render('You' if id == name else id, True, (0, 0, 0))
        screen.blit(txt, (x + width // 2 - txt.get_size()[0] // 2, y + width + 2))


def draw_bullet(name, x, y, owner, width, height, **kwargs):
        color = (168, 19, 19) if owner == name else (0, 0, 0)
        pygame.draw.rect(screen, color, (x, y, width, height))