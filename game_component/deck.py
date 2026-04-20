import random


class Deck:
    """
    Represents one card deck in Splendor.

    Each deck belongs to one level (Tier 1, 2, or 3) and manages:
    - hidden cards in the deck
    - face-up cards available for purchase or reserve
    """

    def __init__(self, level, cards):
        """
        Initialize a deck.

        :param level: int, deck level (1, 2, or 3)
        :param cards: list of Card objects
        """
        self.level = level
        self.cards = cards[:]      # Make a copy of the input list
        self.face_up = []          # Visible cards on the board

    def shuffle(self):
        """
        Shuffle the hidden cards in the deck.
        """
        random.shuffle(self.cards)

    def draw(self):
        """
        Draw one hidden card from the deck.

        :return: Card object if available, otherwise None
        """
        if len(self.cards) > 0:
            return self.cards.pop()
        return None

    def setup_face_up(self, amount=4):
        """
        Fill the face-up area at the start of the game.

        :param amount: int, number of face-up cards to show
        """
        for _ in range(amount):
            card = self.draw()
            if card is not None:
                self.face_up.append(card)

    def refill_face_up(self):
        """
        Refill the face-up cards until there are 4 cards,
        or until the hidden deck becomes empty.
        """
        while len(self.face_up) < 4 and len(self.cards) > 0:
            card = self.draw()
            if card is not None:
                self.face_up.append(card)

    def take_face_up_card(self, index):
        """
        Take one face-up card by index, then refill the row.

        :param index: int, position in face_up list
        :return: Card object if index is valid, otherwise None
        """
        if 0 <= index < len(self.face_up):
            selected_card = self.face_up.pop(index)
            self.refill_face_up()
            return selected_card
        return None

    def draw_hidden_card(self):
        """
        Draw one card directly from the hidden deck.
        This is used when a player reserves from the deck.

        :return: Card object if available, otherwise None
        """
        return self.draw()

    def get_face_up_cards(self):
        """
        Get the current visible cards.

        :return: list of Card objects
        """
        return self.face_up

    def hidden_count(self):
        """
        Get the number of hidden cards left in the deck.

        :return: int
        """
        return len(self.cards)

    def is_empty(self):
        """
        Check whether both the hidden deck and face-up cards are empty.

        :return: bool
        """
        return len(self.cards) == 0 and len(self.face_up) == 0

    def __str__(self):
        """
        Return a readable string representation of the deck.
        """
        return f"Deck(level={self.level}, hidden={len(self.cards)}, face_up={len(self.face_up)})"