# This module implements the Minimax AI agent for Gomoku, using greedy's tactical
# checks for immediate wins/blocks, the CNN policy network's scores to order moves,
# and evaluation's scoring to evaluate leaf positions, with alpha-beta pruning to keep the search fast.
import random

from game.board import board, EMPTY, get_possible_moves, check_win, board_full
from game.evaluation import evaluate_board_static
from game.greedy_agent import find_winning_move, find_blocking_move
from game.cnn_agent import policy_scores, cnn_algorithm

# Evaluate the current board from the player's perspective.
# A positive score means the position favors the player.
# A negative score means the position favors the opponent.
def evaluate_board_for_minimax(player, opponent):
    return evaluate_board_static(player) - evaluate_board_static(opponent)

# Generate candidate moves ordered from most to least promising for current_player using the CNN's
# policy scores instead of greedy's hand-written ranking, then keep only the top max_moves.
# Searching more promising moves first can help alpha-beta pruning cut off more branches.
def get_cnn_ordered_moves(current_player, max_moves):
    scores = policy_scores(current_player)
    candidates = get_possible_moves(2)

    scored_moves = []
    for move in candidates:
        x, y = move
        scored_moves.append((scores.get((x, y), float("-inf")), move))

    scored_moves.sort(key=lambda item: item[0], reverse=True)

    return [item[1] for item in scored_moves[:max_moves]]

# Recursively search possible moves up to the given depth using Minimax with alpha-beta pruning.
# The player to move alternates between maximizing (the player) and minimizing (the opponent).
# alpha is the best score the maximizer can guarantee so far, beta is the best score
# the minimizer can guarantee so far; once beta <= alpha the remaining moves are pruned.
def minimax_search(depth, maximizing, player, opponent, alpha, beta):
    # Stop searching and score the position once the depth limit is reached or the board is full.
    if depth == 0 or board_full():
        return evaluate_board_for_minimax(player, opponent)

    # Limit how many CNN-ordered candidate moves are explored at each node to keep the search fast.
    max_moves = 10

    if maximizing:
        best_score = -1000000000
        possible_moves = get_cnn_ordered_moves(player, max_moves)

        # Try each candidate move for the player and keep the highest resulting score.
        for move in possible_moves:
            x, y = move

            board[y][x] = player

            # Treat an immediate win as the best possible outcome instead of recursing further.
            if check_win(x, y, player):
                score = 100000000
            else:
                score = minimax_search(depth - 1, False, player, opponent, alpha, beta)

            board[y][x] = EMPTY

            if score > best_score:
                best_score = score

            if best_score > alpha:
                alpha = best_score

            # Prune remaining moves once the minimizer would never let this branch be reached.
            if beta <= alpha:
                break

        return best_score

    else:
        best_score = 1000000000
        possible_moves = get_cnn_ordered_moves(opponent, max_moves)

        # Try each candidate move for the opponent and keep the lowest resulting score.
        for move in possible_moves:
            x, y = move

            board[y][x] = opponent

            # Treat an immediate opponent win as the worst possible outcome instead of recursing further.
            if check_win(x, y, opponent):
                score = -100000000
            else:
                score = minimax_search(depth - 1, True, player, opponent, alpha, beta)

            board[y][x] = EMPTY

            if score < best_score:
                best_score = score

            if best_score < beta:
                beta = best_score

            # Prune remaining moves once the maximizer would never let this branch be reached.
            if beta <= alpha:
                break

        return best_score

# Choose and make a move using CNN-ordered Minimax search, while first checking
# for an immediate win or a required block using greedy's tactical helpers.
# Then recursively search a CNN-selected subset of moves up to the given depth, using Minimax with alpha-beta pruning.
def cnn_minimax_algorithm(player, opponent, depth):
    all_possible_moves = get_possible_moves(2)

    # 1. Win immediately if possible (reuses greedy's tactical check).
    move = find_winning_move(player, all_possible_moves)
    if move is not None:
        x, y = move
        board[y][x] = player
        return x, y

    # 2. Block opponent's immediate win (reuses greedy's tactical check).
    move = find_blocking_move(player, opponent, all_possible_moves)
    if move is not None:
        x, y = move
        board[y][x] = player
        return x, y

    # 3. At depth 1 there is no search to do, so just defer to the CNN's own move choice.
    if depth == 1:
        return cnn_algorithm(player, opponent)

    # 4. Otherwise search ahead, using the CNN's policy scores to order candidate moves.
    possible_moves = get_cnn_ordered_moves(player, 40)

    best_moves = []
    best_score = -1000000000

    # Score each candidate move and keep every move tied for the highest score.
    for move in possible_moves:
        x, y = move

        board[y][x] = player

        # Scores are integers. Use best_score - 1 as alpha so branches equal to
        # the current best score are fully checked and can be recorded as ties.
        score = minimax_search(depth - 1, False, player, opponent, best_score - 1, 1000000000)

        board[y][x] = EMPTY

        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)

    # Randomly choose one of the equally best moves. (If there are multiple)
    move = random.choice(best_moves)

    x, y = move

    board[y][x] = player

    return x, y
