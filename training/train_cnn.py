# Examples:
# python train_cnn.py --epochs 20

from __future__ import annotations
import argparse
import random
import numpy as np
import torch
from pathlib import Path
from torch import nn
from torch.utils.data import DataLoader, Dataset

BOARD_SIZE = 15
NUM_CELLS = BOARD_SIZE * BOARD_SIZE

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a CNN to predict the next Gomoku move."
    )
    # Path to gomoku_dataset_split.
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("datasets") / "gomoku_dataset_split",
    )
    # Output checkpoint path.
    parser.add_argument(
        "--model-out",
        type=Path,
        default=Path("gomoku_cnn.pt"),
    )
    # Number of epochs.
    parser.add_argument(
        "--epochs", # 10 20 40
        type=int,
        default=20,
    )
    # Number of samples per training batch.
    parser.add_argument(
        "--batch-size", # 64 128 256
        type=int,
        default=128,
    )
    # Initial learning rate for the AdamW optimizer.
    parser.add_argument(
        "--learning-rate", # 5e-4 1e-3 2e-3
        type=float,
        default=1e-3,
    )
    # L2 weight decay applied by the AdamW optimizer.
    parser.add_argument(
        "--weight-decay",
        type=float,
        default=1e-4,
    )
    # Number of hidden CNN channels.
    parser.add_argument(
        "--channels", # 32 64 128
        type=int,
        default=64,
    )
    # Number of residual blocks.
    parser.add_argument(
        "--blocks", # 2 5 10
        type=int,
        default=5,
    )
    # DataLoader worker count. Use 0 for maximum portability.
    parser.add_argument(
        "--num-workers",
        type=int,
        default=0,
    )
    # Disable rotations/reflections during training.
    parser.add_argument(
        "--no-augmentation",
        action="store_true",
    )
    # Random seed for reproducible shuffling, augmentation, and initialization.
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )
    # Fraction of the training samples to hold out as a validation set
    # (sample-level split). Used for LR scheduling and best-checkpoint
    # selection; the test set is only evaluated once, after training finishes.
    parser.add_argument(
        "--val-fraction",
        type=float,
        default=0.1, # 10%
    )
    return parser.parse_args()

# Seed every RNG used during training (Python, NumPy, PyTorch CPU/CUDA) so a
# run with the same --seed reproduces the same shuffling, augmentation, and initialization.
def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

# Pick the best available device to train on: CUDA GPU, then Apple MPS,
# then fall back to CPU. (In this project, we use cuda for training)
def choose_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")

    if (
        hasattr(torch.backends, "mps")
        and torch.backends.mps.is_available()
    ):
        return torch.device("mps")

    return torch.device("cpu")

# Load one dataset split (boards, next-move coords, next-move players) from
# .npy files under data_dir, validate it, and drop samples whose target square is already occupied.
def load_split(data_dir: Path, split: str):
    split_dir = data_dir / split / "full_board"

    boards_path = split_dir / "board_states.npy"
    moves_path = split_dir / "next_moves_coords.npy"
    players_path = split_dir / "next_moves_players.npy"

    # Fail early with a clear error if any expected file is missing.
    for path in (boards_path, moves_path, players_path):
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    # Load the raw arrays: board states, next-move coords, and next-move players.
    boards = np.load(boards_path)       # board_states.npy: (N, 15, 15) array where 0=empty, 1=black, -1=white
    moves = np.load(moves_path)         # next_moves_coords.npy: (N, 2) array with (x,y) coordinates
    players = np.load(players_path)     # next_moves_players.npy: (N,) array with player indicators (1=black, -1=white)

    validate_split(boards, moves, players, split)

    # One index per sample, used to select the target cell from each board.
    sample_indices = np.arange(len(boards))

    # Coordinates are stored as (x, y); boards are indexed as [sample, y, x].
    x = moves[:, 0].astype(np.int64)
    y = moves[:, 1].astype(np.int64)

    # For each sample, check whether its labeled target square is empty.
    valid_mask = boards[sample_indices, y, x] == 0

    invalid_count = int((~valid_mask).sum())

    # Drop any samples whose target square was already occupied.
    if invalid_count > 0:
        print(
            f"Warning: {split} contains {invalid_count} invalid samples "
            "whose target square is occupied. These samples will be skipped."
        )

        boards = boards[valid_mask]
        moves = moves[valid_mask]
        players = players[valid_mask]

    return boards, moves, players

