# This program runs repeated AI vs. AI Gomoku games to compare two supported AI algorithms.
# The AI types, number of games, process display option, and move interval are provided through command-line arguments.
# To improve fairness, the two AIs alternate moving first between games.
# The program records each game in log.txt, displays the testing progress,
# and summarizes the win, loss, and draw rates, average turns, average moves, and execution time.
import os
import sys
import time
from game import game

# Enable ANSI escape sequence processing on Windows consoles. (For display colors in consoles)
if os.name == "nt":
    os.system("")

# Set the log file path and load the supported AI algorithm types.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "log.txt")
SUPPORTED_AI_TYPES = game.SUPPORTED_ALGORITHMS

# Add and setup colors for console outputs.
class Color:
    RESET = "\033[0m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
def colorize(text, color):
    return color + text + Color.RESET if color else text
def ai_color(ai_name):
    return Color.RED if ai_name == "AI 1" else Color.BLUE

# Convert a command-line string to a Boolean value.
def parse_bool(value):
    value = value.lower()
    if value in ["true", "t"]:
        return True
    if value in ["false", "f"]:
        return False
    raise ValueError("WATCH_PROCESS must be true/false or t/f")

# Parse and validate the command-line arguments.
def parse_args():
    if len(sys.argv) < 5 or len(sys.argv) > 6:
        print("Usage: python TEST.py AI_TYPE_1 AI_TYPE_2 TEST_TIMES WATCH_PROCESS [INTERVAL_SECONDS]")
        print("Example: python TEST.py random greedy 100 false")
        sys.exit(1)

    ai_type_1 = sys.argv[1].lower()
    ai_type_2 = sys.argv[2].lower()

    if ai_type_1 not in SUPPORTED_AI_TYPES:
        print("Error: AI_TYPE_1 must be one of:", ", ".join(SUPPORTED_AI_TYPES))
        sys.exit(1)

    if ai_type_2 not in SUPPORTED_AI_TYPES:
        print("Error: AI_TYPE_2 must be one of:", ", ".join(SUPPORTED_AI_TYPES))
        sys.exit(1)

    try:
        test_times = int(sys.argv[3])
    except ValueError:
        print("Error: TEST_TIMES must be an integer.")
        sys.exit(1)

    if test_times <= 0:
        print("Error: TEST_TIMES must be greater than 0.")
        sys.exit(1)

    try:
        watch_process = parse_bool(sys.argv[4])
    except ValueError as error:
        print("Error:", error)
        sys.exit(1)

    interval_seconds = 0.0
    if len(sys.argv) == 6:
        try:
            interval_seconds = float(sys.argv[5])
        except ValueError:
            print("Error: INTERVAL_SECONDS must be a number.")
            sys.exit(1)

        if interval_seconds < 0:
            print("Error: INTERVAL_SECONDS cannot be negative.")
            sys.exit(1)

    return ai_type_1, ai_type_2, test_times, watch_process, interval_seconds

# Convert the board to a string for command-line output and log.txt.
def string_board():
    lines = []
    lines.append("")

    for y in range(game.SIZE - 1, -1, -1):
        line = str(y).rjust(2) + " "
        for x in range(game.SIZE):
            line += str(game.board[y][x]).rjust(2) + " "
        lines.append(line)

    bottom = "   "
    for x in range(game.SIZE):
        bottom += str(x).rjust(2) + " "
    lines.append(bottom)
    lines.append("")

    return "\n".join(lines)

# Write to log.txt.
def output(text, log_file, watch_process=False, color=None):
    log_file.write(text + "\n")
    if watch_process:
        print(colorize(text, color))

# Play one game between the two AI algorithms and return the result.
def play_one_game(game_number, ai_type_1, ai_type_2, watch_process, interval_seconds, log_file):
    # Reset the board before starting a new game
    game.reset_board()

    # In odd-numbered games, Player 1 goes first; in even-numbered games, Player 2 goes first. 
    # Switching first moves ensures fairness.
    if game_number % 2 == 1:
        first_ai_name = "AI 1"
        first_ai_type = ai_type_1
        first_result_key = "ai1_win"
        second_ai_name = "AI 2"
        second_ai_type = ai_type_2
        second_result_key = "ai2_win"
    else:
        first_ai_name = "AI 2"
        first_ai_type = ai_type_2
        first_result_key = "ai2_win"
        second_ai_name = "AI 1"
        second_ai_type = ai_type_1
        second_result_key = "ai1_win"

    first_player = game.PLAYER1
    second_player = game.PLAYER2

    # Output the game information and board.
    output("=" * 70, log_file, watch_process)
    output(f"Game {game_number}", log_file, watch_process)
    output(f"{first_ai_name}: {first_ai_type} = X / black / first", log_file, watch_process, color=ai_color(first_ai_name))
    output(f"{second_ai_name}: {second_ai_type} = O / white / second", log_file, watch_process, color=ai_color(second_ai_name))
    output(string_board(), log_file, watch_process)

    move_count = 0

    while True:
        move_count += 1

        # Let the first-moving AI choose and make a move.
        x, y = game.choose_algorithm_move(first_ai_type, first_player, second_player)
        output(f"Turn {move_count} - {first_ai_name} ({first_ai_type}, X) move: {x},{y}", log_file, watch_process, color=ai_color(first_ai_name))
        output(string_board(), log_file, watch_process)

        # Check whether the first-moving AI has won.
        if game.check_win(x, y, first_player):
            moves = move_count * 2 - 1
            output(f"Result: {first_ai_name} won. Total turn number: {move_count}", log_file, watch_process, color=ai_color(first_ai_name))
            return first_result_key, move_count, moves

        # End the game as a draw if the board is full.
        if game.board_full():
            moves = move_count * 2 - 1
            output(f"Result: Draw. Total turn number: {move_count}", log_file, watch_process)
            return "draw", move_count, moves

        # Pause between moves when displaying the game process.
        if watch_process and interval_seconds > 0:
            time.sleep(interval_seconds)

        # Let the second-moving AI choose and make a move.
        x, y = game.choose_algorithm_move(second_ai_type, second_player, first_player)
        output(f"Turn {move_count} - {second_ai_name} ({second_ai_type}, O) move: {x},{y}", log_file, watch_process, color=ai_color(second_ai_name))
        output(string_board(), log_file, watch_process)

        # Check whether the second-moving AI has won.
        if game.check_win(x, y, second_player):
            moves = move_count * 2
            output(f"Result: {second_ai_name} won. Total turn number: {move_count}", log_file, watch_process, color=ai_color(second_ai_name))
            return second_result_key, move_count, moves

        # End the game as a draw if the board is full.
        if game.board_full():
            moves = move_count * 2
            output(f"Result: Draw. Total turn number: {move_count}", log_file, watch_process)
            return "draw", move_count, moves

        # Pause between moves when displaying the game process.
        if watch_process and interval_seconds > 0:
            time.sleep(interval_seconds)

