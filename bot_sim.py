"""
bot_sim.py - Run Bot vs. Bot simulations and log results to CSV.
"""

from bot import bot_make_move
from data_logger import DataLogger
from game_component.game_factory import create_game

MAX_STALLED_STEPS = 20
MAX_STEPS_PER_GAME = 2000


def _finish_deadlocked_game(game):
    """Force-finish a stalled game so batch simulations cannot hang forever."""
    game.game_over = True
    game.winner = max(
        game.players,
        key=lambda p: (p.get_points(), -len(p.cards_owned))
    )


def run_simulations(n=100, logger=None, on_progress=None):
    """
    Simulate n Bot vs. Bot games, logging each result.

    :param n:           number of games
    :param logger:      DataLogger; creates default if None
    :param on_progress: optional callback(games_done, total)
    :return:            number of games completed
    """
    if logger is None:
        logger = DataLogger()

    for i in range(n):
        game = create_game("BotA", "BotB")
        fails = 0
        stalled_steps = 0
        steps = 0

        while not game.game_over:
            ok = bot_make_move(game)
            steps += 1

            if not ok:
                fails += 1
                stalled_steps += 1
                if fails >= 10:
                    # Give the other bot a chance, but do not allow infinite loops.
                    game.current_player_index = (
                        (game.current_player_index + 1) % len(game.players)
                    )
                    fails = 0
            else:
                fails = 0
                stalled_steps = 0

            if stalled_steps >= MAX_STALLED_STEPS or steps >= MAX_STEPS_PER_GAME:
                _finish_deadlocked_game(game)
                break

        logger.log(game)
        if on_progress:
            on_progress(i + 1, n)

    return n
