#!/usr/bin/env python3
"""Build the summary PDF of findings (English, publication format)."""

import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "tft"))
from xls_reader import read_xls, sheet_columns  # noqa: E402

OUT = os.path.join(HERE, "device_and_scaling_findings.pdf")
ROOT = os.path.join(HERE, "..")

# ---- simulation results measured in this session (ngspice-46) --------------
LADDER_F = [50.0, 66.6667, 83.3333, 100.0, 116.6667,
            133.3333, 150.0, 166.6667, 183.3333, 200.0]
MODES_SHARED = {
    2: [53.4, 85.0], 3: [57.0, 84.9, 110.0], 4: [59.5, 85.4, 109.7, 134.3],
    6: [62.8, 86.7, 110.1, 133.8, 157.6, 181.9],
    8: [64.7, 87.8, 110.9, 134.2, 157.6, 181.2, 204.9, 229.0],
    10: [65.9, 88.7, 111.7, 134.7, 158.0, 181.3, 204.7, 228.2, 251.9, 275.8],
}
MODES_ISOLATED = {
    2: [48.9, 65.1], 3: [49.1, 65.4, 81.8], 4: [49.2, 65.5, 82.0, 98.4],
    6: [49.3, 65.7, 82.2, 98.6, 115.1, 131.6],
    8: [49.4, 65.8, 82.3, 98.8, 115.2, 131.7, 148.2, 164.6],
    10: [49.4, 65.9, 82.3, 98.8, 115.3, 131.8, 148.3, 164.7, 181.2, 197.6],
}
GM_REQ = {"A (55.89 MHz)": 2019e-6, "B (100.0 MHz)": 808e-6}
GM_MAX_VDD15 = {"long-channel (L>=40 um)": 88.8e-6, "short-channel (L=8 um)": 31.7e-6}

TITLE = "100X Improvement in Bioelectronic Signal Acquisition"
SUB = ("Device and scaling findings: IGZO TFT extraction and N-channel scaling\n"
       "UCLA (Clites / Herman) - UCI (Velez Cuervo / Sanchez)")

C_A, C_B, C_BAD, C_OK, C_GREY = "#2E5EAA", "#D1495B", "#D1495B", "#2A9D8F", "#6C757D"


def page_title(pdf):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.text(0.5, 0.80, TITLE, ha="center", size=19, weight="bold")
    fig.text(0.5, 0.745, SUB, ha="center", size=11, color=C_GREY)
    fig.text(0.5, 0.70, "Generated 2026-08-19 - ngspice-46, closed-loop verified",
             ha="center", size=8.5, color=C_GREY)

    body = [
        ("Headline", None),
        ("The topology is sound and reproduces its verified design point. Two things",
         None),
        ("block it: the shared return destroys the channel plan, and the measured", None),
        ("IGZO TFTs fall 9x-64x short of the required transconductance at 1.5 V.", None),
        ("", None),
        ("1.  Isolated return is a requirement, not an optimisation", "h"),
        ("With the shared return the resonant modes land 27-38 % away from their", None),
        ("design frequencies, and the error grows with channel count. With an", None),
        ("isolated return the error is <= 2.4 % and shrinks with N (1.2 % at N=10).", None),
        ("", None),
        ("2.  The IGZO TFTs are normal devices; the circuit asked for silicon", "h"),
        ("Measured Kp = 0.72 uA/V^2 (best chip, long channel) against 1000 uA/V^2", None),
        ("assumed in every simulation to date - a factor of ~1400. This is not a", None),
        ("fabrication defect: it is what mu*Cox gives for a normal IGZO TFT.", None),
        ("", None),
        ("3.  The wall is the supply voltage, not the current budget", "h"),
        ("At VDD = 1.5 V the transistor cannot pass the needed current at all:", None),
        ("gm saturates at 89 uS (best case) against 808-2019 uS required.", None),
        ("More current does not help - VGS is capped by the supply.", None),
        ("", None),
        ("4.  Contacts, not the semiconductor, limit the short-channel devices", "h"),
        ("Kp is flat at ~0.72 uA/V^2 for L >= 40 um and collapses to 0.13 uA/V^2", None),
        ("at L = 8 um. Linear and saturation extractions agree to 0.5 % on long", None),
        ("channels and diverge to 0.64 on short ones - the contact fingerprint.", None),
        ("2*Rc*W = 6.6e6 Ohm*um (660 Ohm*cm), ~100x worse than good IGZO practice.", None),
        ("", None),
        ("5.  gm required scales with tank loss, and that lever is too small", "h"),
        ("Measured gm_req / RS = 854 uS/Ohm, constant to +-4 % over a 16x range of", None),
        ("RS. Closing a 9x gap this way needs RS = 0.11 Ohm; thin-film inductors go", None),
        ("the other way.", None),
    ]
    y = 0.63
    for txt, kind in body:
        if kind == "h":
            fig.text(0.10, y, txt, size=10.5, weight="bold", color=C_A)
            y -= 0.021
        elif txt == "":
            y -= 0.011
        else:
            w = "bold" if txt == "Headline" else "normal"
            fig.text(0.10, y, txt, size=9.2, weight=w)
            y -= 0.0185
    fig.text(0.10, 0.06,
             "Every number here was measured in this session: the .xls readers were\n"
             "cross-checked against the pre-existing reports (172/172 exact) and the\n"
             "netlist generator reproduces the verified two-channel design point.",
             size=8, color=C_GREY, style="italic")
    pdf.savefig(fig)
    plt.close(fig)


