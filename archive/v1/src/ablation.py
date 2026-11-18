"""
ChargeAhead: ablation checks for the mid-semester review.

Answers the two questions reviewers flagged:

  Q1 "Is any one component dominating the Transition Index?"
     Drop-one ablation. For each of C1..C4, rebuild the index without
     that component, then re-run the Baidu walk-forward to see whether
     the predictive gain survives.

  Q2 "Does the full-window min-max normalization sneak future info
      into the historical index?"
     Expanding-window min-max. Recompute each component at every
     month using ONLY data available up to that month, then measure
     how far this leakage-free index drifts from the full-window one.

Writes
------
data/processed/ablation_dropone.csv       drop-one component results
data/processed/ablation_expanding_mm.csv  expanding-window index series
data/processed/ablation_expanding_summary.csv  gap stats vs full-window index
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"


COMPONENTS = {
    "C1_nev_penetration": "c1_nev_penetration",
    "C2_ice_decline":     "c2_ice_decline",
    "C3_bev_share_nev":   "c3_bev_share_nev",
    "C4_bev_a0_plus_a":   "c4_bev_a0_plus_a",
}


def _minmax(s: pd.Series) -> pd.Series:
    lo, hi = s.min(skipna=True), s.max(skipna=True)
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(np.nan, index=s.index)
    return (s - lo) / (hi - lo)


def _build_index(df: pd.DataFrame, use_cols: list[str]) -> pd.Series:
    norm = pd.DataFrame({c: _minmax(df[c]) for c in use_cols})
    return norm.mean(axis=1, skipna=True)


def _walkforward_mae(idx: pd.Series, baidu: pd.DataFrame) -> dict:
    """Mimic methodology.walkforward on an arbitrary index series.
    Returns persistence vs Baidu MAE, direction accuracy, and MASE."""
    df = pd.DataFrame({"month": idx.index, "transition_index": idx.values})
    df = df.merge(baidu[["month", "att_nev_overall"]], on="month").sort_values("month").reset_index(drop=True)
    df["dIdx"] = df["transition_index"].diff()
    df["d_att_nev"] = df["att_nev_overall"].diff()
    df = df.dropna(subset=["dIdx"]).reset_index(drop=True)

    MIN_TRAIN = 24
    out = []
    for t in range(MIN_TRAIN, len(df)):
        train = df.iloc[:t]
        x_train = train["d_att_nev"].shift(1).values
        y_train = train["dIdx"].values
        mask = ~(np.isnan(x_train) | np.isnan(y_train))
        if mask.sum() < 10:
            continue
        beta = np.polyfit(x_train[mask], y_train[mask], 1)
        x_known = df.iloc[t - 1]["d_att_nev"]
        if np.isnan(x_known):
            x_known = 0
        yhat = beta[0] * x_known + beta[1]
        y_persist = df.iloc[t - 1]["dIdx"]
        y_true = df.iloc[t]["dIdx"]
        out.append({"y_true": y_true, "y_hat_b": yhat, "y_hat_p": y_persist})
    wf = pd.DataFrame(out)
    if len(wf) == 0:
        return {"n": 0, "mae_persist": np.nan, "mae_baidu": np.nan,
                "dir_persist": np.nan, "dir_baidu": np.nan, "mase": np.nan}
    mae_p = (wf["y_hat_p"] - wf["y_true"]).abs().mean()
    mae_b = (wf["y_hat_b"] - wf["y_true"]).abs().mean()
    dir_p = (np.sign(wf["y_hat_p"]) == np.sign(wf["y_true"])).mean()
    dir_b = (np.sign(wf["y_hat_b"]) == np.sign(wf["y_true"])).mean()
    return {"n": len(wf), "mae_persist": float(mae_p), "mae_baidu": float(mae_b),
            "dir_persist": float(dir_p), "dir_baidu": float(dir_b),
            "mase": float(mae_b / mae_p) if mae_p > 0 else np.nan}


# ------------------------------------------------------------------
# Q1  Drop-one ablation
# ------------------------------------------------------------------
def drop_one_ablation():
    idx_full = pd.read_csv(PROC / "transition_index.csv", parse_dates=["month"])
    baidu = pd.read_csv(PROC / "baidu_signals_monthly.csv", parse_dates=["month"])
    all_cols = list(COMPONENTS.values())

    # baseline: all four components
    full = _build_index(idx_full.set_index("month"), all_cols)
    base = _walkforward_mae(full, baidu)
    rows = [{"variant": "FULL (all 4 components)", "dropped": "none", **base}]

    # drop-one variants
    for name, col in COMPONENTS.items():
        use = [c for c in all_cols if c != col]
        idx_var = _build_index(idx_full.set_index("month"), use)
        m = _walkforward_mae(idx_var, baidu)
        rows.append({"variant": f"DROP {name}", "dropped": name, **m})

    df = pd.DataFrame(rows)
    df["mae_improvement_pct"] = (1 - df["mae_baidu"] / df["mae_persist"]) * 100
    df = df.round(4)
    df.to_csv(PROC / "ablation_dropone.csv", index=False)
    print("\n=== Drop-one ablation (Baidu NEV walk-forward on each index variant) ===")
    print(df.to_string(index=False))
    return df


# ------------------------------------------------------------------
# Q2  Expanding-window min-max (no look-ahead)
# ------------------------------------------------------------------
def expanding_minmax():
    """At each month t, normalize each component using only data from months <= t.
    This removes look-ahead from the index itself (training-time view only).
    Compare the resulting series with the full-window index."""
    idx_full = pd.read_csv(PROC / "transition_index.csv", parse_dates=["month"]).sort_values("month").reset_index(drop=True)
    cols = list(COMPONENTS.values())

    out = {"month": [], "transition_index_full": [], "transition_index_expanding": []}
    for t in range(len(idx_full)):
        sub = idx_full.iloc[: t + 1]
        norm_at_t = {}
        for c in cols:
            s = sub[c]
            lo, hi = s.min(skipna=True), s.max(skipna=True)
            if pd.isna(lo) or pd.isna(hi) or hi == lo or pd.isna(sub.iloc[-1][c]):
                norm_at_t[c] = np.nan
            else:
                norm_at_t[c] = (sub.iloc[-1][c] - lo) / (hi - lo)
        vals = [v for v in norm_at_t.values() if not pd.isna(v)]
        exp_idx = float(np.mean(vals)) if vals else np.nan
        out["month"].append(idx_full.iloc[t]["month"])
        out["transition_index_full"].append(float(idx_full.iloc[t]["transition_index"]))
        out["transition_index_expanding"].append(exp_idx)

    exp_df = pd.DataFrame(out)
    exp_df["gap"] = exp_df["transition_index_expanding"] - exp_df["transition_index_full"]
    exp_df.to_csv(PROC / "ablation_expanding_mm.csv", index=False)

    summary = pd.DataFrame([{
        "mean_abs_gap":  float(exp_df["gap"].abs().mean()),
        "max_abs_gap":   float(exp_df["gap"].abs().max()),
        "max_gap_month": str(exp_df.loc[exp_df["gap"].abs().idxmax(), "month"].date()),
        "corr_full_vs_expanding": float(exp_df[["transition_index_full", "transition_index_expanding"]].corr().iloc[0, 1]),
        "note": "Expanding-window min-max removes look-ahead; small gap = leakage was limited",
    }])
    summary.to_csv(PROC / "ablation_expanding_summary.csv", index=False)
    print("\n=== Expanding-window min-max (no look-ahead) vs full-window index ===")
    print(summary.to_string(index=False))

    # Also, run the walk-forward on the expanding-window index to see whether the
    # 27% MAE gain survives when the index itself is leakage-free.
    baidu = pd.read_csv(PROC / "baidu_signals_monthly.csv", parse_dates=["month"])
    exp_series = exp_df.set_index("month")["transition_index_expanding"]
    exp_result = _walkforward_mae(exp_series, baidu)
    exp_full_result = _walkforward_mae(exp_df.set_index("month")["transition_index_full"], baidu)
    cmp_df = pd.DataFrame([
        {"index_variant": "Full-window min-max (current)", **exp_full_result},
        {"index_variant": "Expanding-window min-max (no look-ahead)", **exp_result},
    ]).round(4)
    cmp_df["mae_improvement_pct"] = (1 - cmp_df["mae_baidu"] / cmp_df["mae_persist"]) * 100
    cmp_df.to_csv(PROC / "ablation_expanding_walkforward.csv", index=False)
    print("\n=== Baidu walk-forward on both index variants ===")
    print(cmp_df.to_string(index=False))

    return exp_df, summary, cmp_df


def main():
    drop_one_ablation()
    expanding_minmax()


if __name__ == "__main__":
    main()
