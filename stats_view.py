"""
stats_view.py — Statistics dashboard drawing for Splendor.
All functions draw onto a pygame Surface using only drawing primitives.
"""

import pygame
import math

# ── Palette ───────────────────────────────────────────────────────────────────
_BG       = (14, 10,  8)
_PANEL    = (26, 20, 14)
_BORDER   = (60, 48, 30)
_TEXT     = (228, 220, 204)
_DIM      = (120, 108, 88)
_GOLD     = (252, 200,   0)
_ACCENT   = (255, 230,  60)

_GEM = {
    "white": (220, 215, 200),
    "blue":  ( 62, 126, 184),
    "green": ( 48, 160,  74),
    "red":   (210,  50,  50),
    "black": ( 70,  70,  70),
}
_TIER = {1: (88, 152, 76), 2: (172, 116, 54), 3: (148, 68, 68)}
_P1   = ( 72, 148, 224)
_P2   = (224, 120,  52)
_BAR  = ( 72, 120, 210)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _rnd(surf, col, rect, r=8, bw=0, bc=None):
    pygame.draw.rect(surf, col, rect, border_radius=r)
    if bw:
        pygame.draw.rect(surf, bc or col, rect, bw, border_radius=r)


def _panel(surf, rect, title, fonts):
    _rnd(surf, _PANEL, rect, r=10)
    _rnd(surf, _PANEL, rect, r=10, bw=1, bc=_BORDER)
    sh = fonts["bold"].render(title, True, (0, 0, 0))
    surf.blit(sh, (rect[0] + 13, rect[1] + 11))
    surf.blit(fonts["bold"].render(title, True, _GOLD), (rect[0] + 12, rect[1] + 10))


def _no_data(surf, rect, fonts):
    t = fonts["normal"].render("No data — press  Run Simulations  to start", True, _DIM)
    surf.blit(t, t.get_rect(center=(rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)))


def _int(row, key):
    try:
        return int(row.get(key, 0))
    except (ValueError, TypeError):
        return 0


# ── Chart 1 — Stacked bar: Gem Color Collection Frequency ────────────────────

