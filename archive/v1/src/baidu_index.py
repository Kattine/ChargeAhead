"""
ChargeAhead: Baidu Search Index integration.

Input
-----
data/raw/baidu_index_weekly.xlsx
  Columns: keyword, iso_year, iso_week, week_start, week_end,
           index_all_mean, index_all_sum, days, is_partial_week, month

Output
------
data/processed/baidu_weekly.csv            tidy weekly series
data/processed/baidu_monthly.csv           rolled up to CPCA month grain
data/processed/baidu_signals_monthly.csv   composite attention signals
data/processed/leadlag_baidu_*.csv         lead-lag vs transition index
data/processed/baidu_vs_baseline.csv       Baidu-as-feature baseline

Signals constructed
-------------------
  attention_powertrain_bev     mean of (纯电车)  — low volume, used as sanity only
  attention_powertrain_phev    mean of (插电式混合动力车, 混动车)
  attention_powertrain_erev    EREV category queries + top EREV models
  attention_powertrain_nev     新能源汽车 + 新能源车  (high volume, reliable)
  attention_brand_bev_pure     mean across pure-BEV brands
  attention_brand_erev_lead    理想 + 问界 + 鸿蒙智行 (EREV leaders)
  attention_brand_phev_lead    比亚迪 (dominant PHEV brand)
  attention_model_top          mean of top models
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------
# keyword taxonomy
# ------------------------------------------------------------------
POWERTRAIN_BEV = ["纯电车"]
POWERTRAIN_PHEV = ["插电式混合动力车", "混动车"]
POWERTRAIN_EREV = ["增程式混动和插电式混动的区别", "增程式电动车是什么意思"]
POWERTRAIN_NEV_OVERALL = ["新能源汽车", "新能源车"]
POWERTRAIN_ICE = ["燃油车"]

# Pure-BEV brands (BYD excluded because it is PHEV-dominated)
BRAND_BEV_PURE = ["特斯拉", "小米汽车", "小鹏", "蔚来", "极氪", "埃安"]
BRAND_EREV_LEAD = ["理想", "问界", "鸿蒙智行"]
BRAND_PHEV_LEAD = ["比亚迪"]
BRAND_MIXED = ["零跑", "吉利", "奇瑞", "吉利银河", "深蓝", "阿维塔", "领克"]

MODEL_TOP = [
    "model y", "model 3", "比亚迪宋", "比亚迪海豚", "比亚迪秦plus",
    "海鸥", "小米su7", "理想l6", "理想l7", "理想l9",
    "问界m7", "问界m9", "零跑c10", "零跑c11", "小鹏mona m03",
    "吉利星愿", "元up",
]


# ------------------------------------------------------------------
# load + reshape
# ------------------------------------------------------------------
def load_weekly(path=RAW / "baidu_index_weekly.xlsx"):
    df = pd.read_excel(path)
    df.columns = [c.strip() for c in df.columns]
    df["keyword"] = df["keyword"].str.lower().str.strip()
    df["week_start"] = pd.to_datetime(df["week_start"])
    df["week_end"] = pd.to_datetime(df["week_end"])
    df["month"] = pd.to_datetime(df["month"])
    return df


def monthly_rollup(weekly: pd.DataFrame) -> pd.DataFrame:
    """Roll weekly series up to months using the `month` attribution column.
    Uses mean intensity (not sum) so months with different week counts stay comparable."""
    g = (weekly
         .groupby(["keyword", "month"])
         .agg(index_mean=("index_all_mean", "mean"),
              n_weeks=("iso_week", "count"))
         .reset_index())
    # Pivot: one column per keyword
    wide = g.pivot(index="month", columns="keyword", values="index_mean").sort_index()
    return wide


# ------------------------------------------------------------------
# composite signals
# ------------------------------------------------------------------
def _safe_mean(df: pd.DataFrame, cols: list) -> pd.Series:
    present = [c for c in cols if c in df.columns]
    if not present:
        return pd.Series(np.nan, index=df.index)
    return df[present].mean(axis=1, skipna=True)


def build_signals(monthly: pd.DataFrame) -> pd.DataFrame:
    sig = pd.DataFrame(index=monthly.index)

    sig["att_pw_bev_cat"] = _safe_mean(monthly, [k.lower() for k in POWERTRAIN_BEV])
    sig["att_pw_phev_cat"] = _safe_mean(monthly, [k.lower() for k in POWERTRAIN_PHEV])
    sig["att_pw_erev_cat"] = _safe_mean(monthly, [k.lower() for k in POWERTRAIN_EREV])
    sig["att_pw_ice_cat"] = _safe_mean(monthly, [k.lower() for k in POWERTRAIN_ICE])
    sig["att_nev_overall"] = _safe_mean(monthly, [k.lower() for k in POWERTRAIN_NEV_OVERALL])

    sig["att_brand_bev_pure"] = _safe_mean(monthly, [k.lower() for k in BRAND_BEV_PURE])
    sig["att_brand_erev_lead"] = _safe_mean(monthly, [k.lower() for k in BRAND_EREV_LEAD])
    sig["att_brand_phev_lead"] = _safe_mean(monthly, [k.lower() for k in BRAND_PHEV_LEAD])

    sig["att_model_top"] = _safe_mean(monthly, [k.lower() for k in MODEL_TOP])

    # Combined BEV-lean attention (brand level is stronger than category)
    sig["att_bev_combined"] = _safe_mean(monthly, [k.lower() for k in BRAND_BEV_PURE + MODEL_TOP[:6]])

    return sig.reset_index()


# ------------------------------------------------------------------
# lead-lag vs Transition Index
# ------------------------------------------------------------------
def xcorr(a: pd.Series, b: pd.Series, max_lag=6) -> pd.DataFrame:
    out = []
    for k in range(-max_lag, max_lag + 1):
        shifted = b.shift(-k)
        aligned = pd.concat([a, shifted], axis=1).dropna()
        n = len(aligned)
        if n < 6:
            out.append({"lag": k, "n": n, "corr": np.nan})
            continue
        c = aligned.corr().iloc[0, 1]
        out.append({"lag": k, "n": n, "corr": c})
    return pd.DataFrame(out)


def run_leadlag(signals: pd.DataFrame, idx: pd.DataFrame) -> dict:
    merged = signals.merge(idx[["month", "transition_index"]], on="month")
    merged = merged.sort_values("month").reset_index(drop=True)
    target = merged["transition_index"]

    results = {}
    for col in ["att_nev_overall", "att_brand_bev_pure", "att_brand_erev_lead",
                "att_brand_phev_lead", "att_model_top", "att_pw_erev_cat",
                "att_pw_bev_cat", "att_pw_phev_cat", "att_pw_ice_cat"]:
        results[col] = xcorr(merged[col], target)
    return results


# ------------------------------------------------------------------
# Baidu as feature in baseline
# ------------------------------------------------------------------
def baidu_baseline(idx: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
    """Evaluate Baidu attention as a predictor of one-step change in Transition Index."""
    df = idx[["month", "transition_index"]].merge(signals, on="month").sort_values("month").reset_index(drop=True)
    df["dIdx"] = df["transition_index"].diff()

    # Candidate features
    features = ["att_nev_overall", "att_brand_bev_pure", "att_brand_erev_lead", "att_model_top"]
    for f in features:
        df[f"d_{f}"] = df[f].diff()

    # Simple regression: dIdx ~ change in attention (lag 1)
    results = []
    for f in features:
        x = df[f"d_{f}"].shift(1).values
        y = df["dIdx"].values
        mask = ~(np.isnan(x) | np.isnan(y))
        if mask.sum() < 10:
            continue
        xt, yt = x[mask], y[mask]
        # fit on first 70%
        n_train = int(len(xt) * 0.7)
        if n_train < 8:
            continue
        beta = np.polyfit(xt[:n_train], yt[:n_train], 1)
        y_pred = beta[0] * xt + beta[1]
        # eval on last 30%
        test_mae = float(np.mean(np.abs(yt[n_train:] - y_pred[n_train:])))
        test_dir = float((np.sign(yt[n_train:]) == np.sign(y_pred[n_train:])).mean())
        results.append({"feature": f, "slope": float(beta[0]), "intercept": float(beta[1]),
                        "n_train": n_train, "n_test": len(xt) - n_train,
                        "test_mae": test_mae, "test_direction_acc": test_dir})

    # Benchmark: persistence
    y = df["dIdx"].values
    yp = df["dIdx"].shift(1).values
    mask = ~(np.isnan(y) | np.isnan(yp))
    yt, yt_p = y[mask], yp[mask]
    n_train = int(len(yt) * 0.7)
    pers_mae = float(np.mean(np.abs(yt[n_train:] - yt_p[n_train:])))
    pers_dir = float((np.sign(yt[n_train:]) == np.sign(yt_p[n_train:])).mean())
    results.append({"feature": "PERSISTENCE_BASELINE", "slope": None, "intercept": None,
                    "n_train": n_train, "n_test": len(yt) - n_train,
                    "test_mae": pers_mae, "test_direction_acc": pers_dir})

    return pd.DataFrame(results)


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------
def main():
    weekly = load_weekly()
    weekly.to_csv(PROC / "baidu_weekly.csv", index=False)
    print(f"Weekly: {weekly.shape}, {weekly['keyword'].nunique()} keywords, "
          f"{weekly['week_start'].min().date()} to {weekly['week_end'].max().date()}")

    monthly = monthly_rollup(weekly)
    monthly.to_csv(PROC / "baidu_monthly.csv")
    print(f"Monthly wide: {monthly.shape}")

    sigs = build_signals(monthly)
    sigs.to_csv(PROC / "baidu_signals_monthly.csv", index=False)
    print(f"Signals: {sigs.shape}")
    print(sigs.set_index("month").describe().round(0).T[["mean", "min", "max"]].to_string())

    idx = pd.read_csv(PROC / "transition_index.csv", parse_dates=["month"])
    results = run_leadlag(sigs, idx)
    headline = []
    for name, df in results.items():
        df.to_csv(PROC / f"leadlag_baidu_{name}.csv", index=False)
        if df["corr"].notna().any():
            best_idx = df["corr"].abs().idxmax()
            headline.append({
                "signal": name,
                "best_lag": int(df.loc[best_idx, "lag"]),
                "corr_at_best_lag": float(df.loc[best_idx, "corr"]),
                "n_at_best_lag": int(df.loc[best_idx, "n"]),
            })
    pd.DataFrame(headline).to_csv(PROC / "leadlag_baidu_headline.csv", index=False)
    print("\n=== Baidu lead-lag headline ===")
    print(pd.DataFrame(headline).to_string(index=False))

    bb = baidu_baseline(idx, sigs)
    bb.to_csv(PROC / "baidu_vs_baseline.csv", index=False)
    print("\n=== Baidu as feature vs persistence baseline (one-step dIndex) ===")
    print(bb.to_string(index=False))


if __name__ == "__main__":
    main()
