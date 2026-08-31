#!/usr/bin/env python3
"""
One transistor size for all ten channels is the wrong choice, and the fT table
shows why: the tank needs less gm as frequency rises (gm_req = 2*RS/(w*L)^2), so
the bias ladder starves the high channels, the overdrive collapses from 2.8 V to
0.16 V, and fT collapses with it because fT is proportional to Vov.

Sizing each channel's transistor for a COMMON overdrive fixes that:

    W_k / L = gm_req(f_k) / (Kp * Vov_target)

W then falls as 1/f^2, every channel runs at the same healthy overdrive, and the
device capacitance loading each tank falls at the same rate - which also cures
the detuning that was worst at the top of the band.
"""

import json
import os
import subprocess
import sys

import numpy as np
from scipy.signal import find_peaks

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cotune10 import model, one_notch  # noqa: E402
from gen_nchan import LADDER_F, coupling_fF  # noqa: E402

SC = os.environ.get("SCRATCH", "/tmp")
KP = 0.717e-6
COX = 1.564e-15
L_LOOP = 100e-9
RS_LOOP = 1.0


def gm_req(f_hz):
    return 2 * RS_LOOP / (2 * np.pi * f_hz * L_LOOP) ** 2


def size_channels(vov, L_um):
    """Return per-channel W (um) and the tail current that gives that overdrive."""
    Ws, Its = [], []
    for f in LADDER_F:
        g = gm_req(f * 1e6)
        wl = g / (KP * vov)
        Ws.append(wl * L_um)
        Its.append(2 * 0.5 * KP * wl * vov ** 2 * 1e3)   # Itail in mA
    return Ws, Its


def dev_cap_pF(W, L, ov=0.5):
    return (COX * W * L + 2 * ov * COX * W) * 1e12


def seed_cap(f_mhz, cdev, cp_fF):
    ctot = 1.0 / (4 * np.pi ** 2 * (f_mhz * 1e6) ** 2 * L_LOOP) * 1e12
    return max(0.3, ctot - cdev - cp_fF / 1000.0)


def netlist(caps, cps, its, Ws, L, VDD, analysis, csv):
    a = ["* ten channels, per-channel device sizing", model(),
         "VV4 VDD 0 'VDD'", f".param VDD={VDD}",
         "VV3 n05 actm 0 AC 1", "RR5 actp n05 1k m=1",
         "RRbias actm VDD 1meg m=1"]
    for k in range(len(caps)):
        nd, ns, ret = f"nd{k}", f"ns{k}", f"am{k}"
        a += [f"CCp{k} actp {nd} {2*cps[k]:.6g}f m=1",
              f"CCq{k} actm {ret} {2*cps[k]:.6g}f m=1",
              f"MMa{k} {nd} {ret} {ns} {ns} TFT_K w={Ws[k]:.6g}u l={L}u m=1",
              f"MMb{k} {ret} {nd} {ns} {ns} TFT_K w={Ws[k]:.6g}u l={L}u m=1",
              f"LLa{k} VDD xa{k} 50n m=1", f"RLa{k} xa{k} {nd} 0.5 m=1",
              f"LLb{k} VDD xb{k} 50n m=1", f"RLb{k} xb{k} {ret} 0.5 m=1",
              f"CCt{k} {ret} {nd} {caps[k]:.8g}p m=1",
              f"IIt{k} {ns} 0 {its[k]:.8g}m"]
    a += [analysis, ".control", "run", "let vact = v(actp)-v(actm)",
          f"wrdata {csv} vact", "quit", ".endc", ".end"]
    return "\n".join(a) + "\n"


def sim(caps, cps, its, Ws, L, VDD, lo, hi, npts, tag):
    csv = f"{SC}/pw_{tag}.csv"
    open(f"{SC}/pw_{tag}.spice", "w").write(
        netlist(caps, cps, its, Ws, L, VDD, f".ac lin {npts} {lo}Meg {hi}Meg", csv))
    subprocess.run(["ngspice", "-b", f"{SC}/pw_{tag}.spice"],
                   capture_output=True, timeout=1800)
    try:
        d = np.loadtxt(csv)
    except Exception:
        return None
    f, m = d[:, 0], np.hypot(d[:, 1], d[:, 2])
    if not np.all(np.isfinite(m)):
        return None
    return f, 20 * np.log10(np.maximum(m, 1e-30))