def page_scaling(pdf):
    fig, axes = plt.subplots(2, 1, figsize=(8.27, 11.69))
    fig.suptitle("Phase 1 / 2 - Channel scaling: shared vs isolated return",
                 size=14, weight="bold", y=0.965)

    ax = axes[0]
    for n, col, mk in ((10, C_BAD, "o"),):
        ax.plot(LADDER_F[:n], MODES_SHARED[n], mk, color=C_BAD, ms=7,
                label="shared return (N=10)")
        ax.plot(LADDER_F[:n], MODES_ISOLATED[n], "s", color=C_OK, ms=7,
                label="isolated return (N=10)")
    lim = [40, 290]
    ax.plot(lim, lim, "--", color=C_GREY, lw=1, label="ideal (mode = design)")
    ax.set_xlabel("design target frequency (MHz)")
    ax.set_ylabel("simulated mode frequency (MHz)")
    ax.set_title("Where the modes actually land", size=11)
    ax.legend(frameon=False, fontsize=9)
    ax.grid(alpha=0.25)
    ax.set_xlim(40, 210)

    ax = axes[1]
    ns = sorted(MODES_SHARED)
    for modes, col, lab in ((MODES_SHARED, C_BAD, "shared return"),
                            (MODES_ISOLATED, C_OK, "isolated return")):
        err = [max(abs(modes[n][i] - LADDER_F[i]) / LADDER_F[i] * 100
                   for i in range(n)) for n in ns]
        ax.plot(ns, err, "-o", color=col, label=lab)
    ax.axhline(0, color=C_GREY, lw=0.8)
    ax.set_xlabel("channels populated, N")
    ax.set_ylabel("worst-case frequency error (%)")
    ax.set_title("Placement error vs channel count", size=11)
    ax.legend(frameon=False, fontsize=9)
    ax.grid(alpha=0.25)
    fig.text(0.09, 0.045,
             "Shared return: the N return inductors sit in parallel, so the effective return\n"
             "inductance is (L/2)/N and shrinks as channels are added. The 16.67 MHz design\n"
             "spacing is replaced by a ~23 MHz spacing the designer does not control, and\n"
             "channel 10 lands at 275.8 MHz - outside the 50-200 MHz band entirely.",
             size=8.3, color=C_GREY)
    fig.subplots_adjust(top=0.90, bottom=0.14, hspace=0.30)
    pdf.savefig(fig)
    plt.close(fig)


