# This module provides a central interface for the Gomoku game system.
# It imports the board rules and supported AI algorithms, lists the available all algorithm types, 
# and calls the appropriate AI algorithm based on the selected type.

# Import the board state, game constants, and rule functions. (For main.py & TEST.py call)
from game.board import (
    SIZE,
    EMPTY,
    PLAYER1,
    PLAYER2,
    board,
    valid_move,
    board_full,
    place_stone,
    check_win,
    get_possible_moves,
    reset_board,
)

# Import all AI move-selection algorithms.
from game.random_agent import random_algorithm
from game.greedy_agent import greedy_algorithm
from game.minimax_agent import minimax_algorithm
from game.cnn_agent import cnn_algorithm
from game.cnn_minimax_agent import cnn_minimax_algorithm

# List the AI algorithm types available to the game and test programs.
SUPPORTED_ALGORITHMS = [
    "random", "greedy",
    "minimax1", "minimax2", "minimax3", "minimax4",
    "cnn",
    "cnnminimax1", "cnnminimax2", "cnnminimax3", "cnnminimax4",
]

# Choose and run the AI move algorithm based on the selected algorithm type.
def choose_algorithm_move(algorithm_type, player, opponent):
    if algorithm_type == "random":
        return random_algorithm(player)

    if algorithm_type == "greedy":
        return greedy_algorithm(player, opponent)

    if algorithm_type == "minimax1":
        return minimax_algorithm(player, opponent, 1)

    if algorithm_type == "minimax2":
        return minimax_algorithm(player, opponent, 2)

    if algorithm_type == "minimax3":
        return minimax_algorithm(player, opponent, 3)

    if algorithm_type == "minimax4":
        return minimax_algorithm(player, opponent, 4)

    if algorithm_type == "cnn":
        return cnn_algorithm(player, opponent)

    if algorithm_type == "cnnminimax1":
        return cnn_minimax_algorithm(player, opponent, 1)

    if algorithm_type == "cnnminimax2":
        return cnn_minimax_algorithm(player, opponent, 2)

    if algorithm_type == "cnnminimax3":
        return cnn_minimax_algorithm(player, opponent, 3)

    if algorithm_type == "cnnminimax4":
        return cnn_minimax_algorithm(player, opponent, 4)

    raise ValueError("Unsupported algorithm type: " + algorithm_type)
