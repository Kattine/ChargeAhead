"""
ChargeAhead: model- / brand-level validation preview.

Status: the file "data/raw/model_level_sales_2026.xlsx" is a hand-collected,
dense Excel sheet (two column blocks side by side, one brand per block, with
brand-level and model-level rows nested together).  For the midterm, we extract
brand-level monthly totals (Mar - Aug 2026) and classify each brand by
powertrain profile.  Full model-level parsing is a next-step task.

Analysis
--------
For each brand covered in the file we pull its monthly total for Mar..Aug 2026,
tag its powertrain profile (BEV-only vs PHEV/EREV-only vs mixed) using the
brand-section label on the sheet, then measure growth from Mar to Aug 2026.
We then compare that growth with the growth of the Transition Index over the
same months.  The intent is directional, not causal.
"""

from pathlib import Path
import openpyxl
import pandas as pd
import re

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"

MONTHS = ["2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08"]


def _col_block_months(ws, header_row, start_col):
    """given a block starting at start_col, find which columns hold the 2026 months Mar-Aug."""
    header = {}
    for c in range(start_col, min(start_col + 12, ws.max_column + 1)):
        v = ws.cell(row=header_row, column=c).value
        if hasattr(v, "strftime"):
            key = v.strftime("%Y-%m")
            if key in MONTHS:
                header[key] = c
    return header


def extract_brands(path=RAW / "model_level_sales_2026.xlsx"):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["品牌（厂商）2026年汽车销量"]

    brands = []
    for row in range(1, ws.max_row + 1):
        for col in [1, 13]:   # the file lays out two blocks: columns A..K and M..W
            v = ws.cell(row=row, column=col).value
            if not isinstance(v, str):
                continue
            m = re.match(r"(.+?)销量详情[（(](.+?)[)）]", v)
            if not m:
                continue
            brand = m.group(1).strip()
            powertrain = m.group(2).strip()
            # locate the header row (row+1 typically contains "项目" and the dates)
            hdr_row = row + 1
            col_map = _col_block_months(ws, hdr_row, col)
            if not col_map:
                continue
            # brand total row is typically row+2 (brand name repeated)
            # Pick the first row after header whose column[col] starts with the brand name
            total_row = None
            for r in range(hdr_row + 1, min(hdr_row + 5, ws.max_row + 1)):
                v2 = ws.cell(row=r, column=col).value
                if isinstance(v2, str) and brand in v2:
                    total_row = r
                    break
            if total_row is None:
                continue
            rec = {"brand": brand, "powertrain_profile": powertrain}
            for mkey, mcol in col_map.items():
                v3 = ws.cell(row=total_row, column=mcol).value
                try:
                    rec[mkey] = float(v3)
                except (TypeError, ValueError):
                    rec[mkey] = None
            brands.append(rec)

    df = pd.DataFrame(brands)
    # keep brands with at least Mar and Aug coverage
    df = df.dropna(subset=["2026-03", "2026-08"]).reset_index(drop=True)
    return df


def main():
    bdf = extract_brands()
    bdf["growth_mar_to_aug"] = bdf["2026-08"] / bdf["2026-03"] - 1

    # classify powertrain profile
    def classify(p):
        p = p.lower()
        if "插混" in p and "纯电" in p:
            return "mixed_bev_phev"
        if "增程" in p and "纯电" in p:
            return "mixed_bev_erev"
        if "插混" in p:
            return "phev_only"
        if "增程" in p:
            return "erev_only"
        if "纯电" in p:
            return "bev_only"
        return "unknown"

    bdf["profile"] = bdf["powertrain_profile"].apply(classify)
    bdf = bdf.sort_values("growth_mar_to_aug", ascending=False)
    bdf.to_csv(PROC / "brand_growth_2026H1.csv", index=False)
    print("\n=== Brand-level sales growth, Mar - Aug 2026 ===")
    print(bdf[["brand", "profile"] + MONTHS + ["growth_mar_to_aug"]].to_string(index=False))

    # Transition Index growth over same window
    idx = pd.read_csv(PROC / "transition_index.csv", parse_dates=["month"])
    mask = (idx["month"] >= "2026-03-01") & (idx["month"] <= "2026-08-01")
    sub = idx.loc[mask, ["month", "transition_index"]].sort_values("month")
    tidx_mar = float(sub.iloc[0]["transition_index"])
    tidx_aug = float(sub.iloc[-1]["transition_index"])
    tidx_change = tidx_aug - tidx_mar
    print(f"\nTransition Index Mar 2026 = {tidx_mar:.3f}, Aug 2026 = {tidx_aug:.3f}, +{tidx_change:.3f}")

    # grouped summary
    group = bdf.groupby("profile")["growth_mar_to_aug"].agg(["count", "mean", "median"])
    group.to_csv(PROC / "brand_growth_by_profile.csv")
    print("\n=== Grouped by powertrain profile ===")
    print(group.round(3).to_string())


if __name__ == "__main__":
    main()
