import unittest
from game_component.card import Card
from game_component.noble import Noble
from game_component.deck import Deck
from game_component.Tokenbank import TokenBank
from game_component.player import Player
from game_component.game import Board, Game, IDLE, PENDING_RETURN_TOKENS, PENDING_CHOOSE_NOBLE


def make_card(level=1, bonus="white", cost=None, points=0):
    if cost is None:
        cost = {}
    return Card(level, bonus, cost, points)


def make_deck(level, count=8):
    cards = [make_card(level=level) for _ in range(count)]
    return Deck(level, cards)


def make_game(num_nobles=0):
    """Build a minimal Game ready to play (setup already called)."""
    decks = [make_deck(1), make_deck(2), make_deck(3)]
    nobles = [Noble({"red": 3}, points=3) for _ in range(num_nobles)]
    bank = TokenBank()
    board = Board(decks, nobles, bank)
    players = [Player("Alice"), Player("Bob")]
    game = Game(players, board)
    game.setup()
    return game


class TestGameSetup(unittest.TestCase):

    def test_setup_fills_face_up(self):
        game = make_game()
        for deck in game.board.decks:
            self.assertEqual(len(deck.get_face_up_cards()), 4)

    def test_initial_player_is_first(self):
        game = make_game()
        self.assertEqual(game.current_player.name, "Alice")

    def test_initial_state_idle(self):
        game = make_game()
        self.assertFalse(game.is_pending())
        self.assertEqual(game.get_pending_state(), IDLE)

    def test_game_not_over_at_start(self):
        game = make_game()
        self.assertFalse(game.game_over)
        self.assertIsNone(game.winner)


class TestTakeTokens(unittest.TestCase):

    def setUp(self):
        self.game = make_game()

    def test_take_three_distinct(self):
        result = self.game.take_tokens(["white", "blue", "green"])
        self.assertTrue(result)
        p = self.game.players[0]  # Alice took the tokens
        self.assertEqual(p.tokens["white"], 1)
        self.assertEqual(p.tokens["blue"], 1)
        self.assertEqual(p.tokens["green"], 1)

    def test_take_three_distinct_removes_from_bank(self):
        self.game.take_tokens(["white", "blue", "red"])
        bank = self.game.board.token_bank
        self.assertEqual(bank.tokens["white"], 3)
        self.assertEqual(bank.tokens["blue"], 3)
        self.assertEqual(bank.tokens["red"], 3)

    def test_take_two_same(self):
        result = self.game.take_tokens(["white", "white"])
        self.assertTrue(result)
        p = self.game.players[0]
        self.assertEqual(p.tokens["white"], 2)

    def test_take_two_same_not_enough_in_bank(self):
        self.game.board.token_bank.tokens["blue"] = 3  # only 3 left
        result = self.game.take_tokens(["blue", "blue"])
        self.assertFalse(result)

    def test_take_invalid_selection(self):
        result = self.game.take_tokens(["white", "white", "blue"])  # 2 same + 1 diff
        self.assertFalse(result)

    def test_take_tokens_advances_turn(self):
        self.game.take_tokens(["white", "blue", "green"])
        self.assertEqual(self.game.current_player.name, "Bob")

    def test_take_one_token_allowed(self):
        result = self.game.take_tokens(["white"])
        self.assertTrue(result)
        self.assertEqual(self.game.players[0].tokens["white"], 1)


class TestReserveCard(unittest.TestCase):

    def setUp(self):
        self.game = make_game()

    def test_reserve_face_up_card(self):
        result = self.game.reserve_card(1, 0)
        self.assertTrue(result)
        p = self.game.players[0]
        self.assertEqual(len(p.reserved_cards), 1)

    def test_reserve_gives_gold_if_available(self):
        result = self.game.reserve_card(1, 0)
        self.assertTrue(result)
        p = self.game.players[0]
        self.assertEqual(p.tokens["gold"], 1)
        self.assertEqual(self.game.board.token_bank.tokens["gold"], 4)

    def test_reserve_no_gold_when_bank_empty(self):
        self.game.board.token_bank.tokens["gold"] = 0
        self.game.reserve_card(1, 0)
        p = self.game.players[0]
        self.assertEqual(p.tokens["gold"], 0)

    def test_reserve_hidden_card(self):
        result = self.game.reserve_hidden_card(1)
        self.assertTrue(result)
        p = self.game.players[0]
        self.assertEqual(len(p.reserved_cards), 1)

    def test_cannot_reserve_more_than_3(self):
        self.game.reserve_card(1, 0)
        self.game.take_tokens(["white"])   # Bob's turn
        self.game.reserve_card(1, 0)
        self.game.take_tokens(["white"])   # Bob's turn
        self.game.reserve_card(1, 0)
        self.game.take_tokens(["white"])   # Bob's turn
        # Alice has 3 reserved now
        result = self.game.reserve_card(1, 0)
        self.assertFalse(result)

    def test_reserve_invalid_deck_level(self):
        result = self.game.reserve_card(99, 0)
        self.assertFalse(result)

    def test_reserve_invalid_card_index(self):
        result = self.game.reserve_card(1, 99)
        self.assertFalse(result)

    def test_reserve_advances_turn(self):
        self.game.reserve_card(1, 0)
        self.assertEqual(self.game.current_player.name, "Bob")


