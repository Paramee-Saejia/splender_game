"""
stats_view.py - Statistics dashboard rendered with pygame + matplotlib.
"""

import math
import statistics
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
PAGE_LABELS = ["Resources", "Outcomes", "Gold Analysis"]


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


def _gold_spent_per_match(rows):
    return [_i(r, "p1_gold_spent") + _i(r, "p2_gold_spent") for r in rows]


def _pct(numerator, denominator):
    return 0.0 if denominator == 0 else (numerator / denominator) * 100.0


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


def _style_table_axes(ax, title, accent):
    ax.set_facecolor(MPL_CARD)
    for spine in ax.spines.values():
        spine.set_color(MPL_BORDER)
        spine.set_linewidth(1.0)
    ax.set_xticks([])
    ax.set_yticks([])
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


def _plot_gold_summary_table(ax, rows):
    _style_table_axes(ax, "Gold Spend Summary", MPL_GOLD)
    ax.text(
        0.03, 0.88,
        "Statistical values from total gold spent per match",
        transform=ax.transAxes,
        color=MPL_DIM,
        fontsize=8.5,
        ha="left",
        va="top",
    )

    gold_values = _gold_spent_per_match(rows)
    margins = [_i(r, "score_margin") for r in rows]
    if not gold_values:
        ax.text(0.5, 0.5, "No gold data", ha="center", va="center", color=MPL_DIM, transform=ax.transAxes)
        return

    median_gold = statistics.median(gold_values)
    low_group = [m for g, m in zip(gold_values, margins) if g <= median_gold]
    high_group = [m for g, m in zip(gold_values, margins) if g > median_gold]

    table_rows = [
        ["Matches", f"{len(rows)}"],
        ["Avg Gold / Match", f"{statistics.mean(gold_values):.2f}"],
        ["Median Gold", f"{median_gold:.2f}"],
        ["Min - Max Gold", f"{min(gold_values)} - {max(gold_values)}"],
        ["Avg Margin (Low Gold)", f"{statistics.mean(low_group):.2f}" if low_group else "-"],
        ["Avg Margin (High Gold)", f"{statistics.mean(high_group):.2f}" if high_group else "-"],
    ]

    tbl = ax.table(
        cellText=table_rows,
        colLabels=["Metric", "Value"],
        colColours=[_blend := (0.16, 0.12, 0.08), _blend],
        cellLoc="left",
        colLoc="left",
        bbox=[0.03, 0.18, 0.94, 0.60],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor(MPL_BORDER)
        cell.set_linewidth(0.8)
        if row == 0:
            cell.set_facecolor((0.18, 0.13, 0.08))
            cell.get_text().set_color(MPL_TEXT)
            cell.get_text().set_fontweight("bold")
        else:
            cell.set_facecolor((0.10, 0.08, 0.06))
            cell.get_text().set_color(MPL_TEXT if col == 0 else MPL_GOLD)

    ax.text(
        0.03, 0.10,
        "Low Gold = matches with total gold spent less than or equal to the median",
        transform=ax.transAxes,
        color=MPL_DIM,
        fontsize=8,
        ha="left",
        va="center",
    )


def _plot_gem_summary_table(ax, rows):
    _style_table_axes(ax, "Gem Collection Values", MPL_TEAL)
    colors = ["white", "blue", "green", "red", "black"]
    short = ["WHI", "BLU", "GRE", "RED", "BLA"]
    p1 = [sum(_i(r, f"p1_gem_{c}") for r in rows) for c in colors]
    p2 = [sum(_i(r, f"p2_gem_{c}") for r in rows) for c in colors]
    totals = [a + b for a, b in zip(p1, p2)]
    rows_data = [[lbl, str(a), str(b), str(t)] for lbl, a, b, t in zip(short, p1, p2, totals)]
    tbl = ax.table(
        cellText=rows_data,
        colLabels=["Color", "Bot A", "Bot B", "Total"],
        cellLoc="center",
        colLoc="center",
        bbox=[0.04, 0.16, 0.92, 0.70],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.3)
    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor(MPL_BORDER)
        cell.set_linewidth(0.8)
        if row == 0:
            cell.set_facecolor((0.10, 0.16, 0.16))
            cell.get_text().set_color(MPL_TEXT)
            cell.get_text().set_fontweight("bold")
        else:
            cell.set_facecolor((0.10, 0.08, 0.06))
            cell.get_text().set_color(MPL_TEXT)


def _plot_tier_summary_table(ax, rows):
    _style_table_axes(ax, "Tier Purchase Values", MPL_GOLD)
    tiers = [1, 2, 3]
    values = [sum(_i(r, f"p1_tier{t}") + _i(r, f"p2_tier{t}") for r in rows) for t in tiers]
    total_cards = sum(values)
    rows_data = [[f"Tier {t}", str(v), f"{_pct(v, total_cards):.1f}%"] for t, v in zip(tiers, values)]
    rows_data.append(["All Tiers", str(total_cards), "100.0%" if total_cards else "0.0%"])
    tbl = ax.table(
        cellText=rows_data,
        colLabels=["Tier", "Count", "Share"],
        cellLoc="center",
        colLoc="center",
        bbox=[0.10, 0.18, 0.80, 0.62],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor(MPL_BORDER)
        cell.set_linewidth(0.8)
        if row == 0:
            cell.set_facecolor((0.18, 0.13, 0.08))
            cell.get_text().set_color(MPL_TEXT)
            cell.get_text().set_fontweight("bold")
        else:
            cell.set_facecolor((0.10, 0.08, 0.06))
            cell.get_text().set_color(MPL_TEXT if col != 1 else MPL_GOLD)


def _plot_margin_summary_table(ax, rows):
    _style_table_axes(ax, "Margin Statistical Values", MPL_ROSE)
    values = sorted(_i(r, "score_margin") for r in rows)
    if not values:
        ax.text(0.5, 0.5, "No margin data", ha="center", va="center", color=MPL_DIM, transform=ax.transAxes)
        return
    rows_data = [
        ["Matches", f"{len(values)}"],
        ["Average", f"{statistics.mean(values):.2f}"],
        ["Median", f"{statistics.median(values):.2f}"],
        ["Minimum", str(min(values))],
        ["Maximum", str(max(values))],
        ["Range", str(max(values) - min(values))],
    ]
    tbl = ax.table(
        cellText=rows_data,
        colLabels=["Metric", "Value"],
        cellLoc="left",
        colLoc="left",
        bbox=[0.08, 0.18, 0.84, 0.62],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor(MPL_BORDER)
        cell.set_linewidth(0.8)
        if row == 0:
            cell.set_facecolor((0.18, 0.10, 0.10))
            cell.get_text().set_color(MPL_TEXT)
            cell.get_text().set_fontweight("bold")
        else:
            cell.set_facecolor((0.10, 0.08, 0.06))
            cell.get_text().set_color(MPL_TEXT if col == 0 else MPL_ROSE)


def _plot_turn_summary_table(ax, rows):
    _style_table_axes(ax, "Turn Statistical Values", MPL_BLUE)
    values = [_i(r, "total_turns") for r in rows if _i(r, "total_turns") > 0]
    if not values:
        ax.text(0.5, 0.5, "No turn data", ha="center", va="center", color=MPL_DIM, transform=ax.transAxes)
        return
    rows_data = [
        ["Matches", f"{len(values)}"],
        ["Average", f"{statistics.mean(values):.2f}"],
        ["Median", f"{statistics.median(values):.2f}"],
        ["Minimum", str(min(values))],
        ["Maximum", str(max(values))],
        ["Std Dev", f"{statistics.pstdev(values):.2f}" if len(values) > 1 else "0.00"],
    ]
    tbl = ax.table(
        cellText=rows_data,
        colLabels=["Metric", "Value"],
        cellLoc="left",
        colLoc="left",
        bbox=[0.08, 0.18, 0.84, 0.62],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor(MPL_BORDER)
        cell.set_linewidth(0.8)
        if row == 0:
            cell.set_facecolor((0.10, 0.12, 0.18))
            cell.get_text().set_color(MPL_TEXT)
            cell.get_text().set_fontweight("bold")
        else:
            cell.set_facecolor((0.10, 0.08, 0.06))
            cell.get_text().set_color(MPL_TEXT if col == 0 else MPL_BLUE)


def _plot_gold_margin_scatter(ax, rows):
    _style_axes(ax, "Gold Spent vs Score Margin", MPL_GOLD)
    gold_values = _gold_spent_per_match(rows)
    margins = [_i(r, "score_margin") for r in rows]
    if not gold_values:
        ax.text(0.5, 0.5, "No gold data", ha="center", va="center", color=MPL_DIM, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        return

    ax.grid(True, axis="both", color=MPL_BORDER, alpha=0.35, linewidth=0.8)
    ax.scatter(
        gold_values,
        margins,
        s=34,
        color=_mpl_color(P2_COL),
        edgecolors=_mpl_color(GOLD),
        linewidths=0.8,
        alpha=0.85,
        label="Matches",
        zorder=3,
    )
    ax.set_xlabel("Total gold spent in match", color=MPL_DIM, fontsize=9, labelpad=10)
    ax.set_ylabel("Score margin", color=MPL_DIM, fontsize=9)

    mean_gold = statistics.mean(gold_values)
    mean_margin = statistics.mean(margins)
    ax.axvline(mean_gold, color=MPL_GOLD, linewidth=1.3, linestyle="--", alpha=0.9)
    ax.axhline(mean_margin, color=MPL_ROSE, linewidth=1.3, linestyle=":", alpha=0.9)

    n = len(gold_values)
    if n >= 2:
        sum_x = sum(gold_values)
        sum_y = sum(margins)
        sum_xy = sum(x * y for x, y in zip(gold_values, margins))
        sum_x2 = sum(x * x for x in gold_values)
        denom = n * sum_x2 - sum_x * sum_x
        if denom != 0:
            slope = (n * sum_xy - sum_x * sum_y) / denom
            intercept = (sum_y - slope * sum_x) / n
            x1, x2 = min(gold_values), max(gold_values)
            y1 = slope * x1 + intercept
            y2 = slope * x2 + intercept
            ax.plot([x1, x2], [y1, y2], color=_mpl_color(P1_COL), linewidth=2.0, label="Trend", zorder=4)

    ax.annotate(
        f"avg gold {mean_gold:.2f}\navg margin {mean_margin:.2f}",
        xy=(0.98, 0.08),
        xycoords="axes fraction",
        ha="right",
        va="bottom",
        fontsize=8.5,
        color=MPL_TEXT,
        bbox=dict(boxstyle="round,pad=0.28", facecolor=MPL_CARD, edgecolor=MPL_BORDER, linewidth=0.8),
    )
    ax.legend(loc="upper right", frameon=False, labelcolor=MPL_TEXT, fontsize=8)


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

    if page == 0:
        gs = fig.add_gridspec(2, 2, left=0.06, right=0.985, top=0.95, bottom=0.06,
                              hspace=0.24, wspace=0.18, height_ratios=[1.08, 0.92])
        ax_gem = fig.add_subplot(gs[0, 0])
        ax_tier = fig.add_subplot(gs[0, 1])
        ax_gem_table = fig.add_subplot(gs[1, 0])
        ax_tier_table = fig.add_subplot(gs[1, 1])
        _plot_gem_chart(ax_gem, rows)
        _plot_tier_chart(ax_tier, rows)
        _plot_gem_summary_table(ax_gem_table, rows)
        _plot_tier_summary_table(ax_tier_table, rows)
    elif page == 1:
        gs = fig.add_gridspec(2, 2, left=0.06, right=0.985, top=0.95, bottom=0.06,
                              hspace=0.24, wspace=0.18, height_ratios=[1.08, 0.92])
        ax_box = fig.add_subplot(gs[0, 0])
        ax_hist = fig.add_subplot(gs[0, 1])
        ax_margin_table = fig.add_subplot(gs[1, 0])
        ax_turn_table = fig.add_subplot(gs[1, 1])
        _plot_boxplot(ax_box, rows)
        _plot_hist(ax_hist, rows)
        _plot_margin_summary_table(ax_margin_table, rows)
        _plot_turn_summary_table(ax_turn_table, rows)
    else:
        gs = fig.add_gridspec(1, 2, left=0.05, right=0.985, top=0.95, bottom=0.10,
                              hspace=0.2, wspace=0.18, width_ratios=[0.85, 1.15])
        ax_gold_table = fig.add_subplot(gs[0, 0])
        ax_gold_scatter = fig.add_subplot(gs[0, 1])
        _plot_gold_summary_table(ax_gold_table, rows)
        _plot_gold_margin_scatter(ax_gold_scatter, rows)

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
    return len(PAGE_LABELS)


def get_stats_nav_rects(screen_w, screen_h, total_pages):
    nav = {
    }
    tab_y = 66
    tab_w = 132
    tab_h = 28
    gap = 10
    total_w = total_pages * tab_w + max(0, total_pages - 1) * gap
    start_x = screen_w // 2 - total_w // 2
    nav["tabs"] = [
        (start_x + i * (tab_w + gap), tab_y, tab_w, tab_h)
        for i in range(total_pages)
    ]
    return nav


def _draw_stats_nav(surf, fonts, screen_w, screen_h, page, total_pages):
    mx, my = pygame.mouse.get_pos()
    nav = get_stats_nav_rects(screen_w, screen_h, total_pages)
    page = max(0, min(page, total_pages - 1))

    for i, rect in enumerate(nav.get("tabs", [])):
        active = i == page
        hovered = rect[0] <= mx < rect[0] + rect[2] and rect[1] <= my < rect[1] + rect[3]
        fill = CARD2 if active else CARD
        edge = GOLD if active else (BLUE if hovered else BORDER)
        _rnd(surf, fill, rect, r=8)
        _rnd(surf, fill, rect, r=8, bw=1, bc=edge)
        label = PAGE_LABELS[i] if i < len(PAGE_LABELS) else f"Page {i + 1}"
        t = fonts["small"].render(label, True, TEXT if active or hovered else DIM)
        surf.blit(t, t.get_rect(center=(rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)))



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
    _draw_stats_nav(surf, fonts, screen_w, screen_h, page, total_pages)
    content_rect = (8, 102, screen_w - 16, screen_h - 160)

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

    if sim_running:
        done, total = sim_progress
        msg = fonts["small"].render(f"Simulating {done}/{total}", True, GREEN_A)
        surf.blit(msg, (16, screen_h - 36))
