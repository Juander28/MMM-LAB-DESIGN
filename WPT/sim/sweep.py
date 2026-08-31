#!/usr/bin/env python3
"""The four sweeps that locate the maximum, and the coupling-capacitor test.

Everything here runs the full link in ngspice with the coils and the device
sizing the earlier stages chose, so these are answers about the circuit rather
than about the magnetics:

  1. efficiency against FREQUENCY across the 100 - 500 kHz band, with the
     transmitter re-tuned at every point (leaving it tuned to one frequency
     would measure the tuning, not the band)
  2. efficiency against DISTANCE, through the coupling coefficient
  3. efficiency against LOAD resistance
  4. THE COUPLING CAPACITOR: does adding one help, and where

THE COUPLING-CAPACITOR EXPERIMENT.  "Would a coupling capacitor increase the
transfer" has three distinct readings, and the sweep does all three rather than
picking one:

    series, transmit side   CTX  - tunes out the transmit coil's reactance.
                            This one is not optional and it is already in every
                            run: the transmit coil is 171 uH and its reactance
                            at 500 kHz is 539 ohms against 11.6 of resistance.
                            The sweep shows what removing it costs.
    shunt, across the coil  CPRX - parallel resonance on the receive side
    shunt, at the rectifier CCPL - across the doubler's input node

The receive-side answers are expected to be "no", and for a reason that is
worth stating with a number rather than an opinion: a resonance can only
multiply a voltage by the Q of the loop it is in, and the receive loop's Q is
0.006.  A capacitor cannot raise a voltage by a factor below one.
"""

import csv
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tb_wpt as T                                          # noqa: E402
import rectifier as R                                       # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

F_GRID = [100e3, 150e3, 200e3, 250e3, 300e3, 350e3, 400e3, 450e3, 500e3]
Z_GRID_MM = [1, 2, 3, 5, 8, 12, 20]
RLOAD_GRID = [100, 300, 1e3, 3e3, 1e4, 3e4, 1e5, 3e5, 1e6]
CCPL_GRID = [T.OPEN_C, 1e-12, 10e-12, 100e-12, 1e-9, 10e-9, 100e-9,
             1e-6, 2e-6, 10e-6]

P_IN = 1000.0               # the drive the rectifier sweep settled on


def design():
    """The link, with the device sizing rectifier.py chose."""
    d = T.load_design()
    rec = json.load(open(os.path.join(HERE, "rectifier.json")))["design"]
    kw = {"wtft": rec["w"], "ltft": rec["l"], "ov": rec["ov"],
          "rload": rec["rload"], "corner": rec.get("corner", "tt")}
    return d, kw


def point(d, kw, **over):
    p_in = over.pop("p_in", P_IN)
    args = dict(kw, **over)
    args["vamp"] = R.vamp_for_power(d, p_in)
    rload = args.pop("rload")
    m, _ = T.steady_state(d, cout=10e-6, rload=rload, **args)
    return {"vout": m.get("vout_avg", 0.0), "pin": m.get("pin_avg", 0.0),
            "pout": m.get("pout_avg", 0.0), "eta": m.get("eta", 0.0),
            "ripple": m.get("vout_max", 0.0) - m.get("vout_min", 0.0),
            "drift_pct": m.get("drift_pct", float("nan")),
            "settled": bool(m.get("settled", False)), "rload": rload}


