#!/usr/bin/env python3
"""Figures for the OPAM report.

Palette: the first three categorical slots of the reference theme, validated
with the dataviz validator (light surface) - lightness band, chroma floor, CVD
separation and normal-vision floor all PASS.  The aqua slot warns on contrast
against a white surface, so every series is direct-labelled rather than left to
a legend swatch.

Magnitude and phase are two stacked axes sharing a frequency axis, never one
plot with two y-scales.
"""

import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SERIES = {"best": "#2a78d6", "tt": "#eb6834", "all": "#1baf7a"}
INK, MUTED, GRID = "#1a1a19", "#555555", "#e3e3e0"
A4W = 6.6


def _style(ax, xlabel, ylabel, logx=True):
    if logx:
        ax.set_xscale("log")
    ax.set_xlabel(xlabel, size=8, color=MUTED)
    ax.set_ylabel(ylabel, size=8, color=MUTED)
    ax.tick_params(labelsize=7.5, colors=MUTED, length=3)
    ax.grid(True, which="both", color=GRID, lw=0.5)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)


def bode(curves, title):
    """Magnitude above, phase below, one shared frequency axis."""
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(A4W, 3.6), sharex=True,
                                 gridspec_kw={"height_ratios": [1.35, 1]})
    fig.patch.set_facecolor("white")
    order = [c for c in ("best", "tt", "all") if c in curves]
    for corner, c in curves.items():
        if not c or "ac" not in c or not c["ac"]:
            continue
        f, mag, _, ph = c["ac"]
        a1.plot(f, mag, color=SERIES[corner], lw=1.6, solid_capstyle="round")
        a2.plot(f, ph, color=SERIES[corner], lw=1.6, solid_capstyle="round")
        a1.annotate(corner, (f[-1], mag[-1]), textcoords="offset points",
                    xytext=(-24, 3 + 9 * order.index(corner)), size=7.5,
                    color=SERIES[corner], weight="bold")
    a1.axhline(0, color=MUTED, lw=0.6, ls=":")
    _style(a1, "", "gain (dB)")
    _style(a2, "frequency (Hz)", "phase (deg)")
    fig.tight_layout()
    return fig


def transfer(curves, title):
    fig, ax = plt.subplots(figsize=(A4W, 2.4))
    fig.patch.set_facecolor("white")
    for corner, c in curves.items():
        if not c or "dc" not in c or not c["dc"]:
            continue
        vin, vout = c["dc"]
        ax.plot(vin, vout, color=SERIES[corner], lw=1.6, solid_capstyle="round")
        ax.annotate(corner, (vin[-1], vout[-1]), textcoords="offset points",
                    xytext=(-22, 4), size=7.5, color=SERIES[corner], weight="bold")
    _style(ax, "differential input (V)", "output (V)", logx=False)
    fig.tight_layout()
    return fig


