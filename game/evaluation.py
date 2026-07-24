# This module evaluates Gomoku moves and board positions for AI algorithms.
# It scores connected stone patterns based on their length and open ends,
# evaluates the attacking and defensive value of candidate moves, 
# and provides a static board evaluation for Minimax search.
from game.board import board, SIZE, EMPTY

# Count consecutive stones in both directions and determine how many ends are open.
def count_line(x, y, dx, dy, player):
    count = 1
    open_ends = 0

    # Count consecutive stones in the positive direction.
    nx = x + dx
    ny = y + dy
    while 0 <= nx < SIZE and 0 <= ny < SIZE and board[ny][nx] == player:
        count += 1
        nx += dx
        ny += dy
    # Count the positive end as open if the next position is empty
    if 0 <= nx < SIZE and 0 <= ny < SIZE and board[ny][nx] == EMPTY:
        open_ends += 1

    # Count consecutive stones in the opposite direction
    nx = x - dx
    ny = y - dy
    while 0 <= nx < SIZE and 0 <= ny < SIZE and board[ny][nx] == player:
        count += 1
        nx -= dx
        ny -= dy
    # Count the opposite end as open if the next position is empty
    if 0 <= nx < SIZE and 0 <= ny < SIZE and board[ny][nx] == EMPTY:
        open_ends += 1

    return count, open_ends

# Convert a line pattern into a numerical score based on its strength.
def line_score(count, open_ends):
    # Give a very high heuristic score to a winning line.
    if count >= 5:
        return 2000000
    
    if count == 4:
        if open_ends == 2:
            return 1000000      # open four, almost win
        if open_ends == 1:
            return 120000       # single-ended four

    if count == 3:
        if open_ends == 2:
            return 50000        # open three
        if open_ends == 1:
            return 8000         # single-ended three

    if count == 2:
        if open_ends == 2:
            return 3000         # open two
        if open_ends == 1:
            return 500          # single-ended two

    # Give a small score to a single stone with two open ends
    if count == 1 and open_ends == 2:
        return 30
    
    return 0

# Temporarily tests a move and calculates how valuable that move is for a player.
def evaluate_move(x, y, player):
    # Evaluate the horizontal, vertical, and two diagonal directions.
    directions = [
        [1, 0],
        [0, 1],
        [1, 1],
        [1, -1]
    ]

    # Temporarily place the player's stone on the candidate position.
    board[y][x] = player

    total_score = 0
    strong_threats = 0

    # Score the line created by the move in each direction.
    for direction in directions:
        dx, dy = direction

        count, open_ends = count_line(x, y, dx, dy, player)
        score = line_score(count, open_ends)
        total_score += score

        # Count each direction containing an open three or a stronger pattern.
        if score >= 50000:
            strong_threats += 1

    # Remove the temporary stone and restore the board.
    board[y][x] = EMPTY

    if strong_threats >= 2:
        total_score += 200000   # Double threat bonus

    # Add a small center preference to break ties between similar moves.
    center = SIZE // 2
    distance_from_center = abs(x - center) + abs(y - center)
    total_score += max(0, 20 - distance_from_center)

    return total_score

# Evaluate a candidate move by combining its attacking and defensive value.
def evaluate_candidate_move(x, y, player, opponent):
    attack_score = evaluate_move(x, y, player) 
    defense_score = evaluate_move(x, y, opponent)
    # Combine both scores.
    total_score = attack_score + int(defense_score * 1.15) # Strengthened defense.
    return total_score

# Evaluate the current board by scoring every existing line for the given player.
# Unlike evaluate_move(), this function does not simulate an additional move,
# making it suitable for evaluating Minimax leaf positions.
def evaluate_board_static(player):
    directions = [
        [1, 0],
        [0, 1],
        [1, 1],
        [1, -1]
    ]
    total_score = 0

    # Examine every stone belonging to the given player.
    for y in range(SIZE):
        for x in range(SIZE):
            if board[y][x] != player:
                continue
            
            for direction in directions:
                dx, dy = direction

                # Skip this stone if the same line has already started at an earlier position.
                px = x - dx
                py = y - dy
                if 0 <= px < SIZE and 0 <= py < SIZE and board[py][px] == player:
                    continue

                count = 1
                open_ends = 0

                # Check whether the position before the run is open.
                if 0 <= px < SIZE and 0 <= py < SIZE and board[py][px] == EMPTY:
                    open_ends += 1

                # Count all consecutive stones in the current direction.
                nx = x + dx
                ny = y + dy
                while 0 <= nx < SIZE and 0 <= ny < SIZE and board[ny][nx] == player:
                    count += 1
                    nx += dx
                    ny += dy

                # Check whether the position after the run is open.
                if 0 <= nx < SIZE and 0 <= ny < SIZE and board[ny][nx] == EMPTY:
                    open_ends += 1

                total_score += line_score(count, open_ends)
    return total_score
