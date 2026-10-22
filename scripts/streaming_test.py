"""Basic throughput/restart/retention helper notes and topic inspection."""
import argparse, json, time
from kafka import KafkaConsumer
p=argparse.ArgumentParser()
p.add_argument("--bootstrap",default="localhost:9092")
p.add_argument("--topic",default="bank-transactions")
p.add_argument("--seconds",type=int,default=15)
args=p.parse_args()
consumer=KafkaConsumer(args.topic,bootstrap_servers=args.bootstrap,
 auto_offset_reset="earliest",enable_auto_commit=False,
 consumer_timeout_ms=args.seconds*1000)
start=time.time(); count=0
try:
 for msg in consumer:
  count+=1
finally:
 consumer.close()
elapsed=max(time.time()-start,.001)
print(json.dumps({"messages_read":count,"elapsed_seconds":round(elapsed,2),
 "observed_messages_per_second":round(count/elapsed,2)},indent=2))
print("This is a read-throughput smoke test, not a benchmark.")