def sine(curve, title):
    """One corner only: the waveform, not a comparison."""
    fig, ax = plt.subplots(figsize=(A4W, 2.2))
    fig.patch.set_facecolor("white")
    t, vout, _, vin = curve["tr"]
    t0 = t[0]
    ts = [(x - t0) * 1e3 for x in t]
    ax.plot(ts, vout, color=SERIES["best"], lw=1.6)
    ax.annotate("output", (ts[len(ts) // 6], vout[len(ts) // 6]),
                textcoords="offset points", xytext=(4, 6), size=7.5,
                color=SERIES["best"], weight="bold")
    _style(ax, "time (ms)", "output (V)", logx=False)
    ax.set_title(title, size=9, color=INK, loc="left", pad=6)
    fig.tight_layout()
    return fig


def bandwidth_vs_field(rows, title, xlabel, ylabel):
    """How far the corner moves as the mobility changes."""
    fig, ax = plt.subplots(figsize=(A4W, 2.4))
    fig.patch.set_facecolor("white")
    x = [r["dmu"] for r in rows]
    y = [r["f3db"] for r in rows]
    ax.plot(x, y, color=SERIES["best"], lw=1.8, marker="o", ms=4,
            markerfacecolor="white", markeredgewidth=1.4)
    # only the endpoints carry a label; the rest would crowd the line
    ax.annotate("%.0f Hz" % rows[0]["f3db"], (rows[0]["dmu"], rows[0]["f3db"]),
                textcoords="offset points", xytext=(8, -4), size=7.5, color=MUTED)
    ax.annotate("%.0f Hz" % rows[-1]["f3db"], (rows[-1]["dmu"], rows[-1]["f3db"]),
                textcoords="offset points", xytext=(-34, 10), size=7.5, color=MUTED)
    ax.set_xlim(-0.05, 1.05)
    _style(ax, xlabel, ylabel, logx=False)
    ax.set_title(title, size=9, color=INK, loc="left", pad=6)
    fig.tight_layout()
    return fig


def probe_sensitivity(rows_by_circuit, title, xlabel, ylabel):
    """Sensitivity against where the probe tone sits on the response."""
    fig, ax = plt.subplots(figsize=(A4W, 2.4))
    fig.patch.set_facecolor("white")
    colors = [SERIES["best"], SERIES["tt"]]
    for (name, rows), col in zip(rows_by_circuit.items(), colors):
        x = list(range(len(rows)))
        y = [abs(r["sens"]) for r in rows]
        ax.plot(x, y, color=col, lw=1.8, marker="o", ms=4,
                markerfacecolor="white", markeredgewidth=1.4)
        ax.annotate(name, (x[-1], y[-1]), textcoords="offset points",
                    xytext=(-30, 6), size=7.5, color=col, weight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([r["tag"] for r in rows], rotation=0)
    _style(ax, xlabel, ylabel, logx=False)
    ax.set_title(title, size=9, color=INK, loc="left", pad=6)
    fig.tight_layout()
    return fig


# one hue per probe frequency, taken in fixed order from the categorical theme
FREQ_SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#4a3aa7"]


def gain_vs_field(series, title, xlabel, ylabel):
    """Gain against relative mobility change, one line per probe frequency.

    Five fixed tones, five hues in the theme's order - never cycled.  Each line
    is labelled at its own right-hand end rather than in a legend box, so the
    identity never rests on colour alone.
    """
    fig, ax = plt.subplots(figsize=(A4W, 3.0))
    fig.patch.set_facecolor("white")
    for (label, entry), col in zip(series.items(), FREQ_SERIES):
        pts = entry["points"]
        x = [p["dmu"] for p in pts]
        y = [p["gain"] for p in pts]
        ax.plot(x, y, color=col, lw=1.8, marker="o", ms=3.5,
                markerfacecolor="white", markeredgewidth=1.2,
                solid_capstyle="round")
        ax.annotate(label, (x[-1], y[-1]), textcoords="offset points",
                    xytext=(6, -2), size=7.5, color=col, weight="bold",
                    va="center")
    ax.axhline(0, color=MUTED, lw=0.6, ls=":")
    _style(ax, xlabel, ylabel, logx=False)
    ax.set_xlim(-0.03, 1.28)
    if title:
        ax.set_title(title, size=9, color=INK, loc="left", pad=6)
    fig.tight_layout()
    return fig


def sine_io(curve, title, xlabel, y_in, y_out):
    """Input and output against time, stacked.

    Two panels sharing the time axis, not one plot with two y-scales: the input
    is under a millivolt and the output is hundreds of millivolts, and forcing
    them onto one scale would hide the input completely.
    """
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(A4W, 3.0), sharex=True,
                                 gridspec_kw={"height_ratios": [1, 1]})
    fig.patch.set_facecolor("white")
    t, vout, _, vin = curve["tr"]
    t0 = t[0]
    ts = [(x - t0) * 1e3 for x in t]
    vin_mv = [v * 1e3 for v in vin]
    a1.plot(ts, vin_mv, color=SERIES["tt"], lw=1.6, solid_capstyle="round")
    a2.plot(ts, vout, color=SERIES["best"], lw=1.6, solid_capstyle="round")
    a1.annotate("input", (ts[len(ts) // 8], vin_mv[len(ts) // 8]),
                textcoords="offset points", xytext=(4, 6), size=7.5,
                color=SERIES["tt"], weight="bold")
    a2.annotate("output", (ts[len(ts) // 8], vout[len(ts) // 8]),
                textcoords="offset points", xytext=(4, 6), size=7.5,
                color=SERIES["best"], weight="bold")
    _style(a1, "", y_in, logx=False)
    _style(a2, xlabel, y_out, logx=False)
    if title:
        a1.set_title(title, size=9, color=INK, loc="left", pad=6)
    fig.tight_layout()
    return fig
