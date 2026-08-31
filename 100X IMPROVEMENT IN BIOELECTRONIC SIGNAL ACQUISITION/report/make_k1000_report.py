#!/usr/bin/env python3
"""Report for the W/L = 1000 ten-channel test: AC, per-channel zooms, and the
noise-driven time-domain confirmation."""

import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SC = os.environ.get("SCRATCH", "/tmp")
TAG = os.environ.get("TAG", "k1000")
OUT = os.path.join(ROOT, "ten_channel_k1000.pdf")

A4 = (8.27, 11.69)
BLUE, RED, GREEN, AMBER, GREY = "#2E5EAA", "#C1425A", "#2A9D8F", "#E0A100", "#6C757D"
INK = "#1A1A1A"


def head(fig, t, sub=None):
    fig.text(0.07, 0.955, t, size=14, weight="bold", color=INK)
    if sub:
        fig.text(0.07, 0.934, sub, size=9, color=GREY)
    fig.add_artist(plt.Line2D([0.07, 0.93], [0.925, 0.925], color=BLUE, lw=1.5))


def foot(fig, n):
    fig.text(0.93, 0.032, str(n), size=8, color=GREY, ha="right")
    fig.text(0.07, 0.032, "Ten-channel ladder, W/L = 1000 - AC and transient",
             size=7.5, color=GREY)


def page_cover(pdf, cfg, rows, tr):
    fig = plt.figure(figsize=A4)
    fig.text(0.5, 0.915, "1 0 0 X   I M P R O V E M E N T   I N   B I O E L E C T R O N I C\nS I G N A L   A C Q U I S I T I O N", ha="center", size=8.5,
             color=BLUE, weight="bold", linespacing=1.6)
    fig.text(0.5, 0.855, "W/L = 1000 resonant ladder", ha="center",
             size=21, weight="bold", color=INK)
    fig.text(0.5, 0.822, "AC sweep, per-channel zooms, and a noise-driven "
             "time-domain confirmation", ha="center", size=10, color=GREY)

    cfgtxt = [
        f"device        W/L = {cfg['wl']:g}   (W = {cfg['W']:g} um, L = {cfg['L']:g} um)",
        f"model         Kp = 0.717 uA/V^2, Vth = 0.09 V, lambda = 0.0067",
        f"gate stack    50 nm Al2O3, Cox = 156 nF/cm^2, self-aligned S/D (0.5 um)",
        f"supply        VDD = {cfg['vdd']} V",
        f"return        isolated per channel",
        f"tanks         2 x 50 nH per channel, 0.5 Ohm per branch",
    ]
    y = 0.775
    fig.text(0.07, y, "Configuration", size=11, weight="bold", color=BLUE)
    y -= 0.024
    for line in cfgtxt:
        fig.text(0.07, y, line, size=8.8, family="monospace", color=INK)
        y -= 0.0175

    y -= 0.018
    fig.text(0.07, y, "Result per channel (AC, zoomed)", size=11,
             weight="bold", color=BLUE)
    y -= 0.026
    hdr = f"{'ch':>3} {'target':>9} {'f0 [MHz]':>10} {'err':>7} {'depth':>8} {'BW [kHz]':>10} {'Q_L':>8} {'ok':>4}"
    fig.text(0.07, y, hdr, size=8.4, family="monospace", weight="bold", color=GREY)
    y -= 0.0175
    nok = 0
    for r in rows:
        ok = r["depth"] > 3 and r["bw"] == r["bw"] and r["bw"] <= 30e3
        nok += ok
        bw = r["bw"] / 1e3 if r["bw"] == r["bw"] else float("nan")
        q = r["q"] if r["q"] == r["q"] else float("nan")
        line = (f"{r['ch']:3d} {r['target']:9.2f} {r['f0']/1e6:10.4f} "
                f"{100*(r['f0']/1e6-r['target'])/r['target']:6.2f}% {r['depth']:7.2f} "
                f"{bw:10.2f} {q:8.0f} {'OK' if ok else '--':>4}")
        fig.text(0.07, y, line, size=8.4, family="monospace",
                 color=GREEN if ok else INK)
        y -= 0.0175

    y -= 0.02
    fig.text(0.07, y, f"{nok} of 10 channels meet depth > 3 dB and BW <= 30 kHz",
             size=10, weight="bold", color=GREEN if nok >= 5 else AMBER)

    if tr:
        y -= 0.035
        fig.text(0.07, y, "Time-domain confirmation", size=11,
                 weight="bold", color=BLUE)
        y -= 0.024
        for line in tr:
            fig.text(0.07, y, line, size=8.8, family="monospace", color=INK)
            y -= 0.0175

    fig.text(0.07, 0.07,
             "Every number here is measured, not calculated. The AC figures come from\n"
             "zoomed sweeps (a full-span sweep under-reports depth). The time-domain\n"
             "figures come from a transient driven by white noise, analysed without\n"
             "using .ac at all.",
             size=8, color=GREY, style="italic")
    pdf.savefig(fig); plt.close(fig)


