"""
ChargeAhead: parse CPCA monthly reports (2023-2026) into a tidy monthly panel.

Inputs
------
data/raw/cpca_2023.xlsx     section-headed layout, text-heavy
data/raw/cpca_2024.xlsx     table-headed layout, numeric cells
data/raw/cpca_2025.xlsx     table-headed layout, numeric cells
data/raw/cpca_2026.xlsx     table-headed layout, 1-8 月

Output
------
data/processed/national_panel.csv  one row per month, Jan 2023 - Aug 2026
"""

from __future__ import annotations
import re
from pathlib import Path
import openpyxl
import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT = Path(__file__).resolve().parents[1] / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------
NUM = r"(-?\d+(?:\.\d+)?)"

def _wan_to_number(s):
    """turn '203.5' or '203.5万辆' into float 203.5 (万辆 unit kept)"""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip().replace(",", "").replace("，", "")
    m = re.search(NUM, s)
    return float(m.group(1)) if m else None


def _month_from_cell(c):
    """'1月' -> 1 ; otherwise None"""
    if c is None:
        return None
    m = re.match(r"\s*(\d{1,2})\s*月", str(c))
    return int(m.group(1)) if m else None


def _rows(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    return [tuple(r) for r in ws.iter_rows(values_only=True)]


# ------------------------------------------------------------------
# 2023 parser (section-headed layout)
# ------------------------------------------------------------------
def parse_2023(path=RAW / "cpca_2023.xlsx"):
    rows = _rows(path)

    # section 一: retail totals; section 五: wholesale; section 九: NEV
    sections = {}
    cur = None
    for r in rows:
        if r[0] and isinstance(r[0], str) and re.match(r"\s*[一二三四五六七八九十]+、", r[0]):
            cur = r[0]
            sections[cur] = []
        elif cur is not None:
            sections[cur].append(r)

    out = {m: {} for m in range(1, 13)}

    def _grab(sec_prefix, col_map):
        key = next((k for k in sections if k.startswith(sec_prefix)), None)
        if key is None:
            return
        for r in sections[key]:
            m = _month_from_cell(r[0])
            if m is None:
                continue
            for name, idx in col_map.items():
                v = _wan_to_number(r[idx]) if idx < len(r) else None
                if v is not None:
                    out[m][name] = v

    _grab("一、", {"retail_wan": 1, "retail_yoy": 2, "retail_mom": 3})
    _grab("五、", {"wholesale_wan": 1, "wholesale_yoy": 2, "wholesale_mom": 3})
    _grab("九、", {"nev_wholesale_wan": 1, "nev_retail_wan": 2, "nev_penetration": 3})

    # section 十: BEV share + segment mix from TEXT
    # eg "纯电27.2万 / 插混11.7万"  "B级39% / A0级25% / A级22% / A00级14%"
    key = next((k for k in sections if k.startswith("十、")), None)
    if key:
        for r in sections[key]:
            m = _month_from_cell(r[0])
            if m is None:
                continue
            pwr_txt = str(r[1] or "")
            lvl_txt = str(r[2] or "")

            bev = re.search(r"纯电\s*" + NUM, pwr_txt)
            phev = re.search(r"插混\s*" + NUM, pwr_txt)
            # 2023 report lumps EREV into 插混 text in some months
            if bev:
                out[m]["bev_wholesale_wan"] = float(bev.group(1))
            if phev:
                # treat as PHEV+EREV combined for 2023
                out[m]["phev_erev_wholesale_wan"] = float(phev.group(1))
            if bev and phev:
                total = float(bev.group(1)) + float(phev.group(1))
                if total > 0:
                    out[m]["bev_share_of_nev_implied"] = float(bev.group(1)) / total

            for lvl in ("A00", "A0", "A", "B"):
                mm = re.search(lvl + r"级\s*" + NUM + r"%", lvl_txt)
                if mm:
                    out[m][f"bev_mix_{lvl.lower()}"] = float(mm.group(1)) / 100.0

    df = pd.DataFrame(out).T.reset_index().rename(columns={"index": "month_num"})
    df.insert(0, "year", 2023)
    df.insert(1, "month", pd.to_datetime(df["month_num"].astype(str) + "/2023", format="%m/%Y"))
    return df.drop(columns=["month_num"])


# ------------------------------------------------------------------
# 2024-2026 parser (table-headed layout)
# ------------------------------------------------------------------
_SECTION_RE = re.compile(r"^\s*(表[一二三四五六七八九十]+|[一二三四五六七八九十]+、)")
_SEPARATOR_RE = re.compile(r"^\s*===+\s*$")

def _hint_positions(rows, header_hint):
    """return all row indices where header_hint appears in any cell"""
    hits = []
    for i, r in enumerate(rows):
        for cell in r:
            if isinstance(cell, str) and header_hint in cell:
                hits.append(i)
                break
    return hits


def _find_table_rows(rows, header_hint, data_cols=12):
    """find a table whose cell contains header_hint, return list of data rows below it.
    multiple occurrences (e.g. TOC + real table): pick the one whose immediate following rows
    contain month cells."""
    for i in _hint_positions(rows, header_hint):
        data = []
        found_month = False
        for j in range(i + 1, min(i + 30, len(rows))):
            rj = rows[j]
            first = rj[0]
            if isinstance(first, str) and _SECTION_RE.match(first):
                break
            if isinstance(first, str) and _SEPARATOR_RE.match(first):
                continue
            if isinstance(first, str) and ("全年累计" in first or first.startswith("1-")):
                continue
            if first is None:
                continue
            if _month_from_cell(first) is not None:
                found_month = True
            data.append(rj)
        if found_month:
            return data
    return []


def _find_wide_table_rows(rows, header_hint):
    """for wide-by-month tables (one row per category, columns = months).
    returns list of category rows (first col = category label like '纯电动 (BEV)')."""
    for i in _hint_positions(rows, header_hint):
        data = []
        has_category = False
        for j in range(i + 1, min(i + 30, len(rows))):
            rj = rows[j]
            first = rj[0]
            if isinstance(first, str) and _SECTION_RE.match(first):
                break
            if isinstance(first, str) and _SEPARATOR_RE.match(first):
                continue
            if first is None:
                continue
            if isinstance(first, str) and _month_from_cell(first):
                continue
            if isinstance(first, str) and first.strip() in ("月份", "动力类型", "细分级别", "厂商名称", "指标类型"):
                continue
            if isinstance(first, str) and any(numeric_cell_present(x) for x in rj[1:]):
                has_category = True
            data.append(rj)
        if has_category:
            return data
    return []


def numeric_cell_present(x):
    if isinstance(x, (int, float)):
        return True
    if isinstance(x, str) and re.search(r"\d", x):
        return True
    return False


def _parse_table_year(path, year, months_available):
    rows = _rows(path)

    # table 1 (overall retail/wholesale/production/export)
    tbl1_hint_list = ["表一：", "一、"]
    # table 2 (NEV core + penetration)
    tbl2_hint_list = ["表二：", "二、"]
    # table 3 (NEV powertrain mix BEV/PHEV/EREV)
    tbl3_hint_list = ["表三：", "三、"]
    # table 4 (BEV level mix)
    tbl4_hint_list = ["表四："]

    out = {m: {} for m in months_available}

    def _try(hints, cols, from_rows=None):
        src = rows if from_rows is None else from_rows
        for h in hints:
            data = _find_table_rows(src, h)
            if data:
                return data
        return []

    # ---- table 1
    data = _try(tbl1_hint_list, None)
    for r in data:
        m = _month_from_cell(r[0])
        if m is None or m not in out:
            continue
        for name, idx in {
            "retail_wan": 1, "retail_yoy": 2, "retail_mom": 3,
            "wholesale_wan": 4, "wholesale_yoy": 5,
            "production_wan": 6, "production_yoy": 7,
            "export_wan": 8, "export_yoy": 9,
        }.items():
            v = _wan_to_number(r[idx]) if idx < len(r) else None
            if v is not None:
                out[m][name] = v

    # ---- table 2
    data = _try(tbl2_hint_list, None)
    for r in data:
        m = _month_from_cell(r[0])
        if m is None or m not in out:
            continue
        # 2024: nev_retail, zy_yoy, retail_penetration, nev_wholesale, batch_yoy, batch_penetration, nev_export, yoy
        # 2025/2026: nev_retail, yoy, nev_wholesale, batch_yoy, nev_production, prod_yoy, nev_export, yoy, retail_penetration, wholesale_penetration
        if year == 2024:
            mapping = {
                "nev_retail_wan": 1, "nev_retail_yoy": 2, "nev_penetration": 3,
                "nev_wholesale_wan": 4, "nev_wholesale_yoy": 5, "nev_wholesale_penetration": 6,
                "nev_export_wan": 7, "nev_export_yoy": 8,
            }
        else:
            mapping = {
                "nev_retail_wan": 1, "nev_retail_yoy": 2,
                "nev_wholesale_wan": 3, "nev_wholesale_yoy": 4,
                "nev_production_wan": 5, "nev_production_yoy": 6,
                "nev_export_wan": 7, "nev_export_yoy": 8,
                "nev_penetration": 9, "nev_wholesale_penetration": 10,
            }
        for name, idx in mapping.items():
            v = _wan_to_number(r[idx]) if idx < len(r) else None
            if v is not None:
                out[m][name] = v

    # ---- table 3  (BEV/PHEV/EREV)
    data = _try(tbl3_hint_list, None)
    if year == 2024:
        # 2024 table 3 is wide-by-month: no, actually it is one row per month
        for r in data:
            m = _month_from_cell(r[0])
            if m is None or m not in out:
                continue
            bev_t = str(r[1] or "")
            phev_t = str(r[2] or "")
            erev_t = str(r[3] or "")
            def _get_wan(s):
                mm = re.search(NUM + r"\s*万", s)
                return float(mm.group(1)) if mm else None
            bev = _get_wan(bev_t); phev = _get_wan(phev_t); erev = _get_wan(erev_t)
            if bev is not None: out[m]["bev_wholesale_wan"] = bev
            if phev is not None: out[m]["phev_wholesale_wan"] = phev
            if erev is not None: out[m]["erev_wholesale_wan"] = erev
            tot = sum(x for x in (bev, phev, erev) if x is not None)
            if bev is not None and tot > 0:
                out[m]["bev_share_of_nev"] = bev / tot
    else:
        # 2025/2026: wide-by-month (one row per powertrain, columns are months 1..12)
        wide = _find_wide_table_rows(rows, "表三：")
        for r in wide:
            label = str(r[0] or "")
            if "纯电动" in label:
                for mm in months_available:
                    v = _wan_to_number(r[mm])
                    if v is not None:
                        out[mm]["bev_wholesale_wan"] = v
            elif "狭义插混" in label or "PHEV" in label:
                for mm in months_available:
                    v = _wan_to_number(r[mm])
                    if v is not None:
                        out[mm]["phev_wholesale_wan"] = v
            elif "增程" in label or "EREV" in label:
                for mm in months_available:
                    v = _wan_to_number(r[mm])
                    if v is not None:
                        out[mm]["erev_wholesale_wan"] = v
        for mm in months_available:
            bev = out[mm].get("bev_wholesale_wan")
            phev = out[mm].get("phev_wholesale_wan")
            erev = out[mm].get("erev_wholesale_wan")
            tot = sum(x for x in (bev, phev, erev) if x is not None)
            if bev is not None and tot > 0:
                out[mm]["bev_share_of_nev"] = bev / tot

    # ---- table 4  BEV level mix
    data = _find_wide_table_rows(rows, "表四：")
    if year == 2024:
        # In 2024 file it is table 七 or just text; we try fallback
        pass
    if data:
        # 2025/2026 layout: columns are months, rows are levels; cells like "11.7 (23%)"
        for r in data:
            label = str(r[0] or "")
            lvl = None
            if "A00" in label:
                lvl = "a00"
            elif "A0" in label:
                lvl = "a0"
            elif label.startswith("A级") or "紧凑型" in label:
                lvl = "a"
            elif "B级" in label or "中型" in label:
                lvl = "b"
            if lvl is None:
                continue
            for mm in months_available:
                v = r[mm] if mm < len(r) else None
                if v is None:
                    continue
                m_pct = re.search(NUM + r"\s*%", str(v))
                if m_pct:
                    out[mm][f"bev_mix_{lvl}"] = float(m_pct.group(1)) / 100.0
                else:
                    # if cell is pure number, treat as wan units (shouldn't happen)
                    pass

    # For 2024 BEV level mix, parse section 七 text form
    if year == 2024:
        tbl7 = _find_table_rows(rows, "表七") or _find_table_rows(rows, "七、")
        for r in tbl7:
            m = _month_from_cell(r[0])
            if m is None or m not in out:
                continue
            bev_t = str(r[1] or "")
            phev_t = str(r[2] or "")
            # 2024 section 七 says 纯电动占59%；B级占纯电动份额34%
            mb = re.search(r"B级[^0-9%]*" + NUM + r"%", bev_t)
            if mb: out[m]["bev_mix_b"] = float(mb.group(1)) / 100.0
            # need to parse A00/A0/A too but 2024 only gives B level in section 七
            # for 2024 we'll leave A00/A0/A as missing; midterm chart can show 2025-2026

    df = pd.DataFrame(out).T.reset_index().rename(columns={"index": "month_num"})
    df.insert(0, "year", year)
    df.insert(1, "month", pd.to_datetime(df["month_num"].astype(str) + f"/{year}", format="%m/%Y"))
    return df.drop(columns=["month_num"])


def parse_2024():
    return _parse_table_year(RAW / "cpca_2024.xlsx", 2024, list(range(1, 13)))


def parse_2025():
    return _parse_table_year(RAW / "cpca_2025.xlsx", 2025, list(range(1, 13)))


def parse_2026():
    return _parse_table_year(RAW / "cpca_2026.xlsx", 2026, list(range(1, 9)))


# ------------------------------------------------------------------
# channel inventory parser
# ------------------------------------------------------------------
def parse_channel(path=RAW / "channel_inventory.xlsx"):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["渠道库存信号总表"]
    out = []
    for r in ws.iter_rows(values_only=True):
        yr = r[0]; mo = r[1]
        if yr is None or mo is None:
            continue
        try:
            yr = int(float(str(yr)))
        except (TypeError, ValueError):
            continue
        if yr < 2020 or yr > 2030:
            continue
        m = _month_from_cell(mo)
        if m is None and isinstance(mo, (int, float)):
            m = int(mo)
        if m is None:
            continue
        try:
            out.append({
                "year": int(yr), "month_num": m,
                "retail_wan": float(r[2]) if r[2] is not None else None,
                "wholesale_wan": float(r[3]) if r[3] is not None else None,
                "channel_gap_wan": float(r[4]) if r[4] is not None else None,
                "inventory_ratio": float(r[5]) if r[5] is not None else None,
                "channel_change_wan": float(r[6]) if (r[6] is not None and str(r[6]) != "—") else None,
            })
        except (TypeError, ValueError):
            continue
    df = pd.DataFrame(out)
    if df.empty:
        return pd.DataFrame(columns=["year", "month", "channel_gap_wan", "inventory_ratio", "channel_change_wan"])
    df["month"] = pd.to_datetime(df["month_num"].astype(str) + "/" + df["year"].astype(str), format="%m/%Y")
    return df[["year", "month", "channel_gap_wan", "inventory_ratio", "channel_change_wan"]]


# ------------------------------------------------------------------
# ICE YoY decline parser
# ------------------------------------------------------------------
def parse_ice(path=RAW / "ice_yoy_decline.xlsx"):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["ICE同比降幅"]
    rows = []
    for r in ws.iter_rows(values_only=True):
        m = _month_from_cell(r[0])
        if m is None:
            continue
        for year, idx in [(2024, 1), (2025, 2), (2026, 3)]:
            v = r[idx] if idx < len(r) else None
            if isinstance(v, (int, float)):
                rows.append({"year": year, "month_num": m, "ice_yoy": float(v)})
    df = pd.DataFrame(rows)
    df["month"] = pd.to_datetime(df["month_num"].astype(str) + "/" + df["year"].astype(str), format="%m/%Y")
    return df[["year", "month", "ice_yoy"]]


# ------------------------------------------------------------------
# build the national panel
# ------------------------------------------------------------------
def build_panel():
    frames = [parse_2023(), parse_2024(), parse_2025(), parse_2026()]
    panel = pd.concat(frames, ignore_index=True, sort=False)

    chan = parse_channel()
    panel = panel.merge(chan.drop(columns=["year"]), on="month", how="left", suffixes=("", "_ch"))

    ice = parse_ice()
    panel = panel.merge(ice.drop(columns=["year"]), on="month", how="left")

    # normalize shares (CPCA sometimes prints "51.1%" as text, parsed as 51.1)
    for col in ["nev_penetration", "nev_wholesale_penetration"]:
        if col in panel.columns:
            panel[col] = panel[col].where(panel[col].abs() <= 2, panel[col] / 100.0)

    # derive ICE retail from totals when ICE not present
    panel["ice_retail_wan"] = panel["retail_wan"] - panel["nev_retail_wan"]
    # year-over-year ICE change computed from ICE retail
    panel["ice_retail_yoy_calc"] = (
        panel["ice_retail_wan"] / panel.groupby(panel["month"].dt.month)["ice_retail_wan"].shift(1) - 1
    )

    panel = panel.sort_values("month").reset_index(drop=True)
    return panel


if __name__ == "__main__":
    panel = build_panel()
    out_path = OUT / "national_panel.csv"
    panel.to_csv(out_path, index=False)
    print(f"Wrote {out_path}  shape={panel.shape}  months={panel['month'].min()}..{panel['month'].max()}")
    # quick QC
    cols = ["month", "retail_wan", "nev_retail_wan", "nev_penetration",
            "bev_wholesale_wan", "phev_wholesale_wan", "erev_wholesale_wan",
            "bev_share_of_nev", "bev_mix_a00", "bev_mix_a0", "bev_mix_a", "bev_mix_b",
            "channel_gap_wan", "ice_yoy", "ice_retail_wan"]
    print(panel[cols].to_string(index=False))
