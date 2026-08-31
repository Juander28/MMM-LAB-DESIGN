#!/usr/bin/env python3
"""Print the final report for a sized design: corners, operating point, margin.

    python3 report.py opam2
    python3 report.py opam
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json
import optimize, tb_common as tb, validate

# OPAM2's sizing lives here; OPAM's in best_opam.json (see load_opam).
FINAL = {
    "opam2": (8, dict(
        w_in=3200, l_in=25, w_dl=50, l_dl=200, w_tail=200, l_tail=200,
        w_cms=200, l_cms=200, w_cmd=140, l_cmd=200, w_sf=50, l_sf=800,
        w_sfl=200, l_sfl=100, w_d2s=200, l_d2s=200, w_od=1300, l_od=140,
        w_ol=140, l_ol=200), None),
}

def load_biased():
    """The self-biased variant: no BIAS pin, and nothing trimmed per corner."""
    b = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "best_opam_biased.json")))
    sz = dict(b["sizing"], c_boot=160.64, c_fb=160.64)
    return b["vdd"], sz, None, b["vcm"]


def load_opam():
    """OPAM's sizing lives in best_opam.json, written by search_opam.py."""
    b = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "best_opam.json")))
    sz = dict(b["sizing"], c_boot=160.64, c_fb=160.64)
    # vcm is a testbench setting, not a device dimension, so it may sit beside
    # the sizing rather than inside it
    vbias = sz.pop("vbias")
    vcm = b.get("vcm", sz.pop("vcm", 2.0))
    return b["vdd"], sz, {"vbias": vbias}, vcm


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "opam2"
    if name in ("opam", "opam_biased"):
        if name == "opam":
            vdd, sizing, extra, vcm = load_opam()
            d = optimize.OPAM
        else:
            import bias_gen
            bias_gen.write_core()
            vdd, sizing, extra, vcm = load_biased()
            d = optimize.OPAM_BIASED
        validate.report(d, sizing, vdd, extra, vcm=vcm)
        # The bootstrap load is a current source only in band, so the swing has
        # to come from a transient run, not from a DC sweep.
        print("\n--- output swing in transient (20 mV differential input) ---")
        for corner in validate.CORNERS:
            row = []
            for f in (10, 100, 1000, 10000):
                sw = tb.transient_swing(
                    d.core, d.instance, sizing, vdd, vcm, corner, f, 0.02,
                    validate._volts_for(d, extra, corner))
                row.append("%6.0f Hz: %s" % (f, "n/a" if sw is None
                                             else "%5.2f V" % sw))
            print("  %-5s %s" % (corner, "   ".join(row)))
    else:
        vdd, sizing, extra = FINAL[name]
        d = optimize.DESIGNS[name]
        validate.report(d, sizing, vdd, extra, vcm=d.vcm_frac * vdd)
