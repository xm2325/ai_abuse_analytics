-- Self-service semantic views for a BI layer.
CREATE VIEW v_abuse_account_review AS
SELECT account_id, split, plan, region, risk_score, flagged, reason_codes,
       managed_infrastructure, legitimate_profile, requests_per_active_day,
       unique_devices, unique_ips, max_token_degree, max_payment_degree
FROM account_risk_scores;

CREATE VIEW v_abuse_daily_health AS
SELECT event_date, requests_per_active_account, agent_share, injection_rate,
       policy_signal_rate, safety_block_rate, ip_missing_rate, device_missing_rate
FROM daily_abuse_monitor;

-- Production BI should use certified measures rather than redefining precision,
-- FPR, review workload, or signal coverage in each dashboard.
