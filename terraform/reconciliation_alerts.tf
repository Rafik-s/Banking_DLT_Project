# ============================================================================
# RECONCILIATION ALERTING
# Creates a Gold view that surfaces only FAIL rows, for Power BI / Teams.
# ============================================================================

resource "databricks_sql_exec" "reconciliation_views" {
  warehouse_id = var.sql_warehouse_id

  sql = <<SQL
    -- View for on-call: latest failing reconciliations
    CREATE OR REPLACE VIEW ${var.catalog_name}.cur_gold.reconciliation_failures AS
    SELECT
        business_date,
        dataset,
        reconciliation_type,
        source_layer,
        target_layer,
        count_difference,
        source_amount_inr,
        target_amount_inr,
        amount_difference,
        failure_reason,
        reconciled_at
    FROM ${var.catalog_name}.cur_gold.reconciliation_results
    WHERE status = 'FAIL'
      AND business_date >= current_date() - INTERVAL 7 DAYS
    ORDER BY business_date DESC, dataset;

    -- View for daily SLA reporting
    CREATE OR REPLACE VIEW ${var.catalog_name}.cur_gold.reconciliation_sla AS
    SELECT
        business_date,
        COUNT(*)                                        AS total_checks,
        SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) AS passed,
        SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END) AS failed,
        ROUND(
          100.0 * SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) / COUNT(*),
          2
        ) AS pass_rate_pct
    FROM ${var.catalog_name}.cur_gold.reconciliation_results
    WHERE business_date >= current_date() - INTERVAL 30 DAYS
    GROUP BY business_date
    ORDER BY business_date DESC;
  SQL
}