#!/usr/bin/env python3
"""What a magnetic field does to these amplifiers, and what it would take.

The PDK models classical magnetoresistance: the wrapper divides the intrinsic
width by 1 + (mu*b_scale*B)^2.  Because level 1 only ever uses the product
Kp*W/L, that is the same as dividing Kp, which is the same as dividing the
mobility - so Kn and channel resistance move together, as one fact.

Two sweeps, because one says nothing on its own:

  * B at b_gain = 1 - the classical effect.  At the measured mobility this is
    (mu*B)^2 = 2e-7 per tesla and the answer is that nothing happens.  That is
    the result, not a failure to find one.
  * b_gain at fixed B - how far a measured effect would have to sit from
    classical before the amplifier noticed.  This is the useful form: it tells
    the laboratory what sensitivity it would have to see.

Run per corner, because the effect goes as mu^2 and mu changes by a factor of
5.6 across the corners - so the sensitivity changes by 31x.

    python3 bfield.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import optimize as O
import report
import tb_common as tb
import validate

CORNERS = ("best", "tt", "all")
MU = {"best": 4.584e-4, "tt": 3.593e-4, "short": 8.184e-5, "all": 2.436e-4}

FIELDS = (0.0, 0.05, 0.5, 1.0, 5.0)
GAINS = (1.0, 1e2, 278.0, 1e3, 1e4)


def measure(design, sizing, vdd, vcm, corner, extra, b_field, b_gain):
    volts = dict(validate._volts_for(design, extra, corner),
                 b_field=b_field, b_gain=b_gain)
    res = tb.run(tb.build_netlist(design.core, design.instance, design.nodes,
                                  sizing, vdd, vcm, corner, volts,
                                  getattr(design, "stages", ())))
    if not res:
        return None
    m = res["meas"]
    return {"av": m.get(design.gain_key, float("nan")),
            "f3db": m.get("f3db", float("nan")),
            "funity": m.get("funity", float("nan")),
            "vout": res["nodes"].get("out", float("nan")),
            "idd": res["idd"]}


def sweep(name, design, sizing, vdd, vcm, extra):
    print("=== %s ===" % name.upper())
    for corner in CORNERS:
        base = measure(design, sizing, vdd, vcm, corner, extra, 0.0, 1.0)
        if base is None:
            print("  %-5s no operating point" % corner)
            continue
        print("  corner %s   (mu = %.3e m2/Vs, classical (mu*B)^2 at 1 T = %.2e)"
              % (corner, MU[corner], MU[corner] ** 2))

        print("    B sweep at b_gain = 1 (classical):")
        for b in FIELDS:
            r = measure(design, sizing, vdd, vcm, corner, extra, b, 1.0)
            # the analytical shift is exact; the simulated one is below the
            # resolution of any measurement here, which is the whole point
            print("      B = %5.2f T   W/mr %+.3e %%   dAv = %+.3e dB   "
                  "dIdd = %+.3e %%"
                  % (b, -100.0 * (1 - 1 / (1 + (MU[corner] * b) ** 2)),
                     r["av"] - base["av"],
                     100.0 * (r["idd"] / base["idd"] - 1)))

        print("    b_gain sweep at B = 1 T (a measured effect, n times classical):")
        for g in GAINS:
            r = measure(design, sizing, vdd, vcm, corner, extra, 1.0, g)
            mr = 1.0 + (MU[corner] * g) ** 2
            print("      b_gain = %8.0f  ->  W/mr %+6.2f %%   dAv = %+7.3f dB"
                  "   df3dB = %+7.2f %%   dIdd = %+6.2f %%   dVout = %+7.4f V"
                  % (g, -100.0 * (1 - 1 / mr), r["av"] - base["av"],
                     100.0 * (r["f3db"] / base["f3db"] - 1),
                     100.0 * (r["idd"] / base["idd"] - 1),
                     r["vout"] - base["vout"]))
        print()


if __name__ == "__main__":
    vdd2, sz2, _ = report.FINAL["opam2"]
    sweep("opam2", O.OPAM2, sz2, vdd2, O.OPAM2.vcm_frac * vdd2, None)

    vdd, sz, extra, vcm = report.load_opam()
    sweep("opam", O.OPAM, sz, vdd, vcm, extra)


SENSE_TB = """* gain at fixed frequencies, under field - see bfield.py
.include {pdk}/design.ngspice
.lib {pdk}/igzo_mmm_lab.ngspice {corner}
.include "{here}/{core}"
.param vdd = {vdd}
.param vcm = {vcm}
{extra}
{sizing}
VDD VDD 0 DC 'vdd'
VCM cm  0 DC 'vcm'
VD  d   0 DC 0 AC 1
EIP INP cm d 0 0.5
EIN INN cm d 0 -0.5
{instance}
.control
ac dec 20 0.1 1e6
meas ac av_max MAX vdb(OUT)
meas ac f3db   WHEN vdb(OUT)='av_max-3' FALL=1
echo CORNER $&f3db
ac lin 1 {f_edge} {f_edge}
let a_edge = vdb(OUT)
echo EDGE $&a_edge
ac lin 1 {f_flat} {f_flat}
let a_flat = vdb(OUT)
echo FLAT $&a_flat
.endc
.end
"""


def gain_at(design, sizing, vdd, vcm, corner, extra, b_field, b_gain,
            f_edge, f_flat):
    """Gain at two FIXED frequencies, plus wherever the corner has moved to.

    The frequencies do not follow the corner.  That is the whole point: the
    probe tone stays put and the response slides out from under it.
    """
    import re
    volts = dict(validate._volts_for(design, extra, corner),
                 b_field=b_field, b_gain=b_gain)
    lines = "\n".join(".param {} = {:.6g}u".format(k, v)
                       for k, v in sorted(sizing.items()))
    ex = "\n".join(".param {} = {:.6g}".format(k, v) for k, v in sorted(volts.items()))
    deck = SENSE_TB.format(pdk=tb.PDK, here=tb.HERE, core=design.core,
                           corner=corner, vdd=vdd, vcm=vcm, sizing=lines,
                           extra=ex, instance=design.instance,
                           f_edge=f_edge, f_flat=f_flat)
    res = tb.run(deck)
    if not res:
        return None
    got = {}
    for tag, key in (("CORNER", "f3db"), ("EDGE", "edge"), ("FLAT", "flat")):
        m = re.search(tag + r"\s+(\S+)", res["raw"])
        if not m:
            return None
        got[key] = float(m.group(1))
    return got


def sensitivity(name, design, sizing, vdd, vcm, extra, corner="best"):
    """Put the probe tone on the -3 dB corner and let the field move the corner.

    In the flat band the gain barely moves: it is set by ratios of identical
    devices, and a mobility change scales all of them together.  The CORNER is
    a different matter - it is set by g/C at the dominant node, and g follows
    the mobility while C does not.  So the response slides sideways, and a tone
    parked on the edge of it reads that slide as an amplitude change.

    Both tones are held fixed at their B = 0 values; only the circuit moves.
    """
    print("=== %s: a tone parked on the corner, %s corner ===" % (name.upper(), corner))
    probe = gain_at(design, sizing, vdd, vcm, corner, extra, 0.0, 1.0, 1.0, 1.0)
    if probe is None:
        print("  no result\n")
        return []
    f_edge = probe["f3db"]
    f_flat = f_edge / 10.0
    base = gain_at(design, sizing, vdd, vcm, corner, extra, 0.0, 1.0,
                   f_edge, f_flat)
    print("  probe tones: %.2f Hz (on the corner) and %.2f Hz (flat band)"
          % (f_edge, f_flat))
    print("  at B = 0: flat %.2f dB, corner %.2f dB" % (base["flat"], base["edge"]))
    print("  %-9s %-8s %-9s %-11s %-11s %s"
          % ("b_gain", "dmu/mu", "f-3dB", "d(flat)", "d(tone)", "gain over flat"))
    rows = []
    for g in (1.0, 100.0, 278.0, 1e3, 3e3, 1e4):
        r = gain_at(design, sizing, vdd, vcm, corner, extra, 1.0, g,
                    f_edge, f_flat)
        if r is None:
            continue
        dmu = 1.0 - 1.0 / (1.0 + (MU[corner] * g) ** 2)
        d_flat = r["flat"] - base["flat"]
        d_edge = r["edge"] - base["edge"]
        ratio = (d_edge / d_flat) if abs(d_flat) > 1e-6 else float("nan")
        print("  %-9.0f %-8.4f %-9.1f %-+11.4f %-+11.4f %.1fx"
              % (g, dmu, r["f3db"], d_flat, d_edge, ratio))
        rows.append({"b_gain": g, "dmu": dmu, "f3db": r["f3db"],
                     "d_flat": d_flat, "d_edge": d_edge})
    print()
    return rows


def best_probe(name, design, sizing, vdd, vcm, extra, corner="best",
               b_gain=278.0):
    """Where on the response should the probe tone sit?

    A mobility change slides the response sideways.  How much amplitude that
    produces depends on how steep the curve is where the tone sits: flat band,
    nothing; on the corner, the first bit of slope; further down the skirt, the
    full roll-off - which for a multi-stage amplifier is steeper than
    20 dB/decade.  So sweep the probe frequency and report the sensitivity as
    dB of output per unit of relative mobility change.

    b_gain = 278 puts (mu*b_scale*B)^2 at about 1 % at one tesla, which keeps
    the measurement in the small-signal regime where a sensitivity means
    something.
    """
    probe = gain_at(design, sizing, vdd, vcm, corner, extra, 0.0, 1.0, 1.0, 1.0)
    if probe is None:
        print("  no result\n")
        return []
    f3 = probe["f3db"]
    dmu = 1.0 - 1.0 / (1.0 + (MU[corner] * b_gain) ** 2)
    print("=== %s: where to put the probe tone (%s corner, f-3dB = %.2f Hz) ==="
          % (name.upper(), corner, f3))
    print("  relative mobility change under test: %.4f" % dmu)
    print("  %-12s %-10s %-12s %s" % ("tone", "f (Hz)", "dGain (dB)",
                                      "sensitivity (dB per unit dmu/mu)"))
    rows = []
    for mult, tag in ((0.1, "flat band"), (1.0, "corner"), (3.0, "3x corner"),
                      (10.0, "10x corner"), (30.0, "30x corner")):
        f = f3 * mult
        b0 = gain_at(design, sizing, vdd, vcm, corner, extra, 0.0, 1.0, f, f)
        b1 = gain_at(design, sizing, vdd, vcm, corner, extra, 1.0, b_gain, f, f)
        if not (b0 and b1):
            continue
        d = b1["edge"] - b0["edge"]
        print("  %-12s %-10.2f %-+12.5f %.2f" % (tag, f, d, d / dmu))
        rows.append({"tag": tag, "f": f, "dgain": d, "sens": d / dmu})
    print()
    return rows


def gain_vs_field(name, design, sizing, vdd, vcm, extra, corner="best",
                  mults=(0.1, 1.0, 3.0, 10.0, 30.0)):
    """Gain against field, one curve per probe frequency.

    The frequencies are fixed multiples of the zero-field corner and stay put
    while the field moves the circuit underneath them.  That is the whole
    experiment: in the flat band the curves are almost horizontal, and the
    further down the roll-off the tone sits, the more the same mobility change
    shows up as amplitude.
    """
    probe = gain_at(design, sizing, vdd, vcm, corner, extra, 0.0, 1.0, 1.0, 1.0)
    if probe is None:
        return {}
    f3 = probe["f3db"]
    gains = (1.0, 100.0, 300.0, 600.0, 1000.0, 2000.0, 3000.0, 6000.0, 1e4)
    out = {}
    for mult in mults:
        f = f3 * mult
        base = gain_at(design, sizing, vdd, vcm, corner, extra, 0.0, 1.0, f, f)
        pts = []
        for g in gains:
            r = gain_at(design, sizing, vdd, vcm, corner, extra, 1.0, g, f, f)
            if not r:
                continue
            dmu = 1.0 - 1.0 / (1.0 + (MU[corner] * g) ** 2)
            pts.append({"dmu": dmu, "gain": r["edge"],
                        "dgain": r["edge"] - base["edge"]})
        label = ("%.2g x f-3dB" % mult) if mult != 1.0 else "f-3dB"
        out[label] = {"f": f, "points": pts}
    return out