# Randomly split training samples into training and validation sets.
def split_train_validation(
    boards: np.ndarray,
    moves: np.ndarray,
    players: np.ndarray,
    val_fraction: float,
    seed: int,
):
    # Generate a reproducible random ordering of all sample indices.
    num_samples = len(boards)
    permutation = np.random.RandomState(seed).permutation(num_samples)

    # Use the first portion for validation and the rest for training.
    num_val = int(round(num_samples * val_fraction))
    val_indices = permutation[:num_val]
    train_indices = permutation[num_val:]

    return (
        boards[train_indices],
        moves[train_indices],
        players[train_indices],
        boards[val_indices],
        moves[val_indices],
        players[val_indices],
    )

# Validate the shapes, sample counts, values, and move coordinates of one split.
def validate_split(
    boards: np.ndarray,
    moves: np.ndarray,
    players: np.ndarray,
    split: str,
):
    # Each sample must contain one BOARD_SIZE × BOARD_SIZE board.
    if boards.ndim != 3 or boards.shape[1:] != (BOARD_SIZE, BOARD_SIZE):
        raise ValueError(
            f"{split}: expected boards shape (N, 15, 15), got {boards.shape}"
        )

    # Each move must contain an (x, y) coordinate pair.
    if moves.ndim != 2 or moves.shape[1] != 2:
        raise ValueError(
            f"{split}: expected moves shape (N, 2), got {moves.shape}"
        )

    # Each sample must contain one player value.
    if players.ndim != 1:
        raise ValueError(
            f"{split}: expected players shape (N,), got {players.shape}"
        )

    # Boards, moves, and players must contain the same number of samples.
    if not (len(boards) == len(moves) == len(players)):
        raise ValueError(
            f"{split}: sample counts differ: "
            f"boards={len(boards)}, moves={len(moves)}, players={len(players)}"
        )

    # Board cells may contain only player stones (-1, 1) or empty spaces (0).
    if not np.all(np.isin(boards, (-1, 0, 1))):
        raise ValueError(f"{split}: boards must contain only -1, 0, and 1.")

    # The next player must be either -1 or 1.
    if not np.all(np.isin(players, (-1, 1))):
        raise ValueError(f"{split}: players must contain only -1 and 1.")

    # Move coordinates are stored in (x, y) order.
    x = moves[:, 0]
    y = moves[:, 1]

    # Both coordinates must lie within the board boundaries. (15x15, so 0-14)
    if np.any((x < 0) | (x >= BOARD_SIZE)):
        raise ValueError(f"{split}: x coordinate outside 0..14.")

    if np.any((y < 0) | (y >= BOARD_SIZE)):
        raise ValueError(f"{split}: y coordinate outside 0..14.")

