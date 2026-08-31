#!/usr/bin/env python3
"""Re-size OPAM with a phase margin it can actually close a loop on.

The gain-optimal sizing has -36 degrees of margin.  Compensation on its own does
not rescue it: a Miller capacitor puts its right-half-plane zero at gm/C, and
with gm in microsiemens and mim plates in picofarads that zero lands on the
unity-gain frequency (measured: -117 degrees).  Loading the dominant node has no
zero but needs 4 mm2 of plate to buy 2 degrees.

So the margin has to come out of the sizing, and the search pays for it in gain.
Both starts are kept: the gain-optimal one, and one with the cross-coupled pair
turned down, since that pair is positive feedback and positive feedback is what
a margin is spent on.
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import optimize as O
import report as rep

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "best_opam_stable.json")


def main():
    vdd, sz, extra, vcm = rep.load_opam()
    base = dict(sz, vcm=vcm, **extra)
    starts = [
        ("gain-optimal", base),
        ("cross-coupling turned down", dict(base, w_cc=50, l_cc=400)),
        ("cross-coupling off", dict(base, w_cc=10, l_cc=2000)),
        # the output has to be able to sit at the common mode, so start with a
        # common mode up where the output stage actually lives
        ("common mode raised", dict(base, vcm=4.0)),
        ("common mode raised, weak cross-coupling",
         dict(base, vcm=4.0, w_cc=50, l_cc=400)),
    ]
    pool, log, best = ThreadPoolExecutor(O.WORKERS), [], None
    for tag, seed in starts:
        sz2 = dict(seed)
        for factors in (O.FACTORS, O.FINE):
            sz2, val, bad, info = O.coordinate_descent(O.OPAM, sz2, vdd, log,
                                                       pool, factors=factors)
        print("%-42s Av=%7.2f dB  PM=%+6.1f deg  Vout=%.2f  viol=%d %s"
              % (tag, info.get("av_db", float("nan")),
                 info.get("pm", float("nan")), info.get("vout", float("nan")),
                 len(bad), bad[:1] or ""))
        sys.stdout.flush()
        if not bad and (best is None or info["av_db"] > best[0]):
            best = (info["av_db"], sz2, info)
    if best:
        av, sz2, info = best
        json.dump({"vdd": vdd, "av_db": av, "pm": info["pm"],
                   "vout": info["vout"], "power": info["power"], "sizing": sz2},
                  open(OUT, "w"), indent=1, sort_keys=True)
        print("\nwritten to best_opam_stable.json: %.2f dB at %+.1f deg"
              % (av, info["pm"]))
    else:
        print("\nno feasible point at 45 degrees")


if __name__ == "__main__":
    main()
