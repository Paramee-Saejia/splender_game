import unittest
from game_component.card import Card


class TestCard(unittest.TestCase):

    def setUp(self):
        self.card = Card(
            level=1,
            color_bonus="red",
            cost={"white": 2, "blue": 1},
            points=0
        )
        self.card_with_points = Card(
            level=3,
            color_bonus="black",
            cost={"red": 4, "white": 3},
            points=5
        )

    def test_level(self):
        self.assertEqual(self.card.level, 1)

    def test_get_bonus(self):
        self.assertEqual(self.card.get_bonus(), "red")

    def test_get_cost(self):
        self.assertEqual(self.card.get_cost(), {"white": 2, "blue": 1})

    def test_get_points_zero(self):
        self.assertEqual(self.card.get_points(), 0)

    def test_get_points_nonzero(self):
        self.assertEqual(self.card_with_points.get_points(), 5)

    def test_str(self):
        result = str(self.card)
        self.assertIn("Level 1", result)
        self.assertIn("red", result)


if __name__ == "__main__":
    unittest.main()
