"""
main.py — Splendor: Human vs Bot  (Pygame)
"""

import pygame
import sys
from game_component.game_factory import create_game
from game_component.game import IDLE, PENDING_RETURN_TOKENS, PENDING_CHOOSE_NOBLE
from bot import bot_make_move

# ── Constants ─────────────────────────────────────────────────────────────────

SW, SH   = 1280, 768
FPS      = 60
BOT_DELAY = 900   # ms before bot acts

CARD_W, CARD_H = 100, 138
CARD_GAP       = 8
HIDDEN_W       = 60
TOKEN_R        = 26

BOARD_X  = 10
BOARD_Y  = 195
ROW_GAP  = 12

NOBLE_X  = 10
NOBLE_Y  = 50
NOBLE_W, NOBLE_H = 110, 120

RIGHT_X  = 890
STATUS_Y = SH - 48

# ── Colours ───────────────────────────────────────────────────────────────────

GEM = {
    "white": (240, 238, 220),
    "blue":  (70,  130, 180),
    "green": (55,  160, 80),
    "red":   (210, 55,  55),
    "black": (45,  45,  45),
    "gold":  (255, 205, 0),
}
GEM_TEXT = {           # readable text colour on each gem background
    "white": (30,  30,  30),
    "blue":  (255, 255, 255),
    "green": (255, 255, 255),
    "red":   (255, 255, 255),
    "black": (220, 220, 220),
    "gold":  (60,  40,  0),
}
COLORS_ORDER = ["white", "blue", "green", "red", "black"]

BG        = (22, 28, 38)
PANEL     = (38, 46, 62)
CARD_BG   = (195, 188, 170)
CARD_FACE = (160, 153, 135)   # face-down colour
TEXT      = (230, 225, 210)
DIM       = (140, 135, 120)
HIGHLIGHT = (255, 215, 40)
BTN_N     = (50,  80, 125)
BTN_H     = (75, 115, 170)
BTN_A     = (45, 140, 75)
BTN_DIS   = (55,  58,  68)
RED_HINT  = (210, 60,  60)

# ── Animation system ──────────────────────────────────────────────────────────

class Anim:
    """Linear float animation from start to end over duration ms."""
    def __init__(self, start, end, duration):
        self.start    = start
        self.end      = end
        self.duration = duration
        self.elapsed  = 0
        self.done     = False

    def update(self, dt):
        if self.done:
            return self.end
        self.elapsed += dt
        t = min(self.elapsed / self.duration, 1.0)
        val = self.start + (self.end - self.start) * t
        if t >= 1.0:
            self.done = True
        return val

    @property
    def value(self):
        if self.done:
            return self.end
        t = min(self.elapsed / self.duration, 1.0)
        return self.start + (self.end - self.start) * t


class FlyingToken:
    """A token that flies from one screen position to another."""
    def __init__(self, color, src, dst, duration=350):
        self.color    = color
        self.x_anim   = Anim(src[0], dst[0], duration)
        self.y_anim   = Anim(src[1], dst[1], duration)
        self.a_anim   = Anim(255, 255, duration)
        self.done     = False

    def update(self, dt):
        x = self.x_anim.update(dt)
        y = self.y_anim.update(dt)
        self.done = self.x_anim.done
        return int(x), int(y)


class FlyingCard:
    """A card that slides off screen when bought/reserved."""
    def __init__(self, rect, dst_x, color, points):
        self.x_anim  = Anim(rect[0], dst_x, 380)
        self.y_anim  = Anim(rect[1], rect[1] - 30, 380)
        self.a_anim  = Anim(255, 0, 380)
        self.rect    = rect
        self.color   = color
        self.points  = points
        self.done    = False

    def update(self, dt):
        x = self.x_anim.update(dt)
        y = self.y_anim.update(dt)
        a = self.a_anim.update(dt)
        self.done = self.x_anim.done
        return int(x), int(y), int(a)


class FloatingText:
    """A short text label that rises and fades."""
    def __init__(self, text, x, y, color=HIGHLIGHT, duration=900):
        self.text   = text
        self.x      = x
        self.y_anim = Anim(y, y - 50, duration)
        self.a_anim = Anim(255, 0, duration)
        self.color  = color
        self.done   = False

    def update(self, dt, font):
        y = self.y_anim.update(dt)
        a = self.a_anim.update(dt)
        self.done = self.y_anim.done
        surf = font.render(self.text, True, self.color)
        surf.set_alpha(int(a))
        return surf, self.x, int(y)


# ── UI state ──────────────────────────────────────────────────────────────────

