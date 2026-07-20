from __future__ import annotations

from pathlib import Path
import pandas as pd


def _metrics(g: pd.DataFrame,pred: pd.Series)->dict:
    y=g.label.astype(int); pred=pred.astype(bool); tp=int(((y==1)&pred).sum()); fp=int(((y==0)&pred).sum()); tn=int(((y==0)&~pred).sum()); fn=int(((y==1)&~pred).sum())
    return {"accounts_triggered":int(pred.sum()),"review_workload_share":float(pred.mean()),"precision":tp/max(1,tp+fp),"recall":tp/max(1,tp+fn),"false_positive_rate":fp/max(1,fp+tn),"legitimate_confounder_hits":int((pred&g.legitimate_profile.isin(["power_user","shared_enterprise","security_research"])).sum())}

def evaluate_shadow_rules(scores: pd.DataFrame,out_dir: str|Path)->pd.DataFrame:
    frames=[]
    for scope,g in [("development",scores.loc[scores.split.eq("train")].copy()),("holdout",scores.loc[scores.split.eq("holdout")].copy())]:
        velocity_cut=float(g.requests_per_active_day.quantile(0.75)); quota_cut=float(g.quota_pressure.quantile(0.75)); candidates={"identity_dispersion_multisignal":(g.unique_devices>=5)&(g.unique_ips>=7),"shared_token_multisignal":(g.max_token_degree>=2)&((g.risk_score>=0.45)|(g.max_device_degree>=2)),"scripted_usage_multisignal":(g.requests_per_active_day>=velocity_cut)&(g.cadence_regularity>=0.48)&(g.overnight_share>=0.07),"quota_evasion_multisignal":(g.quota_pressure>=quota_cut)&((g.max_payment_degree>=2)|(g.max_device_degree>=2)),"policy_signal_escalation":(g.policy_signal_rate>=0.03)|((g.policy_signal_rate>=0.015)&(g.injection_rate>=0.015))}
        for name,pred in candidates.items(): frames.append({"rule_name":name,"evaluation_scope":scope,"accounts_evaluated":len(g),**_metrics(g,pred)})
    out=pd.DataFrame(frames); holdout=out[out.evaluation_scope.eq("holdout")].set_index("rule_name"); recommendations={}
    for rule,r in holdout.iterrows(): recommendations[rule]="insufficient_holdout_volume" if r.accounts_triggered<3 else "candidate_for_review_queue" if r.precision>=0.70 and r.false_positive_rate<=0.05 else "keep_in_shadow"
    out["recommendation"]=out.rule_name.map(recommendations); out["enforcement_boundary"]="human investigation only; never auto-enforce from this rule"; out=out.sort_values(["rule_name","evaluation_scope"]); Path(out_dir).mkdir(parents=True,exist_ok=True); out.to_csv(Path(out_dir)/"rule_shadow_evaluation.csv",index=False); return out
