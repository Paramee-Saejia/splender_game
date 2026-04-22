"""
bot.py - Heuristic bot for Splendor (2-player).

This bot tries to feel more like a solid human player:
  1. Buy the highest-value affordable card
  2. Reserve strong cards to gain gold and protect future buys
  3. Collect tokens toward its top one or two targets
  4. Fall back to flexible token-taking when no focused plan is possible
"""

from game_component.game import PENDING_CHOOSE_NOBLE, PENDING_RETURN_TOKENS

COLORS = ["white", "blue", "green", "red", "black"]


def _effective_cost(player, card):
    bonus = player.get_bonus_count()
    return {color: max(0, need - bonus.get(color, 0)) for color, need in card.cost.items()}


def _shortages_by_color(player, card):
    effective = _effective_cost(player, card)
    shortages = {}
    for color, need in effective.items():
        gap = max(0, need - player.tokens.get(color, 0))
        if gap > 0:
            shortages[color] = gap
    return shortages


def _shortage(player, card):
    return sum(_shortages_by_color(player, card).values())


def _noble_synergy(player, card, nobles):
    if not nobles:
        return 0.0

    before = player.get_bonus_count()
    after = before.copy()
    after[card.color_bonus] = after.get(card.color_bonus, 0) + 1

    score = 0.0
    for noble in nobles:
        before_missing = sum(max(0, req - before.get(color, 0))
                             for color, req in noble.requirement.items())
        after_missing = sum(max(0, req - after.get(color, 0))
                            for color, req in noble.requirement.items())
        if after_missing == 0 and before_missing > 0:
            score += 3.0
        elif after_missing < before_missing:
            score += (before_missing - after_missing) * 0.7
    return score


def _card_value(player, card, nobles, reserved=False):
    shortage = _shortage(player, card)
    effective_total = sum(_effective_cost(player, card).values())
    reserve_bonus = 0.8 if reserved else 0.0
    return (
        card.points * 12.0
        + card.level * 2.5
        + _noble_synergy(player, card, nobles)
        - shortage * 3.5
        - effective_total * 0.25
        + reserve_bonus
    )


def _all_face_up(game):
    result = []
    for deck in game.board.decks:
        for i, card in enumerate(deck.get_face_up_cards()):
            result.append((card, deck.level, i))
    return result


def _best_buy(player, face_up, nobles):
    candidates = []
    for i, card in enumerate(player.reserved_cards):
        if player.can_afford(card):
            candidates.append((_card_value(player, card, nobles, reserved=True),
                               "reserved", i, card))

    for card, level, idx in face_up:
        if player.can_afford(card):
            candidates.append((_card_value(player, card, nobles), "board", (level, idx), card))

    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])


def _reserve_score(player, opponent, card, nobles, gold_available):
    shortage = _shortage(player, card)
    opponent_threat = 7.0 if opponent and opponent.can_afford(card) else 0.0
    near_buy = 4.5 if shortage <= 2 else (2.5 if shortage <= 4 else 0.0)
    gold_bonus = 2.0 if gold_available else 0.0
    return (
        card.points * 13.0
        + card.level * 3.5
        + _noble_synergy(player, card, nobles) * 1.4
        + near_buy
        + opponent_threat
        + gold_bonus
        - shortage * 2.2
        - sum(_effective_cost(player, card).values()) * 0.2
    )


def _pick_reserve_target(game, player, opponent, face_up):
    if not player.can_reserve():
        return None

    nobles = game.board.nobles
    gold_available = game.board.token_bank.tokens.get("gold", 0) > 0
    candidates = []
    for card, level, idx in face_up:
        if player.can_afford(card):
            continue
        score = _reserve_score(player, opponent, card, nobles, gold_available)
        candidates.append((score, card, level, idx))

    if not candidates:
        return None

    score, card, level, idx = max(candidates, key=lambda item: item[0])
    shortage = _shortage(player, card)
    should_reserve = (
        card.points >= 3
        or shortage <= 2
        or (opponent and opponent.can_afford(card))
        or score >= 20
    )
    if not should_reserve:
        return None
    return card, level, idx


def _pick_targets(game, player, face_up):
    nobles = game.board.nobles
    targets = []

    for card in player.reserved_cards:
        if not player.can_afford(card):
            targets.append((_card_value(player, card, nobles, reserved=True) + 3.0, card))

    for card, _, _ in face_up:
        if not player.can_afford(card):
            targets.append((_card_value(player, card, nobles), card))

    targets.sort(key=lambda item: item[0], reverse=True)
    cards = []
    seen = set()
    for _, card in targets:
        ident = id(card)
        if ident in seen:
            continue
        seen.add(ident)
        cards.append(card)
        if len(cards) == 2:
            break
    return cards


