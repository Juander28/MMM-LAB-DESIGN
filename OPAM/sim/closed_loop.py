#!/usr/bin/env python3
"""Close the loop and look at a step.  This is the proof, not the phase margin.

A phase margin is a small-signal number read off an open-loop sweep.  What it
predicts is whether the amplifier rings or oscillates when the loop is closed,
so the honest check is to close it: wire OUT back to INN, step INP, and watch.

Overshoot maps onto margin the usual way - about 16 % at 60 degrees, 25 % at 45,
and anything that does not settle has none.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tb_common as tb
import validate

BUFFER = """* unity-gain buffer step response - see closed_loop.py
.include {pdk}/design.ngspice
.lib {pdk}/igzo_mmm_lab.ngspice {corner}
.include "{here}/{core}"
.param vdd = {vdd}
.param vcm = {vcm}
{extra}
{sizing}
VDD VDD 0 DC 'vdd'
* a step of {step} V on top of the common mode, slow enough not to slew-limit
VIN INN 0 PWL(0 'vcm' {t0} 'vcm' {t1} 'vcm+{step}' {tend} 'vcm+{step}')
* the loop: output straight back to the INVERTING input, which for OPAM is INP -
* its DC transfer has a negative slope against (INP - INN), so INP is the one
* that inverts.  Feeding back to INN instead gives positive feedback and the
* buffer latches, which is exactly what the first attempt did.
{instance}
.control
tran {tstep} {tend} 0 {tstep}
meas tran vfin  FIND v(OUT) AT={tend}
meas tran vpk   MAX  v(OUT) FROM={t1} TO={tend}
meas tran vmin  MIN  v(OUT) FROM={t1} TO={tend}
meas tran vstart FIND v(OUT) AT={t0}
echo STEPRESULT $&vstart $&vfin $&vpk $&vmin
.endc
.end
"""


def step_response(design, sizing, vdd, vcm, corner, extra, step=0.2,
                  tend=2.0, inst=None):
    """Drive a step into a unity-gain buffer and report overshoot and settling."""
    volts = validate._volts_for(design, extra, corner)
    lines = "\n".join(".param {} = {:.6g}u".format(k, v)
                      for k, v in sorted(sizing.items()))
    ex = "\n".join(".param {} = {:.6g}".format(k, v)
                   for k, v in sorted((volts or {}).items()))
    # OUT feeds INN: the instance line is rewritten so the loop is closed
    instance = inst or design.instance.replace(" INP ", " OUT ")
    deck = BUFFER.format(pdk=tb.PDK, here=tb.HERE, core=design.core,
                         corner=corner, vdd=vdd, vcm=vcm, sizing=lines,
                         extra=ex, instance=instance, step=step,
                         t0=tend * 0.1, t1=tend * 0.1 + tend / 500.0,
                         tend=tend, tstep=tend / 4000.0)
    res = tb.run(deck)
    if not res:
        return None
    m = re.search(r"STEPRESULT\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", res["raw"])
    if not m:
        return None
    v0, vf, vpk, vmin = (float(x) for x in m.groups())
    swing = vf - v0
    over = 100.0 * (vpk - vf) / abs(swing) if abs(swing) > 1e-6 else float("nan")
    under = 100.0 * (vf - vmin) / abs(swing) if abs(swing) > 1e-6 else float("nan")
    return {"v0": v0, "vf": vf, "peak": vpk, "min": vmin,
            "overshoot": over, "undershoot": under, "gain": swing / step}