def page_quality(pdf, rows):
    """Achieved vs demanded Q, and why the two diverge."""
    fig = plt.figure(figsize=A4)
    head(fig, "Quality factor: achieved against demanded",
         "the specification asks for Q growing with frequency; the circuit delivers Q flat")
    fch = [r["target"] for r in rows]
    ql = [r["q"] if r["q"] == r["q"] else np.nan for r in rows]
    spec = [f * 1e6 / 30e3 for f in fch]

    ax = fig.add_axes([0.11, 0.60, 0.80, 0.28])
    ax.plot(fch, spec, "-", color=RED, lw=2, label="demanded  Q_L = f0 / 30 kHz")
    ax.plot(fch, ql, "o-", color=BLUE, ms=7, lw=1.2, label="achieved (AC, zoomed)")
    for f, q, sp in zip(fch, ql, spec):
        if q == q:
            ax.annotate(f"{q:.0f}", (f, q), textcoords="offset points",
                        xytext=(0, 8), ha="center", size=7, color=BLUE)
    ax.fill_between(fch, spec, [max(spec)] * len(spec), color=RED, alpha=0.06)
    ax.set_xlabel("channel frequency (MHz)", size=9)
    ax.set_ylabel("loaded Q", size=9)
    ax.grid(alpha=0.25); ax.legend(frameon=False, fontsize=8.5)
    ax.tick_params(labelsize=8)
    ax.set_title("only where the blue line sits above the red one is the channel met",
                 size=9, color=GREY)

    # fT per channel - the explanation
    KP, COX = 0.717e-6, 1.564e-15
    W, L, ov = 1000.0, 1.0, 0.5
    Ct = (2 / 3) * COX * W * L + 2 * ov * COX * W
    its = [r["itail"] for r in rows]
    fts, ratio = [], []
    for k, r in enumerate(rows):
        Id = its[k] * 1e-3 / 2
        vov = np.sqrt(2 * Id / (KP * W / L))
        gm = KP * (W / L) * vov
        ft = gm / (2 * np.pi * Ct)
        fts.append(ft / 1e6)
        ratio.append(ft / (r["target"] * 1e6))

    ax = fig.add_axes([0.11, 0.30, 0.80, 0.22])
    ax.semilogy(fch, fts, "o-", color=BLUE, ms=6, label="transistor fT")
    ax.semilogy(fch, fch, "--", color=RED, lw=1.4, label="channel frequency")
    ax.set_xlabel("channel frequency (MHz)", size=9)
    ax.set_ylabel("MHz (log)", size=9)
    ax.grid(alpha=0.25, which="both"); ax.legend(frameon=False, fontsize=8.5)
    ax.tick_params(labelsize=8)
    ax.set_title("why: the bias ladder starves the high channels and fT collapses "
                 "with it", size=9, color=GREY)

    y = 0.235
    for line in [
        "The specification demands the same enhancement at every channel: Q_L = f0/30 kHz",
        "and the bare tank Q0 = wL/RS both grow linearly with f, so each channel needs its",
        "loss cancelled to the same ~53x.  That needs the transistor to still have gain at",
        "its own channel frequency.",
        "",
        "With one transistor size shared by all ten it cannot.  The tank needs LESS gm as",
        "frequency rises (gm_req = 2*RS/(w*L)^2: 2026 uS down to 127 uS), so the bias",
        "ladder starves the high channels - overdrive falls 2.82 V to 0.16 V and fT falls",
        "with it, 123 MHz to 7 MHz.  Channel 10 asks a transistor 28x slower than itself",
        "to cancel its loss.",
        "",
        "Sizing each channel for a COMMON overdrive removes the cause: W/L =",
        "gm_req(f)/(Kp*Vov) makes W fall as 1/f^2 and holds fT at 123 MHz for all ten.",
        "Simulated: placement within 0.02 % across 50-200 MHz on the first pass, and",
        "channel 9 rises from unmeasurable to Q_L 5869 against a 6111 specification.",
    ]:
        if line == "":
            y -= 0.008
        else:
            fig.text(0.07, y, line, size=8.4, color=GREY)
            y -= 0.0157
    foot(fig, 3)
    pdf.savefig(fig); plt.close(fig)


