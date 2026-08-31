#!/usr/bin/env python3
"""Sizing search for the IGZO TFT amplifiers.

Coordinate descent on the 5 um grid (10 um floor), multi-start, with an outer
sweep over VDD.  Each evaluation is one ngspice batch run (~40 ms), so the
search is brute force on purpose: no gradient of a SPICE deck is needed.

    python3 optimize.py opam2
    python3 optimize.py opam
"""

import csv
import itertools
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tb_common as tb
import score

CORNERS = ("best", "tt", "all")
VDD_SWEEP = (5, 6, 7, 8)
OPAM_VDD_SWEEP = (8,)
FACTORS = (0.5, 0.7, 1.4, 2.0)
FINE = (0.85, 1.18)
W_MAX, L_MAX = 5000.0, 2000.0
V_STEP = 0.05          # grid for the bias / common-mode voltages
WORKERS = 12


def split(params):
    """Separate the micron-valued dimensions from the volt-valued biases."""
    um = {k: v for k, v in params.items() if not k.startswith("v")}
    volts = {k: v for k, v in params.items() if k.startswith("v")}
    return um, volts


class Design:
    def __init__(self, name, core, instance, nodes, diodes, seeds,
                 vcm_frac=0.4, cutoff=(), gain_key="av_db", trim=None,
                 coupled=(), swing_min=score.SWING_MIN, fixed=(),
                 stages=(), pm_min=0.0, follow_tol=0.0):
        self.name, self.core, self.instance = name, core, instance
        self.nodes, self.diodes, self.seeds = nodes, diodes, seeds
        self.vcm_frac, self.cutoff, self.gain_key = vcm_frac, cutoff, gain_key
        self.trim, self.coupled = trim, coupled
        self.swing_min, self.fixed = swing_min, fixed
        self.stages, self.pm_min = stages, pm_min
        self.follow_tol = follow_tol

    def evaluate(self, sizing, vdd, corners=CORNERS):
        """Score a candidate at its WORST corner.

        Scoring on `best` alone finds knife edges: a cross-coupled or
        near-cancelled load can show 70 dB there and go to pieces at `tt`,
        where Vto moves by 0.35 V.  The worst corner is the design.
        """
        um, volts = split(sizing)
        vcm = volts.pop("vcm", self.vcm_frac * vdd)
        worst = None
        for corner in corners:
            # An external bias pin is trimmed on the bench, so it follows the
            # corner.  Vto moves 0.62 V between `best` and `all`, and no fixed
            # bias voltage survives that - but the trim needed is exactly the
            # threshold shift, so apply it rather than searching for it.  The
            # sizing still has to work at all three.
            cand = dict(volts)
            if self.trim:
                cand[self.trim] = max(0.05, volts[self.trim]
                                      + tb.VTO[corner] - tb.VTO["best"])
            res = tb.run(tb.build_netlist(self.core, self.instance, self.nodes,
                                          um, vdd, vcm, corner, cand))
            out = score.objective(res, vdd, tb.VTO[corner], self.diodes,
                                  self.cutoff, self.gain_key,
                                  self.swing_min, self.pm_min, vcm,
                                  self.follow_tol) + (res,)
            if worst is None or out[0] < worst[0]:
                worst = out
        return worst


def clamp(key, value, vdd):
    if key.startswith("v"):
        return min(vdd, max(V_STEP, round(value / V_STEP) * V_STEP))
    hi = W_MAX if key.startswith("w") else L_MAX
    return min(hi, score.snap(value))


