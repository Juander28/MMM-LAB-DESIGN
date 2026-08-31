#!/usr/bin/env python3
"""Choose the receive coil: the best planar spiral that fits in 1000 x 1000 um.

Sweeps the drawn geometry - track width, gap, turns, shape, topology - against
the DRC of this process, and reports FOUR answers, because the question has
four answers and they are not the same point:

    max L      the largest inductance the area can hold
    max Q      the best quality factor the area can hold
    max FOM    the best k^2 Q1 Q2 - the right answer for a MATCHED load
    max EMF    the largest induced voltage - the right answer for a
               THRESHOLD-limited load, and the one this design has

WHICH OBJECTIVE GOVERNS DEPENDS ON THE LOAD, AND HERE IT IS NOT THE OBVIOUS ONE.
A link delivering power into a matched impedance is judged by k^2 Q1 Q2, and
that is where this search started.  But the load is not matched, it is a pair
of diode-connected TFTs, and they do not conduct at all until the voltage
across them passes threshold.  Below that the link delivers nothing, and the
figure of merit is not describing the circuit.  What has to be maximised first
is the open-circuit induced voltage,

    EMF = w * M * I_tx ,        M proportional to the receiver's total turn area

so the receiver wants turn AREA, not the best ratio of area to resistance.  The
two point at very different coils - a factor of 4.4 in EMF between them - and
the search reports both with the reason for choosing between them.

THERE IS NO TANK, AND THIS IS WHY THE CAPACITOR DOES NOT CONSTRAIN ANYTHING.
The first version of this search treated the three external capacitors as
tuning elements and only allowed geometries that resonated inside the band.
Comparing the three impedances in the loop shows that was wrong: at 1 uH and
1 uF the reactances are about 1 ohm each, and the coil's own resistance is 500.
R beats both by three orders of magnitude everywhere in the band, so the loop
is a resistor, the "resonance" is a number with no circuit behind it, and the
capacitor's real job is the doubler's DC block.  Any of the three works.  The
frequency is therefore free inside the band - and since EMF is proportional to
frequency, free means the top of it.

WHY THE RANKING BARELY DEPENDS ON THE TRANSMIT COIL.  M is proportional to the
flux the receiver intercepts.  The transmitter is centimetres across and the
receiver is one millimetre, so the field over the receiver is uniform and the
ranking is a property of the receiver alone whatever the transmitter looks
like.  That is asserted, so it is also checked: `--check-tx` reruns the search
against two deliberately different reference transmitters.

WHAT IS SWEPT, AND WHAT IS PINNED
  d_out  pinned at 1000 um - the area is the constraint, so the coil is grown
         inward from the boundary rather than outward from the centre
  w      5 to 200 um.  Below 5 um is GATE.1 / SD.1
  gap    5 to 50 um.  Below 5 um is GATE.2 / SD.2
  n      1 to 80, bounded further by the inner diameter staying positive
  shape  square and circular
  t      50 nm and 1 um, both reported side by side throughout

Lengths are carried in MICRONS through the sweep and converted to metres only
where the physics is called.  Holding the grid in metres cost an afternoon: the
DRC floor is 5 um, and `5.0 * 1e-6` is one ulp BELOW the literal `5e-6`, so the
minimum-width corner of the space - which is where maximum inductance lives -
was silently rejected as a violation.
"""
import csv
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import link                                                 # noqa: E402
sys.path.insert(0, link.PDK_TOOLS)                          # coil_core lives there

import numpy as np                                          # noqa: E402
import coil_core as cc                                      # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# --- the problem, as posed ------------------------------------------------
AREA_UM = 1000.0            # the 1000 x 1000 um the coil has to fit in
THICKNESS_UM = (0.05, 1.0)  # the two metal thicknesses asked about
CAPS = (1e-6, 2e-6, 10e-6)  # the external capacitors that exist
F_PREF = 100e3              # the frequency the user would prefer
F_OP = 500e3                # where the link is actually operated: EMF ~ w,
                            # and nothing in the band constrains the choice
