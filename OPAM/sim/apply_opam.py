#!/usr/bin/env python3
"""Write the OPAM result into OPAM.sch and test.sch, then check the netlist.

The check is the point: after patching, xschem is asked to netlist the
schematic and every device's three terminals are compared against
opam_core.spice, which is what was actually simulated.  If the drawing and the
simulation ever drift apart, this fails loudly.
"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apply_sizing as A

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
DEV = re.compile(r"(XM\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+igzo_tft")

CONTROL = '''value="
* The IGZO models are DC-only and validated for VGS <= 6 V, VDS <= 10 V.
* The bootstrap load is diode-connected at DC and only becomes a current
* source above the corner set by C1/C2, so read the gain from the AC plateau,
* not from DC, and take the swing from the transient run.
.control
save all
op
print v(OUT) v(x1.net1) v(x1.net2) v(x1.net3) v(x1.net9)
ac dec 10 0.1 1e6
meas ac av_max MAX vdb(OUT)
meas ac av_stage1 MAX vdb(x1.net3) from=0.1 to=1e6
meas ac av_stage2 MAX vdb(x1.net9) from=0.1 to=1e6
plot vdb(OUT)
.endc
"}'''


def main():
    b = json.load(open(os.path.join(HERE, "best_opam.json")))
    sz = dict(b["sizing"], c_boot=160.64, c_fb=160.64)
    # vcm lives beside the sizing, not inside it, since it is a testbench
    # setting rather than a device dimension
    vbias = sz.pop("vbias")
    vcm, vdd = b.get("vcm", sz.pop("vcm", 2.0)), b["vdd"]

    # OPAM.sch.base is already oriented by make_opam_structure.py; applying
    # the swap again here would just undo it
    A.patch(os.path.join(SRC, "OPAM.sch"), sz, A.OPAM_GROUPS, set())
    print("OPAM.sch: sizing written from OPAM.sch.base")

    p = os.path.join(SRC, "test.sch")
    t = open(p).read()
    t = re.sub(r"\{name=V1 value=\S+ ", "{name=V1 value=%g " % vdd, t)
    t = re.sub(r"\{name=V2 value=\S+ ", "{name=V2 value=%.2f " % vbias, t)
    t = re.sub(r"\{name=V3 value=\S+ ", "{name=V3 value=%.2f " % vcm, t)
    old = 'value="\n.control\nsave all\ndc V4 -10 10 0.1 \nplot v(OUT)\n.endc\n"}'
    if old in t:
        t = t.replace(old, CONTROL)
    open(p, "w").write(t)
    print("test.sch: VDD=%g V, BIAS=%.2f V, Vcm=%.2f V" % (vdd, vbias, vcm))

    env = dict(os.environ, PDK_ROOT="/headless/pdks", PDK="TFT-MMM-LAB-PDK",
               DESIGNS="/foss/designs")
    out = os.path.join(SRC, "simulation", "test.sch")
    os.makedirs(out, exist_ok=True)
    subprocess.run(["xschem", "-q", "-n", "-s", "-r", "--rcfile",
                    os.path.expanduser("~/.xschem/xschemrc"), "-o", out,
                    "test.sch"], cwd=SRC, env=env, capture_output=True)

    got = {m.group(1): m.groups()[1:] for m in
           (DEV.match(l) for l in open(os.path.join(out, "test.spice"))) if m}
    want = {m.group(1): m.groups()[1:] for m in
            (DEV.match(l) for l in open(os.path.join(HERE, "opam_core.spice"))) if m}
    bad = [n for n in want if got.get(n) != want[n]]
    print("netlist check: %d/%d devices match%s"
          % (len(want) - len(bad), len(want),
             "" if not bad else " - MISMATCH on %s" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
