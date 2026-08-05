# CMPT310-G18 — CNN Training

## Trained Models and Training Script

This directory contains all 11 trained CNN model checkpoints and the training script, `train_cnn.py`.

The project uses the external [Karesis/Gomoku dataset](https://huggingface.co/datasets/Karesis/Gomoku/blob/main/README.md) from Hugging Face.

The datasets/ contain the external databases we used.

## Requirements

The following libraries are required:

* NumPy
* PyTorch

Install the required packages from the `training/` directory:

```bash
pip install -r requirements.txt
```

## Dataset Paths

The training and test datasets are stored in the following directory structure:

```text
training/datasets/gomoku_dataset_split/
├── train/
│   └── full_board/
│       ├── board_states.npy
│       ├── next_moves_coords.npy
│       └── next_moves_players.npy
└── test/
    └── full_board/
        ├── board_states.npy
        ├── next_moves_coords.npy
        └── next_moves_players.npy
```

The three files contain:

* `board_states.npy`: Gomoku board states with shape `(N, 15, 15)`
* `next_moves_coords.npy`: labeled next-move coordinates with shape `(N, 2)`
* `next_moves_players.npy`: the player making each labeled move with shape `(N,)`

## Training the Model

Run the training program from the `training/` directory:

```bash
python train_cnn.py
```

With no additional parameters, the program uses the default configuration:

* 20 training epochs
* Batch size of 128
* Learning rate of `1e-3`
* 64 CNN feature channels
* 5 residual blocks
* 10% validation split
* Data augmentation enabled

The program automatically selects the best available device in the following order:

1. CUDA GPU
2. Apple MPS
3. CPU

## Command-Line Parameters

The general command format is:

```bash
python train_cnn.py [OPTIONS]
```

Use the following command to display the available options:

```bash
python train_cnn.py --help
```

| Parameter               | Type    | Default                         | Description                                                                                                                                                   |
| ----------------------- | ------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--data-dir PATH`       | Path    | `datasets/gomoku_dataset_split` | Specifies the dataset root directory containing the `train/` and `test/` folders. Relative paths are resolved from the current working directory.             |
| `--model-out PATH`      | Path    | `gomoku_cnn.pt`                 | Specifies where the best model checkpoint will be saved. The checkpoint with the highest validation Top-1 accuracy is retained.                               |
| `--epochs N`            | Integer | `20`                            | Sets the number of complete passes through the training dataset. The tested values were `10`, `20`, and `40`.                                                 |
| `--batch-size N`        | Integer | `128`                           | Sets the number of training samples processed in each batch. The tested values were `64`, `128`, and `256`.                                                   |
| `--learning-rate VALUE` | Float   | `1e-3`                          | Sets the initial learning rate used by the AdamW optimizer. The tested values were `5e-4`, `1e-3`, and `2e-3`.                                                |
| `--weight-decay VALUE`  | Float   | `1e-4`                          | Sets the L2 weight-decay regularization applied by the AdamW optimizer.                                                                                       |
| `--channels N`          | Integer | `64`                            | Sets the number of feature channels in the CNN. More channels increase model capacity and resource usage. The tested values were `32`, `64`, and `128`.       |
| `--blocks N`            | Integer | `5`                             | Sets the number of residual blocks in the CNN. More blocks create a deeper network. The tested values were `2`, `5`, and `10`.                                |
| `--num-workers N`       | Integer | `0`                             | Sets the number of worker processes used by each PyTorch DataLoader. A value of `0` provides maximum compatibility.                                           |
| `--no-augmentation`     | Flag    | Disabled                        | Disables random board rotations and reflections. Data augmentation is enabled when this flag is not included.                                                 |
| `--seed N`              | Integer | `42`                            | Sets the random seed used by Python, NumPy, and PyTorch for reproducible splitting, shuffling, augmentation, and model initialization.                        |
| `--val-fraction VALUE`  | Float   | `0.1`                           | Sets the fraction of cleaned training samples reserved for validation. The validation set is used for learning-rate scheduling and best-checkpoint selection. |

## Example Custom Training Command

The following command trains a larger model for 40 epochs and saves it as `gomoku_cnn_custom.pt`:

```bash
python train_cnn.py \
  --data-dir datasets/gomoku_dataset_split \
  --model-out gomoku_cnn_custom.pt \
  --epochs 40 \
  --batch-size 128 \
  --learning-rate 1e-3 \
  --weight-decay 1e-4 \
  --channels 128 \
  --blocks 10 \
  --num-workers 0 \
  --seed 42 \
  --val-fraction 0.1
```
