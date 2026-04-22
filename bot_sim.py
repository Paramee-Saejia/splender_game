"""
bot_sim.py — Run Bot vs. Bot simulations and log results to CSV.
"""

from game_component.game_factory import create_game
from bot import bot_make_move
from data_logger import DataLogger


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
        while not game.game_over:
            ok = bot_make_move(game)
            if not ok:
                fails += 1
                if fails >= 10:
                    # Unstick a deadlocked game by force-advancing the turn
                    game.current_player_index = (
                        (game.current_player_index + 1) % len(game.players))
                    fails = 0
            else:
                fails = 0
        logger.log(game)
        if on_progress:
            on_progress(i + 1, n)

    return n
