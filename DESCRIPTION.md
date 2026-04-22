# Project Description

## 1. Project Overview

- **Project Name:**  
  Splendor: Human vs Bot with Statistics Dashboard

- **Brief Description:**  
  This project is a digital adaptation of the board game *Splendor*, implemented in Python with Pygame. It allows a human player to play against an AI bot in a two-player match while preserving the core rules of the original game: collecting gem tokens, purchasing development cards, attracting nobles, and racing to 15 prestige points.

  In addition to the main game, the project includes a built-in statistics system. Match results can be logged to CSV, simulated through automated bot-versus-bot games, and visualized through an in-game dashboard. This makes the project both an interactive game and a small data-analysis application.

- **Problem Statement:**  
  The project solves two related problems. First, it provides a playable digital version of *Splendor* for users who want to enjoy the game without setting up the physical board. Second, it helps players analyze gameplay patterns by recording match data and presenting summaries such as gem collection, tier purchases, score margins, and match length.

- **Target Users:**  
  - Students learning object-oriented programming through a game-based project
  - Players who want to play *Splendor* against a computer opponent
  - Users interested in simulation and gameplay statistics
  - Instructors or reviewers who want to inspect class design and rule implementation

- **Key Features:**  
  - Full two-player *Splendor* gameplay with rule validation
  - Human vs Bot mode with a heuristic-based AI opponent
  - Bot vs Bot simulation mode for batch testing
  - Persistent match logging to CSV
  - In-game statistics dashboard with multiple charts
  - Custom fantasy-themed artwork for cards, nobles, tokens, and menu screens

### Screenshots

The repository currently contains the game assets, but screenshot files are not committed yet. Add your final screenshots to the repository and replace the placeholder paths below.

- Gameplay screenshot: `./docs/screenshots/gameplay.png`
- Statistics dashboard screenshot: `./docs/screenshots/statistics-dashboard.png`

Example Markdown once the files are added:

```md
![Gameplay Screenshot](./docs/screenshots/gameplay.png)
![Statistics Dashboard](./docs/screenshots/statistics-dashboard.png)
```

### Proposal

- Proposal PDF: `[Add your proposal PDF link here](./proposal.pdf)`

### Presentation Video

- YouTube presentation link: `[Add your 7-minute presentation here](https://www.youtube.com/)`

The presentation should include:
- A short introduction and demonstration of both the game and the statistics system
- An explanation of the class design and how the classes are used together
- An explanation of the recorded statistics and data visualization

---

## 2. Concept

### 2.1 Background

This project exists because board games are an excellent way to practice object-oriented programming. *Splendor* has a clear rule system, several interacting game objects, and meaningful state transitions, which make it a strong case study for class design, composition, and rule enforcement.

The project was inspired by the original *Splendor* board game and by the idea of combining a playable game with post-game analysis. Instead of only recreating the board game, the system also records data from every match and presents it visually inside the application. This adds educational value because it connects game programming with data collection and visualization.

The problem is important because game projects are often judged only by whether they are playable. In this project, the goal is broader: to show that a well-structured software system can support gameplay, AI decision-making, simulation, persistent records, and statistics dashboards in one integrated application.

### 2.2 Objectives

- Implement a rule-correct two-player *Splendor* game in Python
- Design the system using object-oriented principles with clear class responsibilities
- Support human-versus-bot play in a responsive GUI
- Create an AI bot that can make practical decisions instead of random moves
- Record match outcomes and gameplay features automatically
- Visualize recorded data in a way that helps users understand how games evolve
- Demonstrate software design, data handling, and user interface development in one project

---

## 3. UML Class Diagram

### UML PDF Attachment

- UML Class Diagram PDF: `[Add UML PDF here](./docs/uml-class-diagram.pdf)`

### UML Preview (Mermaid)

