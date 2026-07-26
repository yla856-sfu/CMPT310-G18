# CMPT310-G18

Main branch

## Run

Install pygame:

```bash
pip install -r requirements.txt
```

## Human VS AI (GUI)

Run the game:

```bash
python main.py
```

The player plays against an AI in the pygame GUI.  
The player can choose AI type before the game starts.  
![GUI](https://i.ibb.co/JFz6LTW7/2.png)  
The player can click restart button to restart game when game is end.  
![GUI](https://i.ibb.co/ynSjN6Ny/GUI.png)  

## AI VS AI

### Run AI testing:

```bash
python TEST.py AI_TYPE_1 AI_TYPE_2 TEST_TIMES WATCH_PROCESS [INTERVAL_SECONDS]
```

Example 1:

```bash
python TEST.py random greedy 100 false
```

Run random AI against greedy AI for 100 games without showing each move.

Example 2:

```bash
python TEST.py greedy greedy 1 true 1
```

Run greedy AI against greedy AI for 1 game, show each move, and wait 1 second between moves.  
  
### Or you can run AI testing with multiprocessing, but this will disable [WATCH_PROCESS] and log.txt save:

```bash
python TEST_mp.py AI_TYPE_1 AI_TYPE_2 TEST_TIMES [WORKERS]
```

Example 1:

```bash
python TEST.py random greedy 100 4
```

Run random AI against greedy AI for 100 games with 4 processing.

