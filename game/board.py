# This module stores the Gomoku board state and implements the basic game rules.
# It creates the board, validates and places stones, checks for wins and draws,
# generates candidate moves for AI algorithms, and resets the board for a new game.
SIZE = 15
EMPTY = "."

PLAYER1 = "X"
PLAYER2 = "O"

# Create a two-dimensional board filled with empty positions.
board = []
for y in range(SIZE):
    row = []
    for x in range(SIZE):
        row.append(EMPTY)
    board.append(row)

# Check whether a board position is inside the board and currently empty.
def valid_move(x, y):
    if x < 0 or x >= SIZE:
        return False
    if y < 0 or y >= SIZE:
        return False
    if board[y][x] != EMPTY:
        return False
    return True

# Check whether there are no empty positions left on the board.
def board_full():
    for y in range(SIZE):
        for x in range(SIZE):
            if board[y][x] == EMPTY:
                return False
    return True

# Place a stone for the given player if the selected position is valid.
def place_stone(x, y, player):
    if valid_move(x, y):
        board[y][x] = player
        return True
    return False

# Check whether the last move creates a line of five or more stones for the given player.
def check_win(x, y, player):
    # Check the horizontal, vertical, and two diagonal directions.
    directions = [
        [1, 0],
        [0, 1],
        [1, 1],
        [1, -1]
    ]
    # Examine each possible winning direction
    for direction in directions:
        dx, dy = direction

        # Count the last placed stone as the first stone in the line
        count = 1

        # Count consecutive stones in the positive direction
        nx = x + dx
        ny = y + dy
        while 0 <= nx < SIZE and 0 <= ny < SIZE and board[ny][nx] == player:
            count += 1
            nx += dx
            ny += dy

        # Count consecutive stones in the opposite direction
        nx = x - dx
        ny = y - dy
        while 0 <= nx < SIZE and 0 <= ny < SIZE and board[ny][nx] == player:
            count += 1
            nx -= dx
            ny -= dy

        # Declare a win when five or more connected stones are found
        if count >= 5:
            return True
    return False

# Find all legal candidate moves near existing stones within the given radius.
# Around one isolated stone, radius 1 checks up to 8 surrounding positions,
# while radius 2 checks up to 24 surrounding positions.
# In this project, we use radius = 2 in most algorithms.
def get_possible_moves(radius):
    possible_moves = []
    seen = set()

    # Search around every stone already placed on the board.
    for y in range(SIZE):
        for x in range(SIZE):
            if board[y][x] != EMPTY:
                # Examine all positions within the square search radius.
                for dy in range(-radius, radius + 1):
                    for dx in range(-radius, radius + 1):
                        # Skip the position of the existing stone itself.
                        if dx == 0 and dy == 0:
                            continue
                        # Calculate the coordinates of the nearby position.
                        nx = x + dx
                        ny = y + dy
                        # Add the position only if it is legal and has not been added before.
                        if valid_move(nx, ny) and (nx, ny) not in seen:
                            seen.add((nx, ny)) # Mark this coordinate as already added.
                            possible_moves.append([nx, ny]) # Add the coordinate to the list returned to the AI.
                            
    # Use the center position as the first move when no candidates are found.
    if len(possible_moves) == 0:
        possible_moves.append([SIZE // 2, SIZE // 2])

    return possible_moves

# Clear the board so a new game can start.
def reset_board():
    for y in range(SIZE):
        for x in range(SIZE):
            board[y][x] = EMPTY
