-- ============================================================================
-- DQ ALERT VIEW
-- Query this on a schedule; page on-call if any row is returned.
-- ============================================================================
CREATE OR REPLACE VIEW banking_prod_catalog.cur_gold.dq_alerts AS
WITH latest_run AS (
    SELECT
        pipeline_name,
        update_id,
        MAX(event_ts) AS last_event_ts
    FROM banking_prod_catalog.cur_gold.dq_metrics_history
    WHERE metric_date = current_date()
    GROUP BY pipeline_name, update_id
)
SELECT
    m.metric_date,
    m.pipeline_name,
    m.update_id,
    m.flow_name,
    m.expectation_name,
    m.pass_rate_pct,
    m.failed_records,
    m.dropped_records,
    m.total_records,
    CASE
        WHEN m.pass_rate_pct < 95.0 THEN 'CRITICAL'
        WHEN m.pass_rate_pct < 99.0 THEN 'WARNING'
        ELSE 'OK'
    END AS alert_severity
FROM banking_prod_catalog.cur_gold.dq_metrics_history m
JOIN latest_run l
  ON m.pipeline_name = l.pipeline_name
 AND m.update_id     = l.update_id
WHERE m.metric_date = current_date()
  AND m.pass_rate_pct < 99.0
ORDER BY m.pass_rate_pct ASC;