F_BAND = (100e3, 500e3)     # the band the resonance has to land in
RHO = link.RHO_AU           # gold: what the process assumes

# --- the DRC of this process ---------------------------------------------
# libs.tech/klayout/tech/drc/igzo_mmm_lab.drc, rules GATE.1/GATE.2 (gate metal)
# and SD.1/SD.2 (source-drain metal).  Both metals, both rules, 5 um.
W_MIN_UM = 5.0
GAP_MIN_UM = 5.0
D_IN_MIN_UM = 20.0          # leave room for the inner terminal to get out

# --- the sweep grid, in microns ------------------------------------------
W_GRID = np.arange(5.0, 200.1, 1.0)
GAP_GRID = np.arange(5.0, 50.1, 1.0)
N_MAX = 80
# Parallel rings need an n x n matrix inverse per geometry, so they get a
# coarser grid.  They are a comparison, not the main search.
W_GRID_COARSE = np.arange(5.0, 200.1, 5.0)
GAP_GRID_COARSE = np.arange(5.0, 50.1, 5.0)

SHAPES = {"square": "cuadrada", "circular": "circular"}


# --------------------------------------------------------------------------
# Reference transmitters - only to turn the ranking into a real number
# --------------------------------------------------------------------------

def ref_tx(d_in_mm=10.0, n=20, awg=26, z_mm=5.0):
    """A flat copper pancake, as a stand-in transmitter.

    tx_coil.py does the real transmitter search; this exists so the receive
    coil can be scored on an honest FOM instead of a proportionality.
    """
    d_w = cc.awg_to_diameter(awg)
    d_in = d_in_mm * 1e-3
    d_out = cc.outer_diameter(d_in, d_w, 0.0, n)
    l_h = cc.mohan_wheeler(d_in, d_w, 0.0, n, "circular")
    length = cc.spiral_length_circular(d_in, d_out, n)
    radii = [(d_in / 2.0 + d_w / 2.0 + k * d_w) for k in range(n)]
    return {"l_h": l_h, "length": length, "d_w": d_w, "radii": radii,
            "z": z_mm * 1e-3, "awg": awg, "n": n, "d_in_mm": d_in_mm}


def ref_tx_solenoid(d_mm=30.0, n=40, awg=22, z_mm=5.0):
    """A deliberately different transmitter: a solenoid, bigger, thicker wire."""
    d_w = cc.awg_to_diameter(awg)
    a = d_mm * 1e-3 / 2.0
    length_ax = n * d_w
    l_h = cc.wheeler_multilayer(a, length_ax, d_w, n)
    length = math.pi * d_mm * 1e-3 * n
    radii = link.solenoid_radii(d_mm * 1e-3, n)
    z_of = link.solenoid_axial(length_ax, n, z0=-length_ax / 2.0)
    return {"l_h": l_h, "length": length, "d_w": d_w, "radii": radii,
            "z_of": z_of, "z": z_mm * 1e-3, "awg": awg, "n": n, "d_in_mm": d_mm}


def tx_q(tx, f):
    r = cc.ac_resistance_round(link.RHO_CU, tx["length"], tx["d_w"], f)
    return cc.quality_factor(tx["l_h"], r, f), r


# --------------------------------------------------------------------------
# One geometry
# --------------------------------------------------------------------------

def d_in_um(w_um, gap_um, n, d_out_um=AREA_UM):
    """Inner diameter of a coil grown inward from a fixed outer extent."""
    return d_out_um - 2.0 * n * w_um - 2.0 * (n - 1) * gap_um


def fits(w_um, gap_um, n, d_out_um=AREA_UM):
    if w_um < W_MIN_UM or gap_um < GAP_MIN_UM:
        return False
    return d_in_um(w_um, gap_um, n, d_out_um) >= max(D_IN_MIN_UM, 2.0 * w_um)


