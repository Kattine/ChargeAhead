from pathlib import Path
import json,pandas as pd
R=Path(__file__).resolve().parents[1];D=R/'data/processed'
def rows(n):return json.loads(pd.read_csv(D/(n+'.csv')).to_json(orient='records'))
data=dict(market=rows('national_panel_v2'),national=rows('forecast_metrics'),brands=rows('brand_panel_final'),metrics=rows('brand_metrics_final'),delay=rows('brand_metrics_delayed'),summary=json.loads((D/'brand_summary_final.json').read_text()))
(R/'final_app/index.html').write_text((R/'final_app/template.html').read_text().replace('__DATA__',json.dumps(data,ensure_ascii=False)))
