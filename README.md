# ChargeAhead

ChargeAhead began with a car buyer’s concern: as the powertrain market changes, what could that mean for the car they own? 
I built a data pipeline and tested whether search attention adds information about market changes. The final outcome is a working dashboard that shows both the market and the evidence behind the signal. The results are mixed, and the product makes that visible.
 

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

The dashboard is running on local with three views:

Rebuild steps:

```bash
python -m src.brand_analysis
python -m src.export_audit
python -m src.build_dashboard
python -m unittest discover -s tests -v
```

## Scope and limits

- Source files are workbook extracts provided for coursework.
- This repo checks internal reproducibility.
- Wholesale and retail are reported separately and are not merged into one flow claim.
- Results are retrospective checks, not preregistered proof.

## Acknowledgments

Parts of the code in this repository were drafted and refined with assistance from copilot, and reviewed/tested by the author.



## Folder map

- `src/analysis.py`: data prep + matched evaluation
- `src/plot_results.py`: standalone charts
- `src/parse_cpca.py`: workbook parsing
- `src/model_validation.py`: brand-level parser utilities
- `tests/`: chronology and extraction checks
- `archive/v1/`: previous version kept for audit only
- `final_app/`: final offline dashboard

The tool this repo delivered can analyze the market, compare forecasts, and check evidence. 

Key Takeaway：A change in search popularity is different from it improving forecast accuracy.

