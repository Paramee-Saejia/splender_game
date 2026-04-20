"""
cards_data.py — Raw card definitions for Splendor.

Each entry is (bonus_color, cost_dict, points).
Level is assigned by which list the entry is in.
"""

# ── Level 1 (40 cards) ──────────────────────────────────────────────────────

LEVEL_1 = [
    # White bonus
    ("white", {"blue": 1, "green": 1, "red": 1, "black": 1}, 0),
    ("white", {"blue": 1, "green": 2, "red": 1, "black": 1}, 0),
    ("white", {"green": 2, "blue": 1},                        0),
    ("white", {"red": 2, "black": 2},                         0),
    ("white", {"red": 2, "green": 1},                         0),
    ("white", {"red": 3},                                     0),
    ("white", {"blue": 1, "red": 1, "black": 3},              0),
    ("white", {"blue": 2, "green": 2, "black": 1},            1),
    # Blue bonus
    ("blue",  {"white": 1, "green": 1, "red": 1, "black": 1}, 0),
    ("blue",  {"white": 1, "green": 1, "red": 2, "black": 1}, 0),
    ("blue",  {"white": 2, "red": 2},                          0),
    ("blue",  {"green": 2, "black": 2},                        0),
    ("blue",  {"white": 1, "black": 2},                        0),
    ("blue",  {"black": 3},                                    0),
    ("blue",  {"white": 3, "green": 1, "red": 1},              0),
    ("blue",  {"white": 2, "red": 1, "black": 2},              1),
    # Green bonus
    ("green", {"white": 1, "blue": 1, "red": 1, "black": 1},  0),
    ("green", {"white": 1, "blue": 2, "red": 1, "black": 1},  0),
    ("green", {"blue": 2, "black": 2},                         0),
    ("green", {"white": 2, "red": 1},                          0),
    ("green", {"white": 2, "blue": 2},                         0),
    ("green", {"blue": 3},                                     0),
    ("green", {"white": 1, "blue": 1, "black": 3},             0),
    ("green", {"white": 1, "blue": 3, "black": 1},             1),
    # Red bonus
    ("red",   {"white": 1, "blue": 1, "green": 1, "black": 1}, 0),
    ("red",   {"white": 2, "blue": 1, "green": 1, "black": 1}, 0),
    ("red",   {"white": 2, "blue": 2},                          0),
    ("red",   {"blue": 2, "green": 1},                          0),
    ("red",   {"green": 1, "black": 2},                         0),
    ("red",   {"white": 3},                                     0),
    ("red",   {"blue": 1, "green": 3, "black": 1},              0),
    ("red",   {"blue": 2, "green": 1, "black": 2},              1),
    # Black bonus
    ("black", {"white": 1, "blue": 1, "green": 1, "red": 1},  0),
    ("black", {"white": 1, "blue": 1, "green": 2, "red": 1},  0),
    ("black", {"white": 2, "green": 2},                        0),
    ("black", {"white": 1, "green": 2},                        0),
    ("black", {"red": 2, "white": 1},                          0),
    ("black", {"green": 3},                                    0),
    ("black", {"white": 1, "green": 1, "red": 3},              0),
    ("black", {"white": 2, "green": 2, "blue": 1},             1),
]

# ── Level 2 (30 cards) ──────────────────────────────────────────────────────

