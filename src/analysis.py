"""ChargeAhead v2: transparent targets, matched backtests and source audits.

Run with `python run_analysis.py` from the project root. No network calls.
All findings are exploratory on user-supplied extracts.
"""
from pathlib import Path
import hashlib
import json
import re
import numpy as np
import pandas as pd
import openpyxl
from .parse_cpca import build_panel
from .model_validation import extract_brands

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
OUT = ROOT / "data/processed"
FIRST_TEST = pd.Timestamp("2025-03-01")
PRIMARY_TERMS = ["新能源汽车", "新能源车"]


def save(df, name):
    df.to_csv(OUT / name, index=False)


def prepare_panel():
    d = build_panel().sort_values("month").reset_index(drop=True)
    assert d.month.is_unique
    assert list(d.month) == list(pd.date_range(d.month.min(), d.month.max(), freq="MS"))
    assert (d.retail_wan > 0).all()
    assert ((d.nev_retail_wan >= 0) & (d.nev_retail_wan <= d.retail_wan)).all()
    # A directly interpretable target, with the same definition in every month.
    d["nev_share"] = d.nev_retail_wan / d.retail_wan
    d["share_change_pp"] = d.nev_share.diff() * 100
    d["reported_share_gap_pp"] = (d.nev_penetration - d.nev_share) * 100
    # Recalculate derived fields; retain the input's reported counterparts.
    d["ice_yoy_calculated"] = d.ice_retail_wan.pct_change(12, fill_method=None)
    d["wholesale_retail_gap_wan"] = d.wholesale_wan - d.retail_wan
    d["wholesale_retail_ratio"] = d.wholesale_wan / d.retail_wan
    # This is NOT an inventory stock. Exports and population differences remain.
    d["domestic_flow_residual_wan"] = d.wholesale_wan - d.export_wan - d.retail_wan
    save(d, "national_panel_v2.csv")
    audit = d[["month", "nev_penetration", "nev_share", "reported_share_gap_pp"]].copy()
    audit["needs_source_reconciliation"] = audit.reported_share_gap_pp.abs() > .15
    save(audit, "share_source_audit.csv")
    return d


def prepare_attention():
    w = pd.read_excel(RAW / "baidu_index_weekly.xlsx")
    w["keyword"] = w.keyword.str.lower().str.strip()
    for c in ["week_start", "week_end", "month"]:
        w[c] = pd.to_datetime(w[c])
    assert not w.duplicated(["keyword", "week_start", "week_end"]).any()
    assert (w.week_end >= w.week_start).all()
    # A week belongs to the month in which it ENDS. Never use an unfinished week.
    w["available_month"] = w.week_end.dt.to_period("M").dt.to_timestamp()
    w["weighted_intensity"] = w.index_all_mean * w.days
    m = w.groupby(["keyword", "available_month"], as_index=False).agg(
        weighted_intensity=("weighted_intensity", "sum"), observed_days=("days", "sum"),
        n_weeks=("week_end", "size"), max_week_end=("week_end", "max"))
    m["attention"] = m.weighted_intensity / m.observed_days
    assert (m.max_week_end <= m.available_month + pd.offsets.MonthEnd(0)).all()
    save(m, "attention_monthly_long.csv")
    wide = m.pivot(index="available_month", columns="keyword", values="attention")
    # Exactly two conceptually chosen broad-NEV terms, with equal weights.
    # No selection of the best of 42 terms using test results.
    assert all(k in wide for k in PRIMARY_TERMS)
    a = wide[PRIMARY_TERMS].mean(axis=1).rename("attention").reset_index()
    a = a.rename(columns={"available_month": "month"})
    a["attention_change"] = a.attention.diff()
    save(a, "attention_primary.csv")
    meta = {
        "keywords": int(w.keyword.nunique()), "weeks": int(w.week_end.nunique()),
        "rows": len(w), "start": str(w.week_start.min().date()),
        "end": str(w.week_end.max().date()), "primary_terms": PRIMARY_TERMS,
        "attribution_matches_week_end": int((w.month == w.available_month).sum()),
        "sum_mean_days_ratio_median": float((w.index_all_sum / (w.index_all_mean * w.days)).median()),
        "note": "Use supplied mean intensity. Sum/mean/day semantics need source confirmation."
    }
    return a, meta


def ols_predict(train, row, features):
    clean = train.dropna(subset=["y"] + features)
    if len(clean) < 10:
        raise ValueError("Insufficient training data")
    # Training-only centering/scaling for numerical stability; OLS with intercept.
    x = clean[features].to_numpy(float)
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale[scale < 1e-12] = 1.0
    design = np.column_stack([np.ones(len(clean)), (x-mean)/scale])
    coef = np.linalg.lstsq(design, clean.y.to_numpy(float), rcond=None)[0]
    xt = (row[features].to_numpy(float)-mean)/scale
    return float(np.r_[1., xt] @ coef), len(clean)


