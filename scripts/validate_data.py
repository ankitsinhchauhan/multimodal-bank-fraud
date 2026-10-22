import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
tx_path = ROOT/"data/structured/transactions_100k.csv"
event_path = ROOT/"data/semi_structured/transaction_events.jsonl"
complaint_path = ROOT/"data/unstructured/customer_complaints.jsonl"
out_path = ROOT/"reports/validation_report.json"
tx = pd.read_csv(tx_path)

checks = {
 "exactly_100k_transactions": len(tx)==100_000,
 "unique_transaction_ids": tx.transaction_id.is_unique,
 "no_missing_cells": not tx.isna().any().any(),
 "binary_fraud_label": set(tx.fraud_label.unique()).issubset({0,1}),
 "positive_amounts": bool((tx.amount>0).all()),
 "timestamps_parse": bool(pd.to_datetime(tx.timestamp,utc=True,errors="coerce").notna().all()),
 "parquet_exists": (ROOT/"data/structured/transactions_100k.parquet").exists()
}
events=bad_events=0
with event_path.open(encoding="utf-8") as f:
    for line in f:
        events += 1
        try:
            obj=json.loads(line)
            assert obj.get("transaction_id") and obj.get("event_time")
        except Exception:
            bad_events += 1
checks["events_match_transaction_count"] = events==len(tx)
checks["all_events_valid"] = bad_events==0

complaints=bad_complaints=0
with complaint_path.open(encoding="utf-8") as f:
    for line in f:
        complaints += 1
        try:
            obj=json.loads(line)
            assert obj.get("transaction_id") and obj.get("customer_message")
        except Exception:
            bad_complaints += 1
checks["complaints_valid"] = bad_complaints==0
checks["complaint_count_5000"] = complaints==5000

report={
 "checks":checks, "passed":sum(checks.values()), "total":len(checks),
 "transaction_rows":len(tx),"event_rows":events,"complaint_rows":complaints,
 "null_cells":int(tx.isna().sum().sum()),
 "duplicate_rows":int(tx.duplicated().sum()),
 "fraud_distribution":{str(k):int(v) for k,v in tx.fraud_label.value_counts().items()},
 "notice":"Integrity checks do not prove real-world statistical fidelity."
}
out_path.parent.mkdir(exist_ok=True)
out_path.write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
if not all(checks.values()):
    raise SystemExit("VALIDATION FAILED")
print("ALL VALIDATION CHECKS PASSED")
