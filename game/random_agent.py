# This module implements the random AI agent for Gomoku.
# It randomly selects one of the legal candidate moves near existing stones,
# places the player's stone on the board, and returns the selected coordinates.
# It is used as a baseline agent to ensure the basic implementation of the game.
import random

from game.board import board, get_possible_moves

# Randomly choose and make a legal candidate move for the given player
def random_algorithm(player):
    # Get all legal moves within radius = 1 from existing stones
    possible_moves = get_possible_moves(1)

    # Randomly select one move from the candidate list.
    move = random.choice(possible_moves)

    # Unpack the selected move into x and y coordinates.
    x, y = move

    # Place the player's stone at the selected board position.
    board[y][x] = player

    # Return the coordinates of the completed move.
    return x, y