def forecast(panel, attention, target="nev_share", availability_lag=1):
    """Predict delta share in pp, then add last observed level to evaluate level.

    lag=1 assumes prior-month market data is available at forecast issuance.
    This is typically within the target month, NOT a verified month-end forecast.
    lag=2 is a conservative sensitivity with both inputs and training outcomes
    delayed one extra month. It evaluates the same delta target and test dates.
    """
    d = panel[["month", target]].merge(attention, on="month", validate="one_to_one")
    d["y"] = d[target].diff()*100
    d["lag_change"] = d.y.shift(availability_lag)
    d["lag_attention"] = d.attention_change.shift(availability_lag)
    d["seasonal_change"] = d.y.shift(12)
    rows = []
    for t in range(len(d)):
        row = d.iloc[t]
        if row.month < FIRST_TEST or not np.isfinite(row.y):
            continue
        # No future outcome, feature or preprocessing is permitted in the fit.
        train = d.iloc[:t-availability_lag+1].dropna(subset=["y", "lag_change", "lag_attention"])
        y = float(row.y)
        predictions = {
            "No change": 0.,
            "Historical mean": float(train.y.mean()),
            "Historical median": float(train.y.median()),
            "Repeat last change": float(row.lag_change),
            "Last year's change": float(row.seasonal_change),
        }
        for name, features in {
            "Search only": ["lag_attention"],
            "History only (AR1)": ["lag_change"],
            "History + search": ["lag_change", "lag_attention"],
        }.items():
            predictions[name], _ = ols_predict(train, row, features)
        for name, prediction in predictions.items():
            rows.append({"month": row.month, "target": target, "availability_lag": availability_lag,
                         "model": name, "actual_change_pp": y, "predicted_change_pp": prediction,
                         "train_n": len(train), "train_last_month": train.month.max(),
                         "latest_input_month": d.month.iloc[t-availability_lag]})
    return pd.DataFrame(rows)


def summarize(f):
    rows = []
    for name, g in f.groupby("model", sort=False):
        actual = g.actual_change_pp.to_numpy()
        pred = g.predicted_change_pp.to_numpy()
        errors = pred-actual
        call = np.abs(pred) > 1e-10
        rows.append({"model": name, "n": len(g), "mae_pp": float(np.abs(errors).mean()),
                     "rmse_pp": float(np.sqrt((errors**2).mean())),
                     "direction_accuracy": float((np.sign(pred[call]) == np.sign(actual[call])).mean()) if call.any() else None,
                     "direction_call_coverage": float(call.mean()),
                     "start": str(g.month.min().date()), "end": str(g.month.max().date())})
    result = pd.DataFrame(rows)
    ref = result.loc[result.model == "No change", "mae_pp"].iloc[0]
    result["mae_ratio_to_no_change"] = result.mae_pp/ref
    return result


def incremental_diagnostic(f):
    p = f.pivot(index="month", columns="model", values="predicted_change_pp")
    actual = f.drop_duplicates("month").set_index("month").actual_change_pp.reindex(p.index)
    gains = abs(p["History only (AR1)"]-actual)-abs(p["History + search"]-actual)
    # Positive gain means adding search helps. Circular block resampling is a
    # descriptive stability check, not proof after exploratory model development.
    rng = np.random.default_rng(20261014)
    n = len(gains)
    starts = rng.integers(0, n, size=(4000, int(np.ceil(n/3))))
    ids = ((starts[..., None]+np.arange(3)) % n).reshape(4000,-1)[:,:n]
    draws = gains.to_numpy()[ids].mean(axis=1)
    out = {"comparison": "History only (AR1) minus History + search absolute error",
           "n": n, "mean_mae_gain_pp": float(gains.mean()),
           "positive_gain_months": int((gains>0).sum()),
           "bootstrap_p05_pp": float(np.quantile(draws,.05)),
           "bootstrap_p95_pp": float(np.quantile(draws,.95)),
           "bootstrap_replicates": 4000, "block_length_months": 3,
           "note": "Exploratory 90% block-bootstrap range; small sample, not confirmatory inference."}
    return out


