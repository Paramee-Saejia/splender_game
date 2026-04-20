"""
bot.py — Greedy bot for Splendor (2-player).

Priority order each turn:
  1. Buy highest-point card it can afford (reserved first, then face-up L3→L1)
  2. Reserve the highest-point card it cannot yet afford but is close to
  3. Take tokens that most help it toward the card it is saving for
  4. Fallback: take any 3 distinct tokens (or 2-same if only that is possible)
"""

import random
from game_component.game import PENDING_RETURN_TOKENS, PENDING_CHOOSE_NOBLE

COLORS = ["white", "blue", "green", "red", "black"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _shortage(player, card):
    """How many extra tokens (including gold) the player needs for this card."""
    bonus = player.get_bonus_count()
    total = 0
    for color, need in card.cost.items():
        remaining = max(0, need - bonus.get(color, 0))
        total += max(0, remaining - player.tokens.get(color, 0))
    return total  # gold needed to cover the gap


def _best_buyable(player, candidates):
    """From a list of (card, meta) pairs return the one with most points."""
    affordable = [(c, m) for c, m in candidates if player.can_afford(c)]
    if not affordable:
        return None
    return max(affordable, key=lambda x: (x[0].points, sum(x[0].cost.values())))


def _all_face_up(game):
    """Return list of (card, deck_level, card_index) for all visible cards."""
    result = []
    for deck in game.board.decks:
        for i, card in enumerate(deck.get_face_up_cards()):
            result.append((card, deck.level, i))
    return result


# ── Main bot move ─────────────────────────────────────────────────────────────

def bot_make_move(game):
    """
    Execute one full bot turn (resolves all pending states too).
    Returns True if any action was taken.
    """
    # Handle pending states first
    if game.get_pending_state() == PENDING_RETURN_TOKENS:
        return _resolve_return(game)
    if game.get_pending_state() == PENDING_CHOOSE_NOBLE:
        return _resolve_noble(game)

    player = game.current_player

    # 1. Buy best reserved card
    for i, card in enumerate(player.reserved_cards):
        if player.can_afford(card):
            ok = game.buy_reserved_card(i)
            if ok:
                _resolve_pending(game)
                return True

    # 2. Buy best face-up card
    face_up = _all_face_up(game)
    best = _best_buyable(player, [(c, (lv, i)) for c, lv, i in face_up])
    if best:
        card, (lv, idx) = best
        ok = game.buy_card(lv, idx)
        if ok:
            _resolve_pending(game)
            return True

    # 3. Find the highest-value card the bot cannot yet afford
    target = _pick_target(player, face_up)

    # 4. Take tokens toward the target
    if target is not None:
        result = _take_toward(game, player, target)
        if result:
            _resolve_pending(game)
            return True

    # 5. Fallback: take any available tokens
    if _take_any(game):
        _resolve_pending(game)
        return True

    # 6. Last resort: reserve something
    for deck in game.board.decks:
        cards = deck.get_face_up_cards()
        if cards and player.can_reserve():
            ok = game.reserve_card(deck.level, 0)
            if ok:
                _resolve_pending(game)
                return True

    return False


# ── Pending resolution helpers ────────────────────────────────────────────────

def _resolve_pending(game):
    while game.get_pending_state() == PENDING_RETURN_TOKENS:
        _resolve_return(game)
    if game.get_pending_state() == PENDING_CHOOSE_NOBLE:
        _resolve_noble(game)


def _resolve_return(game):
    player = game.current_player
    # Return the color of which the bot has the most tokens
    best_color = max(COLORS + ["gold"], key=lambda c: player.tokens.get(c, 0))
    game.resolve_return_token(best_color)
    return True


def _resolve_noble(game):
    nobles = game.get_pending_nobles()
    if nobles:
        game.resolve_choose_noble(0)
    return True


# ── Strategy helpers ──────────────────────────────────────────────────────────

def _pick_target(player, face_up):
    """Pick the most attractive card the bot cannot afford yet."""
    candidates = [c for c, lv, i in face_up if not player.can_afford(c)]
    if not candidates:
        return None
    # Prefer high points; among equals prefer lowest shortage
    return min(candidates, key=lambda c: (_shortage(player, c), -c.points))


def _take_toward(game, player, target):
    """Take up to 3 distinct tokens that help most toward target."""
    bank = game.board.token_bank
    bonus = player.get_bonus_count()

    # Colors where the player is short
    needed = []
    for color, need in target.cost.items():
        remaining = max(0, need - bonus.get(color, 0) - player.tokens.get(color, 0))
        if remaining > 0 and bank.tokens.get(color, 0) >= 1:
            needed.append((color, remaining))

    # Sort by most needed first
    needed.sort(key=lambda x: -x[1])
    pick = [c for c, _ in needed[:3]]

    if len(pick) == 0:
        return False

    if len(pick) == 1:
        color = pick[0]
        # Prefer 2-same if bank allows
        if bank.can_take_two_same(color):
            return game.take_tokens([color, color])
        return game.take_tokens([color])

    return game.take_tokens(pick)


def _take_any(game):
    """Take 3 distinct tokens from whatever colors are available."""
    bank = game.board.token_bank
    available = [c for c in COLORS if bank.tokens.get(c, 0) >= 1]
    if not available:
        return False
    pick = available[:3]
    return game.take_tokens(pick)
