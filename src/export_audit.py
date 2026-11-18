from pathlib import Path
import openpyxl,pandas as pd
R=Path(__file__).resolve().parents[1];out=[]
for year,header in [(2025,91),(2026,67)]:
 w=openpyxl.load_workbook(R/f'data/raw/cpca_{year}.xlsx',data_only=True).active
 for row in range(header+1,header+10):
  name=w.cell(row,1).value
  if not name or '===' in str(name):break
  for month in range(1,13 if year==2025 else 9):
   v=w.cell(row,month+1).value
   out.append(dict(manufacturer=name,month=f'{year}-{month:02d}-01',exports_units=v if isinstance(v,(int,float)) else None,source_file=f'cpca_{year}.xlsx',source_row=row,source_column=month+1))
pd.DataFrame(out).to_csv(R/'data/processed/export_coverage_final.csv',index=False)
