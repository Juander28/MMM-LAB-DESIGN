#!/usr/bin/env python3
"""Replace the external BIAS pin with a transistor reference on the chip.

BIAS has to be re-trimmed per corner today - 1.25 / 0.90 / 0.63 V - because
what the tail device M8 actually needs is a fixed OVERDRIVE, and Vto moves
0.62 V from `best` to `all`.  A diode-connected divider does that tracking by
itself: the tap sits one gate-source drop above VSS, and a gate-source drop is
Vth + Vov.

Two devices from VDD to VSS, both diode-connected:

    VDD --| MB1 (weak, W/L = r * bottom) |-- BIAS --| MB2 |-- VSS

Equating the two currents gives

    BIAS = Vth + sqrt(r)/(1+sqrt(r)) * (VDD - 2*Vth)

so d(BIAS)/d(Vth) = (1 - sqrt(r)) / (1 + sqrt(r)): a weak top device tracks
Vth almost one for one, a strong one does not track at all.  Perfect tracking
would need the reference current to scale with Kp, which no two-device divider
can do, so this sweeps r and keeps whatever actually holds the amplifier
together at all three corners.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import optimize as O
import report
import score
import tb_common as tb

CORNERS = ("best", "tt", "all")
HERE = os.path.dirname(os.path.abspath(__file__))
CORE = "opam_biased_core.spice"          # build_netlist resolves it against HERE


REF = """
* --- on-chip bias reference: BIAS is generated here, not brought in on a pin -
* Three diode-connected devices from VDD to VSS.  The tap sits two gate-source
* drops above VSS, and a gate-source drop is Vth + Vov, so BIAS follows Vth on
* its own - which is exactly the per-corner trim that used to be applied by
* hand.  The top of the chain is split in two so no device sees more than
* about half the supply across its gate: a single top device would sit at
* Vgs = 6.7 V, outside the range the models are validated for.
XMB1  net_b1  net_b1  BIAS    igzo_tft W='w_b1' L='l_b1' ov=5u nf=1 B='b_field' b_scale='b_gain'
XMB0  VDD     VDD     net_b1  igzo_tft W='w_b1' L='l_b1' ov=5u nf=1 B='b_field' b_scale='b_gain'
XMB2  BIAS    BIAS    VSS     igzo_tft W='w_b2' L='l_b2' ov=5u nf=1 B='b_field' b_scale='b_gain'
"""


def write_core():
    """opam_core.spice with the reference branch added and BIAS made internal."""
    src = open(os.path.join(HERE, "opam_core.spice")).read()
    src = src.replace(".subckt OPAM VDD OUT INN INP BIAS VSS",
                      ".subckt OPAM VDD OUT INN INP VSS")
    src = src.replace("\n.ends OPAM", "\n" + REF + "\n.ends OPAM")
    open(os.path.join(HERE, CORE), "w").write(src)


def evaluate(sizing, vdd, vcm, w_top, l_top, w_bot, l_bot):
    """Worst corner, with no bias trim anywhere - that is the whole point."""
    write_core(w_top, l_top, w_bot, l_bot)
    worst, rows = None, []
    for corner in CORNERS:
        res = tb.run(tb.build_netlist(
            CORE, "x1 VDD OUT INN INP 0 OPAM",
            ["OUT", "x1.BIAS", "x1.net1", "x1.net3", "x1.net7"],
            sizing, vdd, vcm, corner, None,
            (("st_stage1", "x1.net3"), ("st_stage2", "x1.net7"))))
        val, bad, info = score.objective(res, vdd, tb.VTO[corner], O.OPAM.diodes,
                                         O.OPAM.cutoff, O.OPAM.gain_key,
                                         O.OPAM.swing_min)
        bias = res["nodes"].get("x1.bias", float("nan")) if res else float("nan")
        rows.append((corner, bias, info.get("av_db", float("nan")),
                     info.get("power", float("nan")), bad))
        if worst is None or val < worst:
            worst = val
    return worst, rows


if __name__ == "__main__":
    vdd, sizing, extra, vcm = report.load_opam()
    print("target: BIAS = 1.25 / 0.90 / 0.63 V at best / tt / all")
    print("        (Vto = +0.09 / -0.26 / -0.53 V, so it must follow Vto 1:1)\n")

    # bottom device: Vov = 1.16 V at 1 uA in the best corner -> W/L about 2
    w_bot, l_bot = 200.0, 100.0
    best = None
    for r in (0.01, 0.02, 0.03, 0.05, 0.08, 0.15, 0.3):
        w_top, l_top = 60.0, round(60.0 / (r * w_bot / l_bot) / 5) * 5
        val, rows = evaluate(sizing, vdd, vcm, w_top, l_top, w_bot, l_bot)
        track = (1 - math.sqrt(r)) / (1 + math.sqrt(r))
        print("r = %5.3f  (top %gu/%gu, dBIAS/dVth = %.2f)" % (r, w_top, l_top, track))
        for corner, bias, av, pw, bad in rows:
            print("    %-5s BIAS = %5.3f V   Av = %6.2f dB   P = %5.0f uW  %s"
                  % (corner, bias, av, pw * 1e6,
                     "OK" if not bad else bad[0]))
        if best is None or val > best[0]:
            best = (val, r, w_top, l_top)
        print()
    print("best worst-corner score: r = %.3f (top %gu/%gu)" % best[1:])
