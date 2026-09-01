#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""What the coupling is worth, what it can be, and whether a 1 uH transmitter
is the better one.

Three questions, all of them yours.

1. "ESTO FUE ASUMIENDO 1 DE k, MIRA SI ES LO MEJOR."  k = 1 means perfect flux
   linkage: every line of field the transmitter makes passes through the
   receiver and back.  Between a coil measured in millimetres and a square
   millimetre of spiral on glass that cannot happen at any separation, so the
   question is not whether k = 1 is best - of course more coupling is better -
   but how far below it reality sits.  This forces k across the whole range
   and simulates each one, so what k = 1 would give is a number in a table
   next to what the geometry actually delivers.

2. "CUANDO BOBINAS MAS PEQUENAS HABIA MEJOR ACOPLE, POR EJEMPLO DE 1 uH."  You
   are right, and the reason is in the definition: k = M / sqrt(L1 L2), so
   shrinking L1 raises k even when M does not move.  The whole candidate grid
   is swept at the working separation and binned by inductance, which shows
   both the k your memory recalls AND what it does to the induced voltage,
   which is the thing that has to be maximised.

3. THE SEPARATION.  Phase 1 assumed 5 mm without asking; the answer is
   contact.  This is what that changes.

Everything is evaluated at params.Z_MM, so editing that one line moves all
three.
"""

import csv
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import params as P                                          # noqa: E402
import link                                                 # noqa: E402
import rx_coil                                              # noqa: E402
import tb_wpt as T                                          # noqa: E402
import tx_coil as TX                                        # noqa: E402

sys.path.insert(0, P.PDK_TOOLS)
import coil_core as cc                                      # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def rx_radii():
    return rx_coil.turn_radii(P.RX_W_UM, P.RX_GAP_UM, P.RX_N, P.RX_SHAPE,
                              P.RX_AREA_UM)


def simulate(d, k=None, l_tx=None, r_tx=None):
    """One link, in ngspice, at the operating point params.py describes."""
    dd = dict(d)
    if k is not None:
        dd["k"] = k
    if l_tx is not None:
        dd["l_tx"] = l_tx
    if r_tx is not None:
        dd["r_tx"] = r_tx
    ctx = 1.0 / ((2.0 * math.pi * P.F_OP) ** 2 * dd["l_tx"]) if P.TX_TUNE \
        else T.SHORT_C
    # The drive amplitude must come from the resistance of the coil BEING
    # SIMULATED, not from whichever one params.py happens to hold.  Taking it
    # from params gave every candidate in the inductance sweep a different
    # input power - the low-resistance coils were fed several kilowatts while
    # the table claimed a constant 1 kW, and one of them read 20.2 V where at
    # an honest 1 kW it gives 6.9.
    vamp = math.sqrt(2.0 * P.P_IN_W * (P.R_SRC + dd["r_tx"]))
    m, _ = T.steady_state(dd, cout=P.C_OUT, rload=P.R_LOAD, ctx=ctx,
                          vamp=vamp)
    return {"vamp": vamp,
            "vout": m.get("vout_avg", float("nan")),
            "pin": m.get("pin_avg", float("nan")),
            "pout": m.get("pout_avg", float("nan")),
            "eta": m.get("eta", float("nan")),
            "settled": bool(m.get("settled", False))}


# --------------------------------------------------------------------------
# 1. forced coupling
# --------------------------------------------------------------------------

def forced_k(d, geometric_k):
    print("=== 1. coupling forced, geometry ignored ===")
    print("  The geometry gives k = %.4e at %g mm.  Everything below that is"
          % (geometric_k, P.Z_MM))
    print("  a hypothetical; k = 1 is not reachable between these two coils.\n")
    print("     k          V(C3) (V)     P_out (W)    eta          vs real")
    rows = []
    ref = None
    for k in sorted(set(list(P.K_GRID) + [geometric_k])):
        r = simulate(d, k=k)
        r["k"] = k
        r["is_real"] = abs(k - geometric_k) < 1e-12
        if r["is_real"]:
            ref = r
        rows.append(r)
    for r in rows:
        rel = (r["eta"] / ref["eta"]) if ref and ref["eta"] else float("nan")
        print("     %-10.4g %-13.6e %-12.4e %-12.4e %s"
              % (r["k"], r["vout"], r["pout"], r["eta"],
                 "<- the real one" if r["is_real"] else "x%.0f" % rel))
    top = max(rows, key=lambda r: r["k"])
    if ref:
        print("\n  k = 1 would give %.3f V against the real %.3f V - a factor "
              "%.0f in voltage" % (top["vout"], ref["vout"],
                                   top["vout"] / max(ref["vout"], 1e-15)))
        print("  and %.0f in efficiency.  It is a ceiling, not an option."
              % (top["eta"] / max(ref["eta"], 1e-30)))
    return rows


# --------------------------------------------------------------------------
# 2. the transmitter's inductance
# --------------------------------------------------------------------------

def tx_inductance(d):
    print("\n=== 2. the transmitter's inductance, at %g mm ===" % P.Z_MM)
    print("  Your recollection: smaller coils coupled better.  They do - k is")
    print("  M/sqrt(L1 L2), so a smaller L1 raises it.  What matters for a")
    print("  threshold-limited rectifier is the induced VOLTAGE, so both are")
    print("  reported.\n")
    rxr = rx_radii()
    cands = []
    for t in TX.candidates():
        if not (TX.PRACTICAL_AWG_MIN <= t["awg"] <= TX.PRACTICAL_AWG_MAX):
            continue
        r = TX.link_to(t, rxr, P.RX_L, P.RX_Q, P.F_OP, P.Z_MM)
        cands.append((t, r))
    print("  %d practical candidates at this separation" % len(cands))

    # best in each inductance decade
    bins, rows = {}, []
    for t, r in cands:
        b = int(math.floor(math.log10(max(t["l_h"], 1e-12))))
        if b not in bins or r["emf_per_sqrtw"] > bins[b][1]["emf_per_sqrtw"]:
            bins[b] = (t, r)
    print("\n  best in each decade of L1:")
    print("     L1 (uH)    coil                          Q1      k          "
          "EMF/sqrtW  V(C3) (V)")
    for b in sorted(bins):
        t, r = bins[b]
        sim = simulate(d, k=r["k"], l_tx=t["l_h"], r_tx=r["r_ac"])
        row = {"vamp": sim["vamp"], "l_uh": t["l_h"] * 1e6, "topology": t["topology"],
               "d_mm": t["d_in_mm"], "n": t["n"], "layers": t["layers"],
               "awg": t["awg"], "d_wire_mm": t["d_wire_mm"],
               "q": r["q"], "k": r["k"], "m_h": r["m_h"],
               "emf_per_sqrtw": r["emf_per_sqrtw"], "vout": sim["vout"],
               "eta": sim["eta"], "r_ac": r["r_ac"]}
        rows.append(row)
        print("     %-10.4g %-29s %-7.1f %-10.4e %-10.5f %.4f"
              % (row["l_uh"],
                 "%s %gmm %dt x%d AWG%d" % (t["topology"], t["d_in_mm"],
                                            t["n"], t["layers"], t["awg"]),
                 row["q"], row["k"], row["emf_per_sqrtw"], row["vout"]))

    best_emf = max(rows, key=lambda r: r["vout"])
    best_k = max(rows, key=lambda r: r["k"])
    print("\n  most coupling: %.4g uH, k = %.4e  (%.0fx the %.4g uH coil)"
          % (best_k["l_uh"], best_k["k"], best_k["k"] / best_emf["k"],
             best_emf["l_uh"]))
    print("  most output:   %.4g uH, %.4f V" % (best_emf["l_uh"],
                                                best_emf["vout"]))

    # Is a ~1 uH transmitter competitive?  That is the specific question.
    near1 = min(rows, key=lambda r: abs(math.log10(max(r["l_uh"], 1e-6))))
    print("\n  the ~1 uH candidate: %.4g uH, %s %g mm, %d turns x%d AWG %d"
          % (near1["l_uh"], near1["topology"], near1["d_mm"], near1["n"],
             near1["layers"], near1["awg"]))
    print("    k = %.4e (%.1fx the best-output coil), V(C3) = %.4f V "
          "(%.1f %% of the best)"
          % (near1["k"], near1["k"] / best_emf["k"], near1["vout"],
             100.0 * near1["vout"] / max(best_emf["vout"], 1e-15)))
    return rows, best_emf, near1


# --------------------------------------------------------------------------
# 3. separation
# --------------------------------------------------------------------------

def distance(d):
    print("\n=== 3. separation ===")
    print("  Phase 1 assumed 5 mm and never asked.  You work at contact.\n")
    t = TX.solenoid(P.TX_D_MM, P.TX_N, P.TX_AWG, P.TX_LAYERS)
    rxr = rx_radii()
    rows = []
    print("     z (mm)   k           M (H)        V(C3) (V)   eta")
    for z in P.Z_GRID_MM:
        r = TX.link_to(t, rxr, P.RX_L, P.RX_Q, P.F_OP, z)
        sim = simulate(d, k=r["k"])
        row = {"z_mm": z, "k": r["k"], "m_h": r["m_h"], "vout": sim["vout"],
               "eta": sim["eta"]}
        rows.append(row)
        print("     %-8g %-11.4e %-12.4e %-11.4f %.4e"
              % (z, r["k"], r["m_h"], sim["vout"], sim["eta"]))
    at5 = next((r for r in rows if r["z_mm"] == 5.0), None)
    atz = min(rows, key=lambda r: abs(r["z_mm"] - P.Z_MM))
    if at5 and at5["eta"]:
        print("\n  contact (%g mm) against the 5 mm phase 1 assumed: "
              "%.2fx in voltage, %.2fx in efficiency"
              % (atz["z_mm"], atz["vout"] / at5["vout"],
                 atz["eta"] / at5["eta"]))
    return rows


def main():
    d = T.load_design()
    geometric_k = d["k"]
    print("Coupling study, at %g mm, %.0f kHz, TFT L = %.0f um"
          % (P.Z_MM, P.F_OP / 1e3, P.TFT_L * 1e6))
    print("  receive coil %.2f nH / %.0f ohm, transmit %.2f uH / %.2f ohm\n"
          % (P.RX_L * 1e9, P.RX_R, P.TX_L * 1e6, P.TX_R))

    k_rows = forced_k(d, geometric_k)
    l_rows, best_emf, near1 = tx_inductance(d)
    z_rows = distance(d)

    out = {"z_mm": P.Z_MM, "f_hz": P.F_OP, "geometric_k": geometric_k,
           "forced_k": k_rows, "tx_inductance": l_rows,
           "best_output": best_emf, "near_1uh": near1, "distance": z_rows,
           "tft_l": P.TFT_L}
    with open(os.path.join(HERE, "k_study.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=float)
    with open(os.path.join(HERE, "k_study.csv"), "w", newline="") as fh:
        keys = sorted({k for grp in (k_rows, l_rows, z_rows) for r in grp
                       for k in r})
        w = csv.DictWriter(fh, fieldnames=["sweep"] + keys)
        w.writeheader()
        for tag, grp in (("forced_k", k_rows), ("tx_inductance", l_rows),
                         ("distance", z_rows)):
            for r in grp:
                w.writerow(dict({"sweep": tag},
                                **{k: r.get(k) for k in keys}))
    print("\nwrote k_study.json and k_study.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
