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


# ------------------------------------------------------------------
# chart 9: STL decomposition of the Transition Index
# ------------------------------------------------------------------
def chart_stl():
    stl = pd.read_csv(PROC / "stl_components.csv", parse_dates=["month"]).sort_values("month")

    fig, axes = plt.subplots(4, 1, figsize=(10, 4.6), sharex=True,
                             gridspec_kw={"height_ratios": [1, 1, 1, 1]})
    titles = ["Observed", "Trend", "Seasonal (period 12)", "Residual"]
    cols = ["observed", "trend", "seasonal", "resid"]
    colors = [NAVY, TEAL_DARK, AMBER, ORANGE]
    for ax, title, col, color in zip(axes, titles, cols, colors):
        ax.plot(stl["month"], stl[col], color=color, linewidth=1.6)
        ax.set_ylabel(title, color=GREY, fontsize=8)
        ax.grid(axis="y", alpha=0.3)
        if title == "Residual":
            ax.axhline(0, color=GREY_LIGHT, linewidth=0.6)
    axes[0].set_title("STL decomposition of the Transition Index  —  trend, seasonal, residual",
                      fontsize=11, color=NAVY, loc="left", pad=10, fontweight="bold")
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    _save(fig, "09_stl.png")


# ------------------------------------------------------------------
# chart 10: Walk-forward comparison (Baidu vs Persistence)
# ------------------------------------------------------------------
def chart_walkforward():
    wf = pd.read_csv(PROC / "walkforward_metrics.csv", parse_dates=["month"]).sort_values("month")
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(10, 2.8),
                                   gridspec_kw={"width_ratios": [1.2, 1]})

    # Left panel: forecasts vs actual
    ax0.plot(wf["month"], wf["y_true"], color=NAVY, linewidth=2, label="Actual dIndex", marker="o", markersize=3)
    ax0.plot(wf["month"], wf["y_hat_baidu"], color=TEAL, linewidth=1.4, label="Baidu NEV (walk-forward)", linestyle="--")
    ax0.plot(wf["month"], wf["y_hat_persist"], color=AMBER, linewidth=1.4, label="Persistence baseline", linestyle=":")
    ax0.axhline(0, color=GREY_LIGHT, linewidth=0.6)
    ax0.set_ylabel("dIndex (next-month change)", color=GREY, fontsize=8)
    ax0.set_title("Forecasts vs actual", fontsize=10, color=NAVY, loc="left", fontweight="bold")
    ax0.legend(frameon=False, fontsize=7, loc="upper left", ncol=1)
    ax0.grid(axis="y", alpha=0.4)
    ax0.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax0.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))

    # Right panel: cumulative absolute error
    cum_b = wf["abs_err_baidu"].cumsum()
    cum_p = wf["abs_err_persist"].cumsum()
    ax1.plot(wf["month"], cum_b, color=TEAL, linewidth=2, label="Baidu")
    ax1.plot(wf["month"], cum_p, color=AMBER, linewidth=2, label="Persistence")
    ax1.fill_between(wf["month"], cum_b, cum_p, where=(cum_p >= cum_b), alpha=0.15, color=TEAL)
    ax1.set_ylabel("Cumulative abs error", color=GREY, fontsize=8)
    ax1.set_title("Cumulative error (lower is better)", fontsize=10, color=NAVY, loc="left", fontweight="bold")
    ax1.grid(axis="y", alpha=0.4)
    ax1.legend(frameon=False, fontsize=8, loc="upper left")
    ax1.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))

    plt.tight_layout()
    _save(fig, "10_walkforward.png")


