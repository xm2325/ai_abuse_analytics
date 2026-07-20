from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


def evaluate_slices(scores: pd.DataFrame, out_dir: str | Path) -> pd.DataFrame:
    eval_df = scores.loc[scores["split"].eq("holdout")].copy() if "split" in scores.columns else scores.copy()
    rows = []
    for col in ["plan", "region", "managed_infrastructure", "legitimate_profile"]:
        if col not in eval_df.columns:
            continue
        for val, g in eval_df.groupby(col, dropna=False):
            y = g.label.values
            pred = g.flagged.values
            tp = int(((y == 1) & (pred == 1)).sum())
            fp = int(((y == 0) & (pred == 1)).sum())
            tn = int(((y == 0) & (pred == 0)).sum())
            fn = int(((y == 1) & (pred == 0)).sum())
            rows.append({"slice_type":col,"slice_value":str(val),"n":len(g),"positives":int((y==1).sum()),"negatives":int((y==0).sum()),"reportable":int(len(g)>=10 and int((y==0).sum())>=5),"precision":tp/max(1,tp+fp),"recall":tp/max(1,tp+fn),"false_positive_rate":fp/max(1,fp+tn),"false_negative_rate":fn/max(1,fn+tp),"flag_rate":float(pred.mean())})
    out = pd.DataFrame(rows)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out.to_csv(Path(out_dir)/"slice_metrics.csv",index=False)
    return out


def data_quality_report(data_dir: str | Path, out_dir: str | Path) -> pd.DataFrame:
    t = pd.read_csv(Path(data_dir)/"telemetry.csv",keep_default_na=False)
    cols=["device_hash","ip_hash","payment_hash","token_hash","prompt_chars","completion_chars","prompt_injection_signal","content_policy_signal"]
    rows=[]
    for c in cols:
        missing=(t[c].astype(str).eq("")|t[c].isna()).mean()
        rows.append({"signal":c,"coverage":1-float(missing),"missing_rate":float(missing),"recommended_action":"instrument source and alert on coverage regression" if missing>0.01 else "monitor"})
    q=pd.DataFrame(rows); Path(out_dir).mkdir(parents=True,exist_ok=True); q.to_csv(Path(out_dir)/"signal_coverage.csv",index=False); return q


def review_capacity_analysis(scores: pd.DataFrame, out_dir: str | Path) -> pd.DataFrame:
    eval_df=scores.loc[scores["split"].eq("holdout")].copy() if "split" in scores.columns else scores.copy(); eval_df=eval_df.sort_values("risk_score",ascending=False).reset_index(drop=True)
    rows=[]; positives=max(1,int(eval_df.label.sum()))
    for share in [0.01,0.02,0.05,0.10,0.15,0.20,0.30]:
        k=max(1,int(round(len(eval_df)*share))); reviewed=eval_df.head(k); tp=int(reviewed.label.sum())
        rows.append({"review_capacity_share":share,"accounts_reviewed":k,"precision_at_capacity":tp/max(1,k),"known_abuse_recall_at_capacity":tp/positives,"false_positive_reviews":k-tp})
    out=pd.DataFrame(rows); Path(out_dir).mkdir(parents=True,exist_ok=True); out.to_csv(Path(out_dir)/"review_capacity_scenarios.csv",index=False); return out
