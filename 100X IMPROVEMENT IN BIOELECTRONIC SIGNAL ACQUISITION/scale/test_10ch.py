#!/usr/bin/env python3
"""
Stand-alone 10-channel test: where do all ten notches land, and how deep?

Runs the 50-200 MHz channel ladder on the isolated return (the topology shown
to hold placement error under 2.4 %), with a chosen device, and reports
f0 / depth / BW / Q_L for every channel it can resolve.

  python3 test_10ch.py --wl 500 --kp 0.717u
  python3 test_10ch.py --wl 500 --kp 500u
"""

import argparse
import os
import subprocess
import sys

import numpy as np
from scipy.signal import find_peaks

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_nchan import build, LADDER_F, MODEL_DIR  # noqa: E402

SC = os.environ.get("SCRATCH", "/tmp")
COX = 1.564e-15          # F/um^2, measured (50 nm Al2O3, 400x400 um cap)
OVERLAP = 5.0            # um per side, measured off TFT_layout.GDS


def device_model(kp, overlap, vto=0.09, lam=0.0067):
    cg = COX * overlap / 1e-6
    return (f".model TFT_K NMOS (Level=1 Vto={vto} Kp={kp} Lambda={lam}\n"
            f"+  Tox=22.1n Cgso={cg:.4g} Cgdo={cg:.4g} Cgbo=1.0e-9)")


def run(wl, L_um, kp, overlap, VDD, bias_scale, lo, hi, npts=120000):
    W = wl * L_um
    csv = f"{SC}/ch10.csv"
    txt = build(10, "isolated", model="TFT_K", w=f"{W:g}u", l=f"{L_um:g}u",
                span=f".ac lin {npts} {lo}Meg {hi}Meg", out_csv=csv)
    txt = txt.replace(
        f".include {MODEL_DIR}/nmosgen_test1.lib",
        device_model(kp, overlap))
    txt = txt.replace(
        f".include {MODEL_DIR}/tft_igzo_test1.lib", "")
    txt = txt.replace(".param VDD=1.5", f".param VDD={VDD}")
    # scale every channel bias by a common factor
    out = []
    for line in txt.split("\n"):
        if line.startswith("IIt") and line.endswith("m"):
            p = line.split()
            val = float(p[-1][:-1]) * bias_scale
            out.append(" ".join(p[:-1] + [f"{val:.6g}m"]))
        else:
            out.append(line)
    txt = "\n".join(out)
    open(f"{SC}/ch10.spice", "w").write(txt)
    subprocess.run(["ngspice", "-b", f"{SC}/ch10.spice"],
                   capture_output=True, timeout=1800)
    d = np.loadtxt(csv)
    f, m = d[:, 0], np.hypot(d[:, 1], d[:, 2])
    if not np.all(np.isfinite(m)):
        return None
    return f, 20 * np.log10(np.maximum(m, 1e-30))


def notches(f, db, prom=0.02):
    idx, _ = find_peaks(-db, prominence=prom)
    out = []
    w = max(50, len(f) // 80)
    for i in idx:
        lo, hi = max(0, i - w), min(len(f), i + w + 1)
        ring = np.r_[db[lo:max(lo, i - w // 5)], db[min(hi, i + w // 5):hi]]
        if ring.size < 10:
            continue
        base = float(np.median(ring))
        depth = base - db[i]
        thr = base - 3.0
        j = i
        while j > 0 and db[j] < thr:
            j -= 1
        k = i
        while k < len(f) - 1 and db[k] < thr:
            k += 1
        bw = (f[k] - f[j]) if k > j else np.nan
        out.append((f[i], depth, bw))
    return out


def report(title, f, db):
    print(f"\n{'='*78}\n{title}\n{'='*78}")
    ns = notches(f, db)
    if not ns:
        print("  no resolvable notch")
        return
    print(f"{'#':>3} {'target[MHz]':>12} {'f0[MHz]':>10} {'err%':>7} "
          f"{'depth[dB]':>10} {'BW[kHz]':>10} {'Q_L':>8} {'Q_L spec':>9} {'ok':>4}")
    used = set()
    for k, tgt in enumerate(LADDER_F):
        cand = [n for n in ns if n[0] / 1e6 not in used]
        if not cand:
            break
        best = min(cand, key=lambda n: abs(n[0] / 1e6 - tgt))
        f0, dep, bw = best
        used.add(f0 / 1e6)
        q = f0 / bw if bw == bw and bw > 0 else float("nan")
        spec = f0 / 30e3
        ok = "SI" if (dep > 3 and bw == bw and bw <= 30e3) else "no"
        print(f"{k+1:3d} {tgt:12.2f} {f0/1e6:10.3f} {100*(f0/1e6-tgt)/tgt:7.2f} "
              f"{dep:10.2f} {bw/1e3 if bw == bw else float('nan'):10.2f} "
              f"{q:8.0f} {spec:9.0f} {ok:>4}")
    deep = sum(1 for _, d_, _ in ns if d_ > 3)
    print(f"\n  notches found: {len(ns)}   deeper than 3 dB: {deep}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wl", type=float, default=500.0)
    ap.add_argument("--L", type=float, default=8.0)
    ap.add_argument("--kp", default="0.717u")
    ap.add_argument("--overlap", type=float, default=OVERLAP)
    ap.add_argument("--vdd", type=float, default=5.0)
    ap.add_argument("--bias", type=float, default=1.0)
    ap.add_argument("--lo", default="35")
    ap.add_argument("--hi", default="215")
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    r = run(a.wl, a.L, a.kp, a.overlap, a.vdd, a.bias, a.lo, a.hi)
    if r is None:
        print("simulation diverged")
        return
    f, db = r
    lbl = a.label or (f"W/L = {a.wl:g} (W = {a.wl*a.L:g} um, L = {a.L:g} um), "
                      f"Kp = {a.kp}, overlap = {a.overlap:g} um, VDD = {a.vdd} V, "
                      f"bias x{a.bias:g}")
    report(lbl, f, db)
    np.save(f"{SC}/ch10_{a.wl:g}_{a.kp}_L{a.L:g}_ov{a.overlap:g}_b{a.bias:g}.npy", np.vstack([f, db]))


if __name__ == "__main__":
    main()
