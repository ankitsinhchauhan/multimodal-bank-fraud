# Demo Runbook (Day 5)

## Start
1. Open Ubuntu WSL and `cd ~/multimodal-bank-fraud`.
2. `source .venv/bin/activate`
3. `docker compose up -d kafka`
4. Verify topic: `docker exec -it bank-fraud-kafka kafka-topics --bootstrap-server localhost:9092 --list`
5. Start streaming in Terminal A: `spark-submit scripts/streaming_pipeline.py`
6. Start producer in Terminal B: `python scripts/stream_producer.py --rate 100 --limit 10000`
7. Run batch ETL: `spark-submit scripts/batch_pipeline.py`
8. Run ML/statistics: `spark-submit scripts/train_model.py` and `python scripts/statistical_analysis.py`
9. Run quality/monitoring: `python scripts/validate_data.py`; `python scripts/monitoring.py`
10. Start dashboard: `streamlit run dashboard/app.py --server.address 0.0.0.0`

## Stop
- Stop foreground jobs with Ctrl+C.
- `docker compose down` stops Kafka but retains its named data volume.
- `docker compose down -v` deletes Kafka persisted demo data (destructive).

## Restart/checkpoint test
- Keep `checkpoints/kafka_window/` and `data/streaming/window_results/`.
- Stop streaming with Ctrl+C; restart the same command.
- Record logs and compare output counts. Do not claim universal exactly-once semantics.

## Evidence for presentation
- `reports/validation_report.json`
- `reports/batch_summary.json`
- `reports/model_metrics.json`
- `reports/statistical_report.json`
- `reports/monitoring_snapshot.json`
- Dashboard screenshots and Kafka topic description
