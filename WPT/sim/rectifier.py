#!/usr/bin/env python3
"""Size the two diode-connected TFTs of the voltage doubler.

The rectifier is where this link stops being about magnetics and starts being
about the transistor.  A diode-connected IGZO TFT is not a good diode: it has
no exponential region a level-1 model can express, it does not conduct at all
until the gate passes threshold, and every micron of width it is given comes
with overlap capacitance that loads the very node the signal arrives on.

THE TRADE, in the constants design.ngspice actually measured:

    Rc  = rc_w / W = 3.3 / W        contact resistance, per contact
    Cov = cox_area * ov * W         overlap capacitance, per side
        = 1.564e-3 * 5e-6 * W       = 7.82 fF per micron of width at ov = 5 um

Width buys conduction and costs loading, and the loading is on the receive
node, whose source impedance is the coil's 497 ohms.  So there is an optimum
width and it is not the largest one.

WHAT IS SWEPT
    W    100 um to 20 mm
    L    5 to 50 um  (5 um is the DRC floor, SD.2, and prints at about 8)
    ov   2 to 10 um  - design.ngspice singles this out as the parameter worth
         moving, because it does not scale with L and so flattens fT

SCORED AT THE WORST CORNER.  best, tt and all, and the choice is made on the
worst of the three, following OPAM/sim/score.py.  The corners differ mostly in
Vto - +0.09, -0.26, -0.53 - and for a threshold-limited rectifier that is not a
detail, it is the whole problem.
"""

import csv
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tb_wpt as T                                          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

CORNERS = ("best", "tt", "all")
VTO = {"best": 0.09, "tt": -0.26, "all": -0.53}

W_GRID = [100e-6, 300e-6, 1e-3, 3e-3, 6e-3, 10e-3, 20e-3]
L_GRID = [5e-6, 10e-6, 20e-6, 50e-6]
OV_GRID = [2e-6, 5e-6, 10e-6]
RLOAD_GRID = [1e3, 1e4, 1e5, 1e6, 1e7]

# The drive.  The receiver produces EMF = emf_per_sqrtw * sqrt(P_in), and the
# TFT needs a few hundred millivolts to conduct at all, so the bench is run at
# a power that actually reaches threshold.  What that costs is the point, and
# it is reported rather than buried.
P_IN_GRID = [1.0, 10.0, 100.0, 1000.0]


def vamp_for_power(d, p_watt, rsrc=1.0):
    """Source amplitude that puts p_watt into the transmit loop.

    A sine of amplitude V across R delivers V^2/(2R) on average, and the loop
    is resistive at resonance, so V = sqrt(2 P R).
    """
    r_tot = rsrc + d["r_tx"]
    return math.sqrt(2.0 * p_watt * r_tot)


def run_point(d, w=6e-3, l=10e-6, ov=5e-6, rload=1e5, p_in=100.0,
              corner="tt", cout=10e-6):
    """One sizing at one drive level, in steady state."""
    vamp = vamp_for_power(d, p_in)
    m, _ = T.steady_state(d, cout=cout, rload=rload, corner=corner,
                          vamp=vamp, wtft=w, ltft=l, ov=ov)
    return {"w_um": w * 1e6, "l_um": l * 1e6, "ov_um": ov * 1e6,
            "rload": rload, "p_in_req": p_in, "corner": corner, "vamp": vamp,
            "vout": m.get("vout_avg", 0.0), "pout": m.get("pout_avg", 0.0),
            "pin": m.get("pin_avg", 0.0), "eta": m.get("eta", 0.0),
            "ripple": m.get("vout_max", 0.0) - m.get("vout_min", 0.0),
            "drift_pct": m.get("drift_pct", float("nan")),
            "settled": bool(m.get("settled", False))}


def threshold_note(d):
    """Why a diode-connected IGZO TFT is not a diode.

    Vto is NEGATIVE on three of the four corners - the PDK says so in as many
    words: "Vto is near zero and slightly negative on many devices
    (depletion-like), which is normal for unpassivated IGZO."  A diode-
    connected device with a negative threshold conducts at zero gate-source
    bias, and keeps conducting until the bias goes below Vto.  So it does not
    block: XM2 passes current backwards from the output whenever the input
    node sits less than |Vto| below it.

    This is not a sizing problem and no width fixes it.  It is reported here
    because it is the second reason the rectifier does not work, and it would
    still be there if the coils delivered a hundred times the voltage.
    """
    print("\nThe threshold, and why a diode-connected TFT is not a diode:")
    for c in CORNERS:
        v = VTO[c]
        print("  %-5s Vto = %+.2f V -> %s"
              % (c, v,
                 "blocks until %.2f V forward" % v if v > 0 else
                 "CONDUCTS AT ZERO BIAS; leaks until %.2f V reverse" % v))
    print("  Only the `best` corner is enhancement-mode.  On tt and all the")
    print("  doubler's series device passes current back out of the output")
    print("  capacitor, and no choice of W or L changes that.")


