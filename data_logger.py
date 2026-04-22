"""
data_logger.py — Append match results to stats/match_log.csv.
"""

import csv
import os
from datetime import datetime

_STATS_DIR = os.path.join(os.path.dirname(__file__), "stats")
CSV_PATH   = os.path.join(_STATS_DIR, "match_log.csv")

FIELDNAMES = [
    "match_id", "timestamp", "total_turns", "winner",
    "winner_score", "loser_score", "score_margin",
    "p1_name", "p1_gold_spent", "p1_tier1", "p1_tier2", "p1_tier3",
    "p1_gem_white", "p1_gem_blue", "p1_gem_green", "p1_gem_red", "p1_gem_black",
    "p2_name", "p2_gold_spent", "p2_tier1", "p2_tier2", "p2_tier3",
    "p2_gem_white", "p2_gem_blue", "p2_gem_green", "p2_gem_red", "p2_gem_black",
]

GEM_COLORS = ["white", "blue", "green", "red", "black"]


class DataLogger:
    def __init__(self, path=CSV_PATH):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w", newline="") as f:
                csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()

    def log(self, game):
        """Append one summary row for a finished Game."""
        ms = game.match_stats
        p1, p2 = game.players[0], game.players[1]
        winner = game.winner
        loser  = p2 if (winner and winner.name == p1.name) else p1
        ws = winner.get_points() if winner else 0
        ls = loser.get_points()

        def gems(p):
            return {c: ms["gems_taken"][p.name].get(c, 0) for c in GEM_COLORS}

        g1, g2 = gems(p1), gems(p2)
        row = {
            "match_id":      self._count_rows() + 1,
            "timestamp":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_turns":   ms["turns"],
            "winner":        winner.name if winner else "draw",
            "winner_score":  ws,
            "loser_score":   ls,
            "score_margin":  ws - ls,
            "p1_name":       p1.name,
            "p1_gold_spent": ms["gold_spent"].get(p1.name, 0),
            "p1_tier1":      ms["tiers_bought"][p1.name].get(1, 0),
            "p1_tier2":      ms["tiers_bought"][p1.name].get(2, 0),
            "p1_tier3":      ms["tiers_bought"][p1.name].get(3, 0),
            **{f"p1_gem_{c}": g1[c] for c in GEM_COLORS},
            "p2_name":       p2.name,
            "p2_gold_spent": ms["gold_spent"].get(p2.name, 0),
            "p2_tier1":      ms["tiers_bought"][p2.name].get(1, 0),
            "p2_tier2":      ms["tiers_bought"][p2.name].get(2, 0),
            "p2_tier3":      ms["tiers_bought"][p2.name].get(3, 0),
            **{f"p2_gem_{c}": g2[c] for c in GEM_COLORS},
        }
        with open(self.path, "a", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES).writerow(row)

    def load_all(self):
        """Return all rows as a list of dicts."""
        if not os.path.exists(self.path):
            return []
        with open(self.path, newline="") as f:
            return list(csv.DictReader(f))

    def _count_rows(self):
        if not os.path.exists(self.path):
            return 0
        with open(self.path) as f:
            return max(0, sum(1 for _ in f) - 1)
