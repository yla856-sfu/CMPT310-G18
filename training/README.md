# CMPT310-G18
## Trained Models and Training Script

This directory contains all 11 trained models and the training script, `train_cnn.py`.  
The datasets contain the external databases we used.  
The link is https://huggingface.co/datasets/Karesis/Gomoku/blob/main/README.md  

### Requirements

The following libraries are required:

* NumPy
* PyTorch

### Dataset Paths

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
## Run

Install pytorch:

```bash
pip install -r requirements.txt
```

## Training model

Run the training:

```bash
python train_cnn.py
```