class TestBuyCard(unittest.TestCase):

    def setUp(self):
        self.game = make_game()

    def _give_player_enough_tokens(self, player, cost):
        for color, amount in cost.items():
            player.add_token(color, amount)

    def test_buy_free_card(self):
        result = self.game.buy_card(1, 0)
        self.assertTrue(result)
        p = self.game.players[0]
        self.assertEqual(len(p.cards_owned), 1)

    def test_buy_card_removes_from_board(self):
        face_up_before = list(self.game.board.decks[0].get_face_up_cards())
        self.game.buy_card(1, 0)
        face_up_after = self.game.board.decks[0].get_face_up_cards()
        self.assertNotIn(face_up_before[0], face_up_after)

    def test_buy_card_with_cost(self):
        cost = {"blue": 2, "red": 1}
        card = make_card(level=1, bonus="white", cost=cost, points=1)
        self.game.board.decks[0].face_up[0] = card
        alice = self.game.players[0]
        self._give_player_enough_tokens(alice, cost)
        result = self.game.buy_card(1, 0)
        self.assertTrue(result)
        self.assertEqual(alice.tokens["blue"], 0)
        self.assertEqual(alice.tokens["red"], 0)

    def test_buy_card_returns_tokens_to_bank(self):
        cost = {"blue": 2}
        card = make_card(cost=cost)
        self.game.board.decks[0].face_up[0] = card
        alice = self.game.players[0]
        alice.add_token("blue", 2)
        bank_before = self.game.board.token_bank.tokens["blue"]
        self.game.buy_card(1, 0)
        self.assertEqual(self.game.board.token_bank.tokens["blue"], bank_before + 2)

    def test_buy_card_cannot_afford(self):
        card = make_card(cost={"red": 5})
        self.game.board.decks[0].face_up[0] = card
        result = self.game.buy_card(1, 0)
        self.assertFalse(result)

    def test_buy_card_advances_turn(self):
        self.game.buy_card(1, 0)
        self.assertEqual(self.game.current_player.name, "Bob")


class TestBuyReservedCard(unittest.TestCase):

    def setUp(self):
        self.game = make_game()

    def test_buy_reserved_card(self):
        self.game.reserve_card(1, 0)    # Alice reserves (turn passes to Bob)
        self.game.take_tokens(["white"])  # Bob's turn
        # Now Alice's turn again — buy reserved card 0
        result = self.game.buy_reserved_card(0)
        self.assertTrue(result)
        alice = self.game.players[0]
        self.assertEqual(len(alice.reserved_cards), 0)
        self.assertEqual(len(alice.cards_owned), 1)

    def test_buy_reserved_invalid_index(self):
        result = self.game.buy_reserved_card(0)
        self.assertFalse(result)

    def test_buy_reserved_returns_tokens_to_bank(self):
        cost = {"blue": 2}
        card = make_card(cost=cost)
        alice = self.game.players[0]
        alice.reserve_card(card)
        alice.add_token("blue", 2)
        bank_before = self.game.board.token_bank.tokens["blue"]
        self.game.buy_reserved_card(0)
        self.assertEqual(self.game.board.token_bank.tokens["blue"], bank_before + 2)


class TestPendingReturnTokens(unittest.TestCase):

    def setUp(self):
        self.game = make_game()

    def _fill_player_tokens(self, player, amount):
        per_color = amount // 5
        for color in ("white", "blue", "green", "red", "black"):
            player.add_token(color, per_color)

    def test_token_limit_triggers_pending(self):
        alice = self.game.players[0]
        self._fill_player_tokens(alice, 10)  # 10 tokens already
        # Taking even 1 more pushes to 11
        self.game.take_tokens(["white"])
        self.assertEqual(self.game.get_pending_state(), PENDING_RETURN_TOKENS)

    def test_resolve_return_token(self):
        alice = self.game.players[0]
        self._fill_player_tokens(alice, 10)
        self.game.take_tokens(["white"])
        result = self.game.resolve_return_token("white")
        self.assertTrue(result)
        self.assertFalse(self.game.is_pending())

    def test_resolve_return_token_wrong_state(self):
        with self.assertRaises(RuntimeError):
            self.game.resolve_return_token("white")

    def test_primary_action_blocked_during_pending(self):
        alice = self.game.players[0]
        self._fill_player_tokens(alice, 10)
        self.game.take_tokens(["white"])
        with self.assertRaises(RuntimeError):
            self.game.take_tokens(["blue"])

    def test_token_returned_to_bank(self):
        alice = self.game.players[0]
        self._fill_player_tokens(alice, 10)
        self.game.take_tokens(["white"])
        bank_before = self.game.board.token_bank.tokens["white"]
        self.game.resolve_return_token("white")
        self.assertEqual(self.game.board.token_bank.tokens["white"], bank_before + 1)


