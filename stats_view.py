"""
stats_view.py — Modern statistics dashboard for Splendor.
"""

import pygame
import math

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = (10,  8,  6)
CARD    = (20, 16, 12)
CARD2   = (28, 22, 16)
BORDER  = (48, 38, 24)
TEXT    = (232, 224, 210)
DIM     = (115, 104, 84)
GOLD    = (245, 197,  62)
GOLD2   = (180, 140,  30)
TEAL    = ( 42, 191, 175)
BLUE    = ( 70, 150, 230)
ROSE    = (220,  80,  80)
GREEN_A = ( 72, 200, 110)

GEM = {
    "white": (215, 210, 195),
    "blue":  ( 58, 130, 200),
    "green": ( 42, 168,  70),
    "red":   (210,  52,  52),
    "black": ( 80,  80,  80),
}
GEM_BRIGHT = {
    "white": (255, 252, 240),
    "blue":  (100, 170, 255),
    "green": ( 80, 220, 110),
    "red":   (255, 100, 100),
    "black": (130, 130, 130),
}
TIER_COL  = {1: (72, 165, 72),  2: (185, 122, 46), 3: (168, 58,  58)}
TIER_GLOW = {1: (120, 220, 100), 2: (230, 165, 80), 3: (220, 90, 90)}
P1_COL    = ( 70, 148, 228)
P2_COL    = (228, 118,  50)


# ── Draw helpers ──────────────────────────────────────────────────────────────

def _rnd(surf, col, rect, r=8, bw=0, bc=None):
    pygame.draw.rect(surf, col, rect, border_radius=r)
    if bw:
        pygame.draw.rect(surf, bc or col, rect, bw, border_radius=r)


def _gradient_bar(surf, rect, top_c, bot_c, r=5):
    """Draw a vertically-gradated bar clipped to rounded rect."""
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return
    tmp = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h):
        t = i / max(h - 1, 1)
        c = tuple(int(top_c[j] * (1 - t) + bot_c[j] * t) for j in range(3))
        pygame.draw.line(tmp, c, (0, i), (w, i))
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=r)
    tmp.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(tmp, (x, y))


def _glow_circle(surf, cx, cy, r, col, strength=60):
    for i in range(3, 0, -1):
        alpha = strength // i
        s = pygame.Surface((r * 2 * i, r * 2 * i), pygame.SRCALPHA)
        pygame.draw.circle(s, (*col, alpha), (r * i, r * i), r * i)
        surf.blit(s, (cx - r * i, cy - r * i))


def _panel(surf, rect, title, accent, fonts):
    """Draw a card panel with colored accent bar and title."""
    _rnd(surf, CARD, rect, r=10)
    _rnd(surf, CARD, rect, r=10, bw=1, bc=BORDER)
    # Top accent stripe
    pygame.draw.rect(surf, accent, (rect[0] + 1, rect[1] + 1, rect[2] - 2, 3),
                     border_radius=10)
    sh = fonts["bold"].render(title, True, (0, 0, 0))
    surf.blit(sh, (rect[0] + 13, rect[1] + 12))
    surf.blit(fonts["bold"].render(title, True, TEXT), (rect[0] + 12, rect[1] + 11))


