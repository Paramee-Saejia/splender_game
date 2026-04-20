"""
game.py  –  Game controller for Splendor
=========================================
Coordinates turn order, action validation, and rule enforcement.
Does NOT handle UI, rendering, images, or pygame drawing.

Pending-state machine
---------------------
After a normal action the game may enter one of two pending states before
the turn is officially over:

  PENDING_RETURN_TOKENS
      The current player holds more than 10 tokens.
      They must call `resolve_return_token()` one or more times until their
      total drops to ≤ 10, then the noble-check / turn-end proceeds.

  PENDING_CHOOSE_NOBLE
      The current player qualifies for more than one noble at once.
      They must call `resolve_choose_noble()` with the chosen noble index
      to accept exactly one noble before the turn ends.

While in a pending state all normal action methods (take_tokens,
reserve_card, buy_card) are blocked and return False / raise RuntimeError.
"""

# ── Pending state constants ────────────────────────────────────────────────
IDLE                  = "IDLE"
PENDING_RETURN_TOKENS = "PENDING_RETURN_TOKENS"
PENDING_CHOOSE_NOBLE  = "PENDING_CHOOSE_NOBLE"

# Victory threshold (official Splendor rule)
VICTORY_POINTS = 15


class Board:
    """
    Lightweight container for the shared game resources.

    Holds:
    - decks       : list of Deck objects (one per level, usually 3)
    - nobles      : list of Noble objects still on the board
    - token_bank  : TokenBank object
    """

    def __init__(self, decks, nobles, token_bank):
        """
        :param decks:       list of Deck objects
        :param nobles:      list of Noble objects
        :param token_bank:  TokenBank object
        """
        self.decks = decks
        self.nobles = nobles
        self.token_bank = token_bank

    def __str__(self):
        deck_info = ", ".join(
            f"L{d.level}({d.hidden_count()} hidden, {len(d.get_face_up_cards())} up)"
            for d in self.decks
        )
        noble_info = ", ".join(str(n) for n in self.nobles)
        return (
            f"Board(decks=[{deck_info}], "
            f"nobles=[{noble_info}], "
            f"bank={self.token_bank})"
        )


