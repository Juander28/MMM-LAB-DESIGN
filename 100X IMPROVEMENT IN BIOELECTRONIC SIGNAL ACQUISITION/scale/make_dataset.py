#!/usr/bin/env python3
"""
Produce every AC dataset the report needs from a co-tuned configuration:
one full-span sweep and one high-resolution zoom per channel.
"""

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cotune10 import simulate, one_notch  # noqa: E402
from gen_nchan import LADDER_F  # noqa: E402
from scipy.signal import find_peaks  # noqa: E402

SC = os.environ.get("SCRATCH", "/tmp")


def main():
    cfgname = sys.argv[1] if len(sys.argv) > 1 else "cotune10_k1000.json"
    tag = sys.argv[2] if len(sys.argv) > 2 else "k1000"
    cfg = json.load(open(os.path.join(HERE, cfgname)))
    caps, cps, its = cfg["caps"], cfg["cps"], cfg["its"]
    W, L, VDD = cfg["W"], cfg["L"], cfg["vdd"]

    print("full span 35-215 MHz ...")
    r = simulate(caps, cps, its, W, L, VDD, 35, 215, 200000, tag=f"full_{tag}")
    if r is None:
        print("diverged"); return
    f, db = r
    np.save(f"{SC}/ds_{tag}_full.npy", np.vstack([f, db]))
    idx, _ = find_peaks(-db, prominence=0.05)
    modes = sorted(f[i] for i in idx)
    print(f"  {len(modes)} modes: " + ", ".join(f"{m/1e6:.2f}" for m in modes))

    rows = []
    for k, f0 in enumerate(modes[:10]):
        half = max(0.12e6, 0.0025 * f0)
        lo, hi = (f0 - half) / 1e6, (f0 + half) / 1e6
        print(f"zoom ch{k+1} around {f0/1e6:.3f} MHz ({lo:.3f}-{hi:.3f}) ...")
        rz = simulate(caps, cps, its, W, L, VDD, lo, hi, 60000, tag=f"z{k}_{tag}")
        if rz is None:
            continue
        fz, dbz = rz
        np.save(f"{SC}/ds_{tag}_zoom{k}.npy", np.vstack([fz, dbz]))
        nf0, dep, bw, peak = one_notch(fz, dbz)
        q = nf0 / bw if bw == bw and bw > 0 else float("nan")
        rows.append(dict(ch=k + 1, target=LADDER_F[k], f0=nf0, depth=dep,
                         bw=bw, q=q, itail=its[k], cap=caps[k], cp=cps[k]))
        print(f"    f0={nf0/1e6:9.4f} MHz  depth={dep:6.2f} dB  "
              f"BW={bw/1e3 if bw == bw else float('nan'):8.2f} kHz  Q_L={q:8.0f}")

    json.dump(rows, open(f"{SC}/ds_{tag}_rows.json", "w"), indent=1)
    ok = sum(1 for r_ in rows if r_["depth"] > 3 and r_["bw"] == r_["bw"]
             and r_["bw"] <= 30e3)
    print(f"\nchannels meeting depth>3dB and BW<=30kHz: {ok}/10")


if __name__ == "__main__":
    main()