def draw_gem_chart(surf, rows, rect, fonts):
    x, y, w, h = rect
    _panel(surf, rect, "Gem Color Collection Frequency", fonts)
    if not rows:
        _no_data(surf, rect, fonts); return

    colors = ["white", "blue", "green", "red", "black"]
    # Per-color totals split by p1 / p2
    p1 = {c: sum(_int(r, f"p1_gem_{c}") for r in rows) for c in colors}
    p2 = {c: sum(_int(r, f"p2_gem_{c}") for r in rows) for c in colors}
    max_v = max((p1[c] + p2[c]) for c in colors) or 1

    ax, ay = x + 42, y + 34
    aw, ah = w - 54, h - 72
    bw     = aw // 7
    gap    = (aw - bw * 5) // 6

    for i, c in enumerate(colors):
        bx   = ax + i * (bw + gap) + gap
        tot  = p1[c] + p2[c]
        full = int(ah * tot / max_v)
        h1   = int(ah * p1[c] / max_v)
        h2   = full - h1

        # p1 (bottom)
        if h1 > 0:
            _rnd(surf, _P1, (bx, ay + ah - h1, bw, h1), r=3)
        # p2 (top)
        if h2 > 0:
            _rnd(surf, _GEM[c], (bx, ay + ah - full, bw, h2), r=3)

        # Value label
        if tot > 0:
            lbl = fonts["small"].render(str(tot), True, _ACCENT)
            surf.blit(lbl, lbl.get_rect(center=(bx + bw // 2, ay + ah - full - 12)))

        # X label (colored dot + name)
        pygame.draw.circle(surf, _GEM[c], (bx + bw // 2, ay + ah + 14), 5)
        nl = fonts["small"].render(c[:3].upper(), True, _TEXT)
        surf.blit(nl, nl.get_rect(center=(bx + bw // 2, ay + ah + 26)))

    # Y-axis ticks
    for pct in [0, 50, 100]:
        ty = ay + ah - int(ah * pct / 100)
        pygame.draw.line(surf, _BORDER, (ax - 4, ty), (ax + aw, ty), 1)
        v = fonts["small"].render(str(int(max_v * pct / 100)), True, _DIM)
        surf.blit(v, (x + 4, ty - 7))

    # Legend
    lx, ly = ax, ay + ah + 42
    for col, lbl in [(_P1, "Bot A / You"), (_GEM["white"], "Bot B")]:
        pygame.draw.rect(surf, col, (lx, ly, 12, 10), border_radius=2)
        surf.blit(fonts["small"].render(lbl, True, _DIM), (lx + 16, ly))
        lx += 110


# ── Chart 2 — Bar chart: Card Tier Purchase Frequency ────────────────────────

def draw_tier_chart(surf, rows, rect, fonts):
    x, y, w, h = rect
    _panel(surf, rect, "Card Tier Purchase Frequency", fonts)
    if not rows:
        _no_data(surf, rect, fonts); return

    totals = {t: sum(_int(r, f"p1_tier{t}") + _int(r, f"p2_tier{t}") for r in rows) for t in [1, 2, 3]}
    max_v  = max(totals.values()) or 1

    ax, ay = x + 42, y + 34
    aw, ah = w - 54, h - 72
    bw     = aw // 5
    gap    = (aw - bw * 3) // 4

    for i, tier in enumerate([1, 2, 3]):
        bx  = ax + i * (bw + gap) + gap
        bh2 = int(ah * totals[tier] / max_v)
        by  = ay + ah - bh2
        _rnd(surf, _TIER[tier], (bx, by, bw, bh2), r=5)
        # Highlight top edge
        pygame.draw.rect(surf, tuple(min(255, v + 40) for v in _TIER[tier]),
                         (bx, by, bw, 4), border_radius=5)
        # Value
        val = fonts["bold"].render(str(totals[tier]), True, _ACCENT)
        surf.blit(val, val.get_rect(center=(bx + bw // 2, by - 16)))
        # Label
        lbl = fonts["bold"].render(f"Tier {tier}", True, _TEXT)
        surf.blit(lbl, lbl.get_rect(center=(bx + bw // 2, ay + ah + 14)))

    for pct in [0, 50, 100]:
        ty = ay + ah - int(ah * pct / 100)
        pygame.draw.line(surf, _BORDER, (ax - 4, ty), (ax + aw, ty), 1)
        v = fonts["small"].render(str(int(max_v * pct / 100)), True, _DIM)
        surf.blit(v, (x + 4, ty - 7))


# ── Chart 3 — Boxplot: Final Score Margin ────────────────────────────────────

def draw_boxplot(surf, rows, rect, fonts):
    x, y, w, h = rect
    _panel(surf, rect, "Final Score Margin", fonts)
    if not rows:
        _no_data(surf, rect, fonts); return

    values = sorted(_int(r, "score_margin") for r in rows)
    n = len(values)
    if n == 0:
        _no_data(surf, rect, fonts); return

    lo  = values[0]
    hi  = values[-1]
    q1  = values[n // 4]
    med = values[n // 2]
    q3  = values[3 * n // 4]
    avg = sum(values) / n
    span = max(hi - lo, 1)

    ax, ay = x + 14, y + 44
    aw, ah = w - 28, h - 88

    def px(v):
        return ax + int(aw * (v - lo) / span)

    cy2 = ay + ah // 2
    bh2 = ah // 3

    # Grid lines
    for pct in [0, 25, 50, 75, 100]:
        gx = ax + int(aw * pct / 100)
        pygame.draw.line(surf, _BORDER, (gx, ay), (gx, ay + ah), 1)
        lv = lo + int(span * pct / 100)
        t = fonts["small"].render(str(lv), True, _DIM)
        surf.blit(t, t.get_rect(center=(gx, ay + ah + 14)))

    # Whiskers
    pygame.draw.line(surf, _DIM, (px(lo), cy2), (px(q1), cy2), 2)
    pygame.draw.line(surf, _DIM, (px(q3), cy2), (px(hi), cy2), 2)
    for cap_x in (px(lo), px(hi)):
        pygame.draw.line(surf, _DIM, (cap_x, cy2 - bh2 // 2), (cap_x, cy2 + bh2 // 2), 2)

    # IQR box
    box_rect = (px(q1), cy2 - bh2 // 2, max(4, px(q3) - px(q1)), bh2)
    _rnd(surf, (50, 80, 138), box_rect, r=4)
    _rnd(surf, (50, 80, 138), box_rect, r=4, bw=1, bc=(80, 120, 190))

    # Median
    pygame.draw.line(surf, _GOLD, (px(med), cy2 - bh2 // 2), (px(med), cy2 + bh2 // 2), 3)

    # Mean dot
    pygame.draw.circle(surf, (210, 80, 80), (int(px(avg)), cy2), 5)
    pygame.draw.circle(surf, (255, 120, 120), (int(px(avg)), cy2), 3)

    # Stat labels above box
    for v, lbl, col in [(lo, "Min", _DIM), (q1, "Q1", _TEXT),
                         (med, "Med", _GOLD), (q3, "Q3", _TEXT), (hi, "Max", _DIM)]:
        t = fonts["small"].render(f"{lbl}={v}", True, col)
        surf.blit(t, t.get_rect(center=(px(v), ay + 12)))

    # Summary
    info = fonts["small"].render(f"n={n}   avg={avg:.1f}   med={med}   IQR={q3-q1}", True, _DIM)
    surf.blit(info, info.get_rect(center=(ax + aw // 2, ay + ah + 28)))


# ── Chart 4 — Pie chart: Gold Token Usage ────────────────────────────────────

def draw_pie_chart(surf, rows, rect, fonts):
    x, y, w, h = rect
    _panel(surf, rect, "Gold Token Usage", fonts)
    if not rows:
        _no_data(surf, rect, fonts); return

    p1g = sum(_int(r, "p1_gold_spent") for r in rows)
    p2g = sum(_int(r, "p2_gold_spent") for r in rows)
    tot = p1g + p2g or 1

    cx2 = x + w * 2 // 5
    cy2 = y + h // 2 + 8
    rad = min(w, h) // 3 - 4

    slices = [(p1g, _P1, "Bot A / You"), (p2g, _P2, "Bot B")]
    angle  = -math.pi / 2
    for val, col, lbl in slices:
        sweep = 2 * math.pi * val / tot
        steps = max(3, int(sweep * 40))
        pts   = [(cx2, cy2)]
        for s in range(steps + 1):
            a = angle + sweep * s / steps
            pts.append((cx2 + rad * math.cos(a), cy2 + rad * math.sin(a)))
        if len(pts) >= 3:
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, _PANEL, pts, 2)
        # Mid-angle label
        mid_a = angle + sweep / 2
        if sweep > 0.3:
            lx2 = cx2 + int(rad * 0.6 * math.cos(mid_a))
            ly2 = cy2 + int(rad * 0.6 * math.sin(mid_a))
            pct = fonts["small"].render(f"{val*100//tot}%", True, (255, 255, 255))
            surf.blit(pct, pct.get_rect(center=(lx2, ly2)))
        angle += sweep

    # Legend
    lx, ly = x + w * 3 // 5 + 8, y + h // 2 - 24
    for val, col, lbl in slices:
        _rnd(surf, col, (lx, ly, 14, 14), r=3)
        t = fonts["small"].render(f"{lbl}:  {val}", True, _TEXT)
        surf.blit(t, (lx + 20, ly))
        ly += 26
    tot_t = fonts["small"].render(f"Total: {p1g + p2g}", True, _DIM)
    surf.blit(tot_t, (lx, ly + 6))


# ── Chart 5 — Histogram: Total Turns per Match ───────────────────────────────

def draw_histogram(surf, rows, rect, fonts):
    x, y, w, h = rect
    _panel(surf, rect, "Total Turns per Match", fonts)
    if not rows:
        _no_data(surf, rect, fonts); return

    values = [_int(r, "total_turns") for r in rows if _int(r, "total_turns") > 0]
    if not values:
        _no_data(surf, rect, fonts); return

    lo, hi = min(values), max(values)
    n_bins  = 10
    bsize   = max(1, math.ceil((hi - lo + 1) / n_bins))
    bins    = [0] * n_bins
    for v in values:
        bi = min(n_bins - 1, (v - lo) // bsize)
        bins[bi] += 1
    max_cnt = max(bins) or 1

    ax, ay = x + 42, y + 34
    aw, ah = w - 54, h - 72
    bw2    = aw // n_bins - 2

    for i, cnt in enumerate(bins):
        bh2 = int(ah * cnt / max_cnt)
        bx  = ax + i * (aw // n_bins)
        by  = ay + ah - bh2
        shade = tuple(min(255, int(c * (0.6 + 0.4 * cnt / max_cnt))) for c in _BAR)
        _rnd(surf, shade, (bx, by, bw2, bh2), r=3)
        if cnt > 0:
            cv = fonts["small"].render(str(cnt), True, _ACCENT)
            surf.blit(cv, cv.get_rect(center=(bx + bw2 // 2, by - 11)))
        lbl_v = lo + i * bsize
        lv = fonts["small"].render(str(lbl_v), True, _DIM)
        surf.blit(lv, lv.get_rect(center=(bx + bw2 // 2, ay + ah + 14)))

    for pct in [0, 50, 100]:
        ty = ay + ah - int(ah * pct / 100)
        pygame.draw.line(surf, _BORDER, (ax - 4, ty), (ax + aw, ty), 1)
        v = fonts["small"].render(str(int(max_cnt * pct / 100)), True, _DIM)
        surf.blit(v, (x + 4, ty - 7))

    avg = sum(values) / len(values)
    info = fonts["small"].render(
        f"n={len(values)}   avg={avg:.1f}   min={lo}   max={hi}", True, _DIM)
    surf.blit(info, info.get_rect(center=(ax + aw // 2, ay + ah + 28)))


# ── Full stats screen ─────────────────────────────────────────────────────────

def draw_stats_screen(surf, rows, fonts, SW, SH, sim_running=False, sim_progress=(0, 0)):
    surf.fill(_BG)

    # Title
    sh = fonts["title"].render("Statistics Dashboard", True, (0, 0, 0))
    surf.blit(sh, sh.get_rect(center=(SW // 2 + 2, 28)))
    surf.blit(fonts["title"].render("Statistics Dashboard", True, _GOLD),
              fonts["title"].render("Statistics Dashboard", True, _GOLD).get_rect(center=(SW // 2, 27)))

    n_t = fonts["normal"].render(f"{len(rows)} matches recorded", True, _DIM)
    surf.blit(n_t, n_t.get_rect(midright=(SW - 14, 27)))

    pygame.draw.line(surf, _BORDER, (0, 52), (SW, 52), 1)

    # Layout
    mg = 8
    row1_y, row1_h = 58, 300
    row2_y = row1_y + row1_h + mg
    row2_h = SH - row2_y - 56

    half  = (SW - mg * 3) // 2
    third = (SW - mg * 4) // 3

    charts_row1 = [
        (draw_gem_chart,  (mg,           row1_y, half,  row1_h)),
        (draw_tier_chart, (half + mg*2,  row1_y, half,  row1_h)),
    ]
    charts_row2 = [
        (draw_boxplot,    (mg,                       row2_y, half,  row2_h)),
        (draw_pie_chart,  (half + mg*2,              row2_y, third, row2_h)),
        (draw_histogram,  (half + mg*2 + third + mg, row2_y, third, row2_h)),
    ]

    for fn, rect in charts_row1 + charts_row2:
        fn(surf, rows, rect, fonts)

    # Bottom bar
    pygame.draw.line(surf, _BORDER, (0, SH - 50), (SW, SH - 50), 1)

    if sim_running:
        done, total = sim_progress
        pct = done / total if total else 0
        bar = (SW // 2 - 220, SH - 36, 440, 16)
        _rnd(surf, (30, 28, 22), bar, r=4)
        if pct > 0:
            _rnd(surf, (72, 190, 100), (bar[0], bar[1], int(bar[2] * pct), bar[3]), r=4)
        t = fonts["small"].render(f"Simulating…  {done} / {total}", True, _TEXT)
        surf.blit(t, t.get_rect(center=(SW // 2, SH - 27)))
