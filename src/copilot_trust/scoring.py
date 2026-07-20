from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score,brier_score_loss,confusion_matrix,roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler
NUMERIC=["requests_per_active_day","unique_devices","unique_ips","acceptance_rate","injection_rate","policy_signal_rate","block_rate","overnight_share","quota_pressure","max_token_degree","max_payment_degree","max_device_degree","max_ip_degree","cadence_regularity","ip_missing_rate","device_missing_rate"]
CATEGORICAL=["plan","billing_status"]
def _choose_threshold(y,p,max_fpr=0.025):
    candidates=np.unique(np.quantile(p,np.linspace(0.55,0.995,120)));best=(0.5,-1.0)
    for t in candidates:
        pred=p>=t;tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel();fpr=fp/max(1,fp+tn);precision=tp/max(1,tp+fp);recall=tp/max(1,tp+fn);f1=2*precision*recall/max(1e-12,precision+recall)
        if fpr<=max_fpr and f1>best[1]:best=(float(t),f1)
    return best[0]
def _reason_codes(r):
    pairs=[("high_velocity",r.requests_per_active_day/80),("device_dispersion",r.unique_devices/8),("ip_dispersion",r.unique_ips/12),("shared_token",(r.max_token_degree-1)/3),("shared_payment",(r.max_payment_degree-1)/4),("shared_device",(r.max_device_degree-1)/4),("overnight_automation",r.overnight_share*2),("policy_signals",r.policy_signal_rate*8),("prompt_injection",r.injection_rate*8),("quota_pressure",r.quota_pressure*1.5),("regular_cadence",r.cadence_regularity*1.4)];pairs=sorted(pairs,key=lambda x:x[1],reverse=True)[:3];return "|".join(k for k,v in pairs if v>0.35) or "weak_multisignal_pattern"
def train_and_score(feature_csv: str|Path,out_dir: str|Path,seed:int=17):
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True);df=pd.read_csv(feature_csv);df["label"]=(df.ground_truth_abuse_type!="legitimate").astype(int);indices=np.arange(len(df));tr,te=train_test_split(indices,test_size=0.30,random_state=seed,stratify=df.label)
    pre=ColumnTransformer([("num",StandardScaler(),NUMERIC),("cat",OneHotEncoder(handle_unknown="ignore"),CATEGORICAL)]);clf=Pipeline([("pre",pre),("model",LogisticRegression(max_iter=1500,class_weight="balanced",C=0.7))]);clf.fit(df.loc[tr,NUMERIC+CATEGORICAL],df.loc[tr,"label"]);sup=clf.predict_proba(df[NUMERIC+CATEGORICAL])[:,1]
    scaler=StandardScaler();scaled_train=scaler.fit_transform(df.loc[tr,NUMERIC].fillna(0));iso=IsolationForest(n_estimators=180,contamination=0.10,random_state=seed);iso.fit(scaled_train);raw=-iso.score_samples(scaler.transform(df[NUMERIC].fillna(0)));anom=(raw-raw.min())/(raw.max()-raw.min()+1e-9);graph=np.maximum.reduce([np.clip((df.max_token_degree-1)/4,0,1),np.clip((df.max_payment_degree-1)/5,0,1),np.clip((df.max_device_degree-1)/5,0,1),np.clip((df.max_ip_degree-1)/7,0,1)]);risk=np.clip(0.68*sup+0.17*anom+0.15*graph,0,1);threshold=_choose_threshold(df.loc[tr,"label"].values,risk[tr],0.025)
    df["split"]="train";df.loc[te,"split"]="holdout";df["supervised_probability"]=sup;df["anomaly_score"]=anom;df["graph_signal"]=graph;df["risk_score"]=risk;df["flagged"]=(risk>=threshold).astype(int);df["reason_codes"]=df.apply(_reason_codes,axis=1);y=df.loc[te,"label"].values;p=risk[te];pred=(p>=threshold).astype(int);tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel();metrics={"roc_auc":float(roc_auc_score(y,p)),"average_precision":float(average_precision_score(y,p)),"brier_score":float(brier_score_loss(y,p)),"threshold":float(threshold),"precision":float(tp/max(1,tp+fp)),"recall":float(tp/max(1,tp+fn)),"false_positive_rate":float(fp/max(1,fp+tn)),"false_negative_rate":float(fn/max(1,fn+tp)),"flag_rate":float(pred.mean()),"test_accounts":int(len(te))}
    names=clf.named_steps["pre"].get_feature_names_out();coefs=clf.named_steps["model"].coef_[0];coef_df=pd.DataFrame({"feature":names,"coefficient":coefs});coef_df["abs_coefficient"]=coef_df.coefficient.abs();coef_df.sort_values("abs_coefficient",ascending=False).to_csv(out/"model_feature_coefficients.csv",index=False);holdout=df.loc[te].copy();rows=[]
    for behavior,g in holdout.groupby("ground_truth_abuse_type"):
        positive=behavior!="legitimate";rows.append({"benchmark_behavior":behavior,"n":len(g),"flag_rate":float(g.flagged.mean()),"mean_risk":float(g.risk_score.mean()),"miss_rate_if_abuse":float((1-g.flagged).mean()) if positive else np.nan,"false_positive_rate_if_legitimate":float(g.flagged.mean()) if not positive else np.nan})
    pd.DataFrame(rows).to_csv(out/"error_analysis_by_behavior.csv",index=False);df.to_csv(out/"account_risk_scores.csv",index=False);(out/"model_metrics.json").write_text(json.dumps(metrics,indent=2));return df,metrics
