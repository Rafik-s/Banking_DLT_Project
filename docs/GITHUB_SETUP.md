# 🐙 GitHub Configuration Guide

> **Owner:** Rafik-s
> **Last reviewed:** 2026-10-04

This document describes the GitHub-native settings that should be enabled on
this repository to match the security posture of the code.

Some of these are **one-time setup steps** that must be done via the GitHub UI
(cannot be enforced via code).

---

## 1. Branch Protection

**Settings → Branches → Add branch protection rule**

### For `main`

| Setting | Value |
|---|---|
| Require a pull request before merging | ✅ |
| Require approvals | 2 |
| Dismiss stale PR approvals when new commits are pushed | ✅ |
| Require review from Code Owners | ✅ |
| Require status checks to pass | ✅ |
| Require branches to be up to date | ✅ |
| Require signed commits | ✅ |
| Require linear history | ✅ |
| Include administrators | ✅ |
| Restrict who can push | Only maintainers |
| Allow force pushes | ❌ |
| Allow deletions | ❌ |

### Required status checks

- `Security & Static Analysis / Gitleaks`
- `Security & Static Analysis / Bandit`
- `Security & Static Analysis / Checkov`
- `ContractValidation / ValidateContracts`
- `DABValidate / Validate`
- `CodeQL / Analyze Python`
- `Markdown Lint / Lint Markdown`
- `Link Check / Check Markdown Links`

### For `develop`

Same as `main` but with **1 approval** instead of 2.

---

## 2. GitHub Advanced Security

**Settings → Code security and analysis**

| Feature | Enable? |
|---|---|
| Dependency graph | ✅ |
| Dependabot alerts | ✅ |
| Dependabot security updates | ✅ |
| Dependabot version updates | ✅ (via `.github/dependabot.yml`) |
| CodeQL analysis | ✅ (via workflow) |
| Secret scanning | ✅ (free for public repos) |
| Push protection for secrets | ✅ |
| Private vulnerability reporting | ✅ |

**Note:** GitHub secret scanning is free for public repositories. It
**complements** gitleaks — GitHub catches known token formats (AWS, Azure, etc.)
at push time; gitleaks catches custom patterns (Databricks PATs, PAN, Aadhaar)
via CI.

---

## 3. Signed Commits

**Setup (one-time per developer):**

```bash
# Generate a GPG key (if you don't have one)
gpg --full-generate-key
# Choose: RSA and RSA, 4096 bits, no expiration (or 2 years)

# Get the key ID
gpg --list-secret-keys --keyid-format=long

# Export the public key
gpg --armor --export <KEY_ID>

# Add to GitHub: Settings → SSH and GPG keys → New GPG key

Configure Git to sign:

bash
git config --global user.signingkey <KEY_ID>
git config --global commit.gpgsign true
git config --global tag.gpgsign true
Verify:

bash
git log --show-signature
# Look for "Good signature from ..."
GitHub will now show "Verified" badges on signed commits.

4. CODEOWNERS
Already committed (.github/CODEOWNERS or CODEOWNERS at root).

Test it:

Open a PR that touches src/silver_transformation.py

GitHub should auto-request review from @Rafik-s

PR cannot merge until review is complete (with branch protection)

5. Security Advisories
Settings → Code security → Advisories → Enable private vulnerability reporting

This lets security researchers report vulnerabilities privately before
disclosure. See SECURITY.md for the disclosure policy.

6. Repository Settings
Setting	Value
Description	Enterprise-grade reference implementation of a Tier-1 banking data platform on Azure Databricks
Website	(leave blank, or link to your blog post if you write one)
Topics	databricks, delta-lake, dlt, unity-catalog, medallion-architecture, banking, terraform, data-engineering, spark, pyspark
Features → Issues	✅
Features → Discussions	✅
Features → Projects	Optional
Features → Wiki	❌ (use docs/ instead)
Features → Sponsorships	Optional
Merge button	Allow squash merges only
Auto-delete head branches	✅
Default branch	main

7. GitHub Environments (for deployment approvals)
Settings → Environments

Create:

Environment	Protection Rules
dev	None (auto-deploy)
qa	1 required reviewer
prod	2 required reviewers + wait timer (5 min)
Used by .azure-pipelines/azure-pipelines.yml — the deployment: job type
enforces these rules.

8. Tags & Releases
Tag releases with semver:

bash
git tag -a v1.0.0 -m "Release v1.0.0 — Initial reference implementation"
git push origin v1.0.0
Create a GitHub Release:

Releases → Draft a new release

Select the tag

Use the CHANGELOG.md section for the release notes

Attach build artefacts if any

Publish

9. Notifications
Settings → Notifications

Recommended:

✅ Participating and @mentions

✅ Security alerts

❌ All activity (too noisy)

Custom routing:

security-advisories@ → InfoSec team (if applicable)

CI failures → team channel

10. Testing the Setup
Test 1 — Branch protection works
bash
git checkout main
echo "test" >> README.md
git commit -am "test: should be blocked"
git push origin main
# Expected: rejected — "protected branch update failed"
Test 2 — Secret scanning works
# DO NOT PUSH — this is a test
echo "dapi1234567890abcdef1234567890ab" > test.txt
git add test.txt
git commit -m "test: fake PAT"
git push origin test-branch
# Expected: push rejected by GitHub secret scanning (or gitleaks in CI)
Test 3 — CodeQL runs
Open a PR, then check Actions → CodeQL → Analysis. Should complete in 3–5 min.

Test 4 — Dependabot works
Check Insights → Dependency graph → Dependabot. Should show any CVEs and
scheduled update PRs.

Test 5 — CODEOWNERS works
Open a PR touching src/*.py. Review should be auto-requested.

11. Maintenance Checklist
Weekly:

□ Review Dependabot PRs
□ Check Security tab for new alerts
□ Verify CI is passing on main
Monthly:

□ Review branch protection rules
□ Audit GitHub Apps and integrations
□ Rotate any deploy keys
Quarterly:

□ Review CODEOWNERS
□ Review repository topics and description
□ Update SECURITY.md if policy changes
12. Change Log
Date	Change	Author
2026-10-04	Initial setup guide	Rafik-s
