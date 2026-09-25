"""risk.py - Framingham Hard CHD 10-year risk (ATP III, 2001)

Coefficients: Framingham Heart Study / ATP III (Wilson et al.)
Valid for: ages 30-79, no diabetes, no known coronary heart disease.

For demo/educational use only - not a diagnostic tool.
"""

import math

MODELS = {
    "m": {
        "coef": {
            "ln_age": 52.00961,
            "ln_tchol": 20.014077,
            "ln_hdl": -0.905964,
            "ln_sbp": 1.305784,
            "trt_htn": 0.241549,
            "smoker": 12.096316,
            "ln_age_x_ln_tchol": -4.605038,
            "ln_age_x_smoker": -2.84367,
            "ln_age_x_ln_age": -2.93323,
        },
        "constant": 172.300168,
        "baseline_survival": 0.9402,
        "smoker_age_cap": 70,  # above 70: ln(70)*smoker
    },
    "f": {
        "coef": {
            "ln_age": 31.764001,
            "ln_tchol": 22.465206,
            "ln_hdl": -1.187731,
            "ln_sbp": 2.552905,
            "trt_htn": 0.420251,
            "smoker": 13.07543,
            "ln_age_x_ln_tchol": -5.060998,
            "ln_age_x_smoker": -2.996945,
            "ln_age_x_ln_age": 0.0,  # women: no quadratic age term
        },
        "constant": 146.5933061,
        "baseline_survival": 0.98767,
        "smoker_age_cap": 78,  # above 78: ln(78)*smoker
    },
}


def framingham(sex, age, total_chol, hdl, sbp, treated_hypertension, smoker):
    """Return the 10-year risk of MI or coronary death in % (1 decimal).

    sex: 'm' or 'f'; total_chol and hdl in mg/dL; sbp in mmHg.
    """
    if sex not in MODELS:
        raise ValueError("sex must be 'm' or 'f'")
    if not 30 <= age <= 79:
        raise ValueError("score is only validated for ages 30-79")
    if min(total_chol, hdl, sbp) <= 0:
        raise ValueError("lab values and blood pressure must be positive")

    model = MODELS[sex]
    c = model["coef"]

    ln_age = math.log(age)
    ln_age_smoking = math.log(min(age, model["smoker_age_cap"]))
    ln_tchol = math.log(total_chol)
    smk = 1 if smoker else 0
    trt = 1 if (treated_hypertension and sbp > 120) else 0

    L = (
        c["ln_age"] * ln_age
        + c["ln_tchol"] * ln_tchol
        + c["ln_hdl"] * math.log(hdl)
        + c["ln_sbp"] * math.log(sbp)
        + c["trt_htn"] * trt
        + c["smoker"] * smk
        + c["ln_age_x_ln_tchol"] * ln_age * ln_tchol
        + c["ln_age_x_smoker"] * ln_age_smoking * smk
        + c["ln_age_x_ln_age"] * ln_age * ln_age
    )

    risk = 1 - model["baseline_survival"] ** math.exp(L - model["constant"])
    return round(risk * 100, 1)


if __name__ == "__main__":
    cases = [
        ("m", 55, 213, 50, 120, False, False),
        ("m", 55, 213, 50, 120, False, True),
        ("m", 75, 250, 40, 150, True, True),
        ("f", 55, 213, 50, 120, False, False),
        ("f", 65, 240, 45, 145, True, True),
    ]
    for case in cases:
        print(case, "->", framingham(*case), "%")
