#!/usr/bin/env python3
"""Refine OPAM from a given start, keeping best_opam.json up to date."""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import optimize as O

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "best_opam.json")
VDD = 8

start = json.load(open(sys.argv[1])) if len(sys.argv) > 1 \
    else json.load(open(OUT))["sizing"]
if "sizing" in start:
    start = start["sizing"]

pool, log = ThreadPoolExecutor(O.WORKERS), []
sz = dict(start)
for factors in (O.FACTORS, O.FINE, O.FINE):
    sz, val, bad, info = O.coordinate_descent(O.OPAM, sz, VDD, log, pool,
                                              factors=factors)
    print("pass -> Av=%7.2f dB  viol=%d %s"
          % (info.get("av_db", float("nan")), len(bad), bad[:1] or ""))
    sys.stdout.flush()

if not bad:
    prev = json.load(open(OUT)) if os.path.exists(OUT) else {"av_db": -1e9}
    if info["av_db"] > prev["av_db"]:
        json.dump({"seed": "refine", "vdd": VDD, "av_db": info["av_db"],
                   "vout": info["vout"], "power": info["power"], "sizing": sz},
                  open(OUT, "w"), indent=1, sort_keys=True)
        print("** new best written to best_opam.json")
    else:
        print("no improvement on the stored best (%.2f dB)" % prev["av_db"])