def coordinate_descent(design, sizing, vdd, log, pool, max_rounds=40,
                       factors=FACTORS):
    """Steepest-descent over single-dimension moves.

    Every candidate move of the current point is simulated in parallel and the
    best improving one is taken.  ngspice runs as a subprocess, so threads are
    enough to use every core.
    """
    best = dict(sizing)
    best_val, best_bad, best_info, _ = design.evaluate(best, vdd)
    log.append((vdd, best_val, best_info.get("av_db"), dict(best)))

    for _ in range(max_rounds):
        trials = []
        for key in sorted(best):
            if key in design.fixed:
                continue
            # dimensions move by factors, bias voltages by grid steps
            moves = ([best[key] + n * V_STEP for n in (-4, -1, 1, 4)]
                     if key.startswith("v")
                     else [best[key] * f for f in factors])
            for value in moves:
                trial = dict(best)
                trial[key] = clamp(key, value, vdd)
                if trial[key] != best[key]:
                    trials.append(trial)
        # Coupled moves.  Single-coordinate descent cannot lower BIAS, because
        # on its own that starves both tails; it only pays off together with
        # the extra width that keeps the current up.  Offer the pair directly.
        for group in design.coupled:
            for f in factors:
                for dv in (-2 * V_STEP, -V_STEP, V_STEP, 2 * V_STEP):
                    trial = dict(best)
                    for key in group:
                        trial[key] = clamp(key, best[key] * f, vdd)
                    if design.trim and design.trim in trial:
                        trial[design.trim] = clamp(design.trim,
                                                   best[design.trim] + dv, vdd)
                    if trial != best:
                        trials.append(trial)
        if not trials:
            break
        outcomes = list(pool.map(lambda t: design.evaluate(t, vdd), trials))
        for trial, (val, bad, info, _) in zip(trials, outcomes):
            log.append((vdd, val, info.get("av_db"), dict(trial)))
        val, bad, info, _ = max(outcomes, key=lambda o: o[0])
        if val <= best_val + 1e-4:
            break
        best = trials[outcomes.index(max(outcomes, key=lambda o: o[0]))]
        best_val, best_bad, best_info = val, bad, info
    return best, best_val, best_bad, best_info


def search(design, out_csv):
    log, results = [], []
    pool = ThreadPoolExecutor(WORKERS)
    sweep = OPAM_VDD_SWEEP if design.name == "opam" else VDD_SWEEP
    for vdd, seed in itertools.product(sweep, design.seeds):
        sizing, val, bad, info = coordinate_descent(design, seed, vdd, log, pool)
        # second pass with smaller steps, to settle where the coarse grid overshot
        sizing, val, bad, info = coordinate_descent(design, sizing, vdd, log,
                                                    pool, factors=FINE)
        results.append((val, vdd, sizing, bad, info))
        print("VDD=%d  score=%8.3f  Av=%7.2f dB  viol=%d  %s"
              % (vdd, val, info.get("av_db", float("nan")), len(bad),
                 "OK" if not bad else bad[0]))
        sys.stdout.flush()

    with open(out_csv, "w", newline="") as fh:
        keys = sorted(design.seeds[0])
        w = csv.writer(fh)
        w.writerow(["vdd", "score", "av_db"] + keys)
        for vdd, val, av, sz in log:
            w.writerow([vdd, "%.4f" % val, "" if av is None else "%.4f" % av]
                       + ["%.6g" % sz[k] for k in keys])

    results.sort(key=lambda r: -r[0])
    return results


# ---------------------------------------------------------------- OPAM2 ----
OPAM2 = Design(
    name="opam2",
    core="opam2_core.spice",
    instance="x1 VDD INP OUT INN 0 OPAM2",
    nodes=["OUT", "x1.net1", "x1.net2", "x1.net3", "x1.net4", "x1.net5", "x1.net6"],
    diodes=("xm6", "xm7", "xm2", "xm17", "xm13"),
    seeds=[
        # hand-computed start: low-Vov input pair, weak diode loads
        dict(w_in=1550, l_in=10, w_dl=100, l_dl=110, w_tail=1120, l_tail=10,
             w_cms=100, l_cms=100, w_cmd=1120, l_cmd=10, w_sf=170, l_sf=10,
             w_sfl=100, l_sfl=60, w_d2s=100, l_d2s=60, w_od=100, l_od=60,
             w_ol=100, l_ol=110),
        # the schematic as it stands, for reference
        dict(w_in=1000, l_in=10, w_dl=100, l_dl=100, w_tail=1000, l_tail=10,
             w_cms=1000, l_cms=10, w_cmd=1000, l_cmd=10, w_sf=1000, l_sf=100,
             w_sfl=1000, l_sfl=10, w_d2s=100, l_d2s=100, w_od=100, l_od=100,
             w_ol=1000, l_ol=100),
        # everything square, a neutral start
        dict.fromkeys(
            ["w_in", "l_in", "w_dl", "l_dl", "w_tail", "l_tail", "w_cms",
             "l_cms", "w_cmd", "l_cmd", "w_sf", "l_sf", "w_sfl", "l_sfl",
             "w_d2s", "l_d2s", "w_od", "l_od", "w_ol", "l_ol"], 200),
    ],
)