# ------------------------------------------------------------------
# chart 11: Methodology summary (ADF + MASE + IC + regime table)
# ------------------------------------------------------------------
def chart_methodology_summary():
    adf = pd.read_csv(PROC / "adf_tests.csv")
    mase = pd.read_csv(PROC / "mase_scores.csv")
    ic = pd.read_csv(PROC / "ic_summary.csv")
    regime = pd.read_csv(PROC / "regime_verdict.csv")

    fig, axes = plt.subplots(2, 2, figsize=(10, 4.4))
    for ax in axes.flat:
        ax.axis("off")

    def _text_block(ax, title, lines, x=0.02, start_y=0.9, dy=0.14, title_color=NAVY):
        ax.text(x, 0.98, title, fontsize=10, color=title_color, fontweight="bold",
                ha="left", va="top", transform=ax.transAxes)
        for i, (label, value, color) in enumerate(lines):
            ax.text(x, start_y - dy * i, label, fontsize=8.5, color=GREY,
                    ha="left", va="top", transform=ax.transAxes)
            ax.text(0.98, start_y - dy * i, value, fontsize=9.5, color=color, fontweight="bold",
                    ha="right", va="top", transform=ax.transAxes)

    # ADF card
    adf_lines = []
    for _, r in adf.iterrows():
        verdict = "stationary" if r["stationary_5pct"] else "NON-stationary"
        color = TEAL if r["stationary_5pct"] else ORANGE
        adf_lines.append((r["series"], f"p = {r['p_value']:.2g}  {verdict}", color))
    _text_block(axes[0, 0], "ADF stationarity test", adf_lines)

    # Scaled error card (renamed from MASE to be precise about definition)
    mase_lines = []
    for _, r in mase.iterrows():
        color = TEAL if r["MASE"] < 1 else GREY
        mase_lines.append((r["model"], f"ratio = {r['MASE']:.2f}", color))
    mase_lines.append(("walk-forward, 19 monthly forecasts", "", GREY_LIGHT))
    _text_block(axes[0, 1], "Scaled error = Baidu MAE / persistence MAE  (<1 beats baseline)", mase_lines)

    # IC card
    ic_lines = []
    for _, r in ic.iterrows():
        color = TEAL if abs(r["ic_full_sample"]) > 0.1 else GREY
        ic_lines.append((r["signal"], f"IC = {r['ic_full_sample']:.2f}", color))
    ic_lines.append(("sign is inverted, see risks slide", "", GREY_LIGHT))
    _text_block(axes[1, 0], "Information Coefficient", ic_lines)

    # Regime card
    regime_lines = []
    for _, r in regime.iterrows():
        color = TEAL if r["verdict"] == "PASS" else ORANGE
        regime_lines.append((f"{r['regime']}  (n={r['n_months']})",
                             f"MAE {r['mae_baidu']:.03f} vs {r['mae_persist']:.03f}  {r['verdict']}", color))
    _text_block(axes[1, 1], "Regime verdict (Baidu vs persistence)", regime_lines, dy=0.17)

    fig.suptitle("Methodology upgrade  —  Lec 6 four-step rigor applied to the Transition Index",
                 fontsize=12, color=NAVY, x=0.02, ha="left", fontweight="bold", y=1.02)
    plt.tight_layout()
    _save(fig, "11_methodology.png")


# ------------------------------------------------------------------
# chart 12: Baseline comparison matrix (70/30 split vs walk-forward)
# ------------------------------------------------------------------
def chart_baseline_matrix():
    """Three-panel honest comparison. Panel 1: 70/30 split. Panel 2:
    walk-forward on the ORIGINAL full-window-scaled index. Panel 3:
    walk-forward on the LEAKAGE-CHECKED (expanding-window min-max) index.
    This makes the headline leakage-checked, with the old 27% shown for
    comparison, and surfaces the direction accuracy collapse honestly."""
    bvb = pd.read_csv(PROC / "baidu_vs_baseline.csv")
    wf = pd.read_csv(PROC / "walkforward_summary.csv")
    exp = pd.read_csv(PROC / "ablation_expanding_walkforward.csv")

    split_rows = [
        ("Persist.", float(bvb.loc[bvb["feature"] == "PERSISTENCE_BASELINE", "test_mae"].iloc[0]),
         float(bvb.loc[bvb["feature"] == "PERSISTENCE_BASELINE", "test_direction_acc"].iloc[0])),
        ("Baidu", float(bvb.loc[bvb["feature"] == "att_nev_overall", "test_mae"].iloc[0]),
         float(bvb.loc[bvb["feature"] == "att_nev_overall", "test_direction_acc"].iloc[0])),
    ]
    orig_wf_rows = [
        ("Persist.", float(wf.loc[wf["model"] == "Persistence", "mae"].iloc[0]),
         float(wf.loc[wf["model"] == "Persistence", "direction_accuracy"].iloc[0])),
        ("Baidu", float(wf.loc[wf["model"] == "Baidu NEV attention (walk-forward)", "mae"].iloc[0]),
         float(wf.loc[wf["model"] == "Baidu NEV attention (walk-forward)", "direction_accuracy"].iloc[0])),
    ]
    leak = exp.loc[exp["index_variant"] == "Expanding-window min-max (no look-ahead)"].iloc[0]
    leak_rows = [
        ("Persist.", float(leak["mae_persist"]), float(leak["dir_persist"])),
        ("Baidu",    float(leak["mae_baidu"]),   float(leak["dir_baidu"])),
    ]

    fig, (ax0, ax1, ax2) = plt.subplots(1, 3, figsize=(10, 2.9))

    def _panel(ax, rows, title, subtitle, headline_color):
        labels = [r[0] for r in rows]
        mae = [r[1] for r in rows]
        dir_acc = [r[2] * 100 for r in rows]
        x = np.arange(len(labels))
        w = 0.38
        colors_mae = [AMBER, TEAL]
        colors_dir = [GREY_LIGHT, TEAL_DARK]

        ax.bar(x - w/2, mae, w, color=colors_mae)
        for xi, v in zip(x - w/2, mae):
            ax.text(xi, v + 0.004, f"{v:.3f}", ha="center", fontsize=7.5, color=NAVY)

        axR = ax.twinx()
        axR.bar(x + w/2, dir_acc, w, color=colors_dir, alpha=0.9)
        for xi, v in zip(x + w/2, dir_acc):
            axR.text(xi, v + 2, f"{v:.0f}%", ha="center", fontsize=7.5, color=NAVY)
        axR.set_ylim(0, 110)
        axR.set_ylabel("Direction %", color=GREY, fontsize=7.5)
        axR.spines["right"].set_visible(True)
        axR.spines["right"].set_color(GREY_LIGHT)
        axR.tick_params(labelsize=7)

        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=8, color=NAVY)
        ax.set_ylabel("MAE (dIndex)", color=GREY, fontsize=7.5)
        ax.set_ylim(0, 0.12)
        ax.tick_params(labelsize=7)
        ax.set_title(f"{title}\n{subtitle}",
                     fontsize=9, color=headline_color, loc="left", fontweight="bold", pad=6)
        ax.grid(axis="y", alpha=0.3)

    _panel(ax0, split_rows,    "70/30 split",            "14% MAE gain", GREY)
    _panel(ax1, orig_wf_rows,  "Walk-forward, orig. scaling",   "27% MAE gain", GREY)
    _panel(ax2, leak_rows,     "Walk-forward, leakage-checked", "21% MAE gain  ← primary", TEAL_DARK)

    fig.suptitle("Primary result (right): Baidu lowers MAE 21%, direction drops to 33%.  Middle panel overstates both; included only for comparison.",
                 fontsize=8.5, color=NAVY, x=0.02, ha="left", y=1.03, fontweight="bold")
    plt.tight_layout()
    _save(fig, "12_baseline_matrix.png")


