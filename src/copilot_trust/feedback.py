from __future__ import annotations

from pathlib import Path
import pandas as pd


def evaluate_review_feedback(scores: pd.DataFrame, data_dir: str | Path, out_dir: str | Path, label_maturity_days: int = 7) -> tuple[pd.DataFrame,pd.DataFrame]:
    data_dir=Path(data_dir); out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    reviews=pd.read_csv(data_dir/"reviews.csv"); reviews["review_date"]=pd.to_datetime(reviews.review_date,utc=True,format="mixed"); benchmark_end=reviews.review_date.max().normalize()+pd.Timedelta(days=1); reviews["label_age_days"]=(benchmark_end-reviews.review_date).dt.total_seconds()/86400; reviews["matured_label"]=reviews.label_age_days>=label_maturity_days
    joined=reviews.merge(scores[["account_id","risk_score","reason_codes","plan","region","legitimate_profile"]],on="account_id",how="left"); joined["final_confirmed"]=joined.final_outcome.eq("confirmed_abuse").astype(int); joined["risk_band"]=pd.cut(joined.risk_score,bins=[-0.001,0.25,0.50,0.70,0.85,1.001],labels=["very_low","low","medium","high","very_high"])
    matured=joined[joined.matured_label].copy(); rows=[]
    for scope,group_col in [("overall",None),("risk_band","risk_band"),("plan","plan")]:
        groups=[("all",matured)] if group_col is None else matured.groupby(group_col,observed=True)
        for value,g in groups:
            if len(g)==0: continue
            enforced=g.enforcement_action.ne("none"); appeals=g.appeal_filed.eq(1)
            rows.append({"scope":scope,"value":str(value),"matured_reviews":int(len(g)),"final_confirmation_rate":float(g.final_confirmed.mean()),"enforcement_rate":float(enforced.mean()),"appeal_rate_among_enforced":float(g.loc[enforced,"appeal_filed"].mean()) if enforced.any() else 0.0,"overturn_rate_among_appeals":float(g.loc[appeals,"appeal_outcome"].eq("overturned").mean()) if appeals.any() else 0.0,"median_decision_latency_hours":float(g.decision_latency_hours.median())})
    metrics=pd.DataFrame(rows)
    safety=matured.groupby(["plan","enforcement_action"],dropna=False).agg(reviews=("investigation_id","count"),appeal_rate=("appeal_filed","mean"),final_confirmation_rate=("final_confirmed","mean"),median_latency_hours=("decision_latency_hours","median")).reset_index()
    appealed=matured[matured.appeal_filed.eq(1)]; overturn=appealed.groupby(["plan","enforcement_action"])["appeal_outcome"].apply(lambda s:s.eq("overturned").mean()).rename("overturn_rate").reset_index(); safety=safety.merge(overturn,on=["plan","enforcement_action"],how="left").fillna({"overturn_rate":0.0})
    joined.to_csv(out_dir/"review_feedback_joined.csv",index=False); metrics.to_csv(out_dir/"review_feedback_metrics.csv",index=False); safety.to_csv(out_dir/"enforcement_safety_metrics.csv",index=False); return metrics,safety
