import pygame
import random
import math
import csv

pygame.init()

WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ReCaptcha")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
GREEN = (0, 255, 0)

# Game states
START_SCREEN = 0
PLAYING = 1
GAME_OVER = 2

# Player settings
player_size = 20
player_speed = 4

# Movement tracking settings
MOVEMENT_FILE = 'movement.csv'
CURSOR_FILE = 'cursor.csv'
player_movements = []
cursor_movements = []
last_player_pos = None
last_cursor_pos = None

class MovementTracker:
    def __init__(self):
        self.last_pos = None
        self.accumulator = [0, 0]
        self.sampling_rate = 16.67  # ~60Hz sampling
        self.last_sample_time = 0
        self.movement_buffer = []
        
    def update(self, current_pos, current_time):
        if self.last_pos is None:
            self.last_pos = current_pos.copy()
            self.last_sample_time = current_time
            return None
            
        # Calculate sub-pixel movement
        dx = current_pos[0] - self.last_pos[0]
        dy = current_pos[1] - self.last_pos[1]
        
        # Accumulate sub-pixel movements
        self.accumulator[0] += dx
        self.accumulator[1] += dy
        
        # Check if enough time has passed for a new sample
        time_delta = current_time - self.last_sample_time
        if time_delta >= self.sampling_rate:
            # Add some subtle variation to make movement more natural
            noise_x = random.uniform(-0.2, 0.2)
            noise_y = random.uniform(-0.2, 0.2)
            
            # Record position with accumulated movement and noise
            recorded_pos = [
                self.last_pos[0] + self.accumulator[0] + noise_x,
                self.last_pos[1] + self.accumulator[1] + noise_y
            ]
            
            # Reset accumulator and update last position
            self.accumulator = [0, 0]
            self.last_pos = current_pos.copy()
            self.last_sample_time = current_time
            
            return recorded_pos
        
        return None