# Apply one of eight square symmetries to both the board and its move label.
# Since board orientation is not strategically significant in Gomoku,
# applying random rotations and reflections exposes the model to equivalent
# board positions in different orientations.
def transform_board_and_label(
    board: torch.Tensor,
    label: int,
    transform_id: int,
):
    # Convert the flattened move label into a 2D one-hot position map.
    move_map = torch.zeros(
        (BOARD_SIZE, BOARD_SIZE),
        dtype=torch.bool,
    )
    y = label // BOARD_SIZE
    x = label % BOARD_SIZE
    move_map[y, x] = True

    # IDs 0–3 select rotation; IDs 4–7 also apply a horizontal reflection.
    rotations = transform_id % 4
    reflected = transform_id >= 4

    # Rotate the board and target position together in 90-degree steps.
    if rotations:
        board = torch.rot90(board, rotations, dims=(-2, -1))
        move_map = torch.rot90(move_map, rotations, dims=(-2, -1))

    # Reflect both the board and target position from left to right.
    if reflected:
        board = torch.flip(board, dims=(-1,))
        move_map = torch.flip(move_map, dims=(-1,))

    # Convert the transformed 2D target position back to a flattened label.
    transformed_label = int(
        torch.argmax(
            move_map.reshape(-1).to(torch.int64)
        ).item()
    )
    return board, transformed_label

# Converts raw Gomoku board data into PyTorch samples that can be used directly to train a CNN.
# Represents each board as two channels: the current player's stones and the opponent's stones.
# Returns the board features, target move label, and occupied-position mask for each sample.
class GomokuDataset(Dataset):
    # Store board states, target moves, player values, and augmentation settings.
    def __init__(
        self,
        boards: np.ndarray,
        moves: np.ndarray,
        players: np.ndarray,
        augment: bool,
    ):
        self.boards = boards
        self.moves = moves.astype(np.int64)
        self.players = players.astype(np.int8)
        self.augment = augment

    # Return the total number of samples.
    def __len__(self) -> int:
        return len(self.boards)

    # Convert one sample into model inputs, its target label, and an occupied-cell mask.
    def __getitem__(self,index: int):
        board = self.boards[index]
        player = self.players[index]

        # Represent the board from the current player's perspective:
        # channel 0 = current player's stones
        # channel 1 = opponent's stones
        own_stones = board == player
        opponent_stones = board == -player

        # Combine both binary boards into a (2, BOARD_SIZE, BOARD_SIZE) input.
        features = np.stack(
            (own_stones, opponent_stones),
            axis=0,
        ).astype(np.float32)

        # Convert the target (x, y) coordinate into a flattened class label.
        x = int(self.moves[index, 0])
        y = int(self.moves[index, 1])
        label = y * BOARD_SIZE + x

        # Convert the NumPy features into a PyTorch tensor.
        features_tensor = torch.from_numpy(features)

        # Randomly apply one of the eight square symmetries during training.
        if self.augment:
            transform_id = random.randrange(8)
            features_tensor, label = transform_board_and_label(
                features_tensor,
                label,
                transform_id,
            )

        # Mark cells occupied by either player and flatten the mask to 225 cells.
        occupied = features_tensor.sum(dim=0) > 0

        return (
            features_tensor,
            torch.tensor(label, dtype=torch.long),
            occupied.reshape(-1),
        )

# Build a residual block with two convolutional layers.
# Looks at nearby board positions to discover new patterns while keeping
# the information that the network has already learned.
class ResidualBlock(nn.Module):
    def __init__(self, channels: int):
        super().__init__()

        self.layers = nn.Sequential(
            # Use a 3×3 window to examine each position and its eight neighbors.
            # padding=1 keeps the board's width and height unchanged.
            nn.Conv2d(
                channels,
                channels,
                kernel_size=3,
                padding=1,
                bias=False,
            ),
            # Keep the calculated values in a stable range during training.
            nn.BatchNorm2d(channels),
            # Replace negative values with zero while keeping positive values.
            nn.ReLU(inplace=True),

            # Examine the board again to discover more detailed patterns
            # based on the information found by the first convolution.
            nn.Conv2d(
                channels,
                channels,
                kernel_size=3,
                padding=1,
                bias=False,
            ),

            # Stabilize the newly calculated values before combining them with the original information.
            nn.BatchNorm2d(channels),
        )

        # This will remove negative values after the old and new information have been combined.
        self.activation = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # self.layers(x) contains newly discovered board information.
        # Adding x keeps the original information instead of losing it.
        # The final ReLU replaces negative results with zero.
        return self.activation(x + self.layers(x))

