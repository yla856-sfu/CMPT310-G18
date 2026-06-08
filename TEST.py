import os
import sys
import time
import game

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "log.txt")
SUPPORTED_AI_TYPES = game.SUPPORTED_ALGORITHMS

# Check and prompt parameters
def parse_bool(value):
    value = value.lower()
    if value in ["true", "t"]:
        return True
    if value in ["false", "f"]:
        return False
    raise ValueError("WATCH_PROCESS must be true/false or t/n")

# Check and prompt parameters
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

# The string board use to output games in commander line and log.txt
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

# Write to log.txt
def output(text, log_file, watch_process=False):
    log_file.write(text + "\n")
    if watch_process:
        print(text)


def play_one_game(game_number, ai_type_1, ai_type_2, watch_process, interval_seconds, log_file):
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

    # Output info
    output("=" * 70, log_file, watch_process)
    output("Game " + str(game_number), log_file, watch_process)
    output(first_ai_name + ": " + first_ai_type + " = X / black / first", log_file, watch_process)
    output(second_ai_name + ": " + second_ai_type + " = O / white / second", log_file, watch_process)
    output(string_board(), log_file, watch_process)

    move_count = 0

    while True:
        move_count += 1

        # First moves
        x, y = game.choose_algorithm_move(first_ai_type, first_player, second_player)
        output("Turn " + str(move_count) + " - " + first_ai_name + " (" + first_ai_type + ", X) move: " + str(x) + "," + str(y), log_file, watch_process)
        output(string_board(), log_file, watch_process)

        if game.check_win(x, y, first_player):
            moves = move_count * 2 - 1
            output("Result: " + first_ai_name + " won. Total turn number: " + str(move_count), log_file, watch_process)
            return first_result_key, move_count, moves

        if game.board_full():
            moves = move_count * 2 - 1
            output("Result: Draw. Total turn number: " + str(move_count), log_file, watch_process)
            return "draw", move_count, moves

        if watch_process and interval_seconds > 0:
            time.sleep(interval_seconds)

        # Second moves
        x, y = game.choose_algorithm_move(second_ai_type, second_player, first_player)
        output("Turn " + str(move_count) + " - " + second_ai_name + " (" + second_ai_type + ", O) move: " + str(x) + "," + str(y), log_file, watch_process)
        output(string_board(), log_file, watch_process)

        if game.check_win(x, y, second_player):
            moves = move_count * 2
            output("Result: " + second_ai_name + " won. Total turn number: " + str(move_count), log_file, watch_process)
            return second_result_key, move_count, moves

        if game.board_full():
            moves = move_count * 2
            output("Result: Draw. Total turn number: " + str(move_count), log_file, watch_process)
            return "draw", move_count, moves

        if watch_process and interval_seconds > 0:
            time.sleep(interval_seconds)


def percentage(count, total):
    return count * 100.0 / total


def main():
    ai_type_1, ai_type_2, test_times, watch_process, interval_seconds = parse_args()

    ai1_wins = 0
    ai1_losses = 0
    draws = 0
    total_turns = 0
    total_moves = 0
    total_game_time = 0.0

    with open(LOG_FILE, "w", encoding="utf-8") as log_file:
        output("AI vs AI Gomoku Test", log_file, watch_process)
        output("AI 1: " + ai_type_1, log_file, watch_process)
        output("AI 2: " + ai_type_2, log_file, watch_process)
        output("Test times: " + str(test_times), log_file, watch_process)
        output("Watch process: " + str(watch_process), log_file, watch_process)
        output("Interval seconds: " + str(interval_seconds), log_file, watch_process)

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

            if result == "ai1_win":
                ai1_wins += 1
            elif result == "ai2_win":
                ai1_losses += 1
            else:
                draws += 1

        ai2_wins = ai1_losses
        ai2_losses = ai1_wins

        summary_lines = []
        summary_lines.append("Total games: " + str(test_times))
        summary_lines.append("AI 1: " + ai_type_1)
        summary_lines.append("Wins: " + str(ai1_wins) + " (" + format(percentage(ai1_wins, test_times), ".2f") + "%) | Losses: " + str(ai1_losses) + " (" + format(percentage(ai1_losses, test_times), ".2f") + "%) | Draws: " + str(draws) + " (" + format(percentage(draws, test_times), ".2f") + "%)")
        summary_lines.append("AI 2: " + ai_type_2)
        summary_lines.append("Wins: " + str(ai2_wins) + " (" + format(percentage(ai2_wins, test_times), ".2f") + "%) | Losses: " + str(ai2_losses) + " (" + format(percentage(ai2_losses, test_times), ".2f") + "%) | Draws: " + str(draws) + " (" + format(percentage(draws, test_times), ".2f") + "%)")
        summary_lines.append("Average turns: " + format(total_turns / test_times, ".2f"))
        summary_lines.append("Average moves: " + format(total_moves / test_times, ".2f"))
        summary_lines.append("Average time per game: " + format(total_game_time / test_times, ".4f") + " seconds")
        summary_lines.append("Total time: " + format(total_game_time, ".4f") + " seconds")
        summary_lines.append("Process log file: " + LOG_FILE)

        for line in summary_lines:
            log_file.write(line + "\n")

    for line in summary_lines:
        print(line)

if __name__ == "__main__":
    main()
