import pygame
import game
import gui

def main():
    pygame.init()
    screen = pygame.display.set_mode((gui.WINDOW_WIDTH, gui.WINDOW_HEIGHT))
    pygame.display.set_caption("Gomoku")
    font = pygame.font.SysFont(None, 26)
    big_font = pygame.font.SysFont(None, 40)
    clock = pygame.time.Clock()

    # Players first choose the type of AI they want to play against, and then the game begins.
    ai_type = gui.choose_ai(screen, font, big_font)

    message = "Your turn: Click on the intersection of the board to place a piece."
    turn_count = 1
    game_over = False

    running = True

    while running:
        gui.draw_board(screen, font)
        gui.draw_info(screen, font, big_font, message, turn_count, ai_type)

        # when game over show restart button
        if game_over:
            gui.draw_restart_button(screen, font)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                if game_over:
                    if gui.click_restart_button(mouse_x, mouse_y):
                        game.reset_board()
                        message = "Your turn: Click on the intersection of the board to place a piece."
                        turn_count = 1
                        game_over = False
                    continue                
                
                x, y = gui.screen_to_board(mouse_x, mouse_y)

                if x is None:
                    message = "Please click near the intersection of the board."
                    continue

                if game.valid_move(x, y) == False:
                    message = "This position is unsuitable."
                    continue

                game.place_stone(x, y, game.PLAYER1)
                message = "Your move:" + str(x) + "," + str(y)

                if game.check_win(x, y, game.PLAYER1):
                    message = "You Won! Final round number:" + str(turn_count)
                    game_over = True
                    continue

                if game.board_full():
                    message = "Draw!"
                    game_over = True
                    continue

                ai_x, ai_y = game.choose_algorithm_move(ai_type, game.PLAYER2, game.PLAYER1)

                message = "Your move:" + str(x) + "," + str(y) + "\nAI move:" + str(ai_x) + "," + str(ai_y)

                if game.check_win(ai_x, ai_y, game.AI):
                    message = "AI Won! Final round number:" + str(turn_count)
                    game_over = True
                    continue

                if game.board_full():
                    message = "Draw!"
                    game_over = True
                    continue
                turn_count += 1

            if event.type == pygame.KEYDOWN and game_over == False:
                # Press \ to skip player turn, test only.
                if event.key == pygame.K_BACKSLASH:
                    ai_x, ai_y = game.choose_algorithm_move(ai_type, game.PLAYER2, game.PLAYER1)

                    message = "You skipped this turn; AI move:" + str(ai_x) + "," + str(ai_y)

                    if game.check_win(ai_x, ai_y, game.AI):
                        message = "AI Won! Final round number:" + str(turn_count)
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