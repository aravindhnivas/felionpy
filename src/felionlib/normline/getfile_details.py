from pathlib import Path as pt
import numpy as np
from numpy.typing import NDArray
from felionlib.utils.FELion_definitions import sendData, var_find


def main(args):
    
    files = [pt(f) for f in args["files"]]
    dataToSend = {"files": []}

    for f in files:
    
        res, b0, trap = var_find(f)
        wn: NDArray = np.genfromtxt(f).T[0]
        
        val = {
            "filename": f.stem,
            "res": round(res, 1),
            "b0": round(b0, 1),
            "trap": round(trap / 1000, 1),
            "range": [int(wn.min()), int(wn.max())],
        }
        dataToSend["files"].append(val)
    sendData(dataToSend, calling_file=pt(__file__).stem)
    