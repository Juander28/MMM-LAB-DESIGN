#!/usr/bin/env python3
"""Proximity-effect resistance in a multi-layer winding: Dowell's equation.

WHY THIS FILE EXISTS.  coil_core.ac_resistance_round models the skin effect in
an ISOLATED round wire, which is the right model for a single layer and the
wrong one for a winding.  In a multi-layer coil the field of every other layer
drives eddy currents in each conductor, and the loss grows roughly as the
square of the layer count.  Without that term an optimiser handed a free choice
of layers will take as many as the grid allows: a twelve-layer solenoid came
out of this sweep claiming Q = 845 at 500 kHz, which no hand-wound coil reaches.
The term is not a refinement, it is the reason the answer was wrong.

THE MODEL.  Dowell 1966 - the standard one-dimensional treatment.  The winding
is flattened into equivalent foil layers, and for layer count m,

    F_R = X * [ (sinh 2X + sin 2X)/(cosh 2X - cos 2X)          <- skin
                + (2/3)(m^2 - 1)(sinh X - sin X)/(cosh X + cos X) ]   <- proximity

X is the layer thickness in skin depths.

ONLY THE SECOND TERM IS TAKEN FROM DOWELL HERE.  The first one is a foil
model, and a foil is not a wire: it treats the layer as solid copper spanning
the full breadth, so for one layer of 0.64 mm wire at 500 kHz it returns 6.2
where the round conductor really has about 2.0.  The skin term is therefore
taken from coil_core.ac_resistance_round, which models the annulus the current
actually flows in, and Dowell supplies the proximity term it is missing:

    R_ac = R_skin(round wire) + R_dc * X * (2/3)(m^2-1) * (sinh X - sin X)
                                                        / (cosh X + cos X)

Each term from the model that describes it, and neither counted twice.

ROUND WIRE INTO FOIL.  Two corrections, both standard:
  - a round conductor of diameter d is replaced by a square of the same area,
    of side d*sqrt(pi)/2 = 0.886 d;
  - the layer is not solid copper, so its conductivity is scaled by the
    porosity eta = (turns per layer) * d / (winding breadth), and X picks up a
    factor sqrt(eta).

WHAT IT DOES NOT COVER.  It is one-dimensional: it assumes the field runs
parallel to the layers, which is true well inside a long solenoid and less true
at its ends and in a flat spiral.  For a short coil it OVERSTATES the loss, so
the efficiency that comes out of it is a floor rather than a centre estimate.
That is the direction an honest error should point.

Reference
  P. L. Dowell, "Effects of eddy currents in transformer windings",
  Proc. IEE, vol. 113, no. 8, pp. 1387-1394, 1966.
"""

import math


def _x(d_wire, delta, turns_per_layer=None, breadth=None):
    """Layer thickness in skin depths, with the round-to-foil corrections."""
    h = d_wire * math.sqrt(math.pi) / 2.0        # equal-area square conductor
    eta = 1.0
    if turns_per_layer and breadth and breadth > 0:
        eta = min(turns_per_layer * d_wire / breadth, 1.0)
    return (h / delta) * math.sqrt(eta)


def proximity_factor(d_wire, delta, layers, turns_per_layer=None, breadth=None):
    """The proximity term alone, as a multiple of R_dc.  Zero for one layer."""
    if d_wire <= 0 or delta <= 0 or layers <= 1:
        return 0.0
    x = _x(d_wire, delta, turns_per_layer, breadth)
    if x < 1e-6:
        return 0.0
    if x > 30.0:
        return x * (2.0 / 3.0) * (layers * layers - 1)
    s1, c1 = math.sinh(x), math.cosh(x)
    return x * (2.0 / 3.0) * (layers * layers - 1) * (s1 - math.sin(x)) / (c1 + math.cos(x))


def dowell_factor(d_wire, delta, layers, turns_per_layer=None, breadth=None):
    """Dowell's full R_ac/R_dc, foil model for both terms.

    Kept for reference and for the selftest; ac_resistance() below does NOT
    use its skin term.  See the module docstring for why.

    d_wire   conductor diameter, m
    delta    skin depth at the frequency of interest, m
    layers   number of layers the field builds up across
    turns_per_layer, breadth   used for the porosity; if either is missing the
                               turns are taken as touching (eta = 1), which is
                               the densest case and therefore the lossiest
    """
    if d_wire <= 0 or delta <= 0 or layers < 1:
        return 1.0
    x = _x(d_wire, delta, turns_per_layer, breadth)
    if x < 1e-6:
        return 1.0
    if x > 30.0:
        # Both bracketed terms saturate; evaluating the hyperbolics overflows.
        return x * (1.0 + (2.0 / 3.0) * (layers * layers - 1))

    s2, c2 = math.sinh(2 * x), math.cosh(2 * x)
    s1, c1 = math.sinh(x), math.cosh(x)
    skin = (s2 + math.sin(2 * x)) / (c2 - math.cos(2 * x))
    prox = (2.0 / 3.0) * (layers * layers - 1) * (s1 - math.sin(x)) / (c1 + math.cos(x))
    return x * (skin + prox)


