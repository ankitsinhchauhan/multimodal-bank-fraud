"""Generate synthetic banking demo data. All records are fictional."""
import json, random
from pathlib import Path
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
from faker import Faker
from sdv.metadata import SingleTableMetadata
from sdv.single_table import CTGANSynthesizer

SEED = 42
SEED_ROWS = 2000
FINAL_ROWS = 100_000
CUSTOMER_COUNT = 10_000
COMPLAINT_COUNT = 5_000
random.seed(SEED); np.random.seed(SEED); Faker.seed(SEED)
fake = Faker("en_IN")

ROOT = Path(__file__).resolve().parents[1]
RAW, STRUCTURED = ROOT/"data/raw", ROOT/"data/structured"
SEMI, UNSTRUCTURED, REPORTS = ROOT/"data/semi_structured", ROOT/"data/unstructured", ROOT/"reports"
for p in [RAW, STRUCTURED, SEMI, UNSTRUCTURED, REPORTS]: p.mkdir(parents=True, exist_ok=True)

print("[1/6] Creating fictional customer master...")
customers = pd.DataFrame({
    "customer_id": [f"C{i:06d}" for i in range(1, CUSTOMER_COUNT+1)],
    "customer_name": [fake.name() for _ in range(CUSTOMER_COUNT)],
    "email": [f"customer{i}@example.test" for i in range(1, CUSTOMER_COUNT+1)],
    "city": np.random.choice(["Ahmedabad","Mumbai","Delhi","Surat","Bengaluru","Pune","Jaipur","Hyderabad"], CUSTOMER_COUNT),
    "account_type": np.random.choice(["Savings","Current","Salary"], CUSTOMER_COUNT)
})
customers.to_csv(STRUCTURED/"customers.csv", index=False)

def seed_row():
    amount = min(float(np.random.lognormal(7.4, 1.0)), 250000.0)
    return {
        "amount": round(max(1.0, amount), 2),
        "transaction_type": random.choice(["UPI","Card","Online","ATM","BankTransfer"]),
        "merchant_category": random.choice(["Grocery","Fuel","Electronics","Travel","Restaurant","Healthcare","Shopping","Utilities"]),
        "payment_method": random.choice(["DebitCard","CreditCard","UPI","NetBanking"]),
        "location": random.choice(["Ahmedabad","Mumbai","Delhi","Surat","Bengaluru","Pune","Jaipur","Hyderabad"]),
        "device_os": random.choice(["Android","iOS","Windows","Linux"]),
        "hour": random.randint(0,23),
        "account_balance": round(float(np.random.lognormal(10.3,1.0)),2),
        "transactions_last_5min": random.choices([0,1,2,3,4,5,6], weights=[15,25,25,18,10,5,2])[0],
        "is_international": random.choice([0,1])
    }

print("[2/6] Creating seed data and fitting CTGAN (can take time)...")
seed = pd.DataFrame([seed_row() for _ in range(SEED_ROWS)])
seed.to_csv(RAW/"seed_transactions.csv", index=False)
metadata = SingleTableMetadata()
metadata.detect_from_dataframe(data=seed)
for col in ["transaction_type","merchant_category","payment_method","location","device_os","is_international"]:
    metadata.update_column(column_name=col, sdtype="categorical")
synth = CTGANSynthesizer(metadata, epochs=50, verbose=True)
synth.fit(seed)
tx = synth.sample(num_rows=FINAL_ROWS)

print("[3/6] Normalizing fields and adding synthetic IDs/timestamps...")
for col, default, low, high in [
    ("amount",100,1,500000), ("account_balance",1000,0,10_000_000)
]:
    tx[col] = pd.to_numeric(tx[col], errors="coerce").fillna(default).clip(low,high).round(2)
for col, default, low, high in [
    ("hour",12,0,23), ("transactions_last_5min",0,0,100), ("is_international",0,0,1)
]:
    tx[col] = pd.to_numeric(tx[col], errors="coerce").fillna(default).round().clip(low,high).astype(int)

