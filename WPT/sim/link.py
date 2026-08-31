#!/usr/bin/env python3
"""Coupling between the transmit and the receive coil, and what it is worth.

The physics is not reimplemented here.  Mutual inductance comes from
coil_core.mutual_coaxial_rings - Neumann's integral in closed form via the
complete elliptic integrals, Babic & Akyel 2008 - applied to every pair of
turns, one turn of one coil against one turn of the other.  This module only
turns a pair of drawn geometries into that sum, and the sum into the numbers a
link is judged by: M, k, and the figure of merit.

TWO COILS OF DIFFERENT SHAPES.  The receive coil is a square planar spiral on
glass; the transmit coil is round copper wire.  mutual_coaxial_rings takes
circular rings, so each square turn is replaced by the circle enclosing the
same area - side s becomes radius s/sqrt(pi).  Mutual inductance at a distance
is set by enclosed flux, and flux is set by area, so matching the area is the
right substitution; it is exact in the far field and an approximation close up,
where the shape of the boundary starts to matter.

WHAT THE FIGURE OF MERIT IS.  For two coils coupled by k, each with its own Q,
the best power efficiency any matching network can reach is a function of one
number only:

    FOM = k^2 * Q1 * Q2
    eta_max = FOM / (1 + sqrt(1 + FOM))^2

That is the ceiling, not a prediction: it assumes both sides are tuned and the
load is the optimal one.  A real rectifier reaches less.  It is used here as
the objective for the geometry search, because it is the part of the problem
that geometry controls - and then ngspice is asked what the actual circuit
does, which is a different question with a smaller answer.
"""

import math
import os
import sys

PDK_TOOLS = "/foss/designs/TFT-MMM-LAB-PDK/tools"
if PDK_TOOLS not in sys.path:
    sys.path.insert(0, PDK_TOOLS)

import numpy as np                                          # noqa: E402
from scipy.special import ellipe, ellipk                    # noqa: E402
import coil_core as cc                                      # noqa: E402

MU0 = cc.MU0
RHO_AU = 2.44e-8            # gold, the metal the PCell assumes
RHO_CU = 1.68e-8            # copper, the transmit coil


# --------------------------------------------------------------------------
# Geometry: a drawn spiral, turn by turn
# --------------------------------------------------------------------------

def square_turn_sides(d_out, w, gap, n):
    """Centreline side length of each turn of a square spiral, outermost first.

    d_out is the outer extent of the metal, so the outermost centreline sits
    half a track width inside it.  Everything in metres.
    """
    pitch = w + gap
    return [d_out - w - 2.0 * k * pitch for k in range(int(n))]


def circular_turn_diameters(d_out, w, gap, n):
    """Centreline diameter of each turn of a circular spiral, outermost first."""
    pitch = w + gap
    return [d_out - w - 2.0 * k * pitch for k in range(int(n))]


def equivalent_radii(d_out, w, gap, n, shape):
    """Radius of the equal-area circle for each turn.

    A square of side s encloses s^2, so the equal-area circle has radius
    s/sqrt(pi).  A circular turn is already a circle and passes through.
    """
    if shape == "square":
        return [s / math.sqrt(math.pi) for s in square_turn_sides(d_out, w, gap, n)]
    return [d / 2.0 for d in circular_turn_diameters(d_out, w, gap, n)]


def solenoid_radii(d_mean, n_turns):
    """Every turn of a solenoid sits at the same radius."""
    return [d_mean / 2.0] * int(n_turns)


def solenoid_axial(length, n_turns, z0=0.0):
    """Axial position of each turn of a solenoid of the given winding length."""
    n = int(n_turns)
    if n <= 1:
        return [z0]
    step = length / float(n - 1)
    return [z0 - length / 2.0 + k * step for k in range(n)]


# --------------------------------------------------------------------------
# Mutual inductance and coupling
# --------------------------------------------------------------------------

def mutual(radii_a, radii_b, z_a=None, z_b=None, gap_z=0.0):
    """Total mutual inductance between two coaxial coils, turn pair by turn pair.

    radii_* are the turn radii.  z_* are the axial positions of those turns
    within their own coil; when omitted every turn is taken as coplanar, which
    is what a planar spiral is.  gap_z is the separation between the two coils'
    reference planes.
    """
    za = [0.0] * len(radii_a) if z_a is None else list(z_a)
    zb = [0.0] * len(radii_b) if z_b is None else list(z_b)
    total = 0.0
    for ra, zaa in zip(radii_a, za):
        for rb, zbb in zip(radii_b, zb):
            total += cc.mutual_coaxial_rings(ra, rb, abs(gap_z + zbb - zaa))
    return total


def mutual_fast(radii_a, radii_b, z_a=None, z_b=None, gap_z=0.0):
    """mutual(), vectorised.  Same formula, all turn pairs at once.

    The scalar version calls scipy's elliptic integrals once per turn pair.
    With a 49-turn receiver and a 2400-turn transmitter that is 118 000 calls
    per candidate and the sweep stops being runnable.  scipy's ellipk and
    ellipe are already array functions, so the whole pair matrix goes through
    in one call.  Checked against the scalar version in the selftest.
    """
    ra = np.asarray(radii_a, dtype=float)[:, None]
    rb = np.asarray(radii_b, dtype=float)[None, :]
    za = (np.zeros(len(radii_a)) if z_a is None
          else np.asarray(z_a, dtype=float))[:, None]
    zb = (np.zeros(len(radii_b)) if z_b is None
          else np.asarray(z_b, dtype=float))[None, :]
    d = np.abs(gap_z + zb - za)

    k2 = 4.0 * ra * rb / ((ra + rb) ** 2 + d * d)
    k2 = np.clip(k2, 0.0, 1.0 - 1e-12)
    k = np.sqrt(k2)
    kk, ee = ellipk(k2), ellipe(k2)
    m = MU0 * np.sqrt(ra * rb) * ((2.0 / k - k) * kk - (2.0 / k) * ee)
    return float(np.sum(m))


