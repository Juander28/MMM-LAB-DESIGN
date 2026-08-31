#!/usr/bin/env python3
"""Figures for the WPT report.

Palette and conventions inherited from OPAM/sim/figures.py, so the two reports
look like one set: the same three categorical slots, direct labelling rather
than legend swatches wherever a line can carry its own name, and magnitude and
phase as two stacked axes sharing a frequency axis rather than one plot with
two y-scales.

Every figure is drawn from a file the sweeps wrote - rx_sweep.csv,
tx_sweep.csv, rect_sweep.csv, sweeps.json - so a figure cannot show a number
the report does not also state.
"""

import csv
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                             # noqa: E402
import numpy as np                                          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

SERIES = {"a": "#2a78d6", "b": "#eb6834", "c": "#1baf7a", "d": "#8a3324"}
INK, MUTED, GRID = "#1a1a19", "#555555", "#e3e3e0"
A4W = 6.6
MARK = "#8a3324"


def _style(ax, xlabel, ylabel, logx=False, logy=False):
    if logx:
        ax.set_xscale("log")
    if logy:
        ax.set_yscale("log")
    ax.set_xlabel(xlabel, size=8, color=MUTED)
    ax.set_ylabel(ylabel, size=8, color=MUTED)
    ax.tick_params(labelsize=7.5, colors=MUTED, length=3)
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_color(GRID)


def _rows(name):
    with open(os.path.join(HERE, name)) as fh:
        return list(csv.DictReader(fh))


def _f(r, k):
    try:
        return float(r[k])
    except (KeyError, ValueError, TypeError):
        return float("nan")


# --------------------------------------------------------------------------
# The receive coil
# --------------------------------------------------------------------------

def pareto_l_q(rx):
    """Every legal geometry as a point in the L-Q plane, both thicknesses."""
    rows = [r for r in _rows("rx_sweep.csv") if r["topology"] == "series"]
    fig, axes = plt.subplots(1, 2, figsize=(A4W, 2.6))
    for ax, t in zip(axes, ("0.05", "1")):
        sub = [r for r in rows if abs(_f(r, "t_um") - float(t)) < 1e-9]
        l = np.array([_f(r, "l_nh") for r in sub])
        q = np.array([_f(r, "q") for r in sub])
        ax.scatter(l, q, s=0.6, c="#c9d6e8", lw=0, rasterized=True)
        for key, lab, col in (("max_l", "max L", "a"), ("max_q", "max Q", "b"),
                              ("chosen", "chosen", "d")):
            src = (rx["by_thickness"]["1um" if t == "1" else "50nm"]["series"]
                   .get(key if key != "chosen" else "max_emf"))
            if not src:
                continue
            ax.scatter([src["l_nh"]], [src["q"]], s=26, c=SERIES[col],
                       zorder=5, edgecolor="white", lw=0.6)
            ax.annotate(lab, (src["l_nh"], src["q"]), textcoords="offset points",
                        xytext=(5, 4), size=7, color=SERIES[col], weight="bold")
        _style(ax, "L (nH)", "Q at %g kHz" % (rx["f_op_hz"] / 1e3),
               logx=True, logy=True)
        ax.set_title("%s of gold" % ("50 nm" if t == "0.05" else "1 um"),
                     size=8.5, color=INK)
    fig.tight_layout()
    return fig


