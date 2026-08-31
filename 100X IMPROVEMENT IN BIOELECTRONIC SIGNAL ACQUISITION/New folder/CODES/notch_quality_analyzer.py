"""LTSpice notch analyzer with auto-detected sweep structure and PDF report.

Opens a file dialog, parses an LTSpice AC export (with .step parametric
runs, possibly multi-parameter like 'Itail=170u Cp=100f'), and:
  * Auto-detects all swept parameters.
  * Plots ALL curves per signal column.
  * Plots GROUPED views: one subplot per fixed value of each swept
    parameter, with the other parameter(s) shown as the legend.
  * Computes the quality factor of each notch (Q = f0 / BW measured at
    passband - 3 dB).
  * Saves a single PDF report and a CSV table next to the input txt.
"""

from __future__ import annotations

import os
import re
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------
COMPLEX_TOKEN_RE = re.compile(
    r"\(\s*(?P<mag>[-+0-9.eE]+)\s*dB\s*,\s*(?P<phase>[-+0-9.eE]+).*?\)",
    re.IGNORECASE,
)
STEP_HEADER_RE = re.compile(
    r"Step Information:\s*(?P<body>.+?)\s*\(Step:\s*\d+\s*/\s*\d+\s*\)"
)


# ---------------------------------------------------------------------------
# SPICE suffix parsing  ('170u' -> 170e-6, '100f' -> 100e-15, '5Meg' -> 5e6)
# ---------------------------------------------------------------------------
_SI_SUFFIX = {
    "f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "\xb5": 1e-6, "µ": 1e-6,
    "m": 1e-3, "k": 1e3, "g": 1e9, "t": 1e12,
}


def parse_spice_value(s: str) -> float:
    """Parse a SPICE-style number with optional suffix; returns NaN on failure."""
    if s is None:
        return float("nan")
    s = s.strip()
    m = re.match(r"\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)(.*)", s)
    if not m:
        return float("nan")
    try:
        num = float(m.group(1))
    except ValueError:
        return float("nan")
    suf = m.group(2).strip().lower()
    if suf.startswith("meg"):
        return num * 1e6
    if not suf:
        return num
    c = suf[0]
    if c in _SI_SUFFIX:
        return num * _SI_SUFFIX[c]
    # Non-ASCII garbage (corrupted µ) — assume micro
    if ord(c) > 127:
        return num * 1e-6
    return num


# ---------------------------------------------------------------------------
# File parsing
# ---------------------------------------------------------------------------
def pick_file() -> str:
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title="Select LTSpice AC export",
        filetypes=[
            ("Text / AC exports", "*.txt *.csv *.raw *.log *.tsv *.dat"),
            ("All files", "*.*"),
        ],
    )
    root.destroy()
    return path


def parse_complex_token(token: str):
    m = COMPLEX_TOKEN_RE.search(token)
    if not m:
        return None
    try:
        return float(m.group("mag")), float(m.group("phase"))
    except ValueError:
        return None


def parse_step_label(line: str):
    m = STEP_HEADER_RE.search(line)
    return m.group("body").strip() if m else None


def parse_step_params(label: str) -> dict[str, str]:
    """'Itail=170u Cp=100f' -> {'Itail': '170u', 'Cp': '100f'}."""
    out: dict[str, str] = {}
    for tok in label.split():
        if "=" in tok:
            k, _, v = tok.partition("=")
            out[k.strip()] = v.strip()
    return out


def parse_file(path: str):
    with open(path, "r", encoding="latin-1", errors="replace") as f:
        raw_lines = f.read().splitlines()
    lines = [ln.rstrip("\r") for ln in raw_lines if ln.strip()]
    if not lines:
        raise ValueError("File is empty.")

    header = lines[0].split("\t")
    if len(header) < 2:
        raise ValueError(f"Header could not be parsed (tab-separated). Got: {header!r}")
    column_names = header[1:]

    data: dict[str, dict[str, list[tuple[float, float, float]]]] = {
        col: {} for col in column_names
    }
    current_step = "single"

    for ln in lines[1:]:
        if ln.startswith("Step Information"):
            label = parse_step_label(ln)
            current_step = label if label else current_step
            continue
        parts = ln.split("\t")
        if len(parts) < 2:
            continue
        try:
            freq = float(parts[0])
        except ValueError:
            continue
        for i, col in enumerate(column_names, start=1):
            if i >= len(parts):
                continue
            parsed = parse_complex_token(parts[i])
            if parsed is None:
                continue
            mag, ph = parsed
            data[col].setdefault(current_step, []).append((freq, mag, ph))

    out: dict[str, dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]] = {}
    for col, steps in data.items():
        out[col] = {}
        for lab, rows in steps.items():
            if not rows:
                continue
            arr = np.asarray(rows, dtype=float)
            order = np.argsort(arr[:, 0])
            arr = arr[order]
            out[col][lab] = (arr[:, 0], arr[:, 1], arr[:, 2])
    return column_names, out


