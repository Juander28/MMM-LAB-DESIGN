#!/usr/bin/env python3
"""Find a sizing for the self-biased OPAM: no BIAS pin, no per-corner trim.

Two stages, because the reference branch and the amplifier are coupled through
one node and a blind joint search wastes most of its time infeasible:

  1. hold the amplifier at the sizing found with an external bias and sweep the
     reference branch until BIAS lands somewhere the amplifier can live with;
  2. from there, run the usual coordinate descent over everything at once.

Success is not a gain figure - it is that all three corners pass with nothing
adjusted between them.
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bias_gen
import optimize as O
import report

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "best_opam_biased.json")
VDD = 8


def main():
    bias_gen.write_core()
    vdd, amp, _, vcm = report.load_opam()
    d = O.OPAM_BIASED
    d.vcm_frac = vcm / vdd

    print("stage 1: sweeping the reference branch, amplifier held fixed")
    best = None
    for w_b2, l_b2 in ((200, 100), (200, 200), (100, 200), (400, 100)):
        for w_b1, l_b1 in ((60, 1000), (60, 600), (100, 1000), (100, 600),
                           (200, 1000), (60, 300), (200, 400), (400, 400)):
            sz = dict(amp, w_b1=w_b1, l_b1=l_b1, w_b2=w_b2, l_b2=l_b2)
            val, bad, info, res = d.evaluate(sz, VDD)
            bias = res["nodes"].get("x1.bias", float("nan")) if res else float("nan")
            tag = "OK" if not bad else "%d viol (%s)" % (len(bad), bad[0])
            print("  b1 %4d/%4d  b2 %4d/%4d  BIAS=%5.3f V  Av=%7.2f dB  %s"
                  % (w_b1, l_b1, w_b2, l_b2, bias,
                     info.get("av_db", float("nan")), tag))
            sys.stdout.flush()
            if best is None or val > best[0]:
                best = (val, sz)
    print("\nstage 1 best score %.2f\n" % best[0])

    print("stage 2: coordinate descent over amplifier and reference together")
    pool, log = ThreadPoolExecutor(O.WORKERS), []
    sz = dict(best[1])
    for factors in (O.FACTORS, O.FINE, O.FINE):
        sz, val, bad, info = O.coordinate_descent(d, sz, VDD, log, pool,
                                                  factors=factors)
        print("  pass -> Av=%7.2f dB  viol=%d %s"
              % (info.get("av_db", float("nan")), len(bad), bad[:1] or ""))
        sys.stdout.flush()

    if not bad:
        json.dump({"vdd": VDD, "vcm": vcm, "av_db": info["av_db"],
                   "vout": info["vout"], "power": info["power"], "sizing": sz},
                  open(OUT, "w"), indent=1, sort_keys=True)
        print("\nwritten to best_opam_biased.json")
    else:
        print("\nno feasible point found; best had %d violations" % len(bad))
        for b in bad:
            print("   ", b)


if __name__ == "__main__":
    main()
