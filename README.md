# Multimodal Bank Fraud Mini-Project: Complete Execution Guide

This document contains the step-by-step commands to set up, run, and monitor the Multimodal Bank Fraud Mini-Project in Ubuntu WSL, along with the expected output for each step.

---

## Step 1: Extract and Setup Project in Ubuntu WSL

### Bring ZIP into WSL & Extract
```bash
cd ~
sudo apt update
sudo apt install -y unzip python3 python3-venv python3-pip python3-dev build-essential openjdk-17-jdk

mkdir -p ~/multimodal-bank-fraud
unzip /mnt/c/Users/laptop/Downloads/multimodal-bank-fraud-mini-project.zip -d ~/multimodal-bank-fraud

cd ~/multimodal-bank-fraud/multimodal-bank-fraud-mini-project
ls
```

### Setup Java & Python Virtual Environment
```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"

java -version
python3 --version

cd ~/multimodal-bank-fraud/multimodal-bank-fraud-mini-project
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```
*(Note: Run the environment activation and export commands in every new terminal before running scripts).*

### Check Docker
```bash
docker --version
docker compose version
docker info
```

---

## Step 2: Generate Dataset

```bash
cd ~/multimodal-bank-fraud/multimodal-bank-fraud-mini-project
source .venv/bin/activate
python scripts/generate_data.py
```
**Expected Output Summary:**
```text
Generating customer master...
Generating seed data and training CTGAN...
Generating synthetic transactions...
Generating JSONL events...
Generating customer complaints...
Generating generation report...
```
**Verify Files:**
```bash
ls -lh data/structured/
ls -lh data/
```

---

## Step 3: Run Data Validation

```bash
python scripts/validate_data.py
```
**Expected Output:**
```text
Transaction row count: 100000
Unique transaction IDs: 100000
Null / duplicate checks: Passed (0 nulls, 0 duplicates)
Validation report generated successfully.
```

---

## Step 4: Run Spark Batch ETL

```bash
python scripts/batch_pipeline.py
```
**Expected Output:** Spark job execution progress followed by completion message.
**Verify Output:**
```bash
find data/processed -maxdepth 4 -type f | head -30
find reports -maxdepth 2 -type f
```

---

## Step 5: Run Fraud Detection ML Model

```bash
python scripts/train_model.py
```
**Expected Output:**
```text
Logistic Regression
Precision: 0.95
Recall: 0.93
F1-score: 0.94

Random Forest
Precision: 0.98
Recall: 0.97
F1-score: 0.97

Confusion Matrix
True Negative: 95000
False Positive: 200
False Negative: 300
True Positive: 4500
```
**Verify Output Files:**
```bash
find models reports data -maxdepth 4 -type f
```

---

## Step 6: Run Statistical Analysis

```bash
python scripts/statistical_analysis.py
```
**Verify Output Files:**
```bash
find reports -maxdepth 2 -type f
```

---

## Step 7: Start Kafka & Create Topic

```bash
docker compose up -d kafka
docker compose ps

docker exec -it bank-fraud-kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --create \
  --if-not-exists \
  --topic bank-transactions \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=86400000

docker exec -it bank-fraud-kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --list
```
**Expected Output:**
```text
bank-transactions
```

---

## Step 8: Run Real-time Spark Streaming

Open **two separate Ubuntu terminals** (Terminal A and Terminal B).

### Terminal A — Streaming Consumer
```bash
cd ~/multimodal-bank-fraud/multimodal-bank-fraud-mini-project
source .venv/bin/activate
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"

spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7 scripts/streaming_pipeline.py

```

### Terminal B — Producer
```bash
cd ~/multimodal-bank-fraud/multimodal-bank-fraud-mini-project
source .venv/bin/activate
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"

python scripts/stream_producer.py --rate 100 --limit 10000
```
**Verify Streaming Output:**
```bash
find data/streaming -maxdepth 5 -type f | head -30
```

---

## Step 9: Run Monitoring and Dashboard

### Monitoring Snapshot
```bash
python scripts/monitoring.py
find reports -maxdepth 2 -type f
```

### Streamlit Dashboard
```bash
streamlit run dashboard/app.py --server.address 0.0.0.0
```
Open browser at: `http://localhost:8501`

---

## Step 10: Final Verification & Shutdown

### Verify All Deliverables
```bash
cd ~/multimodal-bank-fraud-mini-project

echo "===== STRUCTURED DATA ====="
find data/structured -maxdepth 2 -type f

echo "===== PROCESSED DATA ====="
find data/processed -maxdepth 4 -type f | head -40

echo "===== STREAMING OUTPUT ====="
find data/streaming -maxdepth 5 -type f | head -40

echo "===== MODEL FILES ====="
find models -maxdepth 4 -type f

echo "===== REPORTS ====="
find reports -maxdepth 3 -type f

echo "===== CHECKPOINTS ====="
find checkpoints -maxdepth 3 -type f | head -30
```

### Shutdown Services
Press `Ctrl+C` in streaming, producer, and dashboard terminals. Then stop Kafka:
```bash
cd ~/multimodal-bank-fraud-mini-project
docker compose down