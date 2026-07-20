-- Time-based replay example for a frozen human-review rule.
-- The checkpoint date is supplied externally; no events after the checkpoint are used.
-- Production systems should materialize this as an event-time incremental mart.
WITH params AS (
  SELECT DATE('2026-05-20') AS checkpoint_date,
         DATE('2026-05-14') AS window_start,
         30.0 AS frozen_velocity_cut
), windowed AS (
  SELECT t.account_id,
         COUNT(*) AS requests,
         COUNT(DISTINCT DATE(t.timestamp)) AS active_days,
         COUNT(DISTINCT NULLIF(t.device_hash,'')) AS unique_devices,
         COUNT(DISTINCT NULLIF(t.ip_hash,'')) AS unique_ips,
         AVG(t.content_policy_signal*1.0) AS policy_signal_rate,
         AVG(t.prompt_injection_signal*1.0) AS injection_rate,
         AVG(CASE WHEN t.model_family='agent' THEN 1.0 ELSE 0.0 END) AS agent_share,
         AVG(CASE WHEN CAST(strftime('%H',t.timestamp) AS INTEGER)<6 OR CAST(strftime('%H',t.timestamp) AS INTEGER)>=23 THEN 1.0 ELSE 0.0 END) AS overnight_share
  FROM telemetry t CROSS JOIN params p
  WHERE DATE(t.timestamp) BETWEEN p.window_start AND p.checkpoint_date
  GROUP BY t.account_id
), replay AS (
  SELECT w.*,
         w.requests*1.0/NULLIF(w.active_days,0) AS requests_per_active_day,
         CASE WHEN w.requests*1.0/NULLIF(w.active_days,0)>=p.frozen_velocity_cut
                   AND w.overnight_share>=0.08 THEN 1 ELSE 0 END AS scripted_usage_v1,
         CASE WHEN w.policy_signal_rate>=0.03 THEN 1 ELSE 0 END AS policy_signal_v1,
         CASE WHEN (w.policy_signal_rate>=0.02 AND w.injection_rate>=0.015)
                    OR (w.policy_signal_rate>=0.025 AND w.agent_share>=0.35) THEN 1 ELSE 0 END AS policy_signal_v2
  FROM windowed w CROSS JOIN params p
)
SELECT * FROM replay
ORDER BY scripted_usage_v1 DESC, policy_signal_v2 DESC, requests_per_active_day DESC;
