#!/usr/bin/env python3
# Visualize Gomoku CNN experiments recorded in train_cnn.py console logs.

# Examples: python plot_gomoku_training.py "AI VS AI record.txt"

# The script only needs matplotlib. It does not load PyTorch .pt checkpoints,
# because a checkpoint contains model weights, not the historical per-epoch loss.

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter


EPOCH_PATTERN = re.compile(
    r"Epoch\s+(?P<epoch>\d+)/(?P<total>\d+)\s*\|\s*"
    r"lr=(?P<lr>[-+0-9.eE]+)\s*\|\s*"
    r"train loss=(?P<train_loss>[-+0-9.eE]+)\s*\|\s*"
    r"train top1=(?P<train_top1>[-+0-9.eE]+)\s*\|\s*"
    r"val loss=(?P<val_loss>[-+0-9.eE]+)\s*\|\s*"
    r"top1=(?P<val_top1>[-+0-9.eE]+)\s*\|\s*"
    r"top3=(?P<val_top3>[-+0-9.eE]+)\s*\|\s*"
    r"top5=(?P<val_top5>[-+0-9.eE]+)\s*\|\s*"
    r"top10=(?P<val_top10>[-+0-9.eE]+)"
)

TEST_PATTERN = re.compile(
    r"Final test loss=(?P<loss>[-+0-9.eE]+)\s*\|\s*"
    r"top1=(?P<top1>[-+0-9.eE]+)\s*\|\s*"
    r"top3=(?P<top3>[-+0-9.eE]+)\s*\|\s*"
    r"top5=(?P<top5>[-+0-9.eE]+)\s*\|\s*"
    r"top10=(?P<top10>[-+0-9.eE]+)"
)

BATTLE_PATTERN = re.compile(
    r"AI 1:\s*cnn[\s\S]*?"
    r"Wins:\s*\d+\s*\((?P<win>[0-9.]+)%\)\s*\|\s*"
    r"Losses:\s*\d+\s*\((?P<loss>[0-9.]+)%\)\s*\|\s*"
    r"Draws:\s*\d+\s*\((?P<draw>[0-9.]+)%\)"
)


@dataclass
class Run:
    model: str
    epoch: list[int] = field(default_factory=list)
    learning_rate: list[float] = field(default_factory=list)
    train_loss: list[float] = field(default_factory=list)
    train_top1: list[float] = field(default_factory=list)
    val_loss: list[float] = field(default_factory=list)
    val_top1: list[float] = field(default_factory=list)
    val_top3: list[float] = field(default_factory=list)
    val_top5: list[float] = field(default_factory=list)
    val_top10: list[float] = field(default_factory=list)
    best_val_top1: float = float("nan")
    test_loss: float = float("nan")
    test_top1: float = float("nan")
    test_top3: float = float("nan")
    test_top5: float = float("nan")
    test_top10: float = float("nan")
    battle_win: float = float("nan")
    battle_loss: float = float("nan")
    battle_draw: float = float("nan")
    average_turns: float = float("nan")
    seconds_per_game: float = float("nan")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create matplotlib figures from train_cnn.py console logs."
    )
    parser.add_argument(
        "record",
        type=Path,
        nargs="?",
        default=Path("cnn Model record.txt"),
        help="Path to the training log file (default: cnn Model record.txt)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("figures"),
        help="Directory for PNG and CSV outputs (default: figures)",
    )
    parser.add_argument(
        "--model",
        help=(
            "Only draw one named model, for example gomoku_cnn_epoch_40. "
            "Comparison figures still use all parsed models."
        ),
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="PNG resolution (default: 300)",
    )
    return parser.parse_args()


def first_float(text: str, pattern: str) -> float:
    match = re.search(pattern, text)
    return float(match.group(1)) if match else float("nan")


def parse_segment(segment: str) -> Run | None:
    model_match = re.search(r"--model-out\s+[\"']?([^\s\"']+)", segment)
    if not model_match:
        return None

    run = Run(model=model_match.group(1))
    for match in EPOCH_PATTERN.finditer(segment):
        values = match.groupdict()
        run.epoch.append(int(values["epoch"]))
        run.learning_rate.append(float(values["lr"]))
        run.train_loss.append(float(values["train_loss"]))
        run.train_top1.append(float(values["train_top1"]))
        run.val_loss.append(float(values["val_loss"]))
        run.val_top1.append(float(values["val_top1"]))
        run.val_top3.append(float(values["val_top3"]))
        run.val_top5.append(float(values["val_top5"]))
        run.val_top10.append(float(values["val_top10"]))

    if not run.epoch:
        return None

    run.best_val_top1 = first_float(
        segment, r"Best validation Top-1 accuracy:\s*([-+0-9.eE]+)"
    )

    test_match = TEST_PATTERN.search(segment)
    if test_match:
        values = test_match.groupdict()
        run.test_loss = float(values["loss"])
        run.test_top1 = float(values["top1"])
        run.test_top3 = float(values["top3"])
        run.test_top5 = float(values["top5"])
        run.test_top10 = float(values["top10"])

    battle_match = BATTLE_PATTERN.search(segment)
    if battle_match:
        values = battle_match.groupdict()
        run.battle_win = float(values["win"]) / 100
        run.battle_loss = float(values["loss"]) / 100
        run.battle_draw = float(values["draw"]) / 100

    run.average_turns = first_float(
        segment, r"Average turns:\s*([-+0-9.eE]+)"
    )
    run.seconds_per_game = first_float(
        segment, r"Average time per game:\s*([-+0-9.eE]+)\s*seconds"
    )
    return run


