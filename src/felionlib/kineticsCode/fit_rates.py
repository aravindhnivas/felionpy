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

    rate_constant = unp_y / unp_x**polyOrder
    mean_weighted = get_weighted_mean_from_uarray(rate_constant, ufloat_fmt=True, verbose=True)
    dataToSend = {
        "rate_constant": {
            "val": unp.nominal_values(rate_constant).tolist(),
            "std": unp.std_devs(rate_constant).tolist(),
            "weighted_mean": f"{mean_weighted:.2e}",
            "ylabel_units": f"s<sup>-1</sup> cm<sup>{3 * polyOrder}</sup>",
        },
    }

    if not args["fit"]:
        return dataToSend

    addIntercept = bool(args["addIntercept"])
    effective_rate_polyOrder = float(args["effective_rate_polyOrder"])

    ke = unp_y / unp_x**effective_rate_polyOrder
    ke_val = unp.nominal_values(ke)
    ke_std = unp.std_devs(ke)

    rate_constant_guess = float(args["$rate_constant_guess"])

    def fit_func(x, m, c):
        if addIntercept:
            return m * x**polyOrder + c
        return m * x**polyOrder

    if addIntercept:
        intercept_guess = float(args["$intercept_guess"])
        p0 = [rate_constant_guess, intercept_guess]
    else:
        p0 = [rate_constant_guess]

    popt, pcov = curve_fit(fit_func, x, ke_val, sigma=ke_std, absolute_sigma=True, p0=p0)
    perr = np.sqrt(np.diag(pcov))

    upop = unp.uarray(popt, perr)
    if addIntercept:
        slope = upop[0]
        intercept = upop[1]
    else:
        slope = upop
        intercept = 0

    # x_val_std = unp.uarray(x, x_err)
    fitX = np.linspace(0, x.max() * 1.5, 100)
    fitY = fit_func(fitX, *popt)
    # print(f"{upop=}", flush=True)
    # print(f"{fitY=}", flush=True)

    dataToSend = dataToSend | {
        # "fitY": {
        #     "val": unp.nominal_values(fitY).tolist(),
        #     "std": unp.std_devs(fitY).tolist(),
        #     "name": f"fitted slope={upop[0]}; intercept={upop[1]}",
        # },
        "ke": {
            "val": unp.nominal_values(ke).tolist(),
            "std": unp.std_devs(ke).tolist(),
        },
        "fitX": fitX.tolist(),
        "fitY": fitY.tolist(),
        "fitted_slope": f"{slope:.2e}",
        "fitted_intercept": f"{intercept:.2e}",
    }

    return dataToSend
