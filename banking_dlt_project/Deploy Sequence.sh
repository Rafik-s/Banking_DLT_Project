# 1. Provision secrets + security functions
terraform -chdir=terraform init
terraform -chdir=terraform apply -var-file=dev.tfvars

# 2. Validate the bundle
databricks bundle validate -t dev

# 3. Deploy
databricks bundle deploy -t dev

# 4. Trigger pipeline
databricks bundle run -t dev banking_medallion_dlt_pipeline

# 5. After first successful run — apply masks
terraform -chdir=terraform apply -var-file=dev.tfvars -target=databricks_sql_exec.uc_mask_attachments

# 6. Verify event log
databricks sql --warehouse-id <id> \
  "SELECT * FROM event_log(TABLE(banking_dev_catalog.raw_bronze.bronze_customers)) LIMIT 10;"