def page_tft(pdf):
    rows = list(np.load(os.path.join(ROOT, "tft", "params.npy"), allow_pickle=True))
    fig, axes = plt.subplots(2, 1, figsize=(8.27, 11.69))
    fig.suptitle("Phase 5 - IGZO TFT extraction: contact-limited, not material-limited",
                 size=14, weight="bold", y=0.965)

    ax = axes[0]
    for chip, col, mk in (("TFT1", C_A, "o"), ("TFT2", C_BAD, "^"), ("TFT3", C_OK, "s")):
        r = [x for x in rows if x["chip"] == chip]
        if r:
            ax.semilogx([x["L"] for x in r], [x["kp_lin"] * 1e6 for x in r],
                        mk, color=col, ms=5, alpha=0.75, label=chip)
    ax.axhline(0.717, ls="--", color=C_GREY, lw=1)
    ax.text(9, 0.75, "0.72 uA/V^2  intrinsic (long channel)", size=8, color=C_GREY)
    ax.set_xlabel("channel length L (um)")
    ax.set_ylabel("extracted Kp (uA/V$^2$)")
    ax.set_title("Kp collapses below L ~ 40 um: the contacts, not the IGZO", size=11)
    ax.legend(frameon=False, fontsize=9)
    ax.grid(alpha=0.25, which="both")

    ax = axes[1]
    r1 = [x for x in rows if x["chip"] == "TFT1"]
    ax.semilogx([x["L"] for x in r1], [x["kp_lin"] / x["kp_sat"] for x in r1],
                "o", color=C_A, ms=6)
    ax.axhline(1.0, ls="--", color=C_GREY, lw=1)
    ax.set_xlabel("channel length L (um)")
    ax.set_ylabel("Kp(linear) / Kp(saturation)")
    ax.set_ylim(0, 1.6)
    ax.set_title("Two independent extractions agree on long channels, diverge on short",
                 size=11)
    ax.grid(alpha=0.25, which="both")
    fig.text(0.09, 0.045,
             "The linear route (gd = dId/dVDS as VDS -> 0) and the saturation route\n"
             "(sqrt(Isat) vs VGS at VDS = 10 V) agree to 0.5 % for L >= 40 um. Below that the\n"
             "linear route reads low, which is exactly how series contact resistance shows up.\n"
             "Independently: 2*Rc*W = 6.6e6 Ohm*um, contact-limited length L_c ~ 54 um.",
             size=8.3, color=C_GREY)
    fig.subplots_adjust(top=0.90, bottom=0.14, hspace=0.30)
    pdf.savefig(fig)
    plt.close(fig)


def page_gm(pdf):
    fig, axes = plt.subplots(2, 1, figsize=(8.27, 11.69))
    fig.suptitle("Phase 5 - The transconductance gap", size=14, weight="bold", y=0.965)

    ax = axes[0]
    labels = list(GM_REQ) + list(GM_MAX_VDD15)
    vals = list(GM_REQ.values()) + list(GM_MAX_VDD15.values())
    cols = [C_BAD, C_BAD, C_A, C_A]
    bars = ax.barh(range(len(vals)), [v * 1e6 for v in vals], color=cols, alpha=0.85)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(["required: " + labels[0], "required: " + labels[1],
                        "TFT max: " + labels[2], "TFT max: " + labels[3]], size=9)
    ax.set_xscale("log")
    ax.set_xlabel("transconductance (uS, log scale)")
    ax.set_title("What the tank demands vs what the device can give at VDD = 1.5 V",
                 size=11)
    for b, v in zip(bars, vals):
        ax.text(v * 1e6 * 1.1, b.get_y() + b.get_height() / 2,
                f"{v*1e6:.0f} uS", va="center", size=8.5)
    ax.grid(alpha=0.25, axis="x", which="both")
    ax.invert_yaxis()

    ax = axes[1]
    vdd = np.linspace(1, 35, 300)
    for lab, kp, vth, col in (("best case (Kp = 0.72 uA/V$^2$)", 0.717e-6, 0.09, C_A),
                              ("short channel (Kp = 0.13 uA/V$^2$)", 0.128e-6, -1.32, C_GREY)):
        gm = kp * (703 / 8) * (vdd - vth)
        ax.plot(vdd, gm * 1e6, color=col, label=lab)
    for lab, g, col in (("channel A", 2019, C_BAD), ("channel B", 808, "#E8A33D")):
        ax.axhline(g, ls="--", color=col, lw=1.2)
        ax.text(1.5, g * 1.08, f"{lab} needs {g} uS", size=8.5, color=col)
    ax.axvline(1.5, color=C_GREY, lw=1)
    ax.text(1.8, 20, "VDD = 1.5 V", size=8.5, color=C_GREY, rotation=90)
    ax.set_xlabel("supply voltage available to drive the gate (V)")
    ax.set_ylabel("achievable gm (uS)")
    ax.set_title("gm is capped by VGS, so the supply - not the current - is the wall",
                 size=11)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    ax.grid(alpha=0.25)
    fig.text(0.09, 0.045,
             "W = 703 um, L = 8 um: the largest pair that fits half of a 150 x 150 um cell.\n"
             "Channel B would close at VDD ~ 13 V, channel A at ~ 32 V - both far above the\n"
             "1.5 V rail, and the resulting bias current then exceeds the 100 uW/channel\n"
             "budget by three orders of magnitude.",
             size=8.3, color=C_GREY)
    fig.subplots_adjust(top=0.90, bottom=0.14, hspace=0.32)
    pdf.savefig(fig)
    plt.close(fig)