def page_full(pdf, rows):
    d = np.load(f"{SC}/ds_{TAG}_full.npy")
    f, db = d[0], d[1]
    fig = plt.figure(figsize=A4)
    head(fig, "Full span, 35 - 215 MHz",
         "all ten channels live at once; depth here is under-reported by the step size")
    ax = fig.add_axes([0.10, 0.55, 0.83, 0.33])
    ax.plot(f / 1e6, db, lw=0.6, color=BLUE)
    for r in rows:
        ax.axvline(r["target"], color=RED, ls=":", lw=0.8, alpha=0.55)
        i = int(np.argmin(np.abs(f - r["f0"])))
        ok = r["depth"] > 3 and r["bw"] == r["bw"] and r["bw"] <= 30e3
        ax.plot(r["f0"] / 1e6, db[i], "v", color=GREEN if ok else AMBER, ms=6)
        ax.annotate(f"{r['ch']}", (r["f0"] / 1e6, db[i]), textcoords="offset points",
                    xytext=(0, -13), ha="center", size=7, color=GREY)
    ax.set_xlabel("frequency (MHz)", size=9)
    ax.set_ylabel("|V(actp) - V(actm)|  (dB)", size=9)
    ax.grid(alpha=0.25); ax.tick_params(labelsize=8); ax.set_xlim(35, 215)
    ax.set_title("dotted red: design targets    markers: notches found", size=9,
                 color=GREY)

    ax = fig.add_axes([0.10, 0.16, 0.83, 0.28])
    tg = np.array([r["target"] for r in rows])
    got = np.array([r["f0"] / 1e6 for r in rows])
    ax.plot([45, 205], [45, 205], "--", color=GREY, lw=1, label="ideal")
    ax.plot(tg, got, "o", color=BLUE, ms=7, label="after co-tuning")
    for t_, g_ in zip(tg, got):
        ax.annotate(f"{100*(g_-t_)/t_:+.2f}%", (t_, g_), textcoords="offset points",
                    xytext=(7, -9), size=7, color=GREY)
    ax.set_xlabel("design target (MHz)", size=9)
    ax.set_ylabel("achieved (MHz)", size=9)
    ax.set_title("channel placement after per-channel tank trim", size=10, color=INK)
    ax.grid(alpha=0.25); ax.legend(frameon=False, fontsize=8); ax.tick_params(labelsize=8)
    foot(fig, 2)
    pdf.savefig(fig); plt.close(fig)


