"""
main.py — Splendor: Human vs Bot  (Pygame)
"""

import pygame
import sys
import traceback
from game_component.game_factory import create_game
from game_component.game import IDLE, PENDING_RETURN_TOKENS, PENDING_CHOOSE_NOBLE
from bot import bot_make_move

# ── Screen / layout ───────────────────────────────────────────────────────────

SW, SH    = 1280, 720
FPS       = 60
BOT_DELAY = 1000   # ms before bot acts

CARD_W, CARD_H = 126, 130
CARD_GAP       = 9
HIDDEN_W       = 68
ROW_H          = CARD_H + CARD_GAP   # 139
BOARD_X        = 14
BOARD_Y        = 182   # top of first card row

# Card row Y positions
LEVEL_Y = {3: BOARD_Y, 2: BOARD_Y + ROW_H, 1: BOARD_Y + 2 * ROW_H}

# Token bank
TOKEN_R        = 20
TOKEN_ROW_Y    = BOARD_Y + 3 * ROW_H + 14   # ≈599
TOKEN_SPACING  = 64
TOKEN_START_X  = BOARD_X + 16

# Nobles
NOBLE_X, NOBLE_Y = 14, 48
NOBLE_W, NOBLE_H = 114, 120

# Right panel
PANEL_X       = 898
PANEL_W       = SW - PANEL_X - 8
PANEL_H       = 288
HUMAN_PANEL_Y = 48
BOT_PANEL_Y   = 346
BTN_Y         = 644
STATUS_Y      = SH - 44

# ── Colours ───────────────────────────────────────────────────────────────────

GEM = {
    "white": (242, 238, 218),
    "blue":  (65,  128, 182),
    "green": (52,  158, 76),
    "red":   (208, 52,  52),
    "black": (42,  42,  42),
    "gold":  (252, 200, 0),
}
GEM_TEXT = {
    "white": (30,  30,  30),
    "blue":  (255, 255, 255),
    "green": (255, 255, 255),
    "red":   (255, 255, 255),
    "black": (220, 220, 220),
    "gold":  (50,  34,  0),
}
COLOR_ORDER = ["white", "blue", "green", "red", "black"]

BG        = (20, 26, 36)
PANEL_BG  = (34, 42, 58)
CARD_BG   = (198, 190, 170)
TEXT_C    = (228, 222, 208)
DIM_C     = (130, 125, 112)
HILITE    = (255, 212, 40)
AFFORD_G  = (70,  200, 80)
AFFORD_DG = (35,  100, 40)
BTN_N     = (48,  78,  122)
BTN_H     = (72,  112, 168)
BTN_A     = (42,  138, 72)
BTN_DIS   = (52,  55,  66)
MSG_GOOD  = (90,  210, 90)
MSG_WARN  = (210, 155, 40)
MSG_ERR   = (210, 58,  58)

# ── Animation helpers ─────────────────────────────────────────────────────────

def lerp(a, b, t):
    return a + (b - a) * min(t, 1.0)


class FlyToken:
    """Token that slides from bank to player panel."""
    def __init__(self, color, src, dst, dur=340):
        self.color = color
        self.sx, self.sy = src
        self.dx, self.dy = dst
        self.dur = dur
        self.t   = 0.0
        self.done = False

    def update(self, dt):
        self.t += dt / self.dur
        if self.t >= 1.0:
            self.t = 1.0
            self.done = True

    @property
    def pos(self):
        return int(lerp(self.sx, self.dx, self.t)), int(lerp(self.sy, self.dy, self.t))


class FlyCard:
    """Card that slides up and fades when bought/reserved."""
    def __init__(self, rect, color, dur=380):
        self.x, self.y, self.w, self.h = rect
        self.color = color
        self.dur   = dur
        self.t     = 0.0
        self.done  = False

    def update(self, dt):
        self.t += dt / self.dur
        if self.t >= 1.0:
            self.t = 1.0
            self.done = True

    def draw(self, surf):
        t = self.t
        y   = int(self.y - 40 * t)
        a   = int(255 * (1.0 - t))
        tmp = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        c   = GEM.get(self.color, (160, 155, 140))
        pygame.draw.rect(tmp, (*c, a), (0, 0, self.w, self.h), border_radius=6)
        surf.blit(tmp, (self.x, y))


