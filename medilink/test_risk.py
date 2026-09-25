"""Tests for risk.py - pytest version. Run with: py -m pytest -v"""
import pytest
from risk import framingham


# ---- Level 3: parametrize - one test function, many cases ----------------
@pytest.mark.parametrize("args, expected", [
    (("m", 55, 213, 50, 120, False, False), 6.5),
    (("m", 55, 213, 50, 120, False, True), 12.7),
    (("m", 75, 250, 40, 150, True, True), 30.1),
    (("f", 55, 213, 50, 120, False, False), 1.2),
    (("f", 65, 240, 45, 145, True, True), 14.1),
])
def test_reference_values(args, expected):
    assert framingham(*args) == expected


# ---- Rule: treatment only counts if SBP > 120 -----------------------------
def test_treatment_ignored_at_sbp_120_or_below():
    assert framingham("m", 50, 200, 50, 118, True, False) == \
           framingham("m", 50, 200, 50, 118, False, False)


def test_treatment_increases_risk_above_120():
    assert framingham("m", 50, 200, 50, 130, True, False) > \
           framingham("m", 50, 200, 50, 130, False, False)


# ---- Plausibility ---------------------------------------------------------
def test_smoking_increases_risk():
    assert framingham("f", 60, 220, 50, 130, False, True) > \
           framingham("f", 60, 220, 50, 130, False, False)


def test_higher_bp_increases_risk():
    assert framingham("m", 60, 220, 50, 160, False, False) > \
           framingham("m", 60, 220, 50, 120, False, False)


# ---- Level 3: invalid input must raise ValueError -------------------------
@pytest.mark.parametrize("bad_args", [
    ("x", 50, 200, 50, 120, False, False),   # unknown sex
    ("m", 29, 200, 50, 120, False, False),   # too young
    ("m", 80, 200, 50, 120, False, False),   # too old
    ("f", 50, 0, 50, 120, False, False),     # impossible value
])
def test_invalid_input_raises(bad_args):
    with pytest.raises(ValueError):
        framingham(*bad_args)


# ---- Edge cases: bugs live at boundaries ----------------------------------
@pytest.mark.parametrize("age", [30, 79])
def test_age_boundaries_are_valid(age):
    result = framingham("m", age, 200, 50, 120, False, False)
    assert 0 < result < 100

def test_mmol_input_raises():
    # Cholesterol in mmol/L instead of mg/dL must be rejected
    with pytest.raises(ValueError):
        framingham("m", 55, 5.5, 1.3, 120, False, False)