# Takes a two-channel Gomoku board and calculates a move score
# for every position, allowing the model to choose the next move.
class GomokuCNN(nn.Module):
    def __init__(
        self,
        channels: int = 64,
        blocks: int = 5,
    ):
        super().__init__()

        self.input_layer = nn.Sequential(
            # Examine each 3×3 area of the board and convert the two input
            # channels into many different kinds of board information.
            # Input shape:  (batch_size, 2, BOARD_SIZE, BOARD_SIZE)
            # Output shape: (batch_size, channels, BOARD_SIZE, BOARD_SIZE)
            nn.Conv2d(
                in_channels=2,
                out_channels=channels,
                kernel_size=3,
                padding=1,
                bias=False,
            ),
            # Keep the calculated values stable during training.
            nn.BatchNorm2d(channels),
            # Replace negative values with zero and keep positive values.
            nn.ReLU(inplace=True),
        )

        # Pass the board information through several ResidualBlocks.
        # Each block discovers new board patterns while preserving
        # information that was already learned by earlier layers.
        self.residual_tower = nn.Sequential(
            *[ResidualBlock(channels) for _ in range(blocks)]
        )

        # Combine all discovered board information into one move score for every position on the board.
        self.policy_head = nn.Sequential(
            # At each position, combine the information from all channels
            # and reduce the channel count from 'channels' to 32.
            nn.Conv2d(
                in_channels=channels,
                out_channels=32,
                kernel_size=1,
                bias=False,
            ),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),

            # Reduce the 32 values at each position to one final move score.
            # Output shape: (batch_size, 1, BOARD_SIZE, BOARD_SIZE)
            nn.Conv2d(
                in_channels=32,
                out_channels=1,
                kernel_size=1,
            ),
        )

    # Convert the two-dimensional score board into a one-dimensional list.
    # The output shape is (batch_size, 225).
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.input_layer(x)
        x = self.residual_tower(x)
        x = self.policy_head(x)

        return x.flatten(start_dim=1)

# Replace the scores of occupied positions with an extremely small value.
# This gives those positions almost zero probability and prevents them
# from being selected as the model's next move.
def mask_occupied_logits(
    logits: torch.Tensor,
    occupied: torch.Tensor,
) -> torch.Tensor:
    return logits.masked_fill(occupied, -1e9)

# Evaluate the model by checking whether the correct move appears among
# its Top-1, Top-3, Top-5, and Top-10 recommended moves.
def calculate_topk_correct(
    logits: torch.Tensor,
    labels: torch.Tensor,
    ks: tuple[int, ...] = (1, 3, 5, 10),
):
    # Find the largest Top-k value requested.
    # By default, this is 10 because the function calculates up to Top-10.
    maximum_k = max(ks)

    # For every board in the batch, find the board positions with the
    # highest move scores. With the default settings, this returns the
    # model's 10 most recommended moves for each board.
    # Input shape:  (batch_size, 225)
    # Output shape: (batch_size, 10)
    top_indices = logits.topk(maximum_k, dim=1).indices

    # Store the number of correct predictions for each Top-k value.
    # Example result: {1: 20, 3: 45, 5: 60, 10: 80}
    results: dict[int, int] = {}
    
    for k in ks:
        # Check whether the actual correct move for each board appears
        # anywhere among the model's first k recommended moves.
        # Top-1 is correct only when the model's first choice is correct.
        # Top-3 is correct when the correct move is one of its first 3 choices.
        # The same rule is used for Top-5 and Top-10.
        correct = top_indices[:, :k].eq(labels.unsqueeze(1)).any(dim=1)
        # Count how many boards in this batch have a correct Top-k result.
        results[k] = int(correct.sum().item())

    # Return correct counts
    return results

