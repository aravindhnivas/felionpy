import shutil
import io
import os
from os.path import join
import tempfile
import json
from pathlib import Path as pt
import cProfile
import pstats
from pstats import SortKey
import inspect
import contextlib
import sys
import numpy as np
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
from uncertainties import unumpy as unp, ufloat


def gaussian(x, amp, sig, cen):
    return amp * np.exp(-0.5 * ((x - cen) / sig) ** 2)


def move(pathdir, x):
    return (shutil.move(join(pathdir, x), join(pathdir, "DATA", x)), print("%s moved to DATA folder" % x))


class gauss_fit:
    def __init__(self, x, y):

        print(f"Sigma Guessed: {(x[np.argmax(y)] - x.min())/4}")

        p0 = [y.max(), (x[np.argmax(y)] - x.min()) / 4, x[np.argmax(y)]]
        pop, pcov = curve_fit(gaussian, x, y, p0=p0)

        perr = np.sqrt(np.diag(pcov))

        (
            self.uamplitude,
            self.usigma,
            self.uline_freq,
        ) = unp.uarray(pop, perr)

        self.fit_data = gaussian(x, *pop)

        self.ufwhm = 2 * self.usigma * np.sqrt(2 * np.log(2))

    def get_data(self):
        return self.fit_data, self.uline_freq, self.usigma, self.uamplitude, self.ufwhm

    def get_std(self, value):
        return value.std_dev

    def get_value(self, value):
        return value.nominal_value


def var_find(filename, var=None, get_defaults=True):

    if var is None:
        var = {"res": "m03_ao13_reso", "b0": "m03_ao09_width", "trap": "m04_ao04_sa_delay"}

    with open(filename, "r") as mfile:
        mfile = np.array(mfile.readlines())
    values = {}

    for line in mfile:
        if len(line.strip()) > 0 and line.split()[0] == "#":
            for j in var:
                if var[j] in line.split():
                    values[j] = float(line.split()[-3])

    if get_defaults:
        res = round(values["res"], 2) if "res" in values else "N/A"
        b0 = int(values["b0"] / 1000) if "b0" in values else "N/A"
        trap = int(values["trap"] / 1000) if "trap" in values else "N/A"
        return res, b0, trap

    else:
        return values


def read_dat_file(filename, norm_method):
    read_data = np.genfromtxt(filename).T
    xs = read_data[0]
    if norm_method == "Log":
        ys = read_data[1]
    elif norm_method == "Relative":
        ys = read_data[2]
    else:
        ys = read_data[3]
    return xs, ys


save_location = pt(tempfile.gettempdir()) / "com.felion.app"
if not save_location.exists():
    os.mkdir(save_location)


def sendData(dataToSend: dict, calling_file: str = "", filename: pt = None):

    if filename is None:
        if not calling_file:
            calling_file = pt(inspect.stack()[-1].filename).stem

        print(f"Writing computed file: {calling_file}_data.json", flush=True)

        filename = save_location / f"{calling_file}_data.json"
        os.remove(filename) if filename.exists() else None

    with open(filename, "w+") as f:
        data = json.dumps(dataToSend, sort_keys=True, indent=4, separators=(",", ": "))
        f.write(data)
        print(f"{filename} written", flush=True)


