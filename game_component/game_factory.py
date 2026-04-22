"""
game_factory.py — Builds a fully initialised 2-player Splendor Game.
"""

import random
from game_component.card import Card
from game_component.noble import Noble
from game_component.deck import Deck
from game_component.Tokenbank import TokenBank
from game_component.player import Player
from game_component.game import Board, Game
from game_component.cards_data import LEVEL_1, LEVEL_2, LEVEL_3, NOBLES


def _build_deck(level, raw_list):
    cards = []
    color_counter = {}
    for bonus, cost, pts in raw_list:
        idx = color_counter.get(bonus, 0)
        color_counter[bonus] = idx + 1
        card = Card(level, bonus, dict(cost), pts)
        card._image_index = idx
        cards.append(card)
    return Deck(level, cards)


def create_game(player_name="You", bot_name="Bot"):
    """
    Create and return a ready-to-play 2-player Game.

    Tokens: 4 per normal colour, 5 gold (2-player rule).
    Nobles: 3 randomly chosen from the 10 available.
    Decks:  shuffled, face-up slots filled.
    """
    decks = [
        _build_deck(1, LEVEL_1),
        _build_deck(2, LEVEL_2),
        _build_deck(3, LEVEL_3),
    ]

    noble_pool = [Noble(dict(req), pts) for req, pts in NOBLES]
    indices = random.sample(range(len(noble_pool)), 3)
    nobles = [noble_pool[i] for i in indices]
    for noble, idx in zip(nobles, indices):
        noble._asset_index = idx

    bank = TokenBank(tokens_per_color=4)

    board = Board(decks, nobles, bank)
    players = [Player(player_name), Player(bot_name)]

    game = Game(players, board)
    game.setup()
    return game