start = datetime(2026,1,1,tzinfo=timezone.utc)
end = datetime(2026,10,9,tzinfo=timezone.utc)
seconds = int((end-start).total_seconds())
tx["timestamp"] = [(start+timedelta(seconds=random.randint(0,seconds))).isoformat() for _ in range(FINAL_ROWS)]
tx.insert(0,"transaction_id",[f"TX{i:07d}" for i in range(1,FINAL_ROWS+1)])
tx.insert(1,"customer_id",[f"C{i:06d}" for i in np.random.randint(1,CUSTOMER_COUNT+1,size=FINAL_ROWS)])
tx["device_id"] = [f"D{random.randint(1,20000):06d}" for _ in range(FINAL_ROWS)]

# Transparent rule-derived simulated label, not verified ground truth.
tx["fraud_label"] = (
    (tx["amount"] >= 75000)
    | (tx["transactions_last_5min"] >= 5)
    | ((tx["is_international"] == 1) & (tx["transaction_type"] == "Online") & (tx["amount"] >= 25000))
    | ((tx["amount"] > tx["account_balance"]) & (tx["amount"] >= 15000))
).astype(int)
cols = ["transaction_id","customer_id","timestamp","amount","transaction_type","merchant_category",
        "payment_method","location","device_id","device_os","hour","account_balance",
        "transactions_last_5min","is_international","fraud_label"]
tx = tx[cols]
tx.to_csv(STRUCTURED/"transactions_100k.csv", index=False)
tx.to_parquet(STRUCTURED/"transactions_100k.parquet", index=False)
print(f"Created {len(tx):,} transaction rows; simulated fraud rate={tx.fraud_label.mean():.2%}")

print("[4/6] Creating JSONL event records...")
with (SEMI/"transaction_events.jsonl").open("w",encoding="utf-8") as f:
    for r in tx.to_dict("records"):
        event = {
            "event_id": "EVT_"+r["transaction_id"], "event_type":"transaction_created",
            "transaction_id":r["transaction_id"], "customer_id":r["customer_id"],
            "event_time":r["timestamp"], "amount":float(r["amount"]),
            "device":{"device_id":r["device_id"],"os":r["device_os"]},
            "transaction":{"type":r["transaction_type"],"merchant_category":r["merchant_category"],
                           "payment_method":r["payment_method"]},
            "location":r["location"], "fraud_label":int(r["fraud_label"])
        }
        f.write(json.dumps(event)+"\n")

print("[5/6] Creating complaint text records...")
templates = [
 "I do not recognize this transaction. Please investigate.",
 "I received a transaction notification that I did not expect.",
 "Please review this payment and confirm whether it was authorized.",
 "I believe this payment may be suspicious. Please contact me.",
 "I am reporting an unfamiliar transaction on my account.",
 "Please help me understand why this transaction was processed."
]
sample = tx.sample(n=min(COMPLAINT_COUNT,len(tx)), random_state=SEED)
with (UNSTRUCTURED/"customer_complaints.jsonl").open("w",encoding="utf-8") as f:
    for i,r in enumerate(sample.to_dict("records"),1):
        f.write(json.dumps({
            "complaint_id":f"CMP{i:07d}", "transaction_id":r["transaction_id"],
            "customer_message":random.choice(templates),
            "channel":random.choice(["MobileApp","Email","CallCenter","Web"]),
            "created_at":datetime.now(timezone.utc).isoformat()
        })+"\n")

print("[6/6] Writing generation report...")
report = {
 "expected_transactions":FINAL_ROWS, "actual_transactions":int(len(tx)),
 "unique_transaction_ids":int(tx.transaction_id.nunique()),
 "null_cells":int(tx.isna().sum().sum()), "duplicate_rows":int(tx.duplicated().sum()),
 "fraud_label_distribution":{str(k):int(v) for k,v in tx.fraud_label.value_counts().items()},
 "notice":"Entirely synthetic demonstration data. Labels are rule-derived, not real fraud outcomes."
}
(REPORTS/"generation_report.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
print("DATA GENERATION COMPLETE")
