"""Statistical analytics for the synthetic dataset."""
import json
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency, ttest_ind, pearsonr

ROOT=Path(__file__).resolve().parents[1]
df=pd.read_csv(ROOT/"data/structured/transactions_100k.csv")
out=ROOT/"reports"; out.mkdir(exist_ok=True)
normal=df.loc[df.fraud_label==0,"amount"].dropna()
fraud=df.loc[df.fraud_label==1,"amount"].dropna()
mean=float(df.amount.mean()); sd=float(df.amount.std(ddof=1))
z=((df.amount-mean)/sd).replace([np.inf,-np.inf],np.nan)
q1,q3=df.amount.quantile([.25,.75]); iqr=q3-q1
table=pd.crosstab(df.transaction_type,df.fraud_label)
chi2,p,dof,expected=chi2_contingency(table)
tt=ttest_ind(normal,fraud,equal_var=False) if len(normal)>1 and len(fraud)>1 else None
# Approximate 95% CI for overall mean (large sample normal approximation).
se=sd/np.sqrt(len(df))
report={
 "descriptive":{
  "count":int(df.amount.count()),"mean":mean,"median":float(df.amount.median()),
  "mode":float(df.amount.mode().iloc[0]),"stddev":sd,"variance":float(df.amount.var()),
  "p95":float(df.amount.quantile(.95)),"p99":float(df.amount.quantile(.99)),
  "mean_95_ci":[mean-1.96*se,mean+1.96*se]
 },
 "exploratory":{
  "iqr":float(iqr),"lower_fence":float(q1-1.5*iqr),"upper_fence":float(q3+1.5*iqr),
  "zscore_abs_gt_3_count":int((z.abs()>3).sum())
 },
 "diagnostic":{
  "transaction_type_by_label":table.to_dict(),
  "chi_square_statistic":float(chi2),"chi_square_p_value":float(p),"degrees_of_freedom":int(dof),
  "amount_label_correlation":float(df[["amount","fraud_label"]].corr().iloc[0,1])
 },
 "hypothesis_test":{
  "H0":"Mean transaction amount is equal in the two simulated label groups.",
  "welch_t_statistic":float(tt.statistic) if tt else None,
  "p_value":float(tt.pvalue) if tt else None,
  "warning":"These tests describe rule-generated synthetic labels and do not establish causality."
 }
}
(out/"statistical_report.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
