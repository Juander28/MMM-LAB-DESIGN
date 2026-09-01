#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A Bode plot built from TRANSIENT runs, read off the settled value on C3.

WHY NOT AN AC SWEEP.  ngspice's `ac` linearises every device around its
operating point, and the devices here are two diode-connected TFTs whose whole
job is to be non-linear.  An AC sweep of this circuit reports the small-signal
response of a rectifier that is not rectifying.  Running the transient at each
frequency and reading the DC that actually appears on the output capacitor
measures the circuit as built.  The two are plotted together, and where they
part company is the part an AC sweep cannot tell you.

THE SETTLING PROBLEM, WHICH IS THE HARD PART, AND WHY "JUST RUN LONGER" DOES
NOT WORK HERE.  The output filter is 10 uF into 10 k, so its time constant is
0.1 s.  The carrier at 500 kHz has a 2 us period.  Simulating the charge-up
honestly means about five time constants - a QUARTER OF A MILLION carrier
cycles, fifty million time steps, for ONE point of a twenty-three point sweep.
That is the arithmetic, and no amount of patience fixes it.

What rescues it is that the settled value does not depend on the output
capacitor at all.  It is set by charge balance: what the diodes deliver per
cycle equals what the load draws.  The capacitor sets the ripple and the
settling time and nothing else.  So each point is done in three stages:

  1. SEED - find the answer on a deliberately small capacitor, chosen so its
     time constant is about twenty carrier periods.  It settles in a few
     hundred cycles instead of a quarter million, and it converges to the same
     voltage.
  2. CONFIRM - run the REAL 10 uF capacitor, warm-started at that answer with
     `.ic v(out)=`.  If the seed was right the output does not move; the drift
     across the measurement window is the test, and it is measured, not
     assumed.
  3. EXTEND - if it does move, warm-start again from where it ended and double
     the run.  Stop when stable, or at BODE_MAX_CYCLES - and a point that hit
     the cap is REPORTED AS UNSETTLED, drawn with a hollow marker, never
     quietly passed off as converged.

Each row also carries `naive_cycles`: how many carrier cycles a cold run at
that frequency would have needed.  It is the number that says why stage 1
exists.