def parse_record(path: Path) -> list[Run]:
    text = path.read_text(encoding="utf-8", errors="replace")
    starts = [
        match.start()
        for match in re.finditer(
            r"^.*python\s+train_cnn\.py.*--model-out.*$", text, re.MULTILINE
        )
    ]
    if not starts:
        raise ValueError(
            "No experiment commands containing 'python train_cnn.py' "
            "and '--model-out' were found."
        )

    runs: list[Run] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(text)
        run = parse_segment(text[start:end])
        if run is not None:
            runs.append(run)

    if not runs:
        raise ValueError("Commands were found, but no epoch metrics were parsed.")
    return runs


def friendly_name(model: str) -> str:
    name = model.removeprefix("gomoku_cnn_")
    replacements = (
        ("default", "default\n(20 epochs)"),
        ("epoch_", "epochs="),
        ("batch_", "batch="),
        ("channel_", "channels="),
        ("block_", "blocks="),
        ("lr_", "lr="),
    )
    for old, new in replacements:
        name = name.replace(old, new)
    return name


def safe_name(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", model)


def apply_plot_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "#fbfbfb",
            "axes.grid": True,
            "grid.alpha": 0.25,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 11,
            "axes.titleweight": "bold",
        }
    )


def plot_training_curve(run: Run, output_dir: Path, dpi: int) -> Path:
    epochs = np.asarray(run.epoch)
    train_top1 = np.asarray(run.train_top1)
    val_top1 = np.asarray(run.val_top1)

    figure, axes = plt.subplots(1, 2, figsize=(15, 5.8))

    axes[0].plot(
        epochs, train_top1, marker="o", markersize=3.5,
        linewidth=2, label="Train Accuracy"
    )
    axes[0].plot(
        epochs, val_top1, marker="s", markersize=3.5,
        linewidth=2, label="Validation Accuracy"
    )
    axes[0].set_title("Model Accuracy")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Top-1 Accuracy")
    axes[0].yaxis.set_major_formatter(PercentFormatter(xmax=1))
    axes[0].set_xlim(epochs.min(), epochs.max())
    lower = max(0, min(train_top1.min(), val_top1.min()) - 0.05)
    upper = min(1, max(train_top1.max(), val_top1.max()) + 0.05)
    axes[0].set_ylim(lower, upper)
    axes[0].legend(loc="lower right")

    axes[1].plot(
        epochs, run.train_loss, marker="o", markersize=3.5,
        linewidth=2, label="Train Loss"
    )
    axes[1].plot(
        epochs, run.val_loss, marker="s", markersize=3.5,
        linewidth=2, label="Validation Loss"
    )
    axes[1].set_title("Model Loss")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Cross-Entropy Loss")
    axes[1].set_xlim(epochs.min(), epochs.max())
    axes[1].legend(loc="upper right")

    figure.suptitle(run.model, fontsize=14, fontweight="bold")
    figure.tight_layout()
    output_path = output_dir / f"training_curve_{safe_name(run.model)}.png"
    figure.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(figure)
    return output_path


def plot_model_comparison(
    runs: list[Run], output_dir: Path, dpi: int
) -> Path:
    labels = [friendly_name(run.model) for run in runs]
    x = np.arange(len(runs))
    width = 0.25

    figure, axes = plt.subplots(2, 1, figsize=(16, 9))
    axes[0].bar(
        x - width, [run.best_val_top1 for run in runs], width,
        label="Best Validation Top-1"
    )
    axes[0].bar(
        x, [run.test_top1 for run in runs], width, label="Test Top-1"
    )
    axes[0].bar(
        x + width, [run.battle_win for run in runs], width,
        label="CNN Win Rate vs Greedy"
    )
    axes[0].set_title("Saved Model Performance")
    axes[0].set_ylabel("Rate")
    axes[0].set_ylim(0, 1)
    axes[0].yaxis.set_major_formatter(PercentFormatter(xmax=1))
    axes[0].set_xticks(x, labels, rotation=25, ha="right")
    axes[0].legend(ncols=3, loc="upper center")

    wins = np.asarray([run.battle_win for run in runs])
    losses = np.asarray([run.battle_loss for run in runs])
    draws = np.asarray([run.battle_draw for run in runs])
    axes[1].bar(x, wins, label="Win")
    axes[1].bar(x, losses, bottom=wins, label="Loss")
    axes[1].bar(x, draws, bottom=wins + losses, label="Draw")
    axes[1].set_title("CNN vs Greedy (CNN Recorded as AI 1)")
    axes[1].set_ylabel("Game Outcome")
    axes[1].set_ylim(0, 1)
    axes[1].yaxis.set_major_formatter(PercentFormatter(xmax=1))
    axes[1].set_xticks(x, labels, rotation=25, ha="right")
    axes[1].legend(ncols=3, loc="upper center")

    figure.tight_layout()
    output_path = output_dir / "model_comparison.png"
    figure.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(figure)
    return output_path


