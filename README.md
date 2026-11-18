# ChargeAhead

Final project for AIPI 590 (Nov 2026). This repo keeps both the final handoff and the earlier midterm pipeline.

## Quick start

If you only need the final version, open `final_app/index.html` in a browser.

Run the full analysis locally:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_analysis.py
python -m unittest discover -s tests -v
python -m src.plot_results
```

Windows activation: `.venv\\Scripts\\activate`

## Main finding (national test)

Question: can Baidu search attention improve short-term prediction of monthly NEV retail share change?

On the same 18-month test window (2025-03 to 2026-08):

- History-only model MAE: 3.223 pp
- History+search model MAE: 3.233 pp
- Direction hits: both 12/18

In this setup, adding the two broad search terms does not improve error.

## Final app

The dashboard is static and local-only:

- No login, backend, or live API
- Data is embedded at build time
- Refresh requires rerunning the pipeline

Rebuild steps:

```bash
python -m src.brand_analysis
python -m src.export_audit
python -m src.build_dashboard
python -m unittest discover -s tests -v
```

## Scope and limits

- Source files are workbook extracts provided for coursework.
- This repo checks internal reproducibility, not publisher authenticity or release-vintage history.
- Wholesale and retail are reported separately and are not merged into one flow claim.
- Results are retrospective checks, not preregistered proof.

## Folder map

- `src/analysis.py`: data prep + matched evaluation
- `src/plot_results.py`: standalone charts
- `src/parse_cpca.py`: workbook parsing
- `src/model_validation.py`: brand-level parser utilities
- `tests/`: chronology and extraction checks
- `archive/v1/`: previous version kept for audit only
- `final_app/`: final offline dashboard

## Final milestone notes

Near-term priorities are still: source/vintage checks, a frozen incremental-signal test, and stronger brand-level outcome validation.
