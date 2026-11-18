# ChargeAhead (v1 midterm snapshot)

This is the original midterm version kept for traceability.

- Author: Keming Zhou
- Course: AIPI 590 Alternative Data
- Date: Oct 14, 2026

## What v1 tried to do

Build a powertrain transition index from CPCA + Baidu signals, then test whether search attention helps forecast short-term market movement.

## v1 package contents

- Monthly panel (2023-01 to 2026-08)
- Transition index and component diagnostics
- Lead-lag checks for channel signals
- Baseline forecast comparisons
- 42-keyword Baidu collection and composites
- Brand-level preview for 2026-03 to 2026-08

## Key v1 takeaways

- Transition index rose from 0.21 to 1.00 over the sample.
- Channel metrics tracked index levels reasonably well.
- Search signal helped some magnitude metrics in selected windows, but direction accuracy was mixed.
- Early brand-level patterns were suggestive but based on short windows.

## Why this folder is archived

v1 mixes some assumptions that were tightened in the final revision (target definition, comparable windows, protocol consistency). Keep this folder for audit and reproducibility, but use the main project path for current results.

## Running legacy scripts

```bash
python src/parse_cpca.py
python src/transition_index.py
python src/leadlag.py
python src/baseline.py
python src/baidu_index.py
python src/methodology.py
python src/ablation.py
python src/model_validation.py
python src/make_charts.py
python src/build_deck.py
```

Outputs are written under the v1 data/processed and figure/deck paths in this archive.
