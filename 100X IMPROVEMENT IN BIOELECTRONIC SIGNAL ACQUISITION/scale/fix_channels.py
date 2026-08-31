#!/usr/bin/env python3
"""
Repair channels that ended up misplaced, without disturbing the converged ones.

The earlier version assumed each channel's notch sat near its target frequency
and scanned a window there.  When a channel is badly detuned that window is
empty, every probe fails, and the channel stays broken - which is exactly what
happened to 7 and 8.  This version locates the real modes first, tunes the bias
at whichever mode belongs to the channel, and only then trims the tank.

Starting point for a detuned channel comes from physics rather than the design
table: the transistor adds Cox*W*L plus two overlaps to every tank, which at the
top of the band is a third of the tank value.

    C_tank = 1/(4*pi^2*f^2*L_loop) - C_device - cp
"""

import json
import os
import sys

import numpy as np
from scipy.signal import find_peaks

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cotune10 import simulate, one_notch  # noqa: E402
from gen_nchan import LADDER_F  # noqa: E402

COX = 1.564e-15
L_LOOP = 100e-9


def device_cap_pF(W, L, overlap=0.5):
    return (COX * W * L + 2 * overlap * COX * W) * 1e12


def seed_cap(f_mhz, cdev, cp_fF):
    ctot = 1.0 / (4 * np.pi ** 2 * (f_mhz * 1e6) ** 2 * L_LOOP) * 1e12
    return max(0.5, ctot - cdev - cp_fF / 1000.0)


def main():
    cfgp = os.path.join(HERE, sys.argv[1])
    chans = [int(x) - 1 for x in sys.argv[2].split(",")]
    rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    cfg = json.load(open(cfgp))
    caps, cps, its = cfg["caps"], cfg["cps"], cfg["its"]
    W, L, VDD = cfg["W"], cfg["L"], cfg["vdd"]
    cdev = device_cap_pF(W, L)
    print(f"device adds {cdev:.3f} pF to every tank")

    for k in chans:
        caps[k] = seed_cap(LADDER_F[k], cdev, cps[k])
        print(f"  ch{k+1} tank reseeded to {caps[k]:.4f} pF for {LADDER_F[k]:.2f} MHz")

    for rnd in range(rounds):
        r = simulate(caps, cps, its, W, L, VDD, 35, 215, 150000, tag="fxfull")
        if r is None:
            print("full scan diverged"); return
        f, db = r
        idx, _ = find_peaks(-db, prominence=0.02)
        modes = np.array(sorted(f[i] for i in idx))
        print(f"--- round {rnd}: modes at "
              + ", ".join(f"{m/1e6:.2f}" for m in modes))

        for k in chans:
            tgt = LADDER_F[k] * 1e6
            # take the nearest mode that is not already owned by a neighbour
            others = [LADDER_F[j] * 1e6 for j in range(10) if j not in chans]
            cand = [m for m in modes
                    if all(abs(m - o) > 0.02 * o for o in others)]
            if not cand:
                cand = list(modes)
            f0 = min(cand, key=lambda m: abs(m - tgt))
            half = max(0.4e6, 0.008 * f0)
            lo, hi = (f0 - half) / 1e6, (f0 + half) / 1e6
            base = its[k]
            best = (base, -1.0, None, None)
            for cur in base * np.geomspace(0.3, 3.0, 14):
                trial = list(its); trial[k] = cur
                rz = simulate(caps, cps, trial, W, L, VDD, lo, hi, 20000, tag=f"fx{k}")
                if rz is None:
                    continue
                nf0, dep, bw, peak = one_notch(*rz)
                if peak > 1.0:
                    continue
                if dep > best[1]:
                    best = (cur, dep, nf0, bw)
            centre = best[0]
            for cur in centre * np.linspace(0.94, 1.06, 21):
                trial = list(its); trial[k] = cur
                rz = simulate(caps, cps, trial, W, L, VDD, lo, hi, 20000, tag=f"fx{k}")
                if rz is None:
                    continue
                nf0, dep, bw, peak = one_notch(*rz)
                if peak > 1.0:
                    continue
                if dep > best[1]:
                    best = (cur, dep, nf0, bw)
            if best[1] > 0.3:
                its[k] = best[0]
                caps[k] *= (best[2] / tgt) ** 2
            bw = best[3]
            print(f"    ch{k+1}: mode {f0/1e6:8.3f} -> Itail={its[k]:.6f} mA  "
                  f"depth={best[1]:6.2f} dB  BW={bw/1e3 if bw and bw == bw else float('nan'):7.2f} kHz"
                  f"  C={caps[k]:.4f} pF", flush=True)

    cfg["caps"], cfg["its"] = caps, its
    json.dump(cfg, open(cfgp, "w"), indent=1)
    print("saved", cfgp)


if __name__ == "__main__":
    main()