class TestNobleVisit(unittest.TestCase):

    def _make_game_with_qualifying_noble(self):
        """Build a game where Alice can immediately satisfy a noble."""
        decks = [make_deck(1), make_deck(2), make_deck(3)]
        noble = Noble({"white": 1}, points=3)  # needs only 1 white card
        bank = TokenBank()
        board = Board(decks, [noble], bank)
        players = [Player("Alice"), Player("Bob")]
        game = Game(players, board)
        game.setup()
        return game, noble

    def test_noble_auto_visit_on_buy(self):
        game, noble = self._make_game_with_qualifying_noble()
        alice = game.players[0]
        # Give Alice a free card with white bonus
        card = make_card(bonus="white", cost={}, points=0)
        game.board.decks[0].face_up[0] = card
        game.buy_card(1, 0)
        # Noble should be auto-granted (only 1 eligible)
        self.assertIn(noble, alice.nobles)
        self.assertNotIn(noble, game.board.nobles)

    def test_noble_adds_points(self):
        game, noble = self._make_game_with_qualifying_noble()
        card = make_card(bonus="white", cost={})
        game.board.decks[0].face_up[0] = card
        game.buy_card(1, 0)
        self.assertEqual(game.players[0].get_points(), 3)

    def test_noble_choose_pending_when_multiple(self):
        decks = [make_deck(1), make_deck(2), make_deck(3)]
        noble1 = Noble({"white": 1}, points=3)
        noble2 = Noble({"white": 1}, points=3)  # same requirement
        bank = TokenBank()
        board = Board(decks, [noble1, noble2], bank)
        players = [Player("Alice"), Player("Bob")]
        game = Game(players, board)
        game.setup()
        card = make_card(bonus="white", cost={})
        game.board.decks[0].face_up[0] = card
        game.buy_card(1, 0)
        self.assertEqual(game.get_pending_state(), PENDING_CHOOSE_NOBLE)
        self.assertEqual(len(game.get_pending_nobles()), 2)

    def test_resolve_choose_noble(self):
        decks = [make_deck(1), make_deck(2), make_deck(3)]
        noble1 = Noble({"white": 1}, points=3)
        noble2 = Noble({"white": 1}, points=3)
        bank = TokenBank()
        board = Board(decks, [noble1, noble2], bank)
        players = [Player("Alice"), Player("Bob")]
        game = Game(players, board)
        game.setup()
        card = make_card(bonus="white", cost={})
        game.board.decks[0].face_up[0] = card
        game.buy_card(1, 0)
        result = game.resolve_choose_noble(0)
        self.assertTrue(result)
        self.assertFalse(game.is_pending())
        self.assertEqual(len(game.players[0].nobles), 1)
        self.assertEqual(len(game.board.nobles), 1)  # one remains


class TestEndGame(unittest.TestCase):

    def test_win_at_15_points(self):
        game = make_game()
        alice = game.players[0]
        # Give Alice enough points via high-value cards
        for _ in range(5):
            alice.buy_card(make_card(points=3))  # 15 points total
        # Alice's turn: hits 15 — triggers final round, Bob still gets a turn
        game.take_tokens(["white"])
        self.assertFalse(game.game_over)
        # Bob's final turn
        game.take_tokens(["blue"])
        self.assertTrue(game.game_over)
        self.assertEqual(game.winner.name, "Alice")

    def test_no_win_below_15(self):
        game = make_game()
        alice = game.players[0]
        for _ in range(4):
            alice.buy_card(make_card(points=3))  # 12 points
        game.take_tokens(["white"])
        self.assertFalse(game.game_over)

    def test_turn_does_not_advance_after_game_over(self):
        game = make_game()
        alice = game.players[0]
        for _ in range(5):
            alice.buy_card(make_card(points=3))
        game.take_tokens(["white"])   # Alice triggers final round
        game.take_tokens(["blue"])    # Bob finishes — game over
        self.assertTrue(game.game_over)
        prev_index = game.current_player_index
        # Actions after game over must be rejected
        result = game.take_tokens(["green"])
        self.assertFalse(result)
        self.assertEqual(game.current_player_index, prev_index)


class TestTurnOrder(unittest.TestCase):

    def test_turn_alternates(self):
        game = make_game()
        self.assertEqual(game.current_player.name, "Alice")
        game.take_tokens(["white"])
        self.assertEqual(game.current_player.name, "Bob")
        game.take_tokens(["blue"])
        self.assertEqual(game.current_player.name, "Alice")

    def test_round_number_increments(self):
        game = make_game()
        self.assertEqual(game.round_number, 1)
        game.take_tokens(["white"])  # Alice
        game.take_tokens(["blue"])   # Bob
        self.assertEqual(game.round_number, 2)

    def test_get_status_returns_dict(self):
        game = make_game()
        status = game.get_status()
        self.assertIn("round", status)
        self.assertIn("current_player", status)
        self.assertIn("game_over", status)
        self.assertIn("winner", status)
        self.assertIn("scores", status)


if __name__ == "__main__":
    unittest.main()
