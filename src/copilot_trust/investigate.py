from __future__ import annotations
from pathlib import Path
import pandas as pd

def build_investigation_queue(scores:pd.DataFrame,data_dir:str|Path,out_dir:str|Path,top_n:int=30)->pd.DataFrame:
    out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True);t=pd.read_csv(Path(data_dir)/"telemetry.csv",keep_default_na=False);t["timestamp"]=pd.to_datetime(t.timestamp,utc=True,format="mixed");queue=scores.sort_values("risk_score",ascending=False).head(top_n).copy();queue_cols=["account_id","risk_score","flagged","reason_codes","plan","region","managed_infrastructure","legitimate_profile","requests_per_active_day","unique_devices","unique_ips","max_token_degree","max_payment_degree","policy_signal_rate","injection_rate","cadence_regularity","overnight_share"];queue[queue_cols].to_csv(out_dir/"investigation_queue.csv",index=False)
    case_dir=out_dir/"cases";case_dir.mkdir(exist_ok=True);timeline_rows=[]
    for _,r in queue.head(10).iterrows():
        g=t[t.account_id==r.account_id].copy().sort_values("timestamp");g["event_date"]=g.timestamp.dt.date.astype(str);daily=g.groupby("event_date").agg(requests=("request_id","count"),devices=("device_hash",lambda s:s[s.ne("")].nunique()),ips=("ip_hash",lambda s:s[s.ne("")].nunique()),injection_rate=("prompt_injection_signal","mean"),policy_rate=("content_policy_signal","mean"),block_rate=("safety_blocked","mean")).reset_index();daily["account_id"]=r.account_id;timeline_rows.extend(daily.to_dict("records"));entity_lines=[]
        for c,label in [("token_hash","token"),("payment_hash","payment"),("device_hash","device"),("ip_hash","IP context")]:
            values=[v for v in g[c].unique().tolist() if v];entity_lines.append(f"- Distinct {label} fingerprints in account activity: {len(values)}")
        recent=daily.tail(5);recent_table=recent.to_markdown(index=False,floatfmt=".3f") if len(recent) else "No activity.";managed_note="Managed/shared infrastructure is present. Device/IP dispersion must not be interpreted as independent actors without stronger evidence." if int(r.managed_infrastructure)==1 else "No managed-infrastructure flag is available in the benchmark account context."
        md=f"""# Investigation case: {r.account_id}

## Decision status
**Investigation priority only — no automatic enforcement.**

Risk score: **{r.risk_score:.3f}**  
Reason codes: **{r.reason_codes}**  
Plan / region: **{r.plan} / {r.region}**  
Managed infrastructure: **{bool(r.managed_infrastructure)}**

## Evidence summary
- Requests per active day: {r.requests_per_active_day:.1f}
- Unique devices: {r.unique_devices}
- Unique IP contexts: {r.unique_ips}
- Maximum accounts sharing a token: {r.max_token_degree}
- Maximum accounts sharing a payment fingerprint: {r.max_payment_degree}
- Cadence regularity: {r.cadence_regularity:.3f}
- Overnight usage share: {r.overnight_share:.1%}
- Content-policy signal rate: {r.policy_signal_rate:.3%}
- Prompt-injection signal rate: {r.injection_rate:.3%}

## Identity-context caution
{managed_note}

{chr(10).join(entity_lines)}

## Recent activity timeline
{recent_table}

## Competing explanations to test
1. Approved automation, agent workflow, CI runner, or service integration.
2. Enterprise NAT, VPN, managed-device fleet, travel, or shared development environment.
3. Token rotation, integration migration, or authentication lifecycle effects.
4. Security-research activity that legitimately triggers safety signals.
5. A product or entitlement change that altered expected usage patterns.

## Evidence standard before escalation
Use at least two independent signal families where possible: behavioral/temporal evidence plus a reliable identity or entitlement signal. IP sharing alone is supporting context, not identity proof.

## Privacy and legal boundary
No raw prompts, completions, IP addresses, payment details, or device identifiers are exposed here. Content review or expanded identity linkage requires an approved access path and the appropriate privacy/legal review.
""";(case_dir/f"{r.account_id}.md").write_text(md)
    pd.DataFrame(timeline_rows).to_csv(out_dir/"investigation_timeline.csv",index=False);return queue

class _UnionFind:
    def __init__(self):self.parent={}
    def find(self,x):
        self.parent.setdefault(x,x)
        if self.parent[x]!=x:self.parent[x]=self.find(self.parent[x])
        return self.parent[x]
    def union(self,a,b):
        ra,rb=self.find(a),self.find(b)
        if ra!=rb:self.parent[rb]=ra

def build_linked_account_components(scores:pd.DataFrame,data_dir:str|Path,out_dir:str|Path)->pd.DataFrame:
    t=pd.read_csv(Path(data_dir)/"telemetry.csv",keep_default_na=False);uf=_UnionFind();evidence=[];linkage_policy={"token_hash":("token",1.00,8),"payment_hash":("payment",0.90,8),"device_hash":("device",0.80,6),"ip_hash":("ip",0.35,3)}
    for col,(etype,reliability,max_link_degree) in linkage_policy.items():
        pairs=t.loc[t[col].ne(""),["account_id",col]].drop_duplicates()
        for entity,g in pairs.groupby(col):
            accounts=g.account_id.unique().tolist();degree=len(accounts)
            if degree<2:continue
            eligible=degree<=max_link_degree
            if eligible:
                head=accounts[0]
                for a in accounts[1:]:uf.union(head,a)
            evidence.append({"entity_type":etype,"entity_hash":entity,"linked_accounts":degree,"reliability_weight":reliability,"eligible_to_seed_component":int(eligible),"analyst_note":"usable linkage seed with corroboration" if eligible and etype!="ip" else "supporting context only; review shared infrastructure/NAT" if etype=="ip" else "high-degree entity suppressed from automatic component seeding"})
    members={}
    for a in t.account_id.unique():members.setdefault(uf.find(a),[]).append(a)
    score_map=scores.set_index("account_id")["risk_score"].to_dict();rows=[]
    for i,(_,accs) in enumerate(sorted(members.items(),key=lambda kv:len(kv[1]),reverse=True)):
        if len(accs)<2:continue
        rows.append({"component_id":f"component_{i:04d}","account_count":len(accs),"max_risk_score":max(score_map.get(a,0) for a in accs),"mean_risk_score":sum(score_map.get(a,0) for a in accs)/len(accs),"member_accounts":"|".join(sorted(accs)[:25])})
    out=pd.DataFrame(rows,columns=["component_id","account_count","max_risk_score","mean_risk_score","member_accounts"]);Path(out_dir).mkdir(parents=True,exist_ok=True);out.to_csv(Path(out_dir)/"linked_account_components.csv",index=False);evidence_df=pd.DataFrame(evidence)
    if len(evidence_df):evidence_df=evidence_df.sort_values(["eligible_to_seed_component","reliability_weight","linked_accounts"],ascending=[False,False,False])
    evidence_df.head(1000).to_csv(Path(out_dir)/"shared_entity_evidence.csv",index=False);return out