def _future_color_value(game, player):
    demand = {color: 0.0 for color in COLORS}
    for card, _, _ in _all_face_up(game):
        for color, gap in _shortages_by_color(player, card).items():
            demand[color] += gap + card.points * 0.4 + card.level * 0.2
    return demand


def _take_toward(game, player, primary, secondary=None):
    bank = game.board.token_bank
    weighted = {color: 0.0 for color in COLORS}
    primary_need = _shortages_by_color(player, primary) if primary else {}

    for card, weight in ((primary, 1.0), (secondary, 0.45)):
        if not card:
            continue
        for color, gap in _shortages_by_color(player, card).items():
            if bank.tokens.get(color, 0) >= 1:
                weighted[color] += gap * weight

    if not any(weighted.values()):
        return False

    ranked = sorted(
        COLORS,
        key=lambda color: (weighted[color], bank.tokens.get(color, 0)),
        reverse=True,
    )
    best = ranked[0]

    if primary_need.get(best, 0) >= 2 and bank.can_take_two_same(best):
        return game.take_tokens([best, best])

    pick = [color for color in ranked if weighted[color] > 0 and bank.tokens.get(color, 0) >= 1][:3]
    if len(pick) < 3:
        future = _future_color_value(game, player)
        fillers = sorted(
            [color for color in COLORS if color not in pick and bank.tokens.get(color, 0) >= 1],
            key=lambda color: future[color],
            reverse=True,
        )
        for color in fillers:
            pick.append(color)
            if len(pick) == 3:
                break

    if not pick:
        return False
    return game.take_tokens(pick)


def _take_any(game):
    bank = game.board.token_bank
    available = [c for c in COLORS if bank.tokens.get(c, 0) >= 1]
    if not available:
        return False

    future = _future_color_value(game, game.current_player)
    pick = sorted(available, key=lambda color: future[color], reverse=True)[:3]
    if len(pick) == 1 and bank.can_take_two_same(pick[0]):
        return game.take_tokens([pick[0], pick[0]])
    return game.take_tokens(pick)


def _resolve_pending(game):
    while game.get_pending_state() == PENDING_RETURN_TOKENS:
        _resolve_return(game)
    if game.get_pending_state() == PENDING_CHOOSE_NOBLE:
        _resolve_noble(game)


def _resolve_return(game):
    player = game.current_player
    targets = _pick_targets(game, player, _all_face_up(game))
    keep_value = {color: 0.0 for color in COLORS + ["gold"]}

    for card, weight in ((targets[0], 1.0), (targets[1], 0.45)) if len(targets) >= 2 else ((targets[0], 1.0),) if targets else ():
        for color, gap in _shortages_by_color(player, card).items():
            keep_value[color] += gap * weight
        keep_value["gold"] += _shortage(player, card) * 0.5 * weight

    choices = [color for color in COLORS + ["gold"] if player.tokens.get(color, 0) > 0]
    if not choices:
        return False

    color = min(
        choices,
        key=lambda c: (keep_value.get(c, 0.0), -player.tokens.get(c, 0), 1 if c == "gold" else 0),
    )
    game.resolve_return_token(color)
    return True


def _resolve_noble(game):
    nobles = game.get_pending_nobles()
    if nobles:
        game.resolve_choose_noble(0)
    return True


def bot_make_move(game):
    """
    Execute one full bot turn (resolves all pending states too).
    Returns True if any action was taken.
    """
    if game.get_pending_state() == PENDING_RETURN_TOKENS:
        return _resolve_return(game)
    if game.get_pending_state() == PENDING_CHOOSE_NOBLE:
        return _resolve_noble(game)

    player = game.current_player
    opponent = next((p for p in game.players if p is not player), None)
    face_up = _all_face_up(game)
    nobles = game.board.nobles

    best_buy = _best_buy(player, face_up, nobles)
    if best_buy:
        _, source, meta, _ = best_buy
        ok = game.buy_reserved_card(meta) if source == "reserved" else game.buy_card(meta[0], meta[1])
        if ok:
            _resolve_pending(game)
            return True

    reserve_target = _pick_reserve_target(game, player, opponent, face_up)
    if reserve_target:
        _, level, idx = reserve_target
        ok = game.reserve_card(level, idx)
        if ok:
            _resolve_pending(game)
            return True

    targets = _pick_targets(game, player, face_up)
    primary = targets[0] if targets else None
    secondary = targets[1] if len(targets) > 1 else None
    if primary and _take_toward(game, player, primary, secondary):
        _resolve_pending(game)
        return True

    if _take_any(game):
        _resolve_pending(game)
        return True

    if player.can_reserve():
        for deck in sorted(game.board.decks, key=lambda d: d.level, reverse=True):
            if deck.get_face_up_cards():
                ok = game.reserve_card(deck.level, 0)
                if ok:
                    _resolve_pending(game)
                    return True

    return False
