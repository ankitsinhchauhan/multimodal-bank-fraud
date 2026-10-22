"""Member 3: Spark MLlib models and evaluation report."""
import json
from pathlib import Path
from pyspark.sql import SparkSession, functions as F
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler
from pyspark.ml.classification import LogisticRegression, RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator

ROOT=Path(__file__).resolve().parents[1]
INPUT = (ROOT / "data/structured/transactions_100k.csv").resolve().as_uri()
MODEL_DIR=str(ROOT/"models/fraud_random_forest")
REPORTS=ROOT/"reports"; REPORTS.mkdir(exist_ok=True)
spark=SparkSession.builder.appName("BankFraudMLlib").getOrCreate()
spark.sparkContext.setLogLevel("WARN")
df=spark.read.option("header",True).option("inferSchema",True).csv(INPUT)
df=df.withColumn("label",F.col("fraud_label").cast("double"))
categorical=["transaction_type","merchant_category","payment_method","location","device_os"]
numeric=["amount","account_balance","hour","transactions_last_5min","is_international"]
indexers=[StringIndexer(inputCol=c,outputCol=c+"_idx",handleInvalid="keep") for c in categorical]
encoder=OneHotEncoder(inputCols=[c+"_idx" for c in categorical],outputCols=[c+"_vec" for c in categorical])
assembler=VectorAssembler(inputCols=numeric+[c+"_vec" for c in categorical],outputCol="features",handleInvalid="keep")
train,test=df.randomSplit([0.8,0.2],seed=42)

results={}
for name,clf in [
 ("logistic_regression",LogisticRegression(featuresCol="features",labelCol="label",maxIter=30)),
 ("random_forest",RandomForestClassifier(featuresCol="features",labelCol="label",numTrees=60,maxDepth=8,seed=42))
]:
    pipeline=Pipeline(stages=indexers+[encoder,assembler,clf])
    model=pipeline.fit(train)
    pred=model.transform(test)
    evaluator=BinaryClassificationEvaluator(labelCol="label",rawPredictionCol="rawPrediction",metricName="areaUnderROC")
    multi=MulticlassClassificationEvaluator(labelCol="label",predictionCol="prediction")
    cm=pred.groupBy("label","prediction").count().collect()
    confusion={f"actual_{int(r['label'])}_predicted_{int(r['prediction'])}":int(r["count"]) for r in cm}
    results[name]={
      "roc_auc":float(evaluator.evaluate(pred)),
      "accuracy":float(multi.evaluate(pred, {multi.metricName:"accuracy"})),
      "precision_weighted":float(multi.evaluate(pred, {multi.metricName:"weightedPrecision"})),
      "recall_weighted":float(multi.evaluate(pred, {multi.metricName:"weightedRecall"})),
      "f1_weighted":float(multi.evaluate(pred, {multi.metricName:"f1"})),
      "confusion_counts":confusion
    }
    if name=="random_forest":
        model.write().overwrite().save(MODEL_DIR)
        (pred.select("transaction_id","label","prediction","probability")
         .withColumn("fraud_probability",F.udf(lambda v: float(v[1]),"double")("probability"))
         .select("transaction_id","label","prediction","fraud_probability")
         .write.mode("overwrite").option("header",True).csv(str(ROOT/"data/processed/predictions_csv")))
report={
 "models":results,
 "train_rows":train.count(),"test_rows":test.count(),
 "label_notice":"Labels are synthetic rule-derived labels; scores measure agreement with those rules, not real-bank fraud performance.",
 "risk_thresholds":{"LOW":"0.00-0.29","MEDIUM":"0.30-0.59","HIGH":"0.60-0.79","CRITICAL":"0.80-1.00"}
}
(REPORTS/"model_metrics.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
spark.stop()
