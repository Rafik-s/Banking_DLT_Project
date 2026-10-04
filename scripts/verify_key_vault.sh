#!/usr/bin/env bash
# ============================================================================
# VERIFY KEY VAULT INTEGRATION
# Verifies that Databricks secret scope → Key Vault → PII HMAC works.
# ============================================================================

set -euo pipefail

ENV="${1:-dev}"
VAULT="kv-banking-${ENV}"
SCOPE="banking-pii-${ENV}"

echo "Verifying Key Vault integration for env=${ENV}"
echo ""

# 1. Key Vault reachable
echo "[1/4] Checking Key Vault reachability..."
if ! az keyvault show --name "$VAULT" --query id -o tsv >/dev/null 2>&1; then
  echo "  ❌ Key Vault $VAULT not found or not accessible"
  exit 1
fi
echo "  ✅ Key Vault $VAULT reachable"

# 2. Secret exists
echo "[2/4] Checking pii-hmac-salt secret..."
if ! az keyvault secret show --vault-name "$VAULT" --name "pii-hmac-salt" --query id -o tsv >/dev/null 2>&1; then
  echo "  ❌ Secret 'pii-hmac-salt' not found in $VAULT"
  exit 1
fi
echo "  ✅ Secret 'pii-hmac-salt' exists"

# 3. Databricks secret scope exists
echo "[3/4] Checking Databricks secret scope..."
if ! databricks secrets list-scopes 2>/dev/null | grep -q "$SCOPE"; then
  echo "  ❌ Databricks secret scope $SCOPE not found"
  exit 1
fi
echo "  ✅ Secret scope $SCOPE exists"

# 4. UC function can be called (integration test)
echo "[4/4] Testing UC function security.pii_hmac..."
TEST_RESULT=$(databricks sql --warehouse-id "$WAREHOUSE_ID" \
  "SELECT banking_${ENV}_catalog.security.pii_hmac('test-input')" 2>&1 | tail -1)

if [[ -z "$TEST_RESULT" ]] || [[ "$TEST_RESULT" == *"Error"* ]]; then
  echo "  ❌ UC function failed"
  echo "  Output: $TEST_RESULT"
  exit 1
fi

echo "  ✅ UC function returned hash: ${TEST_RESULT:0:16}..."
echo ""
echo "==================================================================="
echo "  ✅ Key Vault integration verified for env=${ENV}"
echo "==================================================================="