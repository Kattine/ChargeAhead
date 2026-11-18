# Data directory

## raw/
Source files, untouched. Any computation lives in `src/`.

| File | What it is | Window | Notes |
|---|---|---|---|
| `cpca_2023.xlsx` | CPCA monthly report | Jan - Dec 2023 | Section-headed layout |
| `cpca_2024.xlsx` | CPCA monthly report | Jan - Dec 2024 | Table-headed layout |
| `cpca_2025.xlsx` | CPCA monthly report | Jan - Dec 2025 | Table-headed layout, 14 tables |
| `cpca_2026.xlsx` | CPCA monthly report | Jan - Aug 2026 | Table-headed layout, 1-8月 |
| `channel_inventory.xlsx` | Pre-computed channel gap, inventory ratio, change | 2023-01 to 2026-08 | Derived from CPCA batch - retail |
| `ice_yoy_decline.xlsx` | Pre-computed ICE YoY retail decline | 2024-01 to 2026-08 | Derived from total retail - NEV retail |
| `baidu_index_weekly.xlsx` | Baidu Search Index weekly | 2023-01-01 to 2026-10-12 | 42 keywords, 199 weeks each, ISO week + month attribution |
| `model_level_sales_2026.xlsx` | Hand-collected brand sales | Mar - Aug 2026 | 14 brands, two-column layout per sheet |
| `weekly_insurance_registrations_sparse.xlsx` | Hand sample of insurance registrations | 2023-02 to 2025-01 | Sparse, exploratory only |
| `nev_fire_background.xlsx` | Supporting narrative on NEV safety context | n/a | Used only for Idea Pitch narrative |
| `data_checklist.xlsx` | Component-availability map | 2024-2026 | Author's own tracking sheet |

## processed/
Pipeline outputs. Rebuilt from scratch by `python src/parse_cpca.py` then the downstream scripts, so these files are safe to delete.

| File | Produced by | Shape |
|---|---|---|
| `national_panel.csv` | `src/parse_cpca.py` | 44 rows x 36 cols |
| `transition_index.csv` | `src/transition_index.py` | 44 rows x 11 cols |
| `leadlag_*.csv` | `src/leadlag.py` | 13 rows each (lag -6..+6) |
| `baseline_metrics.csv` | `src/baseline.py` | 3 models x 4 metrics |
| `baidu_weekly.csv` | `src/baidu_index.py` | 8358 rows (42 kw x 199 wk) |
| `baidu_monthly.csv` | `src/baidu_index.py` | 46 months x 42 keywords |
| `baidu_signals_monthly.csv` | `src/baidu_index.py` | 46 months x 10 composite signals |
| `leadlag_baidu_*.csv` | `src/baidu_index.py` | 13 rows each per signal |
| `leadlag_baidu_headline.csv` | `src/baidu_index.py` | 9 rows, 4 cols |
| `baidu_vs_baseline.csv` | `src/baidu_index.py` | 5 features x 6 cols |
| `brand_growth_2026H1.csv` | `src/model_validation.py` | 14 brands |
| `brand_growth_by_profile.csv` | `src/model_validation.py` | 3 powertrain groups |
