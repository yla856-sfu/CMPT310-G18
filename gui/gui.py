import pygame
from game import game

CELL_SIZE = 40

BOARD_LEFT = 60
BOARD_TOP = 60

BOARD_PIXEL_SIZE = CELL_SIZE * (game.SIZE - 1)

WINDOW_WIDTH = 850
WINDOW_HEIGHT = 700

INFO_LEFT = 640

RESTART_BUTTON_X = 640
RESTART_BUTTON_Y = 500
RESTART_BUTTON_WIDTH = 130
RESTART_BUTTON_HEIGHT = 45

# Map string board coordinates to GUI coordinates. Like (7,7) will be (340,340)
def board_to_screen(x, y):
    screen_x = BOARD_LEFT + x * CELL_SIZE
    screen_y = BOARD_TOP + (game.SIZE - 1 - y) * CELL_SIZE
    return screen_x, screen_y

# Map GUI coordinates to string board coordinates
def screen_to_board(mouse_x, mouse_y):
    x = round((mouse_x - BOARD_LEFT) / CELL_SIZE)
    y_from_top = round((mouse_y - BOARD_TOP) / CELL_SIZE)
    y = game.SIZE - 1 - y_from_top

    if x < 0 or x >= game.SIZE:
        return None, None
    if y < 0 or y >= game.SIZE:
        return None, None

    point_x, point_y = board_to_screen(x, y)

    distance = ((mouse_x - point_x) ** 2 + (mouse_y - point_y) ** 2) ** 0.5

    if distance <= 18:
        return x, y

    return None, None


# Draw the board grid, axis labels, and all placed stones for the current game state.
def draw_board(screen, font):
    screen.fill((230, 190, 120))

    for i in range(game.SIZE):
        x1 = BOARD_LEFT
        y1 = BOARD_TOP + i * CELL_SIZE
        x2 = BOARD_LEFT + BOARD_PIXEL_SIZE
        y2 = y1

        pygame.draw.line(screen, (0, 0, 0), (x1, y1), (x2, y2), 2)

        x1 = BOARD_LEFT + i * CELL_SIZE
        y1 = BOARD_TOP
        x2 = x1
        y2 = BOARD_TOP + BOARD_PIXEL_SIZE

        pygame.draw.line(screen, (0, 0, 0), (x1, y1), (x2, y2), 2)

    for x in range(game.SIZE):
        text = font.render(str(x), True, (0, 0, 0))
        screen_x = BOARD_LEFT + x * CELL_SIZE - 6
        screen_y = BOARD_TOP + BOARD_PIXEL_SIZE + 15
        screen.blit(text, (screen_x, screen_y))

    for y in range(game.SIZE):
        text = font.render(str(y), True, (0, 0, 0))
        screen_x = BOARD_LEFT - 30
        screen_y = BOARD_TOP + (game.SIZE - 1 - y) * CELL_SIZE - 8
        screen.blit(text, (screen_x, screen_y))

    for y in range(game.SIZE):
        for x in range(game.SIZE):
            if game.board[y][x] != game.EMPTY:
                screen_x, screen_y = board_to_screen(x, y)

                if game.board[y][x] == game.PLAYER1:
                    color = (0, 0, 0)
                else:
                    color = (255, 255, 255)

                pygame.draw.circle(screen, color, (screen_x, screen_y), 16)
                pygame.draw.circle(screen, (0, 0, 0), (screen_x, screen_y), 16, 1)


# Draw the sidebar: game title, player/AI/turn info, and the wrapped status message.
def draw_info(screen, font, big_font, message, turn_count, ai_type):
    title = big_font.render("Gomoku", True, (0, 0, 0))
    screen.blit(title, (INFO_LEFT, 60))

    text1 = font.render("Player: Black", True, (0, 0, 0))
    text2 = font.render("AI: White", True, (0, 0, 0))
    text3 = font.render("Board: 15 x 15", True, (0, 0, 0))
    text4 = font.render("Turn: " + str(turn_count), True, (0, 0, 0))
    text5 = font.render("AI Type: " + ai_type, True, (0, 0, 0))

    screen.blit(text1, (INFO_LEFT, 120))
    screen.blit(text2, (INFO_LEFT, 150))
    screen.blit(text3, (INFO_LEFT, 180))
    screen.blit(text4, (INFO_LEFT, 210))
    screen.blit(text5, (INFO_LEFT, 240))

    text = font.render("Message:", True, (0, 0, 0))
    screen.blit(text, (INFO_LEFT, 270))

    lines = split_message(message, 18)

    y = 300
    for line in lines:
        text = font.render(line, True, (0, 0, 0))
        screen.blit(text, (INFO_LEFT, y))
        y += 28