def plot_topk_comparison(
    runs: list[Run], output_dir: Path, dpi: int
) -> Path:
    labels = [friendly_name(run.model) for run in runs]
    x = np.arange(len(runs))
    width = 0.2
    series = (
        ("Top-1", [run.test_top1 for run in runs]),
        ("Top-3", [run.test_top3 for run in runs]),
        ("Top-5", [run.test_top5 for run in runs]),
        ("Top-10", [run.test_top10 for run in runs]),
    )

    figure, axis = plt.subplots(figsize=(16, 6.5))
    offsets = (-1.5, -0.5, 0.5, 1.5)
    for offset, (label, values) in zip(offsets, series):
        axis.bar(x + offset * width, values, width, label=label)
    axis.set_title("Final Test Top-k Accuracy")
    axis.set_xlabel("Model")
    axis.set_ylabel("Test Accuracy")
    axis.set_ylim(0, 1)
    axis.yaxis.set_major_formatter(PercentFormatter(xmax=1))
    axis.set_xticks(x, labels, rotation=25, ha="right")
    axis.legend(ncols=4, loc="upper center")
    figure.tight_layout()

    output_path = output_dir / "topk_comparison.png"
    figure.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(figure)
    return output_path


def write_summary_csv(runs: list[Run], output_dir: Path) -> Path:
    path = output_dir / "model_summary.csv"
    fields = [
        "model", "epochs", "best_validation_top1", "test_loss",
        "test_top1", "test_top3", "test_top5", "test_top10",
        "battle_win_rate", "battle_loss_rate", "battle_draw_rate",
        "average_turns", "seconds_per_game",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for run in runs:
            writer.writerow(
                {
                    "model": run.model,
                    "epochs": max(run.epoch),
                    "best_validation_top1": run.best_val_top1,
                    "test_loss": run.test_loss,
                    "test_top1": run.test_top1,
                    "test_top3": run.test_top3,
                    "test_top5": run.test_top5,
                    "test_top10": run.test_top10,
                    "battle_win_rate": run.battle_win,
                    "battle_loss_rate": run.battle_loss,
                    "battle_draw_rate": run.battle_draw,
                    "average_turns": run.average_turns,
                    "seconds_per_game": run.seconds_per_game,
                }
            )
    return path


def write_epoch_csv(runs: list[Run], output_dir: Path) -> Path:
    path = output_dir / "epoch_history.csv"
    fields = [
        "model", "epoch", "learning_rate", "train_loss", "train_top1",
        "validation_loss", "validation_top1", "validation_top3",
        "validation_top5", "validation_top10",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for run in runs:
            for index, epoch in enumerate(run.epoch):
                writer.writerow(
                    {
                        "model": run.model,
                        "epoch": epoch,
                        "learning_rate": run.learning_rate[index],
                        "train_loss": run.train_loss[index],
                        "train_top1": run.train_top1[index],
                        "validation_loss": run.val_loss[index],
                        "validation_top1": run.val_top1[index],
                        "validation_top3": run.val_top3[index],
                        "validation_top5": run.val_top5[index],
                        "validation_top10": run.val_top10[index],
                    }
                )
    return path


def main() -> None:
    args = parse_args()
    if not args.record.is_file():
        raise FileNotFoundError(f"Cannot find log file: {args.record}")

    apply_plot_style()
    runs = parse_record(args.record)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    selected_runs = runs
    if args.model:
        selected_runs = [run for run in runs if run.model == args.model]
        if not selected_runs:
            available = ", ".join(run.model for run in runs)
            raise ValueError(
                f"Unknown model '{args.model}'. Available models: {available}"
            )

    output_paths = [
        plot_training_curve(run, args.output_dir, args.dpi)
        for run in selected_runs
    ]
    output_paths.extend(
        [
            plot_model_comparison(runs, args.output_dir, args.dpi),
            plot_topk_comparison(runs, args.output_dir, args.dpi),
            write_summary_csv(runs, args.output_dir),
            write_epoch_csv(runs, args.output_dir),
        ]
    )

    best_top1 = max(runs, key=lambda run: run.test_top1)
    best_loss = min(runs, key=lambda run: run.test_loss)
    print(f"Parsed {len(runs)} experiments from {args.record}")
    print(
        f"Best test Top-1: {best_top1.model} "
        f"({best_top1.test_top1:.2%})"
    )
    print(
        f"Lowest test loss: {best_loss.model} "
        f"({best_loss.test_loss:.4f})"
    )
    print("Created:")
    for path in output_paths:
        print(f"  {path}")


if __name__ == "__main__":
    main()
