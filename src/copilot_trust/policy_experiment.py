from __future__ import annotations

from pathlib import Path
import hashlib
import json
import math
import numpy as np
import pandas as pd

ROLLOUT = pd.Timestamp("2026-05-06", tz="UTC")
ARMS = ("control", "shadow", "canary")


def _u(key: str) -> float:
    h = hashlib.sha256(key.encode()).hexdigest()[:12]
    return int(h, 16) / float(16**12 - 1)


class _UF:
    def __init__(self, ids): self.p = {x:x for x in ids}
    def find(self, x):
        if self.p[x] != x: self.p[x] = self.find(self.p[x])
        return self.p[x]
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb: self.p[max(ra,rb)] = min(ra,rb)


def _assignment(accounts: pd.DataFrame, t: pd.DataFrame, seed: int) -> tuple[pd.DataFrame,pd.DataFrame]:
    pre=t[t.timestamp<ROLLOUT].copy(); pre["event_date"]=pre.timestamp.dt.floor("D")
    agg=pre.groupby("account_id").agg(pre_requests=("request_id","size"),pre_active_days=("event_date","nunique"),pre_policy_signals=("content_policy_signal","sum"),pre_devices=("device_hash","nunique"),pre_ips=("ip_hash","nunique")).reset_index()
    agg["pre_requests_per_active_day"]=agg.pre_requests/agg.pre_active_days.clip(lower=1)
    agg["pre_policy_signal_rate"]=agg.pre_policy_signals/agg.pre_requests.clip(lower=1)
    base=accounts[["account_id","plan","region","org_id","managed_infrastructure"]].merge(agg,on="account_id",how="left").fillna(0)
    for c in ["pre_requests_per_active_day","pre_policy_signal_rate","pre_devices","pre_ips"]:
        base[c+"_pct"]=base[c].rank(pct=True,method="average")
    base["pre_eligibility_score"]=0.45*base.pre_requests_per_active_day_pct+0.25*base.pre_policy_signal_rate_pct+0.15*base.pre_devices_pct+0.15*base.pre_ips_pct
    cutoff=float(base.loc[base.pre_active_days>=5,"pre_eligibility_score"].quantile(0.45)) if (base.pre_active_days>=5).any() else 0
    base["eligible"]=((base.pre_active_days>=5)&(base.pre_eligibility_score>=cutoff)).astype(int)
    ids=base.loc[base.eligible.eq(1),"account_id"].tolist(); uf=_UF(ids)
    for _,m in base[base.eligible.eq(1)&base.org_id.astype(str).ne("0")&base.org_id.astype(str).ne("")].groupby("org_id").account_id.apply(list).items():
        for x in m[1:]: uf.union(m[0],x)
    pe=pre[pre.account_id.isin(ids)]
    for col in ["token_hash","payment_hash"]:
        groups=pe[pe[col].fillna("").ne("")].groupby(col).account_id.unique()
        for m in groups:
            m=list(m)
            if 2<=len(m)<=6:
                for x in m[1:]: uf.union(m[0],x)
    base["cluster_id"]=base.account_id.map(lambda x:f"cl_{uf.find(x)}" if x in uf.p else f"ineligible_{x}")
    e=base[base.eligible.eq(1)].copy()
    cl=e.groupby("cluster_id").agg(cluster_accounts=("account_id","nunique"),pre_score=("pre_eligibility_score","mean")).reset_index()
    cl["stratum"]=pd.qcut(cl.pre_score.rank(method="first"),q=min(3,max(1,len(cl))),labels=False,duplicates="drop").astype(str) if len(cl)>1 else "0"
    rng=np.random.default_rng(seed); pattern=np.array(["control","canary","shadow","control","canary","shadow","control","control","canary","shadow"],dtype=object); amap={}
    for _,g in cl.groupby("stratum"):
        arr=g.cluster_id.to_numpy().copy();rng.shuffle(arr)
        for j,cid in enumerate(arr):amap[str(cid)]=str(pattern[j%len(pattern)])
    cl["arm"]=cl.cluster_id.map(amap)
    # Exposure is assigned only after arm randomization and remains outcome/manifest blind.
    # Deterministic hash ranking gives an auditable ~80% canary exposure rate while preserving
    # at least one unexposed canary cluster when more than one canary cluster exists.
    cl["cluster_exposed"]=0
    canary_idx=cl.index[cl.arm.eq("canary")].tolist()
    ordered=sorted(canary_idx,key=lambda ix:_u(f"exp:{seed}:{cl.loc[ix,'cluster_id']}"))
    if len(ordered)==1:
        n_expose=1
    elif len(ordered)>1:
        n_expose=max(1,min(len(ordered)-1,int(round(0.80*len(ordered)))))
    else:
        n_expose=0
    if n_expose: cl.loc[ordered[:n_expose],"cluster_exposed"]=1
    a=e.merge(cl[["cluster_id","stratum","arm","cluster_exposed"]],on="cluster_id",how="left")
    a["assigned_canary"]=a.arm.eq("canary").astype(int);a["exposed"]=a.cluster_exposed.astype(int)
    a["weak_context_id"]=a.region.astype(str)+"|"+a.plan.astype(str)+"|"+a.account_id.map(lambda x:str(int(_u("ctx:"+x)*4)))
    ctx_canary=a.groupby("weak_context_id").assigned_canary.mean().rename("weak_context_canary_share");a=a.merge(ctx_canary,on="weak_context_id",how="left")
    pairs=[]
    for ip,m in pe[pe.ip_hash.fillna("").ne("")].groupby("ip_hash").account_id.unique().items():
        m=sorted(set(m))
        if 2<=len(m)<=10:
            for i in range(len(m)):
                for j in range(i+1,len(m)):pairs.append((m[i],m[j],ip))
    ip=pd.DataFrame(pairs,columns=["account_a","account_b","ip_context_hash"]) if pairs else pd.DataFrame(columns=["account_a","account_b","ip_context_hash"])
    return a,ip


