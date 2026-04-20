import unittest
from game_component.card import Card
from game_component.noble import Noble
from game_component.player import Player


def make_card(level=1, bonus="white", cost=None, points=0):
    if cost is None:
        cost = {}
    return Card(level, bonus, cost, points)


class TestPlayerInit(unittest.TestCase):

    def test_initial_tokens_zero(self):
        p = Player("Alice")
        for color in ("white", "blue", "green", "red", "black", "gold"):
            self.assertEqual(p.tokens[color], 0)

    def test_initial_lists_empty(self):
        p = Player("Alice")
        self.assertEqual(p.cards_owned, [])
        self.assertEqual(p.reserved_cards, [])
        self.assertEqual(p.nobles, [])


class TestPlayerTokens(unittest.TestCase):

    def setUp(self):
        self.p = Player("Alice")

    def test_add_token(self):
        self.p.add_token("blue", 3)
        self.assertEqual(self.p.tokens["blue"], 3)

    def test_remove_token_success(self):
        self.p.add_token("red", 2)
        result = self.p.remove_token("red", 2)
        self.assertTrue(result)
        self.assertEqual(self.p.tokens["red"], 0)

    def test_remove_token_not_enough(self):
        self.p.add_token("green", 1)
        result = self.p.remove_token("green", 2)
        self.assertFalse(result)
        self.assertEqual(self.p.tokens["green"], 1)  # unchanged

    def test_total_tokens(self):
        self.p.add_token("white", 2)
        self.p.add_token("blue", 3)
        self.p.add_token("gold", 1)
        self.assertEqual(self.p.total_tokens(), 6)


class TestPlayerBonus(unittest.TestCase):

    def test_bonus_count_empty(self):
        p = Player("Alice")
        bonus = p.get_bonus_count()
        for color in ("white", "blue", "green", "red", "black"):
            self.assertEqual(bonus[color], 0)

    def test_bonus_count_after_buying(self):
        p = Player("Alice")
        p.buy_card(make_card(bonus="red"))
        p.buy_card(make_card(bonus="red"))
        p.buy_card(make_card(bonus="blue"))
        bonus = p.get_bonus_count()
        self.assertEqual(bonus["red"], 2)
        self.assertEqual(bonus["blue"], 1)
        self.assertEqual(bonus["white"], 0)


class TestPlayerPoints(unittest.TestCase):

    def test_points_from_cards(self):
        p = Player("Alice")
        p.buy_card(make_card(points=1))
        p.buy_card(make_card(points=3))
        self.assertEqual(p.get_points(), 4)

    def test_points_from_nobles(self):
        p = Player("Alice")
        p.add_noble(Noble({"red": 3}, points=3))
        p.add_noble(Noble({"blue": 4}, points=3))
        self.assertEqual(p.get_points(), 6)

    def test_points_combined(self):
        p = Player("Alice")
        p.buy_card(make_card(points=2))
        p.add_noble(Noble({"red": 3}, points=3))
        self.assertEqual(p.get_points(), 5)


class TestPlayerReserve(unittest.TestCase):

    def test_can_reserve_initially(self):
        p = Player("Alice")
        self.assertTrue(p.can_reserve())

    def test_reserve_card(self):
        p = Player("Alice")
        card = make_card()
        result = p.reserve_card(card)
        self.assertTrue(result)
        self.assertEqual(len(p.reserved_cards), 1)

    def test_reserve_max_3(self):
        p = Player("Alice")
        for _ in range(3):
            p.reserve_card(make_card())
        self.assertFalse(p.can_reserve())
        result = p.reserve_card(make_card())
        self.assertFalse(result)
        self.assertEqual(len(p.reserved_cards), 3)


class TestPlayerAfford(unittest.TestCase):

    def test_can_afford_with_tokens(self):
        p = Player("Alice")
        p.add_token("blue", 2)
        p.add_token("red", 1)
        card = make_card(cost={"blue": 2, "red": 1})
        self.assertTrue(p.can_afford(card))

    def test_cannot_afford_missing_tokens(self):
        p = Player("Alice")
        p.add_token("blue", 1)
        card = make_card(cost={"blue": 2})
        self.assertFalse(p.can_afford(card))

    def test_can_afford_with_bonus_discount(self):
        p = Player("Alice")
        p.buy_card(make_card(bonus="blue"))  # 1 blue bonus
        p.buy_card(make_card(bonus="blue"))  # 2 blue bonus
        card = make_card(cost={"blue": 2})
        self.assertTrue(p.can_afford(card))  # fully covered by bonus

    def test_can_afford_with_gold_wildcard(self):
        p = Player("Alice")
        p.add_token("blue", 1)
        p.add_token("gold", 1)
        card = make_card(cost={"blue": 2})
        self.assertTrue(p.can_afford(card))  # 1 blue + 1 gold

    def test_cannot_afford_not_enough_gold(self):
        p = Player("Alice")
        p.add_token("gold", 1)
        card = make_card(cost={"blue": 3})
        self.assertFalse(p.can_afford(card))

    def test_can_afford_free_card(self):
        p = Player("Alice")
        card = make_card(cost={})
        self.assertTrue(p.can_afford(card))


class TestPlayerPayForCard(unittest.TestCase):

    def test_pay_exact_tokens(self):
        p = Player("Alice")
        p.add_token("red", 2)
        p.add_token("blue", 1)
        card = make_card(cost={"red": 2, "blue": 1})
        spent = p.pay_for_card(card)
        self.assertIsNotNone(spent)
        self.assertEqual(spent["red"], 2)
        self.assertEqual(spent["blue"], 1)
        self.assertEqual(p.tokens["red"], 0)
        self.assertEqual(p.tokens["blue"], 0)

    def test_pay_with_bonus_reduces_cost(self):
        p = Player("Alice")
        p.buy_card(make_card(bonus="red"))  # 1 red bonus
        p.add_token("red", 1)
        card = make_card(cost={"red": 2})
        spent = p.pay_for_card(card)
        self.assertIsNotNone(spent)
        self.assertEqual(spent["red"], 1)  # only 1 token spent (bonus covers the other)

    def test_pay_with_gold_wildcard(self):
        p = Player("Alice")
        p.add_token("blue", 1)
        p.add_token("gold", 2)
        card = make_card(cost={"blue": 3})
        spent = p.pay_for_card(card)
        self.assertIsNotNone(spent)
        self.assertEqual(spent["blue"], 1)
        self.assertEqual(spent["gold"], 2)

    def test_pay_returns_none_if_cannot_afford(self):
        p = Player("Alice")
        card = make_card(cost={"red": 5})
        result = p.pay_for_card(card)
        self.assertIsNone(result)

    def test_pay_does_not_deduct_on_failure(self):
        p = Player("Alice")
        p.add_token("red", 1)
        card = make_card(cost={"red": 5})
        p.pay_for_card(card)
        self.assertEqual(p.tokens["red"], 1)  # unchanged

    def test_pay_free_card(self):
        p = Player("Alice")
        card = make_card(cost={})
        spent = p.pay_for_card(card)
        self.assertIsNotNone(spent)
        self.assertEqual(sum(spent.values()), 0)


class TestPlayerBuyReserved(unittest.TestCase):

    def test_buy_reserved_card_moves_to_owned(self):
        p = Player("Alice")
        card = make_card()
        p.reserve_card(card)
        result = p.buy_reserved_card(0)
        self.assertIs(result, card)
        self.assertEqual(len(p.reserved_cards), 0)
        self.assertEqual(len(p.cards_owned), 1)

    def test_buy_reserved_invalid_index(self):
        p = Player("Alice")
        result = p.buy_reserved_card(0)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
