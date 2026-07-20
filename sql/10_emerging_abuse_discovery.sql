-- Emerging abuse discovery starter query.
-- This query intentionally does not use abuse labels or review outcomes.
-- It creates recent-vs-baseline behavior shifts for analyst cohort discovery.

WITH event_features AS (
  SELECT
    account_id,
    DATE(timestamp) AS event_date,
    COUNT(*) AS requests,
    COUNT(DISTINCT NULLIF(token_hash,'')) AS unique_tokens,
    COUNT(DISTINCT model_family) AS unique_surfaces,
    AVG(CASE WHEN model_family='agent' THEN 1.0 ELSE 0.0 END) AS agent_share,
    AVG(completion_accepted*1.0) AS acceptance_rate
  FROM telemetry
  GROUP BY account_id, DATE(timestamp)
), bounds AS (
  SELECT MAX(event_date) AS max_day FROM event_features
), windows AS (
  SELECT
    e.*,
    CASE
      WHEN event_date >= DATE(max_day,'-9 day') THEN 'recent'
      WHEN event_date >= DATE(max_day,'-37 day') AND event_date < DATE(max_day,'-9 day') THEN 'baseline'
      ELSE 'outside'
    END AS analysis_window
  FROM event_features e CROSS JOIN bounds
), account_window AS (
  SELECT
    account_id,
    analysis_window,
    AVG(requests) AS mean_requests,
    AVG(unique_tokens) AS mean_unique_tokens,
    AVG(unique_surfaces) AS mean_unique_surfaces,
    AVG(agent_share) AS mean_agent_share,
    AVG(acceptance_rate) AS mean_acceptance_rate
  FROM windows
  WHERE analysis_window IN ('baseline','recent')
  GROUP BY account_id, analysis_window
)
SELECT
  b.account_id,
  b.mean_requests AS baseline_requests,
  r.mean_requests AS recent_requests,
  r.mean_unique_tokens-b.mean_unique_tokens AS token_rotation_delta,
  r.mean_unique_surfaces-b.mean_unique_surfaces AS surface_count_delta,
  r.mean_agent_share-b.mean_agent_share AS agent_share_delta,
  ABS(r.mean_acceptance_rate-b.mean_acceptance_rate) AS acceptance_shift
FROM account_window b
JOIN account_window r USING(account_id)
WHERE b.analysis_window='baseline' AND r.analysis_window='recent'
ORDER BY token_rotation_delta DESC, surface_count_delta DESC;

-- Next steps are deliberately outside this SQL:
-- 1. robust multivariate novelty scoring;
-- 2. telemetry-health screen;
-- 3. cohort clustering;
-- 4. entity/context triage;
-- 5. analyst taxonomy proposal;
-- 6. independent shadow/replay validation before any policy change.