class Wall:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
    
    def draw(self, screen):
        pygame.draw.rect(screen, GRAY, self.rect)

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.head_hits = 0
        self.body_hits = 0
        self.size = 30
        self.head_size = 12
        
    def draw(self, screen):
        pygame.draw.rect(screen, RED, (self.x - self.size//2, self.y - self.size//2, self.size, self.size))
        pygame.draw.rect(screen, BLUE, (self.x - self.head_size//2, self.y - self.size//2 - self.head_size, self.head_size, self.head_size))
    
    def is_head_hit(self, x, y):
        return (abs(x - self.x) < self.head_size//2 and 
                abs(y - (self.y - self.size//2 - self.head_size//2)) < self.head_size//2)
    
    def is_body_hit(self, x, y):
        return (abs(x - self.x) < self.size//2 and 
                abs(y - self.y) < self.size//2)
    
    def is_dead(self):
        return self.head_hits >= 1 or self.body_hits >= 2
    
    def get_rect(self):
        return pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size + self.head_size)

def create_walls():
    return [
        Wall(100, 100, WIDTH - 200, 20),
        Wall(100, HEIGHT - 120, WIDTH - 200, 20),
        Wall(100, 100, 20, HEIGHT - 200),
        Wall(WIDTH - 120, 100, 20, HEIGHT - 200),  
        Wall(250, 100, 20, 200), 
        Wall(400, HEIGHT - 320, 20, 200),
        Wall(550, 100, 20, 200),
        Wall(250, 400, 200, 20),
        Wall(450, 200, 200, 20)
    ]

def get_random_position():
    return [
        random.randint(120, WIDTH - 140), 
        random.randint(120, HEIGHT - 140) 
    ]

def is_valid_enemy_position(pos, walls, player_pos, existing_enemies):
    enemy_rect = pygame.Rect(pos[0] - 15, pos[1] - 15, 30, 30)
    
    for wall in walls:
        if enemy_rect.colliderect(wall.rect):
            return False
    
    player_dist = math.sqrt((pos[0] - player_pos[0])**2 + (pos[1] - player_pos[1])**2)
    if player_dist < 200:
        return False
    
    for enemy in existing_enemies:
        enemy_dist = math.sqrt((pos[0] - enemy.x)**2 + (pos[1] - enemy.y)**2)
        if enemy_dist < 100:
            return False
    
    return True

def create_random_enemies(walls, player_pos, num_enemies=3):
    enemies = []
    attempts = 0
    max_attempts = 100    
    while len(enemies) < num_enemies and attempts < max_attempts:
        pos = get_random_position()
        if is_valid_enemy_position(pos, walls, player_pos, enemies):
            enemies.append(Enemy(pos[0], pos[1]))
        attempts += 1
    
    return enemies

def check_collision(pos, walls):
    player_rect = pygame.Rect(pos[0] - player_size//2, pos[1] - player_size//2, player_size, player_size)
    for wall in walls:
        if player_rect.colliderect(wall.rect):
            return True
    return False

def check_line_of_sight(start_pos, end_pos, walls):
    for wall in walls:
        line_start = pygame.math.Vector2(start_pos[0], start_pos[1])
        line_end = pygame.math.Vector2(end_pos[0], end_pos[1])
        
        wall_lines = [
            (pygame.math.Vector2(wall.rect.topleft), pygame.math.Vector2(wall.rect.topright)),
            (pygame.math.Vector2(wall.rect.topright), pygame.math.Vector2(wall.rect.bottomright)),
            (pygame.math.Vector2(wall.rect.bottomright), pygame.math.Vector2(wall.rect.bottomleft)),
            (pygame.math.Vector2(wall.rect.bottomleft), pygame.math.Vector2(wall.rect.topleft))
        ]
        
        for wall_line in wall_lines:
            if line_segments_intersect(line_start, line_end, wall_line[0], wall_line[1]):
                return False
    return True

def line_segments_intersect(p1, p2, p3, p4):
    def ccw(A, B, C):
        return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)
    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

def init_game():
    player_pos = [150, HEIGHT - 150]
    walls = create_walls()
    enemies = create_random_enemies(walls, player_pos)
    movement_tracker = MovementTracker()
    return {
        'player_pos': player_pos,
        'walls': walls,
        'enemies': enemies,
        'game_state': START_SCREEN,
        'game_won': False,
        'data_saved': False,
        'movement_tracker': movement_tracker
    }

def update_game(game_data, current_time):
    if game_data['game_state'] == PLAYING and not game_data['game_won']:
        recorded_pos = game_data['movement_tracker'].update(game_data['player_pos'], current_time)
        if recorded_pos:
            record_movement(current_time, recorded_pos[0], recorded_pos[1], player_movements)

def record_movement(timestamp, x, y, movement_list):
    movement_list.append([timestamp, x, y])

def save_movements_to_csv():
    # Save player movements
    if player_movements:
        with open(MOVEMENT_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'X', 'Y'])
            writer.writerows(player_movements)
    
    # Save cursor movements
    if cursor_movements:
        with open(CURSOR_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'X', 'Y'])
            writer.writerows(cursor_movements)

def clear_movement_data():
    global player_movements, cursor_movements, last_player_pos, last_cursor_pos
    # Clear the movement lists
    player_movements = []
    cursor_movements = []
    last_player_pos = None
    last_cursor_pos = None
    
    # Clear the files by writing just the headers
    with open(MOVEMENT_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'X', 'Y'])
    
    with open(CURSOR_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'X', 'Y'])

game_data = init_game()
running = True
clock = pygame.time.Clock()

font = pygame.font.Font(None, 74)
small_font = pygame.font.Font(None, 36)


clear_movement_data()

while running:
    current_time = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_movements_to_csv()
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                save_movements_to_csv()
                game_data = init_game()
                clear_movement_data()
            elif event.key == pygame.K_SPACE and game_data['game_state'] == START_SCREEN:
                game_data['game_state'] = PLAYING
                clear_movement_data()
        elif event.type == pygame.MOUSEBUTTONDOWN and game_data['game_state'] == PLAYING:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            for enemy in game_data['enemies']:
                if not enemy.is_dead():
                    if check_line_of_sight(game_data['player_pos'], [enemy.x, enemy.y], game_data['walls']):
                        if enemy.is_head_hit(mouse_x, mouse_y):
                            enemy.head_hits += 1
                        elif enemy.is_body_hit(mouse_x, mouse_y):
                            enemy.body_hits += 1
    
    screen.fill(BLACK)

    if game_data['game_state'] == START_SCREEN:
        title = font.render('ReCaptcha', True, WHITE)
        start_text = small_font.render('Press SPACE to Start', True, WHITE)
        controls_text = small_font.render('WASD to move, Mouse to aim and shoot, R to restart', True, WHITE)
        
        title_rect = title.get_rect(center=(WIDTH/2, HEIGHT/3))
        start_rect = start_text.get_rect(center=(WIDTH/2, HEIGHT/2))
        controls_rect = controls_text.get_rect(center=(WIDTH/2, HEIGHT*2/3))
        
        screen.blit(title, title_rect)
        screen.blit(start_text, start_rect)
        screen.blit(controls_text, controls_rect)

    elif game_data['game_state'] == PLAYING:
        if not game_data['game_won']:
            # Track player movement
            update_game(game_data, current_time)
            
            # Track cursor movement
            current_cursor_pos = pygame.mouse.get_pos()
            if last_cursor_pos is None:
                last_cursor_pos = current_cursor_pos
            elif current_cursor_pos != last_cursor_pos:
                record_movement(current_time, current_cursor_pos[0], current_cursor_pos[1], cursor_movements)
                last_cursor_pos = current_cursor_pos


            new_pos = game_data['player_pos'].copy()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a]:
                new_pos[0] -= player_speed
            if keys[pygame.K_d]:
                new_pos[0] += player_speed
            if keys[pygame.K_w]:
                new_pos[1] -= player_speed
            if keys[pygame.K_s]:
                new_pos[1] += player_speed
            
            if not check_collision(new_pos, game_data['walls']):
                game_data['player_pos'] = new_pos

        for wall in game_data['walls']:
            wall.draw(screen)
        
        for enemy in game_data['enemies']:
            if not enemy.is_dead() and check_line_of_sight(game_data['player_pos'], [enemy.x, enemy.y], game_data['walls']):
                pygame.draw.line(screen, GREEN, game_data['player_pos'], (enemy.x, enemy.y), 1)
        
        pygame.draw.circle(screen, WHITE, game_data['player_pos'], player_size//2)
        
        crosshair_pos = pygame.mouse.get_pos()
        pygame.draw.line(screen, WHITE, (crosshair_pos[0] - 10, crosshair_pos[1]), (crosshair_pos[0] + 10, crosshair_pos[1]))
        pygame.draw.line(screen, WHITE, (crosshair_pos[0], crosshair_pos[1] - 10), (crosshair_pos[0], crosshair_pos[1] + 10))
        
        all_dead = True
        for enemy in game_data['enemies']:
            if not enemy.is_dead():
                enemy.draw(screen)
                all_dead = False
        
        if all_dead:
            game_data['game_won'] = True
            if not game_data['data_saved']:
                save_movements_to_csv()
                game_data['data_saved'] = True
            
            win_text = font.render('You Won!', True, WHITE)
            restart_text = small_font.render('Press R to Restart', True, WHITE)
            
            win_rect = win_text.get_rect(center=(WIDTH/2, HEIGHT/2))
            restart_rect = restart_text.get_rect(center=(WIDTH/2, HEIGHT/2 + 50))
            
            screen.blit(win_text, win_rect)
            screen.blit(restart_text, restart_rect)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()