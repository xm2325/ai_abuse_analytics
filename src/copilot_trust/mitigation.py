from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

def _slope(y: pd.Series)->float:
    if len(y)<2:return 0.0
    x=np.arange(len(y),dtype=float); return float(np.polyfit(x,y.astype(float).to_numpy(),1)[0])

def evaluate_mitigation(data_dir: str|Path,out_dir: str|Path,seed:int=17,bootstrap_reps:int=300)->tuple[pd.DataFrame,pd.DataFrame]:
    data_dir=Path(data_dir);out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True);t=pd.read_csv(data_dir/"telemetry.csv");a=pd.read_csv(data_dir/"accounts.csv");t["timestamp"]=pd.to_datetime(t.timestamp,utc=True,format="mixed");t["event_date"]=t.timestamp.dt.floor("D");cutoff=pd.Timestamp("2026-05-06",tz="UTC")
    account_meta=a[["account_id","ground_truth_abuse_type"]].copy();account_meta["treated"]=account_meta.ground_truth_abuse_type.isin(["scripted_automation","quota_evasion"]).astype(int);dates=pd.date_range(t.event_date.min(),t.event_date.max(),freq="D",tz="UTC");panel_index=pd.MultiIndex.from_product([account_meta.account_id,dates],names=["account_id","event_date"]);counts=t.groupby(["account_id","event_date"]).size().rename("requests");panel=counts.reindex(panel_index,fill_value=0).reset_index().merge(account_meta,on="account_id",how="left");panel["post"]=(panel.event_date>=cutoff).astype(int)
    means=panel.groupby(["treated","post"]).requests.mean().unstack(fill_value=0);did=float((means.loc[1,1]-means.loc[1,0])-(means.loc[0,1]-means.loc[0,0]));pre_daily=panel[panel.post.eq(0)].groupby(["event_date","treated"]).requests.mean().unstack();treated_pre_slope=_slope(pre_daily[1]) if 1 in pre_daily else 0.0;control_pre_slope=_slope(pre_daily[0]) if 0 in pre_daily else 0.0;pretrend_gap=treated_pre_slope-control_pre_slope
    rng=np.random.default_rng(seed);account_changes=panel.groupby(["account_id","treated","post"]).requests.mean().unstack(fill_value=0).reset_index();account_changes["change"]=account_changes.get(1,0)-account_changes.get(0,0);tr=account_changes.loc[account_changes.treated.eq(1),"change"].to_numpy();ct=account_changes.loc[account_changes.treated.eq(0),"change"].to_numpy();boot=[]
    if len(tr) and len(ct):
        for _ in range(bootstrap_reps):boot.append(float(rng.choice(tr,size=len(tr),replace=True).mean()-rng.choice(ct,size=len(ct),replace=True).mean()))
    ci_low,ci_high=(float(np.quantile(boot,0.025)),float(np.quantile(boot,0.975))) if boot else (np.nan,np.nan);daily=panel.groupby(["event_date","treated"]).requests.mean().unstack(fill_value=0).reset_index().rename(columns={0:"comparison_mean_requests",1:"treated_mean_requests"});daily["post"]=(daily.event_date>=cutoff).astype(int);daily.to_csv(out_dir/"mitigation_daily_panel.csv",index=False)
    summary=pd.DataFrame([{"cutoff":cutoff.date().isoformat(),"treated_pre_mean_account_day_requests":float(means.loc[1,0]),"treated_post_mean_account_day_requests":float(means.loc[1,1]),"control_pre_mean_account_day_requests":float(means.loc[0,0]),"control_post_mean_account_day_requests":float(means.loc[0,1]),"did_account_day_requests":did,"bootstrap_95_ci_low":ci_low,"bootstrap_95_ci_high":ci_high,"treated_pretrend_slope":treated_pre_slope,"control_pretrend_slope":control_pre_slope,"pretrend_slope_gap":pretrend_gap,"interpretation":"synthetic DiD-style diagnostic; assignment is not randomized and this is not causal proof"}]);summary.to_csv(out_dir/"mitigation_evaluation.csv",index=False);return summary,daily