# Word-wrap text into lines no longer than max_length so long messages fit in the
# sidebar without overflowing, without breaking words mid-way.
def split_message(text, max_length):
    lines = []

    for part in text.split("\n"):
        current = ""

        for word in part.split(" "):
            if current == "":
                candidate = word
            else:
                candidate = current + " " + word

            if len(candidate) > max_length and current != "":
                lines.append(current)
                current = word
            else:
                current = candidate

        if current != "":
            lines.append(current)

    return lines

# Show the AI-selection menu and block until the user clicks a button, returning its AI type.
def choose_ai(screen, font, big_font):
    menu_button_width = 600
    menu_left = (WINDOW_WIDTH - menu_button_width) // 2

    button_height = 60
    row_gap = 25
    menu_top = 160

    row_button_gap = 12
    mini_button_width = (menu_button_width - 3 * row_button_gap) / 4

    row0_y = menu_top
    row1_y = row0_y + button_height + row_gap
    row2_y = row1_y + button_height + row_gap
    row3_y = row2_y + button_height + row_gap
    row4_y = row3_y + button_height + row_gap

    random_button = pygame.Rect(menu_left, row0_y, menu_button_width, button_height)
    greedy_button = pygame.Rect(menu_left, row1_y, menu_button_width, button_height)

    minimax1_button = pygame.Rect(menu_left, row2_y, mini_button_width, button_height)
    minimax2_button = pygame.Rect(menu_left+(mini_button_width+row_button_gap), row2_y, mini_button_width, button_height)
    minimax3_button = pygame.Rect(menu_left+(mini_button_width+row_button_gap)*2, row2_y, mini_button_width, button_height)
    minimax4_button = pygame.Rect(menu_left+(mini_button_width+row_button_gap)*3, row2_y, mini_button_width, button_height)

    cnn_button = pygame.Rect(menu_left, row3_y, menu_button_width, button_height)

    cnnminimax1_button = pygame.Rect(menu_left, row4_y, mini_button_width, button_height)
    cnnminimax2_button = pygame.Rect(menu_left+(mini_button_width+row_button_gap), row4_y, mini_button_width, button_height)
    cnnminimax3_button = pygame.Rect(menu_left+(mini_button_width+row_button_gap)*2, row4_y, mini_button_width, button_height)
    cnnminimax4_button = pygame.Rect(menu_left+(mini_button_width+row_button_gap)*3, row4_y, mini_button_width, button_height)

    while True:
        screen.fill((230, 190, 120))

        title = big_font.render("Choose AI Algorithm", True, (0, 0, 0))
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 80))
        screen.blit(title, title_rect)

        # Each entry pairs a button Rect with its display label and the AI type it selects.
        buttons = [
            [random_button, "Random AI", "random"],
            [greedy_button, "Greedy AI", "greedy"],
            [minimax1_button, "Minimax D1", "minimax1"],
            [minimax2_button, "Minimax D2", "minimax2"],
            [minimax3_button, "Minimax D3", "minimax3"],
            [minimax4_button, "Minimax D4", "minimax4"],
            [cnn_button, "CNN AI", "cnn"],
            [cnnminimax1_button, "CNN+MM D1", "cnnminimax1"],
            [cnnminimax2_button, "CNN+MM D2", "cnnminimax2"],
            [cnnminimax3_button, "CNN+MM D3", "cnnminimax3"],
            [cnnminimax4_button, "CNN+MM D4", "cnnminimax4"]
        ]

        for item in buttons:
            button = item[0]
            label = item[1]

            pygame.draw.rect(screen, (200, 200, 200), button)
            pygame.draw.rect(screen, (0, 0, 0), button, 2)

            text = font.render(label, True, (0, 0, 0))
            text_rect = text.get_rect(center=button.center)

            screen.blit(text, text_rect)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                for item in buttons:
                    button = item[0]
                    ai_type = item[2]

                    if button.collidepoint(mouse_x, mouse_y):
                        return ai_type

# Draw the "Restart" button in the sidebar.
def draw_restart_button(screen, font):
    button_rect = pygame.Rect(
        RESTART_BUTTON_X,
        RESTART_BUTTON_Y,
        RESTART_BUTTON_WIDTH,
        RESTART_BUTTON_HEIGHT
    )

    pygame.draw.rect(screen, (200, 200, 200), button_rect)
    pygame.draw.rect(screen, (0, 0, 0), button_rect, 2)

    text = font.render("Restart", True, (0, 0, 0))
    text_rect = text.get_rect(center=button_rect.center)

    screen.blit(text, text_rect)

# Check whether a mouse click restart button.
def click_restart_button(mouse_x, mouse_y):
    if mouse_x >= RESTART_BUTTON_X and mouse_x <= RESTART_BUTTON_X + RESTART_BUTTON_WIDTH:
        if mouse_y >= RESTART_BUTTON_Y and mouse_y <= RESTART_BUTTON_Y + RESTART_BUTTON_HEIGHT:
            return True

    return False