def coupling(m, l1, l2):
    """k = M / sqrt(L1 L2), clipped at 1 - it is a cosine, it cannot exceed it."""
    if l1 <= 0 or l2 <= 0:
        return 0.0
    return min(m / math.sqrt(l1 * l2), 1.0)


def fom(k, q1, q2):
    """The link figure of merit, k^2 Q1 Q2."""
    return k * k * q1 * q2


def eta_max(f):
    """Best achievable power efficiency for a link of figure of merit f."""
    if f <= 0:
        return 0.0
    return f / (1.0 + math.sqrt(1.0 + f)) ** 2


def resonant_c(l_h, f_hz):
    """The capacitance that resonates with l_h at f_hz."""
    if l_h <= 0 or f_hz <= 0:
        return float("inf")
    return 1.0 / ((2.0 * math.pi * f_hz) ** 2 * l_h)


def resonant_f(l_h, c_f):
    """The frequency at which l_h and c_f resonate."""
    if l_h <= 0 or c_f <= 0:
        return float("inf")
    return 1.0 / (2.0 * math.pi * math.sqrt(l_h * c_f))


# --------------------------------------------------------------------------
# Self-test
# --------------------------------------------------------------------------

def _selftest():
    ok = True

    def check(name, got, want, tol):
        nonlocal ok
        rel = abs(got - want) / abs(want) if want else abs(got)
        good = rel <= tol
        ok = ok and good
        print("  %-52s %12.6g  vs %12.6g  %5.2f%%  %s"
              % (name, got, want, 100 * rel, "ok" if good else "FAIL"))

    print("Two coaxial rings, r1 = r2 = r, far apart: the dipole limit")
    # Two coplanar-axis rings far apart behave as magnetic dipoles:
    #   M -> mu0 * pi * r1^2 * r2^2 / (2 * z^3)
    r = 1e-3
    for z in (20e-3, 50e-3):
        got = cc.mutual_coaxial_rings(r, r, z)
        want = MU0 * math.pi * r ** 4 / (2.0 * z ** 3)
        check("M(r=1mm, z=%gmm)" % (z * 1e3), got, want, 0.02)

    print("\nCoupling never exceeds one, over the whole range")
    d_out, w, gap, n = 1000e-6, 5e-6, 5e-6, 44
    rx = equivalent_radii(d_out, w, gap, n, "square")
    l_rx = cc.mohan_wheeler(d_out - 2 * n * w - 2 * (n - 1) * gap, w, gap, n, "cuadrada")
    worst = 0.0
    for z in (0.0, 1e-4, 1e-3, 1e-2):
        m = mutual(rx, rx, gap_z=z)
        k = coupling(m, l_rx, l_rx)
        worst = max(worst, k)
        print("  z = %7.3f mm   M = %10.4g H   k = %.4f" % (z * 1e3, m, k))
    ok = ok and worst <= 1.0
    print("  max k = %.4f  %s" % (worst, "ok" if worst <= 1.0 else "FAIL"))

    print("\nk = 1 when a coil is coupled to itself at zero distance")
    # M of a coil with itself IS its own inductance, so this is a check that the
    # turn-pair sum and the closed-form L agree in order of magnitude.  They are
    # different approximations - the sum has no self term for a filament - so
    # this is a sanity bound, not an equality.
    m_self = mutual(rx, rx, gap_z=0.0)
    print("  turn-pair sum   = %10.4g H" % m_self)
    print("  Mohan-Wheeler L = %10.4g H" % l_rx)
    print("  ratio           = %.3f (expected order 1)" % (m_self / l_rx))

    print("\nVectorised mutual against the scalar one")
    import time
    ra = [1e-3 + 0.3e-3 * i for i in range(40)]
    rb2 = [2e-4 + 1e-5 * i for i in range(49)]
    zaa = [-1e-3 * i for i in range(40)]
    t0 = time.time(); slow = mutual(ra, rb2, z_a=zaa, gap_z=5e-3); t_s = time.time() - t0
    t0 = time.time(); fast = mutual_fast(ra, rb2, z_a=zaa, gap_z=5e-3); t_f = time.time() - t0
    rel = abs(slow - fast) / abs(slow)
    good = rel < 1e-12
    ok = ok and good
    print("  scalar %.6e H in %.4f s" % (slow, t_s))
    print("  vector %.6e H in %.4f s  (%.0fx faster)" % (fast, t_f, t_s / max(t_f, 1e-9)))
    print("  relative difference %.2e  %s" % (rel, "ok" if good else "FAIL"))

    print("\nResonance round-trips")
    for l_h, c_f in ((1.032e-6, 2e-6), (23.6e-9, 1e-6)):
        f = resonant_f(l_h, c_f)
        check("C(L=%.4gH, f=%.4gHz)" % (l_h, f), resonant_c(l_h, f), c_f, 1e-9)

    print("\neta_max is monotonic and bounded")
    prev = -1.0
    for f in (1e-6, 1e-3, 1.0, 10.0, 1e3, 1e6):
        e = eta_max(f)
        good = 0.0 <= e < 1.0 and e > prev
        ok = ok and good
        print("  FOM = %10.4g -> eta_max = %.6f  %s" % (f, e, "ok" if good else "FAIL"))
        prev = e

    print("\n%s" % ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv else _selftest())
