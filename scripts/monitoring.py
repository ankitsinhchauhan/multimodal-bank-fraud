"""Write a lightweight system/pipeline monitoring snapshot."""
import json, time, subprocess
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
report={"timestamp_epoch":time.time(),"checks":{}}
tx=ROOT/"data/structured/transactions_100k.csv"
report["checks"]["transactions_csv_exists"]=tx.exists()
if tx.exists():
 df=pd.read_csv(tx)
 report["transaction_rows"]=len(df)
 report["null_cells"]=int(df.isna().sum().sum())
 report["fraud_rate"]=float(df.fraud_label.mean())
 report["amount_mean"]=float(df.amount.mean())
for rel in ["reports/validation_report.json","reports/model_metrics.json","data/streaming/window_results"]:
 report["checks"][rel.replace("/","_")+"_exists"]=(ROOT/rel).exists()
(ROOT/"reports/monitoring_snapshot.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