def main():
    d, kw = design()
    print("Sweeps on the full link.")
    print("  TFT  W = %.0f um, L = %.0f um, ov = %.0f um"
          % (kw["wtft"] * 1e6, kw["ltft"] * 1e6, kw["ov"] * 1e6))
    print("  load %.0f ohm, drive %.0f W\n" % (kw["rload"], P_IN))

    out, rows = {}, []

    # ---- 1. frequency ---------------------------------------------------
    print("=== 1. frequency (transmitter re-tuned at each point) ===")
    print("     f (kHz)   vout (V)     pin (W)     eta")
    freq = []
    for f in F_GRID:
        r = point(d, kw, f=f, ctx=T.tx_resonant_c(d, f))
        r["f_hz"] = f
        freq.append(r)
        rows.append(dict(r, sweep="frequency", x=f))
        print("     %7.1f   %.5e  %.4e  %.4e"
              % (f / 1e3, r["vout"], r["pin"], r["eta"]))
    best_f = max(freq, key=lambda r: r["eta"])
    print("  -> best at %.0f kHz, eta = %.4e" % (best_f["f_hz"] / 1e3,
                                                 best_f["eta"]))
    out["frequency"] = freq

    # what leaving the transmitter untuned costs
    r_untuned = point(d, kw, ctx=T.SHORT_C)
    print("  transmitter left untuned: vout = %.4e V, eta = %.4e"
          % (r_untuned["vout"], r_untuned["eta"]))
    print("     - a factor of %.0f in efficiency.  The series capacitor on the"
          % (best_f["eta"] / r_untuned["eta"] if r_untuned["eta"] else float("inf")))
    print("       transmit side is not optional.")
    out["tx_untuned"] = r_untuned

    # ---- 2. distance ----------------------------------------------------
    print("\n=== 2. distance ===")
    tx = json.load(open(os.path.join(HERE, "tx_coil.json")))
    print("     z (mm)    k           vout (V)     eta")
    dist = []
    for row in tx["distance"]:
        if row["z_mm"] not in Z_GRID_MM:
            continue
        r = point(d, kw, k=row["k"])
        r.update({"z_mm": row["z_mm"], "k": row["k"]})
        dist.append(r)
        rows.append(dict(r, sweep="distance", x=row["z_mm"]))
        print("     %6g    %.4e  %.5e  %.4e"
              % (row["z_mm"], row["k"], r["vout"], r["eta"]))
    out["distance"] = dist

    # ---- 3. load --------------------------------------------------------
    print("\n=== 3. load ===")
    print("     R (ohm)     vout (V)     pout (W)     eta")
    load = []
    for rl in RLOAD_GRID:
        r = point(d, kw, rload=rl)
        load.append(r)
        rows.append(dict(r, sweep="load", x=rl))
        print("     %9.0f   %.5e  %.4e  %.4e"
              % (rl, r["vout"], r["pout"], r["eta"]))
    best_l = max(load, key=lambda r: r["eta"])
    print("  -> best at %.0f ohm, eta = %.4e" % (best_l["rload"], best_l["eta"]))
    out["load"] = load

    # ---- 4. the coupling capacitor --------------------------------------
    print("\n=== 4. the coupling capacitor ===")
    ref = point(d, kw)
    print("  reference, no extra capacitor: vout = %.5e V, eta = %.4e"
          % (ref["vout"], ref["eta"]))
    out["coupling_ref"] = ref
    for label, key in (("shunt across the receive coil", "cprx"),
                       ("shunt at the rectifier input", "ccpl")):
        print("\n  %s:" % label)
        print("     C            vout (V)     eta          vs reference")
        sub = []
        for c in CCPL_GRID:
            r = point(d, kw, **{key: c})
            r["c_f"] = c
            sub.append(r)
            rows.append(dict(r, sweep=key, x=c))
            ratio = r["eta"] / ref["eta"] if ref["eta"] else float("nan")
            print("     %-11s  %.5e  %.4e  %+.2f %%"
                  % ("open" if c <= T.OPEN_C else "%g F" % c,
                     r["vout"], r["eta"], 100.0 * (ratio - 1.0)))
        best = max(sub, key=lambda r: r["eta"])
        gain = best["eta"] / ref["eta"] if ref["eta"] else float("nan")
        out[key] = sub
        print("     -> best %.4e, a factor of %.4f on the reference"
              % (best["eta"], gain))
        if gain <= 1.01:
            print("        No improvement.  A resonance multiplies a voltage")
            print("        by the loop's Q, and this loop's Q is far below 1.")

    with open(os.path.join(HERE, "sweeps.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=float)
    with open(os.path.join(HERE, "sweeps.csv"), "w", newline="") as fh:
        keys = sorted({k for r in rows for k in r})
        wtr = csv.DictWriter(fh, fieldnames=keys)
        wtr.writeheader()
        wtr.writerows(rows)
    print("\nwrote sweeps.json and sweeps.csv (%d points)" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
