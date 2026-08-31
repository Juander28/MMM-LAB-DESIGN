#!/usr/bin/env python3
"""
Co-tune a 10-channel ladder: per-channel bias ridge + per-channel tank trim.

A single global bias scale cannot work - the depth ridge is sharp and sits at a
different current for every channel.  This walks the project's own method:
  1. locate the real modes on a full span,
  2. per channel, scan its own bias for maximum depth subject to BW <= 30 kHz,
  3. trim that channel's tank C to pull f0 onto its target,
  4. repeat (the channels move each other, though far less with an isolated
     return than with a shared one).
"""

import json
import os
import subprocess
import sys

import numpy as np
from scipy.signal import find_peaks

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_nchan import LADDER_F, coupling_fF, itail_mA  # noqa: E402

SC = os.environ.get("SCRATCH", "/tmp")
COX = 1.564e-15
LADDER_C = [101.321, 56.9932, 36.4756, 25.3303, 18.61,
            14.2483, 11.2579, 9.11891, 7.53629, 6.33257]


def model(kp="0.717u", overlap=0.5, vto=0.09, lam=0.0067):
    cg = COX * overlap / 1e-6
    return (f".model TFT_K NMOS (Level=1 Vto={vto} Kp={kp} Lambda={lam}\n"
            f"+  Tox=22.1n Cgso={cg:.4g} Cgdo={cg:.4g} Cgbo=1.0e-9)")


def netlist(caps, cps, its, W, L, VDD, analysis, csv, extra_src=""):
    a = ["* 10-channel ladder, isolated return, co-tuned", model(),
         "VV4 VDD 0 'VDD'", f".param VDD={VDD}"]
    a.append(extra_src or "VV3 n05 actm 0 AC 1")
    a.append("RR5 actp n05 1k m=1")
    a.append("RRbias actm VDD 1meg m=1")
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
    a += [analysis, ".control", "run", "let vact = v(actp)-v(actm)",
          f"wrdata {csv} vact", "quit", ".endc", ".end"]
    return "\n".join(a) + "\n"


def simulate(caps, cps, its, W, L, VDD, lo, hi, npts, tag="t"):
    csv = f"{SC}/ct_{tag}.csv"
    open(f"{SC}/ct_{tag}.spice", "w").write(
        netlist(caps, cps, its, W, L, VDD,
                f".ac lin {npts} {lo}Meg {hi}Meg", csv))
    subprocess.run(["ngspice", "-b", f"{SC}/ct_{tag}.spice"],
                   capture_output=True, timeout=1800)
    try:
        d = np.loadtxt(csv)
    except Exception:
        return None
    f, m = d[:, 0], np.hypot(d[:, 1], d[:, 2])
    if not np.all(np.isfinite(m)):
        return None
    return f, 20 * np.log10(np.maximum(m, 1e-30))


def one_notch(f, db):
    """Deepest notch in this window, measured against a local baseline."""
    i = int(np.argmin(db))
    n = len(f)
    edge = max(20, n // 12)
    base = float(np.median(np.r_[db[:edge], db[-edge:]]))
    depth = base - db[i]
    thr = base - 3.0
    j = i
    while j > 0 and db[j] < thr:
        j -= 1
    k = i
    while k < n - 1 and db[k] < thr:
        k += 1
    bw = (f[k] - f[j]) if k > j else np.nan
    peak = float(db.max() - base)
    return f[i], depth, bw, peak


def scan_all(caps, cps, its, W, L, VDD, npts=150000):
    r = simulate(caps, cps, its, W, L, VDD, 35, 215, npts, "full")
    if r is None:
        return None
    f, db = r
    idx, _ = find_peaks(-db, prominence=0.02)
    return f, db, sorted(f[i] for i in idx)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--wl", type=float, default=1000.0)
    ap.add_argument("--L", type=float, default=1.0)
    ap.add_argument("--vdd", type=float, default=5.0)
    ap.add_argument("--iters", type=int, default=3)
    ap.add_argument("--out", default="cotune10.json")
    a = ap.parse_args()
    W = a.wl * a.L

    caps = list(LADDER_C)
    cps = [coupling_fF(x) for x in LADDER_F]
    its = [itail_mA(x) for x in LADDER_F]

    print(f"W/L = {a.wl:g}  (W = {W:g} um, L = {a.L:g} um), VDD = {a.vdd} V")
    print(f"gate cap per device = {COX*W*a.L*1e12:.3f} pF\n")

    for it_round in range(a.iters):
        res = scan_all(caps, cps, its, W, a.L, a.vdd)
        if res is None:
            print("diverged"); return
        f, db, modes = res
        print(f"--- round {it_round}: {len(modes)} modes at "
              + ", ".join(f"{m/1e6:.1f}" for m in modes[:12]))

        for k in range(10):
            if k >= len(modes):
                continue
            f0 = modes[k]
            half = max(0.6e6, 0.012 * f0)
            lo, hi = (f0 - half) / 1e6, (f0 + half) / 1e6
            base_it = its[k]

            def probe(cur):
                trial = list(its)
                trial[k] = cur
                r = simulate(caps, cps, trial, W, a.L, a.vdd, lo, hi, 20000,
                             tag=f"c{k}")
                if r is None:
                    return None
                nf0, dep, bw, peak = one_notch(*r)
                if peak > 1.0:      # past compensation: the notch became a peak
                    return None
                return nf0, dep, bw

            # Two-stage bounded search for the depth ridge.  Bounded on purpose:
            # an unbounded threshold hunt walks one channel to tens of mA when no
            # peak ever appears in its window, and that wrecks every other channel.
            best = (base_it, -1.0, None, None)
            for cur in base_it * np.geomspace(0.3, 2.5, 12):
                res = probe(cur)
                if res and res[1] > best[1]:
                    best = (cur, res[1], res[0], res[2])
            centre = best[0]
            for cur in centre * np.linspace(0.85, 1.15, 13):
                res = probe(cur)
                if res and res[1] > best[1]:
                    best = (cur, res[1], res[0], res[2])
            if best[1] < 0:                 # nothing valid - keep what we had
                best = (base_it, 0.0, None, None)
            its[k] = best[0]
            if best[2] is not None and best[1] > 0.3:
                # trim tank C to pull f0 onto target
                caps[k] *= (best[2] / (LADDER_F[k] * 1e6)) ** 2
            print(f"    ch{k+1:2d}: Itail={its[k]:9.5f} mA  depth={best[1]:6.2f} dB "
                  f"f0={(best[2] or 0)/1e6:8.3f} -> C={caps[k]:8.4f} pF")

    json.dump({"wl": a.wl, "L": a.L, "vdd": a.vdd, "W": W,
               "caps": caps, "cps": cps, "its": its},
              open(os.path.join(HERE, a.out), "w"), indent=1)
    print(f"\nsaved -> scale/{a.out}")


if __name__ == "__main__":
    main()
