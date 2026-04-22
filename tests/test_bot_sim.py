import os
import tempfile
import unittest
from unittest.mock import patch

from bot_sim import run_simulations
from data_logger import DataLogger
from game_component.game_factory import create_game


class TestBotSim(unittest.TestCase):

    def test_run_simulations_force_finishes_stalled_game(self):
        game = create_game("BotA", "BotB")
        path = os.path.join(tempfile.gettempdir(), "splendor_test_bot_sim.csv")
        if os.path.exists(path):
            os.remove(path)
        logger = DataLogger(path)

        with patch("bot_sim.create_game", return_value=game), \
                patch("bot_sim.bot_make_move", return_value=False):
            done = run_simulations(1, logger=logger)

        self.assertEqual(done, 1)
        self.assertTrue(game.game_over)
        self.assertIsNotNone(game.winner)
        rows = logger.load_all()
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
