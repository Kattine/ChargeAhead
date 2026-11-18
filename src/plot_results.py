"""Standalone evidence charts, reproducible with python -m src.plot_results."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"data/processed";O=ROOT/"outputs/figures"
NAVY="#112A35";TEAL="#087F8C";ORANGE="#C46A3D";GREY="#8EA4AA"

def finish(fig,name):
    fig.tight_layout()
    fig.savefig(O/f"{name}.png",dpi=180,bbox_inches="tight")
    fig.savefig(O/f"{name}.svg",bbox_inches="tight")
    plt.close(fig)

def main():
    O.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,"axes.spines.top":False,"axes.spines.right":False})
    p=pd.read_csv(P/"national_panel_v2.csv",parse_dates=["month"])
    fig,ax=plt.subplots(figsize=(10,4.8));ax.plot(p.month,p.nev_share*100,color=TEAL,lw=2.5)
    ax.set(title="NEV retail share in supplied market extracts",ylabel="Share of passenger-car retail (%)",ylim=(0,75));ax.grid(axis="y",alpha=.18)
    finish(fig,"01_nev_share")
    m=pd.read_csv(P/"forecast_metrics.csv").sort_values("mae_pp")
    fig,ax=plt.subplots(figsize=(10,5.5));colors=[TEAL if x=="History + search" else GREY for x in m.model]
    bars=ax.barh(m.model,m.mae_pp,color=colors);ax.invert_yaxis();ax.bar_label(bars,fmt="%.2f",padding=5)
    ax.set(title="Same 18 test months: March 2025-August 2026",xlabel="Mean absolute error (percentage points); lower is better",xlim=(0,5.2))
    finish(fig,"02_matched_baselines")
    g=pd.read_csv(P/"brand_group_summary.csv");x=range(len(g))
    fig,ax=plt.subplots(figsize=(10,5));ax.bar([v-.18 for v in x],g["mean"]*100,.36,label="Mean",color=GREY);ax.bar([v+.18 for v in x],g["median"]*100,.36,label="Median",color=TEAL)
    ax.set_xticks(list(x),[f"{r.profile}\n(n={r.n})" for r in g.itertuples()]);ax.axhline(0,color=NAVY,lw=.8);ax.legend(frameon=False)
    ax.set(title="Brand growth is sensitive to the summary statistic",ylabel="March-August 2026 growth (%)")
    finish(fig,"03_brand_mean_median")
    f=pd.read_csv(P/"forecast_predictions.csv",parse_dates=["month"])
    fig,ax=plt.subplots(figsize=(10,4.8))
    actual=f.drop_duplicates("month");ax.plot(actual.month,actual.actual_change_pp,label="Actual",color=NAVY,lw=2)
    for name,color in [("History only (AR1)",GREY),("History + search",TEAL)]:
        q=f[f.model==name];ax.plot(q.month,q.predicted_change_pp,label=name,color=color,lw=1.8)
    ax.axhline(0,color="#CCCCCC",lw=.8);ax.legend(frameon=False);ax.set(title="Forecasts miss large monthly moves",ylabel="NEV share change (percentage points)")
    finish(fig,"04_monthly_predictions")

if __name__=="__main__":main()
