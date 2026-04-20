class Card:
    """
    Represents a development card in Splendor.

    Each card has:
    - level: Tier of the card (1, 2, or 3)
    - color_bonus: The permanent gem bonus this card provides after purchase
    - cost: Dictionary of required tokens to buy the card
    - points: Prestige points gained from the card
    """

    def __init__(self, level, color_bonus, cost, points):
        """
        Initialize a Card object.

        :param level: int (1, 2, or 3)
        :param color_bonus: str (e.g., "red", "blue", etc.)
        :param cost: dict (e.g., {"red": 2, "blue": 1})
        :param points: int (prestige points)
        """
        self.level = level
        self.color_bonus = color_bonus
        self.cost = cost
        self.points = points

    def get_cost(self):
        """
        Return the cost of the card.

        :return: dict
        """
        return self.cost

    def get_bonus(self):
        """
        Return the bonus color provided by this card.

        :return: str
        """
        return self.color_bonus

    def get_points(self):
        """
        Return the prestige points of the card.

        :return: int
        """
        return self.points

    def __str__(self):
        """
        Return a readable string representation (useful for debugging).

        :return: str
        """
        return f"Card(Level {self.level}, Bonus: {self.color_bonus}, Cost: {self.cost}, Points: {self.points})"