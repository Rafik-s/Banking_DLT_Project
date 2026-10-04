


```python
"""
MODULE: DATA CONTRACT VALIDATION

Loads contracts/*.yaml and validates against:
  1. contracts/_schema.yaml (meta-schema)
  2. The Python StructType in src/schemas_and_security.py
  3. Backward-compatibility with the previous version

Used by:
  - CI (scripts/validate_contracts.py)
  - Runtime (Bronze ingestion — fail-fast on drift)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Python type → Contract type mapping
# ---------------------------------------------------------------------------
PYTHON_TO_CONTRACT = {
    "StringType":   "string",
    "IntegerType":  "integer",
    "LongType":     "long",
    "DoubleType":   "double",
    "BooleanType":  "boolean",
    "TimestampType":"timestamp",
    "DateType":     "date",
    # Decimal handled specially via precision/scale
}


def load_contract(contract_path: Path) -> dict[str, Any]:
    """Load and parse a contract YAML file."""
    with open(contract_path, "r") as f:
        return yaml.safe_load(f)


def validate_against_meta_schema(contract: dict[str, Any], meta_schema_path: Path) -> list[str]:
    """
    Validate a contract against contracts/_schema.yaml using JSON Schema.
    Returns a list of error messages (empty = valid).
    """
    try:
        import jsonschema
    except ImportError:
        logger.warning("jsonschema not installed — skipping meta-schema validation")
        return []

    with open(meta_schema_path, "r") as f:
        meta_schema = yaml.safe_load(f)

    errors = []
    try:
        jsonschema.validate(contract, meta_schema)
    except jsonschema.ValidationError as e:
        errors.append(f"Meta-schema validation failed: {e.message} at {'.'.join(str(p) for p in e.absolute_path)}")
    return errors


def validate_python_schema_match(contract: dict[str, Any], python_schema) -> list[str]:
    """
    Verify that the Python StructType matches the contract schema exactly.
    Raises errors on:
      - Column count mismatch
      - Column name mismatch
      - Column order mismatch
      - Type mismatch
      - Nullability mismatch
    """
    errors = []

    contract_cols = contract["schema"]
    python_cols   = python_schema.fields

    if len(contract_cols) != len(python_cols):
        errors.append(
            f"Column count mismatch: contract has {len(contract_cols)}, "
            f"Python schema has {len(python_cols)}"
        )
        return errors

    for i, (c_col, p_field) in enumerate(zip(contract_cols, python_cols)):
        # Name
        if c_col["name"] != p_field.name:
            errors.append(
                f"Position {i}: name mismatch — contract='{c_col['name']}', "
                f"python='{p_field.name}'"
            )
            continue

        # Type
        p_type_name = type(p_field.dataType).__name__
        if p_type_name == "DecimalType":
            p_type = "decimal"
        else:
            p_type = PYTHON_TO_CONTRACT.get(p_type_name)

        if p_type != c_col["type"]:
            errors.append(
                f"Column '{c_col['name']}': type mismatch — "
                f"contract='{c_col['type']}', python='{p_type}'"
            )
            continue

        # Decimal precision/scale
        if p_type == "decimal":
            if p_field.dataType.precision != c_col.get("precision"):
                errors.append(
                    f"Column '{c_col['name']}': precision mismatch — "
                    f"contract={c_col.get('precision')}, python={p_field.dataType.precision}"
                )
            if p_field.dataType.scale != c_col.get("scale"):
                errors.append(
                    f"Column '{c_col['name']}': scale mismatch — "
                    f"contract={c_col.get('scale')}, python={p_field.dataType.scale}"
                )

        # Nullability
        c_nullable = bool(c_col.get("nullable", True))
        p_nullable = bool(p_field.nullable)
        if c_nullable != p_nullable:
            errors.append(
                f"Column '{c_col['name']}': nullability mismatch — "
                f"contract={c_nullable}, python={p_nullable}"
            )

    return errors


def validate_backward_compatible(
    new_contract: dict[str, Any],
    old_contract: dict[str, Any],
) -> list[str]:
    """
    Verify that a new contract is backward-compatible with the previous version.

    Rules (semver):
      - PATCH bump: no schema change allowed
      - MINOR bump: only additive changes (new nullable columns at the end)
      - MAJOR bump: breaking changes allowed (rename, type change, drop)
    """
    errors = []
    new_ver = new_contract["version"]
    old_ver = old_contract["version"]

    def _parse(v: str) -> tuple[int, int, int]:
        return tuple(int(x) for x in v.split("."))

    new_major, new_minor, new_patch = _parse(new_ver)
    old_major, old_minor, old_patch = _parse(old_ver)

    old_cols = {c["name"]: c for c in old_contract["schema"]}
    new_cols = {c["name"]: c for c in new_contract["schema"]}

    dropped   = set(old_cols) - set(new_cols)
    added     = set(new_cols) - set(old_cols)
    renamed_or_changed = set()

    for name in set(old_cols) & set(new_cols):
        if old_cols[name] != new_cols[name]:
            renamed_or_changed.add(name)

    is_breaking = bool(dropped or renamed_or_changed)

    if is_breaking and new_major == old_major:
        errors.append(
            f"Breaking change requires MAJOR bump: "
            f"was {old_ver}, is {new_ver}. "
            f"Dropped={sorted(dropped)}, changed={sorted(renamed_or_changed)}"
        )

    if (added or dropped or renamed_or_changed) and (new_minor == old_minor and new_major == old_major):
        errors.append(
            f"Schema change requires MINOR or MAJOR bump: was {old_ver}, is {new_ver}"
        )

    if not (added or dropped or renamed_or_changed) and new_patch == old_patch:
        errors.append(
            f"No schema change detected — version unchanged ({new_ver})"
        )

    # New columns must be nullable for MINOR bump
    for name in added:
        if not new_cols[name].get("nullable", True) and new_minor > old_minor and new_major == old_major:
            errors.append(
                f"New column '{name}' must be nullable for MINOR bump"
            )

    return errors