# ----------------------------------------------------------------- OPAM ----
# Hand-computed start for VDD = 8 V, corner `best`.  The binding condition of
# this topology is gm(cross-coupled) < gm(diode load): the cross-coupled pair
# subtracts from the load conductance, and if it wins the stage latches
# instead of amplifying.  With Vcm = 3.0 V the tail sits at 2.5 V, the drains
# at 4.0 V, and (W/L)_cc = 3 against (W/L)_dl = 1.4 leaves the load
# conductance positive but small - which is where the gain comes from.
_OPAM_SEED = dict(
    w_in=1000, l_in=10,      # input pair, Vov = 0.4 V
    w_cc=300, l_cc=100,      # cross-coupled pair, W/L = 3
    w_dl=140, l_dl=100,      # diode loads, W/L = 1.4
    w_tail=1210, l_tail=10,
    w_t2=780, l_t2=10,       # second-stage current sinks
    w_g2=330, l_g2=100,      # second-stage common source
    w_bl=240, l_bl=100,      # bootstrap load (diode at DC, current source in band)
    w_bf=240, l_bf=100,      # its cut-off partner: sets the parallel Cgs
    w_of=1000, l_of=10,      # output followers
    w_od=140, l_od=100,      # output diode loads
    c_boot=160.64, c_fb=160.64, vbias=0.70, vcm=3.0,
)

OPAM = Design(
    name="opam",
    core="opam_core.spice",
    instance="x1 VDD OUT INN INP BIAS 0 OPAM\nVB BIAS 0 DC 'vbias'",
    nodes=["OUT"] + ["x1.net%d" % i for i in (1, 2, 3, 4, 7, 8)]
          + ["x1.BOOT_L", "x1.BOOT_R"],
    # Devices that sit at the saturation edge by construction, so the
    # vds >= vov test does not apply to them:
    #   XM6/XM7/XM9/XM15 - diode-connected loads
    #   XM13/XM19        - gate on VDD, which is also their drain: diode
    #                      connected at DC, current sources in band via C1/C2
    #   XM3/XM4          - cross-coupled: gate on one drain, channel to the
    #                      other, and the two drains sit at the same DC level,
    #                      so vds and vgs are equal
    #   XM11/XM17       - these sit between the second stage's amplifying
    #                      device and VSS, i.e. in its SOURCE.  Held in
    #                      saturation they are a current source in the source
    #                      of a common-source stage, which degenerates gm by
    #                      gm*(1/gds) - about 1600x here - and the stage gives
    #                      no gain at all.  In this topology they are
    #                      degeneration resistors and belong in triode; only
    #                      the model-range limits apply to them.
    diodes=("xm6", "xm7", "xm9", "xm15", "xm13", "xm19", "xm3", "xm4",
            "xm11", "xm17"),
    cutoff=("xm14", "xm20"),
    # the bootstrap load only becomes a current source above the corner set by
    # C1/C2, so the figure of merit for this topology is the mid-band gain
    gain_key="av_max",
    trim="vbias",
    coupled=(("w_tail", "w_t2"),),
    # The bootstrap load is diode-connected at DC and only becomes a current
    # source above the corner set by C1/C2, so this amplifier has almost no DC
    # gain by design and a DC sweep cannot show its swing.  Drop the DC swing
    # constraint here and measure the swing in transient on the final design.
    swing_min=0,
    # C1/C2 and C3/C4 set where the bootstrap starts working, not how much gain
    # it gives, and left free the search simply grows them: it drove C1/C2 to
    # 2000 um a side - a 4 mm2 plate holding 6 nF - to push the corner below
    # the measurement band.  Keep them at the drawn 160.64 um and make the
    # transistors earn the gain.
    fixed=("c_boot", "c_fb", "l_bf"),
    # net3 is the first stage's output, net9 the second stage's, OUT the
    # buffer's - so the three can be compared with the paper stage by stage.
    # net3 is the first stage output, net7 the second stage output
    stages=(("st_stage1", "x1.net3"), ("st_stage2", "x1.net7")),
    # An amplifier with no phase margin is a gain block, not an opamp: 45 deg
    # is the least that survives closing the loop, and the search has to pay
    # for it out of gain rather than pretend it is free.
    pm_min=45.0,
    # And a margin is not enough on its own.  The output has to be able to sit
    # where the common mode is, or a unity-gain buffer has nowhere to settle:
    # the first stable sizing had its output range at 2.7-6.6 V and its common
    # mode at 1.8 V, and the loop latched at every corner but one.
    follow_tol=0.4,
    seeds=[
        # only the starts that already reach a valid operating point; the
        # others were tried and never got there.
        _OPAM_SEED,
        # Low-overdrive tails.  The stack VSS-XM17-XM18-XM19-VDD is three
        # devices deep, and what kept failing was the tail sitting in triode:
        # give it Vov = 0.35 V (BIAS = 0.44 V) and the width to still carry
        # the current, and the stack fits.
        dict(_OPAM_SEED, w_tail=3640, l_tail=10, w_t2=2280, l_t2=10,
             w_g2=270, l_g2=100, w_bl=250, l_bl=100, w_bf=250, l_bf=100,
             w_of=1070, l_of=10, w_od=180, l_od=100, vbias=0.45, vcm=3.0),
        # a more cautious cross-coupling (less cancellation, more margin)
        dict(_OPAM_SEED, w_cc=150, l_cc=100, w_dl=200, l_dl=100),
        # and a more aggressive one
        dict(_OPAM_SEED, w_cc=500, l_cc=100, w_dl=120, l_dl=100),
        # neutral start: everything square.  This is the seed that won for
        # OPAM2, so it is worth giving the search a foothold outside the
        # hand-computed region.
        dict({k: 200 for k in _OPAM_SEED if not k.startswith("v")},
             vbias=1.0, vcm=2.0),
    ],
)

