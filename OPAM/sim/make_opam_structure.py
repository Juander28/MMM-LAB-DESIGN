#!/usr/bin/env python3
"""Build OPAM.sch.base: the original schematic plus every STRUCTURAL fix.

Sizing and structure are separated on purpose.  apply_sizing.patch rewrites W
and L and rederives from a baseline every time, so it is idempotent - but that
means any structural edit made directly to OPAM.sch is wiped the next time a
sizing is applied, which is exactly what happened.  Structure lives here.

Three changes on top of OPAM.sch.orig:

  1. Source/drain orientation.  No longer load-bearing - the PDK's junctions are
     inert since commit 67779ed - but kept, because it is correct and because
     the cores are generated from this file.
  2. The two bootstrap gate nodes are named BOOT_L and BOOT_R, and each gets a
     resistor to VDD standing in for the off-state channel of XM14/XM20.  Level
     1 has no subthreshold current, so without it those nodes have no DC path
     at all and the solver puts them wherever it likes.
  3. C3/C4 back to the 160.64 um they were drawn at.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apply_sizing as A

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(HERE)


def lab(x, y, net, tag):
    return "C {devices/lab_pin.sym} %d %d 0 0 {name=%s lab=%s}\n" % (x, y, tag, net)


def build():
    src = os.path.join(DESIGN, "OPAM.sch.orig")
    base = os.path.join(DESIGN, "OPAM.sch.base")
    # orientation only; sizes are written later by apply_sizing
    A.patch(src, {}, {}, A.OPAM_SWAP, out_path=base)

    t = open(base).read()
    # M13 sits at (360,-800) flip=1 -> gate at (380,-800)
    # M19 sits at (870,-800) flip=0 -> gate at (850,-800)
    add = lab(380, -800, "BOOT_L", "l_boot_l") + lab(850, -800, "BOOT_R", "l_boot_r")
    for i, (x, node) in enumerate(((1100, "BOOT_L"), (1250, "BOOT_R")), start=1):
        add += "C {devices/res.sym} %d -800 0 0 {name=Rb%d value=1T m=1}\n" % (x, i)
        add += lab(x, -830, node, "lrb%dp" % i)
        add += lab(x, -770, "VDD", "lrb%dm" % i)
    t = t.rstrip("\n") + "\n" + add
    for name in ("C3", "C4"):
        t = t.replace("{name=%s\nW=100u\nL=50u" % name,
                      "{name=%s\nW=160.64u\nL=160.64u" % name)
    open(base, "w").write(t)
    print("wrote OPAM.sch.base (%d devices re-oriented, 2 nodes named, "
          "2 resistors added)" % len(A.OPAM_SWAP))


if __name__ == "__main__":
    build()
