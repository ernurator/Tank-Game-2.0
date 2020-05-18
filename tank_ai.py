import pygame
#pylint: disable=no-member

RADIUS = 200

def opposite_direction(direction):
    if direction == 'LEFT':
        return 'RIGHT'
    if direction == 'RIGHT':
        return 'LEFT'
    if direction == 'UP':
        return 'DOWN'
    if direction == 'DOWN':
        return 'UP'

def create_rect(speed, x, y, width, height, direction, seconds=1, **kwargs):
    rects = []
    for i in range(1, 10*seconds + 1):
        if direction == 'LEFT':
            rects.append(pygame.Rect(int(x - speed * i / 10), y, width, height))
        if direction == 'RIGHT':
            rects.append(pygame.Rect(int(x + speed * i / 10), y, width, height))
        if direction == 'UP':
            rects.append(pygame.Rect(x, int(y - speed * i / 10), width, height))
        if direction == 'DOWN':
            rects.append(pygame.Rect(x, int(y + speed * i / 10), width, height))
    return rects

def new_rects(speed, x, y, width, height, direction, seconds=1, **kwargs):
    if direction == 'LEFT':
        return create_rect(speed, x-15, y+13, 15, 5, direction, seconds)
    if direction == 'RIGHT':
        return create_rect(speed, x+width, y+13, 15, 5, direction, seconds)
    if direction == 'UP':
        return create_rect(speed, x+13, y-15, 5, 15, direction, seconds)
    if direction == 'DOWN':
        return create_rect(speed, x+13, y+height, 5, 15, direction, seconds)

def future_collisions(obj1, obj2):
    return any(list(map(lambda x, y: x.colliderect(y), obj1, obj2)))


