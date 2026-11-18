"""
ChargeAhead: generate the chart set used in the mid-semester deck.

Palette matches the Idea Pitch deck:
  BG      F5F8F6 (near white)
  NAVY    10202E (title text, dark bars)
  LIME    C9F03F (accent)
  TEAL    14A88C (NEV / BEV lines)
  ORANGE  D4643C (ICE / warning)
  AMBER   F0A93B (PHEV / supporting)
  GREY    5E6E7E (gridline / axis)
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
FIG = ROOT / "outputs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

BG = "#F5F8F6"
NAVY = "#10202E"
LIME = "#C9F03F"
TEAL = "#14A88C"
TEAL_DARK = "#0A7663"
ORANGE = "#D4643C"
AMBER = "#F0A93B"
GREY = "#5E6E7E"
GREY_LIGHT = "#93A3B3"

plt.rcParams.update({
    "font.family": ["Noto Sans CJK SC", "Noto Sans CJK HK", "DejaVu Sans"],
    "axes.facecolor": BG,
    "figure.facecolor": BG,
    "savefig.facecolor": BG,
    "axes.edgecolor": GREY_LIGHT,
    "axes.labelcolor": GREY,
    "xtick.color": GREY,
    "ytick.color": GREY,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "grid.color": "#D5DBDE",
    "grid.linestyle": "--",
    "grid.linewidth": 0.6,
    "axes.unicode_minus": False,
})

# Mapping from Chinese brand names to English for deliverables
BRAND_EN = {
    "比亚迪": "BYD",
    "特斯拉": "Tesla China",
    "特斯拉中国": "Tesla China",
    "理想汽车": "Li Auto",
    "蔚来": "NIO",
    "小鹏": "XPeng",
    "小米汽车": "Xiaomi",
    "零跑汽车": "Leapmotor",
    "吉利汽车": "Geely",
    "奇瑞汽车": "Chery",
    "极氪": "ZEEKR",
    "赛力斯": "Seres",
    "赛力斯汽车": "Seres",
    "广汽埃安": "GAC Aion",
    "深蓝汽车": "Deepal",
    "阿维塔": "Avatr",
    "智己汽车": "IM Motors",
    "岚图汽车": "Voyah",
    "领克": "Lynk and Co",
    "飞凡汽车": "Rising",
    "ARCFOX极狐": "ARCFOX",
    "上汽通用五菱": "SGMW",
    "长安汽车": "Changan",
    "上汽乘用车": "SAIC",
}


def _save(fig, name):
    out = FIG / name
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


# ------------------------------------------------------------------
# chart 1: Transition Index overview (level + components)
# ------------------------------------------------------------------
def chart_transition_index():
    idx = pd.read_csv(PROC / "transition_index.csv", parse_dates=["month"])
    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(10, 4.6), sharex=True,
                                   gridspec_kw={"height_ratios": [1.3, 1]})

    ax0.plot(idx["month"], idx["transition_index"], color=NAVY, linewidth=2.4, label="Transition Index")
    ax0.fill_between(idx["month"], idx["transition_index"], 0, alpha=0.10, color=TEAL)
    ax0.set_ylabel("Index (0 to 1)", color=GREY)
    ax0.set_ylim(0, 1.05)
    ax0.grid(axis="y", alpha=0.5)
    ax0.set_title("Powertrain Transition Index  —  Jan 2023 to Aug 2026",
                  fontsize=12, color=NAVY, loc="left", pad=10, fontweight="bold")

    # components normalized to [0,1]
    comp_map = [
        ("c1_nev_penetration_norm", "NEV penetration", TEAL),
        ("c2_ice_decline_norm", "ICE YoY decline", ORANGE),
        ("c3_bev_share_nev_norm", "BEV share within NEV", TEAL_DARK),
        ("c4_bev_a0_plus_a_norm", "BEV mainstream (A0+A)", AMBER),
    ]
    for col, label, color in comp_map:
        ax1.plot(idx["month"], idx[col], color=color, linewidth=1.5, alpha=0.9, label=label)

    ax1.legend(ncol=4, frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(0, 1.18))
    ax1.set_ylim(-0.05, 1.05)
    ax1.set_ylabel("Normalized", color=GREY)
    ax1.grid(axis="y", alpha=0.5)
    ax1.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))

    plt.setp(ax1.get_xticklabels(), rotation=0, ha="center")
    _save(fig, "01_transition_index.png")


# ------------------------------------------------------------------
# chart 2: Channel signal + Transition Index
# ------------------------------------------------------------------
def chart_channel_vs_index():
    idx = pd.read_csv(PROC / "transition_index.csv", parse_dates=["month"])
    panel = pd.read_csv(PROC / "national_panel.csv", parse_dates=["month"])
    df = idx[["month", "transition_index"]].merge(
        panel[["month", "channel_gap_wan", "inventory_ratio"]], on="month"
    )

    fig, ax = plt.subplots(figsize=(10, 4.4))
    ax.set_title("Channel inventory signal and Transition Index",
                 fontsize=12, color=NAVY, loc="left", pad=10, fontweight="bold")

    ax.bar(df["month"], df["channel_gap_wan"], width=22, color=GREY_LIGHT, alpha=0.6,
           label="Channel gap, wholesale minus retail (10k units, left)")
    ax.set_ylabel("Channel gap (10k units)", color=GREY)
    ax.axhline(0, color=GREY, linewidth=0.8)
    ax.grid(axis="y", alpha=0.4)

    ax2 = ax.twinx()
    ax2.plot(df["month"], df["transition_index"], color=NAVY, linewidth=2.2,
             label="Transition Index (right)")
    ax2.set_ylabel("Transition Index", color=NAVY)
    ax2.set_ylim(0, 1.05)
    ax2.spines["top"].set_visible(False)

    # merged legend
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=False, fontsize=9)

    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    _save(fig, "02_channel_vs_index.png")


# ------------------------------------------------------------------
# chart 3: Lead-lag correlation
# ------------------------------------------------------------------
def chart_leadlag():
    lgap = pd.read_csv(PROC / "leadlag_channel_gap_vs_index_level.csv")
    lrat = pd.read_csv(PROC / "leadlag_ratio_vs_index_level.csv")

    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.set_title("Lead-lag of channel signals against the Transition Index",
                 fontsize=12, color=NAVY, loc="left", pad=10, fontweight="bold")

    ax.axvline(0, color=GREY_LIGHT, linewidth=0.8)
    ax.axhline(0, color=GREY_LIGHT, linewidth=0.8)

    ax.plot(lgap["lag"], lgap["corr"], marker="o", color=TEAL, linewidth=2,
            label="Channel gap (wholesale - retail)")
    ax.plot(lrat["lag"], lrat["corr"], marker="s", color=TEAL_DARK, linewidth=2,
            label="Inventory ratio")

    # Mark best lag with annotation
    best_lag_g = int(lgap.loc[lgap["corr"].abs().idxmax(), "lag"])
    best_c_g = float(lgap.loc[lgap["corr"].abs().idxmax(), "corr"])
    ax.annotate(f"lag {best_lag_g}  r={best_c_g:.2f}",
                xy=(best_lag_g, best_c_g), xytext=(best_lag_g + 0.5, best_c_g + 0.08),
                color=TEAL, fontsize=9, fontweight="bold")

    best_lag_r = int(lrat.loc[lrat["corr"].abs().idxmax(), "lag"])
    best_c_r = float(lrat.loc[lrat["corr"].abs().idxmax(), "corr"])
    ax.annotate(f"lag {best_lag_r}  r={best_c_r:.2f}",
                xy=(best_lag_r, best_c_r), xytext=(best_lag_r + 0.5, best_c_r - 0.1),
                color=TEAL_DARK, fontsize=9, fontweight="bold")

    ax.set_xlabel("Lag (months), positive = signal leads the index")
    ax.set_ylabel("Pearson correlation")
    ax.set_ylim(-0.3, 1.0)
    ax.legend(loc="lower center", frameon=False, fontsize=9, ncol=2)
    _save(fig, "03_leadlag.png")


# ------------------------------------------------------------------
# chart 4: Brand-level growth, Mar - Aug 2026
# ------------------------------------------------------------------
def chart_brand_growth():
    bdf = pd.read_csv(PROC / "brand_growth_2026H1.csv")
    bdf = bdf.dropna(subset=["growth_mar_to_aug"]).sort_values("growth_mar_to_aug")
    # Translate brand names
    bdf["brand_en"] = bdf["brand"].map(BRAND_EN).fillna(bdf["brand"])
    display = bdf.copy()
    # cap growth above 1.2 for visual balance
    display["g_clip"] = display["growth_mar_to_aug"].clip(upper=1.2)

    color_map = {"bev_only": TEAL, "mixed_bev_erev": AMBER, "mixed_bev_phev": GREY,
                 "phev_only": ORANGE, "erev_only": ORANGE, "unknown": GREY_LIGHT}
    colors = [color_map.get(p, GREY) for p in display["profile"]]

    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.set_title("Brand-level sales growth, March to August 2026",
                 fontsize=12, color=NAVY, loc="left", pad=10, fontweight="bold")
    bars = ax.barh(display["brand_en"], display["g_clip"] * 100, color=colors, edgecolor="white")
    ax.axvline(0, color=GREY, linewidth=0.8)
    ax.set_xlabel("Growth from Mar 2026 to Aug 2026 (%)")
    ax.grid(axis="x", alpha=0.4)

    # Annotate bars with raw growth
    for bar, raw in zip(bars, display["growth_mar_to_aug"]):
        w = bar.get_width()
        ax.text(w + (3 if w >= 0 else -3), bar.get_y() + bar.get_height() / 2,
                f"{raw*100:+.0f}%",
                va="center", ha="left" if w >= 0 else "right",
                color=NAVY, fontsize=8)

    # Legend using proxy artists
    import matplotlib.patches as mpatches
    legend_items = [
        mpatches.Patch(color=TEAL, label="BEV only"),
        mpatches.Patch(color=AMBER, label="BEV + EREV"),
        mpatches.Patch(color=GREY, label="BEV + PHEV"),
    ]
    ax.legend(handles=legend_items, loc="lower right", frameon=False, fontsize=9)
    _save(fig, "04_brand_growth.png")


# ------------------------------------------------------------------
# chart 5: baseline comparison (bar chart)
# ------------------------------------------------------------------
def chart_baseline():
    b = pd.read_csv(PROC / "baseline_metrics.csv")
    fig, ax = plt.subplots(figsize=(10, 3.6))
    x = np.arange(len(b))
    w = 0.35
    ax.bar(x - w/2, b["mae"], width=w, color=TEAL, label="MAE on one-step change in index")
    ax.bar(x + w/2, b["direction_accuracy"], width=w, color=AMBER,
           label="Direction accuracy")
    ax.set_xticks(x)
    ax.set_xticklabels(b["model"], rotation=0, fontsize=8)
    ax.set_title("Baseline evaluation on monthly change of the Transition Index",
                 fontsize=12, color=NAVY, loc="left", pad=10, fontweight="bold")
    ax.axhline(0.5, color=GREY_LIGHT, linewidth=0.8, linestyle=":")
    ax.text(ax.get_xlim()[1], 0.52, "chance = 0.5", color=GREY_LIGHT, fontsize=8, ha="right")
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=2)
    ax.set_ylim(0, 1.0)
    ax.grid(axis="y", alpha=0.4)
    for i, (mae, da) in enumerate(zip(b["mae"], b["direction_accuracy"])):
        ax.text(i - w/2, mae + 0.015, f"{mae:.3f}", ha="center", fontsize=8, color=NAVY)
        ax.text(i + w/2, da + 0.015, f"{da:.0%}", ha="center", fontsize=8, color=NAVY)
    _save(fig, "05_baseline.png")


# ------------------------------------------------------------------
# chart 6: data coverage grid (what we have vs do not)
# ------------------------------------------------------------------
def chart_data_coverage():
    rows = [
        ("CPCA monthly aggregates (retail, wholesale, NEV, BEV/PHEV/EREV, BEV level mix)", 2023, 2026, "in hand"),
        ("Channel inventory signal (batched from CPCA)", 2023, 2026, "in hand"),
        ("ICE YoY retail decline (derived)", 2024, 2026, "in hand"),
        ("Brand- and model-level retail (CPCA auto info website)", 2026, 2026, "partial, Mar to Aug 2026"),
        ("Baidu Search Index (consumer attention)", 2023, 2026, "not yet collected"),
        ("Weekly insurance registrations (hand sample)", 2023, 2025, "sparse, exploratory only"),
        ("Residual values (CADA / Chezhen)", 2024, 2026, "not yet collected"),
    ]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    for i, (label, y0, y1, status) in enumerate(reversed(rows)):
        color = TEAL if "in hand" in status else (AMBER if "partial" in status or "sparse" in status else ORANGE)
        ax.barh(i, y1 - y0 + 1, left=y0, height=0.55, color=color, edgecolor="white")
        ax.text(y0 + 0.05, i, status, va="center", ha="left", color="white", fontsize=8, fontweight="bold")
        ax.text(y0 - 0.08, i, label, va="center", ha="right", color=NAVY, fontsize=8)
    ax.set_xlim(2021.5, 2026.6)
    ax.set_yticks([])
    ax.set_xticks([2023, 2024, 2025, 2026])
    ax.set_title("Data coverage going into the mid-semester review",
                 fontsize=12, color=NAVY, loc="left", pad=10, fontweight="bold")
    ax.spines["left"].set_visible(False)
    _save(fig, "06_data_coverage.png")


# ------------------------------------------------------------------
# chart 7: Baidu attention signals alongside Transition Index
# ------------------------------------------------------------------
def chart_baidu_vs_index():
    sigs = pd.read_csv(PROC / "baidu_signals_monthly.csv", parse_dates=["month"])
    idx = pd.read_csv(PROC / "transition_index.csv", parse_dates=["month"])
    df = sigs.merge(idx[["month", "transition_index"]], on="month").sort_values("month")

    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(10, 4.8), sharex=True,
                                   gridspec_kw={"height_ratios": [1, 1]})

    # Top: Transition Index
    ax0.plot(df["month"], df["transition_index"], color=NAVY, linewidth=2.2, label="Transition Index")
    ax0.fill_between(df["month"], df["transition_index"], 0, alpha=0.1, color=TEAL)
    ax0.set_ylim(0, 1.05)
    ax0.set_ylabel("Index", color=GREY)
    ax0.set_title("Baidu attention signals meet the Transition Index  —  monthly",
                  fontsize=12, color=NAVY, loc="left", pad=10, fontweight="bold")
    ax0.grid(axis="y", alpha=0.4)
    ax0.legend(frameon=False, fontsize=9, loc="upper left")

    # Bottom: three attention signals, normalized to [0,1] each
    def norm(s):
        lo, hi = s.min(), s.max()
        return (s - lo) / (hi - lo) if hi > lo else s * 0

    ax1.plot(df["month"], norm(df["att_nev_overall"]), color=TEAL_DARK, linewidth=1.8,
             label="NEV category (新能源汽车)")
    ax1.plot(df["month"], norm(df["att_brand_bev_pure"]), color=TEAL, linewidth=1.6,
             label="BEV brand pure (6 brands)")
    ax1.plot(df["month"], norm(df["att_brand_erev_lead"]), color=AMBER, linewidth=1.6,
             label="EREV brand lead (Li Auto + AITO + HIMA)")
    ax1.plot(df["month"], norm(df["att_pw_ice_cat"]), color=ORANGE, linewidth=1.4, linestyle=":",
             label="ICE category (燃油车)")

    ax1.set_ylim(-0.05, 1.1)
    ax1.set_ylabel("Attention (normalized)", color=GREY)
    ax1.grid(axis="y", alpha=0.4)
    ax1.legend(ncol=2, frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(0, 1.18))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    _save(fig, "07_baidu_vs_index.png")


# ------------------------------------------------------------------
# chart 8: Baidu-as-feature vs persistence baseline
# ------------------------------------------------------------------
def chart_baidu_baseline():
    b = pd.read_csv(PROC / "baidu_vs_baseline.csv")
    # Simplify names
    name_map = {
        "att_nev_overall": "NEV category attention",
        "att_brand_bev_pure": "BEV brand attention",
        "att_brand_erev_lead": "EREV brand attention",
        "att_model_top": "Top-model attention",
        "PERSISTENCE_BASELINE": "Persistence (baseline)",
    }
    b["label"] = b["feature"].map(name_map).fillna(b["feature"])

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(10, 3.5))
    colors = [LIME if lbl == "Persistence (baseline)" else TEAL for lbl in b["label"]]

    ax0.barh(b["label"], b["test_mae"], color=colors)
    ax0.set_title("Test-set MAE on monthly dIndex (lower is better)", fontsize=10, color=NAVY,
                  loc="left", fontweight="bold")
    for i, v in enumerate(b["test_mae"]):
        ax0.text(v + 0.001, i, f"{v:.3f}", va="center", fontsize=8, color=NAVY)
    ax0.grid(axis="x", alpha=0.4)

    ax1.barh(b["label"], b["test_direction_acc"] * 100, color=colors)
    ax1.set_title("Test-set direction accuracy (higher is better)", fontsize=10, color=NAVY,
                  loc="left", fontweight="bold")
    for i, v in enumerate(b["test_direction_acc"]):
        ax1.text(v * 100 + 1, i, f"{v*100:.0f}%", va="center", fontsize=8, color=NAVY)
    ax1.set_xlim(0, 100)
    ax1.grid(axis="x", alpha=0.4)

    fig.suptitle("Baidu attention as a feature  —  NEV category attention beats persistence on MAE",
                 fontsize=12, color=NAVY, x=0.02, ha="left", fontweight="bold", y=1.03)
    plt.tight_layout()
    _save(fig, "08_baidu_baseline.png")


# ------------------------------------------------------------------
# chart 9: refreshed data coverage (Baidu now in hand)
# ------------------------------------------------------------------
def chart_data_coverage_v2():
    rows = [
        ("CPCA monthly aggregates (retail, wholesale, NEV, BEV/PHEV/EREV, BEV level mix)", 2023, 2026, "in hand"),
        ("Channel inventory signal (derived from CPCA)", 2023, 2026, "in hand"),
        ("ICE YoY retail decline (derived)", 2024, 2026, "in hand"),
        ("Baidu Search Index — 42 kw, weekly, 2023 to Oct 2026", 2023, 2026, "in hand"),
        ("Brand-level retail (CPCA auto info, hand-collected)", 2026, 2026, "partial, Mar-Aug 2026"),
        ("Brand-level wholesale (CPCA table 五, parseable)", 2025, 2026, "parseable, pending"),
        ("Residual values (CADA / Chezhen)", 2024, 2026, "not collected, treated as stretch"),
    ]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    for i, (label, y0, y1, status) in enumerate(reversed(rows)):
        if "in hand" in status:
            color = TEAL
        elif "partial" in status or "parseable" in status:
            color = AMBER
        else:
            color = ORANGE
        ax.barh(i, y1 - y0 + 1, left=y0, height=0.55, color=color, edgecolor="white")
        ax.text(y0 + 0.05, i, status, va="center", ha="left", color="white", fontsize=8, fontweight="bold")
        ax.text(y0 - 0.08, i, label, va="center", ha="right", color=NAVY, fontsize=8)
    ax.set_xlim(2021.5, 2026.6)
    ax.set_yticks([])
    ax.set_xticks([2023, 2024, 2025, 2026])
    ax.set_title("Data coverage after Baidu Index collection", fontsize=12, color=NAVY,
                 loc="left", pad=10, fontweight="bold")
    ax.spines["left"].set_visible(False)
    _save(fig, "06_data_coverage.png")


if __name__ == "__main__":
    chart_transition_index()
    chart_channel_vs_index()
    chart_leadlag()
    chart_brand_growth()
    chart_baseline()
    chart_data_coverage_v2()
    chart_baidu_vs_index()
    chart_baidu_baseline()
