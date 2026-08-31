#!/usr/bin/env python3
"""Build OPAM_BIASED.sch and .sym: the amplifier with its bias made on chip.

Derived from OPAM.sch.  Two changes and nothing else:

  * the BIAS port becomes an internal node - the iopin is replaced by a plain
    label, so the net keeps its name but stops being a pin;
  * three diode-connected devices are added from VDD to VSS.  BIAS is the tap
    one gate-source drop above VSS, and a gate-source drop is Vth + Vov, so the
    node follows the threshold on its own.  The top of the chain is split in
    two so that no device sits at more than about half the supply across its
    gate; one device there would be at Vgs = 6.7 V, outside the validated box.

Connectivity is by labels placed exactly on the pins, so no wire has to be
routed and nothing can be a grid step away from what it appears to touch.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(HERE)

# tft_igzo.sym, rot=0 flip=0: D at (20,-30), G at (-20,0), S at (20,30)
D_OFF, G_OFF, S_OFF = (20, -30), (-20, 0), (20, 30)

DEV = """C {{symbols/tft_igzo.sym}} {x} {y} 0 0 {{name={name}
W={w}u
L={l}u
ov=5u
nf=1
m=1
B=0
b_scale=1
model=igzo_tft
spiceprefix=X
}}
"""


def lab(x, y, net, tag):
    return "C {devices/lab_pin.sym} %d %d 0 0 {name=%s lab=%s}\n" % (x, y, tag, net)


def device(x, y, name, w, l, d, g, s):
    out = DEV.format(x=x, y=y, name=name, w=w, l=l)
    out += lab(x + D_OFF[0], y + D_OFF[1], d, "l%sd" % name)
    out += lab(x + G_OFF[0], y + G_OFF[1], g, "l%sg" % name)
    out += lab(x + S_OFF[0], y + S_OFF[1], s, "l%ss" % name)
    return out


def build(sizing):
    src = open(os.path.join(DESIGN, "OPAM.sch")).read()

    # BIAS stops being a port and becomes an ordinary internal net
    old = "C {iopin.sym} 730 -530 0 0 {name=p7 lab=BIAS}"
    assert old in src, "BIAS iopin not found"
    src = src.replace(old, lab(730, -530, "BIAS", "l_bias"))

    chain = ""
    for i, (name, key, d, g, s) in enumerate((
            ("MB0", "b1", "VDD", "VDD", "NET_B1"),
            ("MB1", "b1", "NET_B1", "NET_B1", "BIAS"),
            ("MB2", "b2", "BIAS", "BIAS", "VSS"))):
        chain += device(1500, -900 + 150 * i, name,
                        sizing["w_" + key], sizing["l_" + key], d, g, s)

    return src.rstrip("\n") + "\n" + chain


def build_sym():
    """OPAM.sym without the BIAS pin."""
    sym = open(os.path.join(DESIGN, "OPAM.sym")).read()
    out = []
    for line in sym.splitlines(True):
        if "name=BIAS" in line and line.startswith("B 5"):
            continue
        if line.startswith("T {BIAS}"):
            continue
        out.append(line)
    return "".join(out)


if __name__ == "__main__":
    import json
    sys.path.insert(0, HERE)
    import apply_sizing as A

    b = json.load(open(os.path.join(HERE, "best_opam_biased.json")))
    sch = os.path.join(DESIGN, "OPAM_BIASED.sch")
    open(sch, "w").write(build(b["sizing"]))
    open(os.path.join(DESIGN, "OPAM_BIASED.sym"), "w").write(build_sym())
    # the amplifier devices still carry OPAM.sch's sizing, which was found with
    # an external bias; write the self-biased one over them.  No orientation
    # swap: OPAM.sch is already oriented and the file is regenerated each run.
    A.patch(sch, b["sizing"], A.OPAM_GROUPS, set())
    print("wrote OPAM_BIASED.sch and OPAM_BIASED.sym")