def turn_area(w_um, gap_um, n, shape, d_out_um=AREA_UM):
    """Total area enclosed by the turns, m^2 - what sets M in a uniform field."""
    pitch = w_um + gap_um
    total = 0.0
    for k in range(int(n)):
        s = (d_out_um - w_um - 2.0 * k * pitch) * 1e-6
        if s <= 0:
            break
        total += s * s if shape == "square" else math.pi * (s / 2.0) ** 2
    return total


def turn_radii(w_um, gap_um, n, shape, d_out_um=AREA_UM):
    return link.equivalent_radii(d_out_um * 1e-6, w_um * 1e-6, gap_um * 1e-6,
                                 n, shape)


def evaluate(w_um, gap_um, n, shape, topology, t_um, f, d_out_um=AREA_UM):
    """One geometry at one frequency.  None if it does not fit or violates DRC."""
    if not fits(w_um, gap_um, n, d_out_um):
        return None
    w, gap, t = w_um * 1e-6, gap_um * 1e-6, t_um * 1e-6
    din = d_in_um(w_um, gap_um, n, d_out_um) * 1e-6
    d_out = d_out_um * 1e-6
    shp = SHAPES[shape]

    if topology == "series":
        l_h = cc.inductance_microcoil(din, w, gap, n, t, shp, "mohan")
        length = (cc.spiral_length_square(din, w, gap, n) if shape == "square"
                  else cc.spiral_length_circular(din, d_out, n))
        r_dc = cc.dc_resistance(RHO, length, w * t)
        r_ac = cc.ac_resistance_rectangular(RHO, length, w, t, f)
    else:
        res = cc.parallel_rings_inductance(din, w, gap, n, t)
        l_h = float(res["L_total"])
        # Parallel rings come out very low - 0.03 nH for 49 rings across a
        # millimetre - and that is real, not a numerical artefact: the rings
        # are concentric, so the innermost one is tiny, and in parallel the
        # smallest inductance dominates.  It is exactly why the topology loses
        # here.  The only guard is the physical bound.
        singles = res.get("L_individual") or []
        if singles and not (0 < l_h <= max(singles) * 1.05):
            return None
        length = (cc.spiral_length_square(din, w, gap, n) if shape == "square"
                  else cc.spiral_length_circular(din, d_out, n))
        r_dc = cc.dc_resistance(RHO, length / n, w * t) / n
        r_ac = cc.ac_resistance_rectangular(RHO, length / n, w, t, f) / n
    if l_h <= 0 or r_ac <= 0:
        return None

    return {
        "shape": shape, "topology": topology,
        "w_um": float(w_um), "gap_um": float(gap_um), "n": int(n),
        "d_in_um": d_in_um(w_um, gap_um, n, d_out_um), "d_out_um": d_out_um,
        "t_um": t_um, "f_hz": f,
        "l_nh": l_h * 1e9, "r_dc": r_dc, "r_ac": r_ac,
        "q": cc.quality_factor(l_h, r_ac, f),
        "len_um": length * 1e6,
        "turn_area_m2": turn_area(w_um, gap_um, n, shape, d_out_um),
    }


def score(rec, tx, z=None):
    """The real figure of merit for this receiver against a reference transmitter.

    ONLY VALID FOR A SERIES SPIRAL.  link.mutual sums the turn-pair mutuals
    with every turn carrying the same current, which is what a series spiral
    is and what parallel rings are not - there the current divides between the
    rings in inverse proportion to their impedance.  So the parallel topology
    is swept and reported for its L and its Q, and is NOT scored on M or on the
    figure of merit.  It loses on inductance by four orders of magnitude
    anyway, so nothing turns on it.
    """
    f = rec["f_hz"]
    l2 = rec["l_nh"] * 1e-9
    rx_r = turn_radii(rec["w_um"], rec["gap_um"], rec["n"], rec["shape"],
                      rec["d_out_um"])
    m = link.mutual_fast(tx["radii"], rx_r, z_a=tx.get("z_of"),
                    gap_z=tx["z"] if z is None else z)
    k = link.coupling(m, tx["l_h"], l2)
    q1, _ = tx_q(tx, f)
    f_om = link.fom(k, q1, rec["q"])
    return {"m_h": m, "k": k, "q1": q1, "fom": f_om,
            "eta_max": link.eta_max(f_om)}


