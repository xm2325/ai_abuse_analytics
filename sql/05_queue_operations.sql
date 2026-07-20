-- Operational queue ageing and priority starting point.
-- Uses the canonical telemetry table name from the data contract.
WITH latest_signal AS (
  SELECT account_id, MAX(timestamp) AS last_signal_at
  FROM telemetry
  GROUP BY account_id
), flagged AS (
  SELECT r.account_id, r.risk_score, r.reason_codes, l.last_signal_at
  FROM account_risk_scores r
  JOIN latest_signal l USING (account_id)
  WHERE r.flagged = 1
)
SELECT account_id, risk_score, reason_codes, last_signal_at,
       CASE WHEN risk_score >= 0.90 THEN 'P0'
            WHEN risk_score >= 0.75 THEN 'P1'
            WHEN risk_score >= 0.60 THEN 'P2'
            ELSE 'P3' END AS priority_tier
FROM flagged ORDER BY risk_score DESC;