# Train the model on the entire training dataset for one epoch. For each batch of board positions, 
# the model first predicts the move locations, compares the predictions with the ground-truth answers, 
# and then updates the network weights based on the errors. 
# Finally, return the average loss and Top-1 accuracy for the epoch.
def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
):
    model.train()

    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    # Load and train one batch of boards at a time.
    # features: CNN input boards.
    # labels: the correct move position for each board.
    # occupied: positions that already contain stones.
    for features, labels, occupied in loader:
        # Move the batch to the selected device, CPU/GPU, GPU first.
        features = features.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)
        occupied = occupied.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)

        # Ask the model to calculate a move score for every board position.
        # For a 15×15 board, logits has shape: (batch_size, 225)
        logits = model(features)
        logits = mask_occupied_logits(logits, occupied)

        # Compare the predicted move scores with the correct move positions.
        # A better prediction produces a smaller loss value.
        loss = criterion(logits, labels)

        # Work backwards from the loss to calculate how every learnable
        # weight in the model should change to improve its predictions.
        loss.backward()

        # Clip unusually large weight changes to keep training stable.
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)

        # Update the model's weights using the changes calculated above.
        optimizer.step()

        batch_size = labels.size(0)
        total_samples += batch_size
        total_loss += float(loss.item()) * batch_size

        # For each board, choose the position with the highest score.
        # Count it as correct when that position matches the actual move.
        total_correct += int(
            logits.argmax(dim=1).eq(labels).sum().item()
        )

    # Return:
    # 1. Average loss per board during this epoch.
    # 2. Percentage of boards whose correct move was the model's first choice.
    return (total_loss / total_samples, total_correct / total_samples)

# Evaluate the current model on the validation and test dataset without further training or updating any network weights. 
# Finally, return the average loss and the Top-1, Top-3, Top-5, and Top-10 accuracies.
# The structure is similar to train_one_epoch.
@torch.inference_mode()
def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
):
    model.eval()

    total_loss = 0.0
    total_samples = 0
    topk_totals = {1: 0, 3: 0, 5: 0, 10: 0}

    for features, labels, occupied in loader:
        features = features.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)
        occupied = occupied.to(device, non_blocking=True)

        logits = model(features)
        logits = mask_occupied_logits(logits, occupied)

        loss = criterion(logits, labels)

        batch_size = labels.size(0)
        total_samples += batch_size
        total_loss += float(loss.item()) * batch_size

        batch_results = calculate_topk_correct(logits, labels)

        for k, count in batch_results.items():
            topk_totals[k] += count

    topk_accuracies = {
        k: count / total_samples
        for k, count in topk_totals.items()
    }

    return total_loss / total_samples, topk_accuracies

# Save the current model weights, optimizer state, training progress, and model architecture information into 
# a single checkpoint file so that the model can be loaded.
def save_checkpoint(
    path: Path,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    best_top1: float,
    channels: int,
    blocks: int,
):
    path.parent.mkdir(parents=True, exist_ok=True)

    checkpoint = {
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "epoch": epoch,
        # Record the validation Top-1 accuracy that made this model the best model found so far.
        "best_top1": best_top1,
        "board_size": BOARD_SIZE,
        "num_cells": NUM_CELLS,
        "input_channels": 2,
        "channels": channels,
        "blocks": blocks,
        "input_format": (
            "channel 0=current player stones; "
            "channel 1=opponent stones"
        ),
        "label_format": "class_id = y * 15 + x",
    }

    torch.save(checkpoint, path)

