"""
ChargeAhead: lead-lag analysis of the channel inventory signal vs the Transition Index.

Hypothesis
----------
Wholesale running above retail (positive channel gap) means dealers are absorbing more cars
than consumers are buying. If OEMs push BEV / NEV stock onto dealers ahead of a demand shift,
the channel gap and the inventory ratio could lead changes in the Transition Index.

Method
------
For each candidate lag k in [-6, +6] months, compute Pearson correlation between
  channel_signal_t   and   transition_index_{t+k}
Positive k means the signal LEADS the index by k months.
"""

from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"


def xcorr(series_a: pd.Series, series_b: pd.Series, max_lag: int = 6) -> pd.DataFrame:
    """series_a (candidate leading signal) vs series_b (target, e.g. transition index)."""
    out = []
    for k in range(-max_lag, max_lag + 1):
        shifted = series_b.shift(-k)
        aligned = pd.concat([series_a, shifted], axis=1).dropna()
        n = len(aligned)
        if n < 6:
            out.append({"lag": k, "n": n, "corr": np.nan})
            continue
        c = aligned.corr().iloc[0, 1]
        out.append({"lag": k, "n": n, "corr": c})
    return pd.DataFrame(out)


def main():
    panel = pd.read_csv(PROC / "national_panel.csv", parse_dates=["month"])
    idx = pd.read_csv(PROC / "transition_index.csv", parse_dates=["month"])
    df = idx.merge(panel[["month", "channel_gap_wan", "inventory_ratio"]], on="month")
    df = df.sort_values("month").reset_index(drop=True)

    # First-difference both to focus on co-movement rather than shared trend
    df["dIdx"] = df["transition_index"].diff()
    df["dChan"] = df["channel_gap_wan"].diff()
    df["dRatio"] = df["inventory_ratio"].diff()

    pairs = {
        "channel_gap_vs_index_level": xcorr(df["channel_gap_wan"], df["transition_index"]),
        "channel_gap_vs_dIndex": xcorr(df["channel_gap_wan"], df["dIdx"]),
        "dChannel_vs_dIndex": xcorr(df["dChan"], df["dIdx"]),
        "ratio_vs_index_level": xcorr(df["inventory_ratio"], df["transition_index"]),
    }

    for name, dfp in pairs.items():
        dfp.to_csv(PROC / f"leadlag_{name}.csv", index=False)
        print(f"\n== {name} ==")
        print(dfp.to_string(index=False))

    # headline table
    headline = pd.DataFrame({
        "pair": list(pairs.keys()),
        "best_lag": [p.loc[p["corr"].abs().idxmax(), "lag"] if p["corr"].notna().any() else np.nan
                      for p in pairs.values()],
        "corr_at_best_lag": [p.loc[p["corr"].abs().idxmax(), "corr"] if p["corr"].notna().any() else np.nan
                              for p in pairs.values()],
        "n_at_best_lag": [p.loc[p["corr"].abs().idxmax(), "n"] if p["corr"].notna().any() else np.nan
                           for p in pairs.values()],
    })
    headline.to_csv(PROC / "leadlag_headline.csv", index=False)
    print("\n== HEADLINE ==")
    print(headline.to_string(index=False))


if __name__ == "__main__":
    main()
