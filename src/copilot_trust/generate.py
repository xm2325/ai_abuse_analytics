from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

ABUSE_TYPES = ["legitimate","scripted_automation","credential_sharing","quota_evasion","token_misuse","coordinated_abuse","policy_abuse"]

@lru_cache(maxsize=None)
def _hash(prefix: str, value: str) -> str:
    return hashlib.sha256(f"{prefix}:{value}".encode()).hexdigest()[:16]

@dataclass
class SyntheticConfig:
    n_accounts: int = 4500
    start: str = "2026-04-01"
    days: int = 56
    seed: int = 17

def _legitimate_profiles(rng: np.random.Generator, abuse: np.ndarray) -> np.ndarray:
    profiles=np.full(len(abuse),"not_applicable",dtype=object); legit_idx=np.where(abuse=="legitimate")[0]; draws=rng.random(len(legit_idx)); special=draws<0.12; profiles[legit_idx]="standard"
    if special.any(): profiles[legit_idx[special]]=rng.choice(["power_user","shared_enterprise","security_research"],size=int(special.sum()),p=[0.45,0.35,0.20])
    return profiles

def generate_synthetic_telemetry(out_dir: str | Path, cfg: SyntheticConfig = SyntheticConfig()) -> dict[str,Path]:
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True); rng=np.random.default_rng(cfg.seed); start=pd.Timestamp(cfg.start,tz="UTC")
    account_ids=[f"acct_{i:06d}" for i in range(cfg.n_accounts)]; created_offsets=rng.integers(0,240,size=cfg.n_accounts); created_at=start-pd.to_timedelta(created_offsets,unit="D")
    regions=rng.choice(["UK","EU","US","CA","APAC"],size=cfg.n_accounts,p=[0.22,0.22,0.30,0.10,0.16]); plans=rng.choice(["free","individual","business","enterprise"],size=cfg.n_accounts,p=[0.20,0.34,0.28,0.18]); org_ids=["" if p in {"free","individual"} else f"org_{rng.integers(0,900):05d}" for p in plans]
    abuse=np.array(["legitimate"]*cfg.n_accounts,dtype=object); candidate_idx=rng.choice(cfg.n_accounts,size=max(1,int(cfg.n_accounts*0.105)),replace=False); abuse[candidate_idx]=rng.choice(ABUSE_TYPES[1:],size=len(candidate_idx),p=[0.25,0.18,0.18,0.12,0.15,0.12]); legitimate_profile=_legitimate_profiles(rng,abuse)
    billing_status=np.where(rng.random(cfg.n_accounts)<0.965,"active","past_due"); managed_infrastructure=((plans=="enterprise")|(plans=="business")|(legitimate_profile=="shared_enterprise")).astype(int)
    accounts=pd.DataFrame({"account_id":account_ids,"created_at":created_at.astype(str),"region":regions,"plan":plans,"org_id":org_ids,"billing_status":billing_status,"managed_infrastructure":managed_infrastructure,"legitimate_profile":legitimate_profile,"ground_truth_abuse_type":abuse})
    events=[]; mitigation_day=start+pd.Timedelta(days=35); emerging_campaign_day=start+pd.Timedelta(days=46)
    for i,row in accounts.iterrows():
        kind=row.ground_truth_abuse_type; legit_profile=row.legitimate_profile; base_rate={"free":5,"individual":10,"business":15,"enterprise":19}[row.plan]; stealth=bool(kind!="legitimate" and rng.random()<0.22); n_days_active=int(rng.integers(12,cfg.days+1)); active_days=np.sort(rng.choice(cfg.days,size=n_days_active,replace=False))
        home_devices=[f"dev_{i:06d}_{j}" for j in range(int(rng.integers(1,4)))]; home_ips=[f"ip_{i:06d}_{j}" for j in range(int(rng.integers(1,5)))]; pay=f"pay_{i:06d}"; token=f"tok_{i:06d}"
        if kind=="credential_sharing": home_devices=[f"dev_{i:06d}_share_{j}" for j in range(int(rng.integers(5,10)))]; home_ips=[f"ip_{i:06d}_share_{j}" for j in range(int(rng.integers(7,17)))]
        if legit_profile=="shared_enterprise": home_devices=[f"dev_{i:06d}_corp_{j}" for j in range(int(rng.integers(4,8)))]; home_ips=[f"corp_ip_{i%12:02d}"]+[f"ip_{i:06d}_corp_{j}" for j in range(int(rng.integers(2,5)))]
        if kind=="token_misuse": token=f"shared_token_{i%18:02d}"
        if kind=="coordinated_abuse":
            cluster=i%16; home_devices=[f"coord_dev_{cluster:02d}",f"dev_{i:06d}_coord"]; home_ips=[f"coord_ip_{cluster:02d}",f"ip_{i:06d}_coord"]; pay=f"coord_pay_{cluster:02d}"
        if kind=="quota_evasion": pay=f"evasion_pay_{i%35:02d}"; home_devices=[f"evasion_dev_{i%35:02d}",f"dev_{i:06d}_evasion"]
        for d in active_days:
            day=start+pd.Timedelta(days=int(d)); lam=float(base_rate)
            if kind=="scripted_automation": lam*=2.5 if stealth else 3.8
            elif kind in {"quota_evasion","token_misuse","coordinated_abuse"}: lam*=1.35 if stealth else 2.0
            elif kind=="policy_abuse": lam*=1.1 if stealth else 1.35
            if legit_profile=="power_user": lam*=2.5
            if day>=mitigation_day and kind in {"scripted_automation","quota_evasion"}: lam*=0.55
            emerging_campaign=day>=emerging_campaign_day and kind in {"coordinated_abuse","policy_abuse"}
            if emerging_campaign: lam*=2.1
            n=max(1,rng.poisson(lam))
            if kind=="scripted_automation" and not stealth: seconds=np.clip(np.arange(n)*max(20,86400//max(n,1))+rng.normal(0,25,n),0,86399)
            else:
                hours=np.clip(rng.normal(14,4,n),0,23.9); seconds=hours*3600+rng.uniform(0,3599,n)
            for s in seconds:
                ts=day+pd.Timedelta(seconds=float(s)); device=rng.choice(home_devices); ip=rng.choice(home_ips); prompt_len=int(np.clip(rng.lognormal(5.2,0.75),15,12000)); completion_len=int(np.clip(rng.lognormal(5.0,0.7),10,9000)); accepted=rng.random()<(0.43 if kind=="scripted_automation" else 0.57)
                inj_base=0.035 if legit_profile=="security_research" else 0.004; pol_base=0.030 if legit_profile=="security_research" else 0.007; inj_prob=(0.055 if stealth else 0.085) if kind=="policy_abuse" else inj_base; policy_prob=(0.080 if stealth else 0.125) if kind=="policy_abuse" else pol_base
                if emerging_campaign and kind=="policy_abuse": inj_prob=min(0.35,inj_prob*2.8); policy_prob=min(0.45,policy_prob*2.5)
                inj=rng.random()<inj_prob; policy=rng.random()<policy_prob; blocked=bool((inj or policy) and rng.random()<0.70); model_probs=[0.20,0.30,0.50] if emerging_campaign else [0.45,0.40,0.15]
                events.append({"request_id":f"req_{len(events):09d}","timestamp":ts.isoformat(),"account_id":row.account_id,"device_hash":_hash("device",str(device)),"ip_hash":_hash("ip",str(ip)),"payment_hash":_hash("payment",str(pay)),"token_hash":_hash("token",str(token)),"model_family":rng.choice(["code_completion","chat","agent"],p=model_probs),"prompt_chars":prompt_len,"completion_chars":completion_len,"completion_accepted":int(accepted),"prompt_injection_signal":int(inj),"content_policy_signal":int(policy),"safety_blocked":int(blocked),"entitlement_limit":{"free":50,"individual":300,"business":600,"enterprise":900}[row.plan]})
    events_df=pd.DataFrame(events); event_ts=pd.to_datetime(events_df["timestamp"],utc=True,format="mixed"); miss_ip=rng.random(len(events_df))<0.015; miss_device=rng.random(len(events_df))<0.008; incident_days={(start+pd.Timedelta(days=42)).date(),(start+pd.Timedelta(days=43)).date()}; incident_mask=event_ts.dt.date.isin(incident_days)&(rng.random(len(events_df))<0.22); events_df.loc[miss_ip|incident_mask,"ip_hash"]=""; events_df.loc[miss_device,"device_hash"]=""
    abuse_accounts=accounts.loc[accounts.ground_truth_abuse_type!="legitimate","account_id"].tolist(); legit_pool=accounts.loc[accounts.ground_truth_abuse_type=="legitimate","account_id"].tolist(); legit_sample_n=min(max(8,int(cfg.n_accounts*0.045)),len(legit_pool)); review_accounts=abuse_accounts+rng.choice(legit_pool,size=legit_sample_n,replace=False).tolist(); review_rows=[]; forced_overturn_used=False
    for j,acc in enumerate(review_accounts):
        account_row=accounts.loc[accounts.account_id==acc].iloc[0]; gt=account_row.ground_truth_abuse_type; is_abuse=gt!="legitimate"; forced=bool((not is_abuse) and (not forced_overturn_used)); forced_overturn_used=forced_overturn_used or forced; confirmed=True if forced else bool(rng.random()<(0.90 if is_abuse else 0.055)); review_day=28 if forced else int(rng.integers(24,cfg.days)); review_date=start+pd.Timedelta(days=review_day,hours=int(rng.integers(0,24))); action=rng.choice(["warning","rate_limit","suspend"],p=[0.28,0.38,0.34]) if confirmed else "none"; appeal_filed=True if forced else bool(confirmed and rng.random()<(0.60 if not is_abuse else 0.17))
        if appeal_filed: overturned=True if forced else bool(rng.random()<(0.76 if not is_abuse else 0.05)); appeal_outcome="overturned" if overturned else "upheld"
        else: appeal_outcome="not_applicable"; overturned=False
        final_outcome="cleared" if (not confirmed or overturned) else "confirmed_abuse"; review_rows.append({"investigation_id":f"inv_{j:06d}","account_id":acc,"review_date":review_date.isoformat(),"review_outcome":"confirmed_abuse" if confirmed else "cleared","enforcement_action":action,"appeal_filed":int(appeal_filed),"appeal_outcome":appeal_outcome,"final_outcome":final_outcome,"decision_latency_hours":float(np.clip(rng.lognormal(2.4,0.65),0.5,120)),"taxonomy_version":"2.0","policy_version":"synthetic-policy-2026-05"})
    reviews=pd.DataFrame(review_rows); paths={"accounts":out/"accounts.csv","telemetry":out/"telemetry.csv","reviews":out/"reviews.csv"}; accounts.to_csv(paths["accounts"],index=False); events_df.to_csv(paths["telemetry"],index=False); reviews.to_csv(paths["reviews"],index=False); return paths