# Run the complete Gomoku CNN training process.
# Load and prepare the data, create the model, train it for the requested
# number of epochs, save the model with the best validation Top-1 accuracy,
# and finally evaluate that best model on the separate test set.
def main():
    args = parse_args()
    set_seed(args.seed)

    device = choose_device()
    print(f"Device: {device}")

    # Load the training data and separate part of it for validation.
    print("Loading training data...")
    train_boards, train_moves, train_players = load_split(
        args.data_dir,
        "train",
    )

    (
        train_boards,
        train_moves,
        train_players,
        val_boards,
        val_moves,
        val_players,
    ) = split_train_validation(
        train_boards,
        train_moves,
        train_players,
        args.val_fraction,
        args.seed,
    )

    # Load the separate test set used only for the final evaluation.
    print("Loading test data...")
    test_boards, test_moves, test_players = load_split(
        args.data_dir,
        "test",
    )

    # Convert the raw arrays into PyTorch datasets.
    train_dataset = GomokuDataset(
        train_boards,
        train_moves,
        train_players,
        augment=not args.no_augmentation,
    )

    val_dataset = GomokuDataset(
        val_boards,
        val_moves,
        val_players,
        augment=False,
    )

    test_dataset = GomokuDataset(
        test_boards,
        test_moves,
        test_players,
        augment=False,
    )

    pin_memory = device.type == "cuda"

    # Group samples into batches. Shuffle only the training data.
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=pin_memory,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=pin_memory,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=pin_memory,
    )

    # Create the CNN.
    model = GomokuCNN(
        channels=args.channels,
        blocks=args.blocks,
    ).to(device)

    criterion = nn.CrossEntropyLoss()

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )

    # Halve the learning rate when validation loss stops improving.
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=0.5,
        patience=2,
    )

    parameter_count = sum(
        parameter.numel()
        for parameter in model.parameters()
        if parameter.requires_grad
    )

    print(f"Training samples: {len(train_dataset)}")
    print(f"Validation samples: {len(val_dataset)}")
    print(f"Test samples: {len(test_dataset)}")
    print(f"Trainable parameters: {parameter_count:,}")
    print(
        "Data augmentation:",
        "enabled" if not args.no_augmentation else "disabled",
    )

    best_top1 = -1.0

    # Train once on the training set and evaluate on the validation set during each epoch.
    for epoch in range(1, args.epochs + 1):
        train_loss, train_top1 = train_one_epoch(
            model,
            train_loader,
            optimizer,
            criterion,
            device,
        )

        val_loss, val_topk = evaluate(
            model,
            val_loader,
            criterion,
            device,
        )

        scheduler.step(val_loss)

        learning_rate = optimizer.param_groups[0]["lr"]

        print(
            f"Epoch {epoch:02d}/{args.epochs} | "
            f"lr={learning_rate:.6f} | "
            f"train loss={train_loss:.4f} | "
            f"train top1={train_top1:.4f} | "
            f"val loss={val_loss:.4f} | "
            f"top1={val_topk[1]:.4f} | "
            f"top3={val_topk[3]:.4f} | "
            f"top5={val_topk[5]:.4f} | "
            f"top10={val_topk[10]:.4f}"
        )

        # Save the model only when it achieves a new best validation Top-1 score.
        if val_topk[1] > best_top1:
            best_top1 = val_topk[1]

            save_checkpoint(
                args.model_out,
                model,
                optimizer,
                epoch,
                best_top1,
                args.channels,
                args.blocks,
            )

            print(f"  Saved new best model to: {args.model_out}")

    print()
    print("Training finished.")
    print(f"Best validation Top-1 accuracy: {best_top1:.4f}")

    # Reload the best validation model and evaluate it on the test set.
    print("Loading best checkpoint for final test evaluation...")
    best_checkpoint = torch.load(args.model_out, map_location=device)
    model.load_state_dict(best_checkpoint["model_state_dict"])

    test_loss, test_topk = evaluate(
        model,
        test_loader,
        criterion,
        device,
    )

    print(
        f"Final test loss={test_loss:.4f} | "
        f"top1={test_topk[1]:.4f} | "
        f"top3={test_topk[3]:.4f} | "
        f"top5={test_topk[5]:.4f} | "
        f"top10={test_topk[10]:.4f}"
    )
    print(f"Best checkpoint: {args.model_out.resolve()}")


if __name__ == "__main__":
    main()
