#!/usr/bin/env python3
"""Third-stage bias refinement: the depth ridge is ~0.25 % wide, so a 2.5 %
grid walks straight past it.  This steps at 0.3 % around the current point."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from cotune10 import simulate, one_notch

def main():
    cfgp = os.path.join(HERE, sys.argv[1])
    cfg = json.load(open(cfgp))
    caps, cps, its = cfg["caps"], cfg["cps"], cfg["its"]
    W, L, VDD = cfg["W"], cfg["L"], cfg["vdd"]
    modes = [float(x) for x in sys.argv[2].split(",")]
    for k, f0 in enumerate(modes):
        if f0 <= 0:
            continue
        half = max(0.15e6, 0.003 * f0 * 1e6)
        lo, hi = (f0 * 1e6 - half) / 1e6, (f0 * 1e6 + half) / 1e6
        base = its[k]
        best = (base, -1.0, None, None)
        for frac in np.linspace(0.94, 1.06, 41):      # 0.3 % steps
            trial = list(its); trial[k] = base * frac
            r = simulate(caps, cps, trial, W, L, VDD, lo, hi, 25000, tag=f"rf{k}")
            if r is None: continue
            nf0, dep, bw, peak = one_notch(*r)
            if peak > 1.0: continue
            if dep > best[1]: best = (base * frac, dep, nf0, bw)
        if best[1] > 0.3:
            its[k] = best[0]
        bw = best[3]
        print(f"  ch{k+1:2d}: Itail={its[k]:.6f} mA  depth={best[1]:6.2f} dB  "
              f"BW={bw/1e3 if bw and bw==bw else float('nan'):8.2f} kHz", flush=True)
    cfg["its"] = its
    json.dump(cfg, open(cfgp, "w"), indent=1)
    print("saved", cfgp)

if __name__ == "__main__":
    main()
