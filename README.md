# Splendor: Human vs Bot with Statistics Dashboard

## Project Description

- Project by: John Farmer
- Game Genre: Digital Board Game / Strategy

This project is a Python + Pygame adaptation of *Splendor*. The player competes against an AI bot by collecting gem tokens, buying development cards, attracting nobles, and trying to reach 15 prestige points first.

The project also includes a statistics system. Completed matches can be logged to CSV, batch simulations can be run automatically, and the results can be viewed through the in-game dashboard. This makes the project both a playable game and a small gameplay analytics tool.

---

## Installation

To clone this project:

```sh
git clone https://github.com/<username>/<project-name>.git
cd <project-name>
```

To create and run a Python environment for this project:

Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install pygame
```

Mac:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install pygame
```

Notes:
- This repository currently does not include a `requirements.txt` file.

---

## Running Guide

After activating the Python environment, run the game with:

Windows:

```bat
python main.py
```

Mac:

```sh
python3 main.py
```

---

## Tutorial / Usage

1. Launch the game with `python main.py` or `python3 main.py`.
2. On the start screen, choose `Start Game` to begin a Human vs Bot match.
3. During your turn, use the action buttons to:
   - take gem tokens,
   - buy a face-up card,
   - reserve a card,
   - buy a reserved card.
4. Build permanent card bonuses to reduce future card costs.
5. Reach noble requirements to gain extra prestige points automatically.
6. The first player to trigger the end condition at 15 prestige points can win after the final round is resolved.
7. From the menu, choose `View Statistics` to see recorded match summaries.
8. Choose `Run 100 Simulations` to generate more match data automatically.

Extra controls:
- Press `F11` to toggle fullscreen.
- Use the `Back to Menu` button during gameplay to return to the start screen.

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

## Known Bugs

- Some Unicode symbols may appear differently on some systems depending on font availability.
- Fullscreen and window scaling behavior may vary slightly depending on the platform and Pygame version.

---

## Unfinished Works

- A final `requirements.txt` file has not been added yet.
- Proposal PDF, UML PDF, and final presentation links still need to be attached in the repository.
- Final screenshot files for documentation still need to be added.

---

## External Sources

Acknowledge to:

1. Pygame, https://www.pygame.org/ [game framework]
2. Python Standard Library, https://docs.python.org/3/library/ [core modules used in the project]

Asset credits can be added here if your team used any third-party or AI-generated artwork, music, or code references.
