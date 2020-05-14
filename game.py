import pygame
import json
from helper import screen, clock, FPS, big_font, font, poster, button_sound
from tank_classes import Button
from single import single
from multi import multi
#pylint: disable=no-member


##########################################    Init    ##########################################

repeat = True
gamemode = ''

##########################################    Menu loop    ##########################################


def start(txt):
    button_sound.play()
    if txt == 'Single player': return 's'
    if txt == 'Multiplayer': return 'm'
    if txt == 'Autoplay': return 'a'


def menu():
    global screen, clock, gamemode
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


def again(winner, lost, kicked):
    global repeat
    if kicked:
        text = font.render("You were kicked!", True, (10, 10, 10))
    elif lost:
        text = font.render("You lost!", True, (10, 10, 10))
    elif winner != '':
        text = font.render(winner, True, (10, 10, 10))
    else:
        text = font.render("It's a draw!", True, (10, 10, 10))

    x = screen.get_size()[0] // 2 - text.get_size()[0] // 2
    y = screen.get_size()[1] // 2 - text.get_size()[1] // 2

    text_r = font.render('Press R to play again', True, (200, 200, 200))
    x1 = screen.get_size()[0] // 2 - text_r.get_size()[0] // 2
    y1 = y + text.get_size()[1] + 25

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

        screen.fill((255, 255, 255))
        screen.blit(text, (x, y))
        screen.blit(text_r, (x1, y1))
        pygame.display.flip()


##########################################    Game launch    ##########################################


while repeat:
    repeat = False
    gamemode = ''
    game_over = False
    menu()
    if gamemode == 's': game_over, winner, lost, kicked = single()
    elif gamemode == 'm': game_over, winner, lost, kicked = multi()
    if game_over: again(winner, lost, kicked)

pygame.quit()
