# 🔑 Key Vault Integration

> **Owner:** Data Platform Engineering + InfoSec
> **Last reviewed:** 2026-10-04
> **Classification:** Internal — Restricted

---

## 1. Architecture
┌─────────────────────────────────────────────────────────────────────────┐
│ Azure Key Vault: kv-banking-{env} │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ Secrets: │ │
│ │ • pii-hmac-salt (PII hashing salt) │ │
│ │ • databricks-host (workspace URL — not a secret, but │ │
│ │ centralizes config) │ │
│ │ • databricks-resource-id (WIF audience) │ │
│ │ • smtp-password (for alerts) │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│ │
│ Access control: │
│ • RBAC (not access policies) │
│ • Reader role → Data Platform SP, CI SP │
│ • Secret Officer role → InfoSec │
│ • No public network access │
│ • Private Endpoint only │
│ • Soft delete + purge protection │
└─────────────────────────────────────────────────────────────────────────┘
│
│ Private Endpoint (VNet)
▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Databricks Workspace │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ Secret Scope: banking-pii-{env} │ │
│ │ (Backed by Key Vault — secrets are NOT copied to Databricks) │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│ │ │
│ │ Used by │
│ ▼ │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ UC Function: security.pii_hmac() │ │
│ │ → secret('banking-pii-{env}', 'salt') │ │
│ └──────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘


### Key principle: **secrets never leave Key Vault**

Databricks Secret Scopes backed by Key Vault **do not copy** the secret
values. When a UC function calls `secret('scope', 'key')`, the value is
fetched at execution time via a secure, audited channel. The value is
**not stored** in the Databricks workspace.

---

## 2. Terraform Provisioning

```hcl
# From terraform/key_vault.tf

resource "azurerm_key_vault" "banking" {
  name                       = "kv-banking-${var.env}"
  location                   = var.primary_region
  resource_group_name        = azurerm_resource_group.banking.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 90
  purge_protection_enabled   = true
  enable_rbac_authorization  = true

  network_acls {
    default_action = "Deny"
    bypass         = "AzureServices"
  }
}

resource "azurerm_key_vault_secret" "pii_hmac_salt" {
  name         = "pii-hmac-salt"
  value        = var.pii_salt
  key_vault_id = azurerm_key_vault.banking.id

  # Never expose in Terraform state at rest — use a data source from KV instead
  lifecycle {
    ignore_changes = [value]   # prevent accidental rotation via Terraform
  }
}

# Grant the Databricks workspace's managed identity access to the secret
resource "azurerm_role_assignment" "databricks_kv_reader" {
  scope                = azurerm_key_vault.banking.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_databricks_workspace.this.managed_identity_id
}

resource "databricks_secret_scope" "pii" {
  name = "banking-pii-${var.env}"

  keyvault_metadata {
    resource_id = azurerm_key_vault.banking.id
    dns_name    = azurerm_key_vault.banking.vault_uri
  }

  depends_on = [azurerm_role_assignment.databricks_kv_reader]
}

3. Access Control Matrix
Role	Key Vault Role	Databricks Scope Access	Can read pii-hmac-salt?
InfoSec Admin	Secret Officer	—	✅ (via KV audit)
Data Platform SP	Reader	Read	✅ (for pipeline)
CI/CD SP (WIF)	Reader	—	✅ (for validation)
Developer	❌ None	❌ None	❌
BI Analyst	❌ None	❌ None	❌
DLT Pipeline	(via workspace MI)	Read	✅
UC Function pii_hmac	(via workspace MI)	Read	✅
Enforced via:

Azure RBAC on Key Vault (Reader / Secrets User roles)

Unity Catalog grants on secret scope

Network ACL (Private Endpoint only)

4. Secret Rotation
4.1 PII HMAC Salt
Rotation frequency: Annually + on incident.
Owner: Data Platform Lead.
Procedure: See docs/SECRET_MANAGEMENT.md §5.1.

Warning: Rotating the salt breaks existing HMAC hashes. Requires
hash-versioning strategy. Do NOT rotate without coordinating with Compliance.

4.2 Other Secrets
Secret	Rotation	Automation
databricks-host	N/A (config, not secret)	—
databricks-resource-id	N/A (config)	—
smtp-password	Quarterly	Azure Function triggers on schedule

# .azure-pipelines/rotate-secrets.yml (scheduled quarterly)
schedules:
  - cron: "0 3 1 */3 *"
    displayName: 'Quarterly secret rotation check'
    branches: [main]

stages:
  - stage: RotationCheck
    jobs:
      - job: CheckAge
        steps:
          - task: AzureCLI@2
            displayName: 'Check secret age'
            inputs:
              azureSubscription: $(AZURE_SERVICE_CONNECTION)
              scriptType: bash
              inlineScript: |
                EXPIRY=$(az keyvault secret show \
                  --vault-name "kv-banking-prod" \
                  --name "smtp-password" \
                  --query "attributes.expires" -o tsv)

                if [[ -z "$EXPIRY" ]] || [[ "$(date -d "$EXPIRY" +%s)" -lt "$(date -d '+30 days' +%s)" ]]; then
                  echo "##vso[task.logissue type=warning]Secret rotation due in 30 days"
                fi

5. Audit Logging
Every access to Key Vault is logged to Azure Monitor:

Event	Logged?	Alert?
Secret read by Data Platform SP	✅	No (expected)
Secret read by CI SP	✅	No (expected)
Secret read by unknown principal	✅	🔴 ALERT
Secret write by non-admin	✅	🔴 ALERT
Vault deletion attempt	✅	🔴 ALERT
Public network access attempt	✅	🔴 ALERT
Retention: 365 days.

AzureDiagnostics
| where ResourceProvider == "MICROSOFT.KEYVAULT"
| where OperationName in ("SecretGet", "SecretSet", "SecretDelete")
| project TimeGenerated, OperationName, identity_claim_upn_s, requestUri_s, ResultType
| where identity_claim_upn_s !in ("sp-banking-dlt-prod", "sp-banking-ci-prod")
| where ResultType == "Success"
| order by TimeGenerated desc

6. Emergency Access
If the platform loses access to Key Vault (rare), the break-glass procedure:

InfoSec Admin logs in via Azure Portal

Verifies the incident is real (not a false positive)

Uses their Secret Officer role to read the affected secret

Provides the value over an encrypted channel (Azure Key Vault link)

Documents the break-glass access in the incident log

Every break-glass access requires:

Two-person integrity (InfoSec Admin + Platform Lead)

Post-incident review within 24 hours

Audit trail preserved for 8 years

7. What NOT to Put in Terraform
Terraform state contains all resource configuration, including databricks_secret.string_value in plaintext.

❌ Don't	✅ Do
databricks_secret.string_value = "mysecret"	Reference from KV: data "azurerm_key_vault_secret" "x"
azurerm_key_vault_secret.value = "mysecret"	Use lifecycle { ignore_changes = [value] } + set out-of-band
Any secret in *.tfvars	Reference from environment variables or CI variables
PAT in Terraform config	Use WIF (no secret needed)
8. Threat Model
Threat	Control
Compromised developer reads production secret	RBAC + Private Endpoint + audit
Leaked secret via Terraform state	Remote backend + encryption + RBAC
Secret in Git	gitleaks CI scan
Malicious insider deletes vault	Purge protection + soft delete + audit
Man-in-the-middle	Private Endpoint + TLS 1.2+
Key Vault compromise	Microsoft-managed HSM + audit logging

9. Change Log
Date	Change	Author
2026-10-04	Initial draft	Data Platform Engineering

