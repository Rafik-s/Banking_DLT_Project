# Pull Request

## What does this change do?

<!-- 1-3 sentences describing the change -->

## Why is this change needed?

<!-- Link to issue, ticket, or context -->

Closes #<!-- issue number -->

## Type of change

- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change (fix or feature that changes existing behavior)
- [ ] Documentation
- [ ] Refactor / cleanup
- [ ] CI/CD / infrastructure

## Scope

- [ ] Bronze layer
- [ ] Silver layer
- [ ] Gold layer
- [ ] Contracts
- [ ] Terraform / infrastructure
- [ ] CI/CD
- [ ] Documentation
- [ ] Tests

## How was this tested?

- [ ] Unit tests pass locally (`pytest tests/unit/ -v`)
- [ ] DAB validates (`databricks bundle validate -t dev`)
- [ ] Terraform validates (`terraform validate`)
- [ ] Deployed to Dev and pipeline ran successfully
- [ ] Manual verification via DLT event log

## Checklist

### Code
- [ ] No hardcoded catalogs, paths, or secrets
- [ ] Config uses `dlt.config.get()` with no defaults
- [ ] SCD2 `sequence_by` uses source-event time (not `current_timestamp()`)
- [ ] Watermarks added for streaming tables with event-time semantics
- [ ] `cluster_by` set for new fact tables
- [ ] PII columns tagged and masked
- [ ] No `uuid()` or non-deterministic functions for IDs

### Data Contracts
- [ ] If schema changed, `contracts/{dataset}.yaml` is updated
- [ ] Version bumped (MAJOR / MINOR / PATCH) per semver rules
- [ ] `change_log` entry added in the contract
- [ ] Backward-compatibility check passes in CI

### Testing
- [ ] New tests added or existing tests updated
- [ ] All tests pass locally

### Documentation
- [ ] `README.md` updated if user-facing behavior changed
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] `docs/` updated if architecture or operations changed

### Security
- [ ] No secrets in code
- [ ] gitleaks pre-commit passes
- [ ] If touching PII: `docs/SECURITY_BOUNDARY.md` reflects the change
- [ ] If touching CI/CD: no PATs introduced

## Breaking Changes

<!-- If this is a breaking change, describe:
     - What breaks
     - Who is affected
     - Migration steps
     - Rollback plan -->

N/A

## Screenshots / Logs

<!-- If applicable, paste relevant screenshots or log excerpts -->

## Reviewer Notes

<!-- Anything specific you want reviewers to look at? -->