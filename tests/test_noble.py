import unittest
from game_component.noble import Noble


class TestNoble(unittest.TestCase):

    def setUp(self):
        self.noble = Noble({"red": 3, "blue": 3, "white": 3})

    def test_default_points(self):
        self.assertEqual(self.noble.get_points(), 3)

    def test_custom_points(self):
        n = Noble({"red": 4}, points=5)
        self.assertEqual(n.get_points(), 5)

    def test_can_visit_exact(self):
        bonus = {"red": 3, "blue": 3, "white": 3, "green": 0, "black": 0}
        self.assertTrue(self.noble.can_visit(bonus))

    def test_can_visit_more_than_enough(self):
        bonus = {"red": 5, "blue": 4, "white": 3, "green": 2, "black": 1}
        self.assertTrue(self.noble.can_visit(bonus))

    def test_cannot_visit_one_short(self):
        bonus = {"red": 3, "blue": 2, "white": 3, "green": 0, "black": 0}
        self.assertFalse(self.noble.can_visit(bonus))

    def test_cannot_visit_missing_color(self):
        bonus = {"red": 3, "green": 0, "black": 0}
        self.assertFalse(self.noble.can_visit(bonus))

    def test_str(self):
        result = str(self.noble)
        self.assertIn("Noble", result)
        self.assertIn("red", result)


if __name__ == "__main__":
    unittest.main()