def convert_intesities(felixlocation, output_filename, wn, inten, norm_method):

    if pt(f"{felixlocation}/{output_filename}.felix").exists():
        felixfile = felixlocation / f"{output_filename}.felix"
    else:
        felixfile = felixlocation / f"{output_filename}.cfelix"

    powerfile = felixlocation / f"{output_filename}.pow"

    with open(powerfile) as f:
        for line in f:
            if line[0] == "#":
                if line.find("Hz") > -1:
                    felix_hz = int(line.split(" ")[1])
                    break

    pow_x, pow_y = np.genfromtxt(powerfile).T
    intepd_power = interp1d(pow_x, pow_y, kind="linear", fill_value="extrapolate")
    power_measured = intepd_power(wn)
    felix_hz = int(felix_hz)
    res, b0, trap = var_find(felixfile)

    nshots = int((trap / 1000) * felix_hz)
    total_power = power_measured * nshots

    if norm_method == "Relative":
        ratio = -((inten / 100) - 1)
    elif norm_method == "Log":
        ratio = np.e ** (-(inten / 1000) * total_power)
    else:
        logInten = (inten * 1e3) / wn
        ratio = np.e ** (-(logInten / 1000) * total_power)
    log_intensity = (-unp.log(ratio) / total_power) * 1000

    log_hv_intensity = (wn * log_intensity) / 1e3
    relative_depletion = (1 - ratio) * 100

    return (
        [relative_depletion.nominal_value, relative_depletion.std_dev],
        [log_intensity.nominal_value, log_intensity.std_dev],
        [log_hv_intensity.nominal_value, log_hv_intensity.std_dev],
    )


def readCodeFromFile(filename: str | pt):

    info = []
    codeToRun = ""
    start = False

    with open(filename, "r") as f:
        info = f.readlines()

    for line in info:

        if "```plaintext" in line:
            start = True
            continue
        if line == "```" or line == "```\n":
            start = False
            continue
        if start:
            codeToRun += line

    # print(f"{codeToRun=}", flush=True)
    return codeToRun


def profile_func(func):
    def profiled_func(*args, **kwargs):
        profiler = cProfile.Profile()
        try:
            profiler.enable()

            result = func(*args, **kwargs)

            profiler.disable()

            return result
        finally:
            profiler.print_stats()
            s = io.StringIO()
            sortby = SortKey.CUMULATIVE

            ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
            ps.print_stats()

            # Save profile

            frm = inspect.stack()[1]
            mod = inspect.getmodule(frm[0])
            filename = pt(mod.__file__)

            filelocation = filename.parent

            with open(filelocation / f"{filename.stem}.prof", "w+") as f:
                f.write(s.getvalue())

    return profiled_func


def get_profiler():
    try:
        from line_profiler import LineProfiler

        print("LineProfiler imported")

        def profile_line(func):
            def profiled_line(*args, **kwargs):
                try:
                    profiler = LineProfiler()
                    profiler.add_function(func)
                    profiler.enable_by_count()
                    return func(*args, **kwargs)

                finally:
                    with stdoutIO() as result:
                        profiler.print_stats()
                        output = result.getvalue()

                        # Save profile
                        frm = inspect.stack()[1]
                        mod = inspect.getmodule(frm[0])
                        filename = pt(mod.__file__)
                        print(f"{save_location=}")

                        with open(save_location / f"{filename.stem}_{func.__name__}.lprof", "w+") as f:
                            f.write(output)

            return profiled_line

        return profile_line

    except ImportError:

        def profile_line(func):
            "Helpful if you accidentally leave in production!"

            def nothing(*args, **kwargs):
                return func(*args, **kwargs)

            return nothing

        return profile_line


@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = io.StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old


def get_weighted_mean_from_uarray(uarr, ufloat_fmt=False, verbose=False):

    values = unp.nominal_values(uarr)
    sigma = unp.std_devs(uarr)

    varience = sigma**2
    weights = 1 / varience
    sum_weights = np.sum(weights)
    
    mean_weighted = np.sum(values * weights) / sum_weights
    
    s_int = 1 / np.sqrt(sum_weights)
    N = len(values)
    
    varience_ext = np.sum(weights*(values-mean_weighted)**2) / sum_weights

    s_ext = np.sqrt(varience_ext/(N-1))
    
    std_dev = max(s_int, s_ext)

    if verbose:
        print(f"{mean_weighted=:.2e}", flush=True)
        print(f"{s_int=:.1e}", flush=True)
        print(f"{s_ext=:.1e}", flush=True)
        print(f"{ufloat(mean_weighted, std_dev):.2e}", flush=True)
    
    if ufloat_fmt:
        return ufloat(mean_weighted, std_dev)
 
    return [mean_weighted, std_dev]
 