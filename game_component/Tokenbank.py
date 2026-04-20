class TokenBank:
    """
    Represents the central pool of tokens in Splendor.

    Responsible for:
    - Storing available tokens
    - Giving tokens to players
    - Receiving tokens back
    - Validating token-taking rules
    """

    def __init__(self, tokens_per_color=4):
        """
        Initialize the token bank.

        :param tokens_per_color: int, starting count for each non-gold color
                                 (4 for 2-player, 5 for 3-player, 7 for 4-player)
        """
        self.tokens = {
            "white": tokens_per_color,
            "blue":  tokens_per_color,
            "green": tokens_per_color,
            "red":   tokens_per_color,
            "black": tokens_per_color,
            "gold":  5
        }

    # ---------- Basic Operations ----------

    def has_token(self, color, amount=1):
        """
        Check if the bank has enough tokens of a specific color.

        :param color: str
        :param amount: int
        :return: bool
        """
        return self.tokens.get(color, 0) >= amount

    def take_token(self, color, amount=1):
        """
        Remove tokens from the bank.

        :param color: str
        :param amount: int
        :return: bool
        """
        if self.has_token(color, amount):
            self.tokens[color] -= amount
            return True
        return False

    def return_token(self, color, amount=1):
        """
        Return tokens back to the bank.

        :param color: str
        :param amount: int
        """
        self.tokens[color] += amount

    def return_tokens(self, token_dict):
        """
        Return multiple tokens at once.

        :param token_dict: dict
        """
        for color, amount in token_dict.items():
            self.tokens[color] += amount

    # ---------- Taking Rules ----------

    def can_take_three_distinct(self, colors):
        """
        Check if player can take 3 different tokens.

        Rules:
        - Must be 3 different colors
        - Each must have at least 1 available

        :param colors: list[str]
        :return: bool
        """
        if len(colors) != 3:
            return False

        if len(set(colors)) != 3:
            return False

        return all(self.has_token(color, 1) for color in colors)

    def take_three_distinct(self, colors):
        """
        Take 3 different tokens if allowed.

        :param colors: list[str]
        :return: bool
        """
        if self.can_take_three_distinct(colors):
            for color in colors:
                self.tokens[color] -= 1
            return True
        return False

    def can_take_two_same(self, color):
        """
        Check if player can take 2 tokens of the same color.

        Rule:
        - Must have at least 4 tokens of that color in the bank

        :param color: str
        :return: bool
        """
        return self.has_token(color, 4)

    def take_two_same(self, color):
        """
        Take 2 tokens of the same color if allowed.

        :param color: str
        :return: bool
        """
        if self.can_take_two_same(color):
            self.tokens[color] -= 2
            return True
        return False

    def take_gold(self):
        """
        Take 1 gold token (used when reserving a card).

        :return: bool
        """
        if self.has_token("gold", 1):
            self.tokens["gold"] -= 1
            return True
        return False

    # ---------- Utility ----------

    def get_tokens(self):
        """
        Get a copy of current tokens (safe for UI use).

        :return: dict
        """
        return self.tokens.copy()

    def __str__(self):
        """
        String representation (useful for debugging).
        """
        return f"TokenBank({self.tokens})"