def legacy_audit():
    old = ROOT / "archive/v1/processed"
    idx = pd.read_csv(old/"ablation_expanding_mm.csv", parse_dates=["month"])
    att = pd.read_csv(old/"baidu_signals_monthly.csv", parse_dates=["month"])
    allrows = []
    for col in ["transition_index_full", "transition_index_expanding"]:
        d=idx[["month",col]].merge(att[["month","att_nev_overall"]],on="month").sort_values("month")
        d["y"]=d[col].diff();d["x"]=d.att_nev_overall.diff()
        d=d.dropna(subset=["y"]).reset_index(drop=True)
        rows=[]
        for t in range(24,len(d)):
            tr=d.iloc[:t];x=tr.x.shift(1);mask=x.notna() & tr.y.notna()
            b=np.polyfit(x[mask],tr.y[mask],1)
            preds={"Search only":np.polyval(b,d.x.iloc[t-1]),"Repeat last change":d.y.iloc[t-1],
                   "No change":0.,"Historical mean":tr.y.mean(),"Historical median":tr.y.median(),
                   "Last year's change":d.y.iloc[t-12]}
            for k,v in preds.items():rows.append({"model":k,"y":d.y.iloc[t],"pred":v,"month":d.month.iloc[t]})
        q=pd.DataFrame(rows)
        for k,g in q.groupby("model",sort=False):
            allrows.append({"index_variant":col,"model":k,"n":len(g),
                            "mae_index_units":float(abs(g.pred-g.y).mean()),
                            "direction_accuracy":float((np.sign(g.pred)==np.sign(g.y)).mean()) if k!="No change" else None,
                            "start":str(g.month.min().date()),"end":str(g.month.max().date())})
    result=pd.DataFrame(allrows);save(result,"legacy_index_audit.csv")
    components=pd.read_csv(old/"transition_index.csv")
    save(components[["month","components_available"]],"legacy_component_coverage.csv")
    return result


def brand_and_model_data():
    b=extract_brands()
    b["growth_mar_aug"]=b["2026-08"]/b["2026-03"]-1
    # Explicitly preserve a triple-powertrain group instead of hiding it inside PHEV.
    def group(s):
        kinds=[label for token,label in [("纯电","BEV"),("插混","PHEV"),("增程","EREV")] if token in s]
        return " + ".join(kinds) if kinds else "Unclassified"
    b["profile"]=b.powertrain_profile.map(group)
    save(b,"brand_growth_v2.csv")
    grouped=b.groupby("profile").growth_mar_aug.agg(n="count",mean="mean",median="median",minimum="min",maximum="max").reset_index()
    save(grouped,"brand_group_summary.csv")
    # Extract real vehicle-model rows. A dash stays missing, never silently zero.
    ws=openpyxl.load_workbook(RAW/"model_level_sales_2026.xlsx",data_only=True).worksheets[0]
    rows=[]
    for start in [1,13]:
        brand=None;profile=None;dates={}
        for r in range(1,ws.max_row+1):
            v=ws.cell(r,start).value
            if isinstance(v,str) and "销量详情" in v:
                brand=v.split("销量详情")[0];profile=v.split("（")[-1].rstrip("）")
                dates={c:ws.cell(r+1,c).value.strftime("%Y-%m-01") for c in range(start,start+11)
                       if hasattr(ws.cell(r+1,c).value,"strftime")}
                continue
            name=ws.cell(r,start+1).value
            if brand and isinstance(name,str) and name.strip() and dates and v is None:
                model_type=ws.cell(r,start+2).value
                if not isinstance(model_type,str) or not model_type.strip():
                    model_type="BEV (inherited from source's BEV-only brand)" if profile=="纯电" else "Unspecified"
                for c,month in dates.items():
                    value=ws.cell(r,c).value
                    rows.append({"brand":brand,"model":name.strip(),"powertrain_source_label":model_type,
                                 "month":month,"sales_units":float(value) if isinstance(value,(int,float)) else np.nan,
                                 "source_row":r,"source_column":c,"source_scope":"retail label in supplied workbook; original source unverified"})
    models=pd.DataFrame(rows)
    assert not models.duplicated(["brand","model","month"]).any()
    save(models,"model_sales_tidy.csv")
    # Longer manufacturer WHOLESALE panel stays separate from retail brand data.
    out=[]
    for year in [2025,2026]:
        ws=openpyxl.load_workbook(RAW/f"cpca_{year}.xlsx",data_only=True).active
        vals=list(ws.values)
        for i,row in enumerate(vals):
            if not str(row[0]).startswith("表五"):continue
            for j in range(i+1,min(i+5,len(vals))):
                if vals[j][0]!="厂商名称":continue
                cols={c:int(re.search(r"\d+",str(v)).group()) for c,v in enumerate(vals[j]) if c and re.fullmatch(r"\d+月",str(v))}
                for rr in range(j+1,len(vals)):
                    label=vals[rr][0]
                    if label is None or "破万辆" in str(label) or str(label).startswith("="):break
                    for c,mo in cols.items():
                        value=vals[rr][c]
                        if isinstance(value,(int,float)):
                            out.append({"manufacturer":label,"month":f"{year}-{mo:02d}-01","nev_wholesale_units":value,
                                        "source_file":f"cpca_{year}.xlsx","source_row":rr+1,"source_column":c+1})
    wholesale=pd.DataFrame(out)
    assert not wholesale.duplicated(["manufacturer","month"]).any()
    save(wholesale,"manufacturer_wholesale_monthly.csv")
    return b,grouped,models,wholesale