# ---------------------------------------------------- OPAM, self-biased ----
# Same amplifier with the bias reference on the chip and no BIAS pin.  Nothing
# is trimmed per corner here - that is the whole point, so `trim` is absent and
# the sizing has to absorb the 0.62 V of Vto spread by itself.
_BIASED_SEED = dict(w_b1=60, l_b1=1000, w_b2=200, l_b2=100)

OPAM_BIASED = Design(
    name="opam_biased",
    core="opam_biased_core.spice",
    instance="x1 VDD OUT INN INP 0 OPAM",
    nodes=["OUT", "x1.BIAS"] + ["x1.net%d" % i for i in (1, 2, 3, 4, 7, 8)]
          + ["x1.BOOT_L", "x1.BOOT_R"],
    diodes=OPAM.diodes + ("xmb0", "xmb1", "xmb2"),
    cutoff=OPAM.cutoff,
    gain_key="av_max",
    coupled=(("w_tail", "w_t2"), ("w_b1", "w_b2")),
    swing_min=0,
    fixed=OPAM.fixed,
    stages=OPAM.stages,
    pm_min=45.0,
    follow_tol=0.4,
    seeds=[],          # filled in by search_biased.py from the OPAM optimum
)

DESIGNS = {"opam2": OPAM2, "opam": OPAM, "opam_biased": OPAM_BIASED}

if __name__ == "__main__":
    d = DESIGNS[sys.argv[1] if len(sys.argv) > 1 else "opam2"]
    res = search(d, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "results_%s.csv" % d.name))
    val, vdd, sizing, bad, info = res[0]
    print("\n=== best: VDD=%d  Av=%.2f dB ===" % (vdd, info["av_db"]))
    for k in sorted(sizing):
        print("  %-8s %6.0f u" % (k, sizing[k]))
    print("  vout=%.2f swing=%.2f power=%.0f uW"
          % (info["vout"], info["swing"], info["power"] * 1e6))
    print("  violations:", bad or "none")
