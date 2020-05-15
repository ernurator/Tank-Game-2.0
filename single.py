import pygame
from helper import screen, clock, FPS, small_font, poster, explosion_sound, button_sound, shoot_sound
from tank_classes import Tank, Bullet, Wall, Box, Direction, Box, Button
#pylint: disable=no-member


##########################################    Collisions    ##########################################


def checkCollisions(obj1, obj2, is_list1, is_list2):
    return pygame.Rect(obj1.coord if is_list1 else (obj1.x, obj1.y), obj1.size).colliderect(pygame.Rect(obj2.coord if is_list2 else (obj2.x, obj2.y), obj2.size))


##########################################    Main loop    ##########################################


def single():
    global clock, screen
    bullets, tanks, walls = [], [], []
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
    tank1 = Tank(spawnpoints[0][0], spawnpoints[0][1], 800//6, (3, 102, 6), 32, 'Player 1', fire=pygame.K_RETURN)
    tank2 = Tank(spawnpoints[1][0], spawnpoints[1][1], 800//6, (135, 101, 26), 32, 'Player 2', d_right=pygame.K_d, d_left=pygame.K_a, d_up=pygame.K_w, d_down=pygame.K_s)
    # tank3 = Tank(100, 100, 800//6, (0, 0, 0xff), pygame.K_h, pygame.K_f, pygame.K_t, pygame.K_g, pygame.K_2)
    # tank4 = Tank(100, 200, 800//6, (0xff, 255, 0), pygame.K_l, pygame.K_j, pygame.K_i, pygame.K_k, pygame.K_3)

    tanks += [tank1, tank2]
    box = Box(0.05, free_spaces)
    cycle = 0

    winner = ''
    game_over = False
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
                    game_over = True
                for tank in tanks:
                    if event.key == tank.fire_key:
                        bullets.append(Bullet(tank))

        pressed = pygame.key.get_pressed()
        for tank in tanks:
            # print(tank.direction)
            # stay = True
            for key in tank.KEY.keys():
                if pressed[key]:
                    tank.changeDirection(tank.KEY[key])
                    tank.is_static = False
                    # stay = False
            # if stay:
            #     tank.is_static = True

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
            tanks[i].move(seconds, box, tanks)
            txt = small_font.render(f'{tanks[i].name}: {tanks[i].lifes} lifes, {tanks[i].score} points', True, (0, 0, 0))
            screen.blit(txt, (5, i*txt.get_size()[1] + 5))
            for j in range(len(walls)):
                if checkCollisions(tanks[i], walls[j], False, True):
                    tanks[i].lifes -= 1
                    del walls[j]
                    break
            for j in range(len(bullets)):
                if checkCollisions(tanks[i], bullets[j], False, False):
                    explosion_sound.play()
                    bullets[j].tank.score += 1
                    tanks[i].lifes -= 1
                    del bullets[j]
                    break
            if tanks[i].lifes <= 0:
                del tanks[i]
                break

        for i in range(len(bullets)):
            bullets[i].move(seconds)
            if bullets[i].lifetime > bullets[i].destroytime:
                del bullets[i]
                break
            for j in range(len(walls)):
                if checkCollisions(bullets[i], walls[j], False, True):
                    bullets[i].lifetime = 10
                    del walls[j]
                    break

        pygame.display.flip()

        if len(tanks) == 0:
            winner = ''
            game_over = True
            mainloop = False
        if len(tanks) == 1:
            win_tank = tanks[0]
            winner = f'Congrats! Score: {win_tank.score}. Winner(-s): {win_tank.name}'
            game_over = True
            mainloop = False

    return game_over, winner, False, False
