#!/usr/bin/env python3
"""Give OPAM a phase margin.

As sized, OPAM has -36 degrees of phase margin: fine as an open-loop gain block,
which is what both papers characterise, but it would oscillate the moment the
loop was closed.  Zhao's title says "with phase compensation loop" for a reason.

The fix is textbook Miller compensation: a capacitor from the second stage's
output back to its input.  It splits the poles - the dominant one goes down, the
one behind it goes up - so the gain is below unity before the second pole has
finished turning the phase.  It costs bandwidth, and this reports how much.

The catch is the right-half-plane zero that the same capacitor creates by
feeding forward through it: it subtracts phase exactly where the margin is
needed.  The standard answer is a series resistor of about 1/gm, and here that
is a TFT held in triode, which is a device this process can actually build.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import optimize as O
import report as rep
import tb_common as tb
import validate

HERE = os.path.dirname(os.path.abspath(__file__))
CORNERS = ("best", "tt", "all")

PROBE = """* phase margin probe - see compensate.py
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
ac dec 40 0.1 1e7
let phase = 180/PI * cph(v(OUT))
meas ac av_max MAX vdb(OUT)
meas ac f3db   WHEN vdb(OUT)='av_max-3' FALL=1
meas ac funity WHEN vdb(OUT)=0 FALL=1
meas ac ph_dc  FIND phase AT=0.1
meas ac ph_u   FIND phase WHEN vdb(OUT)=0 FALL=1
let pm = 180 + (ph_u - ph_dc)
echo PMRESULT $&av_max $&f3db $&funity $&pm
.endc
.end
"""


def with_load_cap(base_core, out_name):
    """Plain capacitor from the second stage's output to ground.

    Dominant-pole compensation: it lowers the first pole and creates no zero at
    all, which matters here because gm is in microsiemens and the mim plates are
    in picofarads, so a Miller zero at gm/C lands right on the unity-gain
    frequency instead of far above it.
    """
    src = open(os.path.join(HERE, base_core)).read()
    branch = "XCL   net7    VSS     cap_mim W='c_load' L='c_load'\n"
    src = src.replace("\n.ends OPAM", "\n" + branch + "\n.ends OPAM")
    open(os.path.join(HERE, out_name), "w").write(src)
    return out_name


def with_miller(base_core, out_name, nulling=False):
    """Add the compensation branch to a copy of the core."""
    src = open(os.path.join(HERE, base_core)).read()
    if nulling:
        # cap in series with a TFT held in triode by its gate on VDD: the
        # nulling resistor, built from the only device this process has
        branch = ("XCC   net_c   net3    cap_mim W='c_mill' L='c_mill'\n"
                  "XMC   net7    VDD     net_c   igzo_tft W='w_null' L='l_null'"
                  " ov=5u nf=1 B='b_field' b_scale='b_gain'\n")
    else:
        branch = "XCC   net7    net3    cap_mim W='c_mill' L='c_mill'\n"
    src = src.replace("\n.ends OPAM", "\n" + branch + "\n.ends OPAM")
    open(os.path.join(HERE, out_name), "w").write(src)
    return out_name


def probe(core, design, sizing, vdd, vcm, corner, extra):
    volts = validate._volts_for(design, extra, corner)
    lines = "\n".join(".param {} = {:.6g}u".format(k, v)
                      for k, v in sorted(sizing.items()))
    ex = "\n".join(".param {} = {:.6g}".format(k, v)
                   for k, v in sorted((volts or {}).items()))
    deck = PROBE.format(pdk=tb.PDK, here=tb.HERE, core=core, corner=corner,
                        vdd=vdd, vcm=vcm, sizing=lines, extra=ex,
                        instance=design.instance)
    res = tb.run(deck)
    if not res:
        return None
    m = re.search(r"PMRESULT\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", res["raw"])
    if not m:
        return None
    return dict(zip(("av", "f3db", "funity", "pm"),
                    (float(x) for x in m.groups())))
