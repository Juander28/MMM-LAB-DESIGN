#!/usr/bin/env python3
"""The OPAM / OPAM2 design report, in English and Spanish.

    python3 make_opam_report.py                 # both, into the OPAM folder
    python3 make_opam_report.py es ~/Documents  # one language, somewhere else

Every number is computed here, by running ngspice against the PDK's own model
files and the same cores the search used.  Nothing is quoted from an earlier
run, so the document cannot drift away from the design it describes.

Code and labels in English; the prose of each PDF in its own language.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/foss/designs/TFT-MMM-LAB-PDK/docs/pdf")

import bfield
import figures
import optimize as O
import report as rep
import report_data as RD
import re
import tb_common as tb

HERE_SIM = os.path.dirname(os.path.abspath(__file__))
from pdfkit import ACCENT, MUTED, Page, PdfPages  # noqa: E402

CORNERS = ("best", "tt", "all")
DB = lambda x: 20 * math.log10(abs(x))       # noqa: E731

TITLES = {"opam2": "OPAM2 - Zysset (EDL 2013)",
          "opam": "OPAM - Zhao (TBCAS 2024)",
          "opam_biased": "OPAM, self-biased"}

GROUPS_OPAM2 = [
    ("input pair", "M3, M4", "w_in", "l_in"),
    ("diode loads", "M6, M7", "w_dl", "l_dl"),
    ("tail", "M8", "w_tail", "l_tail"),
    ("common-mode sensing", "M1, M10", "w_cms", "l_cms"),
    ("common-mode diode", "M2", "w_cmd", "l_cmd"),
    ("diff-to-single followers", "M5, M11", "w_sf", "l_sf"),
    ("diode load at net5", "M17", "w_sfl", "l_sfl"),
    ("pull-down at net6", "M9", "w_d2s", "l_d2s"),
    ("output common source", "M12", "w_od", "l_od"),
    ("output diode load", "M13", "w_ol", "l_ol"),
]
GROUPS_OPAM = [
    ("input pair", "M2, M5", "w_in", "l_in"),
    ("cross-coupled pair", "M3, M4", "w_cc", "l_cc"),
    ("diode loads", "M6, M7", "w_dl", "l_dl"),
    ("first-stage tail", "M8", "w_tail", "l_tail"),
    ("second-stage source devices", "M11, M17", "w_t2", "l_t2"),
    ("second-stage common source", "M12, M18", "w_g2", "l_g2"),
    ("bootstrap load", "M13, M19", "w_bl", "l_bl"),
    ("bootstrap cut-off partner", "M14, M20", "w_bf", "l_bf"),
    ("output followers", "M10, M16", "w_of", "l_of"),
    ("output diode loads", "M9, M15", "w_od", "l_od"),
]
GROUPS_BIAS = [
    ("bias chain, upper pair", "MB0, MB1", "w_b1", "l_b1"),
    ("bias chain, lower", "MB2", "w_b2", "l_b2"),
]


def measure():
    """One pass of ngspice for everything both documents quote."""
    data = RD.collect()

    RD.bias_gen.write_core()
    vdd2, sz2, _ = rep.FINAL["opam2"]
    vdd, sz, extra, vcm = rep.load_opam()

    data["curves"] = {}
    for name, design, sizing, v, c, ex in RD.variants():
        r = data[name]["corners"].get("best")
        if not r:
            continue
        f3 = r["f3db"]
        amp = 0.3 / (10 ** (r["av"] / 20.0))
        data["curves"][name] = {
            corner: RD.curves(name, design, sizing, v, c, corner, ex,
                              f3 / 10.0, amp, "%s_%s" % (name, corner))
            for corner in CORNERS}

    data["field"] = {
        "opam2": bfield.sensitivity("opam2", O.OPAM2, sz2, vdd2,
                                    O.OPAM2.vcm_frac * vdd2, None),
        "opam": bfield.sensitivity("opam", O.OPAM, sz, vdd, vcm, extra),
    }
    data["gvf"] = bfield.gain_vs_field("opam", O.OPAM, sz, vdd, vcm, extra)

    # the AC-versus-transient gap, straight from the standalone testbenches
    data["gain_err"] = {}
    for tag, bench in (("opam2", "tb_opam2.spice"), ("opam", "tb_opam.spice")):
        import subprocess
        out = subprocess.run([tb.NGSPICE, "-b", bench], capture_output=True,
                             text=True, cwd=HERE_SIM).stdout
        m2 = re.search(r"^gain_err\s*=\s*(\S+)", out, re.M)
        data["gain_err"][tag] = float(m2.group(1)) if m2 else float("nan")
    data["probe"] = {
        "OPAM2": bfield.best_probe("opam2", O.OPAM2, sz2, vdd2,
                                   O.OPAM2.vcm_frac * vdd2, None),
        "OPAM": bfield.best_probe("opam", O.OPAM, sz, vdd, vcm, extra),
    }
    return data


def sizing_rows(S, sizing, groups):
    rows = [[S["col_fn"], S["col_dev"], S["col_w"], S["col_l"], S["col_wl"]]]
    for label, devs, wk, lk in groups:
        if wk not in sizing:
            continue
        w, l = sizing[wk], sizing[lk]
        rows.append([label, devs, "%g" % w, "%g" % l, "%.3g" % (w / l)])
    return rows


def result_rows(S, entry, stages=True, bias=False):
    head = [S["col_corner"], S["col_gain"], S["col_f3db"], S["col_pm"],
            S["col_pow"], S["col_vout"]]
    if stages:
        head[2:2] = [S["col_stage1"], S["col_stage2"]]
    if bias:
        head.append(S["col_bias"])
    rows = [head]
    for c in CORNERS:
        r = entry["corners"].get(c)
        if not r:
            continue
        row = [c, "%.2f dB" % r["av"], "%.0f Hz" % r["f3db"],
               "%.2f V" % r["swing"], "%.0f uW" % (r["power"] * 1e6),
               "%.2f V" % r["vout"]]
        if stages:
            row[2:2] = ["%.1f dB" % (r["stage1"] or float("nan")),
                        "%.1f dB" % (r["stage2"] or float("nan"))]
        if bias:
            row.append("%.3f V" % (r["bias"] or float("nan")))
        rows.append(row)
    return rows


def estimate_rows(S, data):
    rows = [[S["col_stage"], S["col_est"], S["col_sim"], S["col_err"]]]
    for name in ("opam2", "opam", "opam_biased"):
        r = data[name]["corners"].get("best")
        if not r:
            continue
        est = r["est"]
        tot_est = sum(DB(v) for v in est.values())
        rows.append(["%s - %s" % (TITLES[name].split(" - ")[0],
                                  "total (best)"),
                     "%.1f dB" % tot_est, "%.1f dB" % r["av"],
                     "%+.1f dB" % (r["av"] - tot_est)])
        for k, v in est.items():
            rows.append(["    %s" % k, "%.1f dB" % DB(v), "", ""])
        rows.append(["    f-3dB", "%.0f Hz" % r["f_est"], "%.0f Hz" % r["f3db"],
                     "x%.1f" % (r["f3db"] / r["f_est"]) if r["f_est"] else ""])
    return rows


def probe_rows(S, data):
    # the full unit does not fit two columns wide; it is in the caption instead
    rows = [[S["col_tone"], S["col_freq"], "OPAM2", "OPAM"]]
    a, b = data["probe"]["OPAM2"], data["probe"]["OPAM"]
    for ra, rb in zip(a, b):
        rows.append([ra["tag"], "%.0f / %.0f" % (ra["f"], rb["f"]),
                     "%.2f" % ra["sens"], "%.2f" % rb["sens"]])
    return rows


def build(lang, out_dir, data):
    import report_text
    S = dict(report_text.STRINGS[lang])
    # Any number quoted in the prose is filled in from the same run that draws
    # the figures, so the two cannot disagree - which they did once, when a
    # re-sizing moved the curves and left the sentence behind.
    gvf = data["gvf"]
    flat = gvf[sorted(gvf, key=lambda k: gvf[k]["f"])[0]]["points"]
    edge = gvf[sorted(gvf, key=lambda k: gvf[k]["f"])[-1]]["points"]
    subs = {
        "gvf_flat": abs(flat[-1]["dgain"]), "gvf_edge": abs(edge[-1]["dgain"]),
        "err2": abs(data["gain_err"]["opam2"]), "err1": abs(data["gain_err"]["opam"]),
    }
    for k in ("gvf", "tran"):
        S[k] = S[k].format(**subs)
    # the design folder by default - the user keeps these with the schematics
    out = os.path.join(out_dir or os.path.dirname(HERE_SIM),
                       "opam_report_%s.pdf" % lang)
    n = 0
    with PdfPages(out) as pdf:
        n += 1
        p = Page(pdf, S["t1"], kicker=S["kicker"], footer=S["footer"])
        p.head(S["intro_h"]); p.text(S["intro"])
        p.head(S["proc_h"]); p.text(S["proc"])
        p.close(n)

        n += 1
        p = Page(pdf, S["size_h"], kicker=S["kicker"], footer=S["footer"])
        p.text(S["size"])
        for name, groups in (("opam2", GROUPS_OPAM2), ("opam", GROUPS_OPAM)):
            p.head(TITLES[name])
            p.table(sizing_rows(S, data[name]["sizing"], groups),
                    [0.30, 0.20, 0.17, 0.17, 0.16])
        p.close(n)

        n += 1
        p = Page(pdf, TITLES["opam_biased"], kicker=S["kicker"], footer=S["footer"])
        p.head(S["bias_h"]); p.text(S["bias"])
        p.table(sizing_rows(S, data["opam_biased"]["sizing"],
                            GROUPS_BIAS + GROUPS_OPAM),
                [0.30, 0.20, 0.17, 0.17, 0.16])
        p.close(n)

        n += 1
        p = Page(pdf, S["gain_h"], kicker=S["kicker"], footer=S["footer"])
        p.text(S["gain"])
        p.head(S["bw_h"]); p.text(S["bw"])
        p.close(n)

        n += 1
        p = Page(pdf, S["res_h"], kicker=S["kicker"], footer=S["footer"])
        p.text(S["res"])
        for name, st, bi in (("opam2", False, False), ("opam", True, False),
                             ("opam_biased", True, True)):
            p.head(TITLES[name])
            p.table(result_rows(S, data[name], st, bi),
                    [0.11, 0.14, 0.13, 0.13, 0.13, 0.12, 0.12, 0.12])
        p.close(n)

        n += 1
        p = Page(pdf, S["exp_h"], kicker=S["kicker"], footer=S["footer"])
        p.text(S["exp"])
        p.table(estimate_rows(S, data), [0.34, 0.22, 0.22, 0.22])
        p.close(n)

        n += 1
        p = Page(pdf, S["gap_h"], kicker=S["kicker"], footer=S["footer"])
        p.text(S["gap"])
        p.figure(figures.bode(data["curves"]["opam"], ""), S["cap_bode"])
        p.close(n)

        n += 1
        p = Page(pdf, "OPAM2", kicker=S["kicker"], footer=S["footer"])
        p.figure(figures.bode(data["curves"]["opam2"], ""), S["cap_bode"])
        p.figure(figures.transfer(data["curves"]["opam2"], ""), S["cap_tf"])
        p.close(n)

        n += 1
        p = Page(pdf, S["field_h"], kicker=S["kicker"], footer=S["footer"])
        p.text(S["field"])
        p.head(S["sense_h"]); p.text(S["sense"])
        p.close(n)

        n += 1
        p = Page(pdf, S["gvf_h"], kicker=S["kicker"], footer=S["footer"])
        p.text(S["gvf"])
        p.figure(figures.gain_vs_field(
            data["gvf"], "", "relative mobility change dmu/mu", "gain (dB)"),
            S["cap_gvf"])
        p.close(n)

        n += 1
        p = Page(pdf, S["tran_h"], kicker=S["kicker"], footer=S["footer"])
        p.text(S["tran"])
        p.figure(figures.sine_io(data["curves"]["opam2"]["best"], "OPAM2",
                                 "time (ms)", "input (mV)", "output (V)"),
                 S["cap_io"])
        p.figure(figures.sine_io(data["curves"]["opam"]["best"], "OPAM",
                                 "time (ms)", "input (mV)", "output (V)"),
                 S["cap_io"])
        p.close(n)

        n += 1
        p = Page(pdf, S["sense_h"], kicker=S["kicker"], footer=S["footer"])
        p.figure(figures.bandwidth_vs_field(
            data["field"]["opam"], "", "relative mobility change dmu/mu",
            "f-3dB (Hz)"), S["cap_bw"])
        p.figure(figures.probe_sensitivity(
            data["probe"], "", "probe tone position",
            "|dB| per unit dmu/mu"), S["cap_probe"])
        p.table(probe_rows(S, data), [0.30, 0.26, 0.22, 0.22])
        p.text(S["col_sens"], size=8, color=MUTED)
        p.close(n)

        n += 1
        p = Page(pdf, S["lim_h"], kicker=S["kicker"], footer=S["footer"])
        p.text(S["lim"])
        p.close(n)

        info = pdf.infodict()
        info["Title"] = ("IGZO TFT amplifiers - design report" if lang == "en"
                         else "Amplificadores IGZO TFT - informe de diseno")
        info["Author"] = "UCI/INRF - MMM Lab"
    print("wrote %s (%d bytes)" % (out, os.path.getsize(out)))


if __name__ == "__main__":
    args = sys.argv[1:]
    out_dir = None
    if args and args[-1].startswith(("/", "~", ".")):
        out_dir = os.path.expanduser(args.pop())
    shared = measure()
    for lg in (args or ["en", "es"]):
        build(lg, out_dir, shared)