def _stat_pill(surf, x, y, label, value, col, fonts):
    """Small pill showing a key stat (e.g. 'Avg  42.3')."""
    lbl = fonts["small"].render(label, True, DIM)
    val = fonts["bold"].render(str(value), True, col)
    w   = max(lbl.get_width(), val.get_width()) + 18
    _rnd(surf, CARD2, (x, y, w, 36), r=6)
    _rnd(surf, CARD2, (x, y, w, 36), r=6, bw=1, bc=BORDER)
    surf.blit(lbl, lbl.get_rect(center=(x + w // 2, y + 10)))
    surf.blit(val,  val.get_rect(center=(x + w // 2, y + 26)))
    return w


def _no_data(surf, rect, fonts):
    t = fonts["normal"].render("No data — press  Run Simulations  to start", True, DIM)
    surf.blit(t, t.get_rect(center=(rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)))


def _i(row, key):
    try: return int(row.get(key, 0))
    except: return 0


def _grid_h(surf, ax, ay, aw, ah, max_v, ticks, font):
    for pct in ticks:
        ty  = ay + ah - int(ah * pct / 100)
        col = (38, 30, 20) if pct != 0 else BORDER
        pygame.draw.line(surf, col, (ax, ty), (ax + aw, ty), 1)
        v   = font.render(str(int(max_v * pct / 100)), True, DIM)
        surf.blit(v, (ax - v.get_width() - 5, ty - 6))


# ── Chart 1 — Gem Color Collection Frequency ─────────────────────────────────

def draw_gem_chart(surf, rows, rect, fonts):
    x, y, w, h = rect
    _panel(surf, rect, "Gem Color Collection", TEAL, fonts)
    if not rows:
        _no_data(surf, rect, fonts); return

    colors = ["white", "blue", "green", "red", "black"]
    p1 = {c: sum(_i(r, f"p1_gem_{c}") for r in rows) for c in colors}
    p2 = {c: sum(_i(r, f"p2_gem_{c}") for r in rows) for c in colors}
    totals = {c: p1[c] + p2[c] for c in colors}
    max_v  = max(totals.values()) or 1

    ax, ay = x + 42, y + 36
    aw, ah = w - 54, h - 86
    bw     = aw // 8
    gap    = (aw - bw * 5) // 6

    _grid_h(surf, ax, ay, aw, ah, max_v, [0, 25, 50, 75, 100], fonts["small"])

    for i, c in enumerate(colors):
        bx  = ax + i * (bw + gap) + gap
        tot = totals[c]
        bh  = int(ah * tot / max_v)
        by  = ay + ah - bh

        # Bar: p1 stacked on p2
        h2 = int(bh * p2[c] / max(tot, 1))
        h1 = bh - h2
        if h2 > 0:
            _gradient_bar(surf, (bx, ay + ah - h2, bw, h2),
                          GEM_BRIGHT[c], GEM[c], r=4 if h1 == 0 else 2)
        if h1 > 0:
            _gradient_bar(surf, (bx, by, bw, h1),
                          tuple(min(255, v + 40) for v in GEM_BRIGHT[c]),
                          GEM_BRIGHT[c], r=4)

        # Glow on top
        if tot > 0:
            _glow_circle(surf, bx + bw // 2, by, 6, GEM_BRIGHT[c], 50)
            lbl = fonts["small"].render(str(tot), True, TEXT)
            surf.blit(lbl, lbl.get_rect(center=(bx + bw // 2, by - 13)))

        # X label
        pygame.draw.circle(surf, GEM[c], (bx + bw // 2, ay + ah + 12), 5)
        nl = fonts["small"].render(c[:3].upper(), True, TEXT)
        surf.blit(nl, nl.get_rect(center=(bx + bw // 2, ay + ah + 26)))

    # Stat pills
    total_all = sum(totals.values())
    px = x + 12
    for lbl, val, col in [
        ("Total", total_all, TEAL),
        ("Matches", len(rows), GOLD),
    ]:
        pw = _stat_pill(surf, px, y + h - 44, lbl, val, col, fonts)
        px += pw + 8


# ── Chart 2 — Card Tier Purchase Frequency ───────────────────────────────────

def draw_tier_chart(surf, rows, rect, fonts):
    x, y, w, h = rect
    _panel(surf, rect, "Card Tier Purchases", GOLD, fonts)
    if not rows:
        _no_data(surf, rect, fonts); return

    totals = {t: sum(_i(r, f"p1_tier{t}") + _i(r, f"p2_tier{t}") for r in rows)
              for t in [1, 2, 3]}
    grand  = sum(totals.values()) or 1

    # Draw as horizontal bars (more modern feel)
    ax, ay = x + 16, y + 42
    aw, ah = w - 32, h - 96
    row_h  = ah // 3 - 6

    for i, tier in enumerate([1, 2, 3]):
        by  = ay + i * (row_h + 16)
        val = totals[tier]
        pct = val / grand
        bar_w = int((aw - 80) * pct)

        # Background track
        _rnd(surf, CARD2, (ax + 60, by, aw - 80, row_h), r=5)

        # Filled bar
        if bar_w > 0:
            _gradient_bar(surf, (ax + 60, by, bar_w, row_h),
                          TIER_GLOW[tier], TIER_COL[tier], r=5)

        # Glow on right edge
        if bar_w > 8:
            _glow_circle(surf, ax + 60 + bar_w, by + row_h // 2, 8,
                         TIER_GLOW[tier], 60)

        # Tier label
        tl = fonts["bold"].render(f"Tier {tier}", True, TIER_GLOW[tier])
        surf.blit(tl, (ax, by + row_h // 2 - tl.get_height() // 2))

        # Value + %
        vl = fonts["bold"].render(f"{val}", True, TEXT)
        surf.blit(vl, (ax + aw - 55, by + row_h // 2 - vl.get_height() // 2))
        pl = fonts["small"].render(f"{pct*100:.0f}%", True, DIM)
        surf.blit(pl, (ax + aw - 32, by + row_h // 2 - pl.get_height() // 2))

    # Pills
    px = x + 12
    for lbl, val, col in [
        ("Total Cards", grand, GOLD),
        ("Per Match", f"{grand/max(len(rows),1):.1f}", GREEN_A),
    ]:
        pw = _stat_pill(surf, px, y + h - 44, lbl, val, col, fonts)
        px += pw + 8


# ── Chart 3 — Final Score Margin ─────────────────────────────────────────────

def draw_boxplot(surf, rows, rect, fonts):
    x, y, w, h = rect
    _panel(surf, rect, "Final Score Margin", ROSE, fonts)
    if not rows:
        _no_data(surf, rect, fonts); return

    values = sorted(_i(r, "score_margin") for r in rows)
    n = len(values)
    if n == 0:
        _no_data(surf, rect, fonts); return

    lo  = values[0]; hi = values[-1]
    q1  = values[n // 4]; med = values[n // 2]; q3 = values[3 * n // 4]
    avg = sum(values) / n
    span = max(hi - lo, 1)

    ax, ay = x + 14, y + 48
    aw, ah = w - 28, h - 110

    def px(v):
        return ax + int(aw * (v - lo) / span)

    cy2 = ay + ah // 2
    bh2 = ah // 3

    # Shaded IQR zone background
    iqr_s = pygame.Surface((max(1, px(q3) - px(q1)), bh2 + 16), pygame.SRCALPHA)
    iqr_s.fill((60, 100, 180, 40))
    surf.blit(iqr_s, (px(q1), cy2 - bh2 // 2 - 8))

    # Grid
    for pct in [0, 25, 50, 75, 100]:
        gx = ax + int(aw * pct / 100)
        pygame.draw.line(surf, (35, 28, 18), (gx, ay), (gx, ay + ah), 1)
        lv = lo + int(span * pct / 100)
        t = fonts["small"].render(str(lv), True, DIM)
        surf.blit(t, t.get_rect(center=(gx, ay + ah + 12)))

    # Whiskers
    pygame.draw.line(surf, DIM, (px(lo), cy2), (px(q1), cy2), 2)
    pygame.draw.line(surf, DIM, (px(q3), cy2), (px(hi), cy2), 2)
    for cap_x in (px(lo), px(hi)):
        pygame.draw.line(surf, DIM, (cap_x, cy2 - bh2 // 2),
                         (cap_x, cy2 + bh2 // 2), 2)

    # Box
    box = (px(q1), cy2 - bh2 // 2, max(4, px(q3) - px(q1)), bh2)
    _gradient_bar(surf, box, (80, 120, 200), (45, 75, 145), r=5)
    _rnd(surf, (45, 75, 145), box, r=5, bw=1, bc=(100, 140, 220))

    # Median
    pygame.draw.line(surf, GOLD, (px(med), cy2 - bh2 // 2),
                     (px(med), cy2 + bh2 // 2), 3)

    # Mean dot with glow
    _glow_circle(surf, int(px(avg)), cy2, 6, ROSE, 80)
    pygame.draw.circle(surf, ROSE, (int(px(avg)), cy2), 5)
    pygame.draw.circle(surf, (255, 150, 150), (int(px(avg)), cy2), 3)

    # Stat labels above
    for v, lbl, col in [(lo, "Min", DIM), (q1, "Q1", TEXT),
                         (med, "Med", GOLD), (q3, "Q3", TEXT), (hi, "Max", DIM)]:
        t = fonts["small"].render(f"{lbl} {v}", True, col)
        surf.blit(t, t.get_rect(center=(px(v), ay + 12)))

    # Pills
    px2 = x + 12
    for lbl, val, col in [
        ("Avg", f"{avg:.1f}", BLUE),
        ("Median", med, GOLD),
        ("n", n, DIM),
    ]:
        pw = _stat_pill(surf, px2, y + h - 44, lbl, val, col, fonts)
        px2 += pw + 8


# ── Chart 4 — Gold Token Usage (Donut) ───────────────────────────────────────

def draw_pie_chart(surf, rows, rect, fonts):
    x, y, w, h = rect
    _panel(surf, rect, "Gold Token Usage", GOLD, fonts)
    if not rows:
        _no_data(surf, rect, fonts); return

    p1g = sum(_i(r, "p1_gold_spent") for r in rows)
    p2g = sum(_i(r, "p2_gold_spent") for r in rows)
    tot = p1g + p2g or 1

    cx2 = x + w // 2
    cy2 = y + h // 2 + 4
    outer = min(w, h) // 3
    inner = outer * 55 // 100   # Donut hole

    slices = [(p1g, P1_COL, (130, 190, 255), "Bot A"),
              (p2g, P2_COL, (255, 180, 120), "Bot B")]
    angle  = -math.pi / 2

    for val, col, bright, lbl in slices:
        sweep = 2 * math.pi * val / tot
        steps = max(3, int(sweep * 50))
        pts   = [(cx2, cy2)]
        for s in range(steps + 1):
            a = angle + sweep * s / steps
            pts.append((cx2 + outer * math.cos(a), cy2 + outer * math.sin(a)))
        if len(pts) >= 3:
            pygame.draw.polygon(surf, col, pts)
        # Inner bright arc (glow on edge)
        for s in range(steps):
            a1 = angle + sweep * s / steps
            a2 = angle + sweep * (s + 1) / steps
            t  = s / steps
            gc = tuple(int(col[i] * (1-t) + bright[i] * t) for i in range(3))
            pygame.draw.line(surf, gc,
                             (cx2 + int(outer*0.88*math.cos(a1)),
                              cy2 + int(outer*0.88*math.sin(a1))),
                             (cx2 + int(outer*math.cos(a1)),
                              cy2 + int(outer*math.sin(a1))), 3)
        angle += sweep

    # Donut hole
    pygame.draw.circle(surf, CARD, (cx2, cy2), inner)
    pygame.draw.circle(surf, BORDER, (cx2, cy2), inner, 1)

    # Center text
    tot_t = fonts["bold"].render(str(p1g + p2g), True, GOLD)
    sub_t = fonts["small"].render("gold used", True, DIM)
    surf.blit(tot_t, tot_t.get_rect(center=(cx2, cy2 - 6)))
    surf.blit(sub_t, sub_t.get_rect(center=(cx2, cy2 + 11)))

    # Legend
    ly = y + h - 78
    for val, col, _, lbl in slices:
        pygame.draw.rect(surf, col, (x + 12, ly, 12, 12), border_radius=3)
        t = fonts["small"].render(f"{lbl}:  {val} ({val*100//tot}%)", True, TEXT)
        surf.blit(t, (x + 28, ly))
        ly += 20


# ── Chart 5 — Total Turns per Match (Histogram) ───────────────────────────────

def draw_histogram(surf, rows, rect, fonts):
    x, y, w, h = rect
    _panel(surf, rect, "Turns per Match", BLUE, fonts)
    if not rows:
        _no_data(surf, rect, fonts); return

    values = [_i(r, "total_turns") for r in rows if _i(r, "total_turns") > 0]
    if not values:
        _no_data(surf, rect, fonts); return

    lo, hi  = min(values), max(values)
    n_bins  = 8
    bsize   = max(1, math.ceil((hi - lo + 1) / n_bins))
    bins    = [0] * n_bins
    for v in values:
        bi = min(n_bins - 1, (v - lo) // bsize)
        bins[bi] += 1
    max_cnt = max(bins) or 1
    avg     = sum(values) / len(values)

    ax, ay = x + 42, y + 36
    aw, ah = w - 54, h - 90
    bw2    = aw // n_bins - 3

    _grid_h(surf, ax, ay, aw, ah, max_cnt, [0, 50, 100], fonts["small"])

    # Average line
    avg_x = ax + int(aw * (avg - lo) / max(hi - lo, 1))
    pygame.draw.line(surf, GOLD, (avg_x, ay), (avg_x, ay + ah), 1)
    al = fonts["small"].render(f"avg {avg:.0f}", True, GOLD)
    surf.blit(al, (avg_x + 3, ay + 2))

    for i, cnt in enumerate(bins):
        bh2 = int(ah * cnt / max_cnt)
        bx  = ax + i * (aw // n_bins) + 1
        by  = ay + ah - bh2
        if cnt == 0:
            continue
        # Color intensity by count
        t   = cnt / max_cnt
        top = tuple(int(BLUE[j] * (0.5 + 0.5 * t) + 80 * (1 - t)) for j in range(3))
        bot = tuple(int(BLUE[j] * 0.5) for j in range(3))
        _gradient_bar(surf, (bx, by, bw2, bh2), top, bot, r=4)

        if cnt > 0:
            cv = fonts["small"].render(str(cnt), True, TEXT)
            surf.blit(cv, cv.get_rect(center=(bx + bw2 // 2, by - 11)))

        lv = fonts["small"].render(str(lo + i * bsize), True, DIM)
        surf.blit(lv, lv.get_rect(center=(bx + bw2 // 2, ay + ah + 13)))

    # Pills
    px2 = x + 12
    for lbl, val, col in [
        ("Avg", f"{avg:.1f}", BLUE),
        ("Min", lo, DIM),
        ("Max", hi, DIM),
    ]:
        pw = _stat_pill(surf, px2, y + h - 44, lbl, val, col, fonts)
        px2 += pw + 8


# ── Summary strip at top ──────────────────────────────────────────────────────

def _draw_summary(surf, rows, SW, fonts):
    if not rows:
        return
    n    = len(rows)
    wins = sum(1 for r in rows if r.get("winner") in ("BotA", "You", "BotA"))
    avg_t = sum(_i(r, "total_turns") for r in rows) / n
    avg_m = sum(_i(r, "score_margin") for r in rows) / n

    pills = [
        ("Matches",    n,        TEAL),
        ("Avg Turns",  f"{avg_t:.1f}", BLUE),
        ("Avg Margin", f"{avg_m:.1f}", ROSE),
    ]
    total_w = sum(90 for _ in pills) + 16 * (len(pills) - 1)
    sx = SW - total_w - 14
    sy = 6
    for lbl, val, col in pills:
        _stat_pill(surf, sx, sy, lbl, val, col, fonts)
        sx += 106


# ── Full stats screen ─────────────────────────────────────────────────────────

def draw_stats_screen(surf, rows, fonts, SW, SH,
                      sim_running=False, sim_progress=(0, 0)):
    surf.fill(BG)

    # ── Title ────────────────────────────────────────────────────────────────
    t_sh = fonts["title"].render("Statistics Dashboard", True, (0, 0, 0))
    t    = fonts["title"].render("Statistics Dashboard", True, GOLD)
    surf.blit(t_sh, t_sh.get_rect(midleft=(14, 29)))
    surf.blit(t,    t.get_rect(midleft=(13, 28)))

    _draw_summary(surf, rows, SW, fonts)

    # Separator
    pygame.draw.line(surf, BORDER, (0, 52), (SW, 52), 1)

    # ── Chart grid ───────────────────────────────────────────────────────────
    mg    = 8
    row1_y, row1_h = 58, 296
    row2_y = row1_y + row1_h + mg
    row2_h = SH - row2_y - 56

    half  = (SW - mg * 3) // 2
    third = (SW - mg * 4) // 3

    for fn, rect in [
        (draw_gem_chart,  (mg,                          row1_y, half,  row1_h)),
        (draw_tier_chart, (half + mg * 2,               row1_y, half,  row1_h)),
        (draw_boxplot,    (mg,                          row2_y, half,  row2_h)),
        (draw_pie_chart,  (half + mg * 2,               row2_y, third, row2_h)),
        (draw_histogram,  (half + mg*2 + third + mg,    row2_y, third, row2_h)),
    ]:
        fn(surf, rows, rect, fonts)

    # ── Bottom bar ───────────────────────────────────────────────────────────
    pygame.draw.line(surf, BORDER, (0, SH - 50), (SW, SH - 50), 1)

    if sim_running:
        done, total = sim_progress
        pct  = done / total if total else 0
        bar  = (SW // 2 - 240, SH - 36, 480, 14)
        _rnd(surf, (28, 22, 14), bar, r=4)
        if pct > 0:
            _gradient_bar(surf, (bar[0], bar[1], int(bar[2] * pct), bar[3]),
                          GREEN_A, (40, 130, 70), r=4)
        prog = fonts["small"].render(
            f"Simulating…  {done} / {total}  ({pct*100:.0f}%)", True, TEXT)
        surf.blit(prog, prog.get_rect(center=(SW // 2, SH - 27)))