class UIMode:
    IDLE           = "IDLE"
    TAKE_TOKENS    = "TAKE_TOKENS"
    BUY_CARD       = "BUY_CARD"
    RESERVE_CARD   = "RESERVE_CARD"
    BUY_RESERVED   = "BUY_RESERVED"
    PEND_RETURN    = "PEND_RETURN"
    PEND_NOBLE     = "PEND_NOBLE"
    BOT_TURN       = "BOT_TURN"
    GAME_OVER      = "GAME_OVER"


# ── Layout helpers ────────────────────────────────────────────────────────────

def card_rect(level, slot):
    """
    Return (x, y, w, h) for a card slot on the board.
    slot 0 = hidden-deck button, slots 1-4 = face-up cards.
    level 1 is bottom row, level 3 is top.
    """
    row = 3 - level  # level3→row0, level2→row1, level1→row2
    y   = BOARD_Y + row * (CARD_H + ROW_GAP)
    if slot == 0:   # hidden deck
        return (BOARD_X, y, HIDDEN_W, CARD_H)
    x = BOARD_X + HIDDEN_W + CARD_GAP + (slot - 1) * (CARD_W + CARD_GAP)
    return (x, y, CARD_W, CARD_H)


def token_rect(color_index):
    """Return (cx, cy) centre of a token in the bank area."""
    token_y = BOARD_Y + 3 * (CARD_H + ROW_GAP) + 30
    gap = 68
    start_x = BOARD_X + 20
    return (start_x + color_index * gap, token_y)


def noble_rect(index):
    """Return (x, y, w, h) for noble tile at position index."""
    x = NOBLE_X + index * (NOBLE_W + 10)
    return (x, NOBLE_Y, NOBLE_W, NOBLE_H)


def reserved_card_rect(player_panel_y, slot):
    """Rect for a reserved card shown inside the human player panel."""
    x = RIGHT_X + 10 + slot * (72 + 6)
    y = player_panel_y + 130
    return (x, y, 72, 96)


# ── Drawing primitives ────────────────────────────────────────────────────────

def draw_rounded(surf, color, rect, radius=8):
    pygame.draw.rect(surf, color, rect, border_radius=radius)


def draw_token_circle(surf, color_name, cx, cy, r=TOKEN_R, alpha=255, label=None, font=None):
    c = GEM[color_name]
    if alpha < 255:
        tmp = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(tmp, (*c, alpha), (r, r), r)
        pygame.draw.circle(tmp, (*_darken(c), alpha), (r, r), r, 2)
        surf.blit(tmp, (cx - r, cy - r))
    else:
        pygame.draw.circle(surf, c, (cx, cy), r)
        pygame.draw.circle(surf, _darken(c), (cx, cy), r, 2)
    if label and font:
        tc = GEM_TEXT[color_name]
        t = font.render(label, True, tc)
        surf.blit(t, t.get_rect(center=(cx, cy)))


def _darken(c, amt=40):
    return tuple(max(0, v - amt) for v in c)


def draw_card(surf, card, rect, fonts, highlight=False, alpha=255):
    x, y, w, h = rect
    bg = CARD_BG
    border = GEM.get(card.color_bonus, (120, 120, 120))

    if alpha < 255:
        tmp = pygame.Surface((w, h), pygame.SRCALPHA)
        _draw_card_surface(tmp, card, (0, 0, w, h), fonts, highlight, border, bg)
        tmp.set_alpha(alpha)
        surf.blit(tmp, (x, y))
    else:
        _draw_card_surface(surf, card, rect, fonts, highlight, border, bg)


def _draw_card_surface(surf, card, rect, fonts, highlight, border, bg):
    x, y, w, h = rect
    draw_rounded(surf, bg, rect, 6)
    if highlight:
        pygame.draw.rect(surf, HIGHLIGHT, rect, 3, border_radius=6)
    else:
        pygame.draw.rect(surf, border, rect, 3, border_radius=6)

    # Bonus colour strip (top bar)
    strip = (x, y, w, 22)
    draw_rounded(surf, border, strip, 6)

    # Points
    if card.points > 0:
        pt = fonts["bold"].render(str(card.points), True, TEXT)
        surf.blit(pt, (x + 5, y + 24))

    # Cost
    cy_off = y + 46
    for color in COLORS_ORDER:
        amt = card.cost.get(color, 0)
        if amt == 0:
            continue
        dot_x, dot_y = x + 10, cy_off
        pygame.draw.circle(surf, GEM[color], (dot_x, dot_y + 6), 7)
        pygame.draw.circle(surf, _darken(GEM[color]), (dot_x, dot_y + 6), 7, 1)
        lbl = fonts["small"].render(str(amt), True, TEXT)
        surf.blit(lbl, (dot_x + 10, dot_y))
        cy_off += 18


