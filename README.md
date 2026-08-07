# CMPT310 D100 2026 Summer

# Gomoku AI — CMPT 310 Group 18

This project implements an AI system for Gomoku (Five in a Row) on a 15 × 15 board. It supports Human vs. AI gameplay through a Pygame interface and automated AI vs. AI evaluation through command-line programs.

The system includes Random, Greedy, Minimax, CNN (Convolutional Neural Networks), and CNN–Minimax hybrid agents.  

## Team Members

* Neo Hyldelund
* Yang Long
* John Park
* Matthew Pham  

## Main Features

* Human vs. AI gameplay with a graphical interface
* Legal-move, win, and draw detection
* 11 selectable AI configurations
* Minimax search with Alpha–Beta pruning
* Residual CNN policy network trained with PyTorch
* CNN–Minimax hybrid search
* Sequential and multiprocessing AI evaluation
* Win rate, draw rate, move count, and thinking-time statistics
* Testing result aggregation and ranking

## Supported AI Types

| Command Name  | Description                                          |
| ------------- | ---------------------------------------------------- |
| `random`      | Selects a random legal move.                         |
| `greedy`      | Uses tactical checks and heuristic board evaluation. |
| `minimax1`    | Minimax search with depth 1.                         |
| `minimax2`    | Minimax search with depth 2.                         |
| `minimax3`    | Minimax search with depth 3.                         |
| `minimax4`    | Minimax search with depth 4.                         |
| `cnn`         | Selects moves using the trained CNN policy network.  |
| `cnnminimax1` | CNN–Minimax hybrid agent with depth 1.               |
| `cnnminimax2` | CNN–Minimax hybrid agent with depth 2.               |
| `cnnminimax3` | CNN–Minimax hybrid agent with depth 3.               |
| `cnnminimax4` | CNN–Minimax hybrid agent with depth 4.               |

Higher Minimax depths provide more extensive search but require significantly more execution time.

## Project Structure

```text
CMPT310-G18/
├── game/                       # Board rules and AI agent implementations
│   ├── board.py
│   ├── game.py
│   ├── evaluation.py
│   ├── random_agent.py
│   ├── greedy_agent.py
│   ├── minimax_agent.py
│   ├── cnn_agent.py
│   └── cnn_minimax_agent.py
├── gui/
│   └── gui.py                  # Pygame user interface
├── training/
│   ├── train_cnn.py            # CNN training and evaluation program
│   ├── README.md               # Training instructions and model information
│   └── gomoku_cnn_*            # Trained model checkpoints
├── record/
│   ├── analyze_record.py       # Testing result analysis
│   ├── AI VS AI record.txt
│   ├── plot_gomoku_training.py # Visualize cnn model performance
│   └── cnn Model record.txt
├── main.py                     # Human-vs.-AI program
├── TEST.py                     # Sequential AI vs. AI evaluation (with log and allow watching)
├── TEST_mp.py                  # Multiprocessing AI vs. AI evaluation
├── requirements.txt
└── README.md
```

## Requirements

The project requires [Python](https://www.python.org/downloads/) 3.12 (3.14 is not supporting pygame for now) and the following libraries:

* NumPy
* Pygame
* PyTorch

Install the required packages from the project root directory:

```bash
pip install -r requirements.txt
```

## Human vs. AI

Start the graphical game by running:

```bash
python main.py
```
![GUI](https://i.ibb.co/JFz6LTW7/2.png)  
Select an AI opponent from the menu before the game begins. The human player uses black stones and moves first, while the selected AI uses white stones.
![GUI](https://i.ibb.co/ynSjN6Ny/GUI.png)  
Click near a board intersection to place a stone. When the game ends, use the restart button to begin another game against the same AI.

## AI vs. AI Evaluation

### Sequential Evaluation

Use `TEST.py` to run repeated games between two AI agents:

```bash
python TEST.py AI_TYPE_1 AI_TYPE_2 TEST_TIMES WATCH_PROCESS [INTERVAL_SECONDS]
```

Example:

```bash
python TEST.py random greedy 100 false
```

This command runs 100 games between the Random and Greedy agents without displaying every move.

To display the board after each move:

```bash
python TEST.py greedy minimax1 1 true 0.5
```

The two agents alternate moving first between games to improve evaluation fairness. Detailed results are written to `log.txt`.

### Multiprocessing Evaluation

Use `TEST_mp.py` to run games in parallel:

```bash
python TEST_mp.py AI_TYPE_1 AI_TYPE_2 TEST_TIMES [WORKERS]
```

Example:

```bash
python TEST_mp.py random greedy 100 4
```

This command runs 100 games using four worker processes.

The multiprocessing version reports final statistics but does not display individual moves or create a detailed per-game log.

## CNN Training and Models

The `training/` directory contains the CNN training program, dataset structure, and all 11 trained model configurations.

For complete training instructions, dataset paths, and model information, see:

[Training README](training/README.md)

The game uses the following checkpoint by default:

```text
training/gomoku_cnn_default.pt
```

The checkpoint is loaded automatically when the CNN or CNN–Minimax agent is selected.

## Testing Result Analysis & Visualize cnn model performance

The project includes a program for aggregating completed AI matchups and ranking the agents according to gameplay strength and execution speed.

Run the analysis from the `record/` directory:

```bash
cd record
python analyze_record.py
```

The program reads `AI VS AI record.txt` and reports each agent’s wins, losses, draws, average thinking time, speed score, and final ranking score.  

And for visualize cnn model performance,

Run the plot from the `record/` directory:
```bash
cd record
python plot_gomoku_training.py
```

The program reads `cnn Model record.txt` and reports each model’s performance.  
