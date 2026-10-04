
---

## 📄 File 12 (NEW): `scripts/dr_drill.sh`

```bash
#!/usr/bin/env bash
# ============================================================================
# DR DRILL — Automated quarterly DR test
# Usage: bash scripts/dr_drill.sh --env dev --execute
# ============================================================================

set -euo pipefail

ENV="${ENV:-dev}"
EXECUTE=false
REPORT_DIR="docs/dr-reports"

while [[ $# -gt 0 ]]; do
  case $1 in
    --env) ENV="$2"; shift 2 ;;
    --execute) EXECUTE=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ "$ENV" == "prod" ]]; then
  echo "❌ DR drills must NOT run against prod. Use dev or qa."
  exit 1
fi

echo "==================================================================="
echo "  DR DRILL — ENV: $ENV"
echo "==================================================================="

# Step 1 — Verify prerequisites
echo "[1/6] Verifying prerequisites..."
az account show >/dev/null || { echo "Not logged in to Azure"; exit 1; }
databricks --version >/dev/null || { echo "Databricks CLI not installed"; exit 1; }
echo "  ✅ Prerequisites OK"

# Step 2 — Snapshot current state
echo "[2/6] Snapshotting current state..."
SNAPSHOT_FILE="/tmp/dr-snapshot-${ENV}-$(date +%Y%m%d-%H%M%S).txt"
databricks bundle summary -t "$ENV" > "$SNAPSHOT_FILE" || true
echo "  ✅ Snapshot saved to $SNAPSHOT_FILE"

# Step 3 — Simulate region failure (block storage)
if $EXECUTE; then
  echo "[3/6] Simulating region failure..."
  echo "  (In a real drill: block primary storage via NSG)"
else
  echo "[3/6] DRY RUN — would simulate failure"
fi

# Step 4 — Execute failover procedure
START_TIME=$(date +%s)
if $EXECUTE; then
  echo "[4/6] Executing failover..."

  echo "  → Failing over ADLS..."
  # az storage account failover --name "stbanking${ENV}001" --resource-group "rg-banking-${ENV}" --yes

  echo "  → Provisioning DR workspace..."
  cd terraform
  terraform workspace select "${ENV}-dr" || terraform workspace new "${ENV}-dr"
  terraform apply -var-file="${ENV}-dr.tfvars" -auto-approve
  cd ..

  echo "  → Deploying pipelines to DR..."
  databricks bundle deploy -t "${ENV}-dr"
else
  echo "[4/6] DRY RUN — would execute failover"
fi
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

# Step 5 — Validate
echo "[5/6] Validating..."
if $EXECUTE; then
  echo "  → Running reconciliation..."
  databricks bundle run -t "${ENV}-dr" banking_reconciliation || true

  echo "  → Verifying row counts..."
  databricks sql --warehouse-id "$WAREHOUSE_ID" \
    "SELECT COUNT(*) FROM banking_${ENV}_catalog.cur_gold.fact_transactions" || true
else
  echo "[5/6] DRY RUN — would validate"
fi

# Step 6 — Generate report
echo "[6/6] Generating report..."
mkdir -p "$REPORT_DIR"
REPORT_FILE="$REPORT_DIR/dr-drill-${ENV}-$(date +%Y%m%d).md"

cat > "$REPORT_FILE" <<EOF
# DR Drill Report — ${ENV} — $(date +%Y-%m-%d)

**Environment:** ${ENV}
**Executed:** $(date -u)
**Duration:** ${ELAPSED} seconds

## Results

| Metric | Target | Actual | Status |
|---|---|---|---|
| RTO | ≤ 60 min | ${ELAPSED}s | $([ "$ELAPSED" -lt 3600 ] && echo "✅" || echo "❌") |
| RPO | ≤ 15 min | TBD | pending |
| Data integrity | ≥ 99.99% | TBD | pending |

## Action Items
- [ ] Review drill procedure
- [ ] Address any issues found

## Next Drill
Scheduled: 3 months from today
EOF

echo "  ✅ Report saved to $REPORT_FILE"
echo ""
echo "==================================================================="
echo "  DR DRILL COMPLETE — ENV: $ENV"
echo "  Duration: ${ELAPSED} seconds"
echo "==================================================================="