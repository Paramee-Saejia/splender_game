class Player:
    """
    Represents a player in Splendor.

    A player stores:
    - tokens currently owned
    - purchased development cards
    - reserved cards
    - collected nobles
    """

    def __init__(self, name):
        """
        Initialize a Player object.

        :param name: str, player name
        """
        self.name = name

        # Tokens currently owned by the player
        self.tokens = {
            "white": 0,
            "blue": 0,
            "green": 0,
            "red": 0,
            "black": 0,
            "gold": 0
        }

        # Cards the player has already bought
        self.cards_owned = []

        # Cards the player has reserved
        self.reserved_cards = []

        # Nobles the player has received
        self.nobles = []

    def get_bonus_count(self):
        """
        Count permanent bonuses from purchased cards.

        :return: dict, number of bonuses for each color
        """
        bonus = {
            "white": 0,
            "blue": 0,
            "green": 0,
            "red": 0,
            "black": 0
        }

        for card in self.cards_owned:
            bonus[card.color_bonus] += 1

        return bonus

    def get_points(self):
        """
        Calculate total prestige points from cards and nobles.

        :return: int
        """
        card_points = sum(card.points for card in self.cards_owned)
        noble_points = sum(noble.points for noble in self.nobles)
        return card_points + noble_points

    def total_tokens(self):
        """
        Count total tokens currently owned.

        :return: int
        """
        return sum(self.tokens.values())

    def add_token(self, color, amount=1):
        """
        Add tokens to the player.

        :param color: str
        :param amount: int
        """
        self.tokens[color] += amount

    def remove_token(self, color, amount=1):
        """
        Remove tokens from the player if possible.

        :param color: str
        :param amount: int
        :return: bool
        """
        if self.tokens.get(color, 0) >= amount:
            self.tokens[color] -= amount
            return True
        return False

    def can_reserve(self):
        """
        Check whether the player can reserve another card.

        A player can reserve at most 3 cards.

        :return: bool
        """
        return len(self.reserved_cards) < 3

    def reserve_card(self, card):
        """
        Add a card to the reserved list.

        :param card: Card object
        :return: bool
        """
        if self.can_reserve():
            self.reserved_cards.append(card)
            return True
        return False

    def can_afford(self, card):
        """
        Check whether the player can afford a card.

        Permanent bonuses reduce the cost.
        Gold tokens can be used as wild tokens.

        :param card: Card object
        :return: bool
        """
        bonus = self.get_bonus_count()
        gold_needed = 0

        for color, cost_amount in card.cost.items():
            discount = bonus.get(color, 0)
            remaining_cost = max(0, cost_amount - discount)

            if self.tokens.get(color, 0) >= remaining_cost:
                continue
            else:
                shortage = remaining_cost - self.tokens.get(color, 0)
                gold_needed += shortage

        return self.tokens["gold"] >= gold_needed

    def pay_for_card(self, card):
        """
        Pay the cost of a card.

        This method only removes tokens from the player.
        Returning tokens to the TokenBank should be handled in Game logic.

        :param card: Card object
        :return: dict or None
                 Returns a dictionary of tokens spent if payment succeeds.
                 Returns None if player cannot afford the card.
        """
        if not self.can_afford(card):
            return None

        bonus = self.get_bonus_count()
        spent = {
            "white": 0,
            "blue": 0,
            "green": 0,
            "red": 0,
            "black": 0,
            "gold": 0
        }

        for color, cost_amount in card.cost.items():
            discount = bonus.get(color, 0)
            remaining_cost = max(0, cost_amount - discount)

            color_tokens_used = min(self.tokens[color], remaining_cost)
            self.tokens[color] -= color_tokens_used
            spent[color] = color_tokens_used

            remaining_cost -= color_tokens_used

            if remaining_cost > 0:
                self.tokens["gold"] -= remaining_cost
                spent["gold"] += remaining_cost

        return spent

    def buy_card(self, card):
        """
        Buy a card and add it to the player's purchased cards.

        This method assumes payment has already been completed.

        :param card: Card object
        """
        self.cards_owned.append(card)

    def buy_reserved_card(self, index):
        """
        Buy a reserved card by index.

        This method removes the card from reserved_cards and moves it to cards_owned.
        Payment must be handled separately before calling this method.

        :param index: int
        :return: Card object or None
        """
        if 0 <= index < len(self.reserved_cards):
            card = self.reserved_cards.pop(index)
            self.cards_owned.append(card)
            return card
        return None

    def add_noble(self, noble):
        """
        Add a noble to the player.

        :param noble: Noble object
        """
        self.nobles.append(noble)

    def __str__(self):
        """
        Return a readable string representation of the player.
        """
        return (
            f"Player(name={self.name}, "
            f"points={self.get_points()}, "
            f"tokens={self.tokens}, "
            f"cards={len(self.cards_owned)}, "
            f"reserved={len(self.reserved_cards)}, "
            f"nobles={len(self.nobles)})"
        )