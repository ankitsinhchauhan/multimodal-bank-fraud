"""Member 2: send JSONL records to Kafka at a controllable rate."""
import argparse, json, time
from pathlib import Path
from kafka import KafkaProducer
from kafka.errors import KafkaError

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument("--bootstrap",default="localhost:9092")
parser.add_argument("--topic",default="bank-transactions")
parser.add_argument("--rate",type=float,default=100.0,help="events per second")
parser.add_argument("--limit",type=int,default=0,help="0 means all events")
args=parser.parse_args()
producer=KafkaProducer(
 bootstrap_servers=args.bootstrap,
 value_serializer=lambda x: json.dumps(x).encode("utf-8"),
 key_serializer=lambda x: x.encode("utf-8"),
 acks="all", retries=5, linger_ms=10
)
path=ROOT/"data/semi_structured/transaction_events.jsonl"
sent=0; started=time.time()
with path.open(encoding="utf-8") as f:
 for line in f:
  event=json.loads(line)
  producer.send(args.topic,key=event["transaction_id"],value=event)
  sent+=1
  if sent % 1000==0:
   producer.flush()
   elapsed=max(time.time()-started,0.001)
   print(f"sent={sent}, avg_rate={sent/elapsed:.1f} events/sec")
  if args.limit and sent>=args.limit: break
  if args.rate>0: time.sleep(1.0/args.rate)
producer.flush(timeout=30)
producer.close()
elapsed=max(time.time()-started,0.001)
print(f"Finished: sent={sent}, seconds={elapsed:.2f}, average={sent/elapsed:.2f} events/sec")
