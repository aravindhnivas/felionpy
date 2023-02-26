import numpy as np
from uncertainties import ufloat
import uncertainties.unumpy as unp
from scipy.optimize import curve_fit
from felionlib.utils.FELion_definitions import get_weighted_mean_from_uarray


def main(args):
    # print(f"{args=}", flush=True)
    polyOrder = float(args["polyOrder"])

    fitted_values = args["fitted_values"]
    number_densities = args["number_densities"]

    x = np.array(number_densities["val"], dtype=float)
    x_err = np.array(number_densities["std"], dtype=float)
    unp_x = unp.uarray(x, x_err)

    y = np.array(fitted_values["val"], dtype=float)
    y_err = np.array(fitted_values["std"], dtype=float)
    unp_y = unp.uarray(y, y_err)

    # print(f"{unp_x=}", flush=True)
    rate_constant = unp_y / unp_x**polyOrder

    dataToSend = {
        "rate_constant": {
            "val": unp.nominal_values(rate_constant).tolist(),
            "std": unp.std_devs(rate_constant).tolist(),
            "mean": f"{ufloat(unp.nominal_values(rate_constant).mean(), unp.nominal_values(rate_constant).std())}",
            "weighted_mean": f"{get_weighted_mean_from_uarray(rate_constant, ufloat_fmt=True)}",
            "ylabel_units": f"s<sup>-1</sup> cm<sup>{3 * polyOrder}</sup>",
        },
    }

    if not args["fit"]:
        return dataToSend

    addIntercept = bool(args["addIntercept"])
    rate_constant_guess = float(args["$rate_constant_guess"])

    # print(f"{fitted_values['val']=}", flush=True)

    def fit_func(x, m, c):
        if addIntercept:
            return m * x**polyOrder + c
        return m * x**polyOrder

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

    dataToSend = dataToSend | {
        "fitY": {
            "val": unp.nominal_values(fitY).tolist(),
            "std": unp.std_devs(fitY).tolist(),
            "name": f"fitted slope={upop[0]}; intercept={upop[1]}",
        },
        "fitted_slope": f"{slope}",
        "fitted_intercept": f"{intercept}",
    }

    return dataToSend
