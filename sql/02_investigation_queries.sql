-- Potential credential sharing: dispersion is an investigation seed, not proof.
SELECT account_id, COUNT(DISTINCT device_hash) AS devices,
       COUNT(DISTINCT ip_hash) AS ips, COUNT(*) AS requests
FROM telemetry
GROUP BY account_id
HAVING devices >= 7 AND ips >= 10
ORDER BY devices DESC, ips DESC;

-- Shared-token graph seed.
SELECT token_hash, COUNT(DISTINCT account_id) AS linked_accounts, COUNT(*) AS requests
FROM telemetry
WHERE token_hash <> ''
GROUP BY token_hash
HAVING linked_accounts >= 2
ORDER BY linked_accounts DESC;

-- Data-quality regression by day.
SELECT DATE(timestamp) AS event_date,
       AVG(CASE WHEN ip_hash='' THEN 1.0 ELSE 0 END) AS missing_ip_rate,
       AVG(CASE WHEN device_hash='' THEN 1.0 ELSE 0 END) AS missing_device_rate
FROM telemetry
GROUP BY 1 ORDER BY 1;