class MsgLog:
    """Scrolling message log — shows last N messages with fade."""
    MAX = 4
    DUR = 3200   # ms

    def __init__(self):
        self.msgs = []   # [(text, elapsed, color)]

    def add(self, text, color=None):
        if color is None:
            color = TEXT_C
        self.msgs.append([text, 0, color])
        if len(self.msgs) > self.MAX:
            self.msgs.pop(0)

    def update(self, dt):
        for m in self.msgs:
            m[1] += dt
        self.msgs = [m for m in self.msgs if m[1] < self.DUR]

    def draw(self, surf, x, y, font):
        for i, (text, elapsed, color) in enumerate(reversed(self.msgs)):
            age = elapsed / self.DUR
            a   = int(255 * (1.0 - age ** 2))
            t   = font.render(text, True, color)
            t.set_alpha(a)
            surf.blit(t, (x, y - i * 20))


# ── Draw primitives ───────────────────────────────────────────────────────────

def rounded(surf, color, rect, r=7, border=0, border_color=None):
    pygame.draw.rect(surf, color, rect, border_radius=r)
    if border:
        pygame.draw.rect(surf, border_color or color, rect, border, border_radius=r)


def darken(c, a=38):
    return tuple(max(0, v - a) for v in c)


def draw_gem(surf, color_name, cx, cy, r=TOKEN_R, label="", font=None):
    c  = GEM[color_name]
    dc = darken(c)
    pygame.draw.circle(surf, c,  (cx, cy), r)
    pygame.draw.circle(surf, dc, (cx, cy), r, 2)
    if label and font:
        t = font.render(label, True, GEM_TEXT[color_name])
        surf.blit(t, t.get_rect(center=(cx, cy)))


def draw_card_face(surf, card, rect, fonts, highlight=False, green_border=False):
    x, y, w, _ = rect
    bonus  = card.color_bonus
    border = GEM.get(bonus, (110, 110, 110))

    rounded(surf, CARD_BG, rect, r=6)
    if highlight:
        pygame.draw.rect(surf, HILITE,    rect, 3, border_radius=6)
    elif green_border:
        pygame.draw.rect(surf, AFFORD_G,  rect, 2, border_radius=6)
    else:
        pygame.draw.rect(surf, border,    rect, 2, border_radius=6)

    # Colour strip
    rounded(surf, border, (x, y, w, 20), r=6)

    # Points
    if card.points > 0:
        pt = fonts["bold"].render(str(card.points), True, TEXT_C)
        surf.blit(pt, (x + 4, y + 22))

    # Cost dots
    cy2 = y + 38
    for color in COLOR_ORDER:
        amt = card.cost.get(color, 0)
        if not amt:
            continue
        pygame.draw.circle(surf, GEM[color],        (x + 10, cy2 + 6), 7)
        pygame.draw.circle(surf, darken(GEM[color]), (x + 10, cy2 + 6), 7, 1)
        n = fonts["small"].render(str(amt), True, TEXT_C)
        surf.blit(n, (x + 21, cy2))
        cy2 += 17