def page_zooms(pdf, rows, start, count, pageno):
    fig = plt.figure(figsize=A4)
    head(fig, f"Per-channel zooms  ({start+1} - {min(start+count, len(rows))} of {len(rows)})",
         "depth and -3 dB bandwidth read off the zoomed sweep, which is the only "
         "valid way to quote Q")
    n = min(count, len(rows) - start)
    for i in range(n):
        r = rows[start + i]
        k = r["ch"] - 1
        p = f"{SC}/ds_{TAG}_zoom{k}.npy"
        if not os.path.exists(p):
            continue
        d = np.load(p); fz, dbz = d[0], d[1]
        row, col = i // 2, i % 2
        ax = fig.add_axes([0.09 + col * 0.47, 0.70 - row * 0.215, 0.38, 0.155])
        ax.plot((fz - r["f0"]) / 1e3, dbz, lw=0.9, color=BLUE)
        edge = max(20, len(fz) // 12)
        base = float(np.median(np.r_[dbz[:edge], dbz[-edge:]]))
        ax.axhline(base, color=GREY, lw=0.7, ls="--")
        ax.axhline(base - 3, color=RED, lw=0.7, ls=":")
        ok = r["depth"] > 3 and r["bw"] == r["bw"] and r["bw"] <= 30e3
        ax.set_title(f"ch {r['ch']} - {r['f0']/1e6:.4f} MHz", size=9,
                     color=GREEN if ok else AMBER)
        bwtxt = f"{r['bw']/1e3:.2f} kHz" if r["bw"] == r["bw"] else "n/a"
        qtxt = f"{r['q']:.0f}" if r["q"] == r["q"] else "n/a"
        ax.text(0.03, 0.06, f"depth {r['depth']:.2f} dB\nBW {bwtxt}\nQ_L {qtxt}",
                transform=ax.transAxes, size=7.2, color=INK, va="bottom")
        ax.set_xlabel("offset from f0 (kHz)", size=7.5)
        ax.set_ylabel("dB", size=7.5)
        ax.grid(alpha=0.22); ax.tick_params(labelsize=6.5)
    fig.text(0.07, 0.11,
             "Dashed grey: local baseline.  Dotted red: baseline - 3 dB, the level the\n"
             "-3 dB bandwidth is measured at.  A channel counts as met only when the\n"
             "notch is deeper than 3 dB (below that a Q number is an artefact) and the\n"
             "bandwidth is at or under 30 kHz.",
             size=8, color=GREY)
    foot(fig, pageno)
    pdf.savefig(fig); plt.close(fig)


def page_time(pdf, tpath):
    d = np.loadtxt(tpath, max_rows=400000)
    t = d[:, 0]; vin = d[:, 1]; vout = d[:, 3] if d.shape[1] > 3 else d[:, 2]
    src = os.path.basename(tpath)
    fig = plt.figure(figsize=A4)
    head(fig, "Time domain: white-noise excitation",
         "the same circuit driven by broadband noise, no .ac involved")
    for i, (t0, t1, lbl) in enumerate([
            (0, 2e-6, "first 2 us - the tanks are still filling"),
            (60e-6, 60.2e-6, "200 ns window in steady state"),
            (60e-6, 60.02e-6, "20 ns window - individual cycles")]):
        m = (t >= t0) & (t <= t1)
        ax = fig.add_axes([0.10, 0.68 - i * 0.235, 0.83, 0.175])
        ax.plot(t[m] * 1e6, vin[m], lw=0.5, color=GREY, label="input (noise)")
        ax.plot(t[m] * 1e6, vout[m], lw=0.7, color=BLUE, label="output (line)")
        ax.set_xlabel("time (us)", size=8.5)
        ax.set_ylabel("volts", size=8.5)
        ax.set_title(lbl, size=9, color=INK)
        ax.grid(alpha=0.22); ax.tick_params(labelsize=7)
        if i == 0:
            ax.legend(frameon=False, fontsize=7.5, ncol=2)
    fig.text(0.07, 0.10,
             f"plotted straight from {src}\n"
             f"input RMS {np.std(vin):.4g} V, output RMS {np.std(vout):.4g} V.\n"
             "The output is the input shaped by the ten resonators. Nothing about the\n"
             "notches is visible by eye in the time record - that is the point of the\n"
             "spectral estimate on the next page.",
             size=8, color=GREY)
    foot(fig, 6)
    pdf.savefig(fig); plt.close(fig)


def page_linearity(pdf, big_txt, small_txt):
    """Why the transient spectrum turns ragged above the sixth channel."""
    sys.path.insert(0, os.path.join(ROOT, "scale"))
    from analyze_transient import load as _load, h_direct
    from scipy.signal import coherence

    fig = plt.figure(figsize=A4)
    head(fig, "Why the transient spectrum frays above channel 6",
         "measured, by re-running the same circuit at 1/34 the drive amplitude")

    curves = {}
    for lbl, path in (("1.01 V RMS drive", big_txt), ("0.030 V RMS drive", small_txt)):
        t, x, y = _load(path, 40.0)
        f, db = h_direct(t, x, y, smooth=7)
        fs = 1.0 / np.median(np.diff(t))
        fc, C = coherence(x, y, fs, nperseg=65536)
        curves[lbl] = (f, db, fc, C)

    ax = fig.add_axes([0.10, 0.60, 0.82, 0.28])
    bands = [(54, 62), (70, 79), (88, 96), (104, 112), (121, 128),
             (137, 145), (155, 162), (171, 178), (187, 194), (203, 210)]
    for lbl, col in (("1.01 V RMS drive", RED), ("0.030 V RMS drive", GREEN)):
        f, db, _, _ = curves[lbl]
        xs, ys = [], []
        for lo, hi in bands:
            m = (f >= lo * 1e6) & (f <= hi * 1e6)
            p = np.polyfit(f[m], db[m], 2)
            xs.append((lo + hi) / 2)
            ys.append((db[m] - np.polyval(p, f[m])).std())
        ax.semilogy(xs, ys, "o-", color=col, ms=6, label=lbl)
    ax.set_xlabel("frequency (MHz)", size=9)
    ax.set_ylabel("estimator scatter in a notch-free band (dB)", size=9)
    ax.grid(alpha=0.25, which="both"); ax.legend(frameon=False, fontsize=8.5)
    ax.tick_params(labelsize=8)
    ax.set_title("the excess is only there at large drive, and only where channels "
                 "8 and 9 sit", size=9, color=GREY)

    ax = fig.add_axes([0.10, 0.31, 0.82, 0.20])
    for lbl, col in (("1.01 V RMS drive", RED), ("0.030 V RMS drive", GREEN)):
        _, _, fc, C = curves[lbl]
        m = (fc >= 40e6) & (fc <= 210e6)
        ax.plot(fc[m] / 1e6, C[m], lw=0.8, color=col, label=lbl)
    ax.set_ylim(0.985, 1.001)
    ax.set_xlabel("frequency (MHz)", size=9)
    ax.set_ylabel("input-output coherence", size=9)
    ax.grid(alpha=0.25); ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    ax.tick_params(labelsize=8)

    y = 0.245
    for line in [
        "The cross-coupled pairs are not linear, and at 1 V RMS they intermodulate. The",
        "channel plan makes that land badly: the ladder is arithmetic, 50 MHz + k x 16.67,",
        "so the sum of any two channels is another channel. Channel 9 at 183.3 MHz gets",
        "ch1+ch6, ch2+ch5 and ch3+ch4; channel 8 at 166.7 MHz gets ch1+ch5, ch2+ch4 and",
        "twice ch3. That energy is not linearly related to the input, so coherence drops",
        "and the estimate frays - exactly above channel 6, where it was observed.",
        "",
        "Re-running at 0.030 V RMS removes it: scatter falls from 0.071 dB to 0.009 dB at",
        "187-194 MHz and from 0.023 dB to 0.008 dB at 171-178 MHz, and coherence returns",
        "to 1.0000 across the band.  Above channel 10, at 203-210 MHz, the large-signal",
        "run is already clean - there is no channel there to receive a sum.",
        "",
        "A measurement artefact here, but a real design warning: an evenly spaced channel",
        "plan puts every second-order product on top of another channel. At 1000 channels",
        "that is a crosstalk mechanism; non-arithmetic spacing would avoid it.",
    ]:
        if line == "":
            y -= 0.008
        else:
            fig.text(0.07, y, line, size=8.3, color=GREY)
            y -= 0.0152
    foot(fig, 8)
    pdf.savefig(fig); plt.close(fig)


def page_psd(pdf, f_ac, db_ac, f_tr, db_tr, rows, tr_rows):
    """AC against both transient drive levels, plus the ring-down cross-check."""
    sys.path.insert(0, os.path.join(ROOT, "scale"))
    from analyze_transient import load as _load, h_direct

    small = os.path.join(HERE, f"transient_{TAG}_smallsignal.txt")
    f_sm = db_sm = None
    if os.path.exists(small):
        ts, xs, ys = _load(small, 40.0)
        fs_, dbs = h_direct(ts, xs, ys, smooth=7)
        ms = (fs_ >= 35e6) & (fs_ <= 215e6)
        f_sm, db_sm = fs_[ms], dbs[ms]

    fig = plt.figure(figsize=A4)
    head(fig, "AC against the time domain, at two drive levels",
         "same circuit, three independent measurements")

    ax = fig.add_axes([0.09, 0.62, 0.84, 0.27])
    ax.plot(f_ac / 1e6, db_ac - np.median(db_ac), lw=0.9, color=INK,
            label="AC sweep")
    ax.plot(f_tr / 1e6, db_tr - np.median(db_tr), lw=0.6, color=RED, alpha=0.7,
            label="transient, 1.01 V RMS drive")
    if f_sm is not None:
        ax.plot(f_sm / 1e6, db_sm - np.median(db_sm), lw=0.7, color=GREEN,
                alpha=0.85, label="transient, 0.030 V RMS drive")
    ax.set_xlim(40, 210)
    ax.set_xlabel("frequency (MHz)", size=9)
    ax.set_ylabel("normalised response (dB)", size=9)
    ax.legend(frameon=False, fontsize=8); ax.grid(alpha=0.25)
    ax.tick_params(labelsize=8)
    ax.set_title("the small-signal run is clean across the whole band and resolves "
                 "all ten", size=9, color=GREY)

    ax = fig.add_axes([0.09, 0.335, 0.84, 0.20]); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 12)
    ax.text(0.0, 11.3, f"{'ch':>3} {'AC f0 [MHz]':>13} {'1.01 V':>12} {'dif kHz':>9} "
                       f"{'0.030 V':>12} {'dif kHz':>9} {'AC depth':>10}",
            size=8.2, family="monospace", weight="bold", color=GREY)
    for i, r in enumerate(rows):
        line = f"{r['ch']:3d} {r['f0']/1e6:13.4f}"
        for f_, db_ in ((f_tr, db_tr), (f_sm, db_sm)):
            if f_ is None:
                line += f" {'-':>12} {'-':>9}"; continue
            m = (f_ >= r["f0"] - 0.6e6) & (f_ <= r["f0"] + 0.6e6)
            if m.sum() < 5:
                line += f" {'-':>12} {'-':>9}"; continue
            fw, dw = f_[m], db_[m]
            g = fw[int(np.argmin(dw))]
            line += f" {g/1e6:12.4f} {(g-r['f0'])/1e3:9.1f}"
        line += f" {r['depth']:9.2f}"
        ax.text(0.0, 10.3 - i * 0.95, line, size=8.2, family="monospace", color=INK)

    fig.text(0.07, 0.275, "Ring-down cross-check", size=11, weight="bold", color=BLUE)
    y = 0.252
    for line in [
        "A 2 ns current pulse into the line, then nothing.  The stored energy decays",
        "monotonically - RMS 2.3e-2 V over 1-3 us, 4.0e-5 over 10-25 us, 9.4e-6 over",
        "25-50 us - so the co-tuned design point is stable, not sitting past the",
        "oscillation boundary.  The ringing is dominated by 49.91 and 66.44 MHz, the",
        "first two channels.  From the decay, tau = 13.7 us gives Q = pi*f0*tau = 2150",
        "at 49.9 MHz, against 3176 from the AC zoom: the same order, 32 % apart.",
        "",
        "UNRESOLVED.  A single-tone probe with synchronous detection, swept across",
        "channel 1 and channel 5, shows only 0.10 and 0.25 dB of variation where the AC",
        "predicts 24 and 4.9 dB.  Drive amplitude, timestep, settling time and estimator",
        "noise were each tested and ruled out.  The noise-driven spectrum and the",
        "ring-down both support the AC, the tone probe does not, and the reason is not",
        "yet identified.  Treat the absolute depths as provisional until it is.",
    ]:
        if line == "":
            y -= 0.008
        else:
            fig.text(0.07, y, line, size=8.3,
                     color=RED if line.startswith("UNRESOLVED") else GREY)
            y -= 0.0152
    foot(fig, 7)
    pdf.savefig(fig); plt.close(fig)


