class Noble:
    """
    Represents a Noble tile in Splendor.

    A Noble gives prestige points when a player has enough
    permanent card bonuses to satisfy its requirement.
    """

    def __init__(self, requirement, points=3):
        """
        Initialize a Noble object.

        :param requirement: dict, required card bonuses
                            example: {"red": 3, "blue": 3, "white": 3}
        :param points: int, prestige points given by this noble
        """
        self.requirement = requirement
        self.points = points

    def can_visit(self, bonus_dict):
        """
        Check whether a player satisfies this noble's requirement.

        :param bonus_dict: dict, player's permanent bonuses
                           example: {"red": 3, "blue": 2, "white": 3, ...}
        :return: bool
        """
        for color, needed_amount in self.requirement.items():
            if bonus_dict.get(color, 0) < needed_amount:
                return False
        return True

    def get_points(self):
        """
        Return the prestige points of this noble.

        :return: int
        """
        return self.points

    def __str__(self):
        """
        Return a readable string representation of the noble.
        """
        return f"Noble(requirement={self.requirement}, points={self.points})"