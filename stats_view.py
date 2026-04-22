"""
stats_view.py - Modern statistics dashboard for Splendor.
"""

import math
import pygame


BG      = (10, 8, 6)
CARD    = (20, 16, 12)
CARD2   = (28, 22, 16)
BORDER  = (48, 38, 24)
TEXT    = (232, 224, 210)
DIM     = (115, 104, 84)
GOLD    = (245, 197, 62)
TEAL    = (42, 191, 175)
BLUE    = (70, 150, 230)
ROSE    = (220, 80, 80)
GREEN_A = (72, 200, 110)

GEM = {
    "white": (215, 210, 195),
    "blue":  (58, 130, 200),
    "green": (42, 168, 70),
    "red":   (210, 52, 52),
    "black": (80, 80, 80),
}
GEM_BRIGHT = {
    "white": (255, 252, 240),
    "blue":  (100, 170, 255),
    "green": (80, 220, 110),
    "red":   (255, 100, 100),
    "black": (130, 130, 130),
}
TIER_COL  = {1: (72, 165, 72), 2: (185, 122, 46), 3: (168, 58, 58)}
TIER_GLOW = {1: (120, 220, 100), 2: (230, 165, 80), 3: (220, 90, 90)}
P1_COL    = (70, 148, 228)
P2_COL    = (228, 118, 50)


def _rnd(surf, col, rect, r=8, bw=0, bc=None):
    pygame.draw.rect(surf, col, rect, border_radius=r)
    if bw:
        pygame.draw.rect(surf, bc or col, rect, bw, border_radius=r)


def _gradient_bar(surf, rect, top_c, bot_c, r=5):
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
    _rnd(surf, CARD, rect, r=10)
    _rnd(surf, CARD, rect, r=10, bw=1, bc=BORDER)
    pygame.draw.rect(surf, accent, (rect[0] + 1, rect[1] + 1, rect[2] - 2, 3),
                     border_radius=10)
    sh = fonts["bold"].render(title, True, (0, 0, 0))
    surf.blit(sh, (rect[0] + 13, rect[1] + 12))
    surf.blit(fonts["bold"].render(title, True, TEXT), (rect[0] + 12, rect[1] + 11))