class AI:
    def __init__(self, name):
        self.name = name
        self.fire = False
        self.last_action = 0
        self.turn_direction = 'UP'
        self.directions = ['RIGHT', 'LEFT', 'UP', 'DOWN']

    def start(self, tanks, bullets):
        me = next((x for x in tanks if x['id'] == self.name), None)
        if not me: return
        bullets = list(filter(lambda x: x['owner'] != self.name, bullets))
        tanks = list(filter(lambda x: x['id'] != self.name, tanks))
        dangerous_bullets = []
        me_rects = create_rect(50, **me)
        for bullet in bullets:
            bullet_rects = create_rect(100, **bullet)
            dist_x = bullet['x'] - me['x']
            dist_y = bullet['y'] - me['y']
            if bullet['direction'] == 'UP' and (me['direction'] == 'UP' or me['direction'] == 'DOWN'):
                if 0 < dist_y < RADIUS + me['height'] and -bullet['width'] < dist_x < me['width']:
                    direction = 'RIGHT' if dist_x + bullet['width'] // 2 < me['width'] // 2 else 'LEFT'
                    dangerous_bullets.append({'distance': dist_y - me['height'], 'turn': direction})

            elif bullet['direction'] == 'DOWN' and (me['direction'] == 'UP' or me['direction'] == 'DOWN'):
                if -bullet['height'] - RADIUS < dist_y < 0 and -bullet['width'] < dist_x < me['width']:
                    direction = 'RIGHT' if dist_x + bullet['width'] // 2 < me['width'] // 2 else 'LEFT'
                    dangerous_bullets.append({'distance': -dist_y - bullet['height'], 'turn': direction})

            elif bullet['direction'] == 'LEFT' and (me['direction'] == 'LEFT' or me['direction'] == 'RIGHT'):
                if 0 < dist_x < RADIUS + me['width'] and -bullet['height'] < dist_y < me['height']:
                    direction = 'DOWN' if dist_y + bullet['height'] // 2 < me['height'] // 2 else 'UP'
                    dangerous_bullets.append({'distance': dist_x - me['width'], 'turn': direction})

            elif bullet['direction'] == 'RIGHT' and (me['direction'] == 'LEFT' or me['direction'] == 'RIGHT'):
                if -RADIUS - bullet['width'] < dist_x < 0 and -bullet['height'] < dist_y < me['height']:
                    direction = 'DOWN' if dist_y + bullet['height'] // 2 < me['height'] // 2 else 'UP'
                    dangerous_bullets.append({'distance': -dist_x - bullet['width'], 'turn': direction})

            elif future_collisions(me_rects, bullet_rects):
                direction = opposite_direction(me['direction'])
                height = max(dist_y - me['height'], -dist_y - bullet['height'])
                width = max(dist_x - me['width'], -dist_x - bullet['width'])
                distance = height if bullet['direction'] == 'UP' or bullet['direction'] == 'DOWN' else width
                dangerous_bullets.append({'distance': distance, 'turn': direction})

        mybullet_rects = new_rects(100, seconds=2, **me)
        tanks_rects = []
        for tank in tanks:
            tank_rects = create_rect(50, seconds=2, **tank)
            tanks_rects.append(tank_rects)
            dist_x = tank['x'] - me['x']
            dist_y = tank['y'] - me['y']
            if tank['direction'] == 'UP' and me['direction'] == 'DOWN':
                if 0 < dist_y < RADIUS + me['height'] and -tank['width'] < dist_x < me['width']:
                    direction = 'RIGHT' if dist_x + tank['width'] // 2 < me['width'] // 2 else 'LEFT'
                    dangerous_bullets.append({'distance': dist_y - me['height'], 'turn': direction})
                    self.fire = True

            elif tank['direction'] == 'DOWN' and me['direction'] == 'UP':
                if -tank['height'] - RADIUS < dist_y < 0 and -tank['width'] < dist_x < me['width']:
                    direction = 'RIGHT' if dist_x + tank['width'] // 2 < me['width'] // 2 else 'LEFT'
                    dangerous_bullets.append({'distance': -dist_y - tank['height'], 'turn': direction})
                    self.fire = True

            elif tank['direction'] == 'LEFT' and me['direction'] == 'RIGHT':
                if 0 < dist_x < RADIUS + me['width'] and -tank['height'] < dist_y < me['height']:
                    direction = 'DOWN' if dist_y + tank['height'] // 2 < me['height'] // 2 else 'UP'
                    dangerous_bullets.append({'distance': dist_x - me['width'], 'turn': direction})
                    self.fire = True

            elif tank['direction'] == 'RIGHT' and me['direction'] == 'LEFT':
                if -RADIUS - tank['width'] < dist_x < 0 and -tank['height'] < dist_y < me['height']:
                    direction = 'DOWN' if dist_y + tank['height'] // 2 < me['height'] // 2 else 'UP'
                    dangerous_bullets.append({'distance': -dist_x - tank['width'], 'turn': direction})
                    self.fire = True

            elif future_collisions(me_rects, tank_rects):
                direction = opposite_direction(me['direction'])
                height = max(dist_y - me['height'], -dist_y - tank['height'])
                width = max(dist_x - me['width'], -dist_x - tank['width'])
                distance = height if tank['direction'] == 'UP' or tank['direction'] == 'DOWN' else width
                dangerous_bullets.append({'distance': distance, 'turn': direction})

            if future_collisions(mybullet_rects, tank_rects):
                self.fire = True

        if dangerous_bullets:
            self.turn_direction = min(dangerous_bullets, key=lambda x: x['distance'])['turn']
        else:
            for direction in self.directions:
                found = False
                if direction == me['direction']: continue
                mybullet_rects_turn = new_rects(100, me['x'], me['y'], me['width'], me['height'], direction=direction, seconds=2)
                for i in range(len(tanks)):
                    if future_collisions(mybullet_rects_turn, tanks_rects[i]) and max(tanks[i]['y'] - me['y'] - me['height'], -tanks[i]['y'] + me['y'] - tanks[i]['height'], tanks[i]['x'] - me['x'] - me['width'], -tanks[i]['x'] + me['x'] - tanks[i]['width']) > 20:
                        self.turn_direction = direction
                        found = True
                        break
                if found: break