def tuned(rec, tx):
    """Re-score a geometry at each capacitor's resonance; keep the best in band."""
    l_h = rec["l_nh"] * 1e-9
    best, options = None, []
    for c in CAPS:
        f = link.resonant_f(l_h, c)
        in_band = F_BAND[0] <= f <= F_BAND[1]
        opt = {"c_f": c, "f_hz": f, "in_band": in_band}
        if in_band:
            at_f = evaluate(rec["w_um"], rec["gap_um"], rec["n"], rec["shape"],
                            rec["topology"], rec["t_um"], f, rec["d_out_um"])
            s = score(at_f, tx)
            opt.update({"q": at_f["q"], "r_ac": at_f["r_ac"], **s})
            if best is None or s["fom"] > best["fom"]:
                best = dict(opt, rec=at_f)
        options.append(opt)
    return best, options


# --------------------------------------------------------------------------
# The sweep
# --------------------------------------------------------------------------

def sweep(t_um, topology="series", shapes=("square", "circular"), f=F_OP):
    """Every legal geometry at one metal thickness, scored at one frequency."""
    wg = W_GRID if topology == "series" else W_GRID_COARSE
    gg = GAP_GRID if topology == "series" else GAP_GRID_COARSE
    out = []
    for shape in shapes:
        for w in wg:
            for gap in gg:
                for n in range(1, N_MAX + 1):
                    if not fits(w, gap, n):
                        break
                    rec = evaluate(w, gap, n, shape, topology, t_um, f)
                    if rec:
                        out.append(rec)
    return out


def regime(rec, caps=CAPS, band=F_BAND):
    """Is this loop a tank or a resistor?  Compare the three impedances."""
    l_h = rec["l_nh"] * 1e-9
    worst, rows = 0.0, []
    for f in (band[0], band[1]):
        for c in caps:
            w = 2.0 * math.pi * f
            xl, xc = w * l_h, 1.0 / (w * c)
            ratio = rec["r_ac"] / max(xl, xc)
            worst = max(worst, 1.0 / ratio)
            rows.append({"f_hz": f, "c_f": c, "xl": xl, "xc": xc,
                         "r": rec["r_ac"], "r_over_x": ratio})
    return {"rows": rows, "resistive": worst < 0.1, "worst_x_over_r": worst}


def pick(records, tx):
    """The four answers.  Everything is scored at one frequency: with a
    resistive loop, Q, the EMF and the FOM all scale with w the same way for
    every candidate, so the ranking does not move with frequency."""
    best_l = max(records, key=lambda r: r["l_nh"])
    best_q = max(records, key=lambda r: r["q"])
    best_a = max(records, key=lambda r: r["turn_area_m2"])

    # M and the FOM are only meaningful for a series spiral - see score().
    if records and records[0]["topology"] != "series":
        return {"max_l": best_l, "max_q": best_q, "max_area": best_a,
                "max_fom": None, "max_fom_link": None,
                "max_emf": None, "max_emf_link": None}

    best_f, best_e = None, None
    for r in records:
        s_ = score(r, tx)
        if best_f is None or s_["fom"] > best_f[1]["fom"]:
            best_f = (r, s_)
        if best_e is None or s_["m_h"] > best_e[1]["m_h"]:
            best_e = (r, s_)
    return {"max_l": best_l, "max_q": best_q, "max_area": best_a,
            "max_fom": best_f[0], "max_fom_link": best_f[1],
            "max_emf": best_e[0], "max_emf_link": best_e[1]}


