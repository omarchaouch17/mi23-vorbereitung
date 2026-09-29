import math

KOEFF_MAENNER = {
    "ln_age": 52.00961, "ln_tchol": 20.014077, "ln_hdl": -0.905964,
    "ln_sbp": 1.305784, "trt_htn": 0.241549, "smoker": 12.096316,
    "ln_age_x_ln_tchol": -4.605038, "ln_age_x_smoker": -2.84367,
    "ln_age_x_ln_age": -2.93323
}
KONSTANTE_MAENNER = 172.300168

def framingham_maenner(alter, gesamt_chol, hdl, sbp, behandelt_hypertonie, raucher):
    ln_age = math.log(alter)
    ln_tchol = math.log(gesamt_chol)
    ln_hdl = math.log(hdl)
    ln_sbp = math.log(sbp)
    smoker_val = 1 if raucher else 0
    trt_val = 1 if behandelt_hypertonie else 0

    L = (KOEFF_MAENNER["ln_age"] * ln_age
         + KOEFF_MAENNER["ln_tchol"] * ln_tchol
         + KOEFF_MAENNER["ln_hdl"] * ln_hdl
         + KOEFF_MAENNER["ln_sbp"] * ln_sbp
         + KOEFF_MAENNER["trt_htn"] * trt_val
         + KOEFF_MAENNER["smoker"] * smoker_val
         + KOEFF_MAENNER["ln_age_x_ln_tchol"] * ln_age * ln_tchol
         + KOEFF_MAENNER["ln_age_x_smoker"] * ln_age * smoker_val
         + KOEFF_MAENNER["ln_age_x_ln_age"] * ln_age * ln_age)

    A = L - KONSTANTE_MAENNER
    B = math.exp(A)
    risiko_prozent = round((1 - 0.9402 ** B) * 100, 1)
    return risiko_prozent


ergebnis = framingham_maenner(
    alter=55,
    gesamt_chol=213,
    hdl=50,
    sbp=120,
    behandelt_hypertonie=False,
    raucher=False
)
print(f"10-Jahres-Risiko: {ergebnis}%")