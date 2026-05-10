"""
stats_view.py - Statistics dashboard rendered with pygame + matplotlib.
"""

import math
import pygame

import matplotlib

matplotlib.use("Agg")

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure


BG = (10, 8, 6)
CARD = (20, 16, 12)
CARD2 = (28, 22, 16)
BORDER = (48, 38, 24)
TEXT = (232, 224, 210)
DIM = (115, 104, 84)
GOLD = (245, 197, 62)
TEAL = (42, 191, 175)
BLUE = (70, 150, 230)
ROSE = (220, 80, 80)
GREEN_A = (72, 200, 110)

GEM = {
    "white": (215, 210, 195),
    "blue": (58, 130, 200),
    "green": (42, 168, 70),
    "red": (210, 52, 52),
    "black": (80, 80, 80),
}
GEM_BRIGHT = {
    "white": (255, 252, 240),
    "blue": (100, 170, 255),
    "green": (80, 220, 110),
    "red": (255, 100, 100),
    "black": (130, 130, 130),
}
TIER_COL = {1: (72, 165, 72), 2: (185, 122, 46), 3: (168, 58, 58)}
P1_COL = (228, 170, 62)
P2_COL = (78, 168, 132)
BOX_COL = (126, 110, 194)
BOX_EDGE = (164, 147, 228)
HIST_COL = (70, 148, 228)

MPL_BG = tuple(c / 255 for c in BG)
MPL_CARD = tuple(c / 255 for c in CARD)
MPL_BORDER = tuple(c / 255 for c in BORDER)
MPL_TEXT = tuple(c / 255 for c in TEXT)
MPL_DIM = tuple(c / 255 for c in DIM)
MPL_GOLD = tuple(c / 255 for c in GOLD)
MPL_TEAL = tuple(c / 255 for c in TEAL)
MPL_BLUE = tuple(c / 255 for c in BLUE)
MPL_ROSE = tuple(c / 255 for c in ROSE)
MPL_BOX = tuple(c / 255 for c in BOX_COL)
MPL_BOX_EDGE = tuple(c / 255 for c in BOX_EDGE)
MPL_HIST = tuple(c / 255 for c in HIST_COL)

_FIGURE_CACHE = {}


def _rnd(surf, col, rect, r=8, bw=0, bc=None):
    pygame.draw.rect(surf, col, rect, border_radius=r)
    if bw:
        pygame.draw.rect(surf, bc or col, rect, bw, border_radius=r)


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


def _rows_signature(rows):
    return (
        len(rows),
        sum(_i(r, "total_turns") for r in rows),
        sum(_i(r, "score_margin") for r in rows),
        sum(_i(r, "p1_gold_spent") + _i(r, "p2_gold_spent") for r in rows),
        sum(_i(r, "p1_tier1") + _i(r, "p2_tier1") for r in rows),
        sum(_i(r, "p1_tier2") + _i(r, "p2_tier2") for r in rows),
        sum(_i(r, "p1_tier3") + _i(r, "p2_tier3") for r in rows),
    )


def _mpl_color(rgb):
    return tuple(c / 255 for c in rgb)


def _style_axes(ax, title, accent):
    ax.set_facecolor(MPL_CARD)
    for spine in ax.spines.values():
        spine.set_color(MPL_BORDER)
        spine.set_linewidth(1.0)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MPL_DIM, labelsize=9, pad=4)
    ax.grid(True, axis="y", color=MPL_BORDER, alpha=0.45, linewidth=0.8)
    ax.set_title("")
    ax.plot([0, 1], [0.985, 0.985], transform=ax.transAxes, color=accent, linewidth=2, clip_on=False)
    ax.text(
        0.012, 0.945, title,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        color=MPL_TEXT,
        fontsize=10,
        fontweight="bold",
        bbox=dict(facecolor=MPL_CARD, edgecolor="none", pad=0.4),
        zorder=5,
    )


def _plot_gem_chart(ax, rows):
    _style_axes(ax, "Gem Color Collection", MPL_TEAL)
    colors = ["white", "blue", "green", "red", "black"]
    labels = ["WHI", "BLU", "GRE", "RED", "BLA"]
    p1 = [sum(_i(r, f"p1_gem_{c}") for r in rows) for c in colors]
    p2 = [sum(_i(r, f"p2_gem_{c}") for r in rows) for c in colors]
    totals = [a + b for a, b in zip(p1, p2)]
    x = list(range(len(colors)))

    ax.bar(x, p1, color=[_mpl_color(GEM_BRIGHT[c]) for c in colors], width=0.66, label="Bot A", edgecolor="none")
    ax.bar(x, p2, bottom=p1, color=[_mpl_color(GEM[c]) for c in colors], width=0.66, label="Bot B", edgecolor="none")
    ax.set_xticks(x, labels)
    ax.margins(x=0.05)
    ymax = max(totals) if totals else 1
    ax.set_ylim(0, ymax * 1.28 if ymax > 0 else 1)
    for i, total in enumerate(totals):
        ax.text(i, total + ymax * 0.05, str(total), ha="center", va="bottom", color=MPL_TEXT, fontsize=9)
    ax.legend(loc="upper right", frameon=False, labelcolor=MPL_TEXT, fontsize=8)


