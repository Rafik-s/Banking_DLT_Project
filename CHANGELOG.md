### Fixed
- **Critical:** `email_masked` in `silver_customers` and `silver_employees` now uses real masking (`j*********@gmail.com`) instead of `lower(trim(email))` which was not a mask
- **Critical:** `silver_employees.phone_masked` now uses real masking — was previously unmasked
- `card_number_masked` README wording changed from "PCI-DSS compliant" to "PCI-DSS-aligned" (accurate classification)
- `_ingestion_file_hash` renamed to `_source_file_path_hash` (it hashes path, not content)
- `silver_transactions_quarantine` and `silver_transactions_validated` now use proper stream-stream joins with time bounds

### Added
- `email_sha256`, `phone_sha256`, `card_number_sha256` for deterministic PII matching without exposing raw values
- `docs/SECURITY_BOUNDARY.md` — formal documentation of Bronze PII security boundary
- `expect_or_fail("valid_record_updated_at", "_record_updated_at IS NOT NULL")` on Silver tables with watermarks
- Explicit `REVOKE EXECUTE ON FUNCTION pii_hmac FROM account users` in Terraform
- `REVOKE SELECT ON SCHEMA raw_bronze FROM account users` in Terraform
- PII column tags now include `tier='bronze-pii'` for audit automation

### Changed
- README framing: "production-grade Tier-1 bank" → "enterprise-grade reference implementation"
- Added `## ⚠️ Disclaimer` section to README
- `_record_updated_at` added to `silver_branches`, `silver_credit_cards`, `silver_loans`, `silver_kyc_documents`, `silver_fraud_alerts`, `silver_atm_transactions` (Workstream 2 prep)