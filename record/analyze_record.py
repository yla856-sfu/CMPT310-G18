# Parses "AI VS AI record.txt" and ranks each AI by:
# Score = 0.85 * WinScore + 0.15 * SpeedScore
# WinScore = 100 * (wins + 0.5*draws) / games, aggregated across every matchup the AI played.
# SpeedScore normalizes each AI's move-weighted average think time on a log scale against
# the fastest/slowest AI in the whole record, since think times span multiple orders of magnitude.
import math
import re
import sys

RECORD_PATH = "AI VS AI record.txt"

BLOCK_RE = re.compile(r"\d+\.\s+(\S+)\s+vs\s+(\S+)")
GAMES_RE = re.compile(r"Total games:\s*(\d+)")
RESULT_RE = re.compile(r"Wins:\s*(\d+).*?Losses:\s*(\d+).*?Draws:\s*(\d+)")
TURNS_RE = re.compile(r"Average turns:\s*([\d.]+)")
THINK1_RE = re.compile(r"AI 1 average think time per move:\s*([\d.]+)")
THINK2_RE = re.compile(r"AI 2 average think time per move:\s*([\d.]+)")


def parse_matchups(text):
    blocks = re.split(r"^/+$", text, flags=re.MULTILINE)
    matchups = []

    for block in blocks:
        header = BLOCK_RE.search(block)
        games_match = GAMES_RE.search(block)
        if header is None or games_match is None:
            continue

        results = RESULT_RE.findall(block)
        turns_match = TURNS_RE.search(block)
        think1_match = THINK1_RE.search(block)
        think2_match = THINK2_RE.search(block)
        if len(results) != 2 or not (turns_match and think1_match and think2_match):
            continue

        ai1, ai2 = header.group(1), header.group(2)
        games = int(games_match.group(1))
        (w1, l1, d1), (w2, l2, d2) = results

        matchups.append({
            "ai1": ai1, "ai2": ai2, "games": games,
            "ai1_w": int(w1), "ai1_l": int(l1), "ai1_d": int(d1),
            "ai2_w": int(w2), "ai2_l": int(l2), "ai2_d": int(d2),
            "turns": float(turns_match.group(1)),
            "ai1_think": float(think1_match.group(1)),
            "ai2_think": float(think2_match.group(1)),
        })

    return matchups


def aggregate(matchups):
    stats = {}

    def add(name, w, l, d, games, turns, think):
        s = stats.setdefault(name, {"w": 0, "l": 0, "d": 0, "n": 0,
                                     "move_weight": 0.0, "think_weighted": 0.0,
                                     "opponents": 0})
        s["w"] += w
        s["l"] += l
        s["d"] += d
        s["n"] += games
        weight = games * turns
        s["move_weight"] += weight
        s["think_weighted"] += weight * think
        s["opponents"] += 1

    for m in matchups:
        add(m["ai1"], m["ai1_w"], m["ai1_l"], m["ai1_d"], m["games"], m["turns"], m["ai1_think"])
        add(m["ai2"], m["ai2_w"], m["ai2_l"], m["ai2_d"], m["games"], m["turns"], m["ai2_think"])

    for s in stats.values():
        s["think_time"] = s["think_weighted"] / s["move_weight"]
        s["win_score"] = 100 * (s["w"] + 0.5 * s["d"]) / s["n"]

    return stats


def score(stats):
    times = [s["think_time"] for s in stats.values()]
    t_min, t_max = min(times), max(times)
    log_min, log_max = math.log(t_min), math.log(t_max)
    span = log_max - log_min

    for s in stats.values():
        if span == 0:
            s["speed_score"] = 100.0
        else:
            s["speed_score"] = 100 * (log_max - math.log(s["think_time"])) / span
        s["score"] = 0.85 * s["win_score"] + 0.15 * s["speed_score"]

    return t_min, t_max


def main():
    with open(RECORD_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    matchups = parse_matchups(text)
    if not matchups:
        print("No completed matchups found.")
        sys.exit(1)

    stats = aggregate(matchups)
    t_min, t_max = score(stats)

    ranked = sorted(stats.items(), key=lambda item: item[1]["score"], reverse=True)

    print(f"Parsed {len(matchups)} completed matchups covering {len(stats)} AIs.")
    print(f"Think-time range across roster: {t_min:.4f}s (fastest) - {t_max:.4f}s (slowest)\n")

    header = f"{'Rank':<5}{'AI':<14}{'Games':>7}{'W':>6}{'L':>6}{'D':>6}{'WinScore':>10}{'AvgThink':>11}{'SpeedScore':>11}{'Score':>8}"
    print(header)
    print("-" * len(header))

    for rank, (name, s) in enumerate(ranked, start=1):
        print(f"{rank:<5}{name:<14}{s['n']:>7}{s['w']:>6}{s['l']:>6}{s['d']:>6}"
              f"{s['win_score']:>10.2f}{s['think_time']:>11.4f}{s['speed_score']:>11.2f}{s['score']:>8.2f}")


if __name__ == "__main__":
    main()