THE CIRCUIT IS HELD FIXED ACROSS THE SWEEP.  The transmit tuning capacitor is
the one that resonates the transmit loop at F_OP, and it stays there while the
frequency moves - because that is what a Bode plot is, the response of one
circuit.  `--retune` sweeps with the transmitter re-resonated at every point
instead, which is a different and also useful curve: the envelope of what the
link could do if it were re-tuned each time.  Both are plotted.
"""

import csv
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import params as P                                          # noqa: E402
import tb_wpt as T                                          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


SEED_TAU_CYCLES = 20.0      # the seed capacitor's time constant, in carrier
                            # periods: long enough to smooth, short enough to
                            # settle inside the run


def settled_point(d, f, vout0=0.0, retune=False, rload=None, cout=None, **kw):
    """One frequency: seed, confirm, extend if needed, then read v(C3).

    Returns the reading plus how much work it took, because "how many cycles
    did this need" is itself a result - it is the answer to the question that
    prompted this whole module.
    """
    rload = P.R_LOAD if rload is None else rload
    cout = P.C_OUT if cout is None else cout
    ctx = T.tx_resonant_c(d, f) if retune else (
        T.tx_resonant_c(d, P.F_OP) if P.TX_TUNE else T.SHORT_C)
    naive = 5.0 * rload * cout * f          # cycles a cold run would need

    # ---- stage 1: the seed, on a small capacitor -------------------------
    c_seed = max(min(SEED_TAU_CYCLES / (rload * f), cout), 1e-15)
    v, total = vout0, 0
    for _ in range(8):
        m, _ = T.transient(d, cycles_settle=int(6 * SEED_TAU_CYCLES),
                           cycles_meas=P.BODE_WINDOW_CYCLES, f=f, ctx=ctx,
                           rload=rload, cout=c_seed, vout0=v, **kw)
        total += int(6 * SEED_TAU_CYCLES) + P.BODE_WINDOW_CYCLES
        new = m.get("vout_avg", v)
        if abs(new - v) <= P.BODE_SETTLE_TOL * max(abs(new), 1e-15):
            v = new
            break
        v = new

    # ---- stages 2 and 3: confirm on the real capacitor, extend if needed --
    settle = P.BODE_WINDOW_CYCLES
    last = None
    while True:
        m, _ = T.transient(d, cycles_settle=settle,
                           cycles_meas=P.BODE_WINDOW_CYCLES,
                           f=f, ctx=ctx, rload=rload, cout=cout, vout0=v, **kw)
        total += settle + P.BODE_WINDOW_CYCLES
        if "vout_avg" not in m:
            return {"f_hz": f, "vout": float("nan"), "cycles": total,
                    "naive_cycles": naive, "c_seed": c_seed,
                    "drift": float("nan"), "settled": False,
                    "pin": float("nan"), "pout": float("nan"),
                    "eta": float("nan"), "ripple": float("nan"),
                    "why": "ngspice produced no measurement"}
        v = m["vout_avg"]
        drift = m.get("drift", float("inf"))
        # Two independent ways of being stable: the output is flat inside the
        # window, AND it agrees with the previous window.  A slow ramp can look
        # flat over twenty cycles, so the second test is the one that catches
        # it.
        between = (abs(v - last) / max(abs(v), 1e-15)) if last is not None \
            else float("inf")
        last = v
        # An absolute floor as well as a relative one.  A relative test on a
        # value that is numerical noise never converges: at the bottom of the
        # sweep the tuning capacitor is an open circuit, the output is a
        # fraction of a nanovolt, and the run walked to the cycle cap chasing
        # a moving last digit.  Below BODE_ABS_V the answer is zero.
        if abs(v) < P.BODE_ABS_V:
            return {"f_hz": f, "vout": v, "cycles": total, "drift": drift,
                    "naive_cycles": naive, "c_seed": c_seed,
                    "between": between, "settled": True,
                    "pin": m.get("pin_avg", float("nan")),
                    "pout": m.get("pout_avg", float("nan")),
                    "eta": m.get("eta", float("nan")),
                    "ripple": m.get("vout_max", 0.0) - m.get("vout_min", 0.0),
                    "why": "below the %g V floor - nothing is delivered here"
                           % P.BODE_ABS_V}
        if drift <= P.BODE_SETTLE_TOL and between <= P.BODE_SETTLE_TOL:
            return {"f_hz": f, "vout": v, "cycles": total, "drift": drift,
                    "naive_cycles": naive, "c_seed": c_seed,
                    "between": between, "settled": True,
                    "pin": m.get("pin_avg", float("nan")),
                    "pout": m.get("pout_avg", float("nan")),
                    "eta": m.get("eta", float("nan")),
                    "ripple": m.get("vout_max", 0.0) - m.get("vout_min", 0.0),
                    "why": "stable"}
        if total >= P.BODE_MAX_CYCLES:
            return {"f_hz": f, "vout": v, "cycles": total, "drift": drift,
                    "naive_cycles": naive, "c_seed": c_seed,
                    "between": between, "settled": False,
                    "pin": m.get("pin_avg", float("nan")),
                    "pout": m.get("pout_avg", float("nan")),
                    "eta": m.get("eta", float("nan")),
                    "ripple": m.get("vout_max", 0.0) - m.get("vout_min", 0.0),
                    "why": "hit BODE_MAX_CYCLES still moving"}
        settle *= 2


def sweep(d, retune=False, verbose=True):
    """Every frequency, warm-started from the previous one."""
    rows, v = [], 0.0
    freqs = P.bode_frequencies()
    if verbose:
        print("  %-11s %-13s %-9s %-11s %-11s %s"
              % ("f (kHz)", "V(C3) (V)", "cycles", "drift", "eta", "state"))
    for f in freqs:
        r = settled_point(d, f, vout0=v, retune=retune)
        if r["settled"]:
            v = r["vout"]           # warm start for the next frequency
        rows.append(r)
        if verbose:
            print("  %-11.1f %-13.6e %-9d %-11.2e %-11.3e %s"
                  % (f / 1e3, r["vout"], r["cycles"], r["drift"], r["eta"],
                     "stable" if r["settled"] else "NOT SETTLED: " + r["why"]))
    return rows


def ac_reference(d):
    """The AC sweep, for the overlay.  Same circuit, linearised."""
    tr = T.traces(d, rload=P.R_LOAD, vout0=0.0, cycles=2)
    if "error" in tr:
        return None
    return {"f": list(tr["f"]), "vrx_mag": list(tr["vrx_mag"])}


# --------------------------------------------------------------------------
# Self-test: does the settling detector actually detect settling?
# --------------------------------------------------------------------------

RC_TB = """* an RC whose settled value is known exactly
V1 in 0 DC {v}
R1 in out {r}
C1 out 0 {c}
.ic v(out)=0
.control
set filetype=ascii
tran {step} {stop}
meas tran vend FIND v(out) AT={t}
echo "@DONE"
.endc
.end
"""


def _selftest():
    """The detector, against a circuit whose answer is arithmetic.

    An RC charging towards V settles to exactly V, and reaches 1 - exp(-n) of
    it after n time constants.  So the test is: does the run report the value
    the algebra gives, and does it report NOT settled when stopped early?
    """
    ok = True
    v, r, c = 5.0, 1e3, 1e-9
    tau = r * c
    print("An RC with tau = %.3g s charging to %.1f V" % (tau, v))
    for n in (1, 3, 7, 15):
        nl = RC_TB.format(v=v, r=r, c=c, step=tau / 200, stop=n * tau * 1.02,
                          t=n * tau)
        m = T.measures(T.run(nl))
        want = v * (1.0 - math.exp(-n))
        got = m.get("vend", float("nan"))
        good = abs(got - want) / want < 5e-3
        ok = ok and good
        print("  after %2d tau: %.6f V, algebra says %.6f  %s"
              % (n, got, want, "ok" if good else "FAIL"))

    print("\nThe drift test on the link itself: an early read must be rejected")
    d = T.load_design()
    m_early, _ = T.transient(d, cycles_settle=2, cycles_meas=5, vout0=0.0)
    m_late, _ = T.transient(d, cycles_settle=2, cycles_meas=5,
                            vout0=m_early.get("vout_avg", 0.0))
    early_drift = m_early.get("drift", float("inf"))
    print("  cold start, 2 cycles of settling: drift = %.3e  -> %s"
          % (early_drift,
             "rejected" if early_drift > P.BODE_SETTLE_TOL else "ACCEPTED"))
    good = early_drift > P.BODE_SETTLE_TOL
    ok = ok and good
    if not good:
        print("  FAIL: a two-cycle cold start should not pass as settled")

    print("\nA converged point must not move when given 50 percent more time")
    pt = settled_point(d, P.F_OP, vout0=0.0)
    print("  converged: %.6e V in %d cycles" % (pt["vout"], pt["cycles"]))
    m, _ = T.transient(d, cycles_settle=int(pt["cycles"] * 1.5),
                       cycles_meas=P.BODE_WINDOW_CYCLES, vout0=pt["vout"])
    moved = abs(m["vout_avg"] - pt["vout"]) / max(abs(pt["vout"]), 1e-15)
    good = moved <= 10 * P.BODE_SETTLE_TOL
    ok = ok and good
    print("  with 50 %% more: %.6e V, moved %.2e  %s"
          % (m["vout_avg"], moved, "ok" if good else "FAIL"))

    print("\n%s" % ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    return 0 if ok else 1


def main():
    d = T.load_design()
    print("Bode by transient - the settled value on C3 at each frequency.")
    print("  link      f_op = %.0f kHz, k = %.4e, z = %g mm"
          % (P.F_OP / 1e3, d["k"], P.Z_MM))
    print("  TFTs      W = %.0f um, L = %.0f um, ov = %.0f um"
          % (P.TFT_W * 1e6, P.TFT_L * 1e6, P.TFT_OV * 1e6))
    print("  drive     %.0f W, %.1f V amplitude" % (P.P_IN_W,
                                                    P.vamp_for_power()))
    print("  C3        %g uF into %g ohm - tau = %.3g s against a %.3g s "
          "period at f_op" % (P.C_OUT * 1e6, P.R_LOAD, P.C_OUT * P.R_LOAD,
                              1.0 / P.F_OP))
    print("  settle to %g relative, giving up at %d cycles\n"
          % (P.BODE_SETTLE_TOL, P.BODE_MAX_CYCLES))

    print("=== transmitter tuned once, at %.0f kHz (this is the Bode plot) ==="
          % (P.F_OP / 1e3))
    fixed = sweep(d, retune=False)

    print("\n=== transmitter re-tuned at every point (the envelope) ===")
    tuned = sweep(d, retune=True)

    ac = ac_reference(d)
    vamp = P.vamp_for_power()
    for rows in (fixed, tuned):
        for r in rows:
            r["db"] = (20.0 * math.log10(abs(r["vout"]) / vamp)
                       if r["vout"] and abs(r["vout"]) > 0 else float("-inf"))

    peak = max((r for r in fixed if r["settled"]), key=lambda r: r["vout"])
    unsettled = [r for r in fixed + tuned if not r["settled"]]
    print("\n=== what the sweep says ===")
    print("  peak of the fixed-tuning curve: %.6f V at %.1f kHz"
          % (peak["vout"], peak["f_hz"] / 1e3))
    print("  worst cycle count: %d, at %.1f kHz"
          % (max(r["cycles"] for r in fixed),
             max(fixed, key=lambda r: r["cycles"])["f_hz"] / 1e3))
    if unsettled:
        print("  %d point(s) did NOT settle and are marked as such:"
              % len(unsettled))
        for r in unsettled:
            print("    %.1f kHz - %s" % (r["f_hz"] / 1e3, r["why"]))
    else:
        print("  every point settled")

    out = {"params": {"f_op": P.F_OP, "z_mm": P.Z_MM, "k": d["k"],
                      "tft_w": P.TFT_W, "tft_l": P.TFT_L, "tft_ov": P.TFT_OV,
                      "c_out": P.C_OUT, "r_load": P.R_LOAD,
                      "p_in": P.P_IN_W, "vamp": vamp,
                      "settle_tol": P.BODE_SETTLE_TOL,
                      "max_cycles": P.BODE_MAX_CYCLES},
           "fixed": fixed, "retuned": tuned, "ac": ac, "peak": peak}
    with open(os.path.join(HERE, "bode_tran.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=float)
    with open(os.path.join(HERE, "bode_tran.csv"), "w", newline="") as fh:
        keys = ["f_hz", "vout", "db", "cycles", "drift", "settled", "pin",
                "pout", "eta", "ripple", "why"]
        w = csv.DictWriter(fh, fieldnames=["tuning"] + keys)
        w.writeheader()
        for tag, rows in (("fixed", fixed), ("retuned", tuned)):
            for r in rows:
                w.writerow(dict({"tuning": tag},
                                **{k: r.get(k) for k in keys}))
    print("\nwrote bode_tran.json and bode_tran.csv")
    return 0


if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv else main())