```mermaid
classDiagram
    class Card {
        +int level
        +str color_bonus
        +dict cost
        +int points
        +get_cost()
        +get_bonus()
        +get_points()
    }

    class Noble {
        +dict requirement
        +int points
        +can_visit(bonus_dict)
        +get_points()
    }

    class Deck {
        +int level
        +list cards
        +list face_up
        +shuffle()
        +draw()
        +setup_face_up()
        +refill_face_up()
        +take_face_up_card(index)
        +draw_hidden_card()
        +get_face_up_cards()
    }

    class TokenBank {
        +dict tokens
        +has_token(color, amount)
        +take_token(color, amount)
        +return_token(color, amount)
        +can_take_three_distinct(colors)
        +take_three_distinct(colors)
        +can_take_two_same(color)
        +take_two_same(color)
        +take_gold()
        +get_tokens()
    }

    class Player {
        +str name
        +dict tokens
        +list cards_owned
        +list reserved_cards
        +list nobles
        +get_bonus_count()
        +get_points()
        +total_tokens()
        +can_reserve()
        +reserve_card(card)
        +can_afford(card)
        +pay_for_card(card)
        +buy_card(card)
        +buy_reserved_card(index)
        +add_noble(noble)
    }

    class Board {
        +list decks
        +list nobles
        +TokenBank token_bank
    }

    class Game {
        +list players
        +Board board
        +int current_player_index
        +int round_number
        +bool game_over
        +Player winner
        +dict match_stats
        +setup()
        +take_tokens(colors)
        +reserve_card(deck_level, card_index)
        +reserve_hidden_card(deck_level)
        +buy_card(deck_level, card_index)
        +buy_reserved_card(reserved_index)
        +resolve_return_token(color)
        +resolve_choose_noble(noble_index)
        +get_status()
    }

    class DataLogger {
        +str path
        +log(game)
        +load_all()
    }

    class SplendorApp {
        +dict assets
        +dict fonts
        +str mode
        +Game game
        +run()
    }

    class FlyToken
    class FlyCard
    class Toast
    class UM

    Board *-- Deck
    Board *-- Noble
    Board *-- TokenBank
    Game *-- Board
    Game *-- Player
    Player --> Card : owns
    Player --> Card : reserves
    Player --> Noble : collects
    Deck --> Card : contains
    DataLogger ..> Game : logs
    SplendorApp --> Game : controls
    SplendorApp --> DataLogger : reads/writes stats
    SplendorApp --> FlyToken
    SplendorApp --> FlyCard
    SplendorApp --> Toast
    SplendorApp --> UM
```

---

## 4. Object-Oriented Programming Implementation

The project applies object-oriented programming by separating the game into small, focused classes. Each class has a clear responsibility and collaborates with the others through composition rather than putting all logic into one file.

- **Card:** Represents one development card, including tier, permanent bonus color, purchase cost, and prestige points.
- **Noble:** Represents a noble tile and checks whether a player has enough permanent bonuses to claim it.
- **Deck:** Manages one level of development cards, including hidden cards and face-up cards on the board.
- **TokenBank:** Stores the shared token supply and validates token-taking rules.
- **Player:** Stores each player's tokens, purchased cards, reserved cards, nobles, and payment logic.
- **Board:** Groups the shared resources of a match, including decks, nobles, and the token bank.
- **Game:** Acts as the main rules engine. It validates actions, controls turns, handles pending states, awards nobles, tracks match statistics, and determines the winner.
- **DataLogger:** Writes completed match summaries to `stats/match_log.csv` and reloads historical data for the dashboard.
- **SplendorApp:** Controls the Pygame application, screen states, rendering, input handling, bot turns, simulation triggers, and transitions between menu, gameplay, and statistics screens.
- **FlyToken:** Handles token movement animation after token-taking actions.
- **FlyCard:** Handles simple card animation effects in the interface.
- **Toast:** Displays temporary on-screen feedback messages.
- **UM:** Stores UI mode constants used by the application state machine.

The project also includes supporting function-based modules:

