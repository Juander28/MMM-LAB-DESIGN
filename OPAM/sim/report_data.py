#!/usr/bin/env python3
"""Collect every number the report quotes, straight from ngspice.

Nothing here is remembered from an earlier run: if the sizing or the models
change, the numbers change with them, and a stale figure is impossible.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bias_gen
import optimize as O
import report as rep
import score
import tb_common as tb
import validate

CORNERS = ("best", "tt", "all")
COX = 1.564e-3        # F/m^2, measured on the 400 x 400 um plate
RC_W = 3.3            # Ohm*m per contact
LAMBDA = {"best": 0.0067, "tt": 0.0142, "all": 0.0355, "short": 0.0659}
KP = {"best": 0.717e-6, "tt": 0.562e-6, "all": 0.381e-6, "short": 0.128e-6}
MU = {"best": 4.584e-4, "tt": 3.593e-4, "all": 2.436e-4, "short": 8.184e-5}


def variants():
    """The three circuits the report covers."""
    bias_gen.write_core()
    vdd2, sz2, _ = rep.FINAL["opam2"]
    vdd, sz, extra, vcm = rep.load_opam()
    vddb, szb, _, vcmb = rep.load_biased()
    return [
        ("opam2", O.OPAM2, sz2, vdd2, O.OPAM2.vcm_frac * vdd2, None),
        ("opam", O.OPAM, sz, vdd, vcm, extra),
        ("opam_biased", O.OPAM_BIASED, szb, vddb, vcmb, None),
    ]


def run_corner(design, sizing, vdd, vcm, corner, extra):
    volts = validate._volts_for(design, extra, corner)
    res = tb.run(tb.build_netlist(design.core, design.instance, design.nodes,
                                  sizing, vdd, vcm, corner, volts,
                                  getattr(design, "stages", ())))
    if not res:
        return None
    val, bad, info = score.objective(res, vdd, tb.VTO[corner], design.diodes,
                                     design.cutoff, design.gain_key,
                                     design.swing_min)
    m = res["meas"]
    return {
        "av": m.get(design.gain_key, float("nan")),
        "av_dc": m.get("av_db", float("nan")),
        "f3db": m.get("f3db", float("nan")),
        "funity": m.get("funity", float("nan")),
        "stage1": m.get("st_stage1"), "stage2": m.get("st_stage2"),
        "vout": info.get("vout", float("nan")),
        "swing": info.get("swing", float("nan")),
        "power": info.get("power", float("nan")),
        "bias": res["nodes"].get("x1.bias"),
        "ok": not bad, "bad": bad,
        "dev": res["dev"], "volts": volts,
    }


def gm_gds(dev, name):
    d = dev.get("m.x1.x%s.m1" % name.lower())
    if d is None:
        return None
    return d["gm"], d["gds"], d["id_t"], d["vgs_t"]


def estimate(name, r, sizing, corner):
    """Hand estimates for the dominant stages, from the operating point.

    These are the textbook expressions, evaluated with the gm and gds the
    simulator reports.  The point is not to reproduce the simulator - it is to
    show which term sets the gain, so a sizing decision can be made without one.
    """
    dev, out = r["dev"], {}

    def g(n):
        v = gm_gds(dev, n)
        return v if v else (float("nan"),) * 4

    if name == "opam2":
        gm_in, gds_in, _, _ = g("m3")
        gm_dl, gds_dl, _, _ = g("m6")
        out["stage1"] = gm_in / (gm_dl + gds_in + gds_dl)
        gm_od, gds_od, _, _ = g("m12")
        gm_ol, gds_ol, _, _ = g("m13")
        out["output"] = gm_od / (gm_ol + gds_od + gds_ol)
    else:
        gm_in, gds_in, _, _ = g("m2")
        gm_dl, gds_dl, _, _ = g("m6")
        gm_cc, gds_cc, _, _ = g("m3")
        out["stage1"] = gm_in / (gm_dl - gm_cc + gds_in + gds_dl + gds_cc)
        gm_g2, gds_g2, _, _ = g("m18")
        _, gds_bl, _, _ = g("m19")
        gm_t2, gds_t2, _, _ = g("m17")
        # the source device degenerates the stage: gm_eff = gm/(1 + gm/gds_t2)
        gm_eff = gm_g2 / (1.0 + gm_g2 / gds_t2) if gds_t2 else float("nan")
        out["stage2"] = gm_eff / (gds_g2 + gds_bl)
    return out


def node_poles(core, sizing, dev, supplies=("vdd", "vss", "0")):
    """Estimate the pole at every internal node, and return the lowest.

    At each node: R is one over the shunt conductance seen there, C is the sum
    of the overlap capacitances of every transistor terminal on it plus any MIM
    plate.  The dominant pole is the smallest 1/(2*pi*R*C).

    Picking the node by hand does not work - for OPAM2 the output sits on a
    diode load and its pole is a kilohertz away, while the real corner is set
    by the first stage's drain.  Sweeping every node finds it without guessing.

    This is the weakest number in the report, and it is weak for a stated
    reason: Cox is measured, but the 5 um gate overlap it multiplies was read
    off one GDS cell, and nothing in this PDK has been checked against a
    measured C-V or an S-parameter.
    """
    import re
    gcond, cap = {}, {}

    def add(d, k, v):
        d[k] = d.get(k, 0.0) + v

    tft = re.compile(r"^(XM\w+)\s+(\S+)\s+(\S+)\s+(\S+)\s+igzo_tft"
                     r"\s+W='(\w+)'\s+L='(\w+)'")
    mim = re.compile(r"^(XC\w+)\s+(\S+)\s+(\S+)\s+cap_mim\s+W='(\w+)'\s+L='(\w+)'")

    for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  core)):
        m = tft.match(line)
        if m:
            name, d, g, s, wk, lk = m.groups()
            e = dev.get("m.x1.%s.m1" % name.lower())
            if not e:
                continue
            w = sizing[wk] * 1e-6
            cov = COX * 5e-6 * w          # per side, at the drawn 5 um overlap
            for node in (d, s):
                add(gcond, node.lower(), e["gds"])
            add(cap, g.lower(), 2 * cov)
            add(cap, d.lower(), cov)
            add(cap, s.lower(), cov)
            # a device whose gate is on one of its own channel nodes loads that
            # node with its full transconductance
            if g.lower() in (d.lower(), s.lower()):
                add(gcond, g.lower(), e["gm"])
            continue
        m = mim.match(line)
        if m:
            _, p, n, wk, lk = m.groups()
            c = COX * sizing[wk] * 1e-6 * sizing[lk] * 1e-6
            add(cap, p.lower(), c)
            add(cap, n.lower(), c)

    best = None
    for node, c in cap.items():
        if node in supplies or c <= 0:
            continue
        g = gcond.get(node, 0.0)
        if g <= 0:
            continue
        f = g / (2 * 3.141592653589793 * c)
        if best is None or f < best[0]:
            best = (f, node, 1.0 / g, c)
    return best or (float("nan"), "?", float("nan"), float("nan"))


def collect():
    data = {}
    for name, design, sizing, vdd, vcm, extra in variants():
        entry = {"sizing": sizing, "vdd": vdd, "vcm": vcm, "corners": {},
                 "design": design.name}
        for corner in CORNERS:
            r = run_corner(design, sizing, vdd, vcm, corner, extra)
            if r is None:
                continue
            r["est"] = estimate(name, r, sizing, corner)
            f, node, rr, cc = node_poles(design.core, sizing, r["dev"])
            r["f_est"], r["f_node"] = f, node
            r["f_r"], r["f_c"] = rr, cc
            del r["dev"]
            entry["corners"][corner] = r
        data[name] = entry
    return data


if __name__ == "__main__":
    d = collect()
    for name, e in d.items():
        print("=== %s (VDD=%g, Vcm=%g) ===" % (name, e["vdd"], e["vcm"]))
        for c, r in e["corners"].items():
            est = r["est"]
            print("  %-5s Av=%6.2f dB  f3dB=%7.1f Hz  P=%5.0f uW  ok=%s"
                  % (c, r["av"], r["f3db"], r["power"] * 1e6, r["ok"]))
            import math
            print("        estimado: " + ", ".join(
                "%s = %.1f dB" % (k, 20 * math.log10(abs(v)))
                for k, v in est.items()))
            print("        polo dominante estimado: %.1f Hz en %s "
                  "(R = %.1f Mohm, C = %.2f pF)"
                  % (r["f_est"], r["f_node"], r["f_r"] / 1e6, r["f_c"] * 1e12))


CURVE_TB = """* curve extraction - see report_data.py
.include {pdk}/design.ngspice
.lib {pdk}/igzo_mmm_lab.ngspice {corner}
.include "{here}/{core}"
.param vdd = {vdd}
.param vcm = {vcm}
{extra}
{sizing}
VDD VDD 0 DC 'vdd'
VCM cm  0 DC 'vcm'
VD  d   0 DC 0 AC 1 SIN(0 {amp} {fsig})
EIP INP cm d 0 0.5
EIN INN cm d 0 -0.5
{instance}
.control
set filetype=ascii
ac dec 20 0.1 1e6
wrdata {out}_ac.txt vdb(OUT) 180/PI*cph(v(OUT))
dc VD -2 2 0.005
wrdata {out}_dc.txt v(OUT)
tran {tstep} {tstop} {tskip}
wrdata {out}_tr.txt v(OUT) v(d)
.endc
.end
"""


def curves(name, design, sizing, vdd, vcm, corner, extra, fsig, amp, out):
    """Write the AC, DC and transient curves to text files and read them back."""
    import subprocess
    import tempfile
    lines = "\n".join(".param {} = {:.6g}u".format(k, v)
                      for k, v in sorted(sizing.items()))
    volts = validate._volts_for(design, extra, corner)
    extra_lines = "\n".join(".param {} = {:.6g}".format(k, v)
                            for k, v in sorted((volts or {}).items()))
    deck = CURVE_TB.format(
        pdk=tb.PDK, here=tb.HERE, core=design.core, corner=corner, vdd=vdd,
        vcm=vcm, sizing=lines, extra=extra_lines, instance=design.instance,
        amp=amp, fsig=fsig, out=out,
        tstep=1.0 / (50 * fsig), tstop=206.0 / fsig, tskip=200.0 / fsig)
    d = tempfile.mkdtemp()
    p = os.path.join(d, "c.spice")
    open(p, "w").write(deck)
    subprocess.run([tb.NGSPICE, "-b", p], capture_output=True, text=True,
                   cwd=d, timeout=600)
    got = {}
    for tag in ("ac", "dc", "tr"):
        f = os.path.join(d, "%s_%s.txt" % (out, tag))
        if not os.path.exists(f):
            continue
        cols = []
        for line in open(f):
            parts = line.split()
            if not parts:
                continue
            try:
                cols.append([float(x) for x in parts])
            except ValueError:
                pass
        got[tag] = list(zip(*cols)) if cols else None
    return got
