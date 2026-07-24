# Start and control a Human vs. AI Gomoku game using the GUI and game modules.
# Handle player input, AI moves, win and draw checks, and game restarts.
# The '\' key is provided as a test feature that lets the player skip the current turn and observe the AI's next action.
import pygame
from game import game
from gui import gui

# Initialize and run the Human vs. AI Gomoku game.
def main():
    pygame.init()
    screen = pygame.display.set_mode((gui.WINDOW_WIDTH, gui.WINDOW_HEIGHT))
    pygame.display.set_caption("Gomoku")
    font = pygame.font.SysFont("segoeui,arial,sans", 22)
    big_font = pygame.font.SysFont("segoeui,arial,sans", 36)
    clock = pygame.time.Clock()

    # Let the player choose an AI type before starting the game.
    ai_type = gui.choose_ai(screen, font, big_font)

    # Initialize the displayed message and game state
    message = "Your turn: \nClick on the intersection of the board to place a piece."
    turn_count = 1
    game_over = False
    running = True

    # Run the main game loop until the window is closed.
    while running:
        gui.draw_board(screen, font)
        gui.draw_info(screen, font, big_font, message, turn_count, ai_type)

        # Show the restart button when the game is over.
        if game_over:
            gui.draw_restart_button(screen, font)

        pygame.display.update()

        # Process window, mouse, and keyboard events.
        for event in pygame.event.get():
            # Stop the main loop when the player closes the window.
            if event.type == pygame.QUIT:
                running = False

            # Get the mouse position when the player clicks.
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                # Restart the game if the restart button is clicked.
                if game_over:
                    if gui.click_restart_button(mouse_x, mouse_y):
                        game.reset_board()
                        message = "Your turn: Click on the intersection of the board to place a piece."
                        turn_count = 1
                        game_over = False
                    continue                
                
                # Convert the mouse position to board coordinates
                x, y = gui.screen_to_board(mouse_x, mouse_y)

                if x is None:
                    message = "Please click near the intersection of the board."
                    continue

                if not game.valid_move(x, y):
                    message = "This position is unavailable."
                    continue

                game.place_stone(x, y, game.PLAYER1)
                message = f"Your move:{x},{y}"

                # Check whether the player's move wins the game
                if game.check_win(x, y, game.PLAYER1):
                    message = f"You Won! Final round number:{turn_count}"
                    game_over = True
                    continue
                
                # Declare a draw if the board is full after the player's move
                if game.board_full():
                    message = "Draw!"
                    game_over = True
                    continue
                
                # Let the selected AI algorithm choose and make its move
                ai_x, ai_y = game.choose_algorithm_move(ai_type, game.PLAYER2, game.PLAYER1)

                message = f"Your move:{x},{y}\nAI move:{ai_x},{ai_y}"

                # Check whether the AI's move wins the game
                if game.check_win(ai_x, ai_y, game.PLAYER2):
                    message = f"AI Won! Final round number:{turn_count}"
                    game_over = True
                    continue
                
                # Declare a draw if the board is full after the AI's move
                if game.board_full():
                    message = "Draw!"
                    game_over = True
                    continue
                turn_count += 1

            # Test key
            elif event.type == pygame.KEYDOWN and not game_over:
                # Press \ to skip player turn, test only.
                if event.key == pygame.K_BACKSLASH:
                    ai_x, ai_y = game.choose_algorithm_move(ai_type, game.PLAYER2, game.PLAYER1)

                    message = f"You skipped this turn; AI move:{ai_x},{ai_y}"

                    if game.check_win(ai_x, ai_y, game.PLAYER2):
                        message = f"AI Won! Final round number:{turn_count}"
                        game_over = True
                        continue

                    if game.board_full():
                        message = "Draw!"
                        game_over = True
                        continue

                    turn_count += 1
                    continue
                
        clock.tick(60)
    pygame.quit()
main()