def _panel(t:pd.DataFrame,a:pd.DataFrame)->pd.DataFrame:
    x=t[t.account_id.isin(a.account_id)].copy();x["event_date"]=x.timestamp.dt.floor("D");x["primary"]=x.model_family.eq("code_completion").astype(int);x["alt"]=x.model_family.isin(["chat","agent"]).astype(int)
    d=x.groupby(["account_id","event_date"]).agg(raw_requests=("request_id","size"),raw_primary=("primary","sum"),raw_alt=("alt","sum"),accepted=("completion_accepted","sum"),prompt_chars_mean=("prompt_chars","mean")).reset_index()
    dates=pd.date_range(x.event_date.min(),x.event_date.max(),freq="D",tz="UTC");idx=pd.MultiIndex.from_product([a.account_id,dates],names=["account_id","event_date"]);d=d.set_index(["account_id","event_date"]).reindex(idx).reset_index()
    for c in ["raw_requests","raw_primary","raw_alt","accepted"]:d[c]=d[c].fillna(0.0).astype(float)
    pre_prompt=x[x.timestamp<ROLLOUT].groupby("account_id").prompt_chars.mean().to_dict();d["prompt_chars_mean"]=d.apply(lambda r:float(r.prompt_chars_mean) if pd.notna(r.prompt_chars_mean) else float(pre_prompt.get(r.account_id,0.0)),axis=1)
    d=d.merge(a[["account_id","cluster_id","arm","exposed","plan","region","managed_infrastructure","weak_context_id","weak_context_canary_share"]],on="account_id",how="left");d["post"]=(d.event_date>=ROLLOUT).astype(int)
    return d


