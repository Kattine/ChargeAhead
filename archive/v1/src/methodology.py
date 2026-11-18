"""
ChargeAhead: Lec 6 / Lec 7 methodology upgrades for the mid-semester review.

Adds to the pipeline:
  1. STL decomposition of the Transition Index (trend / seasonal / residual)
  2. ADF stationarity test on the index and its first difference
  3. Walk-forward backtest with expanding window, retrain every month
  4. Information Coefficient (IC) of Baidu attention vs next-month dIndex
  5. Regime verdict mini-table (PASS / FAIL per sub-period)
  6. MASE scoring vs persistence (formal "beat the dumbest baseline")

Writes
------
data/processed/stl_components.csv
data/processed/adf_tests.csv
data/processed/walkforward_metrics.csv
data/processed/ic_rolling.csv
data/processed/regime_verdict.csv
data/processed/mase_scores.csv
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------
# 1. STL decomposition
# ------------------------------------------------------------------
def stl_decompose():
    from statsmodels.tsa.seasonal import STL
    idx = pd.read_csv(PROC / "transition_index.csv", parse_dates=["month"]).set_index("month")
    y = idx["transition_index"].dropna()
    stl = STL(y, period=12, robust=True)
    res = stl.fit()
    out = pd.DataFrame({
        "month": y.index,
        "observed": y.values,
        "trend": res.trend.values,
        "seasonal": res.seasonal.values,
        "resid": res.resid.values,
    })
    out.to_csv(PROC / "stl_components.csv", index=False)
    print(f"STL: observed std {out['observed'].std():.3f}, "
          f"trend std {out['trend'].std():.3f}, "
          f"seasonal std {out['seasonal'].std():.3f}, "
          f"residual std {out['resid'].std():.3f}")
    return out


# ------------------------------------------------------------------
# 2. ADF stationarity test
# ------------------------------------------------------------------
def adf_tests():
    from statsmodels.tsa.stattools import adfuller
    idx = pd.read_csv(PROC / "transition_index.csv", parse_dates=["month"]).set_index("month")
    y = idx["transition_index"].dropna()
    dy = y.diff().dropna()

    def _adf(series, label):
        r = adfuller(series, autolag="AIC")
        return {"series": label, "adf_stat": r[0], "p_value": r[1],
                "lags": r[2], "n": r[3],
                "crit_1pct": r[4]["1%"], "crit_5pct": r[4]["5%"],
                "stationary_5pct": bool(r[1] < 0.05)}

    rows = [_adf(y, "transition_index (level)"),
            _adf(dy, "transition_index (first diff)")]
    df = pd.DataFrame(rows)
    df.to_csv(PROC / "adf_tests.csv", index=False)
    print("\n=== ADF tests ===")
    print(df.to_string(index=False))
    return df


# ------------------------------------------------------------------
# 3. Walk-forward backtest
# ------------------------------------------------------------------
def walkforward():
    """Expanding window, refit linear regression each month, forecast next-month dIndex."""
    idx = pd.read_csv(PROC / "transition_index.csv", parse_dates=["month"])
    sigs = pd.read_csv(PROC / "baidu_signals_monthly.csv", parse_dates=["month"])
    df = idx[["month", "transition_index"]].merge(sigs, on="month").sort_values("month").reset_index(drop=True)
    df["dIdx"] = df["transition_index"].diff()
    df["d_att_nev"] = df["att_nev_overall"].diff()
    df["d_att_model"] = df["att_model_top"].diff()
    df = df.dropna(subset=["dIdx"]).reset_index(drop=True)

    MIN_TRAIN = 24  # need at least 24 months before first forecast
    out = []
    for t in range(MIN_TRAIN, len(df)):
        # Training window: t-24 .. t-1  (expanding from MIN_TRAIN onward)
        train = df.iloc[:t]
        x_train = train["d_att_nev"].shift(1).values
        y_train = train["dIdx"].values
        mask = ~(np.isnan(x_train) | np.isnan(y_train))
        if mask.sum() < 10:
            continue
        beta = np.polyfit(x_train[mask], y_train[mask], 1)

        # Forecast for period t using info available at t-1
        x_now = df.iloc[t]["d_att_nev"] if not np.isnan(df.iloc[t]["d_att_nev"]) else 0
        # Use the lagged value properly: at time t we have d_att_nev_{t-1} as the known signal
        x_known = df.iloc[t - 1]["d_att_nev"]
        if np.isnan(x_known):
            x_known = 0
        yhat = beta[0] * x_known + beta[1]

        # Persistence prediction: yesterday's dIdx
        y_persist = df.iloc[t - 1]["dIdx"]

        y_true = df.iloc[t]["dIdx"]
        out.append({
            "month": df.iloc[t]["month"],
            "y_true": float(y_true),
            "y_hat_baidu": float(yhat),
            "y_hat_persist": float(y_persist),
            "train_size": int(mask.sum()),
        })

    wf = pd.DataFrame(out)
    wf["err_baidu"] = wf["y_hat_baidu"] - wf["y_true"]
    wf["err_persist"] = wf["y_hat_persist"] - wf["y_true"]
    wf["abs_err_baidu"] = wf["err_baidu"].abs()
    wf["abs_err_persist"] = wf["err_persist"].abs()
    wf["dir_hit_baidu"] = (np.sign(wf["y_hat_baidu"]) == np.sign(wf["y_true"])).astype(int)
    wf["dir_hit_persist"] = (np.sign(wf["y_hat_persist"]) == np.sign(wf["y_true"])).astype(int)
    wf.to_csv(PROC / "walkforward_metrics.csv", index=False)

    summary = pd.DataFrame({
        "model": ["Persistence", "Baidu NEV attention (walk-forward)"],
        "mae": [wf["abs_err_persist"].mean(), wf["abs_err_baidu"].mean()],
        "direction_accuracy": [wf["dir_hit_persist"].mean(), wf["dir_hit_baidu"].mean()],
        "n_forecasts": [len(wf), len(wf)],
    })
    summary.to_csv(PROC / "walkforward_summary.csv", index=False)
    print("\n=== Walk-forward (expanding window, retrain monthly) ===")
    print(summary.to_string(index=False))

    # MASE: scale by persistence MAE
    mase_baidu = wf["abs_err_baidu"].mean() / wf["abs_err_persist"].mean()
    mase_df = pd.DataFrame([
        {"model": "Persistence (reference)", "MASE": 1.0,
         "interpretation": "baseline, equals naive by definition"},
        {"model": "Baidu NEV attention", "MASE": float(mase_baidu),
         "interpretation": "MASE < 1 formally beats the naive baseline" if mase_baidu < 1 else "no improvement over naive"},
    ])
    mase_df.to_csv(PROC / "mase_scores.csv", index=False)
    print("\n=== MASE ===")
    print(mase_df.to_string(index=False))

    return wf, summary, mase_df


# ------------------------------------------------------------------
# 4. Information Coefficient
# ------------------------------------------------------------------
def information_coefficient():
    """IC = Pearson correlation between the Baidu-attention signal and the next-month dIndex,
    computed on the walk-forward forecast set."""
    wf = pd.read_csv(PROC / "walkforward_metrics.csv", parse_dates=["month"])
    full_ic = float(np.corrcoef(wf["y_hat_baidu"], wf["y_true"])[0, 1])
    persist_ic = float(np.corrcoef(wf["y_hat_persist"], wf["y_true"])[0, 1])

    # Rolling 12-month IC
    wf = wf.sort_values("month").reset_index(drop=True)
    rows = []
    for i in range(11, len(wf)):
        window = wf.iloc[i - 11: i + 1]
        try:
            r = float(np.corrcoef(window["y_hat_baidu"], window["y_true"])[0, 1])
        except Exception:
            r = np.nan
        rows.append({"month": window.iloc[-1]["month"], "ic_12m": r})
    rolling = pd.DataFrame(rows)
    rolling.to_csv(PROC / "ic_rolling.csv", index=False)

    summary = pd.DataFrame([
        {"signal": "Baidu NEV attention", "ic_full_sample": full_ic,
         "ir_grinold_proxy_N20": full_ic * np.sqrt(20),
         "interpretation": "IC > 0.05 is professionally interesting; IR scales with sqrt(N) breadth"},
        {"signal": "Persistence (reference)", "ic_full_sample": persist_ic,
         "ir_grinold_proxy_N20": persist_ic * np.sqrt(20),
         "interpretation": "serial-correlation baseline"},
    ])
    summary.to_csv(PROC / "ic_summary.csv", index=False)
    print("\n=== Information Coefficient (full sample) ===")
    print(summary.to_string(index=False))
    return summary, rolling


# ------------------------------------------------------------------
# 5. Regime verdict
# ------------------------------------------------------------------
def regime_verdict():
    wf = pd.read_csv(PROC / "walkforward_metrics.csv", parse_dates=["month"])
    wf["year"] = wf["month"].dt.year
    wf["quarter"] = wf["month"].dt.to_period("Q").astype(str)

    def _pass(row_count, dir_hit_rate, mae_ratio):
        """PASS if direction >= 0.6 and MAE better than persistence."""
        if row_count < 2:
            return "N/A"
        if dir_hit_rate >= 0.6 and mae_ratio <= 1.0:
            return "PASS"
        return "FAIL"

    regimes = []
    # 2024 partial coverage, split by halves
    for label, mask in [
        ("2024-H2 (walk-forward starts)", (wf["month"] >= "2024-07-01") & (wf["month"] < "2025-01-01")),
        ("2025 full year",                (wf["month"] >= "2025-01-01") & (wf["month"] < "2026-01-01")),
        ("2026 Q1 (Spring Festival)",     (wf["month"] >= "2026-01-01") & (wf["month"] < "2026-04-01")),
        ("2026 Q2 to Aug (post-SF)",      (wf["month"] >= "2026-04-01") & (wf["month"] <= "2026-08-01")),
    ]:
        sub = wf[mask]
        n = len(sub)
        if n == 0:
            continue
        mae_b = float(sub["abs_err_baidu"].mean())
        mae_p = float(sub["abs_err_persist"].mean())
        dir_b = float(sub["dir_hit_baidu"].mean())
        dir_p = float(sub["dir_hit_persist"].mean())
        verdict = _pass(n, dir_b, mae_b / mae_p if mae_p > 0 else np.inf)
        regimes.append({
            "regime": label, "n_months": n,
            "mae_baidu": round(mae_b, 4), "mae_persist": round(mae_p, 4),
            "dir_baidu": round(dir_b, 2), "dir_persist": round(dir_p, 2),
            "verdict": verdict,
        })

    df = pd.DataFrame(regimes)
    df.to_csv(PROC / "regime_verdict.csv", index=False)
    print("\n=== Regime verdict ===")
    print(df.to_string(index=False))
    return df


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------
def main():
    stl_decompose()
    adf_tests()
    walkforward()
    information_coefficient()
    regime_verdict()


if __name__ == "__main__":
    main()
