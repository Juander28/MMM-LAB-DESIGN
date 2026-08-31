#!/usr/bin/env python3
"""Report a sizing in full: operating point, gain, swing, corners, robustness.

The gain figure that matters is not just the nominal one.  A unipolar
amplifier that leans on a cross-coupled pair or a bootstrap load buys its gain
from a near-cancellation, and a near-cancellation is only a design if it
survives the corners and a mismatch on the devices doing the cancelling.

Whatever the search did, this has to do too - in particular the per-corner
bias trim.  Vto moves 0.62 V between `best` and `all`, so a design with an
external bias pin is reported at the bias each corner actually needs, and the
three values are printed.  Reporting all three corners at the `best` bias
would just be measuring an untrimmed part.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tb_common as tb
import score

CORNERS = ("best", "tt", "all")


def _volts_for(design, extra, corner):
    """The bias voltages this corner is run at, trim included."""
    v = dict(extra or {})
    if design.trim and design.trim in v:
        v[design.trim] = max(0.05, v[design.trim]
                             + tb.VTO[corner] - tb.VTO["best"])
    return v


def _run(design, sizing, vdd, vcm, corner, extra):
    volts = _volts_for(design, extra, corner)
    res = tb.run(tb.build_netlist(design.core, design.instance, design.nodes,
                                  sizing, vdd, vcm, corner, volts,
                                  getattr(design, "stages", ())))
    val, bad, info = score.objective(res, vdd, tb.VTO[corner], design.diodes,
                                     design.cutoff, design.gain_key,
                                     design.swing_min, design.pm_min, vcm,
                                     design.follow_tol)
    return res, val, bad, info, volts


def report(design, sizing, vdd, extra=None, mismatch=0.10, vcm=None):
    vcm = design.vcm_frac * vdd if vcm is None else vcm
    print("=== %s : VDD = %g V, Vcm = %g V ===" % (design.name.upper(), vdd, vcm))

    for corner in CORNERS:
        res, val, bad, info, volts = _run(design, sizing, vdd, vcm, corner, extra)
        m = res["meas"] if res else {}
        print("\n--- corner %s%s ---"
              % (corner, "  (%s = %.2f V)" % (design.trim, volts[design.trim])
                 if design.trim and design.trim in volts else ""))
        print("  Av(DC)  = %7.2f dB     Av(max) = %7.2f dB at %.3g Hz"
              % (m.get("av_db", float("nan")), m.get("av_max", float("nan")),
                 m.get("f_at_max", float("nan"))))
        print("  Vout    = %7.3f V      swing(DC) = %.2f V   power = %.0f uW"
              % (info.get("vout", float("nan")), info.get("swing", float("nan")),
                 info.get("power", float("nan")) * 1e6))
        print("  status  :", "OK" if not bad else "; ".join(bad))
        if any(k.startswith("st_") for k in m):
            print("  per stage: " + "  ".join(
                "%s = %.2f dB" % (k[3:], m[k])
                for k in sorted(m) if k.startswith("st_")))
        if corner == "best":
            print("  operating point:")
            for n, d in sorted(res["dev"].items()):
                short = n.split(".")[-2]
                vov = d["vgs_t"] - tb.VTO[corner]
                print("    %-6s vgs=%6.3f vov=%6.3f vds=%6.3f id=%8.2f uA "
                      "gm=%8.2f uS gm/gds=%7.1f"
                      % (short, d["vgs_t"], vov, d["vds_t"], d["id_t"] * 1e6,
                         d["gm"] * 1e6,
                         d["gm"] / d["gds"] if d["gds"] else float("inf")))

    # --- robustness: move one width at a time and see what the gain does ---
    print("\n--- robustness: %.0f%% mismatch on one width at a time (best corner) ---"
          % (mismatch * 100))
    base = _run(design, sizing, vdd, vcm, "best", extra)[0]
    base_av = base["meas"].get(design.gain_key, float("nan"))
    worst = (base_av, "none")
    for key in sorted(k for k in sizing if k.startswith("w")):
        for sign in (1 - mismatch, 1 + mismatch):
            trial = dict(sizing)
            trial[key] = sizing[key] * sign
            r = _run(design, trial, vdd, vcm, "best", extra)[0]
            av = r["meas"].get(design.gain_key, float("-inf")) if r else float("-inf")
            if av < worst[0]:
                worst = (av, "%s %+.0f%%" % (key, (sign - 1) * 100))
    print("  nominal %.2f dB -> worst %.2f dB (%s)" % (base_av, worst[0], worst[1]))
    return worst