class Game:
    """
    Controls the full flow of a Splendor game.

    Responsibilities:
    - Maintain turn order
    - Validate and execute player actions
    - Enforce official Splendor rules (token limits, noble visits, etc.)
    - Detect end-of-game conditions
    - Manage pending follow-up decisions (token return, noble selection)
    """

    def __init__(self, players, board):
        """
        Initialize the game.

        :param players: list of Player objects (2–4 players)
        :param board:   Board object containing decks, nobles, and token_bank
        """
        self.players = players
        self.board = board

        self.current_player_index = 0   # Index into self.players
        self.round_number = 1           # Increments after all players finish a round
        self.game_over = False
        self.winner = None

        # ── Pending follow-up state ────────────────────────────────────────
        # What the current player still needs to do before the turn ends.
        self._pending_state = IDLE

        # List of Noble objects the player may currently choose from.
        # Populated when the player qualifies for > 1 noble simultaneously.
        self._pending_nobles = []

    # ══════════════════════════════════════════════════════════════════════
    #  Properties / Helpers
    # ══════════════════════════════════════════════════════════════════════

    @property
    def current_player(self):
        """Return the Player whose turn it currently is."""
        return self.players[self.current_player_index]

    def is_pending(self):
        """Return True if the game is waiting for a follow-up decision."""
        return self._pending_state != IDLE

    def get_pending_state(self):
        """Return the current pending state string (useful for UI)."""
        return self._pending_state

    def get_pending_nobles(self):
        """
        Return the list of nobles the current player may choose from.
        Only meaningful when pending state is PENDING_CHOOSE_NOBLE.

        :return: list of Noble objects
        """
        return list(self._pending_nobles)

    # ══════════════════════════════════════════════════════════════════════
    #  Setup
    # ══════════════════════════════════════════════════════════════════════

    def setup(self):
        """
        Prepare the board for a new game.

        Shuffles all decks and fills their face-up slots.
        Call this once before the first turn.
        """
        for deck in self.board.decks:
            deck.shuffle()
            deck.setup_face_up()

    # ══════════════════════════════════════════════════════════════════════
    #  Guard helper
    # ══════════════════════════════════════════════════════════════════════

    def _require_idle(self):
        """
        Raise RuntimeError if a pending follow-up is unresolved.

        Call this at the start of every primary action method.
        """
        if self._pending_state != IDLE:
            raise RuntimeError(
                f"Cannot perform a new action while in pending state: "
                f"{self._pending_state}. "
                f"Resolve the pending action first."
            )

    # ══════════════════════════════════════════════════════════════════════
    #  Primary Actions  (one per turn)
    # ══════════════════════════════════════════════════════════════════════

    def take_tokens(self, colors):
        """
        Action: Take tokens from the bank.

        Supports two official Splendor token-taking rules:
          • Take up to 3 different-colored tokens (1 each), provided the
            bank has at least 1 of each chosen color.
          • Take 2 tokens of the same color, provided the bank has ≥ 4 of
            that color.

        After taking, if the player exceeds 10 tokens the turn enters
        PENDING_RETURN_TOKENS state.

        :param colors: list[str]
                       - For 3-distinct: e.g. ["red", "blue", "green"]
                       - For 2-same:     e.g. ["red", "red"]
        :return: bool – True if the action was successful
        """
        self._require_idle()

        bank = self.board.token_bank
        player = self.current_player

        # ── Determine action type ─────────────────────────────────────────
        if len(colors) == 2 and colors[0] == colors[1]:
            # Two tokens of the same color
            color = colors[0]
            if not bank.take_two_same(color):
                return False   # Bank doesn't have ≥ 4 of this color
            player.add_token(color, 2)

        elif 1 <= len(colors) <= 3 and len(set(colors)) == len(colors):
            # Up to 3 distinct colors
            # Allow taking fewer than 3 only when fewer options exist in bank
            available_colors = [
                c for c, amt in bank.tokens.items()
                if c != "gold" and amt >= 1
            ]
            max_takeable = min(3, len(available_colors))

            if len(colors) < max_takeable:
                # Player tried to take fewer distinct tokens than they could
                # TODO: decide if this should be an error or a permitted shortfall
                pass  # Permit it for flexibility; UI should enforce the max

            if not bank.can_take_three_distinct(colors) and len(colors) == 3:
                return False
            if len(colors) == 3 and not bank.take_three_distinct(colors):
                return False
            elif len(colors) < 3:
                # Take fewer than 3 distinct tokens individually
                for c in colors:
                    if not bank.take_token(c):
                        # Roll back tokens already taken this loop
                        for already_taken in colors[:colors.index(c)]:
                            bank.return_token(already_taken)
                        return False
            for c in colors:
                player.add_token(c)

        else:
            # Invalid selection
            return False

        # ── Post-action: check token limit ────────────────────────────────
        self._after_action()
        return True

    def reserve_card(self, deck_level, card_index):
        """
        Action: Reserve a face-up card from a deck by level and index.

        The player receives 1 gold token if the bank has one available.
        The card is removed from the face-up area and the deck refills.
        After reserving, if the player exceeds 10 tokens the turn enters
        PENDING_RETURN_TOKENS state.

        :param deck_level:  int, deck level (1, 2, or 3)
        :param card_index:  int, index in that deck's face_up list
        :return: bool
        """
        self._require_idle()

        player = self.current_player

        if not player.can_reserve():
            return False   # Already has 3 reserved cards

        deck = self._get_deck(deck_level)
        if deck is None:
            return False

        card = deck.take_face_up_card(card_index)
        if card is None:
            return False

        player.reserve_card(card)

        # Give 1 gold to the player if the bank has one
        if self.board.token_bank.take_gold():
            player.add_token("gold", 1)

        # ── Post-action: check token limit ────────────────────────────────
        self._after_action()
        return True

    def reserve_hidden_card(self, deck_level):
        """
        Action: Reserve a hidden card from the top of a deck.

        Same gold and pending rules as reserve_card().

        :param deck_level: int, deck level (1, 2, or 3)
        :return: bool
        """
        self._require_idle()

        player = self.current_player

        if not player.can_reserve():
            return False

        deck = self._get_deck(deck_level)
        if deck is None:
            return False

        card = deck.draw_hidden_card()
        if card is None:
            return False

        player.reserve_card(card)

        if self.board.token_bank.take_gold():
            player.add_token("gold", 1)

        self._after_action()
        return True

    def buy_card(self, deck_level, card_index):
        """
        Action: Buy a face-up card from the board.

        Payment is handled by Player.pay_for_card(); spent tokens are
        returned to the bank here in Game.

        After purchasing, nobles are checked.  If the player qualifies for
        multiple nobles the turn enters PENDING_CHOOSE_NOBLE state.

        :param deck_level:  int, deck level (1, 2, or 3)
        :param card_index:  int, index in that deck's face_up list
        :return: bool
        """
        self._require_idle()

        player = self.current_player

        deck = self._get_deck(deck_level)
        if deck is None:
            return False

        face_up = deck.get_face_up_cards()
        if not (0 <= card_index < len(face_up)):
            return False

        card = face_up[card_index]

        spent = player.pay_for_card(card)
        if spent is None:
            return False   # Player cannot afford the card

        # Remove the card from the board and refill
        deck.take_face_up_card(card_index)   # Discards and refills

        # The card is already added to cards_owned inside pay_for_card,
        # BUT pay_for_card only removes tokens – it does NOT add the card.
        # buy_card() on Player only records ownership; payment was above.
        player.buy_card(card)

        # Return spent tokens to bank
        self.board.token_bank.return_tokens(spent)

        # ── Post-action: check nobles then end turn ───────────────────────
        self._after_action()
        return True

    def buy_reserved_card(self, reserved_index):
        """
        Action: Buy one of the player's own reserved cards.

        :param reserved_index: int, index in player.reserved_cards
        :return: bool
        """
        self._require_idle()

        player = self.current_player

        if not (0 <= reserved_index < len(player.reserved_cards)):
            return False

        card = player.reserved_cards[reserved_index]

        spent = player.pay_for_card(card)
        if spent is None:
            return False

        # Remove from reserved and add to owned
        player.buy_reserved_card(reserved_index)

        # Return spent tokens to bank
        self.board.token_bank.return_tokens(spent)

        self._after_action()
        return True

    # ══════════════════════════════════════════════════════════════════════
    #  Pending Follow-up Resolutions
    # ══════════════════════════════════════════════════════════════════════

    def resolve_return_token(self, color):
        """
        Resolution: Return one token of the given color back to the bank.

        Must only be called when pending state is PENDING_RETURN_TOKENS.
        After this call, if the player still has > 10 tokens the state
        remains PENDING_RETURN_TOKENS.  Once they are at ≤ 10 the game
        proceeds to the noble-check phase.

        :param color: str, color of the token to return (gold is allowed)
        :return: bool – True if token was successfully returned
        """
        if self._pending_state != PENDING_RETURN_TOKENS:
            raise RuntimeError(
                "resolve_return_token() called outside of PENDING_RETURN_TOKENS state."
            )

        player = self.current_player

        if not player.remove_token(color):
            return False   # Player does not have a token of that color

        self.board.token_bank.return_token(color)

        if player.total_tokens() <= 10:
            # Token limit satisfied – proceed to noble check
            self._pending_state = IDLE
            self._check_nobles_and_end_turn()

        # If still > 10, remain in PENDING_RETURN_TOKENS
        return True

    def resolve_choose_noble(self, noble_index):
        """
        Resolution: Accept one noble from the list of eligible nobles.

        Must only be called when pending state is PENDING_CHOOSE_NOBLE.
        The chosen noble is removed from the board and given to the player.
        All other eligible nobles remain on the board.
        After this the turn ends.

        :param noble_index: int, index into get_pending_nobles()
        :return: bool
        """
        if self._pending_state != PENDING_CHOOSE_NOBLE:
            raise RuntimeError(
                "resolve_choose_noble() called outside of PENDING_CHOOSE_NOBLE state."
            )

        if not (0 <= noble_index < len(self._pending_nobles)):
            return False

        chosen_noble = self._pending_nobles[noble_index]

        # Remove the chosen noble from the board
        self.board.nobles.remove(chosen_noble)

        # Give it to the player
        self.current_player.add_noble(chosen_noble)

        # Clear pending state and end the turn
        self._pending_nobles = []
        self._pending_state = IDLE
        self._end_turn()
        return True

    # ══════════════════════════════════════════════════════════════════════
    #  Internal Flow Helpers
    # ══════════════════════════════════════════════════════════════════════

    def _after_action(self):
        """
        Called immediately after every primary action completes.

        Order of checks:
        1. If the player holds > 10 tokens → enter PENDING_RETURN_TOKENS.
        2. Otherwise → run the noble check and end/pend the turn.
        """
        player = self.current_player

        if player.total_tokens() > 10:
            # Rule: the player may temporarily exceed 10 tokens after an action,
            # but must return tokens until they hold ≤ 10 before the turn ends.
            self._pending_state = PENDING_RETURN_TOKENS
        else:
            self._check_nobles_and_end_turn()

    def _check_nobles_and_end_turn(self):
        """
        Check which nobles the current player is now eligible for.

        - If exactly one noble qualifies  → automatically give it and end turn.
        - If more than one noble qualifies → enter PENDING_CHOOSE_NOBLE.
        - If none qualify                  → end turn immediately.
        """
        player = self.current_player
        bonus = player.get_bonus_count()

        eligible = [
            noble for noble in self.board.nobles
            if noble.can_visit(bonus)
        ]

        if len(eligible) == 0:
            # No noble visits → end the turn
            self._end_turn()

        elif len(eligible) == 1:
            # Exactly one noble → automatic visit (no choice needed)
            noble = eligible[0]
            self.board.nobles.remove(noble)
            player.add_noble(noble)
            self._end_turn()

        else:
            # More than one noble qualifies →  player must choose one
            # Rule: a player may take only one noble per turn
            self._pending_nobles = eligible
            self._pending_state = PENDING_CHOOSE_NOBLE

    def _end_turn(self):
        """
        Finalize the current turn.

        Checks for a winner (≥ 15 prestige points).  If none, advances to
        the next player.  If all players have had their final turn after
        someone hit 15 points the game ends.

        NOTE: This implementation ends the game immediately when a player
        reaches VICTORY_POINTS.  A more complete version would let the
        remaining players in the same round finish before declaring a winner.
        # TODO: implement same-round completion so all players get a final turn
        """
        player = self.current_player

        if player.get_points() >= VICTORY_POINTS:
            self.game_over = True
            self.winner = player
            return

        # Advance to the next player
        self.current_player_index = (
            (self.current_player_index + 1) % len(self.players)
        )

        # Increment round counter when we cycle back to the first player
        if self.current_player_index == 0:
            self.round_number += 1

    # ══════════════════════════════════════════════════════════════════════
    #  Internal Utility
    # ══════════════════════════════════════════════════════════════════════

    def _get_deck(self, level):
        """
        Find the Deck object for a given level.

        :param level: int (1, 2, or 3)
        :return: Deck object or None if not found
        """
        for deck in self.board.decks:
            if deck.level == level:
                return deck
        return None

    # ══════════════════════════════════════════════════════════════════════
    #  Status / Debug
    # ══════════════════════════════════════════════════════════════════════

    def get_status(self):
        """
        Return a dictionary describing the current game state.
        Useful for UI layers to query what to render without coupling to
        Game internals.

        :return: dict
        """
        return {
            "round":          self.round_number,
            "current_player": self.current_player.name,
            "pending_state":  self._pending_state,
            "pending_nobles": [str(n) for n in self._pending_nobles],
            "game_over":      self.game_over,
            "winner":         self.winner.name if self.winner else None,
            "scores": {
                p.name: p.get_points() for p in self.players
            },
        }

    def __str__(self):
        status = self.get_status()
        return (
            f"Game(round={status['round']}, "
            f"current={status['current_player']}, "
            f"pending={status['pending_state']}, "
            f"game_over={status['game_over']})"
        )
