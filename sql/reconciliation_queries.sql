-- ============================================================================
-- BANKING RECONCILIATION QUERIES
-- Ad-hoc reference queries. The production engine is src/reconciliation.py.
-- ============================================================================

-- 1. FAILURES IN THE LAST 7 DAYS (on-call triage)
SELECT
    business_date,
    dataset,
    reconciliation_type,
    source_layer,
    target_layer,
    count_difference,
    amount_difference,
    failure_reason,
    reconciled_at
FROM banking_prod_catalog.cur_gold.reconciliation_results
WHERE status = 'FAIL'
  AND business_date >= current_date() - INTERVAL 7 DAYS
ORDER BY business_date DESC, dataset, reconciliation_type;

-- 2. PASS RATE BY DAY (trend / SLA reporting)
SELECT
    business_date,
    COUNT(*)                                        AS total_checks,
    SUM(CASE WHEN status = 'PASS'    THEN 1 ELSE 0 END) AS passed,
    SUM(CASE WHEN status = 'FAIL'    THEN 1 ELSE 0 END) AS failed,
    SUM(CASE WHEN status = 'WARNING' THEN 1 ELSE 0 END) AS warned,
    SUM(CASE WHEN status = 'SKIPPED' THEN 1 ELSE 0 END) AS skipped,
    ROUND(100.0 * SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) / COUNT(*), 2)
                                                     AS pass_rate_pct
FROM banking_prod_catalog.cur_gold.reconciliation_results
GROUP BY business_date
ORDER BY business_date DESC;

-- 3. FINANCIAL IMPACT OF FAILURES (regulatory reporting)
SELECT
    business_date,
    dataset,
    SUM(ABS(amount_difference)) AS total_amount_at_risk_inr
FROM banking_prod_catalog.cur_gold.reconciliation_results
WHERE status = 'FAIL'
  AND amount_difference IS NOT NULL
GROUP BY business_date, dataset
ORDER BY business_date DESC;

-- 4. SLA REPORT — last 30 days
SELECT
    business_date,
    CASE
        WHEN SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END) = 0 THEN 'WITHIN_SLA'
        ELSE 'SLA_BREACH'
    END AS sla_status
FROM banking_prod_catalog.cur_gold.reconciliation_results
WHERE business_date >= current_date() - INTERVAL 30 DAYS
GROUP BY business_date
ORDER BY business_date DESC;