def draw_hidden_btn(surf, deck, rect, fonts, hovering=False):
    x, y, w, h = rect
    empty = deck.hidden_count() == 0 and len(deck.get_face_up_cards()) == 0
    col   = {1: (105, 155, 85), 2: (165, 108, 58), 3: (138, 78, 78)}.get(deck.level, (90, 90, 105))
    if empty:
        col = (48, 50, 60)

    rounded(surf, col, rect, r=6)
    if hovering and not empty:
        pygame.draw.rect(surf, HILITE, rect, 2, border_radius=6)
    else:
        pygame.draw.rect(surf, darken(col, 28), rect, 1, border_radius=6)

    lv = fonts["bold"].render(f"L{deck.level}", True, TEXT_C if not empty else DIM_C)
    surf.blit(lv, lv.get_rect(center=(x + w//2, y + h//2 - 10)))
    cnt = fonts["small"].render(str(deck.hidden_count()), True, TEXT_C if not empty else DIM_C)
    surf.blit(cnt, cnt.get_rect(center=(x + w//2, y + h//2 + 8)))


def draw_noble_tile(surf, noble, rect, fonts, highlight=False):
    x, y, _, h = rect
    rounded(surf, (158, 142, 108), rect, r=6)
    bord = HILITE if highlight else (118, 106, 78)
    pygame.draw.rect(surf, bord, rect, 2 if not highlight else 3, border_radius=6)
    pt = fonts["bold"].render(str(noble.points), True, (28, 28, 28))
    surf.blit(pt, (x + 5, y + 4))
    cy2 = y + 26
    for color, amt in noble.requirement.items():
        pygame.draw.circle(surf, GEM[color],        (x + 12, cy2 + 6), 7)
        pygame.draw.circle(surf, darken(GEM[color]), (x + 12, cy2 + 6), 7, 1)
        n = fonts["small"].render(str(amt), True, (28, 28, 28))
        surf.blit(n, (x + 23, cy2))
        cy2 += 18


def draw_btn(surf, text, rect, fonts, state="normal"):
    col = {"normal": BTN_N, "hover": BTN_H, "active": BTN_A, "disabled": BTN_DIS}[state]
    rounded(surf, col, rect, r=7)
    tc = DIM_C if state == "disabled" else TEXT_C
    t  = fonts["normal"].render(text, True, tc)
    surf.blit(t, t.get_rect(center=(rect[0]+rect[2]//2, rect[1]+rect[3]//2)))


# ── Layout helpers ────────────────────────────────────────────────────────────

def card_slot_rect(level, slot):
    """slot 0 = hidden deck, 1-4 = face-up cards."""
    y = LEVEL_Y[level]
    if slot == 0:
        return (BOARD_X, y, HIDDEN_W, CARD_H)
    x = BOARD_X + HIDDEN_W + CARD_GAP + (slot - 1) * (CARD_W + CARD_GAP)
    return (x, y, CARD_W, CARD_H)


def bank_token_pos(color_idx):
    return (TOKEN_START_X + color_idx * TOKEN_SPACING, TOKEN_ROW_Y + TOKEN_R)


def noble_slot_rect(idx):
    return (NOBLE_X + idx * (NOBLE_W + 8), NOBLE_Y, NOBLE_W, NOBLE_H)


def in_rect(mx, my, r):
    return r[0] <= mx < r[0]+r[2] and r[1] <= my < r[1]+r[3]


def in_circle(mx, my, cx, cy, r):
    return (mx - cx) ** 2 + (my - cy) ** 2 <= r * r


# ── UI Mode constants ─────────────────────────────────────────────────────────

class UM:
    IDLE         = "IDLE"
    TAKE_TOKENS  = "TAKE_TOKENS"
    BUY_CARD     = "BUY_CARD"
    RESERVE_CARD = "RESERVE_CARD"
    BUY_RESERVED = "BUY_RESERVED"
    PEND_RETURN  = "PEND_RETURN"
    PEND_NOBLE   = "PEND_NOBLE"
    BOT_TURN     = "BOT_TURN"
    GAME_OVER    = "GAME_OVER"


# ── Main game ─────────────────────────────────────────────────────────────────

class SplendorApp:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SW, SH))
        pygame.display.set_caption("Splendor — Human vs Bot")
        self.clock  = pygame.time.Clock()

        self.fonts = {
            "title":  pygame.font.SysFont("segoeui", 32, bold=True),
            "large":  pygame.font.SysFont("segoeui", 22, bold=True),
            "bold":   pygame.font.SysFont("segoeui", 15, bold=True),
            "normal": pygame.font.SysFont("segoeui", 14),
            "small":  pygame.font.SysFont("segoeui", 12),
        }
        self._new_game()

    def _new_game(self):
        self.game      = create_game("You", "Bot")
        self.mode      = UM.IDLE
        self.sel_toks  = []     # token colours chosen so far
        self.status    = "Your turn — choose an action."
        self.bot_timer = 0
        self.fly_toks  = []
        self.fly_cards = []
        self.msg_log   = MsgLog()

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self._events()
            self._update(dt)
            self._draw()
            pygame.display.flip()

    # ── Events ────────────────────────────────────────────────────────────────

    def _events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self._cancel_mode()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self._click(*ev.pos)

    def _cancel_mode(self):
        if self.mode in (UM.IDLE, UM.BOT_TURN, UM.GAME_OVER,
                         UM.PEND_RETURN, UM.PEND_NOBLE):
            return
        self.mode     = UM.IDLE
        self.sel_toks = []
        self.status   = "Cancelled — choose an action."

    def _click(self, mx, my):
        m = self.mode
        g = self.game
        gp = g.get_pending_state()

        if m == UM.GAME_OVER:
            self._new_game(); return

        if gp == PENDING_CHOOSE_NOBLE:
            self._on_noble_choice(mx, my); return

        if gp == PENDING_RETURN_TOKENS:
            self._on_return_token(mx, my); return

        if m == UM.BOT_TURN:
            return

        # Action buttons always checked first
        btn = self._hit_btn(mx, my)
        if btn:
            self._on_btn(btn); return

        if m == UM.TAKE_TOKENS:  self._on_token_click(mx, my)
        elif m == UM.BUY_CARD:    self._on_buy_card(mx, my)
        elif m == UM.RESERVE_CARD: self._on_reserve(mx, my)
        elif m == UM.BUY_RESERVED: self._on_buy_reserved(mx, my)

    # ── Buttons ───────────────────────────────────────────────────────────────

    def _btn_rects(self):
        bw, bh, g = 180, 34, 8
        x, y = PANEL_X, BTN_Y
        return {
            "take":    (x,      y,          bw, bh),
            "buy":     (x+bw+g, y,          bw, bh),
            "reserve": (x,      y+bh+g,     bw, bh),
            "buy_res": (x+bw+g, y+bh+g,     bw, bh),
            "confirm": (x,      y+2*(bh+g), bw*2+g, bh),
        }

    def _hit_btn(self, mx, my):
        for name, r in self._btn_rects().items():
            if in_rect(mx, my, r):
                return name
        return None

    def _on_btn(self, btn):
        m = self.mode
        if btn == "take" and m == UM.IDLE:
            self.mode = UM.TAKE_TOKENS; self.sel_toks = []
            self.status = "Click tokens to select (3 different, or same colour twice for 2)."
        elif btn == "buy" and m == UM.IDLE:
            self.mode   = UM.BUY_CARD
            self.status = "Click a card to buy it."
        elif btn == "reserve" and m == UM.IDLE:
            self.mode   = UM.RESERVE_CARD
            self.status = "Click a card (or hidden deck) to reserve."
        elif btn == "buy_res" and m == UM.IDLE:
            if self.game.players[0].reserved_cards:
                self.mode   = UM.BUY_RESERVED
                self.status = "Click one of your reserved cards to buy."
            else:
                self.status = "No reserved cards."
        elif btn == "confirm" and m == UM.TAKE_TOKENS:
            self._do_take_tokens()

    # ── Token selection ───────────────────────────────────────────────────────

    def _on_token_click(self, mx, my):
        all_colors = COLOR_ORDER + ["gold"]
        for i, color in enumerate(all_colors):
            if color == "gold":
                continue
            cx, cy = bank_token_pos(i)
            if in_circle(mx, my, cx, cy, TOKEN_R + 4):
                self._pick_token(color)
                return

    def _pick_token(self, color):
        sel  = self.sel_toks
        bank = self.game.board.token_bank

        # Deselect if already chosen (and not in 2-same mode)
        if color in sel and not (len(sel) == 2 and sel[0] == sel[1]):
            sel.remove(color)
            self.status = f"Deselected {color}.  Selected: {sel or 'nothing'}"
            return

        # 2-same: click same colour twice
        if sel == [color]:
            if bank.can_take_two_same(color):
                sel.append(color)
                self.status = f"Taking 2×{color}.  Press Confirm."
            else:
                self.status = f"Need ≥4 {color} in bank to take 2."
            return

        if len(sel) == 2 and sel[0] == sel[1]:
            self.status = "Already selected 2 same — confirm or Esc."
            return

        if bank.tokens.get(color, 0) < 1:
            self.status = f"No {color} tokens in bank."; return

        if len(sel) >= 3:
            self.status = "3 tokens already selected — confirm or Esc."; return

        sel.append(color)
        if len(sel) == 3:
            self._do_take_tokens()   # auto-confirm at 3
        else:
            self.status = f"Selected: {sel}  (click more or Confirm)"

    def _do_take_tokens(self):
        if not self.sel_toks:
            self.status = "Select at least 1 token."; return
        ok = self.game.take_tokens(self.sel_toks)
        if ok:
            self.msg_log.add(f"Took: {', '.join(self.sel_toks)}", MSG_GOOD)
            self._spawn_fly_toks(self.sel_toks)
            self.sel_toks = []
            self._after_human()
        else:
            self.status = "Invalid token selection — try again."

    def _spawn_fly_toks(self, colors):
        all_c = COLOR_ORDER + ["gold"]
        for color in colors:
            if color in all_c:
                i   = all_c.index(color)
                src = bank_token_pos(i)
                dst = (PANEL_X + 20 + len(self.fly_toks) * 30, HUMAN_PANEL_Y + 70)
                self.fly_toks.append(FlyToken(color, src, dst))

    # ── Buy face-up card ──────────────────────────────────────────────────────

    def _on_buy_card(self, mx, my):
        for level in [1, 2, 3]:
            deck = self.game._get_deck(level)
            if deck is None: continue
            for i, card in enumerate(deck.get_face_up_cards()):
                r = card_slot_rect(level, i + 1)
                if in_rect(mx, my, r):
                    ok = self.game.buy_card(level, i)
                    if ok:
                        self.fly_cards.append(FlyCard(r, card.color_bonus))
                        pts = card.points
                        self.msg_log.add(
                            f"Bought L{level} {card.color_bonus} card"
                            + (f" (+{pts}pt)" if pts else ""), MSG_GOOD)
                        self._after_human()
                    else:
                        self.msg_log.add("Can't afford that card.", MSG_WARN)
                        self.mode = UM.IDLE
                        self.status = "Can't afford — choose another action."
                    return

    # ── Reserve card ─────────────────────────────────────────────────────────

    def _on_reserve(self, mx, my):
        g      = self.game
        player = g.players[0]
        if not player.can_reserve():
            self.msg_log.add("Already have 3 reserved cards.", MSG_WARN)
            self.mode = UM.IDLE; return

        # Face-up card
        for level in [1, 2, 3]:
            deck = g._get_deck(level)
            if deck is None: continue
            for i, card in enumerate(deck.get_face_up_cards()):
                r = card_slot_rect(level, i + 1)
                if in_rect(mx, my, r):
                    ok = g.reserve_card(level, i)
                    if ok:
                        self.fly_cards.append(FlyCard(r, card.color_bonus))
                        self.msg_log.add(f"Reserved L{level} {card.color_bonus} card.", MSG_GOOD)
                        self._after_human()
                    return

        # Hidden deck button
        for level in [1, 2, 3]:
            r = card_slot_rect(level, 0)
            if in_rect(mx, my, r):
                ok = g.reserve_hidden_card(level)
                if ok:
                    self.msg_log.add(f"Reserved hidden L{level} card.", MSG_GOOD)
                    self._after_human()
                else:
                    self.msg_log.add("Deck empty.", MSG_WARN)
                    self.mode = UM.IDLE
                return

    # ── Buy reserved card ─────────────────────────────────────────────────────

    def _on_buy_reserved(self, mx, my):
        player = self.game.players[0]
        for i in range(len(player.reserved_cards)):
            r = self._reserved_card_rect(i)
            if in_rect(mx, my, r):
                ok = self.game.buy_reserved_card(i)
                if ok:
                    card = player.cards_owned[-1]
                    self.msg_log.add(f"Bought reserved card (+{card.points}pt).", MSG_GOOD)
                    self._after_human()
                else:
                    self.msg_log.add("Can't afford that reserved card.", MSG_WARN)
                    self.mode = UM.IDLE
                return

    def _reserved_card_rect(self, slot):
        ry = HUMAN_PANEL_Y + PANEL_H - 108
        rx = PANEL_X + 8 + slot * 76
        return (rx, ry, 70, 96)

    # ── Pending states ────────────────────────────────────────────────────────

    def _on_return_token(self, mx, my):
        player = self.game.current_player
        # Click own tokens shown in human panel
        all_c = COLOR_ORDER + ["gold"]
        for i, color in enumerate(all_c):
            cx, cy = PANEL_X + 14 + i * 56 + 14, HUMAN_PANEL_Y + 68
            if in_circle(mx, my, cx, cy, 16) and player.tokens.get(color, 0) > 0:
                ok = self.game.resolve_return_token(color)
                if ok:
                    self.msg_log.add(f"Returned {color} token.", MSG_WARN)
                    if self.game.get_pending_state() == PENDING_RETURN_TOKENS:
                        self.status = "Still over 10 — return another token."
                    else:
                        self._after_human()
                return

    def _on_noble_choice(self, mx, my):
        pending = self.game.get_pending_nobles()
        board_nobles = self.game.board.nobles
        for i, noble in enumerate(pending):
            try:
                board_idx = board_nobles.index(noble)
            except ValueError:
                board_idx = i
            r = noble_slot_rect(board_idx)
            if in_rect(mx, my, r):
                ok = self.game.resolve_choose_noble(i)
                if ok:
                    self.msg_log.add(f"Received noble (+{noble.points}pt)!", MSG_GOOD)
                    self._after_human()
                return

    # ── Post-action routing ───────────────────────────────────────────────────

    def _after_human(self):
        self.mode = UM.IDLE
        g = self.game
        if g.game_over:
            self.mode   = UM.GAME_OVER; return

        gp = g.get_pending_state()
        if gp == PENDING_RETURN_TOKENS:
            self.mode   = UM.PEND_RETURN
            self.status = "Over 10 tokens — click a token in YOUR panel to return one."
            return
        if gp == PENDING_CHOOSE_NOBLE:
            self.mode   = UM.PEND_NOBLE
            self.status = "Multiple nobles — click one to accept."
            return

        if g.current_player.name == "You":
            self.status = "Your turn — choose an action."
        else:
            self.mode      = UM.BOT_TURN
            self.bot_timer = BOT_DELAY
            self.status    = "Bot is thinking…"

    def _after_bot(self):
        g = self.game
        if g.game_over:
            self.mode = UM.GAME_OVER; return

        gp = g.get_pending_state()
        # Bot pending states resolved internally in bot_make_move
        if gp != IDLE:
            # Shouldn't happen — bot resolves own pending states
            self.mode      = UM.BOT_TURN
            self.bot_timer = 200
            return

        if g.current_player.name == "You":
            self.mode   = UM.IDLE
            self.status = "Your turn — choose an action."
        else:
            self.mode      = UM.BOT_TURN
            self.bot_timer = BOT_DELAY

    # ── Update ────────────────────────────────────────────────────────────────

    def _update(self, dt):
        # Bot
        if self.mode == UM.BOT_TURN and not self.game.game_over:
            self.bot_timer -= dt
            if self.bot_timer <= 0:
                try:
                    bot_make_move(self.game)
                except Exception:
                    traceback.print_exc()
                    self.msg_log.add("Bot error — skipping turn.", MSG_ERR)
                    # Force advance turn
                    self.game.current_player_index = (
                        (self.game.current_player_index + 1) % len(self.game.players))
                self._after_bot()

        # Animations
        for ft in self.fly_toks:  ft.update(dt)
        for fc in self.fly_cards: fc.update(dt)
        self.fly_toks  = [f for f in self.fly_toks  if not f.done]
        self.fly_cards = [f for f in self.fly_cards if not f.done]
        self.msg_log.update(dt)

    # ── Draw ──────────────────────────────────────────────────────────────────

    def _draw(self):
        s = self.screen
        s.fill(BG)
        self._draw_title()
        self._draw_nobles()
        self._draw_board()
        self._draw_bank()
        self._draw_panels()
        self._draw_buttons()
        self._draw_status()
        self._draw_anims()
        if self.mode == UM.GAME_OVER:
            self._draw_gameover()

    # -- Title bar
    def _draw_title(self):
        t = self.fonts["title"].render("SPLENDOR", True, HILITE)
        self.screen.blit(t, (10, 6))
        g = self.game
        info = self.fonts["normal"].render(
            f"Round {g.round_number}  ·  {g.current_player.name}'s turn", True, DIM_C)
        self.screen.blit(info, info.get_rect(midright=(SW - 10, 18)))

    # -- Nobles
    def _draw_nobles(self):
        s  = self.screen
        g  = self.game
        pending = g.get_pending_nobles() if g.get_pending_state() == PENDING_CHOOSE_NOBLE else []
        lbl = self.fonts["bold"].render("Nobles", True, DIM_C)
        s.blit(lbl, (NOBLE_X, NOBLE_Y - 16))
        for i, noble in enumerate(g.board.nobles):
            draw_noble_tile(s, noble, noble_slot_rect(i), self.fonts, highlight=noble in pending)

    # -- Board (card rows)
    def _draw_board(self):
        s    = self.screen
        g    = self.game
        m    = self.mode
        mx, my = pygame.mouse.get_pos()
        human  = g.players[0]

        for level in [3, 2, 1]:
            deck = g._get_deck(level)
            if deck is None: continue

            # Hidden deck button
            r0  = card_slot_rect(level, 0)
            hov = in_rect(mx, my, r0) and m == UM.RESERVE_CARD
            draw_hidden_btn(s, deck, r0, self.fonts, hovering=hov)

            for i, card in enumerate(deck.get_face_up_cards()):
                r    = card_slot_rect(level, i + 1)
                hov  = in_rect(mx, my, r)
                can  = human.can_afford(card)
                hl   = hov and m in (UM.BUY_CARD, UM.RESERVE_CARD)
                green = can and m == UM.BUY_CARD and not hl
                draw_card_face(s, card, r, self.fonts, highlight=hl, green_border=green)

    # -- Token bank
    def _draw_bank(self):
        s    = self.screen
        bank = self.game.board.token_bank
        m    = self.mode
        mx, my = pygame.mouse.get_pos()
        all_c  = COLOR_ORDER + ["gold"]

        lbl = self.fonts["bold"].render("Token Bank", True, DIM_C)
        s.blit(lbl, (TOKEN_START_X - 4, TOKEN_ROW_Y - 18))

        for i, color in enumerate(all_c):
            cx, cy = bank_token_pos(i)
            amt    = bank.tokens.get(color, 0)
            sel    = color in self.sel_toks

            if amt == 0 and not sel:
                pygame.draw.circle(s, (48, 50, 62), (cx, cy), TOKEN_R)
                pygame.draw.circle(s, (62, 64, 76), (cx, cy), TOKEN_R, 1)
            else:
                hover  = in_circle(mx, my, cx, cy, TOKEN_R + 4)
                selectable = m == UM.TAKE_TOKENS and color != "gold"
                ring_color = HILITE if sel else (AFFORD_G if selectable and hover else None)
                if ring_color:
                    pygame.draw.circle(s, ring_color, (cx, cy), TOKEN_R + 4)
                draw_gem(s, color, cx, cy, TOKEN_R, label=str(amt), font=self.fonts["bold"])

            name = self.fonts["small"].render(color[:3].upper(), True, DIM_C)
            s.blit(name, name.get_rect(center=(cx, cy + TOKEN_R + 10)))

        # Selected count hint
        if m == UM.TAKE_TOKENS and self.sel_toks:
            hint = self.fonts["small"].render(
                f"Selected: {self.sel_toks}  (Confirm or click more)", True, HILITE)
            s.blit(hint, (TOKEN_START_X, TOKEN_ROW_Y + TOKEN_R * 2 + 14))

    # -- Player panels
    def _draw_panels(self):
        g         = self.game
        is_your_t = g.current_player.name == "You"
        self._draw_player_panel(g.players[0], HUMAN_PANEL_Y, is_your_t, is_human=True)
        self._draw_player_panel(g.players[1], BOT_PANEL_Y,   not is_your_t, is_human=False)

    def _draw_player_panel(self, player, py, active, is_human):
        s   = self.screen
        px  = PANEL_X
        pw  = PANEL_W
        ph  = PANEL_H
        bg  = (44, 58, 80) if active else PANEL_BG

        rounded(s, bg, (px, py, pw, ph), r=8)
        bord = HILITE if active else (55, 65, 88)
        pygame.draw.rect(s, bord, (px, py, pw, ph), 2, border_radius=8)

        # Name + points
        who  = "YOU" if is_human else "BOT"
        name = self.fonts["bold"].render(f"{who} — {player.name}", True, HILITE if active else TEXT_C)
        s.blit(name, (px + 10, py + 7))
        pts = self.fonts["large"].render(str(player.get_points()), True, HILITE if active else TEXT_C)
        s.blit(pts, pts.get_rect(topright=(px + pw - 10, py + 4)))
        s.blit(self.fonts["small"].render("pts", True, DIM_C), (px + pw - 10 - pts.get_width() - 22, py + 12))

        # Tokens
        all_c = COLOR_ORDER + ["gold"]
        tx, ty = px + 10, py + 36
        for i, color in enumerate(all_c):
            cx, cy = tx + i * 56 + 14, ty + 14
            amt    = player.tokens[color]
            # Clickable in PEND_RETURN if human and has tokens
            click_hint = (self.mode == UM.PEND_RETURN and is_human and amt > 0)
            if click_hint:
                mx2, my2 = pygame.mouse.get_pos()
                if in_circle(mx2, my2, cx, cy, 16):
                    pygame.draw.circle(s, HILITE, (cx, cy), 19)
            if amt > 0:
                pygame.draw.circle(s, GEM[color],        (cx, cy), 14)
                pygame.draw.circle(s, darken(GEM[color]), (cx, cy), 14, 1)
                n = self.fonts["small"].render(str(amt), True, GEM_TEXT[color])
                s.blit(n, n.get_rect(center=(cx, cy)))
            else:
                pygame.draw.circle(s, (50, 52, 64), (cx, cy), 14)

        # Bonus cards
        bonus = player.get_bonus_count()
        bx, by2 = px + 10, py + 80
        bl = self.fonts["small"].render("Bonus:", True, DIM_C)
        s.blit(bl, (bx, by2))
        bx += 48
        for color in COLOR_ORDER:
            amt = bonus[color]
            pygame.draw.circle(s, GEM[color],        (bx + 8, by2 + 7), 7)
            pygame.draw.circle(s, darken(GEM[color]), (bx + 8, by2 + 7), 7, 1)
            n = self.fonts["small"].render(str(amt), True, TEXT_C)
            s.blit(n, (bx + 18, by2 + 1))
            bx += 44

        # Reserved cards
        rl = self.fonts["small"].render("Reserved:", True, DIM_C)
        s.blit(rl, (px + 10, py + PANEL_H - 118))
        for i, card in enumerate(player.reserved_cards):
            r  = self._reserved_card_rect(i)  if is_human else (px + 10 + i*72, py + PANEL_H - 98, 66, 86)
            hl = (self.mode == UM.BUY_RESERVED and is_human and
                  in_rect(*pygame.mouse.get_pos(), r))
            can = player.can_afford(card)
            bg2 = CARD_BG
            rounded(s, bg2, r, r=5)
            brd = HILITE if hl else (AFFORD_G if can and is_human else GEM.get(card.color_bonus, (100,100,100)))
            pygame.draw.rect(s, brd, r, 2, border_radius=5)
            if card.points > 0:
                p = self.fonts["small"].render(str(card.points), True, TEXT_C)
                s.blit(p, (r[0]+3, r[1]+2))
            cy2 = r[1] + 16
            for color in COLOR_ORDER:
                amt2 = card.cost.get(color, 0)
                if not amt2: continue
                pygame.draw.circle(s, GEM[color], (r[0]+8, cy2+5), 5)
                a2 = self.fonts["small"].render(str(amt2), True, TEXT_C)
                s.blit(a2, (r[0]+16, cy2))
                cy2 += 13

        # Nobles
        if player.nobles:
            for i, n in enumerate(player.nobles):
                nx = px + 10 + i * 32
                ny = py + PANEL_H - 24
                rounded(s, (158, 142, 108), (nx, ny, 26, 20), r=3)
                t = self.fonts["small"].render(str(n.points), True, (28, 28, 28))
                s.blit(t, t.get_rect(center=(nx+13, ny+10)))

    # -- Buttons
    def _draw_buttons(self):
        s     = self.screen
        m     = self.mode
        mx, my = pygame.mouse.get_pos()
        btns  = self._btn_rects()
        human_active = m in (UM.IDLE, UM.TAKE_TOKENS, UM.BUY_CARD,
                              UM.RESERVE_CARD, UM.BUY_RESERVED)

        label = {"take": "Take Tokens", "buy": "Buy Card",
                 "reserve": "Reserve Card", "buy_res": "Buy Reserved"}
        mode_map = {"take": UM.TAKE_TOKENS, "buy": UM.BUY_CARD,
                    "reserve": UM.RESERVE_CARD, "buy_res": UM.BUY_RESERVED}

        for name in ("take", "buy", "reserve", "buy_res"):
            r     = btns[name]
            if not human_active:
                draw_btn(s, label[name], r, self.fonts, "disabled")
                continue
            is_act  = m == mode_map[name]
            is_hov  = in_rect(mx, my, r)
            state   = "active" if is_act else ("hover" if is_hov else "normal")
            draw_btn(s, label[name], r, self.fonts, state)

        # Confirm button — only in TAKE_TOKENS
        if m == UM.TAKE_TOKENS:
            r   = btns["confirm"]
            has = bool(self.sel_toks)
            st  = ("hover" if in_rect(mx, my, r) and has else
                   "active" if has else "disabled")
            draw_btn(s, "✔  Confirm Take", r, self.fonts, st)

        # ESC hint
        if m not in (UM.IDLE, UM.BOT_TURN, UM.GAME_OVER, UM.PEND_RETURN, UM.PEND_NOBLE):
            hint = self.fonts["small"].render("Esc = cancel", True, DIM_C)
            s.blit(hint, (PANEL_X, BTN_Y - 18))

    # -- Status bar + message log
    def _draw_status(self):
        s  = self.screen
        gp = self.game.get_pending_state()

        msg = self.status
        if gp == PENDING_RETURN_TOKENS:
            msg = "⚠  Over 10 tokens — click a token in YOUR panel to return one."
        elif gp == PENDING_CHOOSE_NOBLE:
            msg = "✦  Multiple nobles qualify — click one to accept."

        pygame.draw.rect(s, PANEL_BG, (0, STATUS_Y - 6, SW, SH - STATUS_Y + 6))
        t = self.fonts["normal"].render(msg, True, TEXT_C)
        s.blit(t, (12, STATUS_Y + 8))

        # Message log at top-right of board area
        self.msg_log.draw(s, BOARD_X + 4, LEVEL_Y[3] - 8, self.fonts["small"])

    # -- Animations
    def _draw_anims(self):
        s = self.screen
        for ft in self.fly_toks:
            cx, cy = ft.pos
            draw_gem(s, ft.color, cx, cy, TOKEN_R - 2)
        for fc in self.fly_cards:
            fc.draw(s)

    # -- Game over overlay
    def _draw_gameover(self):
        s    = self.screen
        ov   = pygame.Surface((SW, SH), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 168))
        s.blit(ov, (0, 0))

        g      = self.game
        winner = g.winner
        you_win = winner and winner.name == "You"
        col    = MSG_GOOD if you_win else MSG_ERR
        title  = self.fonts["title"].render(
            "YOU WIN! 🎉" if you_win else "BOT WINS!", True, col)
        s.blit(title, title.get_rect(center=(SW//2, SH//2 - 70)))

        for i, p in enumerate(g.players):
            line = self.fonts["large"].render(
                f"{p.name}:  {p.get_points()} pts", True, TEXT_C)
            s.blit(line, line.get_rect(center=(SW//2, SH//2 - 20 + i * 36)))

        hint = self.fonts["normal"].render("Click anywhere to play again", True, DIM_C)
        s.blit(hint, hint.get_rect(center=(SW//2, SH//2 + 90)))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    SplendorApp().run()