def page_actions(pdf):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.text(0.5, 0.94, "What to do next", ha="center", size=16, weight="bold")

    items = [
        ("Immediate - costs nothing, changes everything", "h"),
        ("Move to the isolated return before any further channel work. Every", None),
        ("downstream phase (co-tuning, AGC, power) gets simpler because the", None),
        ("channels stop moving each other's resonances.", None),
        ("", None),
        ("Decide the supply voltage question", "h"),
        ("IGZO TFTs are normally run at 5-20 V, not 1.5 V. The 1.5 V rail is", None),
        ("inherited from a silicon-CMOS assumption. Either raise the rail (and", None),
        ("re-do the power budget) or accept that this topology needs a different", None),
        ("active device. This is a project-level decision, not a design tweak.", None),
        ("", None),
        ("Fix the contacts before fabricating more devices", "h"),
        ("2*Rc*W = 660 Ohm*cm is ~100x off good IGZO practice. Recovering that", None),
        ("alone lifts short-channel Kp from 0.13 to ~0.72 uA/V^2 - a 5.6x gain in", None),
        ("Kp, i.e. 2.4x in gm, for no area and no power.", None),
        ("", None),
        ("Measure what is missing", "h"),
        ("The VGS/, COX/ and HALL/ folders are empty for all three chips, and the", None),
        ("CAP structure area is not recorded. Without Cox we cannot separate mu", None),
        ("from Cox, and - more urgently - we cannot predict the gate capacitance", None),
        ("that loads the tank at 50-200 MHz. Also record W and L for the devices", None),
        ("in TFT/test/: their transfer sweeps are the best data in the set and", None),
        ("currently cannot be normalised.", None),
        ("", None),
        ("Open question this session could not settle", "h"),
        ("Channel-to-channel interaction could not be measured: AC analysis is", None),
        ("linear and cannot see oscillation, so the bias threshold sweep never", None),
        ("triggers. This needs pole-zero (.pz) or transient analysis. The 9 %", None),
        ("interaction figure in CLAUDE.md should be re-derived that way.", None),
    ]
    y = 0.87
    for txt, kind in items:
        if kind == "h":
            fig.text(0.10, y, txt, size=11, weight="bold", color=C_A)
            y -= 0.024
        elif txt == "":
            y -= 0.013
        else:
            fig.text(0.10, y, txt, size=9.4)
            y -= 0.0195

    fig.text(0.10, 0.18, "Verification performed", size=11, weight="bold", color=C_A)
    for i, t in enumerate([
        "BIFF8 .xls reader vs pre-existing Isat_report.xlsx: 172/172 exact.",
        "Transfer extraction self-consistency at VDS = 0.1 / 0.1 / 1 / 2 V:",
        "    26.4 / 27.0 / 27.1 / 28.4 uA/V^2 (7 % spread over 20x in VDS).",
        "Extracted Vth reproduces the instrument's own VT column.",
        "Netlist generator reproduces the verified two-channel design point:",
        "    A 55.8901 MHz / 35.90 dB / 22.98 kHz / Q_L 2432",
        "    B 100.0021 MHz / 39.69 dB / 13.98 kHz / Q_L 7151",
        "    (documented: 55.890 / 35.9 / 23.2 / 2413 and 100.002 / 39.7 / 13.9 / 7217)",
    ]):
        fig.text(0.10, 0.152 - i * 0.0175, t, size=8.6, color=C_GREY)
    pdf.savefig(fig)
    plt.close(fig)


def main():
    with PdfPages(OUT) as pdf:
        page_title(pdf)
        page_scaling(pdf)
        page_tft(pdf)
        page_gm(pdf)
        page_actions(pdf)
        d = pdf.infodict()
        d["Title"] = TITLE
        d["Author"] = "UCLA-UCI resonant electrophysiology collaboration"
    print("wrote", OUT)


if __name__ == "__main__":
    main()