- **`bot.py`:** Heuristic AI behavior for the bot player
- **`bot_sim.py`:** Batch simulation runner for bot-versus-bot matches
- **`stats_view.py`:** In-game Pygame dashboard rendering
- **`game_factory.py`:** Factory function that assembles a ready-to-play game
- **`cards_data.py`:** Raw card and noble definitions used to build the board

---

## 5. Statistical Data

### 5.1 Data Recording Method

Match data is recorded automatically at the end of each completed game through the `DataLogger` class. The logger appends one row per match to `stats/match_log.csv`. The system supports both manually played Human vs Bot matches and automated Bot vs Bot simulations.

Each row stores summary information about the match, including:

- Match ID and timestamp
- Total number of turns
- Winner name
- Winner score, loser score, and score margin
- Per-player gold token usage
- Per-player number of purchased cards by tier
- Per-player gem collection totals by color

The `Game` class prepares `match_stats` during gameplay, and `DataLogger` converts those in-memory statistics into a persistent CSV record.

### 5.2 Data Features

The recorded data is structured, numeric, and match-based. It supports summary analysis, comparison between players, and repeated simulation experiments.

Key data features include:

- **Turn count:** Measures how long each match lasts
- **Winner and score margin:** Shows match competitiveness
- **Tier purchases:** Indicates strategic preference for low-, mid-, or high-tier cards
- **Gem collection by color:** Shows resource demand across matches
- **Gold spent:** Helps measure how often wildcard tokens contribute to successful purchases
- **Repeated simulation support:** Makes it possible to analyze trends over many bot-played matches

The statistics are visualized through the in-game dashboard in `stats_view.py`, including gem collection, tier purchases, score margin distribution, gold usage, and turns-per-match views.

---

## 6. Changed Proposed Features

Compared with a typical initial proposal for a digital board game, the final project includes several practical extensions:

- A stronger heuristic bot instead of a simple random or greedy opponent
- Automated bot-versus-bot simulation for generating larger datasets
- A dedicated in-game statistics dashboard
- Custom card, noble, token, and menu artwork integrated into the UI

These changes were made to improve both gameplay quality and the analytical value of the project.

An earlier browser-dashboard experiment was not carried into the final version. The final project keeps the integrated in-game statistics dashboard as the main visualization interface.

---

## 7. External Sources

The project uses the following external libraries and technologies:

- **Pygame**  
  Used for the main game window, rendering, input handling, and animation  
  Source: https://www.pygame.org/  
  License: LGPL

- **Python Standard Library**  
  Modules such as `csv`, `datetime`, `math`, `os`, `random`, `sys`, `threading`, and `traceback` are used throughout the project  
  Source: https://docs.python.org/3/library/

### Artwork and Media Credits

Add your final asset credits here if your submission includes any material created outside your team, such as:

- AI-generated images
- Third-party artwork
- Music or sound effects
- Reused code snippets

### Tutorial Video References and Copyright

The start screen includes optional links to external YouTube tutorial videos for players who want to learn the rules of *Splendor*. These videos are not included, copied, downloaded, or redistributed in this repository. They remain the copyrighted property of their respective creators on YouTube, and this project only provides external reference links for educational and gameplay guidance.

- **Asset/Material:** Splendor tutorial video (English)  
- **Creator / Source:** YouTube creator / original uploader  
- **Link:** https://youtu.be/rue8-jvbc9I?si=TfT2SNTgTbRNzR7f  
- **License / Permission:** External reference link only; copyright remains with the original creator

- **Asset/Material:** Splendor tutorial video (Thai)  
- **Creator / Source:** YouTube creator / original uploader  
- **Link:** https://youtu.be/C-ZkrifmcOg?si=GCs8B34I-2TOsIeY  
- **License / Permission:** External reference link only; copyright remains with the original creator

Suggested format:

- **Asset/Material:**  
- **Creator / Source:**  
- **Link:**  
- **License / Permission:**  