def draw_hidden_deck(surf, deck, rect, fonts, highlight=False):
    x, y, w, h = rect
    if deck.hidden_count() == 0 and not deck.get_face_up_cards():
        draw_rounded(surf, (50, 50, 60), rect, 6)
        t = fonts["small"].render("Empty", True, DIM)
        surf.blit(t, t.get_rect(center=(x + w//2, y + h//2)))
        return
    col = {"1": (110, 160, 90), "2": (170, 110, 60), "3": (140, 80, 80)}
    c = col.get(str(deck.level), (100, 100, 120))
    draw_rounded(surf, c, rect, 6)
    if highlight:
        pygame.draw.rect(surf, HIGHLIGHT, rect, 3, border_radius=6)
    else:
        pygame.draw.rect(surf, _darken(c, 30), rect, 2, border_radius=6)
    lbl = fonts["small"].render(f"L{deck.level}", True, TEXT)
    surf.blit(lbl, lbl.get_rect(center=(x + w//2, y + h//2 - 10)))
    cnt = fonts["small"].render(str(deck.hidden_count()), True, TEXT)
    surf.blit(cnt, cnt.get_rect(center=(x + w//2, y + h//2 + 8)))


def draw_noble(surf, noble, rect, fonts, highlight=False):
    x, y, w, h = rect
    draw_rounded(surf, (160, 145, 110), rect, 6)
    if highlight:
        pygame.draw.rect(surf, HIGHLIGHT, rect, 3, border_radius=6)
    else:
        pygame.draw.rect(surf, (120, 108, 80), rect, 2, border_radius=6)
    pt = fonts["bold"].render(str(noble.points), True, (30, 30, 30))
    surf.blit(pt, (x + 5, y + 5))
    cy = y + 28
    for color, amt in noble.requirement.items():
        pygame.draw.circle(surf, GEM[color], (x + 14, cy + 6), 8)
        lbl = fonts["small"].render(str(amt), True, (30, 30, 30))
        surf.blit(lbl, (x + 25, cy))
        cy += 20


def draw_button(surf, text, rect, fonts, active=False, disabled=False, hover=False):
    if disabled:
        col = BTN_DIS
    elif active:
        col = BTN_A
    elif hover:
        col = BTN_H
    else:
        col = BTN_N
    draw_rounded(surf, col, rect, 7)
    tc = DIM if disabled else TEXT
    t = fonts["normal"].render(text, True, tc)
    surf.blit(t, t.get_rect(center=(rect[0] + rect[2]//2, rect[1] + rect[3]//2)))


def draw_player_panel(surf, player, rect, fonts, is_current, is_human):
    x, y, w, h = rect
    col = (50, 68, 90) if is_current else PANEL
    draw_rounded(surf, col, rect, 8)
    if is_current:
        pygame.draw.rect(surf, HIGHLIGHT, rect, 2, border_radius=8)

    label = ("YOU" if is_human else "BOT") + f"  —  {player.name}"
    t = fonts["bold"].render(label, True, HIGHLIGHT if is_current else TEXT)
    surf.blit(t, (x + 10, y + 8))

    pts = fonts["normal"].render(f"Points: {player.get_points()}", True, TEXT)
    surf.blit(pts, (x + 10, y + 30))

    # Tokens row
    tx = x + 10
    ty = y + 56
    for color in COLORS_ORDER + ["gold"]:
        amt = player.tokens[color]
        pygame.draw.circle(surf, GEM[color], (tx + 12, ty + 10), 10)
        pygame.draw.circle(surf, _darken(GEM[color]), (tx + 12, ty + 10), 10, 1)
        lt = fonts["small"].render(str(amt), True, TEXT)
        surf.blit(lt, (tx + 26, ty + 4))
        tx += 58

    # Bonus row
    bonus = player.get_bonus_count()
    bx = x + 10
    by = y + 84
    bl = fonts["small"].render("Bonus:", True, DIM)
    surf.blit(bl, (bx, by))
    bx += 52
    for color in COLORS_ORDER:
        amt = bonus[color]
        pygame.draw.circle(surf, GEM[color], (bx + 8, by + 7), 8)
        bt = fonts["small"].render(str(amt), True, TEXT)
        surf.blit(bt, (bx + 20, by + 1))
        bx += 44

    # Reserved cards
    rl = fonts["small"].render("Reserved:", True, DIM)
    surf.blit(rl, (x + 10, y + 108))
    for i, card in enumerate(player.reserved_cards):
        rx = x + 10 + i * 76
        ry = y + 126
        rw, rh = 68, 88
        draw_rounded(surf, CARD_BG, (rx, ry, rw, rh), 5)
        border = GEM.get(card.color_bonus, (120, 120, 120))
        pygame.draw.rect(surf, border, (rx, ry, rw, rh), 3, border_radius=5)
        if card.points > 0:
            p = fonts["small"].render(str(card.points), True, TEXT)
            surf.blit(p, (rx + 4, ry + 4))
        cy2 = ry + 20
        for color in COLORS_ORDER:
            amt2 = card.cost.get(color, 0)
            if amt2 == 0:
                continue
            pygame.draw.circle(surf, GEM[color], (rx + 10, cy2 + 5), 6)
            at = fonts["small"].render(str(amt2), True, TEXT)
            surf.blit(at, (rx + 20, cy2))
            cy2 += 15

    # Nobles
    if player.nobles:
        nl = fonts["small"].render("Nobles:", True, DIM)
        surf.blit(nl, (x + 10, y + 220))
        for i, noble in enumerate(player.nobles):
            nx = x + 10 + i * 34
            ny = y + 238
            draw_rounded(surf, (160, 145, 110), (nx, ny, 28, 28), 4)
            nt = fonts["small"].render(str(noble.points), True, (30, 30, 30))
            surf.blit(nt, nt.get_rect(center=(nx + 14, ny + 14)))


# ── Main game class ───────────────────────────────────────────────────────────

class SplendorGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SW, SH))
        pygame.display.set_caption("Splendor — Human vs Bot")
        self.clock  = pygame.time.Clock()

        self.fonts = {
            "bold":   pygame.font.SysFont("segoeui", 16, bold=True),
            "normal": pygame.font.SysFont("segoeui", 15),
            "small":  pygame.font.SysFont("segoeui", 13),
            "large":  pygame.font.SysFont("segoeui", 28, bold=True),
            "title":  pygame.font.SysFont("segoeui", 36, bold=True),
        }

        self.game         = create_game("You", "Bot")
        self.ui_mode      = UIMode.IDLE
        self.selected_toks = []    # colours chosen during TAKE_TOKENS
        self.status       = "Your turn!  Choose an action."
        self.bot_timer    = 0
        self.flying_tokens = []
        self.flying_cards  = []
        self.float_texts   = []
        self.hover         = None  # (type, data) for hover highlighting

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()

    # ── Event handling ────────────────────────────────────────────────────────

    def _handle_events(self):
        mx, my = pygame.mouse.get_pos()
        self.hover = self._hit_test(mx, my)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.ui_mode not in (UIMode.BOT_TURN, UIMode.GAME_OVER):
                    self.ui_mode = UIMode.IDLE
                    self.selected_toks = []
                    self.status = "Cancelled.  Choose an action."
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(mx, my)

    def _handle_click(self, mx, my):
        mode = self.ui_mode
        game = self.game
        g_mode = game.get_pending_state()

        # Game-over restart
        if mode == UIMode.GAME_OVER:
            self._restart()
            return

        # Pending noble choice
        if g_mode == PENDING_CHOOSE_NOBLE:
            self._click_noble_choice(mx, my)
            return

        # Pending token return
        if g_mode == PENDING_RETURN_TOKENS:
            self._click_return_token(mx, my)
            return

        # Bot turn — ignore human clicks
        if mode == UIMode.BOT_TURN:
            return

        # Action buttons
        btn = self._hit_button(mx, my)
        if btn:
            self._handle_button(btn)
            return

        # Mode-specific clicks
        if mode == UIMode.TAKE_TOKENS:
            self._click_token(mx, my)
        elif mode == UIMode.BUY_CARD:
            self._click_buy_card(mx, my)
        elif mode == UIMode.RESERVE_CARD:
            self._click_reserve_card(mx, my)
        elif mode == UIMode.BUY_RESERVED:
            self._click_buy_reserved(mx, my)

    # ── Button definitions ────────────────────────────────────────────────────

    def _buttons(self):
        bx, by = RIGHT_X, SH - 170
        bw, bh = 180, 36
        gap = 10
        return {
            "take":     (bx,        by,          bw, bh),
            "buy":      (bx + bw + gap, by,      bw, bh),
            "reserve":  (bx,        by + bh + gap, bw, bh),
            "buy_res":  (bx + bw + gap, by + bh + gap, bw, bh),
            "confirm":  (bx,        by + 2*(bh + gap), bw*2 + gap, bh),
        }

    def _hit_button(self, mx, my):
        for name, r in self._buttons().items():
            if r[0] <= mx < r[0]+r[2] and r[1] <= my < r[1]+r[3]:
                return name
        return None

    def _handle_button(self, btn):
        mode = self.ui_mode
        if btn == "take" and mode == UIMode.IDLE:
            self.ui_mode = UIMode.TAKE_TOKENS
            self.selected_toks = []
            self.status = "Click tokens to select (up to 3 different, or 2 same).  Confirm when done."
        elif btn == "buy" and mode == UIMode.IDLE:
            self.ui_mode = UIMode.BUY_CARD
            self.status = "Click a face-up card to buy it."
        elif btn == "reserve" and mode == UIMode.IDLE:
            self.ui_mode = UIMode.RESERVE_CARD
            self.status = "Click a face-up card or hidden deck to reserve."
        elif btn == "buy_res" and mode == UIMode.IDLE:
            if self.game.players[0].reserved_cards:
                self.ui_mode = UIMode.BUY_RESERVED
                self.status = "Click one of your reserved cards to buy."
            else:
                self.status = "You have no reserved cards."
        elif btn == "confirm" and mode == UIMode.TAKE_TOKENS:
            self._confirm_take_tokens()

    # ── Token taking ──────────────────────────────────────────────────────────

    def _click_token(self, mx, my):
        for i, color in enumerate(COLORS_ORDER + ["gold"]):
            if color == "gold":
                continue   # gold cannot be taken freely
            cx, cy = token_rect(i)
            if (mx - cx)**2 + (my - cy)**2 <= TOKEN_R**2:
                self._select_token(color, cx, cy)
                return

    def _select_token(self, color, cx, cy):
        sel = self.selected_toks
        bank = self.game.board.token_bank

        # Clicking same colour twice → 2-same mode
        if sel == [color]:
            if bank.can_take_two_same(color):
                sel.append(color)
                self.status = f"Selected: {sel}  —  Confirm to take."
            else:
                self.status = f"Need ≥4 {color} tokens in bank to take 2."
            return

        # Already in 2-same mode, ignore extra clicks
        if len(sel) == 2 and sel[0] == sel[1]:
            self.status = "Already selecting 2 same. Confirm or press Esc to cancel."
            return

        if color in sel:
            sel.remove(color)
            self.status = f"Deselected {color}.  Selected: {sel}"
            return

        if len(sel) >= 3:
            self.status = "Already selected 3 tokens.  Confirm or Esc to cancel."
            return

        if bank.tokens.get(color, 0) < 1:
            self.status = f"No {color} tokens in bank."
            return

        sel.append(color)
        self.status = f"Selected: {sel}" + ("  —  Confirm to take." if len(sel) == 3 else "  Click more or Confirm.")

    def _confirm_take_tokens(self):
        if not self.selected_toks:
            self.status = "Select at least 1 token first."
            return
        ok = self.game.take_tokens(self.selected_toks)
        if ok:
            self._spawn_token_anims(self.selected_toks)
            self.float_texts.append(FloatingText(
                f"Took {', '.join(self.selected_toks)}", SW // 2, SH // 2 - 40))
            self.selected_toks = []
            self._post_action()
        else:
            self.status = "Invalid token selection (check bank availability)."

    def _spawn_token_anims(self, colors):
        for i, color in enumerate(COLORS_ORDER + ["gold"]):
            if color in colors:
                cx, cy = token_rect(i if color != "gold" else 5)
                dst = (RIGHT_X + 50 + len(self.flying_tokens)*30, SH - 250)
                self.flying_tokens.append(FlyingToken(color, (cx, cy), dst))

    # ── Buy face-up card ──────────────────────────────────────────────────────

    def _click_buy_card(self, mx, my):
        for level in [1, 2, 3]:
            deck = self.game._get_deck(level)
            if deck is None:
                continue
            for i, card in enumerate(deck.get_face_up_cards()):
                r = card_rect(level, i + 1)
                if self._in_rect(mx, my, r):
                    ok = self.game.buy_card(level, i)
                    if ok:
                        self._spawn_card_fly(card, r)
                        self.float_texts.append(FloatingText(
                            f"+{card.points}pt" if card.points else "Bought!", r[0], r[1] - 10))
                        self._post_action()
                    else:
                        self.status = "Cannot afford that card."
                    return

    def _spawn_card_fly(self, card, rect):
        dst_x = RIGHT_X + 400   # fly to right side
        self.flying_cards.append(FlyingCard(rect, dst_x, card.color_bonus, card.points))

    # ── Reserve card ─────────────────────────────────────────────────────────

    def _click_reserve_card(self, mx, my):
        game = self.game
        player = game.players[0]
        if not player.can_reserve():
            self.status = "You already have 3 reserved cards."
            self.ui_mode = UIMode.IDLE
            return

        # Face-up card
        for level in [1, 2, 3]:
            deck = game._get_deck(level)
            if deck is None:
                continue
            for i, card in enumerate(deck.get_face_up_cards()):
                r = card_rect(level, i + 1)
                if self._in_rect(mx, my, r):
                    ok = game.reserve_card(level, i)
                    if ok:
                        self._spawn_card_fly(card, r)
                        self.float_texts.append(FloatingText("Reserved!", r[0], r[1] - 10))
                        self._post_action()
                    else:
                        self.status = "Cannot reserve that card."
                    return

        # Hidden deck button (slot 0)
        for level in [1, 2, 3]:
            r = card_rect(level, 0)
            if self._in_rect(mx, my, r):
                ok = game.reserve_hidden_card(level)
                if ok:
                    self.float_texts.append(FloatingText(
                        "Reserved (hidden)!", r[0], r[1] - 10))
                    self._post_action()
                else:
                    self.status = "Deck empty or cannot reserve."
                return

    # ── Buy reserved card ─────────────────────────────────────────────────────

    def _click_buy_reserved(self, mx, my):
        player = self.game.players[0]
        panel_y = self._human_panel_rect()[1]
        for i in range(len(player.reserved_cards)):
            r = reserved_card_rect(panel_y, i)
            if self._in_rect(mx, my, r):
                ok = self.game.buy_reserved_card(i)
                if ok:
                    self.float_texts.append(FloatingText(
                        "Bought reserved!", r[0], r[1] - 10))
                    self._post_action()
                else:
                    self.status = "Cannot afford that card."
                return

    # ── Pending states (human) ────────────────────────────────────────────────

    def _click_return_token(self, mx, my):
        player = self.game.current_player
        panel_y = self._human_panel_rect()[1]
        for i, color in enumerate(COLORS_ORDER + ["gold"]):
            cx, cy = RIGHT_X + 10 + i * 58 + 12, panel_y + 56 + 10
            if (mx - cx)**2 + (my - cy)**2 <= 120:
                if player.tokens.get(color, 0) > 0:
                    ok = self.game.resolve_return_token(color)
                    if ok:
                        self.float_texts.append(FloatingText(
                            f"Returned {color}", cx, cy - 20, RED_HINT))
                        if self.game.get_pending_state() == PENDING_RETURN_TOKENS:
                            self.status = f"Still over 10 tokens.  Return another."
                        else:
                            self._post_action()
                return

    def _click_noble_choice(self, mx, my):
        nobles = self.game.get_pending_nobles()
        board_nobles = self.game.board.nobles
        for i, noble in enumerate(nobles):
            idx_in_board = board_nobles.index(noble) if noble in board_nobles else -1
            r = noble_rect(idx_in_board if idx_in_board >= 0 else i)
            if self._in_rect(mx, my, r):
                ok = self.game.resolve_choose_noble(i)
                if ok:
                    self.float_texts.append(FloatingText(
                        f"+{noble.points}pt Noble!", r[0], r[1] - 10))
                    self._post_action()
                return

    # ── Post-action routing ───────────────────────────────────────────────────

    def _post_action(self):
        g = self.game
        if g.game_over:
            self.ui_mode = UIMode.GAME_OVER
            self.status  = f"Game over!  {g.winner.name} wins with {g.winner.get_points()} points!"
            return

        gp = g.get_pending_state()
        if gp == PENDING_RETURN_TOKENS:
            self.ui_mode = UIMode.PEND_RETURN
            self.status  = f"You have >{10} tokens.  Click a token in YOUR panel to return it."
            return
        if gp == PENDING_CHOOSE_NOBLE:
            self.ui_mode = UIMode.PEND_NOBLE
            self.status  = "Multiple nobles available!  Click one to accept."
            return

        # Turn advances — whose turn now?
        if g.current_player.name == "You":
            self.ui_mode = UIMode.IDLE
            self.status  = "Your turn!  Choose an action."
        else:
            self.ui_mode = UIMode.BOT_TURN
            self.bot_timer = BOT_DELAY
            self.status  = "Bot is thinking…"

    # ── Update ────────────────────────────────────────────────────────────────

    def _update(self, dt):
        # Bot timer
        if self.ui_mode == UIMode.BOT_TURN and not self.game.game_over:
            self.bot_timer -= dt
            if self.bot_timer <= 0:
                bot_make_move(self.game)
                self._post_action()

        # Animations
        self.flying_tokens = [ft for ft in self.flying_tokens if not ft.done]
        for ft in self.flying_tokens:
            ft.update(dt)

        self.flying_cards = [fc for fc in self.flying_cards if not fc.done]
        for fc in self.flying_cards:
            fc.update(dt)

        self.float_texts = [fl for fl in self.float_texts if not fl.done]

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw(self):
        surf = self.screen
        surf.fill(BG)
        self._draw_title()
        self._draw_nobles()
        self._draw_board()
        self._draw_token_bank()
        self._draw_player_panels()
        self._draw_buttons()
        self._draw_status()
        self._draw_animations()
        if self.ui_mode == UIMode.GAME_OVER:
            self._draw_game_over()

    def _draw_title(self):
        t = self.fonts["title"].render("SPLENDOR", True, HIGHLIGHT)
        self.screen.blit(t, (10, 8))
        g = self.game
        info = f"Round {g.round_number}  |  Turn: {g.current_player.name}"
        ti = self.fonts["normal"].render(info, True, TEXT)
        self.screen.blit(ti, ti.get_rect(midright=(SW - 10, 22)))

    def _draw_nobles(self):
        surf = self.screen
        g    = self.game
        pending_nobles = g.get_pending_nobles() if g.get_pending_state() == PENDING_CHOOSE_NOBLE else []
        nl = self.fonts["bold"].render("Nobles:", True, DIM)
        surf.blit(nl, (NOBLE_X, NOBLE_Y - 18))
        for i, noble in enumerate(g.board.nobles):
            r = noble_rect(i)
            hl = noble in pending_nobles
            draw_noble(surf, noble, r, self.fonts, highlight=hl)

    def _draw_board(self):
        surf  = self.screen
        game  = self.game
        mode  = self.ui_mode
        gp    = game.get_pending_state()
        mx, my = pygame.mouse.get_pos()

        for level in [3, 2, 1]:
            deck = game._get_deck(level)
            if deck is None:
                continue

            # Hidden deck button
            r0 = card_rect(level, 0)
            hl_hidden = (mode == UIMode.RESERVE_CARD and self._in_rect(mx, my, r0)
                         and deck.hidden_count() > 0)
            draw_hidden_deck(surf, deck, r0, self.fonts, highlight=hl_hidden)

            # Face-up cards
            for i, card in enumerate(deck.get_face_up_cards()):
                r = card_rect(level, i + 1)
                can_buy = game.players[0].can_afford(card)
                hl = False
                if mode == UIMode.BUY_CARD and self._in_rect(mx, my, r):
                    hl = True
                if mode == UIMode.RESERVE_CARD and self._in_rect(mx, my, r):
                    hl = True
                draw_card(surf, card, r, self.fonts, highlight=hl)

                # Affordability tint border
                if mode == UIMode.BUY_CARD and can_buy and not hl:
                    pygame.draw.rect(surf, (80, 200, 80), r, 2, border_radius=6)

    def _draw_token_bank(self):
        surf = self.screen
        bank = self.game.board.token_bank
        mode = self.ui_mode
        mx, my = pygame.mouse.get_pos()

        all_colors = COLORS_ORDER + ["gold"]
        tl = self.fonts["bold"].render("Bank:", True, DIM)
        cx0, cy0 = token_rect(0)
        surf.blit(tl, (cx0 - 5, cy0 - TOKEN_R - 18))

        for i, color in enumerate(all_colors):
            cx, cy = token_rect(i)
            amt = bank.tokens.get(color, 0)
            if amt == 0:
                # Draw greyed-out circle
                pygame.draw.circle(surf, (55, 58, 68), (cx, cy), TOKEN_R)
                pygame.draw.circle(surf, (70, 72, 80), (cx, cy), TOKEN_R, 2)
            else:
                hovering = (mx - cx)**2 + (my - cy)**2 <= TOKEN_R**2
                hl = (mode == UIMode.TAKE_TOKENS and color in COLORS_ORDER
                      and hovering and color not in ["gold"])
                hl |= (color in self.selected_toks)
                if hl:
                    pygame.draw.circle(surf, HIGHLIGHT, (cx, cy), TOKEN_R + 4)
                draw_token_circle(surf, color, cx, cy, TOKEN_R, label=str(amt),
                                  font=self.fonts["bold"])

            name_t = self.fonts["small"].render(color[:3].upper(), True, DIM)
            surf.blit(name_t, name_t.get_rect(center=(cx, cy + TOKEN_R + 10)))

    def _human_panel_rect(self):
        return (RIGHT_X, 50, SW - RIGHT_X - 10, 290)

    def _bot_panel_rect(self):
        return (RIGHT_X, 350, SW - RIGHT_X - 10, 290)

    def _draw_player_panels(self):
        g = self.game
        human = g.players[0]
        bot   = g.players[1]
        is_human_turn = (g.current_player == human)
        draw_player_panel(self.screen, human, self._human_panel_rect(),
                          self.fonts, is_human_turn, is_human=True)
        draw_player_panel(self.screen, bot,   self._bot_panel_rect(),
                          self.fonts, not is_human_turn, is_human=False)

    def _draw_buttons(self):
        surf = self.screen
        mode = self.ui_mode
        mx, my = pygame.mouse.get_pos()
        buttons = self._buttons()

        human_is_active = (mode in (UIMode.IDLE, UIMode.TAKE_TOKENS,
                                    UIMode.BUY_CARD, UIMode.RESERVE_CARD,
                                    UIMode.BUY_RESERVED))

        for name, r in buttons.items():
            if name == "confirm":
                if mode != UIMode.TAKE_TOKENS:
                    continue
                hover  = self._in_rect(mx, my, r)
                active = bool(self.selected_toks)
                draw_button(surf, "Confirm Take", r, self.fonts,
                            active=active, hover=hover)
                continue

            disabled = not human_is_active
            active   = {
                "take":    mode == UIMode.TAKE_TOKENS,
                "buy":     mode == UIMode.BUY_CARD,
                "reserve": mode == UIMode.RESERVE_CARD,
                "buy_res": mode == UIMode.BUY_RESERVED,
            }.get(name, False)
            hover = self._in_rect(mx, my, r) and not disabled
            labels = {"take": "Take Tokens", "buy": "Buy Card",
                      "reserve": "Reserve Card", "buy_res": "Buy Reserved"}
            draw_button(surf, labels[name], r, self.fonts,
                        active=active, disabled=disabled, hover=hover)

        # ESC hint
        if mode not in (UIMode.IDLE, UIMode.BOT_TURN, UIMode.GAME_OVER):
            hint = self.fonts["small"].render("Esc = cancel", True, DIM)
            surf.blit(hint, (RIGHT_X, SH - 185))

    def _draw_status(self):
        g    = self.game
        gp   = g.get_pending_state()
        msg  = self.status
        if gp == PENDING_RETURN_TOKENS:
            msg = "⚠  You have >10 tokens.  Click a token in YOUR panel to return one."
        elif gp == PENDING_CHOOSE_NOBLE:
            msg = "✦  Multiple nobles available!  Click one to accept."

        pygame.draw.rect(self.screen, PANEL, (0, STATUS_Y - 4, SW, 52))
        t = self.fonts["normal"].render(msg, True, TEXT)
        self.screen.blit(t, (12, STATUS_Y + 10))

    def _draw_animations(self):
        surf = self.screen
        dt   = 0   # already updated in _update; just draw current positions

        for ft in self.flying_tokens:
            x, y = ft.x_anim.value, ft.y_anim.value
            draw_token_circle(surf, ft.color, int(x), int(y), TOKEN_R - 4)

        for fc in self.flying_cards:
            x, y, a = int(fc.x_anim.value), int(fc.y_anim.value), int(fc.a_anim.value)
            tmp = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            color = fc.color
            pygame.draw.rect(tmp, (*GEM.get(color, (180, 180, 180)), a),
                             (0, 0, CARD_W, CARD_H), border_radius=6)
            surf.blit(tmp, (x, y))

        for fl in self.float_texts:
            s, x, y = fl.update(dt, self.fonts["bold"])
            surf.blit(s, s.get_rect(center=(x, y)))

    def _draw_game_over(self):
        surf    = self.screen
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surf.blit(overlay, (0, 0))

        g = self.game
        winner = g.winner
        title  = self.fonts["title"].render(
            f"{'YOU WIN!' if winner.name == 'You' else 'BOT WINS!'}", True, HIGHLIGHT)
        surf.blit(title, title.get_rect(center=(SW//2, SH//2 - 60)))

        for i, p in enumerate(g.players):
            line = self.fonts["large"].render(
                f"{p.name}: {p.get_points()} points", True, TEXT)
            surf.blit(line, line.get_rect(center=(SW//2, SH//2 - 10 + i*40)))

        hint = self.fonts["normal"].render("Click anywhere to play again", True, DIM)
        surf.blit(hint, hint.get_rect(center=(SW//2, SH//2 + 100)))

    # ── Utilities ──────────────────────────────────────────────────────────────

    @staticmethod
    def _in_rect(mx, my, r):
        return r[0] <= mx < r[0]+r[2] and r[1] <= my < r[1]+r[3]

    def _hit_test(self, mx, my):
        return None   # reserved for future hover state

    def _restart(self):
        self.game          = create_game("You", "Bot")
        self.ui_mode       = UIMode.IDLE
        self.selected_toks = []
        self.status        = "New game!  Your turn."
        self.flying_tokens = []
        self.flying_cards  = []
        self.float_texts   = []
        self.bot_timer     = 0


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    SplendorGame().run()