LEVEL_2 = [
    # White bonus
    ("white", {"blue": 3, "green": 2, "red": 2},           1),
    ("white", {"blue": 3, "red": 2, "black": 3},            2),
    ("white", {"blue": 1, "green": 4, "red": 2},            2),
    ("white", {"black": 5},                                  3),
    ("white", {"blue": 2, "green": 3, "red": 3},            1),
    ("white", {"green": 4, "red": 1, "black": 2},           2),
    # Blue bonus
    ("blue",  {"white": 2, "green": 2, "red": 3},           1),
    ("blue",  {"white": 3, "green": 3, "black": 2},         2),
    ("blue",  {"white": 4, "red": 2, "black": 1},           2),
    ("blue",  {"white": 5},                                  3),
    ("blue",  {"white": 3, "green": 2, "black": 3},         1),
    ("blue",  {"white": 4, "green": 2, "red": 1},           2),
    # Green bonus
    ("green", {"white": 3, "blue": 2, "red": 2},            1),
    ("green", {"white": 3, "blue": 2, "black": 3},          2),
    ("green", {"blue": 4, "red": 2, "black": 1},            2),
    ("green", {"red": 5},                                    3),
    ("green", {"white": 2, "blue": 3, "black": 3},          1),
    ("green", {"blue": 4, "red": 1, "black": 2},            2),
    # Red bonus
    ("red",   {"white": 1, "blue": 3, "green": 2, "black": 2}, 1),
    ("red",   {"white": 2, "blue": 3, "black": 3},             2),
    ("red",   {"white": 2, "green": 1, "black": 4},            2),
    ("red",   {"green": 5},                                     3),
    ("red",   {"white": 2, "blue": 1, "green": 4},             2),
    ("red",   {"white": 1, "blue": 2, "green": 4},             2),
    # Black bonus
    ("black", {"blue": 2, "green": 2, "red": 3},            1),
    ("black", {"blue": 3, "green": 3, "white": 2},          2),
    ("black", {"green": 4, "red": 2, "white": 1},           2),
    ("black", {"blue": 5},                                   3),
    ("black", {"white": 3, "blue": 3, "green": 2},          1),
    ("black", {"green": 2, "red": 4, "white": 1},           2),
]

# ── Level 3 (20 cards) ──────────────────────────────────────────────────────

LEVEL_3 = [
    # White bonus
    ("white", {"blue": 3, "green": 3, "red": 3, "black": 5}, 3),
    ("white", {"blue": 7},                                    4),
    ("white", {"blue": 6, "green": 3, "black": 3},           4),
    ("white", {"green": 3, "red": 3, "black": 6},            5),
    # Blue bonus
    ("blue",  {"white": 3, "green": 3, "red": 5, "black": 3}, 3),
    ("blue",  {"white": 7},                                    4),
    ("blue",  {"white": 6, "red": 3, "black": 3},             4),
    ("blue",  {"white": 3, "green": 3, "red": 6},             5),
    # Green bonus
    ("green", {"white": 3, "blue": 3, "red": 3, "black": 5}, 3),
    ("green", {"red": 7},                                     4),
    ("green", {"blue": 3, "red": 6, "black": 3},             4),
    ("green", {"white": 3, "blue": 3, "black": 6},           5),
    # Red bonus
    ("red",   {"white": 3, "blue": 5, "green": 3, "black": 3}, 3),
    ("red",   {"green": 7},                                     4),
    ("red",   {"white": 3, "green": 6, "black": 3},            4),
    ("red",   {"white": 3, "blue": 6, "green": 3},             5),
    # Black bonus
    ("black", {"white": 5, "blue": 3, "green": 3, "red": 3}, 3),
    ("black", {"white": 7},                                   4),
    ("black", {"white": 6, "blue": 3, "green": 3},           4),
    ("black", {"blue": 3, "green": 6, "red": 3},             5),
]

# ── Noble tiles (10 tiles; game picks 3 randomly for 2-player) ──────────────

NOBLES = [
    ({"red": 4, "green": 4},           3),
    ({"white": 4, "blue": 4},          3),
    ({"blue": 4, "black": 4},          3),
    ({"white": 4, "red": 4},           3),
    ({"green": 4, "black": 4},         3),
    ({"white": 3, "blue": 3, "green": 3},  3),
    ({"white": 3, "blue": 3, "black": 3},  3),
    ({"blue": 3, "red": 3, "black": 3},    3),
    ({"white": 3, "red": 3, "black": 3},   3),
    ({"white": 3, "green": 3, "red": 3},   3),
]
