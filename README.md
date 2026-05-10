# Splendor game

## Project Description

This project is a Python + Pygame adaptation of *Splendor*. The player competes against an AI bot by collecting gem tokens, buying development cards, attracting nobles, and trying to reach 15 prestige points first.

The project also includes a statistics system. Completed matches can be logged to CSV, batch simulations can be run automatically, and the results can be viewed through the in-game dashboard. This makes the project both a playable game and a small gameplay analytics tool.

---

## Installation

Clone or download this repository, then create a Python environment and install the required packages.

Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install pygame matplotlib
```

Mac / Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install pygame matplotlib
```

Notes:
- This repository does not currently include a `requirements.txt` file.
- `matplotlib` is required for the statistics dashboard in `stats_view.py`.

---

## Running Guide

After activating the Python environment, run the game with:

Windows:

```bat
python main.py
```

Mac / Linux:

```sh
python3 main.py
```

---

## Tutorial / Usage

1. Launch the game with `python main.py` or `python3 main.py`.
2. On the start screen, choose `Start Game` to begin a Human vs Bot match.
3. During your turn, use the action buttons to take gem tokens, buy a face-up card, reserve a card, or buy a reserved card.
4. Build permanent card bonuses to reduce future card costs.
5. Reach noble requirements to gain extra prestige points automatically.
6. The first player to trigger the end condition at 15 prestige points can win after the final round is resolved.
7. From the menu, choose `View Statistics` to see recorded match summaries.
8. Choose `Run 100 Simulations` to generate more match data automatically.

Extra controls:
- Press `F11` to toggle fullscreen.
- Use the `Back to Menu` button during gameplay to return to the start screen.
- Use the top tabs in the statistics dashboard to switch between visualization pages.

---

## Game Features

- Full two-player *Splendor* rule implementation
- Human vs Bot gameplay
- Heuristic bot with card evaluation, token planning, and tactical reserve decisions
- Reserve system with gold token handling
- Noble claiming and pending-choice resolution
- In-game statistics dashboard with multiple chart panels
- Bot vs Bot simulation mode for large-scale testing
- CSV-based match logging in `stats/match_log.csv`
- Custom fantasy-themed visual assets for menu, cards, nobles, and tokens

---

## Screenshots and Visualization Files

- Gameplay screenshots should be placed in `screenshots/gameplay/`.
- Data visualization screenshots and explanations are stored in `screenshots/visualization/`.
- The visualization write-up is in `screenshots/visualization/VISUALIZATION.md`.

Current visualization screenshots included in the repository:
- `page1_resources_overview.png`
- `page2_outcomes_overview.png`
- `page3_gold_analysis_overview.png`
- Individual chart/table screenshots for all dashboard components

---

## Project Structure

Key files and folders:
- `main.py`: main Pygame application and UI flow
- `bot.py`: heuristic bot logic
- `bot_sim.py`: batch simulation runner
- `data_logger.py`: match logging and CSV loading
- `stats_view.py`: dashboard rendering with Pygame + Matplotlib
- `stats/match_log.csv`: recorded match summaries
- `screenshots/`: submission screenshots for gameplay and visualization
- `game_component/`: game rules, board setup, cards, nobles, and factory code

---

## Known Issues

- Some Unicode symbols may appear differently on some systems depending on font availability.
- Fullscreen and window scaling behavior may vary slightly depending on the platform and Pygame version.

---

## Submission Notes

- Visualization screenshots and `VISUALIZATION.md` have been added under `screenshots/visualization/`.
- The `screenshots/gameplay/` folder is ready for final gameplay screenshots.
- Proposal PDF, UML PDF, and presentation video links should be added if they are required for final submission.

---

## External Sources

1. Pygame, https://www.pygame.org/ [game framework]
2. Matplotlib, https://matplotlib.org/ [statistics chart rendering]
3. Python Standard Library, https://docs.python.org/3/library/ [core modules used in the project]