def skin_resistance_round(rho, length, d_wire, freq):
    """Skin effect in an isolated round wire: the conducting annulus."""
    a = d_wire / 2.0
    r_dc = rho * length / (math.pi * a * a) if a > 0 else 0.0
    if freq <= 0:
        return r_dc
    delta = math.sqrt(rho / (math.pi * 4e-7 * math.pi * freq))
    if delta >= a:
        return r_dc
    return rho * length / (math.pi * (a * a - (a - delta) ** 2))


def ac_resistance(rho, length, d_wire, freq, layers=1, turns_per_layer=None,
                  breadth=None):
    """Skin from the round-wire model, proximity from Dowell.

    Returns (R_ac, R_ac/R_dc).
    """
    a = d_wire / 2.0
    r_dc = rho * length / (math.pi * a * a) if a > 0 else 0.0
    if freq <= 0 or r_dc <= 0:
        return r_dc, 1.0
    delta = math.sqrt(rho / (math.pi * 4e-7 * math.pi * freq))
    r_skin = skin_resistance_round(rho, length, d_wire, freq)
    r_prox = r_dc * proximity_factor(d_wire, delta, layers, turns_per_layer,
                                     breadth)
    r_ac = r_skin + r_prox
    return r_ac, r_ac / r_dc


def _selftest():
    ok = True
    rho, mu0 = 1.68e-8, 4e-7 * math.pi

    def delta_at(f):
        return math.sqrt(rho / (math.pi * mu0 * f))

    print("A single layer of thin wire, well below the skin depth: F_R -> 1")
    for f in (1e3, 1e4):
        _, fr = ac_resistance(rho, 1.0, 0.1e-3, f, layers=1)
        good = abs(fr - 1.0) < 0.05
        ok = ok and good
        print("  f = %6.0f Hz  delta = %6.1f um  F_R = %.4f  %s"
              % (f, delta_at(f) * 1e6, fr, "ok" if good else "FAIL"))

    print("\nOne layer of thick wire: the round-wire skin ratio, NOT the foil one")
    d, f = 0.644e-3, 500e3
    _, fr = ac_resistance(rho, 1.0, d, f, layers=1)
    foil = dowell_factor(d, delta_at(f), 1)
    # d/delta = 6.96; the annulus model gives about 2, the foil model 6.2
    good = 1.5 < fr < 2.5 and foil > 5.0
    ok = ok and good
    print("  d/delta = %.2f   annulus F_R = %.3f   foil F_R = %.3f   %s"
          % (d / delta_at(f), fr, foil, "ok" if good else "FAIL"))

    print("\nF_R grows with layer count, and faster than linearly")
    prev, ratios = None, []
    for m in (1, 2, 4, 8, 12):
        _, fr = ac_resistance(rho, 1.0, d, f, layers=m)
        if prev:
            ratios.append(fr / prev)
        print("  %2d layers  F_R = %8.2f" % (m, fr))
        prev = fr
    good = all(r > 1.0 for r in ratios)
    ok = ok and good
    print("  monotonic increasing: %s" % ("ok" if good else "FAIL"))

    print("\nAt high layer count the factor approaches the m^2 law")
    _, a = ac_resistance(rho, 1.0, d, f, layers=8)
    _, b = ac_resistance(rho, 1.0, d, f, layers=16)
    good = 3.5 < b / a < 4.5
    ok = ok and good
    print("  F_R(16)/F_R(8) = %.2f  (m^2 would give 4.00)  %s"
          % (b / a, "ok" if good else "FAIL"))

    print("\nPorosity: a loosely wound layer loses less than a packed one")
    _, packed = ac_resistance(rho, 1.0, d, f, 4, turns_per_layer=10,
                              breadth=10 * d)
    _, loose = ac_resistance(rho, 1.0, d, f, 4, turns_per_layer=10,
                             breadth=30 * d)
    good = loose < packed
    ok = ok and good
    print("  packed F_R = %.2f, loose F_R = %.2f  %s"
          % (packed, loose, "ok" if good else "FAIL"))

    print("\nNo overflow at extreme argument")
    try:
        _, v = ac_resistance(rho, 1.0, 10e-3, 10e6, layers=20)
        good = math.isfinite(v)
    except OverflowError:
        good = False
        v = float("nan")
    ok = ok and good
    print("  F_R = %.4g  %s" % (v, "ok" if good else "FAIL"))

    print("\n%s" % ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
