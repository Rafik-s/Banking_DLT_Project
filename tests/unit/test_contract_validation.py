"""Unit tests for contract validation logic."""
import importlib.util
import sys
from pathlib import Path

import pytest
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DecimalType, TimestampType, DateType,
)

ROOT = Path(__file__).resolve().parent.parent.parent
SRC  = ROOT / "src"

spec = importlib.util.spec_from_file_location("contract_validation", SRC / "contract_validation.py")
cv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cv)


# ---------------------------------------------------------------------------
# Python schema match
# ---------------------------------------------------------------------------

def test_python_schema_match_exact():
    contract = {
        "schema": [
            {"name": "id",   "type": "string",   "nullable": False},
            {"name": "name", "type": "string",   "nullable": True},
        ]
    }
    python_schema = StructType([
        StructField("id",   StringType(), False),
        StructField("name", StringType(), True),
    ])
    assert cv.validate_python_schema_match(contract, python_schema) == []


def test_python_schema_mismatch_column_count():
    contract = {"schema": [{"name": "id", "type": "string", "nullable": False}]}
    python_schema = StructType([
        StructField("id",   StringType(), False),
        StructField("name", StringType(), True),
    ])
    errors = cv.validate_python_schema_match(contract, python_schema)
    assert len(errors) == 1
    assert "Column count mismatch" in errors[0]


def test_python_schema_mismatch_name():
    contract = {"schema": [{"name": "customer_id", "type": "string", "nullable": False}]}
    python_schema = StructType([StructField("cust_id", StringType(), False)])
    errors = cv.validate_python_schema_match(contract, python_schema)
    assert any("name mismatch" in e for e in errors)


def test_python_schema_mismatch_type():
    contract = {"schema": [{"name": "amount", "type": "integer", "nullable": True}]}
    python_schema = StructType([StructField("amount", StringType(), True)])
    errors = cv.validate_python_schema_match(contract, python_schema)
    assert any("type mismatch" in e for e in errors)


def test_python_schema_mismatch_nullability():
    contract = {"schema": [{"name": "id", "type": "string", "nullable": True}]}
    python_schema = StructType([StructField("id", StringType(), False)])
    errors = cv.validate_python_schema_match(contract, python_schema)
    assert any("nullability mismatch" in e for e in errors)


def test_python_schema_decimal_precision_scale():
    contract = {"schema": [
        {"name": "amount", "type": "decimal", "precision": 18, "scale": 2, "nullable": True},
    ]}
    python_schema = StructType([StructField("amount", DecimalType(18, 2), True)])
    assert cv.validate_python_schema_match(contract, python_schema) == []


def test_python_schema_decimal_mismatch_precision():
    contract = {"schema": [
        {"name": "amount", "type": "decimal", "precision": 18, "scale": 2, "nullable": True},
    ]}
    python_schema = StructType([StructField("amount", DecimalType(20, 2), True)])
    errors = cv.validate_python_schema_match(contract, python_schema)
    assert any("precision mismatch" in e for e in errors)


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------

def test_backward_compat_patch_only():
    """PATCH bump with no schema change is fine."""
    old = {"version": "1.0.0", "schema": [{"name": "id", "type": "string", "nullable": False}]}
    new = {"version": "1.0.1", "schema": [{"name": "id", "type": "string", "nullable": False}]}
    errors = cv.validate_backward_compatible(new, old)
    assert errors == []


def test_backward_compat_additive_requires_minor():
    """Adding a column requires at least MINOR bump."""
    old = {"version": "1.0.0", "schema": [{"name": "id", "type": "string", "nullable": False}]}
    new = {"version": "1.0.0", "schema": [
        {"name": "id",   "type": "string", "nullable": False},
        {"name": "name", "type": "string", "nullable": True},
    ]}
    errors = cv.validate_backward_compatible(new, old)
    assert any("MINOR or MAJOR bump" in e for e in errors)


def test_backward_compat_additive_with_minor_bump():
    old = {"version": "1.0.0", "schema": [{"name": "id", "type": "string", "nullable": False}]}
    new = {"version": "1.1.0", "schema": [
        {"name": "id",   "type": "string", "nullable": False},
        {"name": "name", "type": "string", "nullable": True},
    ]}
    errors = cv.validate_backward_compatible(new, old)
    assert errors == []


def test_backward_compat_breaking_requires_major():
    """Dropping a column requires MAJOR bump."""
    old = {"version": "1.0.0", "schema": [
        {"name": "id",   "type": "string", "nullable": False},
        {"name": "name", "type": "string", "nullable": True},
    ]}
    new = {"version": "1.1.0", "schema": [{"name": "id", "type": "string", "nullable": False}]}
    errors = cv.validate_backward_compatible(new, old)
    assert any("MAJOR bump" in e for e in errors)


def test_backward_compat_breaking_with_major_bump():
    old = {"version": "1.0.0", "schema": [
        {"name": "id",   "type": "string", "nullable": False},
        {"name": "name", "type": "string", "nullable": True},
    ]}
    new = {"version": "2.0.0", "schema": [{"name": "id", "type": "string", "nullable": False}]}
    errors = cv.validate_backward_compatible(new, old)
    assert errors == []


def test_backward_compat_new_non_nullable_column_requires_major():
    """A new NON-nullable column breaks readers → MAJOR bump."""
    old = {"version": "1.0.0", "schema": [{"name": "id", "type": "string", "nullable": False}]}
    new = {"version": "1.1.0", "schema": [
        {"name": "id",         "type": "string", "nullable": False},
        {"name": "created_at", "type": "timestamp", "nullable": False},
    ]}
    errors = cv.validate_backward_compatible(new, old)
    assert any("must be nullable for MINOR" in e for e in errors)