def l_vs_turns(rx):
    """L and Q against turn count, at the winning track width and gap."""
    ch = rx["chosen"]
    rows = [r for r in _rows("rx_sweep.csv")
            if r["topology"] == "series" and r["shape"] == ch["shape"]
            and abs(_f(r, "w_um") - ch["w_um"]) < 1e-9
            and abs(_f(r, "gap_um") - ch["gap_um"]) < 1e-9
            and abs(_f(r, "t_um") - ch["t_um"]) < 1e-9]
    rows.sort(key=lambda r: _f(r, "n"))
    n = [_f(r, "n") for r in rows]
    fig, ax = plt.subplots(figsize=(A4W, 2.3))
    ax.plot(n, [_f(r, "l_nh") for r in rows], color=SERIES["a"], lw=1.6)
    ax.axvline(ch["n"], color=MARK, lw=1.0, ls="--")
    ax.annotate("chosen, n = %d" % ch["n"],
                (ch["n"], max(_f(r, "l_nh") for r in rows)),
                textcoords="offset points", xytext=(-8, -2), ha="right",
                size=7.5, color=MARK, weight="bold")
    _style(ax, "turns", "L (nH)")
    ax2 = ax.twinx()
    ax2.plot(n, [_f(r, "turn_area_m2") * 1e6 for r in rows], color=SERIES["c"],
             lw=1.6)
    ax2.set_ylabel("total turn area (mm$^2$)", size=8, color=SERIES["c"])
    ax2.tick_params(labelsize=7.5, colors=SERIES["c"], length=3)
    for s in ax2.spines.values():
        s.set_color(GRID)
    ax.annotate("L", (n[len(n) // 2], _f(rows[len(rows) // 2], "l_nh")),
                textcoords="offset points", xytext=(4, 6), size=8,
                color=SERIES["a"], weight="bold")
    fig.tight_layout()
    return fig


def l_r_vs_width(rx):
    """The interior optimum in track width: L falls, R falls faster."""
    ch = rx["chosen"]
    rows = [r for r in _rows("rx_sweep.csv")
            if r["topology"] == "series" and r["shape"] == ch["shape"]
            and abs(_f(r, "gap_um") - ch["gap_um"]) < 1e-9
            and abs(_f(r, "t_um") - ch["t_um"]) < 1e-9]
    best = {}
    for r in rows:
        w = _f(r, "w_um")
        if w not in best or _f(r, "turn_area_m2") > _f(best[w], "turn_area_m2"):
            best[w] = r
    ws = sorted(best)
    fig, ax = plt.subplots(figsize=(A4W, 2.3))
    ax.plot(ws, [_f(best[w], "turn_area_m2") * 1e6 for w in ws],
            color=SERIES["c"], lw=1.6)
    _style(ax, "track width w (um)", "best total turn area (mm$^2$)")
    ax2 = ax.twinx()
    ax2.plot(ws, [_f(best[w], "r_ac") for w in ws], color=SERIES["b"], lw=1.6)
    ax2.set_yscale("log")
    ax2.set_ylabel("R at that geometry (ohm)", size=8, color=SERIES["b"])
    ax2.tick_params(labelsize=7.5, colors=SERIES["b"], length=3)
    for s in ax2.spines.values():
        s.set_color(GRID)
    ax.axvline(ch["w_um"], color=MARK, lw=1.0, ls="--")
    ax.annotate("chosen, w = %g um" % ch["w_um"], (ch["w_um"], 0),
                textcoords="offset points", xytext=(6, 20), size=7.5,
                color=MARK, weight="bold")
    fig.tight_layout()
    return fig


def shape_and_topology(rx):
    """Square against circular, series against parallel rings."""
    ch = rx["chosen"]
    fig, ax = plt.subplots(figsize=(A4W, 2.3))
    for i, (shape, topo, lab) in enumerate(
            (("square", "series", "square spiral"),
             ("circular", "series", "circular spiral"),
             ("square", "parallel", "square rings, parallel"),
             ("circular", "parallel", "circular rings, parallel"))):
        rows = [r for r in _rows("rx_sweep.csv")
                if r["shape"] == shape and r["topology"] == topo
                and abs(_f(r, "w_um") - 5.0) < 1e-9
                and abs(_f(r, "gap_um") - 5.0) < 1e-9
                and abs(_f(r, "t_um") - ch["t_um"]) < 1e-9]
        rows.sort(key=lambda r: _f(r, "n"))
        if not rows:
            continue
        col = SERIES[["a", "b", "c", "d"][i]]
        ax.plot([_f(r, "n") for r in rows], [_f(r, "l_nh") for r in rows],
                color=col, lw=1.6)
        ax.annotate(lab, (_f(rows[-1], "n"), _f(rows[-1], "l_nh")),
                    textcoords="offset points", xytext=(-6, 4), size=7,
                    color=col, weight="bold", ha="right")
    ax.set_yscale("log")
    _style(ax, "turns", "L (nH)")
    fig.tight_layout()
    return fig


def coil_drawing(rx):
    """The chosen coil, to scale, inside its 1000 x 1000 um budget."""
    ch = rx["chosen"]
    w, gap, n = ch["w_um"], ch["gap_um"], ch["n"]
    d_out = ch["d_out_um"]
    fig, ax = plt.subplots(figsize=(A4W * 0.52, A4W * 0.52))
    ax.add_patch(plt.Rectangle((0, 0), d_out, d_out, fill=False,
                               edgecolor=MARK, lw=1.0, ls="--"))
    pitch = w + gap
    for k in range(int(n)):
        off = k * pitch
        side = d_out - 2 * off
        if side <= 0:
            break
        ax.add_patch(plt.Rectangle((off, off), side, side, fill=False,
                                   edgecolor=SERIES["a"], lw=0.7))
    ax.set_xlim(-40, d_out + 40)
    ax.set_ylim(-40, d_out + 40)
    ax.set_aspect("equal")
    _style(ax, "um", "um")
    ax.set_title("%s, n = %d, w = %g um, gap = %g um" % (ch["shape"], n, w, gap),
                 size=8.5, color=INK)
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------
# The transmit coil
# --------------------------------------------------------------------------

def tx_by_gauge(tx):
    """What each wire gauge is worth, and where the practical bounds sit."""
    rows = tx["by_awg"]
    awg = [r["awg"] for r in rows]
    fig, ax = plt.subplots(figsize=(A4W, 2.3))
    ax.plot(awg, [r["emf_per_sqrtw"] for r in rows], color=SERIES["a"], lw=1.6,
            marker="o", ms=3)
    lo, hi = tx["practical_awg_min"], tx["practical_awg_max"]
    ax.axvspan(min(awg) - 0.5, lo - 0.5, color="#f2ede6", zorder=0)
    ax.axvspan(hi + 0.5, max(awg) + 0.5, color="#f2ede6", zorder=0)
    ax.annotate("too thick\nto wind", (min(awg) + 1, max(
        r["emf_per_sqrtw"] for r in rows) * 0.55), size=7, color=MUTED)
    ax.annotate("too fine\nto handle", (hi + 1.5, max(
        r["emf_per_sqrtw"] for r in rows) * 0.55), size=7, color=MUTED)
    ax.axvline(tx["chosen"]["awg"], color=MARK, lw=1.0, ls="--")
    ax.annotate("chosen, AWG %d\n(%.3f mm)" % (tx["chosen"]["awg"],
                                               tx["chosen"]["d_wire_mm"]),
                (tx["chosen"]["awg"], tx["chosen_link"]["emf_per_sqrtw"]),
                textcoords="offset points", xytext=(-64, -22), size=7.5,
                color=MARK, weight="bold")
    _style(ax, "AWG (larger number = thinner wire)", "EMF per sqrt(W)  (V/W$^{1/2}$)")
    fig.tight_layout()
    return fig


def skin_depth_fig(tx):
    """Skin depth against frequency, with each gauge's radius marked."""
    import sys
    sys.path.insert(0, HERE)
    import link as L
    sys.path.insert(0, L.PDK_TOOLS)
    import coil_core as cc
    f = np.logspace(3, 7, 200)
    fig, ax = plt.subplots(figsize=(A4W, 2.3))
    for rho, name, col in ((L.RHO_CU, "copper", "a"), (L.RHO_AU, "gold", "b")):
        d = np.array([cc.skin_depth(rho, x) * 1e6 for x in f])
        ax.plot(f / 1e3, d, color=SERIES[col], lw=1.6)
        ax.annotate(name, (f[40] / 1e3, d[40]), textcoords="offset points",
                    xytext=(4, 4), size=7.5, color=SERIES[col], weight="bold")
    for awg in (18, 26, 36):
        r = cc.awg_to_diameter(awg) / 2 * 1e6
        ax.axhline(r, color=GRID, lw=0.8)
        ax.annotate("AWG %d radius" % awg, (1.2e3 / 1e3, r),
                    textcoords="offset points", xytext=(2, 3), size=6.5,
                    color=MUTED)
    ax.axvline(tx["f_hz"] / 1e3, color=MARK, lw=1.0, ls="--")
    ax.annotate("%.0f kHz" % (tx["f_hz"] / 1e3), (tx["f_hz"] / 1e3, 3),
                textcoords="offset points", xytext=(4, 0), size=7.5,
                color=MARK, weight="bold")
    _style(ax, "frequency (kHz)", "skin depth (um)", logx=True, logy=True)
    fig.tight_layout()
    return fig


def coupling_vs_distance(tx, sw):
    """k from the geometry, and the efficiency ngspice measures at each one."""
    d = tx["distance"]
    fig, ax = plt.subplots(figsize=(A4W, 2.3))
    ax.plot([r["z_mm"] for r in d], [r["k"] for r in d], color=SERIES["a"],
            lw=1.6, marker="o", ms=3)
    _style(ax, "separation (mm)", "coupling k", logy=True)
    ax.annotate("k, from the geometry", (d[2]["z_mm"], d[2]["k"]),
                textcoords="offset points", xytext=(6, 6), size=7.5,
                color=SERIES["a"], weight="bold")
    ax2 = ax.twinx()
    s = sw["distance"]
    ax2.plot([r["z_mm"] for r in s], [r["eta"] for r in s], color=SERIES["b"],
             lw=1.6, marker="s", ms=3)
    ax2.set_yscale("log")
    ax2.set_ylabel("efficiency, measured", size=8, color=SERIES["b"])
    ax2.tick_params(labelsize=7.5, colors=SERIES["b"], length=3)
    for sp in ax2.spines.values():
        sp.set_color(GRID)
    ax2.annotate("eta, from ngspice", (s[3]["z_mm"], s[3]["eta"]),
                 textcoords="offset points", xytext=(6, -14), size=7.5,
                 color=SERIES["b"], weight="bold")
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------
# The rectifier
# --------------------------------------------------------------------------

def _rect_slice(rows, key, fixed):
    sub = [r for r in rows
           if all(abs(_f(r, k) - v) < 1e-6 * max(1.0, abs(v))
                  for k, v in fixed.items())]
    sub.sort(key=lambda r: _f(r, key))
    return sub


def rect_width(rec):
    """The interior optimum in device width: conduction against Cov loading."""
    rows = _rows("rect_sweep.csv")
    sub = _rect_slice(rows, "w_um", {"l_um": 10.0, "ov_um": 5.0,
                                     "rload": 1e5})
    if len(sub) < 3:
        sub = _rect_slice(rows, "w_um", {"ov_um": 5.0})
    fig, ax = plt.subplots(figsize=(A4W, 2.3))
    ax.plot([_f(r, "w_um") / 1e3 for r in sub], [_f(r, "vout") for r in sub],
            color=SERIES["a"], lw=1.6, marker="o", ms=3)
    best = max(sub, key=lambda r: _f(r, "vout"))
    ax.axvline(_f(best, "w_um") / 1e3, color=MARK, lw=1.0, ls="--")
    ax.annotate("best, W = %.0f um" % _f(best, "w_um"),
                (_f(best, "w_um") / 1e3, _f(best, "vout")),
                textcoords="offset points", xytext=(6, -12), size=7.5,
                color=MARK, weight="bold")
    _style(ax, "device width W (mm)", "output voltage (V)", logx=True)
    fig.tight_layout()
    return fig


def rect_length_ov(rec):
    """Channel length and gate overlap, the two other device dimensions."""
    rows = _rows("rect_sweep.csv")
    fig, axes = plt.subplots(1, 2, figsize=(A4W, 2.2))
    for ax, key, lab in ((axes[0], "l_um", "channel length L (um)"),
                         (axes[1], "ov_um", "gate overlap ov (um)")):
        seen, sub = set(), []
        for r in sorted(rows, key=lambda r: _f(r, key)):
            v = _f(r, key)
            if v in seen:
                continue
            same = [x for x in rows if abs(_f(x, key) - v) < 1e-9]
            sub.append(max(same, key=lambda x: _f(x, "vout")))
            seen.add(v)
        ax.plot([_f(r, key) for r in sub], [_f(r, "vout") for r in sub],
                color=SERIES["b"], lw=1.6, marker="o", ms=3)
        _style(ax, lab, "output voltage (V)")
    fig.tight_layout()
    return fig


def rect_corners(rec):
    """The three corners, which differ mostly in threshold."""
    cs = rec["corners"]
    fig, ax = plt.subplots(figsize=(A4W * 0.6, 2.1))
    names = [c["corner"] for c in cs]
    vals = [c["vout"] for c in cs]
    vto = [rec["vto"][c["corner"]] for c in cs]
    bars = ax.bar(names, vals, color=[SERIES["a"], SERIES["b"], SERIES["c"]],
                  width=0.55)
    for b, v, t in zip(bars, vals, vto):
        ax.annotate("%.3f V\nVto %+.2f" % (v, t),
                    (b.get_x() + b.get_width() / 2, v),
                    textcoords="offset points", xytext=(0, 3), size=7,
                    color=MUTED, ha="center")
    _style(ax, "", "output voltage (V)")
    ax.set_ylim(0, max(vals) * 1.35)
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------
# The link, simulated
# --------------------------------------------------------------------------

def ac_response(traces):
    """Magnitude and phase of the receive node, stacked on one frequency axis."""
    f, mag, ph = traces["f"], traces["vrx_mag"], traces["vrx_ph"]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(A4W, 3.0), sharex=True,
                                 gridspec_kw={"height_ratios": [2, 1]})
    a1.plot(f / 1e3, mag, color=SERIES["a"], lw=1.6)
    a1.set_yscale("log")
    _style(a1, "", "|v(rx)| (V per V of drive)", logx=True)
    i = int(np.argmax(mag))
    a1.axvline(f[i] / 1e3, color=MARK, lw=1.0, ls="--")
    a1.annotate("peak %.0f kHz" % (f[i] / 1e3), (f[i] / 1e3, mag[i]),
                textcoords="offset points", xytext=(6, -4), size=7.5,
                color=MARK, weight="bold")
    a2.plot(f / 1e3, ph, color=SERIES["b"], lw=1.6)
    _style(a2, "frequency (kHz)", "phase (deg)", logx=True)
    fig.tight_layout()
    return fig


def transient_trace(traces):
    """One steady-state window: the carrier in, the rectified output out."""
    t, vrx, vout = traces["t"], traces["vrx"], traces["vout"]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(A4W, 3.0), sharex=True)
    a1.plot(t * 1e6, vrx, color=SERIES["a"], lw=1.0)
    _style(a1, "", "v(rx) (V)")
    a2.plot(t * 1e6, vout, color=SERIES["c"], lw=1.4)
    _style(a2, "time (us)", "v(out) (V)")
    a2.annotate("ripple %.1f uV on %.3f V"
                % ((vout.max() - vout.min()) * 1e6, vout.mean()),
                (t[len(t) // 2] * 1e6, vout.mean()),
                textcoords="offset points", xytext=(0, 8), size=7.5,
                color=MUTED, ha="center")
    fig.tight_layout()
    return fig


def eta_vs_frequency(sw):
    """Efficiency across the band, with the transmitter re-tuned at each point."""
    s = sw["frequency"]
    fig, ax = plt.subplots(figsize=(A4W, 2.3))
    ax.plot([r["f_hz"] / 1e3 for r in s], [r["eta"] for r in s],
            color=SERIES["a"], lw=1.6, marker="o", ms=3)
    _style(ax, "frequency (kHz)", "efficiency", logy=True)
    ax2 = ax.twinx()
    ax2.plot([r["f_hz"] / 1e3 for r in s], [r["vout"] for r in s],
             color=SERIES["c"], lw=1.6, ls="--")
    ax2.set_ylabel("output voltage (V)", size=8, color=SERIES["c"])
    ax2.tick_params(labelsize=7.5, colors=SERIES["c"], length=3)
    for sp in ax2.spines.values():
        sp.set_color(GRID)
    ax.annotate("efficiency", (s[3]["f_hz"] / 1e3, s[3]["eta"]),
                textcoords="offset points", xytext=(6, -12), size=7.5,
                color=SERIES["a"], weight="bold")
    ax2.annotate("output", (s[-3]["f_hz"] / 1e3, s[-3]["vout"]),
                 textcoords="offset points", xytext=(-40, 2), size=7.5,
                 color=SERIES["c"], weight="bold")
    fig.tight_layout()
    return fig


def eta_vs_load(sw):
    """Efficiency and output voltage peak at DIFFERENT loads."""
    s = sw["load"]
    fig, ax = plt.subplots(figsize=(A4W, 2.3))
    ax.plot([r["rload"] for r in s], [r["eta"] for r in s], color=SERIES["a"],
            lw=1.6, marker="o", ms=3)
    _style(ax, "load resistance (ohm)", "efficiency", logx=True, logy=True)
    best_e = max(s, key=lambda r: r["eta"])
    ax.axvline(best_e["rload"], color=MARK, lw=1.0, ls="--")
    ax.annotate("max eta\n%.0f k" % (best_e["rload"] / 1e3),
                (best_e["rload"], best_e["eta"]), textcoords="offset points",
                xytext=(-38, -26), size=7.5, color=MARK, weight="bold")
    ax2 = ax.twinx()
    ax2.plot([r["rload"] for r in s], [r["vout"] for r in s], color=SERIES["c"],
             lw=1.6, ls="--")
    ax2.set_ylabel("output voltage (V)", size=8, color=SERIES["c"])
    ax2.tick_params(labelsize=7.5, colors=SERIES["c"], length=3)
    for sp in ax2.spines.values():
        sp.set_color(GRID)
    best_v = max(s, key=lambda r: r["vout"])
    ax2.annotate("max volts at %.0f k" % (best_v["rload"] / 1e3),
                 (best_v["rload"], best_v["vout"]), textcoords="offset points",
                 xytext=(-88, 2), size=7.5, color=SERIES["c"], weight="bold")
    fig.tight_layout()
    return fig


def coupling_capacitor(sw):
    """The experiment: every added capacitor makes it worse, and by how much."""
    fig, ax = plt.subplots(figsize=(A4W, 2.4))
    ref = sw["coupling_ref"]["eta"]
    for key, lab, col in (("cprx", "shunt across the receive coil", "a"),
                          ("ccpl", "shunt at the rectifier input", "b")):
        s = [r for r in sw[key] if r["c_f"] > 1e-15]
        ax.plot([r["c_f"] for r in s], [r["eta"] / ref for r in s],
                color=SERIES[col], lw=1.6, marker="o", ms=3)
        ax.annotate(lab, (s[1]["c_f"], s[1]["eta"] / ref),
                    textcoords="offset points",
                    xytext=(4, -12 if col == "b" else 6), size=7.5,
                    color=SERIES[col], weight="bold")
    ax.axhline(1.0, color=MARK, lw=1.0, ls="--")
    ax.annotate("no capacitor at all", (1e-12, 1.0), textcoords="offset points",
                xytext=(4, 5), size=7.5, color=MARK, weight="bold")
    _style(ax, "added capacitance (F)", "efficiency, relative to none",
           logx=True, logy=True)
    fig.tight_layout()
    return fig
