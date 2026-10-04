#!/usr/bin/env bash
# .git/hooks/pre-commit — block commits containing obvious secrets

set -e

FORBIDDEN_PATTERNS=(
    "dapi[0-9a-f]{32}"                    # Databricks PAT
    "AccountKey=[A-Za-z0-9+/=]{40,}"      # Azure Storage key
    "client_secret\s*=\s*['\"][^'\"]+"    # OAuth client secret
    "-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----"
    "pii_salt\s*=\s*['\"][^'\"]{16,}"     # HMAC salt
)

STAGED=$(git diff --cached --name-only --diff-filter=ACM)

for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
    if echo "$STAGED" | xargs -I{} grep -nHE "$pattern" {} 2>/dev/null; then
        echo ""
        echo "❌ COMMIT BLOCKED: Forbidden pattern detected: $pattern"
        echo "   Remove the secret and use Azure Key Vault / Databricks Secrets."
        exit 1
    fi
done

exit 0