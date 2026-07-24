# This module implements the CNN policy agent for Gomoku.
# It rebuilds the network trained by training/train_cnn.py, loads the saved
# checkpoint, and uses the model's per-cell scores to greedily pick a move.
import os
import random
import torch
from torch import nn

from game.board import SIZE, EMPTY, board

# Checkpoint saved under training/. Load CNN models with different parameters by renaming gomoku_cnn.pt.
_CHECKPOINT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "training",
    "gomoku_cnn_default.pt", # <- Rename this.
)

# Cached model instance so the checkpoint is only loaded from disk once.
_model = None

# One residual block: two 3x3 convolutions with a skip connection, matching
# the block used to train the checkpoint in train_cnn.py.
class _ResidualBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()

        self.layers = nn.Sequential(
            nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
        )
        self.activation = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.activation(x + self.layers(x))


# Mirrors the GomokuCNN architecture from train_cnn.py: an input conv layer,
# a tower of residual blocks, and a policy head that outputs one raw score
# per board cell (flattened to a length-225 vector).
class _GomokuCNN(nn.Module):
    def __init__(self, channels, blocks):
        super().__init__()

        self.input_layer = nn.Sequential(
            nn.Conv2d(2, channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
        )

        self.residual_tower = nn.Sequential(
            *[_ResidualBlock(channels) for _ in range(blocks)]
        )

        self.policy_head = nn.Sequential(
            nn.Conv2d(channels, 32, kernel_size=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 1, kernel_size=1),
        )

    def forward(self, x):
        x = self.input_layer(x)
        x = self.residual_tower(x)
        x = self.policy_head(x)
        return x.flatten(start_dim=1)


# Load the checkpoint and rebuild the model on first use, then reuse the
# cached instance on every later call so the checkpoint is read only once.
def _load_model():
    global _model

    if _model is not None:
        return _model

    checkpoint = torch.load(_CHECKPOINT_PATH, map_location="cpu")

    model = _GomokuCNN(
        channels=checkpoint["channels"],
        blocks=checkpoint["blocks"],
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    _model = model
    return _model


# Builds the (1, 2, SIZE, SIZE) input tensor: channel 0 = player's stones,
# channel 1 = opponent's stones. Matches the format train_cnn.py was trained on.
def _board_to_tensor(player):
    own = torch.zeros((SIZE, SIZE), dtype=torch.float32)
    opponent = torch.zeros((SIZE, SIZE), dtype=torch.float32)

    for y in range(SIZE):
        for x in range(SIZE):
            cell = board[y][x]

            if cell == player:
                own[y, x] = 1.0
            elif cell != EMPTY:
                opponent[y, x] = 1.0

    return torch.stack((own, opponent), dim=0).unsqueeze(0)


# Returns {(x, y): score} for every empty cell, using the CNN's raw policy
# logits from player's perspective. Higher score = CNN considers it a
# stronger move for player. Exposed so cnn_minimax_agent
# can reuse the CNN's move ranking without duplicating model loading.
def policy_scores(player):
    model = _load_model()
    features = _board_to_tensor(player)

    with torch.inference_mode():
        logits = model(features)[0]

    scores = {}

    for y in range(SIZE):
        for x in range(SIZE):
            if board[y][x] == EMPTY:
                scores[(x, y)] = logits[y * SIZE + x].item()

    return scores


# Choose and make a move by greedily taking the empty cell with the highest
# CNN policy score, breaking ties randomly among equally-scored cells.
def cnn_algorithm(player, opponent):
    scores = policy_scores(player)

    # Get the highest policy score.
    best_score = max(scores.values())

    # Collect all moves tied for the highest score.
    best_moves = [move for move, score in scores.items() if score == best_score]

    # Randomly choose one of the equally best moves. (If there are multiple)
    x, y = random.choice(best_moves)
    board[y][x] = player

    return x, y
