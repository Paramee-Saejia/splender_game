import unittest
from game_component.card import Card
from game_component.deck import Deck


def make_cards(level, count):
    return [Card(level, "white", {"blue": 1}, 0) for _ in range(count)]


class TestDeckInit(unittest.TestCase):

    def test_initial_face_up_empty(self):
        deck = Deck(1, make_cards(1, 10))
        self.assertEqual(len(deck.get_face_up_cards()), 0)

    def test_hidden_count_before_setup(self):
        deck = Deck(1, make_cards(1, 6))
        self.assertEqual(deck.hidden_count(), 6)

    def test_cards_list_is_copy(self):
        cards = make_cards(1, 4)
        deck = Deck(1, cards)
        cards.clear()
        self.assertEqual(deck.hidden_count(), 4)


class TestDeckSetup(unittest.TestCase):

    def setUp(self):
        self.deck = Deck(1, make_cards(1, 10))
        self.deck.shuffle()
        self.deck.setup_face_up()

    def test_setup_fills_four_face_up(self):
        self.assertEqual(len(self.deck.get_face_up_cards()), 4)

    def test_hidden_count_after_setup(self):
        self.assertEqual(self.deck.hidden_count(), 6)

    def test_setup_small_deck(self):
        deck = Deck(1, make_cards(1, 3))
        deck.setup_face_up()
        self.assertEqual(len(deck.get_face_up_cards()), 3)
        self.assertEqual(deck.hidden_count(), 0)


class TestDeckDraw(unittest.TestCase):

    def setUp(self):
        self.deck = Deck(1, make_cards(1, 5))

    def test_draw_returns_card(self):
        card = self.deck.draw()
        self.assertIsNotNone(card)
        self.assertIsInstance(card, Card)

    def test_draw_reduces_hidden_count(self):
        self.deck.draw()
        self.assertEqual(self.deck.hidden_count(), 4)

    def test_draw_empty_deck_returns_none(self):
        deck = Deck(1, [])
        self.assertIsNone(deck.draw())


class TestDeckTakeFaceUp(unittest.TestCase):

    def setUp(self):
        self.deck = Deck(1, make_cards(1, 8))
        self.deck.setup_face_up()  # 4 up, 4 hidden

    def test_take_face_up_returns_card(self):
        card = self.deck.take_face_up_card(0)
        self.assertIsInstance(card, Card)

    def test_take_face_up_refills_from_hidden(self):
        self.deck.take_face_up_card(0)
        self.assertEqual(len(self.deck.get_face_up_cards()), 4)
        self.assertEqual(self.deck.hidden_count(), 3)

    def test_take_face_up_no_refill_when_hidden_empty(self):
        deck = Deck(1, make_cards(1, 4))
        deck.setup_face_up()  # 4 up, 0 hidden
        deck.take_face_up_card(0)
        self.assertEqual(len(deck.get_face_up_cards()), 3)

    def test_take_face_up_invalid_index(self):
        result = self.deck.take_face_up_card(99)
        self.assertIsNone(result)

    def test_take_face_up_negative_index(self):
        result = self.deck.take_face_up_card(-1)
        self.assertIsNone(result)


class TestDeckIsEmpty(unittest.TestCase):

    def test_not_empty_with_cards(self):
        deck = Deck(1, make_cards(1, 4))
        self.assertFalse(deck.is_empty())

    def test_empty_after_draining(self):
        deck = Deck(1, make_cards(1, 2))
        deck.setup_face_up()
        deck.take_face_up_card(0)
        deck.take_face_up_card(0)
        self.assertTrue(deck.is_empty())

    def test_draw_hidden_card_alias(self):
        deck = Deck(1, make_cards(1, 3))
        card = deck.draw_hidden_card()
        self.assertIsNotNone(card)
        self.assertEqual(deck.hidden_count(), 2)


if __name__ == "__main__":
    unittest.main()
