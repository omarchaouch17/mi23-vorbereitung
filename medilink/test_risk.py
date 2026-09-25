"""Tests for risk.py - run with: py test_risk.py"""
from risk import framingham

# 1. Reference values (verified against Framingham Heart Study coefficients)
assert framingham("m", 55, 213, 50, 120, False, False) == 6.5
assert framingham("m", 55, 213, 50, 120, False, True) == 12.7
assert framingham("m", 75, 250, 40, 150, True, True) == 30.1
assert framingham("f", 55, 213, 50, 120, False, False) == 1.2
assert framingham("f", 65, 240, 45, 145, True, True) == 14.1

# 2. Treatment only counts if SBP > 120
assert framingham("m", 50, 200, 50, 118, True, False) == \
       framingham("m", 50, 200, 50, 118, False, False)
assert framingham("m", 50, 200, 50, 130, True, False) > \
       framingham("m", 50, 200, 50, 130, False, False)

# 3. Plausibility: smoking and higher BP must increase risk
assert framingham("f", 60, 220, 50, 130, False, True) > \
       framingham("f", 60, 220, 50, 130, False, False)
assert framingham("m", 60, 220, 50, 160, False, False) > \
       framingham("m", 60, 220, 50, 120, False, False)

# 4. Invalid input must raise ValueError
for bad in [("x", 50, 200, 50, 120, False, False),   # unknown sex
            ("m", 29, 200, 50, 120, False, False),   # too young
            ("m", 80, 200, 50, 120, False, False),   # too old
            ("f", 50, 0, 50, 120, False, False)]:    # impossible value
    try:
        framingham(*bad)
        assert False, f"no error for {bad}"
    except ValueError:
        pass

print("All tests passed.")
