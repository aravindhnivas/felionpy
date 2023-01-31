from pathlib import Path as pt
import numpy as np


def get_skip_line(scanfile: str, location: pt):
    with open(location/scanfile, 'r') as f:
        skip = 0
        for line in f:
            if len(line) > 1:
                line = line.strip()
                if line == 'ALL:':
                    return skip + 1
            skip += 1
    return 0


def get_iterations(scanfile: str, location: pt):
    
    iterations: list = []
    with open(location/scanfile, 'r') as f:

        for line in f:
            if line.startswith('#mass'):
                iteration: int = int(line.split(':')[-1])
                iterations.append(iteration)
            else:
                continue
    iterations: np.ndarray = np.array(iterations, dtype=int)
    print(f"{iterations=}", flush=True)

    return iterations