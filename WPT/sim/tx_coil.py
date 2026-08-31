#!/usr/bin/env python3
"""Design the transmit coil: discrete copper wire, wound off-chip.

The receiver is fixed by then - rx_coil.py has already chosen it, and it is a
51 nH square spiral on glass with a Q of about 0.01.  This module picks the
copper coil that drives it: topology, diameter, turns, wire gauge, and the
number the question was really about, the thickness of the copper wire.

WHAT IS BEING MAXIMISED, and why it is not the figure of merit.  The receiver
turned out to be threshold-limited rather than impedance-matched - the load is
two diode-connected TFTs that do not conduct at all below threshold - so what
the transmitter has to deliver is VOLTAGE at the receiver, not matched power:

    EMF = w * M * I_tx

For a fair comparison the candidates are normalised to the same input power
rather than the same current, since a coil can always be given more current by
being given more power.  With I_tx = sqrt(P_in / R_total),

    EMF / sqrt(P_in) = w * M / sqrt(R_src + R_tx)

and that is the objective.  k^2 Q1 Q2 is computed and reported alongside,
because it is the standard number and because the difference between the two
is worth seeing, but it is not what chooses the coil.  Q1 and k pull in
opposite directions - a big coil has a high Q and couples badly to a 1 mm
target, a small one couples well and has a poor Q - so the optimum is interior
either way, and the sweep is what finds it.

TWO TOPOLOGIES, both already solved in coil_core:
  pancake    a flat spiral - Mohan-Wheeler for the inductance, and every turn
             at its own radius in the same plane
  solenoid   a cylindrical multi-layer winding - Wheeler 1928, and every turn
             at the same radius but its own axial position

WIRE GAUGE.  AWG diameters are the ASTM B258 formula, in coil_core.  The skin
depth in copper at 500 kHz is 92 um and the wire diameters in play are
comparable to it, so the sweep checks each candidate against its own skin depth
rather than assuming either way.

LOSS IS NOT JUST SKIN EFFECT, AND THAT CHANGED THE ANSWER.  coil_core's
ac_resistance_round is an isolated-wire model.  Scored with it, this sweep
walked straight into the deepest multi-layer winding the grid allowed and
claimed Q = 845 at 500 kHz for a twelve-layer solenoid - a coil that does not
exist, because the proximity effect between layers was missing and nothing
penalised depth.  proximity.py supplies it (Dowell 1966), and the optimum moves.
The lesson is general: an optimiser will find whatever the loss model forgot.

MULTI-LAYER COUNT FOR EACH TOPOLOGY.  Proximity loss is driven by how many
conductors the magnetic field has to build up across:
  solenoid   the radial layers, so m = layers
  pancake    every turn is its own layer in the radial direction, so m = n.
             This is the standard treatment of a flat spiral and it is
             pessimistic for a wide, loosely spaced one.
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
import proximity                                            # noqa: E402
import rx_coil                                              # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RHO = link.RHO_CU

# --- the sweep grid -------------------------------------------------------
# The grid was widened twice, both times because the winner landed on its edge.
# It now runs from AWG 10 (2.6 mm, about as thick as anyone hand-winds) to
# AWG 36, and up to 12 layers deep.
AWG_GRID = list(range(8, 43, 2))            # 8 (3.26 mm) to 42 (0.064 mm)
# The gauge is bounded by what can be wound, NOT by the physics - but which way
# it is bounded depends on the objective, and that caught this sweep out twice.
#
#   Judged on k^2 Q1 Q2, thicker always wins: past the skin depth the current
#   runs in an annulus of depth delta, so R_ac falls as 1/d, slowly and without
#   ever stopping.
#   Judged on EMF per sqrt(watt), THINNER wins instead, and for a different
#   reason: the grid gives every gauge the same turn count, so thin wire packs
#   the same turns into a much shorter winding and keeps them close to the
#   receiver.  Fifty turns of AWG 36 make a 6 mm solenoid; fifty of AWG 18 make
#   a 51 mm one, and its far end couples to nothing.
#
# So the gauge is bounded at both ends, and both bounds are practical rather
# than physical: AWG 18 is about the thickest that is comfortable to wind on a
# former this small, AWG 36 about the thinnest that survives handling.  What
# lies outside is reported rather than silently chosen.  The real answer above
# a few hundred kHz is litz wire, which is outside what coil_core models.
PRACTICAL_AWG_MIN = 18
PRACTICAL_AWG_MAX = 36
D_IN_GRID_MM = [1, 2, 3, 5, 8, 10, 15, 20, 30, 40, 60, 80, 120]
N_GRID = [1, 2, 3, 5, 8, 12, 20, 30, 50, 80, 120, 200]
LAYER_GRID = [1, 2, 4, 6, 8, 12]
Z_DEFAULT_MM = 5.0                          # working separation
R_SRC = 1.0                                 # driver output resistance, ohm
Z_GRID_MM = [1, 2, 3, 5, 8, 12, 20, 30, 50]


def pancake(d_in_mm, n, awg):
    """A flat spiral of round wire, turns laid side by side in one plane."""
    d_w = cc.awg_to_diameter(awg)
    d_in = d_in_mm * 1e-3
    d_out = cc.outer_diameter(d_in, d_w, 0.0, n)
    l_h = cc.mohan_wheeler(d_in, d_w, 0.0, n, "circular")
    length = cc.spiral_length_circular(d_in, d_out, n)
    radii = [d_in / 2.0 + d_w / 2.0 + k * d_w for k in range(int(n))]
    return {"topology": "pancake", "d_in_mm": d_in_mm, "d_out_mm": d_out * 1e3,
            "n": int(n), "layers": 1, "awg": awg, "d_wire_mm": d_w * 1e3,
            "l_h": l_h, "length_m": length, "radii": radii, "z_of": None}


def solenoid(d_mm, n, awg, layers=1):
    """A cylindrical winding: n turns per layer, `layers` layers deep."""
    d_w = cc.awg_to_diameter(awg)
    a = d_mm * 1e-3 / 2.0 + (layers - 1) * d_w / 2.0     # mean radius
    h = n * d_w                                          # axial length
    b = layers * d_w                                     # radial depth
    l_h = cc.wheeler_multilayer(a, h, b, n * layers)
    length = 2.0 * math.pi * a * n * layers
    # The winding runs from its near face (z = 0) away from the receiver, so
    # that a separation of z mm really is z mm to the closest turn.  Centring
    # it on the separation plane instead puts the receiver INSIDE the coil for
    # any winding longer than the gap, and reports a coupling to match.
    radii, z_of = [], []
    for ly in range(int(layers)):
        r = d_mm * 1e-3 / 2.0 + (ly + 0.5) * d_w
        for z in link.solenoid_axial(h, n, z0=-h / 2.0):
            radii.append(r)
            z_of.append(z)
    return {"topology": "solenoid", "d_in_mm": d_mm,
            "d_out_mm": (d_mm * 1e-3 + 2 * layers * d_w) * 1e3,
            "n": int(n), "layers": int(layers), "awg": awg,
            "d_wire_mm": d_w * 1e3, "l_h": l_h, "length_m": length,
            "radii": radii, "z_of": z_of}


def characterise(tx, f):
    """Resistance, skin depth and Q of a candidate at one frequency."""
    d_w = tx["d_wire_mm"] * 1e-3
    r_dc = cc.dc_resistance(RHO, tx["length_m"], math.pi * (d_w / 2.0) ** 2)
    if tx["topology"] == "solenoid":
        m, per_layer, breadth = tx["layers"], tx["n"], tx["n"] * d_w
    else:
        m, per_layer, breadth = tx["n"], 1, d_w
    r_ac, ratio = proximity.ac_resistance(RHO, tx["length_m"], d_w, f,
                                          layers=m, turns_per_layer=per_layer,
                                          breadth=breadth)
    r_skin = proximity.skin_resistance_round(RHO, tx["length_m"], d_w, f)
    delta = cc.skin_depth(RHO, f)
    return {"r_dc": r_dc, "r_ac": r_ac, "r_skin": r_skin,
            "r_prox": r_ac - r_skin, "prox_layers": m,
            "skin_um": delta * 1e6, "skin_limited": delta < d_w / 2.0,
            "r_ratio": ratio, "q": cc.quality_factor(tx["l_h"], r_ac, f)}


def link_to(tx, rx_radii, l_rx, q_rx, f, z_mm):
    """Couple a candidate transmitter to the chosen receiver."""
    m = link.mutual_fast(tx["radii"], rx_radii, z_a=tx["z_of"], gap_z=z_mm * 1e-3)
    k = link.coupling(m, tx["l_h"], l_rx)
    ch = characterise(tx, f)
    f_om = link.fom(k, ch["q"], q_rx)
    # The objective: induced volts per square root of watt into the driver.
    emf_pw = 2.0 * math.pi * f * m / math.sqrt(R_SRC + ch["r_ac"])
    return {"m_h": m, "k": k, "fom": f_om, "eta_max": link.eta_max(f_om),
            "emf_per_sqrtw": emf_pw, **ch}


def candidates():
    for awg in AWG_GRID:
        d_w_mm = cc.awg_to_diameter(awg) * 1e3
        for d in D_IN_GRID_MM:
            for n in N_GRID:
                yield pancake(d, n, awg)
                for ly in LAYER_GRID:
                    # A winding deeper than it is wide is not a solenoid.
                    if ly * d_w_mm > n * d_w_mm:
                        continue
                    yield solenoid(d, n, awg, ly)


def selftest():
    """Two things that were wrong once and are cheap to keep checking.

    Both were sign and placement errors in how a winding is put on the axis,
    and both showed up only as a coupling coefficient that was too good.  A
    number that flatters the design is exactly the kind that does not get
    questioned, so it gets an assertion instead.
    """
    ok = True
    print("Geometry: the nearest turn must sit at the nominal separation")
    for n, ly in ((30, 4), (50, 1), (120, 2)):
        tx = solenoid(2.0, n, 30, ly)
        gap = 5e-3
        d = [abs(gap - z) for z in tx["z_of"]]
        good = abs(min(d) - gap) < 1e-9 and max(d) > gap
        ok = ok and good
        print("  n=%3d layers=%d  closest %.3f mm, farthest %.3f mm  %s"
              % (n, ly, min(d) * 1e3, max(d) * 1e3, "ok" if good else "FAIL"))

    print("\nCoupling: the elliptic sum against the dipole approximation")
    r_rx, l_rx = 965e-6 / math.sqrt(math.pi), 51.13e-9
    for gap_mm in (5.0, 10.0, 20.0):
        tx = solenoid(2.0, 30, 30, 4)
        gap = gap_mm * 1e-3
        m = link.mutual(tx["radii"], [r_rx] * 7, z_a=tx["z_of"], gap_z=gap)
        m_dip = sum(link.MU0 * math.pi * r ** 2 * r_rx ** 2 / (2 * abs(gap - z) ** 3)
                    for r, z in zip(tx["radii"], tx["z_of"])) * 7
        ratio = m / m_dip
        good = 0.7 < ratio < 1.05
        ok = ok and good
        print("  gap %4.1f mm  M = %.4e H  dipole %.4e H  ratio %.3f  %s"
              % (gap_mm, m, m_dip, ratio, "ok" if good else "FAIL"))

    print("\nCoupling falls off monotonically with distance")
    tx = solenoid(2.0, 30, 30, 4)
    prev, mono = float("inf"), True
    for gap_mm in (1, 2, 5, 10, 20, 50):
        m = link.mutual(tx["radii"], [r_rx] * 7, z_a=tx["z_of"],
                        gap_z=gap_mm * 1e-3)
        mono = mono and m < prev
        prev = m
    ok = ok and mono
    print("  %s" % ("ok" if mono else "FAIL"))
    print("\n%s" % ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    return 0 if ok else 1


def main():
    rx = json.load(open(os.path.join(HERE, "rx_coil.json")))
    ch = rx["chosen"]
    f = rx["chosen_link"]["f_hz"] if "f_hz" in rx["chosen_link"] else ch["f_hz"]
    f = ch["f_hz"]
    l_rx = ch["l_nh"] * 1e-9
    q_rx = ch["q"]
    rx_radii = rx_coil.turn_radii(ch["w_um"], ch["gap_um"], ch["n"],
                                  ch["shape"], ch["d_out_um"])

    print("Transmit coil: copper wire, wound off-chip.")
    print("  driving the receiver chosen by rx_coil.py:")
    print("    %s spiral, w=%g gap=%g n=%d, L = %.2f nH, Q = %.5f at %.0f kHz"
          % (ch["shape"], ch["w_um"], ch["gap_um"], ch["n"], ch["l_nh"],
             q_rx, f / 1e3))
    print("  separation %g mm\n" % Z_DEFAULT_MM)

    delta = cc.skin_depth(RHO, f)
    print("Skin depth in copper at %.0f kHz = %.1f um (wire radius above that"
          % (f / 1e3, delta * 1e6))
    print("  is where the gauge starts to cost more than it buys):")
    for awg in AWG_GRID:
        d_w = cc.awg_to_diameter(awg)
        print("    AWG %2d  d = %6.3f mm  radius %6.1f um  %s"
              % (awg, d_w * 1e3, d_w / 2 * 1e6,
                 "SKIN LIMITED" if d_w / 2 > delta else "uniform current"))

    rows, best, free = [], None, None
    for tx in candidates():
        r = link_to(tx, rx_radii, l_rx, q_rx, f, Z_DEFAULT_MM)
        row = {k: v for k, v in tx.items() if k not in ("radii", "z_of")}
        row.update({k: v for k, v in r.items()})
        row["l_uh"] = tx["l_h"] * 1e6
        rows.append(row)
        if free is None or r["emf_per_sqrtw"] > free[1]["emf_per_sqrtw"]:
            free = (tx, r, row)
        if PRACTICAL_AWG_MIN <= tx["awg"] <= PRACTICAL_AWG_MAX and (
                best is None
                or r["emf_per_sqrtw"] > best[1]["emf_per_sqrtw"]):
            best = (tx, r, row)

    print("\n%d candidates evaluated." % len(rows))
    for topo in ("pancake", "solenoid"):
        sub = [r for r in rows
               if r["topology"] == topo
               and PRACTICAL_AWG_MIN <= r["awg"] <= PRACTICAL_AWG_MAX]
        b = max(sub, key=lambda r: r["emf_per_sqrtw"])
        print("  best %-9s d=%4gmm n=%3d layers=%d AWG%2d (%.3f mm)  "
              "L=%7.2fuH Q=%6.1f  k=%.3e  EMF/sqrtW=%.4f  FOM=%.3e"
              % (topo, b["d_in_mm"], b["n"], b["layers"], b["awg"],
                 b["d_wire_mm"], b["l_uh"], b["q"], b["k"],
                 b["emf_per_sqrtw"], b["fom"]))

    # What each gauge is worth - the diminishing return that makes the bound
    # a practical choice rather than a discovered optimum.
    print("\n  best EMF per sqrt(W) at each gauge (this objective wants THINNER):")
    by_awg = []
    for awg in AWG_GRID:
        sub = [r for r in rows if r["awg"] == awg]
        b = max(sub, key=lambda r: r["emf_per_sqrtw"])
        by_awg.append({"awg": awg, "d_wire_mm": b["d_wire_mm"], "fom": b["fom"],
                       "emf_per_sqrtw": b["emf_per_sqrtw"],
                       "q": b["q"], "topology": b["topology"], "n": b["n"],
                       "layers": b["layers"], "d_in_mm": b["d_in_mm"]})
        print("    AWG %2d  %6.3f mm  EMF/sqrtW = %.4f  Q = %6.1f  %s%s"
              % (awg, b["d_wire_mm"], b["emf_per_sqrtw"], b["q"],
                 b["topology"],
                 "   <- practical limit"
                 if awg in (PRACTICAL_AWG_MIN, PRACTICAL_AWG_MAX) else ""))

    tx, r, row = best
    ftx, fr, _ = free
    if not (PRACTICAL_AWG_MIN <= ftx["awg"] <= PRACTICAL_AWG_MAX):
        print("\n  Unbounded, the sweep picks AWG %d (%.2f mm), EMF/sqrtW %.4f,"
              % (ftx["awg"], ftx["d_wire_mm"], fr["emf_per_sqrtw"]))
        print("  a factor of %.2f over the practical choice.  That is the cost"
              % (fr["emf_per_sqrtw"] / r["emf_per_sqrtw"]))
        print("  of the winding constraint, stated rather than hidden.")
    edges = []
    if tx["awg"] in (PRACTICAL_AWG_MIN, PRACTICAL_AWG_MAX):
        pass                    # bounded on purpose, not a grid artefact
    elif tx["awg"] in (min(AWG_GRID), max(AWG_GRID)):
        edges.append("wire gauge (AWG %d)" % tx["awg"])
    if tx["d_in_mm"] in (min(D_IN_GRID_MM), max(D_IN_GRID_MM)):
        edges.append("former diameter (%g mm)" % tx["d_in_mm"])
    if tx["n"] in (min(N_GRID), max(N_GRID)):
        edges.append("turns (%d)" % tx["n"])
    if tx["layers"] in (min(LAYER_GRID), max(LAYER_GRID)) and tx["layers"] != 1:
        edges.append("layers (%d)" % tx["layers"])
    if edges:
        print("\n  WARNING: the winner sits on the edge of the sweep in %s."
              % ", ".join(edges))
        print("  An optimum on a boundary is a grid that stopped too early,")
        print("  not an optimum.  Widen the grid before believing it.")

    print("\n=== the transmit coil ===")
    print("  topology            %s" % tx["topology"])
    print("  turns               %d  in %d layer(s)" % (tx["n"], tx["layers"]))
    print("  former diameter     %.1f mm  (outer %.1f mm)"
          % (tx["d_in_mm"], tx["d_out_mm"]))
    print("  wire                AWG %d" % tx["awg"])
    print("  COPPER WIRE THICKNESS  %.3f mm  (%.1f um)"
          % (tx["d_wire_mm"], tx["d_wire_mm"] * 1e3))
    print("  wire length         %.2f m" % tx["length_m"])
    print("  inductance          %.3f uH" % (tx["l_h"] * 1e6))
    print("  R_dc / R_ac         %.4f / %.4f ohm  (ratio %.3f)"
          % (r["r_dc"], r["r_ac"], r["r_ratio"]))
    print("    of which skin      %.4f ohm, proximity %.4f ohm across %d layers"
          % (r["r_skin"], r["r_prox"], r["prox_layers"]))
    print("  Q at %.0f kHz        %.1f" % (f / 1e3, r["q"]))
    print("  k to the receiver   %.4e" % r["k"])
    print("  EMF per sqrt(W)     %.4f V/sqrt(W)   <- the objective"
          % r["emf_per_sqrtw"])
    print("  FOM / eta_max       %.4e / %.4e  (%.5f %%)"
          % (r["fom"], r["eta_max"], r["eta_max"] * 100))
    for pw in (1.0, 10.0, 100.0):
        print("    at %5.0f W in: I_tx = %7.2f A, EMF = %.4e V"
              % (pw, math.sqrt(pw / (R_SRC + r["r_ac"])),
                 r["emf_per_sqrtw"] * math.sqrt(pw)))
    print("  skin effect         %s (delta = %.1f um, wire radius %.1f um)"
          % ("LIMITED" if r["skin_limited"] else "negligible",
             r["skin_um"], tx["d_wire_mm"] * 1e3 / 2))

    # How coupling and the figure of merit fall away with distance.
    dist = []
    for z in Z_GRID_MM:
        rz = link_to(tx, rx_radii, l_rx, q_rx, f, z)
        dist.append({"z_mm": z, "k": rz["k"], "fom": rz["fom"],
                     "eta_max": rz["eta_max"], "m_h": rz["m_h"],
                     "emf_per_sqrtw": rz["emf_per_sqrtw"]})
    print("\n  distance    k          M (H)      EMF/sqrtW   eta_max")
    for d in dist:
        print("   %5g mm  %.3e  %.3e  %9.5f  %.3e"
              % (d["z_mm"], d["k"], d["m_h"], d["emf_per_sqrtw"],
                 d["eta_max"]))

    out = {"f_hz": f, "z_mm": Z_DEFAULT_MM, "r_src": R_SRC,
           "practical_awg_min": PRACTICAL_AWG_MIN,
           "practical_awg_max": PRACTICAL_AWG_MAX,
           "by_awg": by_awg,
           "free": {k: v for k, v in ftx.items() if k not in ("radii", "z_of")},
           "free_link": fr,
           "rx": {"l_nh": ch["l_nh"], "q": q_rx, "r_ac": ch["r_ac"]},
           "chosen": {k: v for k, v in tx.items() if k not in ("radii", "z_of")},
           "chosen_link": r, "distance": dist,
           "skin_depth_um": delta * 1e6}
    with open(os.path.join(HERE, "tx_coil.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=float)
    with open(os.path.join(HERE, "tx_sweep.csv"), "w", newline="") as fh:
        wtr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wtr.writeheader()
        wtr.writerows(rows)
    print("\nwrote tx_coil.json and tx_sweep.csv (%d candidates)" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
