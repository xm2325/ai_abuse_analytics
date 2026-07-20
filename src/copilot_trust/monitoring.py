from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


def _robust_stats(history: pd.Series) -> tuple[float, float]:
    history = history.dropna().astype(float)
    if len(history) < 7:
        return 0.0, 1.0
    median = float(history.median())
    mad = float((history - median).abs().median())
    scale = 1.4826 * mad
    if scale < 1e-9:
        std = float(history.std(ddof=0))
        scale = std if std > 1e-9 else 1.0
    return median, scale


def build_daily_monitor(data_dir: str | Path, out_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    data_dir = Path(data_dir); out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    t = pd.read_csv(data_dir / "telemetry.csv", keep_default_na=False); t["timestamp"] = pd.to_datetime(t["timestamp"], utc=True, format="mixed"); t["event_date"] = t["timestamp"].dt.date.astype(str)
    daily = t.groupby("event_date").agg(requests=("request_id","count"),active_accounts=("account_id","nunique"),injection_rate=("prompt_injection_signal","mean"),policy_signal_rate=("content_policy_signal","mean"),safety_block_rate=("safety_blocked","mean"),ip_missing_rate=("ip_hash",lambda s:s.astype(str).eq("").mean()),device_missing_rate=("device_hash",lambda s:s.astype(str).eq("").mean())).reset_index()
    agent=t.assign(is_agent=t.model_family.eq("agent").astype(int)).groupby("event_date")["is_agent"].mean().rename("agent_share").reset_index(); account_day=t.groupby(["event_date","account_id"]).agg(requests=("request_id","count"),entitlement_limit=("entitlement_limit","max")).reset_index(); quota=account_day.assign(near_quota=lambda d:d.requests>=0.80*d.entitlement_limit).groupby("event_date")["near_quota"].mean().rename("near_quota_account_rate").reset_index(); daily=daily.merge(agent,on="event_date").merge(quota,on="event_date"); daily["requests_per_active_account"]=daily.requests/daily.active_accounts.clip(lower=1)
    monitored=["requests_per_active_account","agent_share","injection_rate","policy_signal_rate","safety_block_rate","near_quota_account_rate","ip_missing_rate","device_missing_rate"]; alert_rows=[]
    for metric in monitored:
        z_values=[]; baseline_values=[]
        for i,row in daily.iterrows():
            hist=daily.loc[max(0,i-14):i-1,metric] if i>0 else pd.Series(dtype=float); median,scale=_robust_stats(hist); z=(float(row[metric])-median)/scale if len(hist)>=7 else 0.0; z_values.append(float(z)); baseline_values.append(float(median))
            if len(hist)<7 or z<3.0: continue
            previous_z=z_values[i-1] if i>0 else 0.0; sustained_or_extreme=z>=7.0 or (z>=3.0 and previous_z>=2.5); material=float(row[metric])-median>=0.03 if "missing_rate" in metric else (float(row[metric])-median)/max(abs(median),1e-4)>=0.20
            if not(sustained_or_extreme and material): continue
            severity="critical" if z>=10 else "high" if z>=7 else "medium"; alert_rows.append({"event_date":row.event_date,"metric":metric,"value":float(row[metric]),"rolling_baseline":median,"robust_z":float(z),"relative_change":(float(row[metric])-median)/max(abs(median),1e-4),"direction":"increase","severity":severity,"recommended_owner":"Data/Engineering" if "missing" in metric else "Trust & Safety Analytics","next_step":"validate instrumentation and upstream pipeline before changing detection" if "missing" in metric else "segment by surface/plan, inspect linked cases, and decide whether a new investigation query is needed"})
        daily[f"{metric}_robust_z"]=z_values; daily[f"{metric}_rolling_baseline"]=baseline_values
    alerts=pd.DataFrame(alert_rows,columns=["event_date","metric","value","rolling_baseline","robust_z","relative_change","direction","severity","recommended_owner","next_step"])
    if not alerts.empty:
        severity_order={"critical":0,"high":1,"medium":2}; alerts["_order"]=alerts.severity.map(severity_order); alerts=alerts.sort_values(["_order","robust_z","event_date"],ascending=[True,False,False]).drop(columns="_order")
    daily.to_csv(out_dir/"daily_abuse_monitor.csv",index=False); alerts.to_csv(out_dir/"emerging_trend_alerts.csv",index=False); return daily,alerts
