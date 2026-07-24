# This module implements the greedy AI agent for Gomoku.
# The agent first looks for an immediate winning move, then tries to block the opponent's immediate win. 
# If neither exists, it evaluates all candidate moves and randomly selects one of the highest-scoring positions.
import random

from game.board import board, EMPTY, get_possible_moves, check_win
from game.evaluation import evaluate_move, evaluate_candidate_move

# Return an immediate winning move for the player, or None if no such move exists.
def find_winning_move(player, possible_moves):
    # Temporarily place the stone, check for a win, and restore the board.
    for move in possible_moves:
        x, y = move
        board[y][x] = player
        won = check_win(x, y, player)
        board[y][x] = EMPTY

        if won:
            return move
    return None

# Return the best move for blocking an immediate opponent win, or None if no block is needed.
def find_blocking_move(player, opponent, possible_moves):
    opponent_winning_moves = []

    # Temporarily test whether the opponent can win at each candidate position.
    for move in possible_moves:
        x, y = move

        board[y][x] = opponent
        wins = check_win(x, y, opponent)
        board[y][x] = EMPTY

        # Record every immediate winning move available to the opponent.
        if wins:
            opponent_winning_moves.append(move)

    if not opponent_winning_moves:
        return None

    # Initialize the best blocking move and its score.
    best_move = opponent_winning_moves[0]
    best_score = -1

    # Choose the blocking move with the highest value for the current player.
    for move in opponent_winning_moves:
        x, y = move
        score = evaluate_move(x, y, player)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

# Score every candidate move using its attacking and defensive value,
# then return [score, move] pairs sorted from highest to lowest.
def rank_candidate_moves(player, opponent, possible_moves):
    scored_moves = []

    # Evaluate and record the attacking and defensive value of each move.
    for move in possible_moves:
        x, y = move
        score = evaluate_candidate_move(x, y, player, opponent)
        scored_moves.append([score, move])

    # Sort the candidate moves from highest score to lowest score.
    scored_moves.sort(reverse=True)

    return scored_moves

# Choose and make a move using the greedy agent's priority rules.
def greedy_algorithm(player, opponent):
    # Generate legal candidate moves within radius = 2 from existing stones.
    possible_moves = get_possible_moves(2)

    # Take an immediate winning move whenever one is available.
    move = find_winning_move(player, possible_moves)
    if move is not None:
        x, y = move
        board[y][x] = player
        return x, y

    # Block the opponent's immediate win when no winning move is available.
    move = find_blocking_move(player, opponent, possible_moves)
    if move is not None:
        x, y = move
        board[y][x] = player
        return x, y

    # Rank all remaining candidate moves by their evaluation scores.
    scored_moves = rank_candidate_moves(player, opponent, possible_moves)

    # Get the highest evaluation score.
    best_score = scored_moves[0][0]

    # Collect all moves tied for the highest score.
    best_moves = [item[1] for item in scored_moves if item[0] == best_score]

    # Randomly choose one of the equally best moves. (If there are multiple)
    move = random.choice(best_moves)
    
    x, y = move
    board[y][x] = player
    return x, y
