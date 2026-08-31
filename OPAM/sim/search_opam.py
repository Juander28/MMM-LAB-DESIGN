#!/usr/bin/env python3
"""Run the OPAM search one start at a time, writing each result as it lands.

optimize.py only reports when every start is done, which is no use when a
start takes ten minutes: this keeps the best-so-far on disk so the run can be
read, or stopped, at any point.
"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import optimize as O

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "best_opam.json")
VDD = 8

best = None
if os.path.exists(OUT):
    best = json.load(open(OUT))

pool, log = ThreadPoolExecutor(O.WORKERS), []

# Restart from whatever a previous run reached, with the capacitors put back to
# the drawn size, and then work through the seeds.
starts = list(O.OPAM.seeds)
if best:
    starts.insert(0, dict(best["sizing"], c_boot=160.64, c_fb=160.64))
    best = None

for i, seed in enumerate(starts):
    sz = dict(seed)
    for factors in (O.FACTORS, O.FINE):
        sz, val, bad, info = O.coordinate_descent(O.OPAM, sz, VDD, log, pool,
                                                  factors=factors)
    print("seed %d -> Av=%7.2f dB  viol=%d %s"
          % (i, info.get("av_db", float("nan")), len(bad), bad[:1] or ""))
    sys.stdout.flush()
    if not bad and (best is None or info["av_db"] > best["av_db"]):
        best = {"seed": i, "vdd": VDD, "av_db": info["av_db"],
                "vout": info["vout"], "power": info["power"], "sizing": sz}
        json.dump(best, open(OUT, "w"), indent=1, sort_keys=True)
        print("  ** new best, written to best_opam.json")
        sys.stdout.flush()

print("\n=== best ===")
print(json.dumps(best, indent=1, sort_keys=True))
