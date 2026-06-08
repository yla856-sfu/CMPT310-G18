import random

SIZE = 15
EMPTY = "."

PLAYER1 = "X"
PLAYER2 = "O"

board = []

for y in range(SIZE):
    row = []
    for x in range(SIZE):
        row.append(EMPTY)
    board.append(row)

SUPPORTED_ALGORITHMS = ["random", "greedy"]
# Chooses and runs the AI move algorithm based on the selected algorithm type.
def choose_algorithm_move(algorithm_type, player, opponent):
    if algorithm_type == "random":
        return random_algorithm(player)

    if algorithm_type == "greedy":
        return greedy_algorithm(player, opponent)

    raise ValueError("Unsupported algorithm type: " + algorithm_type)

# Checks whether a board position is inside the board and currently empty.
def valid_move(x, y):
    if x < 0 or x >= SIZE:
        return False
    if y < 0 or y >= SIZE:
        return False
    if board[y][x] != EMPTY:
        return False
    return True

# Checks whether there are no empty positions left on the board.
def board_full():
    for y in range(SIZE):
        for x in range(SIZE):
            if board[y][x] == EMPTY:
                return False
    return True

# Places a stone for the given player if the selected position is valid.
def place_stone(x, y, player):
    if valid_move(x, y):
        board[y][x] = player
        return True
    return False

# Finds all legal candidate moves near existing stones within the given radius. 
# Example: For radius = 1, there are 8 positions, for radius = 2, there are 24 positions.
def get_possible_moves(radius):
    possible_moves = []

    for y in range(SIZE):
        for x in range(SIZE):
            if board[y][x] != EMPTY:
                for dy in range(-radius, radius + 1):
                    for dx in range(-radius, radius + 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx = x + dx
                        ny = y + dy
                        if valid_move(nx, ny):
                            if [nx, ny] not in possible_moves:
                                possible_moves.append([nx, ny])
    if len(possible_moves) == 0:
        possible_moves.append([SIZE // 2, SIZE // 2])

    return possible_moves

# Counts continuous stones in one direction and checks how many ends of the line are open.
def count_line(x, y, dx, dy, player):
    count = 1
    open_ends = 0

    nx = x + dx
    ny = y + dy
    while 0 <= nx < SIZE and 0 <= ny < SIZE and board[ny][nx] == player:
        count += 1
        nx += dx
        ny += dy

    if 0 <= nx < SIZE and 0 <= ny < SIZE and board[ny][nx] == EMPTY:
        open_ends += 1

    nx = x - dx
    ny = y - dy
    while 0 <= nx < SIZE and 0 <= ny < SIZE and board[ny][nx] == player:
        count += 1
        nx -= dx
        ny -= dy

    if 0 <= nx < SIZE and 0 <= ny < SIZE and board[ny][nx] == EMPTY:
        open_ends += 1

    return count, open_ends

# Converts a line pattern into a numerical score based on its strength.
def line_score(count, open_ends):
    if count >= 5:
        return 10000000

    if count == 4:
        if open_ends == 2:
            return 1000000      # open four, almost win
        if open_ends == 1:
            return 120000       # blocked four

    if count == 3:
        if open_ends == 2:
            return 50000        # open three
        if open_ends == 1:
            return 8000         # blocked three

    if count == 2:
        if open_ends == 2:
            return 3000         # open two
        if open_ends == 1:
            return 500          # block two

    if count == 1 and open_ends == 2:
        return 30

    return 0

# Temporarily tests a move and calculates how valuable that move is for a player.
def evaluate_move(x, y, player):
    directions = [
        [1, 0],
        [0, 1],
        [1, 1],
        [1, -1]
    ]

    board[y][x] = player

    total_score = 0
    strong_threats = 0

    for direction in directions:
        dx = direction[0]
        dy = direction[1]

        count, open_ends = count_line(x, y, dx, dy, player)
        score = line_score(count, open_ends)
        total_score += score

        # open three or better in more than one direction.
        if score >= 50000:
            strong_threats += 1

    board[y][x] = EMPTY

    if strong_threats >= 2:
        total_score += 200000   # double threat bonus

    # Prefer the center very slightly when scores are close.
    center = SIZE // 2
    distance_from_center = abs(x - center) + abs(y - center)
    total_score += max(0, 20 - distance_from_center)

    return total_score

# Checks whether the given player has made five or more stones in a row from the last move.
def check_win(x, y, player):
    directions = [
        [1, 0],
        [0, 1],
        [1, 1],
        [1, -1]
    ]
    for direction in directions:
        dx = direction[0]
        dy = direction[1]

        count = 1

        nx = x + dx
        ny = y + dy

        while 0 <= nx < SIZE and 0 <= ny < SIZE and board[ny][nx] == player:
            count += 1
            nx += dx
            ny += dy

        nx = x - dx
        ny = y - dy

        while 0 <= nx < SIZE and 0 <= ny < SIZE and board[ny][nx] == player:
            count += 1
            nx -= dx
            ny -= dy

        if count >= 5:
            return True

    return False

def random_algorithm(player):
    possible_moves = get_possible_moves(1)

    move = random.choice(possible_moves)

    x = move[0]
    y = move[1]

    board[y][x] = player

    return x, y

def greedy_algorithm(player, opponent):
    possible_moves = get_possible_moves(2)

    # Win immediately if possible.
    for move in possible_moves:
        x = move[0]
        y = move[1]

        board[y][x] = player
        if check_win(x, y, player):
            return x, y
        board[y][x] = EMPTY

    # Block the opponent's immediate win.
    opponent_winning_moves = []
    for move in possible_moves:
        x = move[0]
        y = move[1]

        board[y][x] = opponent
        if check_win(x, y, opponent):
            opponent_winning_moves.append(move)
        board[y][x] = EMPTY

    if len(opponent_winning_moves) > 0:
        best_move = opponent_winning_moves[0]
        best_score = -1

        for move in opponent_winning_moves:
            x = move[0]
            y = move[1]
            score = evaluate_move(x, y, player)

            if score > best_score:
                best_score = score
                best_move = move

        x = best_move[0]
        y = best_move[1]
        board[y][x] = player
        return x, y

    # Otherwise evaluate attack and defense together.
    best_moves = []
    best_score = -1

    for move in possible_moves:
        x = move[0]
        y = move[1]

        attack_score = evaluate_move(x, y, player)
        defense_score = evaluate_move(x, y, opponent)

        total_score = attack_score + int(defense_score * 1.15)

        if total_score > best_score:
            best_score = total_score
            best_moves = [move]
        elif total_score == best_score:
            best_moves.append(move)

    move = random.choice(best_moves)
    x = move[0]
    y = move[1]

    board[y][x] = player

    return x, y

# Clears the board so a new game can start.
def reset_board():
    for y in range(SIZE):
        for x in range(SIZE):
            board[y][x] = EMPTY