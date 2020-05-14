import pygame
from helper import screen, font, small_font

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
        score_text = small_font.render(f"{t_name}: {tank['score']}, {tank['health']} lifes", True, (0, 0, 0))
        screen.blit(score_text, (900 - score_text.get_size()[0] // 2, prev_y + 10))
        prev_y += score_text.get_size()[1]
    
    room_text = small_font.render(f"Room № {room[5:]}", True, (0, 0, 0))
    screen.blit(room_text, (900 - room_text.get_size()[0] // 2, screen.get_size()[1] - room_text.get_size()[1] - 10))


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