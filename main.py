"""
main.py — Splendor: Human vs Bot  (Pygame)

Layout (1280×720):
  Col A (0–790):   Board – nobles + 3 card rows
  Col B (795–985): Token bank (vertical) + action buttons
  Col C (990–1275): Player panels (You / Bot)
  Bottom 40 px:    Status bar
"""

import pygame
import sys
import os
import math
import traceback
from game_component.game_factory import create_game
from game_component.game import IDLE, PENDING_RETURN_TOKENS, PENDING_CHOOSE_NOBLE
from bot import bot_make_move

# ── Image assets (optional — place files in assets/ to enable) ────────────────
# Expected files:
#   assets/bg.png               — 1280×720 board background
#   assets/token_white.png      — ~60×60 circular token images (transparent PNG)
#   assets/token_blue.png
#   assets/token_green.png
#   assets/token_red.png
#   assets/token_black.png
#   assets/token_gold.png
#   assets/noble_0.png … noble_9.png  — ~118×122 noble portrait images
#   assets/card_bg_L1.png             — card illustration per level (overlaid)
#   assets/card_bg_L2.png
#   assets/card_bg_L3.png

def _load_img(path, size=None):
    """Load an image if it exists; return None otherwise."""
    if not os.path.exists(path):
        return None
    img = pygame.image.load(path).convert_alpha()
    if size:
        img = pygame.transform.smoothscale(img, size)
    return img

_CARD_COUNTS = {1: 8, 2: 6, 3: 4}
_GEM_COLORS  = ["white", "blue", "green", "red", "black"]

def _load_assets():
    base = os.path.join(os.path.dirname(__file__), "assets")
    assets = {}
    assets["bg"]       = _load_img(os.path.join(base, "bg.png"),       (1280, 720))
    assets["start_bg"] = _load_img(os.path.join(base, "start_bg.png"), (1280, 720))
    for color in _GEM_COLORS + ["gold"]:
        assets[f"token_{color}"] = _load_img(
            os.path.join(base, f"token_{color}.png"), (52, 52))
    # Per-card images (card_L{level}_{color}_{index}.png); fall back to card_bg_L{level}.png
    for lv, count in _CARD_COUNTS.items():
        assets[f"card_bg_L{lv}"] = _load_img(
            os.path.join(base, f"card_bg_L{lv}.png"), (148, 152))
        for color in _GEM_COLORS:
            for i in range(count):
                key = f"card_L{lv}_{color}_{i}"
                assets[key] = _load_img(os.path.join(base, f"{key}.png"), (148, 152))
    for i in range(10):
        assets[f"noble_{i}"] = _load_img(
            os.path.join(base, f"noble_{i}.png"), (118, 122))
    return assets

# ── Screen ────────────────────────────────────────────────────────────────────
SW, SH  = 1280, 720
FPS     = 60
BOT_DELAY = 1000

# ── Layout ────────────────────────────────────────────────────────────────────

# Col A – board
BOARD_X  = 8
CARD_W, CARD_H = 148, 152
CARD_GAP = 8
HIDDEN_W = 76
ROW_H    = CARD_H + CARD_GAP        # 160
BOARD_Y  = 176                       # top of card rows

NOBLE_X, NOBLE_Y = 8, 52
NOBLE_W, NOBLE_H = 118, 120

# Col B – tokens + buttons
MID_X    = 796
MID_W    = 188
MID_CX   = MID_X + MID_W // 2      # 890 (token column centre x)
TOKEN_R  = 26
TOK_Y0   = 62                        # centre y of first token row
TOK_DY   = 70                        # gap between token rows

BTN_X    = MID_X + 4
BTN_W    = MID_W - 8
BTN_H    = 36
BTN_DY   = BTN_H + 8
BTN_Y0   = 510                       # top of first action button

# Col C – player panels
PANEL_X  = 992
PANEL_W  = SW - PANEL_X - 6
PANEL_H  = 290
HUMAN_Y  = 8
BOT_Y    = 310

STATUS_Y = SH - 40

# ── Colours ───────────────────────────────────────────────────────────────────
GEM = {
    "white": (242, 238, 218),
    "blue":  (62,  126, 184),
    "green": (48,  160, 74),
    "red":   (210, 50,  50),
    "black": (40,  40,  40),
    "gold":  (252, 200, 0),
}
GEM_DARK = {k: tuple(max(0, v - 45) for v in c) for k, c in GEM.items()}
GEM_TEXT = {
    "white": (30, 30, 30), "blue": (255,255,255), "green": (255,255,255),
    "red":   (255,255,255), "black": (220,220,220), "gold":  (50, 34, 0),
}
COLOR_ORDER = ["white", "blue", "green", "red", "black"]

BG       = (26, 18, 12)
PANEL_BG = (40, 30, 20)
DIVIDER  = (62, 48, 34)
TEXT_C   = (228, 220, 204)
DIM_C    = (122, 112, 96)
HILITE   = (252, 210, 40)
AFFORD_G = (68, 200, 78)
BTN_N    = (56, 80, 128)
BTN_H_C  = (80, 118, 178)
BTN_A    = (40, 140, 68)
BTN_DIS  = (50, 52, 64)
TOAST_OK = (80, 210, 88)
TOAST_WN = (210, 158, 40)
TOAST_ER = (210, 58,  58)
TOAST_BG = (16, 14, 12)

# ── Card background colour ────────────────────────────────────────────────────
_CARD_BASE = (192, 184, 164)

def card_bg(level, bonus):
    tint = {1: 0.14, 2: 0.26, 3: 0.44}[level]
    g = GEM.get(bonus, (180, 175, 165))
    return tuple(int(_CARD_BASE[i] * (1 - tint) + g[i] * tint) for i in range(3))


# ── Animations ────────────────────────────────────────────────────────────────

def lerp(a, b, t):
    return a + (b - a) * min(max(t, 0.0), 1.0)


