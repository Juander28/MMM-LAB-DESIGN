#!/usr/bin/env python3
"""
Time-domain check of the co-tuned 10-channel ladder.

Drives the differential line with band-limited white noise and records the
input and output waveforms.  The point is to confirm, without using .ac at all,
that the notches are really there: the PSD of output/input recovers the same
resonances, depths and bandwidths the AC sweep predicted.

Writes a plain-text time record (time, input, output) so the run can be
re-analysed independently.
"""

import argparse
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cotune10 import model, COX  # noqa: E402

SC = os.environ.get("SCRATCH", "/tmp")


def netlist(cfg, tstop, tmax, tsamp, ts_noise, amp, csv):
    caps, cps, its = cfg["caps"], cfg["cps"], cfg["its"]
    W, L, VDD = cfg["W"], cfg["L"], cfg["vdd"]
    a = ["* 10-channel ladder driven by white noise - time domain", model(),
         "VV4 VDD 0 'VDD'", f".param VDD={VDD}",
         # band-limited white noise: a new random value every ts_noise
         f"VVn n05 actm dc 0 trnoise({amp} {ts_noise} 0 0)",
         "RR5 actp n05 1k m=1",
         "RRbias actm VDD 1meg m=1"]
    for k in range(len(caps)):
        nd, ns, ret = f"nd{k}", f"ns{k}", f"am{k}"
        a += [f"CCp{k} actp {nd} {2*cps[k]:.6g}f m=1",
              f"CCq{k} actm {ret} {2*cps[k]:.6g}f m=1",
              f"MMa{k} {nd} {ret} {ns} {ns} TFT_K w={W}u l={L}u m=1",
              f"MMb{k} {ret} {nd} {ns} {ns} TFT_K w={W}u l={L}u m=1",
              f"LLa{k} VDD xa{k} 50n m=1", f"RLa{k} xa{k} {nd} 0.5 m=1",
              f"LLb{k} VDD xb{k} 50n m=1", f"RLb{k} xb{k} {ret} 0.5 m=1",
              f"CCt{k} {ret} {nd} {caps[k]:.8g}p m=1",
              f"IIt{k} {ns} 0 {its[k]:.8g}m"]
    a += [".options method=gear maxord=2 reltol=1e-4 abstol=1e-12 vntol=1e-9",
          f".tran {tsamp} {tstop} 0 {tmax}",
          ".control", "run",
          # resample onto a uniform grid - the solver uses variable steps and
          # an FFT needs even sampling
          f"linearize",
          "let vin  = v(n05)-v(actm)",
          "let vout = v(actp)-v(actm)",
          f"wrdata {csv} vin vout",
          "quit", ".endc", ".end"]
    return "\n".join(a) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cfg", default="cotune10_k1000.json")
    ap.add_argument("--tstop", default="250u")
    ap.add_argument("--tmax", default="250p")
    ap.add_argument("--tsamp", default="500p")
    ap.add_argument("--tsnoise", default="0.5n")
    ap.add_argument("--amp", default="1.0")
    ap.add_argument("--tag", default="k1000")
    a = ap.parse_args()

    cfg = json.load(open(os.path.join(HERE, a.cfg)))
    csv = f"{SC}/tran_{a.tag}.csv"
    spice = f"{SC}/tran_{a.tag}.spice"
    open(spice, "w").write(netlist(cfg, a.tstop, a.tmax, a.tsamp, a.tsnoise, a.amp, csv))
    print(f"running .tran sample={a.tsamp} stop={a.tstop} maxstep={a.tmax} noise={a.tsnoise}")
    import time; t0=time.time()
    r = subprocess.run(["ngspice", "-b", spice], capture_output=True,
                       text=True, timeout=7200)
    if not os.path.exists(csv):
        print(r.stdout[-2000:], r.stderr[-2000:])
        return
    print(f"done in {time.time()-t0:.1f} s, {os.path.getsize(csv)/1e6:.1f} MB")


if __name__ == "__main__":
    main()