# Calculate the percentage of a count out of the total.
def percentage(count, total):
    return count * 100.0 / total

# Convert a duration in seconds to HH:MM:SS format.
def format_duration(seconds):
    seconds = int(seconds)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)

# Display the test progress, elapsed time, and estimated remaining time. (User-friendly)
def print_progress(game_number, test_times, elapsed_time, bar_length=30):
    fraction = game_number / test_times
    filled = int(bar_length * fraction)
    bar = "#" * filled + "-" * (bar_length - filled)
    avg_time = elapsed_time / game_number
    eta = avg_time * (test_times - game_number)
    line = "\rProgress: [{}] Game {}/{} ({:.1f}%) | Elapsed: {} | ETA: {}".format(
        bar, game_number, test_times, fraction * 100,
        format_duration(elapsed_time), format_duration(eta)
    )
    sys.stdout.write(colorize(line.ljust(100), Color.YELLOW))
    sys.stdout.flush()

# Run the AI comparison test and summarize the results.
def main():
    ai_type_1, ai_type_2, test_times, watch_process, interval_seconds = parse_args()

    # Initialize the result and performance statistics.
    ai1_wins = 0
    ai1_losses = 0
    draws = 0
    total_turns = 0
    total_moves = 0
    total_game_time = 0.0

    # Create the log file and record the test configuration.
    with open(LOG_FILE, "w", encoding="utf-8") as log_file:
        output("AI vs AI Gomoku Test", log_file, watch_process)
        output(f"AI 1: {ai_type_1}", log_file, watch_process, color=Color.RED)
        output(f"AI 2: {ai_type_2}", log_file, watch_process, color=Color.BLUE)
        output(f"Test times: {test_times}", log_file, watch_process)
        output(f"Watch process: {watch_process}", log_file, watch_process)
        output(f"Interval seconds: {interval_seconds}", log_file, watch_process)

        run_start_time = time.perf_counter()
        # Run the requested number of games and collect each result.
        for game_number in range(1, test_times + 1):
            game_start_time = time.perf_counter()
            result, turns, moves = play_one_game(
                game_number,
                ai_type_1,
                ai_type_2,
                watch_process,
                interval_seconds,
                log_file
            )
            game_end_time = time.perf_counter()
            total_turns += turns
            total_moves += moves
            total_game_time += game_end_time - game_start_time

            # Update the win, loss, and draw counts.
            if result == "ai1_win":
                ai1_wins += 1
            elif result == "ai2_win":
                ai1_losses += 1
            else:
                draws += 1

            print_progress(game_number, test_times, time.perf_counter() - run_start_time)

        print()

        ai2_wins = ai1_losses
        ai2_losses = ai1_wins

        # Build the final test summary.
        summary_lines = []
        summary_lines.append((f"Total games: {test_times}", None))
        summary_lines.append((f"AI 1: {ai_type_1}", Color.RED))
        summary_lines.append((
            f"Wins: {ai1_wins} ({percentage(ai1_wins, test_times):.2f}%) | "
            f"Losses: {ai1_losses} ({percentage(ai1_losses, test_times):.2f}%) | "
            f"Draws: {draws} ({percentage(draws, test_times):.2f}%)", Color.RED))
        summary_lines.append((f"AI 2: {ai_type_2}", Color.BLUE))
        summary_lines.append((
            f"Wins: {ai2_wins} ({percentage(ai2_wins, test_times):.2f}%) | "
            f"Losses: {ai2_losses} ({percentage(ai2_losses, test_times):.2f}%) | "
            f"Draws: {draws} ({percentage(draws, test_times):.2f}%)", Color.BLUE))
        summary_lines.append((f"Average turns: {total_turns / test_times:.2f}", None))
        summary_lines.append((f"Average moves: {total_moves / test_times:.2f}", None))
        summary_lines.append((f"Average time per game: {total_game_time / test_times:.4f} seconds", None))
        summary_lines.append((f"Total time: {total_game_time:.4f} seconds", None))
        summary_lines.append((f"Process log file: {LOG_FILE}", None))

        # Write the final summary to the log file. (Without color codes)
        for line, _ in summary_lines:
            log_file.write(line + "\n")

    # Display the final summary in the console with colors.
    for line, color in summary_lines:
        print(colorize(line, color))

# Run the main function when this file is executed directly.
if __name__ == "__main__":
    main()
