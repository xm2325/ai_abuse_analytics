-- Daily observable-signal monitor by product surface.
SELECT DATE(timestamp) AS event_date, model_family,
       COUNT(*) AS requests, COUNT(DISTINCT account_id) AS active_accounts,
       AVG(prompt_injection_signal) AS injection_rate,
       AVG(content_policy_signal) AS policy_signal_rate,
       AVG(safety_blocked) AS block_rate,
       AVG(CASE WHEN ip_hash='' THEN 1.0 ELSE 0.0 END) AS ip_missing_rate
FROM telemetry GROUP BY 1,2 ORDER BY 1,2;

-- Account usage versus entitlement: investigation seed only.
WITH account_day AS (
  SELECT DATE(timestamp) AS event_date, account_id, COUNT(*) AS requests,
         MAX(entitlement_limit) AS entitlement_limit
  FROM telemetry GROUP BY 1,2
)
SELECT event_date, COUNT(*) AS active_accounts,
       AVG(CASE WHEN requests >= 0.80*entitlement_limit THEN 1.0 ELSE 0.0 END) AS near_quota_account_rate
FROM account_day GROUP BY 1 ORDER BY 1;

-- Surface-mix change must be segmented before abuse interpretation.
SELECT DATE(timestamp) AS event_date,
       AVG(CASE WHEN model_family='agent' THEN 1.0 ELSE 0.0 END) AS agent_share
FROM telemetry GROUP BY 1 ORDER BY 1;