def _stat_pill(surf, x, y, label, value, col, fonts):
    lbl = fonts["small"].render(label, True, DIM)
    val = fonts["bold"].render(str(value), True, col)
    w = max(lbl.get_width(), val.get_width()) + 18
    _rnd(surf, CARD2, (x, y, w, 36), r=6)
    _rnd(surf, CARD2, (x, y, w, 36), r=6, bw=1, bc=BORDER)
    surf.blit(lbl, lbl.get_rect(center=(x + w // 2, y + 10)))
    surf.blit(val, val.get_rect(center=(x + w // 2, y + 26)))
    return w


def _no_data(surf, rect, fonts):
    t = fonts["normal"].render("No data - press Run Simulations to start", True, DIM)
    surf.blit(t, t.get_rect(center=(rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)))


def _i(row, key):
    try:
        return int(row.get(key, 0))
    except Exception:
        return 0


def _grid_h(surf, ax, ay, aw, ah, max_v, ticks, font):
    for pct in ticks:
        ty = ay + ah - int(ah * pct / 100)
        col = (38, 30, 20) if pct != 0 else BORDER
        pygame.draw.line(surf, col, (ax, ty), (ax + aw, ty), 1)
        v = font.render(str(int(max_v * pct / 100)), True, DIM)
        surf.blit(v, (ax - v.get_width() - 5, ty - 6))


def draw_gem_chart(surf, rows, rect, fonts):
    x, y, w, h = rect
    _panel(surf, rect, "Gem Color Collection", TEAL, fonts)
    if not rows:
        _no_data(surf, rect, fonts)
        return

    colors = ["white", "blue", "green", "red", "black"]
    p1 = {c: sum(_i(r, f"p1_gem_{c}") for r in rows) for c in colors}
    p2 = {c: sum(_i(r, f"p2_gem_{c}") for r in rows) for c in colors}
    totals = {c: p1[c] + p2[c] for c in colors}
    max_v = max(totals.values()) or 1

    ax, ay = x + 42, y + 36
    aw, ah = w - 54, h - 86
    bw = aw // 8
    gap = (aw - bw * 5) // 6

    _grid_h(surf, ax, ay, aw, ah, max_v, [0, 25, 50, 75, 100], fonts["small"])

    for i, c in enumerate(colors):
        bx = ax + i * (bw + gap) + gap
        tot = totals[c]
        bh = int(ah * tot / max_v)
        by = ay + ah - bh

        h2 = int(bh * p2[c] / max(tot, 1))
        h1 = bh - h2
        if h2 > 0:
            _gradient_bar(surf, (bx, ay + ah - h2, bw, h2),
                          GEM_BRIGHT[c], GEM[c], r=4 if h1 == 0 else 2)
        if h1 > 0:
            _gradient_bar(surf, (bx, by, bw, h1),
                          tuple(min(255, v + 40) for v in GEM_BRIGHT[c]),
                          GEM_BRIGHT[c], r=4)

        if tot > 0:
            _glow_circle(surf, bx + bw // 2, by, 6, GEM_BRIGHT[c], 50)
            lbl = fonts["small"].render(str(tot), True, TEXT)
            surf.blit(lbl, lbl.get_rect(center=(bx + bw // 2, by - 13)))

        pygame.draw.circle(surf, GEM[c], (bx + bw // 2, ay + ah + 12), 5)
        nl = fonts["small"].render(c[:3].upper(), True, TEXT)
        surf.blit(nl, nl.get_rect(center=(bx + bw // 2, ay + ah + 26)))

    total_all = sum(totals.values())
    px = x + 12
    for lbl, val, col in [("Total", total_all, TEAL), ("Matches", len(rows), GOLD)]:
        pw = _stat_pill(surf, px, y + h - 44, lbl, val, col, fonts)
        px += pw + 8


def draw_tier_chart(surf, rows, rect, fonts):
    x, y, w, h = rect
    _panel(surf, rect, "Card Tier Purchases", GOLD, fonts)
    if not rows:
        _no_data(surf, rect, fonts)
        return

    totals = {
        t: sum(_i(r, f"p1_tier{t}") + _i(r, f"p2_tier{t}") for r in rows)
        for t in [1, 2, 3]
    }
    grand = sum(totals.values()) or 1

    ax, ay = x + 16, y + 42
    aw, ah = w - 32, h - 96
    row_h = ah // 3 - 6

    for i, tier in enumerate([1, 2, 3]):
        by = ay + i * (row_h + 16)
        val = totals[tier]
        pct = val / grand
        bar_w = int((aw - 80) * pct)

        _rnd(surf, CARD2, (ax + 60, by, aw - 80, row_h), r=5)
        if bar_w > 0:
            _gradient_bar(surf, (ax + 60, by, bar_w, row_h),
                          TIER_GLOW[tier], TIER_COL[tier], r=5)
        if bar_w > 8:
            _glow_circle(surf, ax + 60 + bar_w, by + row_h // 2, 8,
                         TIER_GLOW[tier], 60)

        tl = fonts["bold"].render(f"Tier {tier}", True, TIER_GLOW[tier])
        surf.blit(tl, (ax, by + row_h // 2 - tl.get_height() // 2))

        vl = fonts["bold"].render(f"{val}", True, TEXT)
        surf.blit(vl, (ax + aw - 55, by + row_h // 2 - vl.get_height() // 2))
        pl = fonts["small"].render(f"{pct * 100:.0f}%", True, DIM)
        surf.blit(pl, (ax + aw - 32, by + row_h // 2 - pl.get_height() // 2))

    px = x + 12
    for lbl, val, col in [
        ("Total Cards", grand, GOLD),
        ("Per Match", f"{grand / max(len(rows), 1):.1f}", GREEN_A),
    ]:
        pw = _stat_pill(surf, px, y + h - 44, lbl, val, col, fonts)
        px += pw + 8


def draw_boxplot(surf, rows, rect, fonts):
    x, y, w, h = rect
    _panel(surf, rect, "Final Score Margin", ROSE, fonts)
    if not rows:
        _no_data(surf, rect, fonts)
        return

    values = sorted(_i(r, "score_margin") for r in rows)
    n = len(values)
    if n == 0:
        _no_data(surf, rect, fonts)
        return

    lo = values[0]
    hi = values[-1]
    q1 = values[n // 4]
    med = values[n // 2]
    q3 = values[3 * n // 4]
    avg = sum(values) / n
    span = max(hi - lo, 1)

    ax, ay = x + 14, y + 48
    aw, ah = w - 28, h - 110

    def px(v):
        return ax + int(aw * (v - lo) / span)

    cy = ay + ah // 2
    bh = ah // 3

    iqr_s = pygame.Surface((max(1, px(q3) - px(q1)), bh + 16), pygame.SRCALPHA)
    iqr_s.fill((60, 100, 180, 40))
    surf.blit(iqr_s, (px(q1), cy - bh // 2 - 8))

    for pct in [0, 25, 50, 75, 100]:
        gx = ax + int(aw * pct / 100)
        pygame.draw.line(surf, (35, 28, 18), (gx, ay), (gx, ay + ah), 1)
        lv = lo + int(span * pct / 100)
        t = fonts["small"].render(str(lv), True, DIM)
        surf.blit(t, t.get_rect(center=(gx, ay + ah + 12)))

    pygame.draw.line(surf, DIM, (px(lo), cy), (px(q1), cy), 2)
    pygame.draw.line(surf, DIM, (px(q3), cy), (px(hi), cy), 2)
    for cap_x in (px(lo), px(hi)):
        pygame.draw.line(surf, DIM, (cap_x, cy - bh // 2), (cap_x, cy + bh // 2), 2)

    box = (px(q1), cy - bh // 2, max(4, px(q3) - px(q1)), bh)
    _gradient_bar(surf, box, (80, 120, 200), (45, 75, 145), r=5)
    _rnd(surf, (45, 75, 145), box, r=5, bw=1, bc=(100, 140, 220))

    pygame.draw.line(surf, GOLD, (px(med), cy - bh // 2), (px(med), cy + bh // 2), 3)
    _glow_circle(surf, int(px(avg)), cy, 6, ROSE, 80)
    pygame.draw.circle(surf, ROSE, (int(px(avg)), cy), 5)
    pygame.draw.circle(surf, (255, 150, 150), (int(px(avg)), cy), 3)

    for v, lbl, col in [
        (lo, "Min", DIM),
        (q1, "Q1", TEXT),
        (med, "Med", GOLD),
        (q3, "Q3", TEXT),
        (hi, "Max", DIM),
    ]:
        t = fonts["small"].render(f"{lbl} {v}", True, col)
        surf.blit(t, t.get_rect(center=(px(v), ay + 12)))

    px2 = x + 12
    for lbl, val, col in [("Avg", f"{avg:.1f}", BLUE), ("Median", med, GOLD), ("n", n, DIM)]:
        pw = _stat_pill(surf, px2, y + h - 44, lbl, val, col, fonts)
        px2 += pw + 8


def draw_pie_chart(surf, rows, rect, fonts):
    x, y, w, h = rect
    _panel(surf, rect, "Gold Token Usage", GOLD, fonts)
    if not rows:
        _no_data(surf, rect, fonts)
        return

    p1g = sum(_i(r, "p1_gold_spent") for r in rows)
    p2g = sum(_i(r, "p2_gold_spent") for r in rows)
    total = p1g + p2g or 1

    cx = x + w // 2
    cy = y + h // 2 + 4
    outer = min(w, h) // 3
    inner = outer * 55 // 100

    slices = [
        (p1g, P1_COL, (130, 190, 255), "Bot A"),
        (p2g, P2_COL, (255, 180, 120), "Bot B"),
    ]
    angle = -math.pi / 2

    for val, col, bright, _ in slices:
        sweep = 2 * math.pi * val / total
        steps = max(3, int(sweep * 50))
        pts = [(cx, cy)]
        for s in range(steps + 1):
            a = angle + sweep * s / steps
            pts.append((cx + outer * math.cos(a), cy + outer * math.sin(a)))
        if len(pts) >= 3:
            pygame.draw.polygon(surf, col, pts)
        for s in range(steps):
            a1 = angle + sweep * s / steps
            t = s / max(steps, 1)
            gc = tuple(int(col[i] * (1 - t) + bright[i] * t) for i in range(3))
            pygame.draw.line(
                surf, gc,
                (cx + int(outer * 0.88 * math.cos(a1)), cy + int(outer * 0.88 * math.sin(a1))),
                (cx + int(outer * math.cos(a1)), cy + int(outer * math.sin(a1))),
                3,
            )
        angle += sweep

    pygame.draw.circle(surf, CARD, (cx, cy), inner)
    pygame.draw.circle(surf, BORDER, (cx, cy), inner, 1)

    tot_t = fonts["bold"].render(str(p1g + p2g), True, GOLD)
    sub_t = fonts["small"].render("gold used", True, DIM)
    surf.blit(tot_t, tot_t.get_rect(center=(cx, cy - 6)))
    surf.blit(sub_t, sub_t.get_rect(center=(cx, cy + 11)))

    ly = y + h - 78
    for val, col, _, lbl in slices:
        pygame.draw.rect(surf, col, (x + 12, ly, 12, 12), border_radius=3)
        t = fonts["small"].render(f"{lbl}: {val} ({val * 100 // total}%)", True, TEXT)
        surf.blit(t, (x + 28, ly))
        ly += 20


def draw_histogram(surf, rows, rect, fonts):
    x, y, w, h = rect
    _panel(surf, rect, "Turns per Match", BLUE, fonts)
    if not rows:
        _no_data(surf, rect, fonts)
        return

    values = [_i(r, "total_turns") for r in rows if _i(r, "total_turns") > 0]
    if not values:
        _no_data(surf, rect, fonts)
        return

    lo, hi = min(values), max(values)
    n_bins = 8
    bsize = max(1, math.ceil((hi - lo + 1) / n_bins))
    bins = [0] * n_bins
    for v in values:
        bi = min(n_bins - 1, (v - lo) // bsize)
        bins[bi] += 1
    max_cnt = max(bins) or 1
    avg = sum(values) / len(values)

    ax, ay = x + 42, y + 36
    aw, ah = w - 54, h - 90
    bw = aw // n_bins - 3

    _grid_h(surf, ax, ay, aw, ah, max_cnt, [0, 50, 100], fonts["small"])

    avg_x = ax + int(aw * (avg - lo) / max(hi - lo, 1))
    pygame.draw.line(surf, GOLD, (avg_x, ay), (avg_x, ay + ah), 1)
    al = fonts["small"].render(f"avg {avg:.0f}", True, GOLD)
    surf.blit(al, (avg_x + 3, ay + 2))

    for i, cnt in enumerate(bins):
        bh = int(ah * cnt / max_cnt)
        bx = ax + i * (aw // n_bins) + 1
        by = ay + ah - bh
        if cnt == 0:
            continue
        t = cnt / max_cnt
        top = tuple(int(BLUE[j] * (0.5 + 0.5 * t) + 80 * (1 - t)) for j in range(3))
        bot = tuple(int(BLUE[j] * 0.5) for j in range(3))
        _gradient_bar(surf, (bx, by, bw, bh), top, bot, r=4)

        cv = fonts["small"].render(str(cnt), True, TEXT)
        surf.blit(cv, cv.get_rect(center=(bx + bw // 2, by - 11)))

        lv = fonts["small"].render(str(lo + i * bsize), True, DIM)
        surf.blit(lv, lv.get_rect(center=(bx + bw // 2, ay + ah + 13)))

    px2 = x + 12
    for lbl, val, col in [("Avg", f"{avg:.1f}", BLUE), ("Min", lo, DIM), ("Max", hi, DIM)]:
        pw = _stat_pill(surf, px2, y + h - 44, lbl, val, col, fonts)
        px2 += pw + 8


def _draw_summary(surf, rows, SW, fonts):
    if not rows:
        return
    n = len(rows)
    avg_t = sum(_i(r, "total_turns") for r in rows) / n
    avg_m = sum(_i(r, "score_margin") for r in rows) / n

    pills = [
        ("Matches", n, TEAL),
        ("Avg Turns", f"{avg_t:.1f}", BLUE),
        ("Avg Margin", f"{avg_m:.1f}", ROSE),
    ]
    total_w = sum(90 for _ in pills) + 16 * (len(pills) - 1)
    sx = SW - total_w - 14
    sy = 6
    for lbl, val, col in pills:
        _stat_pill(surf, sx, sy, lbl, val, col, fonts)
        sx += 106


def get_stats_page_count(screen_h):
    return 1 if screen_h >= 860 else 2


def get_stats_nav_rects(screen_w, screen_h, total_pages):
    if total_pages <= 1:
        return {}
    y = screen_h - 42
    return {
        "prev": (screen_w // 2 - 116, y, 92, 34),
        "page": (screen_w // 2 - 28, y, 56, 34),
        "next": (screen_w // 2 + 24, y, 92, 34),
    }


def _draw_stats_nav(surf, fonts, screen_w, screen_h, page, total_pages):
    if total_pages <= 1:
        return

    mx, my = pygame.mouse.get_pos()
    nav = get_stats_nav_rects(screen_w, screen_h, total_pages)
    page = max(0, min(page, total_pages - 1))

    for key, label, enabled in [
        ("prev", "< Prev", page > 0),
        ("next", "Next >", page < total_pages - 1),
    ]:
        rect = nav[key]
        hovered = enabled and rect[0] <= mx < rect[0] + rect[2] and rect[1] <= my < rect[1] + rect[3]
        _rnd(surf, CARD2 if enabled else CARD, rect, r=7)
        _rnd(surf, CARD2 if enabled else CARD, rect, r=7, bw=1,
             bc=BLUE if hovered else BORDER)
        text_col = TEXT if enabled else DIM
        t = fonts["normal"].render(label, True, text_col)
        surf.blit(t, t.get_rect(center=(rect[0] + rect[2] // 2,
                                        rect[1] + rect[3] // 2)))

    chip = nav["page"]
    _rnd(surf, CARD2, chip, r=7)
    _rnd(surf, CARD2, chip, r=7, bw=1, bc=BORDER)
    t = fonts["bold"].render(f"{page + 1}/{total_pages}", True, GOLD)
    surf.blit(t, t.get_rect(center=(chip[0] + chip[2] // 2,
                                    chip[1] + chip[3] // 2)))


def _draw_single_page_layout(surf, rows, fonts, screen_w, screen_h):
    mg = 8
    row1_y, row1_h = 58, 296
    row2_y = row1_y + row1_h + mg
    row2_h = screen_h - row2_y - 56

    half = (screen_w - mg * 3) // 2
    third = (screen_w - mg * 4) // 3

    draw_gem_chart(surf, rows, (mg, row1_y, half, row1_h), fonts)
    draw_tier_chart(surf, rows, (half + mg * 2, row1_y, half, row1_h), fonts)
    draw_boxplot(surf, rows, (mg, row2_y, half, row2_h), fonts)
    draw_pie_chart(surf, rows, (half + mg * 2, row2_y, third, row2_h), fonts)
    draw_histogram(surf, rows, (half + mg * 2 + third + mg, row2_y, third, row2_h), fonts)


def _draw_paged_layout(surf, rows, fonts, screen_w, screen_h, page):
    mg = 8
    top = 58
    bottom = screen_h - 58
    content_h = bottom - top
    page = max(0, min(page, 1))

    if page == 0:
        row1_h = int(content_h * 0.42)
        row2_y = top + row1_h + mg
        row2_h = bottom - row2_y
        half = (screen_w - mg * 3) // 2

        draw_gem_chart(surf, rows, (mg, top, half, row1_h), fonts)
        draw_tier_chart(surf, rows, (half + mg * 2, top, half, row1_h), fonts)
        draw_boxplot(surf, rows, (mg, row2_y, screen_w - mg * 2, row2_h), fonts)
    else:
        left_w = int((screen_w - mg * 3) * 0.40)
        right_x = mg + left_w + mg
        right_w = screen_w - right_x - mg

        draw_pie_chart(surf, rows, (mg, top, left_w, content_h), fonts)
        draw_histogram(surf, rows, (right_x, top, right_w, content_h), fonts)


def draw_stats_screen(surf, rows, fonts, screen_w, screen_h,
                      sim_running=False, sim_progress=(0, 0), page=0):
    surf.fill(BG)

    t_sh = fonts["title"].render("Statistics Dashboard", True, (0, 0, 0))
    t = fonts["title"].render("Statistics Dashboard", True, GOLD)
    surf.blit(t_sh, t_sh.get_rect(midleft=(14, 29)))
    surf.blit(t, t.get_rect(midleft=(13, 28)))

    _draw_summary(surf, rows, screen_w, fonts)
    pygame.draw.line(surf, BORDER, (0, 52), (screen_w, 52), 1)

    total_pages = get_stats_page_count(screen_h)
    page = max(0, min(page, total_pages - 1))

    if total_pages == 1:
        _draw_single_page_layout(surf, rows, fonts, screen_w, screen_h)
    else:
        _draw_paged_layout(surf, rows, fonts, screen_w, screen_h, page)

    pygame.draw.line(surf, BORDER, (0, screen_h - 50), (screen_w, screen_h - 50), 1)
    _draw_stats_nav(surf, fonts, screen_w, screen_h, page, total_pages)

    if sim_running:
        done, total = sim_progress
        msg = fonts["small"].render(f"Simulating {done}/{total}", True, GREEN_A)
        surf.blit(msg, (16, screen_h - 36))
