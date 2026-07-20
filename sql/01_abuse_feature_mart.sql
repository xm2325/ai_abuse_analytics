-- Warehouse-style feature contract used by the local SQLite implementation.
-- In production this would be materialized incrementally by event date.
WITH account_usage AS (
  SELECT account_id, DATE(timestamp) AS event_date,
         COUNT(*) AS requests,
         COUNT(DISTINCT device_hash) AS devices,
         COUNT(DISTINCT ip_hash) AS ips,
         AVG(prompt_injection_signal) AS injection_rate,
         AVG(content_policy_signal) AS policy_signal_rate,
         AVG(completion_accepted) AS acceptance_rate
  FROM telemetry
  GROUP BY 1,2
)
SELECT * FROM account_usage;