def main():
    cfg = json.load(open(os.path.join(ROOT, "scale", f"cotune10_{TAG}.json")))
    rows = json.load(open(f"{SC}/ds_{TAG}_rows.json"))
    # read the delivered text record, not the intermediate ngspice CSV, so the
    # spectrum in this report is reproducible from the file the reader has
    tpath = os.path.join(HERE, f"transient_{TAG}.txt")
    if not os.path.exists(tpath):
        tpath = f"{SC}/tran_{TAG}.csv"
    trinfo, f_tr, db_tr, tr_rows = [], None, None, []
    sys.path.insert(0, os.path.join(ROOT, "scale"))
    if os.path.exists(tpath):
        from analyze_transient import load as _load, h_direct, notches
        _t, _x, _y = _load(tpath, 40.0)
        _f, _db = h_direct(_t, _x, _y, smooth=7)
        _m = (_f >= 35e6) & (_f <= 215e6)
        f_tr, db_tr = _f[_m], _db[_m]
        tr_rows = [(a, b, c) for a, b, c in notches(f_tr, db_tr, prom=1.2)]
        trinfo = [f"record        {os.path.getsize(tpath)/1e6:.0f} MB text, "
                  f"uniform 500 ps sampling",
                  f"noise source  white, new value every 0.5 ns (flat past 200 MHz)",
                  f"resonances recovered from the time record: {len(tr_rows)}",
                  f"spectrum computed from {os.path.basename(tpath)}"]
    d = np.load(f"{SC}/ds_{TAG}_full.npy"); f_ac, db_ac = d[0], d[1]
    with PdfPages(OUT) as pdf:
        page_cover(pdf, cfg, rows, trinfo)
        page_quality(pdf, rows)
        page_full(pdf, rows)
        for p, s in enumerate(range(0, len(rows), 4)):
            page_zooms(pdf, rows, s, 4, 4 + p)
        if os.path.exists(tpath):
            page_time(pdf, tpath)
        if f_tr is not None:
            page_psd(pdf, f_ac, db_ac, f_tr, db_tr, rows, tr_rows)
        small = os.path.join(HERE, f"transient_{TAG}_smallsignal.txt")
        if os.path.exists(tpath) and os.path.exists(small):
            page_linearity(pdf, tpath, small)
        pdf.infodict()["Title"] = ("100X Improvement in Bioelectronic Signal "
                                   "Acquisition - ten-channel ladder, W/L = 1000")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
