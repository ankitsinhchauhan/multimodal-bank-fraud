"""Member 1: Spark batch ETL, schema checks, partitioned Parquet output."""
from pathlib import Path
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import *

ROOT = Path(__file__).resolve().parents[1]
INPUT = str(ROOT/"data/structured/transactions_100k.csv")
OUTPUT = str(ROOT/"data/processed/transactions_parquet")
REPORTS = ROOT/"reports"
REPORTS.mkdir(exist_ok=True)

schema = StructType([
 StructField("transaction_id",StringType(),False),
 StructField("customer_id",StringType(),False),
 StructField("timestamp",StringType(),True),
 StructField("amount",DoubleType(),True),
 StructField("transaction_type",StringType(),True),
 StructField("merchant_category",StringType(),True),
 StructField("payment_method",StringType(),True),
 StructField("location",StringType(),True),
 StructField("device_id",StringType(),True),
 StructField("device_os",StringType(),True),
 StructField("hour",IntegerType(),True),
 StructField("account_balance",DoubleType(),True),
 StructField("transactions_last_5min",IntegerType(),True),
 StructField("is_international",IntegerType(),True),
 StructField("fraud_label",IntegerType(),True),
])

#spark = SparkSession.builder.appName("BankFraudBatchETL").getOrCreate()
spark = (
    SparkSession.builder
    .appName("BankFraudBatchETL")
    .config("spark.master", "local[*]")
    .config("spark.hadoop.fs.defaultFS", "file:///")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")
raw = spark.read.option("header",True).schema(schema).csv(INPUT)
input_count = raw.count()
clean = (raw.dropDuplicates(["transaction_id"])
 .withColumn("timestamp",F.to_timestamp("timestamp"))
 .withColumn("amount",F.col("amount").cast("double"))
 .withColumn("account_balance",F.col("account_balance").cast("double"))
 .filter(F.col("transaction_id").isNotNull())
 .filter(F.col("customer_id").isNotNull())
 .filter(F.col("amount").isNotNull() & (F.col("amount") > 0))
 .filter(F.col("fraud_label").isin(0,1))
 .withColumn("event_date",F.to_date("timestamp"))
 .withColumn("amount_band",
   F.when(F.col("amount") < 1000,"LOW")
    .when(F.col("amount") < 10000,"MEDIUM")
    .when(F.col("amount") < 75000,"HIGH").otherwise("VERY_HIGH"))
)
output_count = clean.count()
(clean.repartition("event_date")
 .write.mode("overwrite")
 .partitionBy("event_date")
 .parquet(OUTPUT))
summary = clean.agg(
 F.count("*").alias("rows"),
 F.round(F.avg("amount"),2).alias("mean_amount"),
 F.round(F.expr("percentile_approx(amount, 0.5)"),2).alias("median_amount"),
 F.round(F.stddev("amount"),2).alias("stddev_amount"),
 F.sum("fraud_label").alias("simulated_fraud_count")
).toPandas()
summary.to_json(REPORTS/"batch_summary.json",orient="records",indent=2)
print(f"Input rows: {input_count}; cleaned output rows: {output_count}")
print(f"Partitioned Parquet output: {OUTPUT}")
summary.show if False else None
spark.stop()
