#!/usr/bin/env python3
"""
CONTRACT VALIDATION SCRIPT

Runs in CI on every PR. Validates:
  1. Every contracts/*.yaml is valid YAML
  2. Each validates against contracts/_schema.yaml
  3. Each matches the Python StructType in src/schemas_and_security.py
  4. Each is backward-compatible with the previous Git version

Usage:
    python scripts/validate_contracts.py --all
    python scripts/validate_contracts.py --dataset transactions
    python scripts/validate_contracts.py --all --git-diff   # compares to HEAD
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

# Add src to path
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

# Import contract validation module
spec = importlib.util.spec_from_file_location("contract_validation", SRC / "contract_validation.py")
cv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cv)

# Import Python schemas
spec2 = importlib.util.spec_from_file_location("schemas_and_security", SRC / "schemas_and_security.py")
schemas_mod = importlib.util.module_from_spec(spec2)
# Stub dlt and pyspark imports so we can load schemas without a Spark session
sys.modules.setdefault("dlt", type(sys)("dlt"))
spec2.loader.exec_module(schemas_mod)


CONTRACTS_DIR = ROOT / "contracts"
META_SCHEMA   = CONTRACTS_DIR / "_schema.yaml"


PYTHON_SCHEMA_MAP = {
    "customers":       "CUSTOMERS_SCHEMA",
    "accounts":        "ACCOUNTS_SCHEMA",
    "transactions":    "TRANSACTIONS_SCHEMA",
    "branches":        "BRANCHES_SCHEMA",
    "employees":       "EMPLOYEES_SCHEMA",
    "credit_cards":    "CREDIT_CARDS_SCHEMA",
    "loans":           "LOANS_SCHEMA",
    "kyc_documents":   "KYC_DOCUMENTS_SCHEMA",
    "fraud_alerts":    "FRAUD_ALERTS_SCHEMA",
    "atm_transactions":"ATM_TRANSACTIONS_SCHEMA",
}


def validate_one(contract_path: Path, git_diff: bool = False) -> list[str]:
    """Validate a single contract. Returns list of errors."""
    errors = []
    name = contract_path.stem

    print(f"  → {name}")

    # 1. Load
    try:
        contract = cv.load_contract(contract_path)
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]

    # 2. Meta-schema validation
    errors.extend(cv.validate_against_meta_schema(contract, META_SCHEMA))

    # 3. Python schema match
    if name in PYTHON_SCHEMA_MAP:
        python_schema = getattr(schemas_mod, PYTHON_SCHEMA_MAP[name])
        errors.extend(cv.validate_python_schema_match(contract, python_schema))
    else:
        errors.append(f"No Python schema mapping for '{name}' (update PYTHON_SCHEMA_MAP)")

    # 4. Backward-compatibility (compare to git HEAD version)
    if git_diff:
        try:
            old_yaml = subprocess.check_output(
                ["git", "show", f"HEAD:contracts/{contract_path.name}"],
                stderr=subprocess.DEVNULL,
            ).decode("utf-8")
            old_contract = yaml.safe_load(old_yaml)
            errors.extend(cv.validate_backward_compatible(contract, old_contract))
        except subprocess.CalledProcessError:
            # New contract — no HEAD version to compare
            pass

    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--dataset", type=str)
    parser.add_argument("--git-diff", action="store_true",
                        help="Compare against HEAD for backward-compat check")
    args = parser.parse_args()

    if not args.all and not args.dataset:
        parser.error("Pass --all or --dataset <name>")

    if args.dataset:
        contract_paths = [CONTRACTS_DIR / f"{args.dataset}.yaml"]
    else:
        contract_paths = sorted(
            p for p in CONTRACTS_DIR.glob("*.yaml") if not p.name.startswith("_")
        )

    print(f"Validating {len(contract_paths)} contract(s)...\n")

    all_errors = {}
    for path in contract_paths:
        if not path.exists():
            all_errors[str(path)] = [f"Contract not found: {path}"]
            continue
        errs = validate_one(path, git_diff=args.git_diff)
        if errs:
            all_errors[path.stem] = errs

    if all_errors:
        print("\n❌ Validation FAILED\n")
        for ds, errs in all_errors.items():
            print(f"  {ds}:")
            for e in errs:
                print(f"    - {e}")
        sys.exit(1)

    print(f"\n✅ All {len(contract_paths)} contracts valid.")


if __name__ == "__main__":
    main()