def main():
    d = T.load_design()
    print("Sizing the doubler's two diode-connected TFTs.")
    print("  link: f = %.0f kHz, M = %.3e H, coil R = %.0f ohm"
          % (d["f"] / 1e3, d["k"] * math.sqrt(d["l_tx"] * d["l_rx"]), d["r_rx"]))
    print("  Cov = 7.82 fF per micron of width at ov = 5 um (measured)")
    print("  Rc  = 3.3/W per contact (measured)")

    threshold_note(d)

    rows = []
    base = dict(w=6e-3, l=10e-6, ov=5e-6, rload=1e5, p_in=100.0, corner="tt")

    # 1. How hard does the transmitter have to be driven before anything
    #    happens at all?
    print("\n=== drive power ===")
    for p in P_IN_GRID:
        r = run_point(d, **dict(base, p_in=p))
        rows.append(r)
        emf = 0.0
        print("  P_in = %7.1f W (vamp %6.2f V)  vout = %.4e V  eta = %.3e"
              % (p, r["vamp"], r["vout"], r["eta"]))
    best_p = max((r for r in rows), key=lambda r: r["vout"])["p_in_req"]
    base["p_in"] = best_p
    print("  -> swept at %g W from here on" % best_p)

    # 2..4  the device itself, one dimension at a time
    for label, key, grid in (("=== width ===", "w", W_GRID),
                             ("=== length ===", "l", L_GRID),
                             ("=== gate overlap ===", "ov", OV_GRID),
                             ("=== load ===", "rload", RLOAD_GRID)):
        print("\n%s" % label)
        sub = []
        for v in grid:
            r = run_point(d, **dict(base, **{key: v}))
            rows.append(r)
            sub.append(r)
            print("  %-6s = %-10.4g  vout = %.4e V  pin = %.4e W  eta = %.3e"
                  % (key, v, r["vout"], r["pin"], r["eta"]))
        best = max(sub, key=lambda r: r["eta"] if r["eta"] else r["vout"])
        base[key] = {"w": best["w_um"] * 1e-6, "l": best["l_um"] * 1e-6,
                     "ov": best["ov_um"] * 1e-6,
                     "rload": best["rload"]}[key]
        print("  -> best %s = %.4g" % (key, base[key]))

    # 5. the sizing at every corner
    print("\n=== corners, at the chosen sizing ===")
    corner_rows = []
    for c in CORNERS:
        r = run_point(d, **dict(base, corner=c))
        rows.append(r)
        corner_rows.append(r)
        print("  %-5s (Vto %+.2f)  vout = %.4e V  pin = %.4e W  eta = %.3e"
              % (c, VTO[c], r["vout"], r["pin"], r["eta"]))
    worst = min(corner_rows, key=lambda r: r["vout"])

    print("\n=== the sizing ===")
    print("  W    = %.0f um" % (base["w"] * 1e6))
    print("  L    = %.0f um" % (base["l"] * 1e6))
    print("  ov   = %.0f um" % (base["ov"] * 1e6))
    print("  Cov  = %.2f pF per side  (cox_area * ov * W)"
          % (1.564e-3 * base["ov"] * base["w"] * 1e12))
    print("  Rc   = %.2f ohm per contact  (3.3 / W)" % (3.3 / base["w"]))
    print("  load = %.0f ohm" % base["rload"])
    print("  worst corner: %s, vout = %.4e V, eta = %.3e"
          % (worst["corner"], worst["vout"], worst["eta"]))

    out = {"design": {k: v for k, v in base.items()},
           "cov_f": 1.564e-3 * base["ov"] * base["w"],
           "rc_ohm": 3.3 / base["w"],
           "corners": corner_rows, "worst": worst,
           "vto": VTO}
    with open(os.path.join(HERE, "rectifier.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=float)
    with open(os.path.join(HERE, "rect_sweep.csv"), "w", newline="") as fh:
        wtr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wtr.writeheader()
        wtr.writerows(rows)
    print("\nwrote rectifier.json and rect_sweep.csv (%d points)" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