# ------------------------------------------------------------------
# chart 13: Component drop-one ablation
# ------------------------------------------------------------------
def chart_ablation():
    ab = pd.read_csv(PROC / "ablation_dropone.csv")
    # order: FULL first, then C1..C4
    labels = ["FULL"] + [v.replace("DROP ", "") for v in ab["variant"].iloc[1:]]
    short = ["FULL", "no C1\nNEV pen.", "no C2\nICE decl.", "no C3\nBEV share", "no C4\nmainstream"]
    mae_imp = ab["mae_improvement_pct"].tolist()
    dir_b = (ab["dir_baidu"] * 100).tolist()
    dir_p = (ab["dir_persist"] * 100).tolist()

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(10, 3.0))

    # Panel 0: MAE improvement vs persistence
    colors = [TEAL] + [AMBER if v < mae_imp[0] else TEAL_DARK for v in mae_imp[1:]]
    bars = ax0.bar(short, mae_imp, color=colors, width=0.65)
    for b, v in zip(bars, mae_imp):
        ax0.text(b.get_x() + b.get_width()/2, v + 0.8, f"{v:.1f}%",
                 ha="center", fontsize=9, color=NAVY, fontweight="bold")
    ax0.axhline(mae_imp[0], color=GREY_LIGHT, linewidth=0.8, linestyle="--")
    ax0.set_ylim(0, max(mae_imp) * 1.25)
    ax0.set_ylabel("MAE improvement vs persistence (%)", color=GREY, fontsize=8.5)
    ax0.set_title("Drop-one impact on Baidu MAE gain", fontsize=10, color=NAVY, loc="left", fontweight="bold")
    ax0.grid(axis="y", alpha=0.3)

    # Panel 1: direction accuracy, Baidu vs persistence
    x = np.arange(len(short))
    w = 0.4
    ax1.bar(x - w/2, dir_p, w, color=GREY_LIGHT, label="Persistence")
    ax1.bar(x + w/2, dir_b, w, color=TEAL, label="Baidu")
    for xi, v in zip(x - w/2, dir_p):
        ax1.text(xi, v + 1.5, f"{v:.0f}%", ha="center", fontsize=7.5, color=NAVY)
    for xi, v in zip(x + w/2, dir_b):
        ax1.text(xi, v + 1.5, f"{v:.0f}%", ha="center", fontsize=7.5, color=NAVY)
    ax1.set_xticks(x); ax1.set_xticklabels(short, fontsize=8)
    ax1.set_ylim(0, 100)
    ax1.set_ylabel("Direction accuracy (%)", color=GREY, fontsize=8.5)
    ax1.set_title("Direction accuracy under each variant", fontsize=10, color=NAVY, loc="left", fontweight="bold")
    ax1.legend(frameon=False, fontsize=8, loc="lower right")
    ax1.grid(axis="y", alpha=0.3)

    fig.suptitle("Dropping C3 or C4 raises MAE gain, dropping C4 also raises direction accuracy.\n"
                 "C1 (NEV penetration) and C2 (ICE decline) carry the predictable signal.",
                 fontsize=9.5, color=GREY, x=0.02, ha="left", y=1.03)
    plt.tight_layout()
    _save(fig, "13_ablation.png")


if __name__ == "__main__":
    chart_transition_index()
    chart_channel_vs_index()
    chart_leadlag()
    chart_brand_growth()
    chart_baseline()
    chart_data_coverage_v2()
    chart_baidu_vs_index()
    chart_baidu_baseline()
    chart_stl()
    chart_walkforward()
    chart_methodology_summary()
    chart_baseline_matrix()
    chart_ablation()
