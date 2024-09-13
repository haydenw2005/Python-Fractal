import pygame
import random
import sys

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 300
SCREEN_HEIGHT = 600
BLOCK_SIZE = 30

# Grid dimensions
GRID_WIDTH = SCREEN_WIDTH // BLOCK_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // BLOCK_SIZE

# Colors (you can customize these to cat-themed colors)
COLORS = [
    (255, 182, 193),  # Light Pink
    (255, 160, 122),  # Light Salmon
    (255, 228, 181),  # Moccasin
    (240, 230, 140),  # Khaki
    (152, 251, 152),  # Pale Green
    (175, 238, 238),  # Pale Turquoise
    (216, 191, 216),  # Thistle
]

# Cat-themed tetromino shapes
TETROMINOS = {
    'I': [['.....',
           '..C..',
           '..C..',
           '..C..',
           '..C..',
           '..C..',
           '.....']],
    
}

CAT_IMAGE = pygame.image.load('olli-the-polite-cat.jpg')
CAT_IMAGE = pygame.transform.scale(CAT_IMAGE, (BLOCK_SIZE, BLOCK_SIZE))


# Function to create a grid
def create_grid(locked_positions={}):
    grid = [[(0,0,0) for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if (x,y) in locked_positions:
                c = locked_positions[(x,y)]
                grid[y][x] = c
    return grid

# Class for the tetromino pieces
class Piece(object):
    def __init__(self, x, y, shape, color):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = color
        self.rotation = 0

# Function to convert shape formats
def convert_shape_format(shape):
    positions = []
    format = shape.shape[shape.rotation % len(shape.shape)]
    for i, line in enumerate(format):
        row = list(line)
        for j, column in enumerate(row):
            if column == 'C':  # Cat-themed block part
                positions.append((shape.x + j, shape.y + i))
    return positions

# Function to check if position is valid
def valid_space(shape, grid):
    accepted_pos = [[(j, i) for j in range(GRID_WIDTH) if grid[i][j] == (0,0,0)] for i in range(GRID_HEIGHT)]
    accepted_pos = [j for sub in accepted_pos for j in sub]
    formatted = convert_shape_format(shape)
    for pos in formatted:
        if pos not in accepted_pos:
            if pos[1] > -1:
                return False
    return True

# Function to check if game is lost
def check_lost(positions):
    for pos in positions:
        x, y = pos
        if y < 1:
            return True
    return False

# Function to get a random shape
def get_shape():
    global shapes, COLORS
    shape_name = random.choice(list(TETROMINOS.keys()))
    return Piece(GRID_WIDTH//2 - 2, 0, TETROMINOS[shape_name], random.choice(COLORS))

# Function to draw text in the middle
def draw_text_middle(surface, text, size, color):
    font = pygame.font.SysFont("comicsans", size, bold=True)
    label = font.render(text, True, color)
    surface.blit(label, (SCREEN_WIDTH/2 - (label.get_width()/2), SCREEN_HEIGHT/2 - label.get_height()/2))

# Function to clear rows
def clear_rows(grid, locked):
    inc = 0
    for i in range(GRID_HEIGHT-1, -1, -1):
        row = grid[i]
        if (0,0,0) not in row:
            inc += 1
            ind = i
            for j in range(GRID_WIDTH):
                try:
                    del locked[(j, i)]
                except:
                    continue
    if inc > 0:
        for key in sorted(list(locked), key=lambda x: x[1])[::-1]:
            x, y = key
            if y < ind:
                newKey = (x, y + inc)
                locked[newKey] = locked.pop(key)
    return inc


def choose_next_piece(surface):
    options = list(TETROMINOS.keys())
    selected = 0
    choosing = True
    clock = pygame.time.Clock()
    while choosing:
        surface.fill((0, 0, 0))
        font = pygame.font.SysFont('comicsans', 30)
        label = font.render('Choose your next block:', True, (255, 255, 255))
        surface.blit(label, (SCREEN_WIDTH / 2 - label.get_width() / 2, 50))

        for idx, option in enumerate(options):
            color = (255, 255, 255)
            if idx == selected:
                color = (255, 0, 0)  # Highlight selected option
            option_label = font.render(option, True, color)
            surface.blit(option_label, (SCREEN_WIDTH / 2 - option_label.get_width() / 2, 100 + idx * 40))

        pygame.display.update()
        clock.tick(10)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                choosing = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    choosing = False

    shape_name = options[selected]
    return Piece(GRID_WIDTH // 2 - 2, 0, TETROMINOS[shape_name], random.choice(COLORS))

# Main game function
def main(win):
    locked_positions = {}
    grid = create_grid(locked_positions)
    change_piece = False
    run = True
    current_piece = get_shape()
    next_piece = get_shape()
    clock = pygame.time.Clock()
    fall_time = 0
    fall_speed = 0.27
    score = 0
    while run:
        fall_time += clock.get_rawtime()
        clock.tick()
        # Piece falling logic
        if fall_time/1000 >= fall_speed:
            fall_time = 0
            current_piece.y +=1
            if not(valid_space(current_piece, grid)) and current_piece.y > 0:
                current_piece.y -=1
                change_piece = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.display.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_piece.x -=1
                    if not(valid_space(current_piece, grid)):
                        current_piece.x +=1
                elif event.key == pygame.K_RIGHT:
                    current_piece.x +=1
                    if not(valid_space(current_piece, grid)):
                        current_piece.x -=1
                elif event.key == pygame.K_DOWN:
                    current_piece.y +=1
                    if not(valid_space(current_piece, grid)):
                        current_piece.y -=1
                elif event.key == pygame.K_UP:
                    current_piece.rotation +=1
                    if not(valid_space(current_piece, grid)):
                        current_piece.rotation -=1
        shape_pos = convert_shape_format(current_piece)
        for i in range(len(shape_pos)):
            x, y = shape_pos[i]
            if y > -1:
                grid[y][x] = current_piece.color
        if change_piece:
            for pos in shape_pos:
                p = (pos[0], pos[1])
                locked_positions[p] = current_piece.color
            lines_cleared = clear_rows(grid, locked_positions)
            if lines_cleared == 4:
                # Player gets to choose the next piece
                next_piece = choose_next_piece(win)
                options = list(TETROMINOS.keys())
                print("You cleared a Tetris! Choose your next block:")
                for idx, option in enumerate(options):
                    print(f"{idx + 1}: {option}")
                choice = None
                while choice not in range(1, len(options) + 1):
                    try:
                        choice = int(input("Enter the number of your choice: "))
                    except ValueError:
                        continue
                next_piece = choose_next_piece(win)
            else:
                next_piece = get_shape()
            current_piece = next_piece
            change_piece = False
            score += lines_cleared
        grid = create_grid(locked_positions)
        draw_window(win, grid, score)
        pygame.display.update()
        if check_lost(locked_positions):
            run = False
    draw_text_middle(win, "YOU LOST", 80, (255,255,255))
    pygame.display.update()
    pygame.time.delay(2000)

# Function to draw the window
def draw_window(surface, grid, score=0):
    surface.fill((0,0,0))
    # Title
    font = pygame.font.SysFont('comicsans', 60)
    label = font.render('Cat Tetris', True, (255,255,255))
    surface.blit(label, (SCREEN_WIDTH / 2 - (label.get_width() / 2), 30))
    # Current score
    font = pygame.font.SysFont('comicsans', 30)
    label = font.render(f'Score: {score}', True, (255,255,255))
    surface.blit(label, (10, 10))
    # Draw grid
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if grid[i][j] != (0, 0, 0):  # Only draw if the block is not black
                surface.blit(CAT_IMAGE, (j * BLOCK_SIZE, i * BLOCK_SIZE))

    draw_grid(surface)

# Function to draw grid lines
def draw_grid(surface):
    sx = 0
    sy = 0
    for i in range(GRID_HEIGHT):
        pygame.draw.line(surface, (128,128,128), (sx, sy + i*BLOCK_SIZE), (sx + SCREEN_WIDTH, sy + i*BLOCK_SIZE))
        for j in range(GRID_WIDTH):
            pygame.draw.line(surface, (128,128,128), (sx + j*BLOCK_SIZE, sy), (sx + j*BLOCK_SIZE, sy + SCREEN_HEIGHT))

# Start the game
def main_menu():
    win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Cat Tetris')
    main(win)

if __name__ == '__main__':
    main_menu()

