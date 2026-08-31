#!/usr/bin/env python3
"""Check every schematic against the netlist that was actually simulated.

Terminals AND dimensions, device by device.  OPAM had this check from the
start; OPAM2 did not, and it drifted: the input pair kept L = 10 um in the
schematic long after the search had settled on 25 um, so the schematic
testbench reported 40.1 dB where the core reported 36.2 dB.  A sizing that
lives in two places needs a check that they agree.

    python3 check_schematics.py          # exits non-zero on any mismatch
"""

import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(HERE)
TFT = re.compile(r"^(XM\w+)\s+(\S+)\s+(\S+)\s+(\S+)\s+igzo_tft\s+W=(\S+)\s+L=(\S+)")
CAP = re.compile(r"^(XC\w+)\s+(\S+)\s+(\S+)\s+cap_mim\s+W=(\S+)\s+L=(\S+)")
RES = re.compile(r"^(R\w+)\s+(\S+)\s+(\S+)\s+(\S+)")

OPAM2_SIZING = dict(
    l_cmd=200, l_cms=200, l_d2s=200, l_dl=200, l_in=25, l_od=140, l_ol=200,
    l_sf=800, l_sfl=100, l_tail=200, w_cmd=140, w_cms=200, w_d2s=200,
    w_dl=50, w_in=3200, w_od=1300, w_ol=140, w_sf=50, w_sfl=200, w_tail=200)


def biased_sizing():
    b = json.load(open(os.path.join(HERE, "best_opam_biased.json")))["sizing"]
    return dict(b, c_boot=160.64, c_fb=160.64)


def opam_sizing():
    b = json.load(open(os.path.join(HERE, "best_opam.json")))["sizing"]
    return dict(b, c_boot=160.64, c_fb=160.64)


def um(text):
    """'3200u' -> 3200.0"""
    return float(text.rstrip("uU"))


SUFFIX = {"t": 1e12, "g": 1e9, "meg": 1e6, "k": 1e3, "m": 1e-3, "u": 1e-6,
          "n": 1e-9, "p": 1e-12, "f": 1e-15}


def spice_value(text, sizing):
    """Resolve a resistor value: a sizing-group name, or a SPICE number."""
    if text in sizing:
        return float(sizing[text])
    t = text.strip().lower()
    for suf in ("meg", "t", "g", "k", "m", "u", "n", "p", "f"):
        if t.endswith(suf):
            try:
                return float(t[:-len(suf)]) * SUFFIX[suf]
            except ValueError:
                break
    return float(t)


def _dim(text, sizing):
    """A dimension is either a number or the name of a sizing group."""
    return sizing[text] if text in sizing else um(text)


def parse(path, sizing=None):
    """{name: (terminals, W, L)} for every device, sized or parameterised.

    Transistors, capacitors and resistors alike: the r_off resistors are the
    reason the schematic and the simulated core once differed by 11 dB on the
    transient, and a check that only looked at transistors said 19/19.
    """
    sizing = sizing or {}
    out = {}
    for raw in open(path):
        line = raw.replace("'", "")
        m = TFT.match(line)
        if m:
            name, d, g, s, w, l = m.groups()
            # SPICE folds case, so node names are compared folded
            out[name.upper()] = ((d.lower(), g.lower(), s.lower()),
                                 _dim(w, sizing), _dim(l, sizing))
            continue
        m = CAP.match(line)
        if m:
            name, p, n, w, l = m.groups()
            out[name.upper()] = ((p.lower(), n.lower()),
                                 _dim(w, sizing), _dim(l, sizing))
            continue
        m = RES.match(line)
        if m:
            name, p, n, v = m.groups()
            r = spice_value(v, dict(sizing, r_off=1e12))
            out[name.upper()] = ((p.lower(), n.lower()), r, r)
    return out


def netlist(sch, outdir):
    env = dict(os.environ, PDK_ROOT="/headless/pdks", PDK="TFT-MMM-LAB-PDK",
               DESIGNS="/foss/designs")
    os.makedirs(outdir, exist_ok=True)
    subprocess.run(["xschem", "-q", "-n", "-s", "-r", "--rcfile",
                    os.path.expanduser("~/.xschem/xschemrc"), "-o", outdir, sch],
                   cwd=DESIGN, env=env, capture_output=True)


def check(name, sch, core, sizing):
    outdir = os.path.join(DESIGN, "simulation", sch)
    netlist(sch, outdir)
    got = parse(os.path.join(outdir, sch.replace(".sch", ".spice")))
    want = parse(os.path.join(HERE, core), sizing)
    bad = []
    for dev, (term, w, l) in sorted(want.items()):
        g = got.get(dev)
        if g is None:
            bad.append("%s missing from the schematic" % dev)
        elif g[0] != term:
            bad.append("%s terminals %s, expected %s" % (dev, g[0], term))
        elif abs(g[1] - w) > 1e-6 * max(1.0, abs(w)) or abs(g[2] - l) > 1e-6:
            bad.append("%s W/L = %g/%g, expected %g/%g" % (dev, g[1], g[2], w, l))
    print("%-8s %2d/%2d devices match%s"
          % (name, len(want) - len(bad), len(want),
             "" if not bad else ":\n    " + "\n    ".join(bad)))
    return bad


if __name__ == "__main__":
    import bias_gen
    bias_gen.write_core()
    bad = check("OPAM2", "test2.sch", "opam2_core.spice", OPAM2_SIZING)
    bad += check("OPAM", "test.sch", "opam_core.spice", opam_sizing())
    bad += check("BIASED", "test_biased.sch", "opam_biased_core.spice",
                 biased_sizing())
    sys.exit(1 if bad else 0)
