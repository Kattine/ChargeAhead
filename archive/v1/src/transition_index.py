"""
ChargeAhead: Powertrain Transition Index.

Four transparent components, aligned to monthly CPCA data (Jan 2023 - Aug 2026):

  C1  nev_penetration            NEV retail share of total retail
  C2  ice_decline                YoY decline of ICE retail (positive when ICE shrinks)
  C3  bev_share_of_nev           BEV wholesale as share of NEV wholesale
  C4  bev_small_car_share        A0 + A level share within BEV (shift from A00 micro into A0/A)

Each component is min-max normalized to [0, 1] over the full window.
Composite index = equal-weighted average of the four z-aligned components.

Why these four:
  - C1 and C2 capture the headline transition (NEV in, ICE out)
  - C3 captures where NEV demand is concentrating (BEV is the structural winner)
  - C4 captures the within-BEV composition shift from micro cars (A00) to mainstream small cars (A0/A)

Outputs
-------
data/processed/transition_index.csv  monthly index + components
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"


def _minmax(s: pd.Series) -> pd.Series:
    lo, hi = s.min(skipna=True), s.max(skipna=True)
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(np.nan, index=s.index)
    return (s - lo) / (hi - lo)


def build_index(panel: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy().sort_values("month").reset_index(drop=True)

    # C1 NEV penetration (already a share, 0-1)
    df["c1_nev_penetration"] = df["nev_penetration"]

    # C2 ICE YoY decline: use the hand-prepared ice_yoy where present (negative = decline),
    # fall back to calc from ice retail wan when NaN. We define c2 as -ice_yoy so that
    # a bigger decline raises the component.
    ice_yoy = df["ice_yoy"].copy()
    df["c2_ice_decline"] = -ice_yoy

    # C3 BEV share of NEV: use computed where present
    df["c3_bev_share_nev"] = df["bev_share_of_nev"]

    # C4 BEV small-car share = A0 + A
    df["c4_bev_a0_plus_a"] = df[["bev_mix_a0", "bev_mix_a"]].sum(axis=1, min_count=1)

    # min-max normalize each component
    for c in ["c1_nev_penetration", "c2_ice_decline", "c3_bev_share_nev", "c4_bev_a0_plus_a"]:
        df[c + "_norm"] = _minmax(df[c])

    # composite = mean of available normalized components (row-wise)
    norm_cols = [c + "_norm" for c in
                 ["c1_nev_penetration", "c2_ice_decline", "c3_bev_share_nev", "c4_bev_a0_plus_a"]]
    df["transition_index"] = df[norm_cols].mean(axis=1, skipna=True)
    df["components_available"] = df[norm_cols].notna().sum(axis=1)

    keep = ["month"] + \
           ["c1_nev_penetration", "c2_ice_decline", "c3_bev_share_nev", "c4_bev_a0_plus_a"] + \
           norm_cols + ["transition_index", "components_available"]
    return df[keep]


if __name__ == "__main__":
    panel = pd.read_csv(PROC / "national_panel.csv", parse_dates=["month"])
    idx = build_index(panel)
    idx.to_csv(PROC / "transition_index.csv", index=False)
    print(idx.to_string(index=False))
