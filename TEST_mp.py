# This program runs repeated AI vs. AI Gomoku games in parallel to compare two supported AI algorithms.
# The AI types, number of games, and worker process count are provided through command-line arguments.
# To improve fairness, the two AIs alternate moving first between games.

### This version not allow WATCH_PROCESS and not record each game in log.txt ###

import os
import sys
import time
from multiprocessing import Pool
from game import game
import signal

# Enable ANSI escape sequence processing on Windows consoles. (For display colors in consoles)
if os.name == "nt":
    os.system("")

# Load the supported AI algorithm types.
SUPPORTED_AI_TYPES = game.SUPPORTED_ALGORITHMS

# Add and setup colors for console outputs.
class Color:
    RESET = "\033[0m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
def colorize(text, color):
    return color + text + Color.RESET if color else text

# Parse and validate the command-line arguments.
def parse_args():
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print("Usage: python TEST_mp.py AI_TYPE_1 AI_TYPE_2 TEST_TIMES [WORKERS]")
        print("Example: python TEST_mp.py random greedy 100 4")
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

    workers = os.cpu_count() or 1
    if len(sys.argv) == 5:
        try:
            workers = int(sys.argv[4])
        except ValueError:
            print("Error: WORKERS must be an integer.")
            sys.exit(1)

        if workers <= 0:
            print("Error: WORKERS must be greater than 0.")
            sys.exit(1)

    return ai_type_1, ai_type_2, test_times, workers

# Play one game between the two AI algorithms and return the result.
def play_one_game(game_number, ai_type_1, ai_type_2):
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

    # first_is_ai1 tells us which side of the per-move timers (below) the
    # first-moving AI's think time should be added to this game.
    first_is_ai1 = (game_number % 2 == 1)

    move_count = 0
    ai1_think_time = 0.0
    ai1_move_count = 0
    ai2_think_time = 0.0
    ai2_move_count = 0

    while True:
        move_count += 1

        # Let the first-moving AI choose and make a move, timing how long it took to decide.
        move_start = time.perf_counter()
        x, y = game.choose_algorithm_move(first_ai_type, first_player, second_player)
        move_elapsed = time.perf_counter() - move_start
        if first_is_ai1:
            ai1_think_time += move_elapsed
            ai1_move_count += 1
        else:
            ai2_think_time += move_elapsed
            ai2_move_count += 1

        # Check whether the first-moving AI has won.
        if game.check_win(x, y, first_player):
            moves = move_count * 2 - 1
            return (first_result_key, move_count, moves,
                    ai1_think_time, ai1_move_count, ai2_think_time, ai2_move_count)

        # End the game as a draw if the board is full.
        if game.board_full():
            moves = move_count * 2 - 1
            return ("draw", move_count, moves,
                    ai1_think_time, ai1_move_count, ai2_think_time, ai2_move_count)

        # Let the second-moving AI choose and make a move, timing how long it took to decide.
        move_start = time.perf_counter()
        x, y = game.choose_algorithm_move(second_ai_type, second_player, first_player)
        move_elapsed = time.perf_counter() - move_start
        if first_is_ai1:
            ai2_think_time += move_elapsed
            ai2_move_count += 1
        else:
            ai1_think_time += move_elapsed
            ai1_move_count += 1

        # Check whether the second-moving AI has won.
        if game.check_win(x, y, second_player):
            moves = move_count * 2
            return (second_result_key, move_count, moves,
                    ai1_think_time, ai1_move_count, ai2_think_time, ai2_move_count)

        # End the game as a draw if the board is full.
        if game.board_full():
            moves = move_count * 2
            return ("draw", move_count, moves,
                    ai1_think_time, ai1_move_count, ai2_think_time, ai2_move_count)

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
    line = "Progress: [{}] Game {}/{} ({:.1f}%) | Elapsed: {} | ETA: {}".format(
        bar, game_number, test_times, fraction * 100,
        format_duration(elapsed_time), format_duration(eta)
    )
    sys.stdout.write("\r\033[K" + colorize(line, Color.YELLOW))
    sys.stdout.flush()

def run_single_game(game_number, ai_type_1, ai_type_2):
    start_time = time.perf_counter()
    (result, turns, moves,
     ai1_think_time, ai1_move_count, ai2_think_time, ai2_move_count) = play_one_game(
        game_number, ai_type_1, ai_type_2
    )
    elapsed = time.perf_counter() - start_time
    return (result, turns, moves, elapsed,
            ai1_think_time, ai1_move_count, ai2_think_time, ai2_move_count)

def run_single_game_star(args):
    return run_single_game(*args)

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

# Run the AI comparison test and summarize the results.
def main():
    ai_type_1, ai_type_2, test_times, workers = parse_args()

    # Initialize the result and performance statistics.
    ai1_wins = 0
    ai1_losses = 0
    draws = 0
    total_turns = 0
    total_moves = 0
    total_game_time = 0.0
    total_ai1_think_time = 0.0
    total_ai1_move_count = 0
    total_ai2_think_time = 0.0
    total_ai2_move_count = 0
    completed_games = 0

    run_start_time = time.perf_counter()

    game_args = [
        (game_number, ai_type_1, ai_type_2)
        for game_number in range(1, test_times + 1)
    ]

    with Pool(processes=workers, initializer=init_worker) as pool:
        try:
            for (result, turns, moves, elapsed,
                 ai1_think_time, ai1_move_count, ai2_think_time, ai2_move_count) in pool.imap_unordered(
                run_single_game_star, game_args
            ):
                completed_games += 1

                total_turns += turns
                total_moves += moves
                total_game_time += elapsed
                total_ai1_think_time += ai1_think_time
                total_ai1_move_count += ai1_move_count
                total_ai2_think_time += ai2_think_time
                total_ai2_move_count += ai2_move_count

                # Update the win, loss, and draw counts.
                if result == "ai1_win":
                    ai1_wins += 1
                elif result == "ai2_win":
                    ai1_losses += 1
                else:
                    draws += 1

                print_progress(completed_games, test_times, time.perf_counter() - run_start_time)

        except KeyboardInterrupt:
            print("\nCtrl+C interrupt detected")
            pool.terminate()
            pool.join()
            return

    print()

    total_wall_time = time.perf_counter() - run_start_time

    ai2_wins = ai1_losses
    ai2_losses = ai1_wins

    # Build the final test summary.
    summary_lines = []
    summary_lines.append((f"Total games: {test_times}", None))
    summary_lines.append((f"Worker processes: {workers}", None))
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
    summary_lines.append((
        f"AI 1 average think time per move: {total_ai1_think_time / total_ai1_move_count:.4f} seconds", Color.RED))
    summary_lines.append((
        f"AI 2 average think time per move: {total_ai2_think_time / total_ai2_move_count:.4f} seconds", Color.BLUE))
    summary_lines.append((f"Average time per game (CPU time): {total_game_time / test_times:.4f} seconds", None))
    summary_lines.append((f"Total wall-clock time: {total_wall_time:.4f} seconds", None))

    # Display the final summary in the console with colors.
    for line, color in summary_lines:
        print(colorize(line, color))

# Run the main function when this file is executed directly.
if __name__ == "__main__":
    main()