def main():
    vov = float(sys.argv[1]) if len(sys.argv) > 1 else 2.8
    L = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    VDD = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
    rounds = int(sys.argv[4]) if len(sys.argv) > 4 else 2

    Ws, its = size_channels(vov, L)
    cps = [coupling_fF(f) for f in LADDER_F]
    Cgt = [(2 / 3) * COX * W * L * 1e-6 * 1e6 for W in Ws]  # placeholder
    caps = [seed_cap(LADDER_F[k], dev_cap_pF(Ws[k], L), cps[k]) for k in range(10)]

    print(f"per-channel sizing for a common overdrive of {vov} V, L = {L} um")
    print(f"{'ch':>3} {'f[MHz]':>8} {'gm_req[uS]':>11} {'W[um]':>9} {'Itail[mA]':>10} "
          f"{'Cdev[pF]':>9} {'Ctank[pF]':>10} {'fT[MHz]':>9} {'fT/f':>6}")
    for k in range(10):
        cd = dev_cap_pF(Ws[k], L)
        ct = (2 / 3) * COX * Ws[k] * L + 2 * 0.5 * COX * Ws[k]
        g = KP * (Ws[k] / L) * vov
        ft = g / (2 * np.pi * ct)
        print(f"{k+1:3d} {LADDER_F[k]:8.1f} {gm_req(LADDER_F[k]*1e6)*1e6:11.1f} "
              f"{Ws[k]:9.2f} {its[k]:10.5f} {cd:9.3f} {caps[k]:10.3f} "
              f"{ft/1e6:9.1f} {ft/(LADDER_F[k]*1e6):6.2f}")

    for rnd in range(rounds):
        r = sim(caps, cps, its, Ws, L, VDD, 35, 215, 150000, "full")
        if r is None:
            print("diverged"); return
        f, db = r
        idx, _ = find_peaks(-db, prominence=0.02)
        modes = sorted(f[i] for i in idx)
        print(f"\n--- round {rnd}: {len(modes)} modes: "
              + ", ".join(f"{m/1e6:.2f}" for m in modes))
        for k in range(min(10, len(modes))):
            f0 = modes[k]
            half = max(0.3e6, 0.006 * f0)
            lo, hi = (f0 - half) / 1e6, (f0 + half) / 1e6
            base = its[k]
            best = (base, -1.0, None, None)
            for cur in base * np.concatenate([np.geomspace(0.5, 1.6, 10),
                                              np.linspace(0.94, 1.06, 17)]):
                trial = list(its); trial[k] = cur
                rz = sim(caps, cps, trial, Ws, L, VDD, lo, hi, 20000, f"c{k}")
                if rz is None:
                    continue
                nf0, dep, bw, peak = one_notch(*rz)
                if peak > 1.0:
                    continue
                if dep > best[1]:
                    best = (cur, dep, nf0, bw)
            if best[1] > 0.3:
                its[k] = best[0]
                caps[k] *= (best[2] / (LADDER_F[k] * 1e6)) ** 2
            bw = best[3]
            q = best[2] / bw if best[2] and bw and bw == bw else float("nan")
            print(f"    ch{k+1:2d}: depth={best[1]:6.2f} dB  BW={bw/1e3 if bw and bw==bw else float('nan'):7.2f} kHz  "
                  f"Q_L={q:8.0f}  (spec {LADDER_F[k]*1e6/30e3:.0f})", flush=True)

    json.dump({"wl": None, "L": L, "vdd": VDD, "W": Ws, "caps": caps,
               "cps": cps, "its": its, "vov": vov},
              open(os.path.join(HERE, "perchan_w.json"), "w"), indent=1)
    print("\nsaved -> scale/perchan_w.json")


if __name__ == "__main__":
    main()