# ---------------------------------------------------------------------------
# Notch metrics  (Q = f0 / BW at passband - 3 dB)
# ---------------------------------------------------------------------------
def _interp_crossing(f, m, i_lo, i_hi, threshold):
    ml, mh = m[i_lo], m[i_hi]
    if mh == ml:
        return float(f[i_lo])
    t = (threshold - ml) / (mh - ml)
    return float(f[i_lo] + t * (f[i_hi] - f[i_lo]))


def compute_notch_metrics(freq, mag_db):
    n = freq.size
    if n < 5:
        return {"f0_hz": np.nan, "baseline_db": np.nan, "depth_db": np.nan,
                "bw_hz": np.nan, "q": np.nan, "note": "not enough samples"}

    i0 = int(np.argmin(mag_db))
    f0 = float(freq[i0])
    notch_min = float(mag_db[i0])

    n_tail = max(3, n // 10)
    tail = np.concatenate([mag_db[:n_tail], mag_db[-n_tail:]])
    baseline = float(np.median(tail))
    depth = baseline - notch_min
    thr = baseline - 3.0

    fL = fR = float("nan")
    notes: list[str] = []

    if notch_min >= thr:
        notes.append("notch shallower than 3 dB")
    else:
        below = None
        for j in range(i0, -1, -1):
            if mag_db[j] < thr:
                below = j
            else:
                if below is not None:
                    fL = _interp_crossing(freq, mag_db, j, below, thr)
                break
        if below is None or np.isnan(fL):
            notes.append("left -3dB not crossed")
            fL = float("nan")

        below = None
        for j in range(i0, n):
            if mag_db[j] < thr:
                below = j
            else:
                if below is not None:
                    fR = _interp_crossing(freq, mag_db, below, j, thr)
                break
        if below is None or np.isnan(fR):
            notes.append("right -3dB not crossed")
            fR = float("nan")

    if np.isnan(fL) or np.isnan(fR):
        bw = float("nan")
        q = float("nan")
    else:
        bw = fR - fL
        q = f0 / bw if bw > 0 else float("nan")

    return {"f0_hz": f0, "baseline_db": baseline, "depth_db": depth,
            "bw_hz": bw, "q": q, "note": "; ".join(notes)}


# ---------------------------------------------------------------------------
# Sweep-structure analysis
# ---------------------------------------------------------------------------
def analyze_sweep_structure(steps: dict):
    """Return (swept_params_sorted, per_step_params_dict).

    A parameter is 'swept' if it takes more than one distinct value across
    the run. Single-value parameters are silently kept as constants.
    """
    per_step = {lab: parse_step_params(lab) for lab in steps}
    all_params: set[str] = set()
    for d in per_step.values():
        all_params.update(d.keys())
    swept: list[str] = []
    for p in sorted(all_params):
        vals = {per_step[lab].get(p) for lab in steps}
        vals.discard(None)
        if len(vals) > 1:
            swept.append(p)
    return swept, per_step


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------
def _x_scale(f):
    fmax = float(np.max(f))
    if fmax >= 1e9:
        return 1e-9, "Frequency (GHz)"
    if fmax >= 1e6:
        return 1e-6, "Frequency (MHz)"
    if fmax >= 1e3:
        return 1e-3, "Frequency (kHz)"
    return 1.0, "Frequency (Hz)"


def _color_cycle(n):
    if n <= 10:
        return list(plt.get_cmap("tab10").colors)
    if n <= 20:
        return list(plt.get_cmap("tab20").colors)
    return [plt.get_cmap("viridis")(i / max(1, n - 1)) for i in range(n)]


def _legend_for(lab, per_step, params_to_show):
    if not params_to_show:
        return lab
    return ", ".join(f"{p}={per_step[lab].get(p, '?')}" for p in params_to_show)


_QUANTITY_INDEX = {"mag": 1, "phase": 2}
_QUANTITY_LABEL = {"mag": "Magnitude (dB)", "phase": "Phase (deg)"}
_QUANTITY_SHORT = {"mag": "Mag (dB)", "phase": "Phase (deg)"}


def _unwrap_phase(p):
    """Unwrap a phase array (deg) to avoid 360-deg jumps in plots."""
    return np.degrees(np.unwrap(np.radians(p)))


def plot_all_bode(fig, steps, per_step, swept_params):
    """All curves of a column on a 2-axis Bode plot (magnitude + phase)."""
    items = list(steps.items())
    n = len(items)
    colors = _color_cycle(n)
    sample_f = items[0][1][0]
    xs, xl = _x_scale(sample_f)
    show_legend = n <= 12
    lw = 1.2 if n <= 12 else 0.7

    ax_mag, ax_phase = fig.subplots(2, 1, sharex=True,
                                    gridspec_kw={"height_ratios": [2, 1]})

    for i, (lab, (f, m, p)) in enumerate(items):
        leg = _legend_for(lab, per_step, swept_params) if show_legend else None
        ax_mag.plot(f * xs, m, color=colors[i], linewidth=lw, label=leg)
        ax_phase.plot(f * xs, _unwrap_phase(p), color=colors[i], linewidth=lw)

    ax_mag.set_ylabel("Magnitude (dB)")
    ax_mag.grid(True, linestyle=":", alpha=0.6)
    ax_phase.set_ylabel("Phase (deg)")
    ax_phase.set_xlabel(xl)
    ax_phase.grid(True, linestyle=":", alpha=0.6)

    if show_legend:
        ax_mag.legend(fontsize=7, loc="best",
                      title=", ".join(swept_params) if swept_params else None)
    else:
        ax_mag.text(0.99, 0.02, f"{n} curves — color = step order",
                    ha="right", va="bottom", transform=ax_mag.transAxes,
                    fontsize=7, color="gray", style="italic")


def plot_grouped_by(fig, steps, per_step, swept_params, group_param, quantity="mag"):
    """Grid of subplots, one per fixed value of group_param, varying the others.

    quantity: 'mag' for magnitude (dB), 'phase' for phase (deg, unwrapped).
    """
    qidx = _QUANTITY_INDEX[quantity]
    ylabel = _QUANTITY_SHORT[quantity]
    varied = [p for p in swept_params if p != group_param]
    vals = sorted({per_step[lab].get(group_param) for lab in steps
                   if per_step[lab].get(group_param) is not None},
                  key=parse_spice_value)
    n = len(vals)
    if n == 0:
        return
    cols = min(3, n)
    rows = (n + cols - 1) // cols
    axes = fig.subplots(rows, cols, squeeze=False)

    for k, gv in enumerate(vals):
        ax = axes[k // cols][k % cols]
        sub_labels = [lab for lab in steps if per_step[lab].get(group_param) == gv]

        def sort_key(lab):
            return tuple(parse_spice_value(per_step[lab].get(p, "")) for p in varied)
        sub_labels.sort(key=sort_key)

        items = [(lab, steps[lab]) for lab in sub_labels]
        colors = _color_cycle(len(items))
        sample_f = items[0][1][0]
        xs, xl = _x_scale(sample_f)
        for i, (lab, tup) in enumerate(items):
            f = tup[0]
            y = tup[qidx]
            if quantity == "phase":
                y = _unwrap_phase(y)
            leg = _legend_for(lab, per_step, varied) if varied else lab
            ax.plot(f * xs, y, color=colors[i], linewidth=0.9, label=leg)
        ax.set_xlabel(xl, fontsize=8)
        ax.set_ylabel(ylabel, fontsize=8)
        ax.set_title(f"{group_param} = {gv}", fontsize=9, weight="bold")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.tick_params(axis="both", labelsize=7)
        if len(items) <= 10:
            ax.legend(fontsize=6, loc="best",
                      title=", ".join(varied) if varied else None)

    for k in range(n, rows * cols):
        axes[k // cols][k % cols].axis("off")


# ---------------------------------------------------------------------------
# Cross-signal comparison and metrics scans
# ---------------------------------------------------------------------------
def find_act_pas_columns(column_names):
    """Heuristic: locate active vs passive signal columns by name fragments."""
    act = next((c for c in column_names if "act" in c.lower()), None)
    pas = next((c for c in column_names if "pas" in c.lower()), None)
    return act, pas


def compute_metrics_df(steps, per_step, swept):
    """Tidy DataFrame of metrics with one row per step.

    Includes raw-string param columns and numeric '_<param>_num' columns for
    sorting/plotting.
    """
    rows = []
    for lab, (f, m, _) in steps.items():
        met = compute_notch_metrics(f, m)
        row = {p: per_step[lab].get(p, "") for p in swept}
        for p in swept:
            row[f"_{p}_num"] = parse_spice_value(per_step[lab].get(p, ""))
        row["f0_hz"] = met["f0_hz"]
        row["bw_hz"] = met["bw_hz"]
        row["q"] = met["q"]
        row["depth_db"] = met["depth_db"]
        row["baseline_db"] = met["baseline_db"]
        row["note"] = met["note"]
        rows.append(row)
    return pd.DataFrame(rows)


def plot_compare_pas_act(fig, data, per_step_act, swept, group_param,
                         act_col, pas_col):
    """Overlay V(act) (solid) and V(pas) (dashed) per fixed group_param value."""
    varied = [p for p in swept if p != group_param]
    vals = sorted({per_step_act[lab].get(group_param) for lab in data[act_col]
                   if per_step_act[lab].get(group_param) is not None},
                  key=parse_spice_value)
    n = len(vals)
    if n == 0:
        return
    cols = min(3, n)
    rows_g = (n + cols - 1) // cols
    axes = fig.subplots(rows_g, cols, squeeze=False)

    for k, gv in enumerate(vals):
        ax = axes[k // cols][k % cols]
        labels = [lab for lab in data[act_col]
                  if per_step_act[lab].get(group_param) == gv]
        labels.sort(key=lambda lab: tuple(
            parse_spice_value(per_step_act[lab].get(p, "")) for p in varied))
        colors = _color_cycle(len(labels))
        sample_f = data[act_col][labels[0]][0]
        xs, xl = _x_scale(sample_f)
        for i, lab in enumerate(labels):
            f_a, m_a, _ = data[act_col][lab]
            ax.plot(f_a * xs, m_a, color=colors[i], linewidth=1.0,
                    label=_legend_for(lab, per_step_act, varied) if varied else lab)
            if lab in data[pas_col]:
                f_p, m_p, _ = data[pas_col][lab]
                ax.plot(f_p * xs, m_p, color=colors[i], linewidth=1.0,
                        linestyle="--", alpha=0.7)
        ax.set_xlabel(xl, fontsize=8)
        ax.set_ylabel("Mag (dB)", fontsize=8)
        ax.set_title(f"{group_param} = {gv}  (solid={act_col}, dashed={pas_col})",
                     fontsize=8, weight="bold")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.tick_params(axis="both", labelsize=7)
        if len(labels) <= 10:
            ax.legend(fontsize=6, loc="best",
                      title=", ".join(varied) if varied else None)

    for k in range(n, rows_g * cols):
        axes[k // cols][k % cols].axis("off")


def plot_metric_vs_param(ax, df, swept, x_param, y_col, y_label, log_y=False):
    """Plot y_col vs x_param; if other swept params exist, one line per combo."""
    varied = [p for p in swept if p != x_param]
    x_num = f"_{x_param}_num"

    df_clean = df.dropna(subset=[y_col, x_num]).copy()
    if df_clean.empty:
        ax.text(0.5, 0.5, "no valid data", ha="center", va="center",
                transform=ax.transAxes, color="gray")
        ax.set_xlabel(x_param)
        ax.set_ylabel(y_label)
        return

    if not varied:
        sub = df_clean.sort_values(x_num)
        ax.plot(sub[x_num], sub[y_col], "o-", markersize=4)
    else:
        group_keys = [f"_{p}_num" for p in varied]
        for keys, sub in df_clean.groupby(group_keys):
            sub = sub.sort_values(x_num)
            keys_tup = keys if isinstance(keys, tuple) else (keys,)
            first = sub.iloc[0]
            leg = ", ".join(f"{p}={first[p]}" for p in varied)
            ax.plot(sub[x_num], sub[y_col], "o-", markersize=4, label=leg,
                    linewidth=1.0)
        ax.legend(fontsize=6, loc="best", title=", ".join(varied))

    ax.set_xlabel(x_param)
    ax.set_ylabel(y_label)
    if log_y:
        ax.set_yscale("log")
    ax.grid(True, linestyle=":", alpha=0.6, which="both")
    ax.ticklabel_format(axis="x", style="sci", scilimits=(-3, 3))


def plot_quality_heatmap(fig, df, row_param, col_param, q_threshold=1400):
    """Colored cell table: rows=row_param, cols=col_param.

    Red if BW = NaN, yellow if computed, green if Q > q_threshold.
    """
    rvals = sorted({v for v in df[row_param].unique() if v != ""},
                   key=parse_spice_value)
    cvals = sorted({v for v in df[col_param].unique() if v != ""},
                   key=parse_spice_value)
    nr, nc = len(rvals), len(cvals)
    if nr == 0 or nc == 0:
        return

    cell_text = [["" for _ in range(nc)] for _ in range(nr)]
    cell_color = [["#ffffff" for _ in range(nc)] for _ in range(nr)]

    for i, rv in enumerate(rvals):
        for j, cv in enumerate(cvals):
            sub = df[(df[row_param] == rv) & (df[col_param] == cv)]
            if sub.empty:
                cell_text[i][j] = "—"
                cell_color[i][j] = "#e5e7eb"
                continue
            q = sub.iloc[0]["q"]
            bw = sub.iloc[0]["bw_hz"]
            if pd.isna(bw) or pd.isna(q):
                cell_text[i][j] = "no BW"
                cell_color[i][j] = "#fca5a5"  # red
            elif q > q_threshold:
                cell_text[i][j] = f"{q:.0f}"
                cell_color[i][j] = "#86efac"  # green
            else:
                cell_text[i][j] = f"{q:.0f}"
                cell_color[i][j] = "#fde68a"  # yellow

    ax = fig.add_subplot(111)
    ax.axis("off")
    tab = ax.table(cellText=cell_text,
                   rowLabels=[f"{row_param}={v}" for v in rvals],
                   colLabels=[f"{col_param}={v}" for v in cvals],
                   cellColours=cell_color,
                   cellLoc="center", loc="center")
    tab.auto_set_font_size(False)
    tab.set_fontsize(8)
    tab.scale(1.0, 1.6)

    for j in range(nc):
        cell = tab[(0, j)]
        cell.set_facecolor("#1e293b")
        cell.set_text_props(color="white", weight="bold")
    for i in range(1, nr + 1):
        cell = tab[(i, -1)]
        cell.set_facecolor("#1e293b")
        cell.set_text_props(color="white", weight="bold")

    # Legend in the figure
    fig.text(0.5, 0.04,
             f"Red = BW could not be measured    |    "
             f"Yellow = Q computed (Q ≤ {q_threshold})    |    "
             f"Green = Q > {q_threshold}",
             ha="center", fontsize=9, color="#334155")


# ---------------------------------------------------------------------------
# PDF report
# ---------------------------------------------------------------------------
def _make_title_page(pdf, base_name, column_names, total_steps, swept_params_per_col):
    fig = plt.figure(figsize=(8.5, 11))
    fig.text(0.5, 0.88, "LTSpice Notch Quality Report",
             ha="center", fontsize=22, weight="bold")
    fig.text(0.5, 0.83, base_name,
             ha="center", fontsize=13, style="italic", color="#475569")
    fig.text(0.5, 0.76,
             "Auto-detected swept parameters and quality-factor (Q = f0 / BW @ passband-3 dB) analysis",
             ha="center", fontsize=10, color="#334155")

    y = 0.65
    fig.text(0.10, y, "Run summary", fontsize=14, weight="bold", color="#0f172a")
    y -= 0.04
    fig.text(0.10, y, f"Signal columns analyzed: {len(column_names)}", fontsize=10)
    y -= 0.025
    fig.text(0.10, y, f"Total simulation steps   : {total_steps}", fontsize=10)
    y -= 0.04
    for col in column_names:
        sp = swept_params_per_col.get(col, [])
        fig.text(0.10, y, f"  {col}", fontsize=10, family="monospace")
        y -= 0.02
        fig.text(0.13, y,
                 f"swept parameters: {', '.join(sp) if sp else '(no .step sweep)'}",
                 fontsize=9, color="#475569")
        y -= 0.03

    y -= 0.02
    fig.text(0.10, y, "Report contents (per signal column):", fontsize=12, weight="bold")
    y -= 0.03
    for line in ["1. All curves — Bode plot (magnitude + phase)",
                 "2. Magnitude grouped by each swept parameter "
                 "(one subplot per fixed value)",
                 "3. Phase grouped by each swept parameter "
                 "(one subplot per fixed value)",
                 "4. Quality-factor table for that column"]:
        fig.text(0.13, y, line, fontsize=10)
        y -= 0.025

    y -= 0.02
    fig.text(0.10, y, "End of report (extra analyses):", fontsize=12, weight="bold")
    y -= 0.025
    for line in ["A. Cross-signal comparison (act vs pas, if both present)",
                 "B. Q vs each swept parameter (one line per other-param combo)",
                 "C. BW vs each swept parameter",
                 "D. Q heatmap for V(act): rows × columns swept params, colored",
                 "E. Combined quality-factor table across all signals"]:
        fig.text(0.13, y, line, fontsize=10)
        y -= 0.022

    pdf.savefig(fig)
    plt.close(fig)


def _table_pages(pdf, title, df, rows_per_page=32):
    df = df.copy()
    for c in df.columns:
        if df[c].dtype.kind == "f":
            df[c] = df[c].apply(lambda v: f"{v:.4g}" if pd.notna(v) else "")
        else:
            df[c] = df[c].astype(str)

    n = len(df)
    pages = max(1, (n + rows_per_page - 1) // rows_per_page)
    for p in range(pages):
        sub = df.iloc[p * rows_per_page:(p + 1) * rows_per_page]
        fig = plt.figure(figsize=(11, 8.5))  # landscape
        page_title = title + (f"  (page {p + 1}/{pages})" if pages > 1 else "")
        fig.suptitle(page_title, fontsize=13, weight="bold")
        ax = fig.add_subplot(111)
        ax.axis("off")
        tab = ax.table(cellText=sub.values.tolist(),
                       colLabels=list(sub.columns),
                       cellLoc="center", loc="center")
        tab.auto_set_font_size(False)
        tab.set_fontsize(7)
        tab.scale(1.0, 1.25)
        # Header styling
        for j in range(len(sub.columns)):
            cell = tab[(0, j)]
            cell.set_facecolor("#1e293b")
            cell.set_text_props(color="white", weight="bold")
        # Zebra
        for i in range(1, len(sub) + 1):
            if i % 2 == 0:
                for j in range(len(sub.columns)):
                    tab[(i, j)].set_facecolor("#f1f5f9")
        pdf.savefig(fig)
        plt.close(fig)


def build_pdf(pdf_path, column_names, data):
    swept_per_col: dict[str, list[str]] = {}
    per_step_per_col: dict[str, dict] = {}
    for col in column_names:
        steps = data.get(col, {})
        if not steps:
            continue
        sp, ps = analyze_sweep_structure(steps)
        swept_per_col[col] = sp
        per_step_per_col[col] = ps

    total_steps = max((len(data.get(c, {})) for c in column_names), default=0)
    base = os.path.splitext(os.path.basename(pdf_path))[0].replace("_report", "")

    all_metrics_rows: list[dict] = []

    with PdfPages(pdf_path) as pdf:
        _make_title_page(pdf, base, column_names, total_steps, swept_per_col)

        for col in column_names:
            steps = data.get(col, {})
            if not steps:
                continue
            swept = swept_per_col[col]
            per_step = per_step_per_col[col]

            # Section divider
            fig = plt.figure(figsize=(8.5, 11))
            fig.text(0.5, 0.55, f"Signal: {col}",
                     ha="center", fontsize=22, weight="bold")
            fig.text(0.5, 0.50,
                     f"Swept parameters: {', '.join(swept) if swept else '(none)'}",
                     ha="center", fontsize=11, color="#475569")
            fig.text(0.5, 0.46, f"Steps: {len(steps)}",
                     ha="center", fontsize=10, color="#475569")
            pdf.savefig(fig)
            plt.close(fig)

            # 1. All curves — Bode plot (magnitude + phase)
            fig = plt.figure(figsize=(11, 8))
            fig.suptitle(f"{col} — All curves ({len(steps)} steps) — Bode",
                         fontsize=14, weight="bold")
            plot_all_bode(fig, steps, per_step, swept)
            fig.tight_layout(rect=[0, 0, 1, 0.95])
            pdf.savefig(fig)
            plt.close(fig)

            # 2. Grouped views — magnitude page + phase page per swept parameter
            for gp in swept:
                varied = [p for p in swept if p != gp]
                legend_note = (', '.join(varied) if varied else 'step')

                # Magnitude grouped page
                fig = plt.figure(figsize=(11, 8.5))
                fig.suptitle(f"{col} — Magnitude grouped by {gp}"
                             f"  (each subplot fixes {gp}; legend = {legend_note})",
                             fontsize=12, weight="bold")
                plot_grouped_by(fig, steps, per_step, swept, gp, quantity="mag")
                fig.tight_layout(rect=[0, 0, 1, 0.95])
                pdf.savefig(fig)
                plt.close(fig)

                # Phase grouped page
                fig = plt.figure(figsize=(11, 8.5))
                fig.suptitle(f"{col} — Phase grouped by {gp}"
                             f"  (each subplot fixes {gp}; legend = {legend_note})",
                             fontsize=12, weight="bold")
                plot_grouped_by(fig, steps, per_step, swept, gp, quantity="phase")
                fig.tight_layout(rect=[0, 0, 1, 0.95])
                pdf.savefig(fig)
                plt.close(fig)

            # 3. Metrics for this column
            rows: list[dict] = []
            for lab, (f, m, _) in steps.items():
                met = compute_notch_metrics(f, m)
                row = {"Signal": col, "Step": lab}
                for p in swept:
                    row[p] = per_step[lab].get(p, "")
                row.update({
                    "f0 (MHz)": met["f0_hz"] / 1e6 if not np.isnan(met["f0_hz"]) else np.nan,
                    "Baseline (dB)": met["baseline_db"],
                    "Depth (dB)": met["depth_db"],
                    "BW (Hz)": met["bw_hz"],
                    "Q": met["q"],
                    "Note": met["note"],
                })
                rows.append(row)
                all_metrics_rows.append(row)

            df_col = pd.DataFrame(rows).drop(columns=["Step"], errors="ignore")
            _table_pages(pdf, f"{col} — Quality factor table", df_col)

        # =====================================================================
        # SECTION A — Cross-signal comparison (V(act) vs V(pas))
        # =====================================================================
        act_col, pas_col = find_act_pas_columns(column_names)
        if act_col and pas_col and act_col != pas_col \
                and data.get(act_col) and data.get(pas_col):
            swept_act = swept_per_col[act_col]
            per_step_act = per_step_per_col[act_col]

            fig = plt.figure(figsize=(8.5, 11))
            fig.text(0.5, 0.55, "A. Active vs Passive comparison",
                     ha="center", fontsize=20, weight="bold")
            fig.text(0.5, 0.50,
                     f"Solid = {act_col}    Dashed = {pas_col}",
                     ha="center", fontsize=11, color="#475569")
            pdf.savefig(fig); plt.close(fig)

            for gp in swept_act:
                varied = [p for p in swept_act if p != gp]
                fig = plt.figure(figsize=(11, 8.5))
                fig.suptitle(
                    f"A. {act_col} vs {pas_col} — grouped by {gp}"
                    f"  (legend = {', '.join(varied) if varied else 'step'})",
                    fontsize=12, weight="bold")
                plot_compare_pas_act(fig, data, per_step_act, swept_act,
                                     gp, act_col, pas_col)
                fig.tight_layout(rect=[0, 0, 1, 0.95])
                pdf.savefig(fig); plt.close(fig)

        # =====================================================================
        # SECTIONS B & C — Q and BW vs swept parameter, per signal column
        # =====================================================================
        for col in column_names:
            steps = data.get(col, {})
            if not steps:
                continue
            swept = swept_per_col[col]
            if not swept:
                continue
            per_step = per_step_per_col[col]
            df_m = compute_metrics_df(steps, per_step, swept)

            # B. Q vs each swept param
            fig, axes = plt.subplots(1, len(swept), figsize=(5.5 * len(swept), 5),
                                     squeeze=False)
            fig.suptitle(f"B. {col} — Quality factor vs swept parameters",
                         fontsize=13, weight="bold")
            for k, p in enumerate(swept):
                plot_metric_vs_param(axes[0][k], df_m, swept, p,
                                     "q", "Quality factor Q", log_y=False)
                axes[0][k].set_title(f"Q vs {p}", fontsize=10)
            fig.tight_layout(rect=[0, 0, 1, 0.94])
            pdf.savefig(fig); plt.close(fig)

            # C. BW vs each swept param
            fig, axes = plt.subplots(1, len(swept), figsize=(5.5 * len(swept), 5),
                                     squeeze=False)
            fig.suptitle(f"C. {col} — Bandwidth (-3 dB) vs swept parameters",
                         fontsize=13, weight="bold")
            for k, p in enumerate(swept):
                plot_metric_vs_param(axes[0][k], df_m, swept, p,
                                     "bw_hz", "BW (Hz)", log_y=True)
                axes[0][k].set_title(f"BW vs {p}", fontsize=10)
            fig.tight_layout(rect=[0, 0, 1, 0.94])
            pdf.savefig(fig); plt.close(fig)

        # =====================================================================
        # SECTION D — Q heatmap for V(act): rows × cols = first two swept params
        # =====================================================================
        if act_col and data.get(act_col):
            swept_act = swept_per_col[act_col]
            per_step_act = per_step_per_col[act_col]
            if len(swept_act) >= 2:
                df_act = compute_metrics_df(data[act_col], per_step_act, swept_act)
                # Prefer Cp as rows, Itail as columns if both exist; otherwise
                # fall back to the first two swept params.
                row_param = next((p for p in swept_act if "c" in p.lower()),
                                 swept_act[0])
                col_param = next((p for p in swept_act
                                  if p != row_param and "i" in p.lower()),
                                 next(p for p in swept_act if p != row_param))
                fig = plt.figure(figsize=(11, 8.5))
                fig.suptitle(
                    f"D. {act_col} — Q heatmap   "
                    f"(rows = {row_param}, columns = {col_param})",
                    fontsize=13, weight="bold")
                plot_quality_heatmap(fig, df_act, row_param, col_param,
                                     q_threshold=1400)
                pdf.savefig(fig); plt.close(fig)
            elif len(swept_act) == 1:
                # Degenerate case: only one swept param → render as a 1xN heatmap
                df_act = compute_metrics_df(data[act_col], per_step_act, swept_act)
                # Add a dummy row dim
                df_act = df_act.copy()
                df_act["_row_"] = "all"
                fig = plt.figure(figsize=(11, 4))
                fig.suptitle(f"D. {act_col} — Q heatmap (1D)",
                             fontsize=13, weight="bold")
                plot_quality_heatmap(fig, df_act, "_row_", swept_act[0],
                                     q_threshold=1400)
                pdf.savefig(fig); plt.close(fig)

        # =====================================================================
        # SECTION E — Combined table
        # =====================================================================
        if all_metrics_rows:
            df_all = pd.DataFrame(all_metrics_rows).drop(columns=["Step"], errors="ignore")
            _table_pages(pdf, "E. Combined quality-factor table — all signals", df_all)

    return all_metrics_rows


# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
def configure_paper_style():
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "font.family": "serif",
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "axes.grid": True,
        "grid.linestyle": ":",
        "grid.alpha": 0.6,
        "legend.fontsize": 8,
        "legend.frameon": True,
        "legend.framealpha": 0.9,
        "lines.linewidth": 1.2,
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    path = pick_file()
    if not path:
        print("No file selected. Exiting.")
        return 0

    print(f"Reading: {path}")
    try:
        column_names, data = parse_file(path)
    except Exception as exc:
        messagebox.showerror("Parser error", str(exc))
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    configure_paper_style()

    out_dir = os.path.dirname(os.path.abspath(path))
    base_name = os.path.splitext(os.path.basename(path))[0] or "data"
    pdf_path = os.path.join(out_dir, f"{base_name}_report.pdf")
    csv_path = os.path.join(out_dir, f"{base_name}_quality_factor.csv")

    # Detect & report sweep structure on stdout
    print()
    for col in column_names:
        steps = data.get(col, {})
        if not steps:
            print(f"  warning: column {col!r} has no parseable data, skipped.")
            continue
        swept, _ = analyze_sweep_structure(steps)
        print(f"  {col}: {len(steps)} steps, swept params = "
              f"{swept if swept else '(none)'}")

    print(f"\nGenerating PDF report: {pdf_path}")
    all_rows = build_pdf(pdf_path, column_names, data)

    if all_rows:
        pd.DataFrame(all_rows).to_csv(csv_path, index=False)
        print(f"Saved CSV : {csv_path}")
    print(f"Saved PDF : {pdf_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