def _inject(panel:pd.DataFrame,a:pd.DataFrame,seed:int)->tuple[pd.DataFrame,pd.DataFrame]:
    out=panel.copy();out["primary_requests"]=out.raw_primary.astype(float);out["alternate_surface_requests"]=out.raw_alt.astype(float);out["acceptance_rate"]=out.accepted/out.raw_requests.clip(lower=1);out["migration_inflow"]=0.0
    meta=a.set_index("account_id");manifest=[];targets={}
    for acc in meta.index:
        responder=int(_u(f"resp:{seed}:{acc}")<0.72);direct=(0.28+0.12*_u(f"strength:{seed}:{acc}")) if responder else 0.0
        mig=0.18 if (responder and _u(f"mig:{seed}:{acc}")<0.55) else 0.0
        exposed=int(meta.loc[acc,"arm"]=="canary" and meta.loc[acc,"exposed"]==1)
        cand=meta[(meta.weak_context_id==meta.loc[acc,"weak_context_id"])&(meta.arm!="canary")].index.tolist() if exposed and mig>0 else []
        if not cand and exposed and mig>0:cand=meta[(meta.region==meta.loc[acc,"region"])&(meta.arm!="canary")].index.tolist()
        target=sorted(cand)[int(_u(f"target:{seed}:{acc}")*len(cand))%len(cand)] if cand else None;targets[acc]=target
        manifest.append({"account_id":acc,"true_responder":responder,"hidden_response_fraction":direct,"injected_primary_fraction_reduction":direct if exposed else 0.0,"injected_alt_displacement_fraction":0.45 if (responder and exposed) else 0.0,"injected_neighbor_migration_fraction":mig if exposed else 0.0,"migration_target_account":target or "","manifest_boundary":"benchmark only; never used by assignment or effect estimation"})
    adds=[];mm=pd.DataFrame(manifest).set_index("account_id")
    for acc in meta.index:
        mask=out.account_id.eq(acc)&out.post.eq(1)&out.arm.eq("canary")&out.exposed.eq(1);direct=float(mm.loc[acc,"injected_primary_fraction_reduction"])
        if not mask.any():continue
        if direct>0:
            orig=out.loc[mask,"primary_requests"].copy();removed=orig*direct;out.loc[mask,"primary_requests"]=orig-removed;out.loc[mask,"alternate_surface_requests"]+=removed*0.45;out.loc[mask,"acceptance_rate"]=(out.loc[mask,"acceptance_rate"]-0.008).clip(lower=0)
            target=targets.get(acc);mig=float(mm.loc[acc,"injected_neighbor_migration_fraction"])
            if target and mig>0:
                for date,amount in zip(out.loc[mask,"event_date"],removed*mig):adds.append((target,date,float(amount)))
        else:out.loc[mask,"acceptance_rate"]=(out.loc[mask,"acceptance_rate"]-0.004).clip(lower=0)
    if adds:
        ad=pd.DataFrame(adds,columns=["account_id","event_date","migration_inflow"]).groupby(["account_id","event_date"],as_index=False).migration_inflow.sum();out=out.drop(columns="migration_inflow").merge(ad,on=["account_id","event_date"],how="left");out["migration_inflow"]=out.migration_inflow.fillna(0.0)
    out["total_requests"]=out.primary_requests+out.alternate_surface_requests+out.migration_inflow
    return out.drop(columns=["raw_requests","raw_primary","raw_alt","accepted"]),pd.DataFrame(manifest)


def _changes(p:pd.DataFrame,outcome:str,upto=None,ids=None)->pd.DataFrame:
    d=p if ids is None else p[p.account_id.isin(ids)]
    if upto is not None:d=d[d.event_date<=upto]
    pre=d[d.post.eq(0)].groupby(["cluster_id","arm"])[outcome].mean().rename("pre");post=d[d.post.eq(1)].groupby(["cluster_id","arm"])[outcome].mean().rename("post");z=pd.concat([pre,post],axis=1).dropna().reset_index();z["change"]=z.post-z.pre;return z


def _effect(p:pd.DataFrame,outcome:str,treated="canary",control="control",upto=None,ids=None)->dict:
    z=_changes(p,outcome,upto,ids);t=z[z.arm.eq(treated)].change.to_numpy(float);c=z[z.arm.eq(control)].change.to_numpy(float);est=float(t.mean()-c.mean()) if len(t) and len(c) else np.nan;se=float(math.sqrt((np.var(t,ddof=1)/len(t) if len(t)>1 else 0)+(np.var(c,ddof=1)/len(c) if len(c)>1 else 0))) if len(t) and len(c) else np.nan
    return {"estimate":est,"se":se,"ci95_low":est-1.96*se if np.isfinite(se) else np.nan,"ci95_high":est+1.96*se if np.isfinite(se) else np.nan,"n_treated_clusters":int(len(t)),"n_control_clusters":int(len(c))}