def _plot_tier_chart(ax, rows):
    _style_axes(ax, "Card Tier Purchases", MPL_GOLD)
    tiers = [1, 2, 3]
    values = [sum(_i(r, f"p1_tier{t}") + _i(r, f"p2_tier{t}") for r in rows) for t in tiers]
    labels = [f"Tier {t}" for t in tiers]
    ypos = [2, 1, 0]
    cols = [_mpl_color(TIER_COL[t]) for t in tiers]
    ax.barh(ypos, values, color=cols, height=0.5)
    ax.set_yticks(ypos, labels)
    ax.set_xlim(0, max(values) * 1.18 if max(values) > 0 else 1)
    ax.grid(True, axis="x", color=MPL_BORDER, alpha=0.45, linewidth=0.8)
    ax.grid(False, axis="y")
    for y, v in zip(ypos, values):
        ax.text(v + max(values) * 0.02 if max(values) > 0 else 0.05, y, str(v),
                va="center", ha="left", color=MPL_TEXT, fontsize=10, fontweight="bold")


def _plot_boxplot(ax, rows):
    _style_axes(ax, "Final Score Margin", MPL_ROSE)
    values = sorted(_i(r, "score_margin") for r in rows)
    if not values:
        ax.text(0.5, 0.5, "No score margin data", ha="center", va="center", color=MPL_DIM, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        return
    bp = ax.boxplot(
        values,
        vert=False,
        patch_artist=True,
        widths=0.46,
        boxprops=dict(facecolor=MPL_BOX, edgecolor=MPL_BOX_EDGE, linewidth=1.2),
        medianprops=dict(color=MPL_GOLD, linewidth=2.2),
        whiskerprops=dict(color=MPL_DIM, linewidth=1.3),
        capprops=dict(color=MPL_DIM, linewidth=1.3),
        flierprops=dict(marker="o", markersize=3, markerfacecolor=MPL_ROSE, markeredgecolor=MPL_ROSE, alpha=0.8),
    )
    avg = sum(values) / len(values)
    ax.scatter([avg], [1], color=MPL_ROSE, s=55, zorder=3, label=f"Avg {avg:.1f}")
    ax.legend(loc="upper right", frameon=False, labelcolor=MPL_TEXT, fontsize=8)
    ax.set_yticks([])
    ax.grid(True, axis="x", color=MPL_BORDER, alpha=0.45, linewidth=0.8)


def _plot_pie(ax, rows):
    _style_axes(ax, "Gold Token Usage", MPL_GOLD)
    ax.grid(False)
    p1g = sum(_i(r, "p1_gold_spent") for r in rows)
    p2g = sum(_i(r, "p2_gold_spent") for r in rows)
    values = [p1g, p2g]
    labels = ["Bot A", "Bot B"]
    cols = [_mpl_color(P1_COL), _mpl_color(P2_COL)]
    total = sum(values)
    if total == 0:
        ax.text(0.5, 0.5, "No gold spent yet", ha="center", va="center", color=MPL_DIM, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        return
    ax.pie(
        values,
        colors=cols,
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.46, edgecolor=MPL_CARD),
        autopct=lambda pct: f"{pct:.0f}%" if pct > 0 else "",
        pctdistance=0.77,
        textprops=dict(color=MPL_TEXT, fontsize=9, fontweight="bold"),
    )
    ax.legend(labels, loc="lower center", bbox_to_anchor=(0.5, -0.03), ncol=2,
              frameon=False, labelcolor=MPL_TEXT, fontsize=8)


def _plot_hist(ax, rows):
    _style_axes(ax, "Turns per Match", MPL_BLUE)
    values = [_i(r, "total_turns") for r in rows if _i(r, "total_turns") > 0]
    if not values:
        ax.text(0.5, 0.5, "No turn data", ha="center", va="center", color=MPL_DIM, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        return
    counts, bins, patches = ax.hist(values, bins=8, color=MPL_HIST, edgecolor=MPL_BORDER, alpha=0.9)
    avg = sum(values) / len(values)
    ax.axvline(avg, color=MPL_GOLD, linewidth=2)
    peak = max(counts) if len(counts) else 1
    ax.annotate(
        f"avg {avg:.1f}",
        xy=(avg, peak),
        xytext=(8, 10),
        textcoords="offset points",
        ha="left",
        va="bottom",
        color=MPL_GOLD,
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.2", facecolor=MPL_CARD, edgecolor=MPL_GOLD, linewidth=0.8),
    )
    ax.set_ylim(0, peak * 1.18 if peak > 0 else 1)


def _render_matplotlib_page(rows, width, height, page, total_pages):
    fig = Figure(figsize=(width / 100, height / 100), dpi=100, facecolor=MPL_BG)
    canvas = FigureCanvasAgg(fig)

    if total_pages == 1:
        gs = fig.add_gridspec(2, 4, left=0.06, right=0.985, top=0.95, bottom=0.06,
                              hspace=0.24, wspace=0.22)
        ax_gem = fig.add_subplot(gs[0, 0:2])
        ax_tier = fig.add_subplot(gs[0, 2:4])
        ax_box = fig.add_subplot(gs[1, 0:2])
        ax_pie = fig.add_subplot(gs[1, 2])
        ax_hist = fig.add_subplot(gs[1, 3])
        _plot_gem_chart(ax_gem, rows)
        _plot_tier_chart(ax_tier, rows)
        _plot_boxplot(ax_box, rows)
        _plot_pie(ax_pie, rows)
        _plot_hist(ax_hist, rows)
    elif page == 0:
        gs = fig.add_gridspec(2, 2, left=0.06, right=0.985, top=0.95, bottom=0.06,
                              hspace=0.24, wspace=0.18, height_ratios=[0.92, 1.30])
        ax_gem = fig.add_subplot(gs[0, 0])
        ax_tier = fig.add_subplot(gs[0, 1])
        ax_box = fig.add_subplot(gs[1, :])
        _plot_gem_chart(ax_gem, rows)
        _plot_tier_chart(ax_tier, rows)
        _plot_boxplot(ax_box, rows)
    else:
        gs = fig.add_gridspec(1, 2, left=0.05, right=0.985, top=0.95, bottom=0.06,
                              hspace=0.2, wspace=0.18, width_ratios=[0.85, 1.15])
        ax_pie = fig.add_subplot(gs[0, 0])
        ax_hist = fig.add_subplot(gs[0, 1])
        _plot_pie(ax_pie, rows)
        _plot_hist(ax_hist, rows)

    canvas.draw()
    raw = canvas.buffer_rgba()
    surface = pygame.image.frombuffer(raw, (width, height), "RGBA").copy()
    return surface


def _get_dashboard_surface(rows, width, height, page, total_pages):
    key = (width, height, page, total_pages, _rows_signature(rows))
    cached = _FIGURE_CACHE.get(key)
    if cached is not None:
        return cached
    surface = _render_matplotlib_page(rows, width, height, page, total_pages)
    _FIGURE_CACHE.clear()
    _FIGURE_CACHE[key] = surface
    return surface


def _draw_summary(surf, rows, screen_w, fonts):
    if not rows:
        return
    n = len(rows)
    avg_turns = sum(_i(r, "total_turns") for r in rows) / n
    avg_margin = sum(_i(r, "score_margin") for r in rows) / n

    pills = [
        ("Matches", n, TEAL),
        ("Avg Turns", f"{avg_turns:.1f}", BLUE),
        ("Avg Margin", f"{avg_margin:.1f}", ROSE),
    ]
    total_w = sum(90 for _ in pills) + 16 * (len(pills) - 1)
    sx = screen_w - total_w - 14
    sy = 6
    for label, value, color in pills:
        _stat_pill(surf, sx, sy, label, value, color, fonts)
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
        _rnd(surf, CARD2 if enabled else CARD, rect, r=7, bw=1, bc=BLUE if hovered else BORDER)
        text_col = TEXT if enabled else DIM
        t = fonts["normal"].render(label, True, text_col)
        surf.blit(t, t.get_rect(center=(rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)))

    chip = nav["page"]
    _rnd(surf, CARD2, chip, r=7)
    _rnd(surf, CARD2, chip, r=7, bw=1, bc=BORDER)
    t = fonts["bold"].render(f"{page + 1}/{total_pages}", True, GOLD)
    surf.blit(t, t.get_rect(center=(chip[0] + chip[2] // 2, chip[1] + chip[3] // 2)))


def draw_stats_screen(surf, rows, fonts, screen_w, screen_h,
                      sim_running=False, sim_progress=(0, 0), page=0):
    surf.fill(BG)

    t_sh = fonts["title"].render("Statistics Dashboard", True, (0, 0, 0))
    t = fonts["title"].render("Statistics Dashboard", True, GOLD)
    surf.blit(t_sh, t_sh.get_rect(midleft=(14, 29)))
    surf.blit(t, t.get_rect(midleft=(13, 28)))

    _draw_summary(surf, rows, screen_w, fonts)
    pygame.draw.line(surf, BORDER, (0, 60), (screen_w, 60), 1)

    total_pages = get_stats_page_count(screen_h)
    page = max(0, min(page, total_pages - 1))
    content_rect = (8, 70, screen_w - 16, screen_h - 128)

    if not rows:
        _rnd(surf, CARD, content_rect, r=10)
        _rnd(surf, CARD, content_rect, r=10, bw=1, bc=BORDER)
        _no_data(surf, content_rect, fonts)
    else:
        mpl_surface = _get_dashboard_surface(
            rows, content_rect[2], content_rect[3], page, total_pages
        )
        surf.blit(mpl_surface, content_rect[:2])

    pygame.draw.line(surf, BORDER, (0, screen_h - 50), (screen_w, screen_h - 50), 1)
    _draw_stats_nav(surf, fonts, screen_w, screen_h, page, total_pages)

    if sim_running:
        done, total = sim_progress
        msg = fonts["small"].render(f"Simulating {done}/{total}", True, GREEN_A)
        surf.blit(msg, (16, screen_h - 36))
