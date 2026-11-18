"""
ChargeAhead: baseline evaluation of the Transition Index.

What the course asks for a baseline:
  - a simple persistence model (next value = this value) that any index must beat
  - standard error metrics (MAE, MAPE) plus directional accuracy

What is being evaluated:
  - the one-month-ahead change in the Transition Index
  - comparison targets:
      (A) persistence baseline     \hat{dIdx_t} = dIdx_{t-1}
      (B) channel-signal model     \hat{dIdx_t} = alpha + beta * channel_signal_{t-1}
      (C) seasonal naive baseline  \hat{dIdx_t} = dIdx_{t-12}

Note: Baidu Search Index data has not been collected yet, so attention-based signals
      are deliberately left out of this stage. They will enter next.
"""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"


def _safe_mape(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = np.abs(y_true) > 1e-6
    if mask.sum() == 0:
        return np.nan
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def _direction_hit(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = (np.abs(y_true) > 1e-6) & (np.abs(y_pred) > 1e-6)
    if mask.sum() == 0:
        return np.nan
    return float((np.sign(y_true[mask]) == np.sign(y_pred[mask])).mean())


def _metrics(name, y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    yt, yp = y_true[mask], y_pred[mask]
    if len(yt) < 3:
        return {"model": name, "n": len(yt), "mae": np.nan, "mape": np.nan,
                "direction_accuracy": np.nan}
    mae = float(np.mean(np.abs(yt - yp)))
    mape = _safe_mape(yt, yp)
    dir_acc = _direction_hit(yt, yp)
    return {"model": name, "n": int(mask.sum()), "mae": mae, "mape": mape,
            "direction_accuracy": dir_acc}


def main():
    idx = pd.read_csv(PROC / "transition_index.csv", parse_dates=["month"])
    panel = pd.read_csv(PROC / "national_panel.csv", parse_dates=["month"])
    df = idx.merge(panel[["month", "inventory_ratio", "channel_gap_wan"]], on="month")
    df = df.sort_values("month").reset_index(drop=True)
    df["dIdx"] = df["transition_index"].diff()

    # Models (one-step-ahead forecast of dIdx)
    df["pred_persist"] = df["dIdx"].shift(1)             # yesterday's change
    df["pred_season"] = df["dIdx"].shift(12)             # same month last year

    # simple univariate linear fit on inventory_ratio_{t-1}
    reg_df = df[["dIdx", "inventory_ratio"]].copy()
    reg_df["x"] = reg_df["inventory_ratio"].shift(1)
    train = reg_df.dropna().iloc[: int(len(reg_df.dropna()) * 0.7)]
    if len(train) >= 10:
        X = train["x"].values
        y = train["dIdx"].values
        beta = np.polyfit(X, y, 1)
        df["pred_invratio"] = beta[0] * df["inventory_ratio"].shift(1) + beta[1]
    else:
        df["pred_invratio"] = np.nan

    # evaluation window: use the LAST 12 months with data (ongoing validation window)
    eval_df = df.dropna(subset=["dIdx"]).tail(12)

    out = pd.DataFrame([
        _metrics("Persistence (naive)", eval_df["dIdx"], eval_df["pred_persist"]),
        _metrics("Seasonal naive (lag 12)", eval_df["dIdx"], eval_df["pred_season"]),
        _metrics("Channel inventory ratio (lag 1)", eval_df["dIdx"], eval_df["pred_invratio"]),
    ])
    out.to_csv(PROC / "baseline_metrics.csv", index=False)
    print(out.to_string(index=False))

    # Diagnostic: direction accuracy of the Transition Index itself as a classifier for
    # whether NEV penetration will go up next month.
    pen = panel.set_index("month")["nev_penetration"].sort_index()
    pen_up = (pen.diff().shift(-1) > 0).astype(int)
    idx_up = (idx.set_index("month")["transition_index"].diff() > 0).astype(int)
    aligned = pd.concat([idx_up.rename("idx_up"), pen_up.rename("pen_up")], axis=1).dropna()
    agree = float((aligned["idx_up"] == aligned["pen_up"]).mean()) if len(aligned) > 0 else np.nan
    print(f"\nTransition index up this month agrees with NEV penetration up next month: {agree:.1%} ({len(aligned)} obs)")


if __name__ == "__main__":
    main()