def _pretrend(p):
    d=p[p.post.eq(0)].groupby(["event_date","arm"]).total_requests.mean().unstack();rows=[]
    for arm in ARMS:
        y=d[arm].dropna().to_numpy(float) if arm in d else np.array([]);s=float(np.polyfit(np.arange(len(y)),y,1)[0]) if len(y)>=2 else np.nan;rows.append({"arm":arm,"pretrend_slope":s})
    o=pd.DataFrame(rows);ctl=float(o.loc[o.arm.eq("control"),"pretrend_slope"].iloc[0]);o["slope_gap_vs_control"]=o.pretrend_slope-ctl;o["diagnostic_status"]=np.where(o.slope_gap_vs_control.abs()<=0.15,"within_diagnostic_tolerance","review_parallel_trend_risk");return o


def _hte(p):
    rows=[]
    for col in ["plan","managed_infrastructure","region"]:
        for v in sorted(p[col].dropna().unique(),key=str):
            e=_effect(p,"total_requests",ids=set(p.loc[p[col].eq(v),"account_id"].unique()));rows.append({"slice_type":col,"slice_value":v,**e,"reportable":int(e["n_treated_clusters"]>=3 and e["n_control_clusters"]>=3),"interpretation":"diagnostic heterogeneity; do not promote slice-specific policy without multiplicity/evidence review"})
    return pd.DataFrame(rows)


def _sequential(p):
    maxd=p.event_date.max();cps=[];d=ROLLOUT+pd.Timedelta(days=6)
    while d<=maxd:cps.append(d);d+=pd.Timedelta(days=7)
    if not cps or cps[-1]<maxd:cps.append(maxd)
    rows=[]
    for i,cp in enumerate(cps,1):
        pri=_effect(p,"primary_requests",upto=cp);tot=_effect(p,"total_requests",upto=cp);alt=_effect(p,"alternate_surface_requests",upto=cp);acc=_effect(p,"acceptance_rate",upto=cp);neg=_effect(p,"prompt_chars_mean",upto=cp);ratio=max(0,alt["estimate"])/max(1e-9,-pri["estimate"]) if np.isfinite(pri["estimate"]) and pri["estimate"]<0 and np.isfinite(alt["estimate"]) else np.nan;lo=pri["estimate"]-2.58*pri["se"] if np.isfinite(pri["se"]) else np.nan;hi=pri["estimate"]+2.58*pri["se"] if np.isfinite(pri["se"]) else np.nan
        user_harm=bool(np.isfinite(acc["estimate"]) and acc["estimate"]<-0.03 and np.isfinite(acc["ci95_high"]) and acc["ci95_high"]<0)
        action="rollback_to_shadow_user_impact_guardrail" if user_harm else "pause_and_review_displacement" if np.isfinite(ratio) and ratio>0.60 else "continue_canary_collect_evidence" if np.isfinite(hi) and hi<0 else "hold_canary_collect_more_evidence"
        rows.append({"look":i,"checkpoint":cp.date().isoformat(),"primary_itt":pri["estimate"],"primary_monitor_99_low":lo,"primary_monitor_99_high":hi,"total_requests_itt":tot["estimate"],"alternate_surface_itt":alt["estimate"],"acceptance_rate_itt":acc["estimate"],"negative_control_prompt_chars_itt":neg["estimate"],"displacement_ratio":ratio,"recommended_action":action,"sequential_boundary":"conservative 99% descriptive monitoring; human review required; not formal alpha-spending proof"})
    return pd.DataFrame(rows)


def _reviews(data,a):
    r=pd.read_csv(data/"reviews.csv");r["review_date"]=pd.to_datetime(r.review_date,utc=True,format="mixed");r=r[r.review_date>=ROLLOUT].merge(a[["account_id","arm"]],on="account_id",how="inner");rows=[]
    for arm in ARMS:
        g=r[r.arm.eq(arm)];enf=g[g.enforcement_action.ne("none")];ap=enf[enf.appeal_filed.eq(1)];rows.append({"arm":arm,"matured_reviews":len(g),"cleared_rate":float(g.final_outcome.eq("cleared").mean()) if len(g) else np.nan,"enforcement_rate":float(g.enforcement_action.ne("none").mean()) if len(g) else np.nan,"appeal_rate_among_enforced":float(enf.appeal_filed.mean()) if len(enf) else np.nan,"overturn_rate_among_appeals":float(ap.appeal_outcome.eq("overturned").mean()) if len(ap) else np.nan,"evidence_status":"reportable" if len(g)>=5 else "limited_matured_review_evidence"})
    return pd.DataFrame(rows)


