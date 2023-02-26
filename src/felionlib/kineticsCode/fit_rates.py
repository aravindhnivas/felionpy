from uncertainties import ufloat
import uncertainties.unumpy as unp
import numpy as np
from scipy.optimize import curve_fit


def main(args):
    # print(f"{args=}", flush=True)
    polyOrder = float(args["polyOrder"])
    addIntercept = bool(args["addIntercept"])
    fitted_values = args["fitted_values"]
    number_densities = args["number_densities"]

    rate_constant_guess = float(args["$rate_constant_guess"])

    # print(f"{fitted_values['val']=}", flush=True)

    def fit_func(x, m, c):
        if addIntercept:
            return m * x**polyOrder + c
        return m * x**polyOrder

    x = np.array(number_densities["val"])

    y = np.array(fitted_values["val"])
    y_err = np.array(fitted_values["std"])

    if addIntercept:
        intercept_guess = float(args["$intercept_guess"])
        p0 = [rate_constant_guess, intercept_guess]
    else:
        p0 = [rate_constant_guess]

    popt, pcov = curve_fit(fit_func, x, y, sigma=y_err, absolute_sigma=True, p0=p0)
    perr = np.sqrt(np.diag(pcov))

    upop = unp.uarray(popt, perr)

    if addIntercept:
        slope = upop[0]
        intercept = upop[1]
    else:
        slope = upop
        intercept = 0

    x_val_std = unp.uarray(x, y_err)
    fitY = fit_func(x_val_std, *upop)

    print(f"{upop=}", flush=True)
    print(f"{fitY=}", flush=True)

    dataToSend = {
        "fitY": {
            "val": unp.nominal_values(fitY).tolist(),
            "std": unp.std_devs(fitY).tolist(),
            "name": f"fitted slope={upop[0]}; intercept={upop[1]}",
        },
        "fitted_slope": f"{slope}",
        "fitted_intercept": f"{intercept}",
    }

    return dataToSend