class FlyToken:
    def __init__(self, color, src, dst, dur=320):
        self.color = color
        self.sx, self.sy = src
        self.dx, self.dy = dst
        self.dur = dur
        self.t   = 0.0
        self.done = False

    def update(self, dt):
        self.t += dt / self.dur
        if self.t >= 1.0:
            self.t = 1.0; self.done = True

    @property
    def pos(self):
        return int(lerp(self.sx, self.dx, self.t)), int(lerp(self.sy, self.dy, self.t))


class FlyCard:
    def __init__(self, rect, color, dur=360):
        self.x, self.y, self.w, self.h = rect
        self.color = color
        self.dur = dur
        self.t   = 0.0
        self.done = False

    def update(self, dt):
        self.t += dt / self.dur
        if self.t >= 1.0:
            self.t = 1.0; self.done = True

    def draw(self, surf):
        y = int(self.y - 50 * self.t)
        a = int(255 * (1.0 - self.t))
        tmp = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        c = GEM.get(self.color, (160, 155, 140))
        pygame.draw.rect(tmp, (*c, a), (0, 0, self.w, self.h), border_radius=7)
        surf.blit(tmp, (self.x, y))


class Toast:
    """Message that appears in the centre of the board and fades out."""
    def __init__(self, text, color=TEXT_C, dur=1800):
        self.text = text
        self.color = color
        self.dur  = dur
        self.t    = 0.0
        self.done = False

    def update(self, dt):
        self.t += dt / self.dur
        if self.t >= 1.0:
            self.done = True

    @property
    def alpha(self):
        # Fade in first 15 %, fade out last 30 %
        t = self.t
        if t < 0.15:
            return int(255 * t / 0.15)
        if t > 0.70:
            return int(255 * (1.0 - t) / 0.30)
        return 255

    def draw(self, surf, cx, cy, font):
        a = self.alpha
        if a <= 0:
            return
        # Slide upward slightly
        y = cy - int(20 * self.t)
        ts = font.render(self.text, True, self.color)
        pad = 14
        bw, bh = ts.get_width() + pad * 2, ts.get_height() + pad
        box = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(box, (*TOAST_BG, min(a, 200)), (0, 0, bw, bh), border_radius=8)
        box.blit(ts, (pad, pad // 2))
        box.set_alpha(a)
        surf.blit(box, box.get_rect(center=(cx, y)))


# ── Layout helpers ────────────────────────────────────────────────────────────

def card_slot_rect(level, slot):
    """slot 0 = hidden deck button, 1–4 = face-up cards."""
    row = 3 - level          # level3→row0, level2→row1, level1→row2
    y   = BOARD_Y + row * ROW_H
    if slot == 0:
        return (BOARD_X, y, HIDDEN_W, CARD_H)
    x = BOARD_X + HIDDEN_W + CARD_GAP + (slot - 1) * (CARD_W + CARD_GAP)
    return (x, y, CARD_W, CARD_H)


def noble_rect(idx):
    return (NOBLE_X + idx * (NOBLE_W + 8), NOBLE_Y, NOBLE_W, NOBLE_H)


def tok_center(idx):
    """Centre (x, y) of the idx-th token in the bank column."""
    return (MID_CX, TOK_Y0 + idx * TOK_DY)


def btn_rect(row):
    return (BTN_X, BTN_Y0 + row * BTN_DY, BTN_W, BTN_H)


def board_centre():
    bx = BOARD_X + (BOARD_X + HIDDEN_W + CARD_GAP + 4 * (CARD_W + CARD_GAP)) // 2
    by = BOARD_Y + 3 * ROW_H // 2
    return bx, by


def in_rect(mx, my, r):
    return r[0] <= mx < r[0] + r[2] and r[1] <= my < r[1] + r[3]


def in_circ(mx, my, cx, cy, r):
    return (mx - cx) ** 2 + (my - cy) ** 2 <= r * r


# ── Draw primitives ───────────────────────────────────────────────────────────

def rnd(surf, col, rect, r=7, border=0, bcol=None):
    pygame.draw.rect(surf, col, rect, border_radius=r)
    if border:
        pygame.draw.rect(surf, bcol or col, rect, border, border_radius=r)


def gem_circle(surf, color_name, cx, cy, r=TOKEN_R, label="", font=None, alpha=255,
               img=None):
    if img:
        size = r * 2
        scaled = pygame.transform.smoothscale(img, (size, size)).convert_alpha()
        # Clip to a smaller radius to strip the white border ring from the image
        clip_r = max(r - 4, 1)
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (r, r), clip_r)
        scaled.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        if alpha < 255:
            scaled.set_alpha(alpha)
        surf.blit(scaled, (cx - r, cy - r))
        if label and font:
            t = font.render(label, True, GEM_TEXT.get(color_name, (255, 255, 255)))
            surf.blit(t, t.get_rect(center=(cx, cy)))
        return
    if alpha < 255:
        tmp = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        _draw_gem_on(tmp, color_name, r + 1, r + 1, r, label, font)
        tmp.set_alpha(alpha)
        surf.blit(tmp, (cx - r - 1, cy - r - 1))
    else:
        _draw_gem_on(surf, color_name, cx, cy, r, label, font)


def _draw_gem_on(surf, color_name, cx, cy, r, label, font):
    c  = GEM[color_name]
    dc = GEM_DARK[color_name]
    # Outer ring
    pygame.draw.circle(surf, dc, (cx, cy), r)
    # Main fill
    pygame.draw.circle(surf, c,  (cx, cy), r - 2)
    # Highlight (top-left arc feel)
    hl = tuple(min(255, v + 60) for v in c)
    pygame.draw.circle(surf, hl, (cx - r // 4, cy - r // 4), r // 4)
    if label and font:
        t = font.render(label, True, GEM_TEXT[color_name])
        surf.blit(t, t.get_rect(center=(cx, cy)))


def draw_star(surf, cx, cy, r_outer, r_inner, color):
    pts = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    pygame.draw.polygon(surf, color, pts)


def draw_card(surf, card, rect, fonts, hl=False, green=False, assets=None):
    x, y, w, h = rect
    bg = card_bg(card.level, card.color_bonus)
    border = GEM.get(card.color_bonus, (110, 110, 110))

    rnd(surf, bg, rect, r=7)
    card_img = None
    if assets:
        idx = getattr(card, "_image_index", 0)
        card_img = (assets.get(f"card_L{card.level}_{card.color_bonus}_{idx}")
                    or assets.get(f"card_bg_L{card.level}"))
    if card_img:
        tmp = pygame.Surface((w, h), pygame.SRCALPHA)
        tmp.blit(card_img, (0, 0))
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=7)
        tmp.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(tmp, (x, y))
    if hl:
        pygame.draw.rect(surf, HILITE, rect, 3, border_radius=7)
    elif green:
        pygame.draw.rect(surf, AFFORD_G, rect, 2, border_radius=7)
    else:
        pygame.draw.rect(surf, border, rect, 2, border_radius=7)

    # Top colour strip with bonus gem
    rnd(surf, border, (x, y, w, 22), r=7)
    gem_col = GEM.get(card.color_bonus, border)
    pygame.draw.circle(surf, GEM_DARK.get(card.color_bonus, border), (x + w - 13, y + 11), 9)
    pygame.draw.circle(surf, gem_col, (x + w - 13, y + 11), 7)
    hl2 = tuple(min(255, v + 60) for v in gem_col)
    pygame.draw.circle(surf, hl2, (x + w - 16, y + 8), 3)

    # Points: white text with black outline — visible on any card colour
    if card.points > 0:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            sh = fonts["bold"].render(str(card.points), True, (0, 0, 0))
            surf.blit(sh, (x + 5 + dx, y + 3 + dy))
        pt = fonts["bold"].render(str(card.points), True, (255, 255, 255))
        surf.blit(pt, (x + 5, y + 3))

    # Cost (stacked dots with numbers) — starts below strip
    cy2 = y + 28
    for color in COLOR_ORDER:
        amt = card.cost.get(color, 0)
        if not amt:
            continue
        pygame.draw.circle(surf, GEM[color],      (x + 11, cy2 + 6), 8)
        pygame.draw.circle(surf, GEM_DARK[color], (x + 11, cy2 + 6), 8, 1)
        n = fonts["small"].render(str(amt), True, TEXT_C)
        surf.blit(n, (x + 23, cy2))
        cy2 += 19


def draw_hidden(surf, deck, rect, fonts, hovering=False):
    x, y, w, h = rect
    empty = deck.hidden_count() == 0 and not deck.get_face_up_cards()
    palette = {1: (100, 150, 84), 2: (162, 106, 54), 3: (135, 76, 76)}
    col = palette.get(deck.level, (90, 90, 105)) if not empty else (46, 48, 58)

    rnd(surf, col, rect, r=7)
    bord = HILITE if hovering and not empty else tuple(max(0, v - 30) for v in col)
    pygame.draw.rect(surf, bord, rect, 2, border_radius=7)

    lv  = fonts["bold"].render(f"L{deck.level}", True, TEXT_C if not empty else DIM_C)
    cnt = fonts["small"].render(str(deck.hidden_count()), True, TEXT_C if not empty else DIM_C)
    surf.blit(lv,  lv.get_rect(center=(x + w // 2, y + h // 2 - 10)))
    surf.blit(cnt, cnt.get_rect(center=(x + w // 2, y + h // 2 + 9)))


def draw_noble(surf, noble, rect, fonts, hl=False, noble_img=None):
    x, y, _, _ = rect
    rnd(surf, (155, 140, 106), rect, r=7)
    if noble_img:
        nw, nh = rect[2], rect[3]
        tmp = pygame.Surface((nw, nh), pygame.SRCALPHA)
        tmp.blit(noble_img, (0, 0))
        mask = pygame.Surface((nw, nh), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, nw, nh), border_radius=7)
        tmp.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(tmp, (x, y))
    pygame.draw.rect(surf, HILITE if hl else (116, 104, 76), rect, 2 if not hl else 3, border_radius=7)
    for dx, dy in ((-1,0),(1,0),(0,-1),(0,1)):
        sh = fonts["bold"].render(str(noble.points), True, (0, 0, 0))
        surf.blit(sh, (x + 5 + dx, y + 5 + dy))
    pt = fonts["bold"].render(str(noble.points), True, (255, 255, 255))
    surf.blit(pt, (x + 5, y + 5))
    cy2 = y + 26
    for color, amt in noble.requirement.items():
        pygame.draw.circle(surf, GEM[color],      (x + 13, cy2 + 6), 8)
        pygame.draw.circle(surf, GEM_DARK[color], (x + 13, cy2 + 6), 8, 1)
        n = fonts["small"].render(str(amt), True, (24, 24, 24))
        surf.blit(n, (x + 25, cy2))
        cy2 += 20


def shadowed_text(surf, text, pos, font, color=TEXT_C, shadow=(0, 0, 0)):
    """Render text with a 1-px drop shadow for legibility on any background."""
    sh = font.render(text, True, shadow)
    surf.blit(sh, (pos[0] + 1, pos[1] + 1))
    t = font.render(text, True, color)
    surf.blit(t, pos)


def draw_button(surf, text, rect, fonts, state="normal"):
    c = {"normal": BTN_N, "hover": BTN_H_C, "active": BTN_A, "disabled": BTN_DIS}[state]
    rnd(surf, c, rect, r=7)
    tc = DIM_C if state == "disabled" else TEXT_C
    t  = fonts["normal"].render(text, True, tc)
    surf.blit(t, t.get_rect(center=(rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)))


# ── UI Mode ───────────────────────────────────────────────────────────────────

class UM:
    START       = "START"
    IDLE        = "IDLE"
    TAKE_TOKENS = "TAKE_TOKENS"
    BUY_CARD    = "BUY_CARD"
    RESERVE     = "RESERVE"
    BUY_RES     = "BUY_RES"
    PEND_RETURN = "PEND_RETURN"
    PEND_NOBLE  = "PEND_NOBLE"
    BOT_TURN    = "BOT_TURN"
    GAME_OVER   = "GAME_OVER"


# ── App ───────────────────────────────────────────────────────────────────────

class SplendorApp:

    def __init__(self):
        pygame.init()
        self.fullscreen = False
        self.screen = pygame.display.set_mode((SW, SH), pygame.RESIZABLE | pygame.SCALED)
        pygame.display.set_caption("Splendor — Human vs Bot  [F11 = fullscreen]")
        self.clock  = pygame.time.Clock()

        self.assets = _load_assets()

        self.fonts = {
            "title":  pygame.font.SysFont("segoeui", 38, bold=True),
            "large":  pygame.font.SysFont("segoeui", 24, bold=True),
            "bold":   pygame.font.SysFont("segoeui", 15, bold=True),
            "normal": pygame.font.SysFont("segoeui", 14),
            "small":  pygame.font.SysFont("segoeui", 12),
            "toast":  pygame.font.SysFont("segoeui", 20, bold=True),
        }

        self.mode = UM.START
        self.game = None
        self._reset_state()

    def _reset_state(self):
        self.sel_toks   = []
        self.status     = ""
        self.bot_timer  = 0
        self.bot_fails  = 0
        self.fly_toks   = []
        self.fly_cards  = []
        self.toasts     = []   # list of Toast objects

    def _new_game(self):
        self.game = create_game("You", "Bot")
        self._reset_state()
        self.mode   = UM.IDLE
        self.status = "Your turn — choose an action."

    # ── Toast helper ──────────────────────────────────────────────────────────

    def _toast(self, text, color=None, dur=1800):
        if color is None:
            color = TEXT_C
        self.toasts.append(Toast(text, color, dur))

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
                    self._cancel()
                elif ev.key == pygame.K_F11:
                    self.fullscreen = not self.fullscreen
                    flags = (pygame.FULLSCREEN | pygame.SCALED) if self.fullscreen \
                            else (pygame.RESIZABLE | pygame.SCALED)
                    self.screen = pygame.display.set_mode((SW, SH), flags)
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self._click(*ev.pos)

    def _cancel(self):
        if self.mode not in (UM.IDLE, UM.START, UM.BOT_TURN,
                              UM.PEND_RETURN, UM.PEND_NOBLE, UM.GAME_OVER):
            self.mode     = UM.IDLE
            self.sel_toks = []
            self.status   = "Cancelled — choose an action."

    # ── Click dispatcher ──────────────────────────────────────────────────────

    def _click(self, mx, my):
        m  = self.mode
        gp = self.game.get_pending_state() if self.game else IDLE

        if m == UM.START:
            self._click_start(mx, my); return
        if m == UM.GAME_OVER:
            self.mode = UM.START; return
        if gp == PENDING_CHOOSE_NOBLE:
            self._click_noble(mx, my); return
        if gp == PENDING_RETURN_TOKENS:
            self._click_return(mx, my); return
        if m == UM.BOT_TURN:
            return

        # Action buttons — always respond (switch away from current mode)
        btn = self._hit_btn(mx, my)
        if btn:
            self._on_btn(btn); return

        if m == UM.TAKE_TOKENS: self._click_tok(mx, my)
        elif m == UM.BUY_CARD:  self._click_buy(mx, my)
        elif m == UM.RESERVE:   self._click_reserve(mx, my)
        elif m == UM.BUY_RES:   self._click_buy_res(mx, my)

    # ── Start screen ──────────────────────────────────────────────────────────

    def _click_start(self, mx, my):
        r = self._start_btn_rect()
        if in_rect(mx, my, r):
            self._new_game()

    def _start_btn_rect(self):
        bw, bh = 260, 54
        return (SW // 2 - bw // 2, SH // 2 + 30, bw, bh)

    # ── Buttons ───────────────────────────────────────────────────────────────

    def _hit_btn(self, mx, my):
        labels = ["take", "buy", "reserve", "buy_res"]
        for i, name in enumerate(labels):
            if in_rect(mx, my, btn_rect(i)):
                return name
        if self.mode == UM.TAKE_TOKENS:
            if in_rect(mx, my, btn_rect(4)):
                return "confirm"
        return None

    def _on_btn(self, btn):
        # Cancel current mode first (allow mode switching without pressing Esc)
        if self.mode not in (UM.IDLE, UM.BOT_TURN, UM.GAME_OVER,
                              UM.PEND_RETURN, UM.PEND_NOBLE):
            self.mode     = UM.IDLE
            self.sel_toks = []

        if btn == "take":
            self.mode   = UM.TAKE_TOKENS
            self.sel_toks = []
            self.status = "Click gem tokens to select (up to 3 different, or same gem twice for 2)."
        elif btn == "buy":
            self.mode   = UM.BUY_CARD
            self.status = "Click a card on the board to buy it."
        elif btn == "reserve":
            self.mode   = UM.RESERVE
            self.status = "Click a face-up card or the hidden deck button to reserve."
        elif btn == "buy_res":
            if self.game.players[0].reserved_cards:
                self.mode   = UM.BUY_RES
                self.status = "Click one of your reserved cards (right panel) to buy."
            else:
                self._toast("No reserved cards.", TOAST_WN)
                self.status = "No reserved cards."
        elif btn == "confirm":
            self._do_take()

    # ── Take tokens ───────────────────────────────────────────────────────────

    def _click_tok(self, mx, my):
        all_c = COLOR_ORDER + ["gold"]
        for i, color in enumerate(all_c):
            if color == "gold":
                continue
            cx, cy = tok_center(i)
            if in_circ(mx, my, cx, cy, TOKEN_R + 6):
                self._pick(color)
                return

    def _pick(self, color):
        sel  = self.sel_toks
        bank = self.game.board.token_bank

        # 2-same: clicking the same color a second time → try to take 2
        if sel == [color]:
            if bank.can_take_two_same(color):
                sel.append(color)
                self._do_take()
            else:
                self._toast(f"Need ≥ 4 {color} in bank for 2-same.", TOAST_WN)
            return

        # Already committed to a 2-same pair (shouldn't normally be reached)
        if len(sel) == 2 and sel[0] == sel[1]:
            return

        # Deselect a previously chosen distinct color
        if color in sel:
            sel.remove(color)
            self.status = f"Deselected {color}."
            return

        if bank.tokens.get(color, 0) < 1:
            self._toast(f"No {color} tokens left.", TOAST_WN)
            return
        if len(sel) >= 3:
            return

        sel.append(color)
        if len(sel) == 3:
            self._do_take()   # auto-confirm at 3 distinct
        else:
            self.status = f"Selected: {sel}  –  click same color again for 2-same, or pick more."

    def _do_take(self):
        if not self.sel_toks:
            self._toast("Select at least 1 token.", TOAST_WN); return
        ok = self.game.take_tokens(self.sel_toks)
        if ok:
            self._toast("Took: " + ", ".join(self.sel_toks), TOAST_OK)
            self._spawn_fly_toks(self.sel_toks)
            self.sel_toks = []
            self._after_human()
        else:
            self._toast("Invalid selection — try again.", TOAST_ER)
            self.sel_toks = []

    def _spawn_fly_toks(self, colors):
        all_c = COLOR_ORDER + ["gold"]
        for color in colors:
            if color in all_c:
                i  = all_c.index(color)
                cx, cy = tok_center(i)
                dst = (PANEL_X + 18 + len(self.fly_toks) * 28, HUMAN_Y + 72)
                self.fly_toks.append(FlyToken(color, (cx, cy), dst))

    # ── Buy face-up card ──────────────────────────────────────────────────────

    def _click_buy(self, mx, my):
        for level in [1, 2, 3]:
            deck = self.game._get_deck(level)
            if not deck: continue
            for i, card in enumerate(deck.get_face_up_cards()):
                r = card_slot_rect(level, i + 1)
                if in_rect(mx, my, r):
                    ok = self.game.buy_card(level, i)
                    if ok:
                        msg = f"Bought L{level} {card.color_bonus}"
                        if card.points: msg += f" +{card.points}pt"
                        self._toast(msg, TOAST_OK)
                        self.fly_cards.append(FlyCard(r, card.color_bonus))
                        self._after_human()
                    else:
                        self._toast("Can't afford.", TOAST_ER, dur=700)
                    return

    # ── Reserve card ─────────────────────────────────────────────────────────

    def _click_reserve(self, mx, my):
        g = self.game
        if not g.players[0].can_reserve():
            self._toast("Already have 3 reserved cards.", TOAST_WN)
            self.mode = UM.IDLE; return

        for level in [1, 2, 3]:
            deck = g._get_deck(level)
            if not deck: continue
            for i, card in enumerate(deck.get_face_up_cards()):
                r = card_slot_rect(level, i + 1)
                if in_rect(mx, my, r):
                    ok = g.reserve_card(level, i)
                    if ok:
                        self._toast(f"Reserved L{level} {card.color_bonus} card.", TOAST_OK)
                        self.fly_cards.append(FlyCard(r, card.color_bonus))
                        self._after_human()
                    return

        for level in [1, 2, 3]:
            r = card_slot_rect(level, 0)
            if in_rect(mx, my, r):
                ok = g.reserve_hidden_card(level)
                if ok:
                    self._toast(f"Reserved hidden L{level} card.", TOAST_OK)
                    self._after_human()
                else:
                    self._toast("Deck is empty.", TOAST_WN)
                    self.mode = UM.IDLE
                return

    # ── Buy reserved ──────────────────────────────────────────────────────────

    def _click_buy_res(self, mx, my):
        player = self.game.players[0]
        for i in range(len(player.reserved_cards)):
            r = self._res_rect(i)
            if in_rect(mx, my, r):
                ok = self.game.buy_reserved_card(i)
                if ok:
                    card = player.cards_owned[-1]
                    self._toast(f"Bought reserved card"
                                + (f" +{card.points}pt!" if card.points else "!"), TOAST_OK)
                    self._after_human()
                else:
                    self._toast("Can't afford.", TOAST_ER, dur=700)
                return

    def _res_rect(self, slot):
        res_y = HUMAN_Y + 108
        return (PANEL_X + 6 + slot * 85, res_y, 80, 108)

    # ── Pending – return token ────────────────────────────────────────────────

    def _click_return(self, mx, my):
        player = self.game.current_player
        all_c  = COLOR_ORDER + ["gold"]
        for i, color in enumerate(all_c):
            cx, cy = PANEL_X + 14 + i * 56 + 14, HUMAN_Y + 68
            if in_circ(mx, my, cx, cy, 18) and player.tokens.get(color, 0) > 0:
                ok = self.game.resolve_return_token(color)
                if ok:
                    self._toast(f"Returned {color} token.", TOAST_WN)
                    if self.game.get_pending_state() == PENDING_RETURN_TOKENS:
                        self.status = "Still over 10 — return another token."
                    else:
                        self._after_human()
                return

    # ── Pending – choose noble ────────────────────────────────────────────────

    def _click_noble(self, mx, my):
        pending = self.game.get_pending_nobles()
        board   = self.game.board.nobles
        for i, noble in enumerate(pending):
            try:
                bi = board.index(noble)
            except ValueError:
                bi = i
            if in_rect(mx, my, noble_rect(bi)):
                ok = self.game.resolve_choose_noble(i)
                if ok:
                    self._toast(f"Noble visit! +{noble.points}pt", TOAST_OK)
                    self._after_human()
                return

    # ── Post-action routing ───────────────────────────────────────────────────

    def _after_human(self):
        self.mode = UM.IDLE
        g = self.game
        if g.game_over:
            self.mode = UM.GAME_OVER; return

        gp = g.get_pending_state()
        if gp == PENDING_RETURN_TOKENS:
            self.mode   = UM.PEND_RETURN
            self.status = "You have > 10 tokens — click a token in YOUR panel to return one."
            return
        if gp == PENDING_CHOOSE_NOBLE:
            self.mode   = UM.PEND_NOBLE
            self.status = "Multiple nobles qualify — click one to accept."
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
        if g.get_pending_state() != IDLE:
            # shouldn't happen (bot resolves own pending states)
            self.mode = UM.BOT_TURN; self.bot_timer = 300; return
        if g.current_player.name == "You":
            self.mode   = UM.IDLE
            self.status = "Your turn — choose an action."
            self.bot_fails = 0
        else:
            self.mode      = UM.BOT_TURN
            self.bot_timer = BOT_DELAY

    # ── Update ────────────────────────────────────────────────────────────────

    def _update(self, dt):
        if self.mode == UM.BOT_TURN and self.game and not self.game.game_over:
            self.bot_timer -= dt
            if self.bot_timer <= 0:
                try:
                    ok = bot_make_move(self.game)
                    if ok:
                        self.bot_fails = 0
                    else:
                        self.bot_fails += 1
                except Exception:
                    traceback.print_exc()
                    self.bot_fails += 1

                if self.bot_fails >= 3:
                    # Force skip bot turn
                    self.game.current_player_index = (
                        (self.game.current_player_index + 1) % len(self.game.players))
                    self.bot_fails = 0
                    self._toast("Bot skipped (no valid move).", TOAST_WN)

                self._after_bot()

        for ft in self.fly_toks:  ft.update(dt)
        for fc in self.fly_cards: fc.update(dt)
        for to in self.toasts:    to.update(dt)
        self.fly_toks  = [f for f in self.fly_toks  if not f.done]
        self.fly_cards = [f for f in self.fly_cards if not f.done]
        self.toasts    = [t for t in self.toasts    if not t.done]

    # ── Draw ──────────────────────────────────────────────────────────────────

    def _draw(self):
        if self.assets.get("bg"):
            self.screen.blit(self.assets["bg"], (0, 0))
        else:
            self.screen.fill(BG)
        if self.mode == UM.START:
            self._draw_start(); return

        self._draw_title()
        self._draw_nobles()
        self._draw_board()
        self._draw_col_b()
        self._draw_panels()
        self._draw_status()
        self._draw_anims()
        self._draw_toasts()
        if self.mode == UM.GAME_OVER:
            self._draw_gameover()

    # ── Start screen ─────────────────────────────────────────────────────────

    def _draw_start(self):
        s = self.screen
        if self.assets.get("start_bg"):
            s.blit(self.assets["start_bg"], (0, 0))
        else:
            s.fill((16, 12, 8))

        title = self.fonts["title"].render("SPLENDOR", True, HILITE)
        s.blit(title, title.get_rect(center=(SW // 2, SH // 2 - 100)))

        sub = self.fonts["large"].render("Human  vs  Bot", True, TEXT_C)
        s.blit(sub, sub.get_rect(center=(SW // 2, SH // 2 - 44)))

        desc = self.fonts["normal"].render(
            "Collect gem tokens · Buy development cards · Attract nobles · Reach 15 prestige points",
            True, DIM_C)
        s.blit(desc, desc.get_rect(center=(SW // 2, SH // 2 - 4)))

        mx, my = pygame.mouse.get_pos()
        r      = self._start_btn_rect()
        state  = "hover" if in_rect(mx, my, r) else "normal"
        draw_button(s, "▶   Start Game", r, self.fonts,
                    "hover" if state == "hover" else "active")

        hint = self.fonts["small"].render("2-player rules · 4 gems per colour · 3 nobles · 15 pts to win",
                                          True, DIM_C)
        s.blit(hint, hint.get_rect(center=(SW // 2, SH // 2 + 108)))

    # ── Title ────────────────────────────────────────────────────────────────

    def _draw_title(self):
        s = self.screen
        g = self.game
        txt = f"Round {g.round_number}  ·  {g.current_player.name}'s turn"
        info = self.fonts["normal"].render(txt, True, TEXT_C)
        pos = info.get_rect(midright=(MID_X - 8, 16))
        shadowed_text(s, txt, (pos.x, pos.y), self.fonts["normal"], TEXT_C)

    # ── Nobles ───────────────────────────────────────────────────────────────

    def _draw_nobles(self):
        s  = self.screen
        g  = self.game
        pending = (g.get_pending_nobles()
                   if g.get_pending_state() == PENDING_CHOOSE_NOBLE else [])
        shadowed_text(s, "Nobles", (NOBLE_X, NOBLE_Y - 20), self.fonts["bold"], TEXT_C)
        for i, noble in enumerate(g.board.nobles):
            idx = getattr(noble, "_asset_index", i)
            noble_img = self.assets.get(f"noble_{idx}")
            draw_noble(s, noble, noble_rect(i), self.fonts,
                       hl=noble in pending, noble_img=noble_img)

    # ── Board (card rows) ────────────────────────────────────────────────────

    def _draw_board(self):
        s    = self.screen
        g    = self.game
        m    = self.mode
        mx, my = pygame.mouse.get_pos()
        human  = g.players[0]

        for level in [3, 2, 1]:
            deck = g._get_deck(level)
            if not deck: continue
            r0  = card_slot_rect(level, 0)
            hov = in_rect(mx, my, r0) and m == UM.RESERVE
            draw_hidden(s, deck, r0, self.fonts, hovering=hov)

            for i, card in enumerate(deck.get_face_up_cards()):
                r     = card_slot_rect(level, i + 1)
                hov   = in_rect(mx, my, r)
                hl    = hov and m in (UM.BUY_CARD, UM.RESERVE)
                green = human.can_afford(card) and m == UM.BUY_CARD and not hl
                draw_card(s, card, r, self.fonts, hl=hl, green=green,
                          assets=self.assets)

    # ── Middle column B: tokens + buttons ────────────────────────────────────

    def _draw_col_b(self):
        s    = self.screen
        g    = self.game
        bank = g.board.token_bank
        m    = self.mode
        mx, my = pygame.mouse.get_pos()
        all_c  = COLOR_ORDER + ["gold"]

        # Separator line
        pygame.draw.line(s, DIVIDER, (MID_X - 2, 0), (MID_X - 2, SH - STATUS_Y), 1)
        pygame.draw.line(s, DIVIDER, (MID_X + MID_W + 2, 0),
                         (MID_X + MID_W + 2, SH - STATUS_Y), 1)

        lbl_surf = self.fonts["bold"].render("Token Bank", True, TEXT_C)
        lbl_pos  = lbl_surf.get_rect(center=(MID_CX, TOK_Y0 - TOKEN_R - 14))
        shadowed_text(s, "Token Bank", (lbl_pos.x, lbl_pos.y), self.fonts["bold"], TEXT_C)

        for i, color in enumerate(all_c):
            cx, cy = tok_center(i)
            amt    = bank.tokens.get(color, 0)
            sel    = color in self.sel_toks

            if amt == 0 and not sel:
                pygame.draw.circle(s, (46, 48, 58), (cx, cy), TOKEN_R)
            else:
                hov  = in_circ(mx, my, cx, cy, TOKEN_R + 4)
                pick = m == UM.TAKE_TOKENS and color != "gold"
                if sel:
                    pygame.draw.circle(s, HILITE, (cx, cy), TOKEN_R + 5)
                elif pick and hov:
                    pygame.draw.circle(s, AFFORD_G, (cx, cy), TOKEN_R + 4)
                tok_img = self.assets.get(f"token_{color}")
                gem_circle(s, color, cx, cy, TOKEN_R,
                           label=str(amt), font=self.fonts["bold"],
                           img=tok_img)
                if color == "gold" and not tok_img:
                    draw_star(s, cx, cy - TOKEN_R + 9, 5, 2, (50, 34, 0))

            side     = "WILD" if color == "gold" else color[:3].upper()
            side_col = HILITE if color == "gold" else TEXT_C
            name_s   = self.fonts["small"].render(side, True, side_col)
            name_pos = name_s.get_rect(center=(cx + TOKEN_R + 18, cy))
            shadowed_text(s, side, (name_pos.x, name_pos.y), self.fonts["small"], side_col)

        # Buttons
        labels   = ["Take Tokens", "Buy Card", "Reserve Card", "Buy Reserved"]
        modes    = [UM.TAKE_TOKENS, UM.BUY_CARD, UM.RESERVE, UM.BUY_RES]
        human_ok = m in (UM.IDLE, UM.TAKE_TOKENS, UM.BUY_CARD, UM.RESERVE, UM.BUY_RES)

        for i, (lbl, tgt) in enumerate(zip(labels, modes)):
            r   = btn_rect(i)
            if not human_ok:
                draw_button(s, lbl, r, self.fonts, "disabled")
                continue
            is_a = m == tgt
            is_h = in_rect(mx, my, r)
            draw_button(s, lbl, r, self.fonts,
                        "active" if is_a else ("hover" if is_h else "normal"))

        # Confirm button (take tokens only)
        if m == UM.TAKE_TOKENS:
            r   = btn_rect(4)
            has = bool(self.sel_toks)
            st  = ("active" if has and in_rect(mx, my, r)
                   else "hover" if in_rect(mx, my, r)
                   else "normal" if has else "disabled")
            draw_button(s, "✔  Confirm Take", r, self.fonts, st)

        # ESC hint
        if m not in (UM.IDLE, UM.BOT_TURN, UM.PEND_RETURN,
                      UM.PEND_NOBLE, UM.GAME_OVER, UM.START):
            hint = self.fonts["small"].render("Esc = cancel", True, DIM_C)
            s.blit(hint, hint.get_rect(center=(MID_CX, BTN_Y0 + 5 * BTN_DY + 10)))

    # ── Player panels ────────────────────────────────────────────────────────

    def _draw_panels(self):
        g     = self.game
        yt    = g.current_player.name == "You"
        pygame.draw.line(self.screen, DIVIDER,
                         (PANEL_X - 2, 0), (PANEL_X - 2, SH - STATUS_Y), 1)
        self._draw_one_panel(g.players[0], HUMAN_Y, yt,   is_human=True)
        self._draw_one_panel(g.players[1], BOT_Y,   not yt, is_human=False)

    def _draw_one_panel(self, player, py, active, is_human):
        s  = self.screen
        px, pw, ph = PANEL_X, PANEL_W, PANEL_H
        bg = (44, 56, 80) if active else PANEL_BG

        rnd(s, bg, (px, py, pw, ph), r=8)
        rnd(s, bg, (px, py, pw, ph), r=8,
            border=2, bcol=HILITE if active else DIVIDER)

        who  = "YOU" if is_human else "BOT"
        name = self.fonts["bold"].render(f"{who} — {player.name}", True,
                                         HILITE if active else TEXT_C)
        s.blit(name, (px + 10, py + 8))
        pts = self.fonts["large"].render(str(player.get_points()), True,
                                          HILITE if active else TEXT_C)
        s.blit(pts, pts.get_rect(topright=(px + pw - 8, py + 5)))

        # ── Row 1: Tokens (6 circles, 40px spacing) ──────────────────────────
        all_c  = COLOR_ORDER + ["gold"]
        pend_r = (self.mode == UM.PEND_RETURN and is_human)
        mx2, my2 = pygame.mouse.get_pos()
        tok_y  = py + 44   # pushed down so circles don't overlap the name text
        for i, color in enumerate(all_c):
            amt   = player.tokens.get(color, 0)
            cx    = px + 14 + i * 40
            hover = pend_r and in_circ(mx2, my2, cx, tok_y, 14) and amt > 0
            if hover:
                pygame.draw.circle(s, HILITE, (cx, tok_y), 16)
            if amt > 0:
                pygame.draw.circle(s, GEM[color],      (cx, tok_y), 13)
                pygame.draw.circle(s, GEM_DARK[color], (cx, tok_y), 13, 1)
                n = self.fonts["small"].render(str(amt), True, GEM_TEXT[color])
                s.blit(n, n.get_rect(center=(cx, tok_y)))
                if color == "gold":
                    draw_star(s, cx, tok_y - 6, 4, 2, (50, 34, 0))
            else:
                empty_col = (70, 58, 12) if color == "gold" else (48, 50, 62)
                pygame.draw.circle(s, empty_col, (cx, tok_y), 13)
                if color == "gold":
                    draw_star(s, cx, tok_y, 4, 2, (110, 90, 30))

        # ── Row 2: Bonus (cards owned per colour) ────────────────────────────
        bonus = player.get_bonus_count()
        bon_y = py + 70
        bl = self.fonts["small"].render("Bonus:", True, DIM_C)
        s.blit(bl, (px + 8, bon_y))
        bx = px + 52
        for color in COLOR_ORDER:
            amt = bonus[color]
            col = GEM[color] if amt > 0 else tuple(max(0, v - 60) for v in GEM[color])
            pygame.draw.circle(s, col,              (bx + 6, bon_y + 6), 6)
            pygame.draw.circle(s, GEM_DARK[color],  (bx + 6, bon_y + 6), 6, 1)
            n = self.fonts["small"].render(str(amt), True,
                                           TEXT_C if amt > 0 else DIM_C)
            s.blit(n, (bx + 14, bon_y))
            bx += 38

        # ── Divider ──────────────────────────────────────────────────────────
        pygame.draw.line(s, DIVIDER, (px + 6, py + 88), (px + pw - 6, py + 88), 1)

        # ── Row 3: Reserved cards ─────────────────────────────────────────────
        res_label_y = py + 93
        res_y       = py + 108
        rl = self.fonts["small"].render("Reserved:", True, DIM_C)
        s.blit(rl, (px + 8, res_label_y))

        RCARD_W, RCARD_H = 80, 108
        for i, card in enumerate(player.reserved_cards):
            rx  = px + 6 + i * (RCARD_W + 5)
            r   = (rx, res_y, RCARD_W, RCARD_H)
            if is_human:
                # keep _res_rect aligned for click detection
                pass
            hl  = (self.mode == UM.BUY_RES and is_human and in_rect(mx2, my2, r))
            can = player.can_afford(card)
            rnd(s, card_bg(card.level, card.color_bonus), r, r=5)
            border_col = GEM.get(card.color_bonus, border_col := (100,100,100))
            bc = HILITE if hl else (AFFORD_G if can and is_human else border_col)
            pygame.draw.rect(s, bc, r, 2, border_radius=5)
            # Bonus gem in top strip
            strip_col = GEM.get(card.color_bonus, (110, 110, 110))
            rnd(s, strip_col, (rx, res_y, RCARD_W, 18), r=5)
            pygame.draw.circle(s, GEM_DARK.get(card.color_bonus, strip_col),
                               (rx + RCARD_W - 10, res_y + 9), 7)
            pygame.draw.circle(s, strip_col, (rx + RCARD_W - 10, res_y + 9), 5)
            if card.points > 0:
                p = self.fonts["bold"].render(str(card.points), True, TEXT_C)
                s.blit(p, (rx + 4, res_y + 20))
            cy2 = res_y + 34
            for color in COLOR_ORDER:
                a2 = card.cost.get(color, 0)
                if not a2: continue
                pygame.draw.circle(s, GEM[color],      (rx + 10, cy2 + 5), 6)
                pygame.draw.circle(s, GEM_DARK[color], (rx + 10, cy2 + 5), 6, 1)
                t2 = self.fonts["small"].render(str(a2), True, TEXT_C)
                s.blit(t2, (rx + 19, cy2))
                cy2 += 15

        # ── Row 4: Nobles earned ──────────────────────────────────────────────
        nob_y = res_y + RCARD_H + 6
        if player.nobles:
            nb_lbl = self.fonts["small"].render("Nobles:", True, DIM_C)
            s.blit(nb_lbl, (px + 8, nob_y))
            for i, n in enumerate(player.nobles):
                nx2 = px + 60 + i * 36
                rnd(s, (155, 140, 106), (nx2, nob_y - 2, 32, 22), r=4)
                t = self.fonts["small"].render(f"+{n.points}", True, (24, 24, 24))
                s.blit(t, t.get_rect(center=(nx2 + 16, nob_y + 9)))

    # ── Status bar ───────────────────────────────────────────────────────────

    def _draw_status(self):
        s  = self.screen
        g  = self.game
        gp = g.get_pending_state()

        pygame.draw.rect(s, (16, 12, 8), (0, STATUS_Y - 6, SW, SH - STATUS_Y + 6))
        pygame.draw.line(s, DIVIDER, (0, STATUS_Y - 6), (SW, STATUS_Y - 6), 1)
        msg = self.status
        if gp == PENDING_RETURN_TOKENS:
            msg = "Over 10 tokens — click a token in YOUR panel to return one."
        elif gp == PENDING_CHOOSE_NOBLE:
            msg = "Multiple nobles qualify — click a noble tile to accept one."

        t = self.fonts["normal"].render(msg, True, TEXT_C)
        s.blit(t, (12, STATUS_Y + 10))

    # ── Animations ───────────────────────────────────────────────────────────

    def _draw_anims(self):
        s = self.screen
        for ft in self.fly_toks:
            cx, cy = ft.pos
            gem_circle(s, ft.color, cx, cy, TOKEN_R - 3)
        for fc in self.fly_cards:
            fc.draw(s)

    def _draw_toasts(self):
        cx, cy = board_centre()
        for i, t in enumerate(self.toasts):
            t.draw(self.screen, cx, cy - i * 38, self.fonts["toast"])

    # ── Game over overlay ────────────────────────────────────────────────────

    def _draw_gameover(self):
        s  = self.screen
        g  = self.game
        ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 172)); s.blit(ov, (0, 0))

        winner  = g.winner
        you_win = winner and winner.name == "You"
        col     = TOAST_OK if you_win else TOAST_ER
        title   = self.fonts["title"].render(
            "YOU WIN! 🎉" if you_win else "BOT WINS!", True, col)
        s.blit(title, title.get_rect(center=(SW // 2, SH // 2 - 72)))

        for i, p in enumerate(g.players):
            line = self.fonts["large"].render(f"{p.name}:  {p.get_points()} pts", True, TEXT_C)
            s.blit(line, line.get_rect(center=(SW // 2, SH // 2 - 16 + i * 38)))

        hint = self.fonts["normal"].render("Click to return to start screen", True, DIM_C)
        s.blit(hint, hint.get_rect(center=(SW // 2, SH // 2 + 96)))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    SplendorApp().run()