def fmt(rec, label="", extra=""):
    if rec is None:
        return "  %-22s (none)" % label
    return ("  %-22s %-8s w=%5.1f gap=%4.1f n=%2d d_in=%6.1fu  L=%9.2fnH  "
            "R=%8.2f  Q=%.5f%s" % (
                label, rec["shape"], rec["w_um"], rec["gap_um"], rec["n"],
                rec["d_in_um"], rec["l_nh"], rec["r_ac"], rec["q"], extra))


def main():
    tx = ref_tx()
    print("Receive coil: every spiral in %g x %g um the DRC allows"
          % (AREA_UM, AREA_UM))
    print("  w >= %g um, gap >= %g um  (GATE.1/.2, SD.1/.2)"
          % (W_MIN_UM, GAP_MIN_UM))
    print("  band %g - %g kHz, operated at %g kHz"
          % (F_BAND[0] / 1e3, F_BAND[1] / 1e3, F_OP / 1e3))
    print("  reference transmitter: %d-turn AWG%d pancake, d_in %g mm, "
          "L = %.2f uH, at %g mm"
          % (tx["n"], tx["awg"], tx["d_in_mm"], tx["l_h"] * 1e6, tx["z"] * 1e3))

    delta = cc.skin_depth(RHO, F_OP)
    print("\nSkin depth in gold at %g kHz = %.1f um - %.0fx the thicker metal,"
          % (F_OP / 1e3, delta * 1e6, delta / 1e-6))
    print("  so R_ac = R_dc exactly and Q is simply proportional to frequency.")

    results, rows = {}, []
    for t_um in THICKNESS_UM:
        key = "%gnm" % (t_um * 1e3) if t_um < 1 else "1um"
        print("\n=== metal thickness %s ===" % key)
        entry = {"t_um": t_um}
        for topo in ("series", "parallel"):
            recs = sweep(t_um, topo)
            rows.extend(recs)
            p = pick(recs, tx)
            entry[topo] = p
            entry["n_" + topo] = len(recs)
            print(" %s: %d legal geometries" % (topo, len(recs)))
            print(fmt(p["max_l"], "max L"))
            print(fmt(p["max_q"], "max Q"))
            if p["max_fom"]:
                print(fmt(p["max_fom"], "max FOM (matched)",
                          "  FOM=%.3e" % p["max_fom_link"]["fom"]))
                print(fmt(p["max_emf"], "max EMF (threshold)",
                          "  M=%.3eH" % p["max_emf_link"]["m_h"]))
            else:
                print("  (not scored on M: the turn-pair sum assumes one "
                      "current, and parallel rings divide it)")
        results[key] = entry

    ser = results["1um"]["series"]
    chosen, chosen_link = ser["max_emf"], ser["max_emf_link"]
    alt, alt_link = ser["max_fom"], ser["max_fom_link"]
    reg = regime(chosen)

    print("\n=== is there a tank? ===")
    print("  the three impedances in the receive loop, at the band edges:")
    print("    f (kHz)  C (uF)   |wL| (ohm)  |1/wC| (ohm)   R (ohm)     R/X")
    for r in reg["rows"]:
        print("    %7.1f  %6g   %10.3f  %11.4f  %8.1f  %6.0f"
              % (r["f_hz"] / 1e3, r["c_f"] * 1e6, r["xl"], r["xc"], r["r"],
                 r["r_over_x"]))
    print("  -> %s" % ("RESISTIVE: R dominates both reactances everywhere in "
                       "the band." if reg["resistive"] else
                       "there is a genuine tank here; re-examine the choice."))
    if reg["resistive"]:
        print("     The capacitor is not tuning anything - it is the doubler's")
        print("     DC block, and any of the three values does that job.  The")
        print("     frequency is free inside the band, and EMF grows with it,")
        print("     so the link is operated at the top: %g kHz." % (F_OP / 1e3))

    print("\n=== the design point ===")
    print(fmt(chosen, "chosen: max EMF"))
    print(fmt(alt, "rejected: max FOM"))
    print("  M to the reference transmitter: %.4e H vs %.4e H - a factor of %.2f"
          % (chosen_link["m_h"], alt_link["m_h"],
             chosen_link["m_h"] / alt_link["m_h"]))
    print("  turn area:                      %.4e m2 vs %.4e m2"
          % (chosen["turn_area_m2"], alt["turn_area_m2"]))
    print("  FOM:                            %.4e vs %.4e"
          % (chosen_link["fom"], alt_link["fom"]))
    print("  The matched-load figure of merit prefers the other coil.  It is")
    print("  the wrong criterion here: the load is a threshold, not an")
    print("  impedance, and below threshold the link delivers nothing at all.")

    ch50 = evaluate(chosen["w_um"], chosen["gap_um"], chosen["n"],
                    chosen["shape"], "series", 0.05, F_OP)
    ch50_link = score(ch50, tx)
    print("\n" + fmt(ch50, "same coil, 50 nm Au"))
    print("  M is unchanged - it is geometry.  R is %.0fx higher."
          % (ch50["r_ac"] / chosen["r_ac"]))

    print("\n  resonance, for the record (it is not used to choose anything):")
    for c in CAPS:
        f_r = link.resonant_f(chosen["l_nh"] * 1e-9, c)
        print("    C = %5.1f uF -> %8.2f kHz" % (c * 1e6, f_r / 1e3))

    print("\n  PCell parameters (ind_igzo): shape=%s topology=series n=%d "
          "d_in=%.1fu w=%.1fu gap=%.1fu t_metal=%g"
          % (chosen["shape"], chosen["n"], chosen["d_in_um"], chosen["w_um"],
             chosen["gap_um"], chosen["t_um"]))

    out = {"area_um": AREA_UM, "f_pref_hz": F_PREF, "f_op_hz": F_OP,
           "f_band_hz": list(F_BAND), "caps_f": list(CAPS), "rho_ohm_m": RHO,
           "drc": {"w_min_um": W_MIN_UM, "gap_min_um": GAP_MIN_UM},
           "skin_depth_um": delta * 1e6, "regime": reg,
           "ref_tx": {k: v for k, v in tx.items() if k != "radii"},
           "by_thickness": results,
           "chosen": chosen, "chosen_link": chosen_link,
           "rejected_fom": alt, "rejected_fom_link": alt_link,
           "chosen_50nm": ch50, "chosen_50nm_link": ch50_link,
           "resonance": [{"c_f": c,
                          "f_hz": link.resonant_f(chosen["l_nh"] * 1e-9, c)}
                         for c in CAPS]}
    with open(os.path.join(HERE, "rx_coil.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=float)
    with open(os.path.join(HERE, "rx_sweep.csv"), "w", newline="") as fh:
        wtr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wtr.writeheader()
        wtr.writerows(rows)
    print("\nwrote rx_coil.json and rx_sweep.csv (%d geometries)" % len(rows))
    return 0


def check_tx():
    """Does the winner depend on which transmitter it was scored against?"""
    print("Ranking the receive coils against two different transmitters.\n")
    recs = sweep(1.0, "series")
    winners = {}
    for name, txc in (("pancake, 20t AWG26, 10 mm, z=5 mm", ref_tx()),
                      ("solenoid, 40t AWG22, 30 mm, z=5 mm", ref_tx_solenoid())):
        p = pick(recs, txc)
        c = p["max_emf"]
        key = (c["shape"], c["w_um"], c["gap_um"], c["n"])
        winners[name] = key
        print("  %-38s -> %-8s w=%g gap=%g n=%d   M=%.3e H"
              % (name, key[0], key[1], key[2], key[3],
                 p["max_emf_link"]["m_h"]))
    same = len(set(winners.values())) == 1
    print("\n  %s" % ("SAME WINNER - the ranking is a property of the receiver"
                      if same else "DIFFERENT WINNERS - the claim in the "
                                   "docstring is wrong, fix it"))
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(check_tx() if "--check-tx" in sys.argv else main())
