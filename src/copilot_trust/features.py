from __future__ import annotations

import sqlite3
from pathlib import Path
import pandas as pd

BASE_SQL = r'''
SELECT
  account_id,
  COUNT(*) AS requests,
  COUNT(DISTINCT NULLIF(device_hash,'')) AS unique_devices,
  COUNT(DISTINCT NULLIF(ip_hash,'')) AS unique_ips,
  COUNT(DISTINCT NULLIF(token_hash,'')) AS unique_tokens,
  COUNT(DISTINCT NULLIF(payment_hash,'')) AS unique_payments,
  AVG(prompt_chars) AS avg_prompt_chars,
  AVG(completion_chars) AS avg_completion_chars,
  AVG(completion_accepted) AS acceptance_rate,
  AVG(prompt_injection_signal) AS injection_rate,
  AVG(content_policy_signal) AS policy_signal_rate,
  AVG(safety_blocked) AS block_rate,
  SUM(CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) BETWEEN 0 AND 5 THEN 1 ELSE 0 END)*1.0/COUNT(*) AS overnight_share,
  COUNT(DISTINCT substr(timestamp,1,10)) AS active_days,
  MAX(entitlement_limit) AS entitlement_limit,
  SUM(CASE WHEN ip_hash='' THEN 1 ELSE 0 END)*1.0/COUNT(*) AS ip_missing_rate,
  SUM(CASE WHEN device_hash='' THEN 1 ELSE 0 END)*1.0/COUNT(*) AS device_missing_rate
FROM telemetry
GROUP BY account_id
'''


def build_feature_mart(data_dir: str | Path, out_path: str | Path) -> pd.DataFrame:
    data_dir=Path(data_dir); accounts=pd.read_csv(data_dir/'accounts.csv'); telemetry=pd.read_csv(data_dir/'telemetry.csv',keep_default_na=False)
    conn=sqlite3.connect(':memory:'); telemetry.to_sql('telemetry',conn,index=False); base=pd.read_sql_query(BASE_SQL,conn); conn.close()
    shared_frames=[]
    for col,out_col in [('token_hash','max_token_degree'),('payment_hash','max_payment_degree'),('device_hash','max_device_degree'),('ip_hash','max_ip_degree')]:
        valid=telemetry[col].ne(''); degrees=telemetry.loc[valid].groupby(col)['account_id'].nunique(); tmp=telemetry.loc[valid,['account_id',col]].copy(); tmp['degree']=tmp[col].map(degrees).astype(float); shared_frames.append(tmp.groupby('account_id')['degree'].max().rename(out_col))
    shared=pd.concat(shared_frames,axis=1).fillna(1).reset_index()
    telemetry['timestamp']=pd.to_datetime(telemetry['timestamp'],utc=True,format='mixed'); ordered=telemetry[['account_id','timestamp']].sort_values(['account_id','timestamp']); ordered['delta_s']=ordered.groupby('account_id')['timestamp'].diff().dt.total_seconds(); cad=ordered.groupby('account_id')['delta_s'].agg(['mean','std']).reset_index(); cad['interarrival_cv']=(cad['std']/cad['mean']).fillna(1.0).clip(lower=0); cad['cadence_regularity']=1/(1+cad['interarrival_cv']); cad=cad[['account_id','interarrival_cv','cadence_regularity']]
    feat=accounts.merge(base,on='account_id',how='inner').merge(shared,on='account_id',how='left').merge(cad,on='account_id',how='left')
    for c in ['max_token_degree','max_payment_degree','max_device_degree','max_ip_degree']: feat[c]=feat[c].fillna(1)
    feat['requests_per_active_day']=feat.requests/feat.active_days.clip(lower=1); feat['quota_pressure']=feat.requests/(feat.entitlement_limit*feat.active_days).clip(lower=1)
    Path(out_path).parent.mkdir(parents=True,exist_ok=True); feat.to_csv(out_path,index=False); return feat
