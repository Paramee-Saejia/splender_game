import unittest
from game_component.Tokenbank import TokenBank


class TestTokenBankInit(unittest.TestCase):

    def test_default_2player_counts(self):
        bank = TokenBank()
        for color in ("white", "blue", "green", "red", "black"):
            self.assertEqual(bank.tokens[color], 4)
        self.assertEqual(bank.tokens["gold"], 5)

    def test_custom_token_count(self):
        bank = TokenBank(tokens_per_color=7)
        self.assertEqual(bank.tokens["white"], 7)
        self.assertEqual(bank.tokens["gold"], 5)


class TestTokenBankHasToken(unittest.TestCase):

    def setUp(self):
        self.bank = TokenBank()

    def test_has_token_enough(self):
        self.assertTrue(self.bank.has_token("white", 4))

    def test_has_token_exact(self):
        self.assertTrue(self.bank.has_token("blue", 4))

    def test_has_token_too_many(self):
        self.assertFalse(self.bank.has_token("red", 5))

    def test_has_token_zero_always_true(self):
        self.assertTrue(self.bank.has_token("green", 0))


class TestTokenBankTakeReturn(unittest.TestCase):

    def setUp(self):
        self.bank = TokenBank()

    def test_take_token_success(self):
        result = self.bank.take_token("white")
        self.assertTrue(result)
        self.assertEqual(self.bank.tokens["white"], 3)

    def test_take_token_depletes(self):
        for _ in range(4):
            self.bank.take_token("blue")
        self.assertEqual(self.bank.tokens["blue"], 0)
        self.assertFalse(self.bank.take_token("blue"))

    def test_take_token_multiple(self):
        self.bank.take_token("red", 3)
        self.assertEqual(self.bank.tokens["red"], 1)

    def test_take_token_fails_if_not_enough(self):
        self.assertFalse(self.bank.take_token("green", 5))
        self.assertEqual(self.bank.tokens["green"], 4)  # unchanged

    def test_return_token(self):
        self.bank.take_token("black", 2)
        self.bank.return_token("black", 2)
        self.assertEqual(self.bank.tokens["black"], 4)

    def test_return_tokens_dict(self):
        self.bank.return_tokens({"white": 1, "blue": 2})
        self.assertEqual(self.bank.tokens["white"], 5)
        self.assertEqual(self.bank.tokens["blue"], 6)


class TestTokenBankThreeDistinct(unittest.TestCase):

    def setUp(self):
        self.bank = TokenBank()

    def test_can_take_three_distinct_valid(self):
        self.assertTrue(self.bank.can_take_three_distinct(["white", "blue", "green"]))

    def test_can_take_three_distinct_duplicate_color(self):
        self.assertFalse(self.bank.can_take_three_distinct(["white", "white", "green"]))

    def test_can_take_three_distinct_wrong_count(self):
        self.assertFalse(self.bank.can_take_three_distinct(["white", "blue"]))

    def test_can_take_three_distinct_empty_color(self):
        self.bank.tokens["red"] = 0
        self.assertFalse(self.bank.can_take_three_distinct(["white", "blue", "red"]))

    def test_take_three_distinct_removes_tokens(self):
        self.bank.take_three_distinct(["white", "blue", "green"])
        self.assertEqual(self.bank.tokens["white"], 3)
        self.assertEqual(self.bank.tokens["blue"], 3)
        self.assertEqual(self.bank.tokens["green"], 3)

    def test_take_three_distinct_fails_invalid(self):
        self.assertFalse(self.bank.take_three_distinct(["white", "white", "green"]))


class TestTokenBankTwoSame(unittest.TestCase):

    def setUp(self):
        self.bank = TokenBank()

    def test_can_take_two_same_with_4(self):
        self.assertTrue(self.bank.can_take_two_same("white"))

    def test_cannot_take_two_same_with_3(self):
        self.bank.take_token("white")
        self.assertFalse(self.bank.can_take_two_same("white"))

    def test_take_two_same_removes_tokens(self):
        self.bank.take_two_same("blue")
        self.assertEqual(self.bank.tokens["blue"], 2)

    def test_take_two_same_fails_when_not_enough(self):
        self.bank.take_token("green")
        self.assertFalse(self.bank.take_two_same("green"))
        self.assertEqual(self.bank.tokens["green"], 3)  # unchanged


class TestTokenBankGold(unittest.TestCase):

    def setUp(self):
        self.bank = TokenBank()

    def test_take_gold_success(self):
        self.assertTrue(self.bank.take_gold())
        self.assertEqual(self.bank.tokens["gold"], 4)

    def test_take_gold_until_empty(self):
        for _ in range(5):
            self.bank.take_gold()
        self.assertFalse(self.bank.take_gold())

    def test_get_tokens_returns_copy(self):
        copy = self.bank.get_tokens()
        copy["white"] = 999
        self.assertEqual(self.bank.tokens["white"], 4)


if __name__ == "__main__":
    unittest.main()
