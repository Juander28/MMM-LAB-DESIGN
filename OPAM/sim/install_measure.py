#!/usr/bin/env python3
"""Put the shared measurement block into every testbench, .spice and .sch.

The .sch files carry it inside the quoted value="..." of an xschem code block,
so the block deliberately contains no double quotes.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(HERE)

OPAM2_NODES = ["OUT", "x1.net1", "x1.net2", "x1.net3", "x1.net4", "x1.net5",
               "x1.net6"]
OPAM_NODES = ["OUT", "x1.net1", "x1.net2", "x1.net3", "x1.net7",
              "x1.net8", "x1.BOOT_R"]
OPAM_STAGES = [("av_stage1", "x1.net3"), ("av_stage2", "x1.net7")]


PARAM = re.compile(r"^\.param (w_|l_|c_|vcm|vbias|vdd)\S*\s*=.*$", re.M)


def patch_params(path, vdd, vcm, sizing, extra=None):
    """Rewrite the .param block of a standalone testbench from the JSON.

    These files used to carry the sizing by hand, and it went stale the moment
    a search finished: tb_opam.spice was still holding the gain-optimal numbers
    after the design had been re-sized for phase margin, so the report quoted a
    gap of 10.9 dB that no longer existed.
    """
    t = open(path).read()
    block = [".param vdd = %g" % vdd, ".param vcm = %g" % vcm]
    for k, v in sorted((extra or {}).items()):
        block.append(".param %s = %g" % (k, v))
    for k in sorted(sizing):
        block.append(".param %-7s = %gu" % (k, sizing[k]))
    first = PARAM.search(t)
    assert first, path
    t = PARAM.sub("", t)
    t = t[:first.start()] + "\n".join(block) + "\n" + t[first.start():]
    t = re.sub(r"\n{3,}", "\n\n", t)
    open(path, "w").write(t)
    print("params written into", os.path.relpath(path, DESIGN))


def patch_spice(path, nodes, stages):
    """Replace everything from .control to .endc in a standalone testbench."""
    t = open(path).read()
    new = measure.block(nodes, stages, plots=False, src="VD", vin="v(d)")
    t2, n = re.subn(r"\.control\n.*?\.endc\n", new, t, flags=re.S)
    assert n == 1, "no .control block in %s" % path
    open(path, "w").write(t2)
    print("patched", os.path.relpath(path, DESIGN))


def patch_sch(path, nodes, stages):
    """Replace the value=... payload of the NGSPICE code block in a schematic."""
    t = open(path).read()
    # In the schematics the differential source is V4, wired between INN and
    # INP, so there is no single node carrying the differential input.
    new = measure.block(nodes, stages, plots=True, src="V4", vin="v(INN,INP)")
    pat = re.compile(r'(\{name=NGSPICE only_toplevel=true\nvalue=")(.*?)("\})', re.S)
    m = pat.search(t)
    assert m, path
    t2 = t[:m.start(2)] + "\n" + new + t[m.end(2):]
    open(path, "w").write(t2)
    print("patched", os.path.relpath(path, DESIGN))


def refresh_params():
    """Pull both standalone benches back in line with the stored sizings."""
    import report as rep
    vdd2, sz2, _ = rep.FINAL["opam2"]
    patch_params(os.path.join(HERE, "tb_opam2.spice"), vdd2,
                 OPAM2_VCM_FRAC * vdd2, sz2)
    vdd, sz, extra, vcm = rep.load_opam()
    patch_params(os.path.join(HERE, "tb_opam.spice"), vdd, vcm, sz, extra)


OPAM2_VCM_FRAC = 0.4


if __name__ == "__main__":
    patch_spice(os.path.join(HERE, "tb_opam2.spice"), OPAM2_NODES, [])
    patch_spice(os.path.join(HERE, "tb_opam.spice"), OPAM_NODES, OPAM_STAGES)
    patch_sch(os.path.join(DESIGN, "test2.sch"), OPAM2_NODES, [])
    patch_sch(os.path.join(DESIGN, "test.sch"), OPAM_NODES, OPAM_STAGES)
    refresh_params()