def evaluate_policy_experiment(data_dir:str|Path,out_dir:str|Path,seed:int=17)->dict:
    data=Path(data_dir);out=Path(out_dir);out.mkdir(parents=True,exist_ok=True);accounts=pd.read_csv(data/"accounts.csv");t=pd.read_csv(data/"telemetry.csv");t["timestamp"]=pd.to_datetime(t.timestamp,utc=True,format="mixed")
    a,ip=_assignment(accounts,t,seed);p=_panel(t,a);p,manifest=_inject(p,a,seed);manifest.to_csv(data/"hidden_policy_experiment_manifest.csv",index=False)
    amap=a.set_index("account_id").arm.to_dict()
    if len(ip):ip["arm_a"]=ip.account_a.map(amap);ip["arm_b"]=ip.account_b.map(amap);ip=ip.dropna(subset=["arm_a","arm_b"]);ip["cross_arm"]=ip.arm_a.ne(ip.arm_b).astype(int)
    weak_groups=a.groupby("weak_context_id").arm.agg(lambda s:len(set(s))).reset_index(name="arm_count");cross_groups=int((weak_groups.arm_count>1).sum())
    interference=pd.DataFrame([{"network":"strong_org_token_payment_cluster","pairs_or_links":int(a.cluster_id.nunique()),"cross_arm_links":0,"cross_arm_share":0.0,"identity_boundary":"cluster randomization unit; still not an enforcement identity verdict"},{"network":"ip_context_neighbors","pairs_or_links":int(len(ip)),"cross_arm_links":int(ip.cross_arm.sum()) if len(ip) else 0,"cross_arm_share":float(ip.cross_arm.mean()) if len(ip) else 0.0,"identity_boundary":"IP context only; never proves common control; used only for spillover sensitivity"},{"network":"weak_region_plan_context","pairs_or_links":int(len(weak_groups)),"cross_arm_links":cross_groups,"cross_arm_share":cross_groups/max(1,len(weak_groups)),"identity_boundary":"broad context neighborhood only; never proves common control; used for migration/spillover sensitivity"}])
    pri=_effect(p,"primary_requests");tot=_effect(p,"total_requests");alt=_effect(p,"alternate_surface_requests");acc=_effect(p,"acceptance_rate");neg=_effect(p,"prompt_chars_mean");placebo=_effect(p,"total_requests",treated="shadow");exposure=float(a.loc[a.arm.eq("canary"),"exposed"].mean());att=pri["estimate"]/exposure if exposure>0 else np.nan;ratio=max(0,alt["estimate"])/max(1e-9,-pri["estimate"]) if np.isfinite(pri["estimate"]) and pri["estimate"]<0 else np.nan
    effects=pd.DataFrame([
        {"estimand":"ITT_canary_vs_control","outcome":"primary_requests",**{k:pri[k] for k in ["estimate","ci95_low","ci95_high","n_treated_clusters","n_control_clusters"]},"interpretation":"cluster-randomized synthetic ITT; assignment and eligibility use pre-rollout data only"},
        {"estimand":"Wald_ATT_style","outcome":"primary_requests","estimate":att,"ci95_low":pri["ci95_low"]/exposure if exposure>0 else np.nan,"ci95_high":pri["ci95_high"]/exposure if exposure>0 else np.nan,"n_treated_clusters":pri["n_treated_clusters"],"n_control_clusters":pri["n_control_clusters"],"interpretation":"ITT divided by canary exposure rate; exclusion/monotonicity-style assumptions; diagnostic only"},
        {"estimand":"ITT_canary_vs_control","outcome":"total_requests",**{k:tot[k] for k in ["estimate","ci95_low","ci95_high","n_treated_clusters","n_control_clusters"]},"interpretation":"net behavior after within-account displacement and synthetic migration inflow"},
        {"estimand":"ITT_canary_vs_control","outcome":"alternate_surface_requests",**{k:alt[k] for k in ["estimate","ci95_low","ci95_high","n_treated_clusters","n_control_clusters"]},"interpretation":"positive movement can indicate displacement rather than true harm reduction"},
        {"estimand":"ITT_canary_vs_control","outcome":"acceptance_rate_guardrail",**{k:acc[k] for k in ["estimate","ci95_low","ci95_high","n_treated_clusters","n_control_clusters"]},"interpretation":"user-experience guardrail; material negative movement blocks widening"},
        {"estimand":"negative_control_ITT","outcome":"prompt_chars_mean",**{k:neg[k] for k in ["estimate","ci95_low","ci95_high","n_treated_clusters","n_control_clusters"]},"interpretation":"negative-control diagnostic; material movement suggests imbalance/misspecification"},
        {"estimand":"shadow_placebo_vs_control","outcome":"total_requests",**{k:placebo[k] for k in ["estimate","ci95_low","ci95_high","n_treated_clusters","n_control_clusters"]},"interpretation":"shadow has no user-facing treatment; material effect is a randomization/pretrend warning"}
    ])
    pre=_pretrend(p);hte=_hte(p);seq=_sequential(p);rev=_reviews(data,a);can=rev[rev.arm.eq("canary")].iloc[0];reasons=[]
    if np.isfinite(acc["estimate"]) and acc["estimate"]<-0.03 and np.isfinite(acc["ci95_high"]) and acc["ci95_high"]<0:reasons.append("acceptance_rate_harm")
    if np.isfinite(ratio) and ratio>0.60:reasons.append("high_behavior_displacement")
    if pre.loc[pre.arm.eq("canary"),"diagnostic_status"].eq("review_parallel_trend_risk").any():reasons.append("pretrend_risk")
    if int(can.matured_reviews)>=5 and float(can.cleared_rate)>0.35:reasons.append("high_matured_clearance_rate")
    state="rollback_or_pause_to_shadow_for_review" if reasons else "continue_limited_canary_collect_matured_evidence" if np.isfinite(pri["ci95_high"]) and pri["ci95_high"]<0 else "hold_current_canary_collect_more_evidence"
    stop={"recommended_state":state,"guardrail_reasons":reasons,"primary_itt":pri["estimate"],"primary_itt_ci95":[pri["ci95_low"],pri["ci95_high"]],"exposure_rate_canary":exposure,"wald_att_style":att,"displacement_ratio":ratio,"automatic_policy_expansion_allowed":False,"decision_boundary":"human policy-owner review required; sequential diagnostics never auto-expand or auto-enforce"}
    exposed_resp=manifest[(manifest.true_responder.eq(1))&(manifest.injected_primary_fraction_reduction>0)];bench={"hidden_manifest_present":True,"manifest_used_by_assignment":False,"manifest_used_by_effect_estimation":False,"eligible_accounts":len(a),"randomization_clusters":a.cluster_id.nunique(),"canary_exposure_rate":exposure,"hidden_responders":int(manifest.true_responder.sum()),"hidden_exposed_responders":len(exposed_resp),"hidden_migration_sources":int(manifest.injected_neighbor_migration_fraction.gt(0).sum()),"estimated_primary_itt":pri["estimate"],"estimated_total_itt":tot["estimate"],"benchmark_boundary":"hidden responder/migration manifest is benchmark-only and never used by assignment, estimation, HTE, or stopping-rule calculations"}
    a.to_csv(out/"policy_experiment_assignment.csv",index=False);p.to_csv(out/"policy_experiment_daily_outcomes.csv",index=False);effects.to_csv(out/"policy_experiment_effect_summary.csv",index=False);pre.to_csv(out/"policy_experiment_pretrend.csv",index=False);hte.to_csv(out/"policy_experiment_heterogeneous_effects.csv",index=False);seq.to_csv(out/"policy_experiment_sequential_monitor.csv",index=False);interference.to_csv(out/"policy_experiment_interference_audit.csv",index=False);rev.to_csv(out/"policy_experiment_review_guardrails.csv",index=False);(out/"policy_experiment_stopping_decision.json").write_text(json.dumps(stop,indent=2));(out/"policy_experiment_benchmark.json").write_text(json.dumps(bench,indent=2))
    return {"assignment":a,"effects":effects,"pretrend":pre,"hte":hte,"sequential":seq,"interference":interference,"reviews":rev,"stopping":stop,"benchmark":bench}
