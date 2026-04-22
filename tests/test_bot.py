import unittest

from bot import bot_make_move
from game_component.card import Card
from game_component.deck import Deck
from game_component.game import Board, Game
from game_component.noble import Noble
from game_component.player import Player
from game_component.Tokenbank import TokenBank


def make_card(level=1, bonus="white", cost=None, points=0):
    if cost is None:
        cost = {}
    return Card(level, bonus, cost, points)


def make_game():
    decks = [Deck(1, []), Deck(2, []), Deck(3, [])]
    for deck in decks:
        deck.face_up = [
            make_card(level=deck.level, bonus="white", cost={"white": 6}, points=0)
            for _ in range(4)
        ]
    board = Board(decks, [Noble({"red": 3}, points=3)], TokenBank())
    players = [Player("BotA"), Player("BotB")]
    game = Game(players, board)
    game._init_match_stats()
    return game


class TestBotStrategy(unittest.TestCase):

    def test_bot_reserves_high_value_card_and_takes_gold(self):
        game = make_game()
        target = make_card(level=3, bonus="blue", cost={"blue": 4}, points=4)
        game.board.decks[2].face_up[0] = target

        moved = bot_make_move(game)

        self.assertTrue(moved)
        self.assertIn(target, game.players[0].reserved_cards)
        self.assertEqual(game.players[0].tokens["gold"], 1)
        self.assertNotIn(target, game.board.decks[2].face_up)

    def test_bot_buys_reserved_card_using_gold(self):
        game = make_game()
        player = game.players[0]
        card = make_card(level=2, bonus="red", cost={"blue": 3}, points=2)
        player.reserve_card(card)
        player.add_token("blue", 1)
        player.add_token("gold", 2)

        moved = bot_make_move(game)

        self.assertTrue(moved)
        self.assertEqual(len(player.reserved_cards), 0)
        self.assertIn(card, player.cards_owned)
        self.assertEqual(game.match_stats["gold_spent"][player.name], 2)

    def test_bot_reserves_card_the_opponent_can_buy(self):
        game = make_game()
        player = game.players[0]
        opponent = game.players[1]
        threat = make_card(level=2, bonus="green", cost={"red": 4}, points=2)
        game.board.decks[1].face_up[0] = threat
        opponent.add_token("red", 4)

        moved = bot_make_move(game)

        self.assertTrue(moved)
        self.assertNotIn(threat, game.board.decks[1].face_up)
        self.assertIn(threat, player.reserved_cards)


if __name__ == "__main__":
    unittest.main()