def diagnostics(panel,attention):
    from statsmodels.tsa.stattools import adfuller
    from statsmodels.tsa.seasonal import STL
    y=panel.set_index("month").nev_share*100
    stl=STL(y,period=12,robust=True).fit()
    save(pd.DataFrame({"month":y.index,"share_pct":y.values,"trend":stl.trend.values,
                       "seasonal":stl.seasonal.values,"residual":stl.resid.values}),"share_stl.csv")
    records=[]
    for label,z in [("share_level",y),("share_change",y.diff().dropna())]:
        stat,p,lags,n,*_=adfuller(z,autolag="AIC")
        records.append({"series":label,"statistic":stat,"p_value":p,"lags":lags,"n":n})
    save(pd.DataFrame(records),"share_adf.csv")
    # Descriptive fixed lags 0 and 1 only, with changes alongside levels.
    merged=panel.merge(attention,on="month")
    rows=[]
    for col in ["wholesale_retail_ratio","attention"]:
        for change in [False,True]:
            x=merged[col].diff() if change else merged[col]
            yy=merged.nev_share.diff() if change else merged.nev_share
            for lag in [0,1]:
                pairs=pd.concat([x,yy.shift(-lag)],axis=1).dropna()
                rows.append({"signal":col,"transformation":"changes" if change else "levels",
                             "lead_months":lag,"n":len(pairs),"pearson_r":pairs.corr().iloc[0,1]})
    save(pd.DataFrame(rows),"descriptive_correlations.csv")


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    p=prepare_panel();a,ameta=prepare_attention()
    forecasts=forecast(p,a);metrics=summarize(forecasts)
    save(forecasts,"forecast_predictions.csv");save(metrics,"forecast_metrics.csv")
    incremental=incremental_diagnostic(forecasts)
    (OUT/"incremental_search_diagnostic.json").write_text(json.dumps(incremental,indent=2))
    sensitivity=[]
    for label,target,lag in [("primary","nev_share",1),("reported_share","nev_penetration",1),("one_extra_month_delay","nev_share",2)]:
        f=forecast(p,a,target,lag);s=summarize(f);s.insert(0,"scenario",label);sensitivity.append(s)
        if lag==2:save(f,"forecast_predictions_delayed.csv")
    save(pd.concat(sensitivity,ignore_index=True),"forecast_sensitivity.csv")
    legacy=legacy_audit();b,g,models,wholesale=brand_and_model_data();diagnostics(p,a)
    manifest=[]
    for path in sorted(RAW.glob("*.xlsx")):
        manifest.append({"file":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                         "bytes":path.stat().st_size,"provenance":"user-supplied workbook; original publication/vintage not independently verified"})
    save(pd.DataFrame(manifest),"input_manifest.csv")
    payload={"primary_metrics":json.loads(metrics.to_json(orient="records")),"incremental":incremental,"attention":ameta,
             "panel_months":len(p),"share_discrepancy_months":int((p.reported_share_gap_pp.abs()>.15).sum()),
             "model_count":int(models[["brand","model"]].drop_duplicates().shape[0]),
             "model_observed_cells":int(models.sales_units.notna().sum()),"model_total_cells":len(models),
             "wholesale_manufacturers":int(wholesale.manufacturer.nunique()),
             "wholesale_months":int(wholesale.month.nunique()),"wholesale_rows":len(wholesale),
             "wholesale_complete_manufacturers":int((wholesale.groupby("manufacturer").month.nunique()==20).sum()),
             "brand_groups":g.to_dict("records"),
             "share_history":{"months":p.month.dt.strftime("%b %y").tolist(),"values_pct":(p.nev_share*100).tolist()},
             "legacy_audit":json.loads(legacy.to_json(orient="records"))}
    (OUT/"presentation_data.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False))
    print(metrics.round(4).to_string(index=False))
    print(json.dumps({k:v for k,v in payload.items() if k not in ["primary_metrics","share_history","legacy_audit","brand_groups"]},ensure_ascii=False,indent=2))


if __name__=="__main__":main()
