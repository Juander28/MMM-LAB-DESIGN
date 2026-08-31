#!/usr/bin/env python3
"""
Phase 1 / Phase 2 sweep: how far does the channel count scale, and does an
isolated return fix the mode shift and the channel-to-channel interaction?

For each N and each return topology it runs a full-span AC sweep, locates the
real modes (never the naive formula), and measures depth against a LOCAL
baseline so a notch sitting on a sloping response is still measured correctly.
"""

import os
import subprocess
import sys

import numpy as np
from scipy.signal import find_peaks

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_nchan import build, LADDER_F  # noqa: E402

SC = os.environ.get("SCRATCH", "/tmp")


def simulate(n, mode, orig=False, span=".ac lin 12000 20Meg 260Meg", tag=""):
    stem = f"{SC}/scale_{tag}{mode}_{n}"
    open(stem + ".spice", "w").write(
        build(n, mode, orig=orig, span=span, out_csv=stem + ".csv"))
    r = subprocess.run(["ngspice", "-b", stem + ".spice"],
                       capture_output=True, text=True, timeout=1200)
    if not os.path.exists(stem + ".csv"):
        return None, (r.stderr or r.stdout)[-300:]
    d = np.loadtxt(stem + ".csv")
    f, m = d[:, 0], np.hypot(d[:, 1], d[:, 2])
    if not np.all(np.isfinite(m)) or m.max() > 1e6:
        return "OSC", ""
    return (f, 20 * np.log10(np.maximum(m, 1e-30))), ""


def notches(f, db, prom=0.3):
    """Locate minima and measure each against a local baseline."""
    idx, _ = find_peaks(-db, prominence=prom)
    out = []
    w = max(20, len(f) // 60)
    for i in idx:
        lo, hi = max(0, i - w), min(len(f), i + w + 1)
        ring = np.r_[db[lo:max(lo, i - w // 4)], db[min(hi, i + w // 4):hi]]
        if ring.size < 5:
            continue
        base = np.median(ring)
        out.append((f[i] / 1e6, base - db[i]))
    return out


def main():
    print("=" * 78)
    print("PHASE 1 / 2 - CHANNEL SCALING, SHARED vs ISOLATED RETURN")
    print("=" * 78)
    for orig, tag in ((True, "original capacitances (101/70/60 pF, cp=0.4p, Itail=130u)"),
                      (False, "50-200 MHz design ladder")):
        print(f"\n### {tag}")
        for mode in ("shared", "isolated"):
            print(f"  -- {mode} return")
            for n in (2, 3, 4, 6, 8, 10):
                res, err = simulate(n, mode, orig, tag="o" if orig else "d")
                if res is None:
                    print(f"     N={n:2d}: sim failed  {err.strip()[:90]}")
                    continue
                if res == "OSC":
                    print(f"     N={n:2d}: OSCILLATES")
                    continue
                f, db = res
                ns = notches(f, db)
                if not ns:
                    print(f"     N={n:2d}: no notch above 0.3 dB")
                    continue
                s = ", ".join(f"{a:.2f}/{b:.1f}dB" for a, b in ns[:10])
                print(f"     N={n:2d}: {len(ns):2d} modes  {s}")


if __name__ == "__main__":
    main()
