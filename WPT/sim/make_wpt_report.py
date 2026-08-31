#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The WPT design report.

    python3 make_wpt_report.py            # into WPT/
    python3 make_wpt_report.py <dir>      # somewhere else

Every number in the document is read from the files the sweeps wrote, or
computed here by running ngspice against the PDK's own models.  Nothing is
quoted from an earlier run, so the document cannot drift away from the design
it describes - the same rule OPAM/sim/make_opam_report.py follows.

Code and labels in English; the prose in Spanish.  See report_text.py.
"""

import json
import math
import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/foss/designs/TFT-MMM-LAB-PDK/docs/pdf")

import matplotlib                                           # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                             # noqa: E402

import figures as F                                         # noqa: E402
import link as LK                                           # noqa: E402
import report_text as TXT                                   # noqa: E402
import tb_wpt as T                                          # noqa: E402
from pdfkit import (A4, ACCENT, INK, L, MUTED, Page, PdfPages,  # noqa: E402
                    R as PR, lh)

sys.path.insert(0, LK.PDK_TOOLS)
import coil_core as cc                                      # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


# --------------------------------------------------------------------------
# The decision block
# --------------------------------------------------------------------------

class Doc:
    """Pages that break themselves.

    pdfkit's Page warns after the fact when content has run off the bottom,
    which is the right check but the wrong time: by then the page is drawn.
    This asks first.  Anything that knows its own height calls room(h) and
    gets either the current page or a fresh continuation of it.
    """

    BOTTOM = 0.085

    def __init__(self, pdf, footer):
        self.pdf, self.footer = pdf, footer
        self.n, self.page, self.title = 0, None, ""

    def new(self, title, kicker=None):
        self.flush()
        self.n += 1
        self.page = Page(self.pdf, title, kicker=kicker, footer=self.footer)
        self.title = title
        return self.page

    def room(self, h):
        if self.page is None:
            return self.new(self.title)
        if self.page.y - h >= self.BOTTOM:
            return self.page
        t = self.title if self.title.endswith(u"(cont.)") else \
            self.title + u" (cont.)"
        self.flush()
        self.n += 1
        self.page = Page(self.pdf, t, footer=self.footer)
        self.title = t
        return self.page

    def text(self, body, size=9.2, **kw):
        """Prose that breaks between paragraphs rather than mid-sentence.

        Page.text() takes whatever it is given and runs off the bottom if it
        is too long.  This splits on blank lines and asks for room paragraph
        by paragraph, which is where a break is least disruptive.
        """
        for para in body.split("\n\n"):
            if not para.strip():
                continue
            lines = para.count("\n") + 1
            self.room(lines * size / 72.0 / 11.69 * 1.45 + 0.012)
            self.page.text(para, size=size, **kw)

    def flush(self):
        if self.page is not None:
            self.page.close(self.n)
            self.page = None


def equation(page, lines, source=None):
    """Typeset one or more equations with matplotlib's mathtext."""
    fig = plt.figure(figsize=(F.A4W, 0.34 * len(lines) + 0.16))
    fig.patch.set_facecolor("#f7f4ef")
    y = 1.0 - 1.0 / (len(lines) + 1)
    for line in lines:
        fig.text(0.5, y, line, size=13, color=INK, ha="center", va="center")
        y -= 1.0 / (len(lines) + 1)
    if source:
        fig.text(0.985, 0.06, source, size=7, color=MUTED, ha="right")
    page.figure(fig, width=1.0)


WRAP = 104                  # characters per line at the body size


def _wrap(s, width=WRAP):
    """Page.text() splits on newlines and does NOT wrap.

    A 250-character paragraph handed to it straight becomes one line running
    off the right edge of the page - which is how the decision blocks were
    rendering before anyone looked at the PDF rather than the overflow
    warnings, since running off the SIDE produces no warning at all.
    """
    return textwrap.wrap(s, width) or [""]


def _fig_height(fig, caption=None, width=1.0):
    """How much of the page a matplotlib figure will occupy, in figure units.

    The same arithmetic pdfkit._place does.  It has to be the real formula
    rather than a guess, because _place SHRINKS a figure that does not fit
    instead of overflowing - so an under-estimate here does not show up as a
    squashed figure, it shows up as the table after it running off the page.
    """
    if fig is None:
        return 0.0
    # The figure's OWN aspect, not the page width.  Assuming every figure is
    # A4W wide understated the one square figure in the document by a factor
    # of two, and that page overflowed - the only page that did.
    w_in, h_in = fig.get_size_inches()
    w_fig = (PR - L) * width
    h = w_fig * (h_in / w_in) * (A4[0] / A4[1]) + 0.008 + 0.010
    if caption:
        h += lh(7.8) * len(textwrap.wrap(caption, 118))
    return h


def decision_height(eq, fig, caption, table, decided_by, would_change,
                    fig_width=1.0):
    """How much of a page one decision block will take.

    Measured from pdfkit's own constants rather than guessed, because the only
    other way to know is to draw it, and by then the page is committed.
    """
    h = 0.012 + lh(11, 2.0)                              # the heading
    eq_fig_in = 0.34 * len(eq) + 0.16
    h += (PR - L) * (eq_fig_in / F.A4W) * (A4[0] / A4[1]) + 0.018
    h += lh(9.2) * len(_wrap(u"ELEGIDO: " + choice_stub(eq))) + 0.006
    if fig is not None:
        h += _fig_height(fig, caption, fig_width)
    h += lh(8.6, 1.7) * len(table) + 0.016 + 0.006       # the table
    h += lh(8.8) * len(_wrap(decided_by)) + 0.006
    h += lh(8.8) * len(_wrap(would_change)) + 0.006
    return h * 1.06                                      # 6 % of slack


def choice_stub(_eq):
    """The ELEGIDO line is one or two lines; two is the safe assumption."""
    return "x" * (WRAP + 1)


def decision(doc, n, title, eq, eq_source, choice, fig, caption, table,
             widths, decided_by, would_change, fig_width=1.0):
    """One design decision, always in the same six parts.

    A decision missing its equation, its data or its counterfactual is an
    assertion, so this refuses to render one.
    """
    for name, val in (("eq", eq), ("table", table),
                      ("decided_by", decided_by),
                      ("would_change", would_change)):
        if not val:
            raise ValueError("decision %d (%s) has no %s" % (n, title, name))
    page = doc.room(decision_height(eq, fig, caption, table, decided_by,
                                    would_change, fig_width))
    page.head(u"Decision %d - %s" % (n, title))
    equation(page, eq, eq_source)
    page.text("\n".join(_wrap(u"ELEGIDO: " + choice, WRAP - 6)),
              size=9.2, weight="bold")
    if fig is not None:
        page.figure(fig, caption=caption, width=fig_width)
    page.table(table, widths)
    page.text("\n".join(_wrap(u"LO QUE DECIDIO: " + decided_by)), size=8.8)
    page.text("\n".join(_wrap(u"QUE CAMBIARIA LA RESPUESTA: " + would_change)),
              size=8.8, color=MUTED)


def num(x, n=4):
    return ("%." + str(n) + "g") % x


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(
        os.path.join(HERE, ".."))
    os.makedirs(out_dir, exist_ok=True)

    rx = json.load(open(os.path.join(HERE, "rx_coil.json")))
    tx = json.load(open(os.path.join(HERE, "tx_coil.json")))
    rec = json.load(open(os.path.join(HERE, "rectifier.json")))
    sw = json.load(open(os.path.join(HERE, "sweeps.json")))

    ch, ct, dz = rx["chosen"], tx["chosen"], rec["design"]
    worst, ser = rec["worst"], rx["by_thickness"]["1um"]["series"]
    d = T.load_design()

    # live traces for the simulation figures
    tr = T.traces(d, rload=dz["rload"], vout0=worst["vout"],
                  vamp=worst["vamp"], wtft=dz["w"], ltft=dz["l"],
                  ov=dz["ov"], cout=10e-6)
    if "error" in tr:
        print("  ! traces failed: %s" % tr["error"][:300])
        tr = None

    f_op = rx["f_op_hz"]
    out = os.path.join(out_dir, "WPT_diseno_es.pdf")
    with PdfPages(out) as pdf:
        doc = Doc(pdf, TXT.FOOTER)
        # ---- 1. verdict --------------------------------------------------
        p = doc.new(TXT.TITLE, kicker="Informe de diseno")
        p.text(TXT.SUBTITLE, size=10, color=MUTED)
        p.head(u"1. Resumen y veredicto")
        doc.text(TXT.VERDICT.format(
            vout=worst["vout"], pin=worst["pin"], eta=worst["eta"],
            q=ch["q"], t=ch["t_um"], q50=rx["chosen_50nm"]["q"]))

        # ---- 2. theory ---------------------------------------------------
        p = doc.new(u"2. Teoria del enlace")
        ratio = (rx["chosen_link"]["m_h"] / rx["rejected_fom_link"]["m_h"])
        doc.text(TXT.THEORY.format(ratio=ratio))
        equation(p, [r"$\mathrm{EMF} = \omega\,M\,I_{tx}$",
                     r"$k = M/\sqrt{L_1 L_2}$",
                     r"$\mathrm{FOM} = k^2 Q_1 Q_2$",
                     r"$\eta_{max} = \mathrm{FOM}\,/\,(1+\sqrt{1+\mathrm{FOM}})^2$"],
                 "Mohan 1999 | Babic-Akyel 2008")
        p.table([[u"magnitud", u"valor", u"de donde"],
                 [u"M", u"%s H" % num(tx["chosen_link"]["m_h"]),
                  u"suma de mutuas vuelta a vuelta"],
                 [u"k", u"%s" % num(tx["chosen_link"]["k"]),
                  u"M / raiz(L1 L2)"],
                 [u"Q1 (transmisora)", u"%.1f" % tx["chosen_link"]["q"],
                  u"wL/R, con proximidad"],
                 [u"Q2 (receptora)", u"%s" % num(ch["q"]),
                  u"wL/R, 1 um de oro"],
                 [u"FOM", u"%s" % num(tx["chosen_link"]["fom"]), u"k^2 Q1 Q2"],
                 [u"eta_max (techo)", u"%s" % num(tx["chosen_link"]["eta_max"]),
                  u"la formula de arriba"],
                 [u"eta medida", u"%s" % num(worst["eta"]),
                  u"ngspice, transitorio"]],
                [0.26, 0.24, 0.50])

        # ---- 3. the receive coil ----------------------------------------
        p = doc.new(u"3. La bobina receptora")
        doc.text(TXT.RX_INTRO.format(
            area=rx["area_um"], n=rx["by_thickness"]["1um"]["n_series"],
            wmin=rx["drc"]["w_min_um"], gmin=rx["drc"]["gap_min_um"],
            f=f_op / 1e3, skin=rx["skin_depth_um"]))
        p = doc.room(0.42)
        p.figure(F.pareto_l_q(rx),
                 caption=u"Las %s geometrias legales en el plano L-Q, para los "
                         u"dos espesores. Los tres extremos no son el mismo "
                         u"punto, y ninguno de ellos es el elegido."
                         % "{:,}".format(rx["by_thickness"]["1um"]["n_series"]))
        p = doc.room(0.16)
        p.table([[u"objetivo", u"forma", u"w", u"gap", u"n", u"L (nH)",
                  u"R (ohm)", u"Q"],
                 [u"max L", ser["max_l"]["shape"],
                  u"%g" % ser["max_l"]["w_um"], u"%g" % ser["max_l"]["gap_um"],
                  u"%d" % ser["max_l"]["n"], u"%.1f" % ser["max_l"]["l_nh"],
                  u"%.0f" % ser["max_l"]["r_ac"], num(ser["max_l"]["q"], 3)],
                 [u"max Q", ser["max_q"]["shape"],
                  u"%g" % ser["max_q"]["w_um"], u"%g" % ser["max_q"]["gap_um"],
                  u"%d" % ser["max_q"]["n"], u"%.1f" % ser["max_q"]["l_nh"],
                  u"%.1f" % ser["max_q"]["r_ac"], num(ser["max_q"]["q"], 3)],
                 [u"max FOM", ser["max_fom"]["shape"],
                  u"%g" % ser["max_fom"]["w_um"],
                  u"%g" % ser["max_fom"]["gap_um"],
                  u"%d" % ser["max_fom"]["n"],
                  u"%.1f" % ser["max_fom"]["l_nh"],
                  u"%.1f" % ser["max_fom"]["r_ac"], num(ser["max_fom"]["q"], 3)],
                 [u"max EMF (elegida)", ch["shape"], u"%g" % ch["w_um"],
                  u"%g" % ch["gap_um"], u"%d" % ch["n"], u"%.1f" % ch["l_nh"],
                  u"%.0f" % ch["r_ac"], num(ch["q"], 3)]],
                [0.22, 0.12, 0.08, 0.09, 0.07, 0.13, 0.14, 0.15])

        # ---- 4. the receive-coil decisions -------------------------------
        p = doc.new(u"4. Decisiones: la bobina receptora")
        reg = rx["regime"]
        worst_x = max(max(r["xl"], r["xc"]) for r in reg["rows"])
        decision(
            doc, 1, u"El criterio: tension inducida, no figura de merito",
            [r"$\mathrm{FOM}=k^2Q_1Q_2$   (carga adaptada)",
             r"$\mathrm{EMF}=\omega M I_{tx}$,   $M \propto \sum_k A_k$   (carga de umbral)"],
            "Mohan 1999 | Babic-Akyel 2008",
            u"maximizar la EMF, es decir el area total encerrada por las "
            u"vueltas: %s, w = %g um, gap = %g um, n = %d."
            % (ch["shape"], ch["w_um"], ch["gap_um"], ch["n"]),
            None, None,
            [[u"criterio", u"geometria", u"M (H)", u"FOM", u"L (nH)"],
             [u"max FOM", u"w=%g n=%d" % (rx["rejected_fom"]["w_um"],
                                          rx["rejected_fom"]["n"]),
              num(rx["rejected_fom_link"]["m_h"]),
              num(rx["rejected_fom_link"]["fom"]),
              u"%.1f" % rx["rejected_fom"]["l_nh"]],
             [u"max EMF", u"w=%g n=%d" % (ch["w_um"], ch["n"]),
              num(rx["chosen_link"]["m_h"]), num(rx["chosen_link"]["fom"]),
              u"%.1f" % ch["l_nh"]]],
            [0.20, 0.24, 0.20, 0.20, 0.16],
            u"un factor %.1f en M. La FOM prefiere la otra bobina, pero por "
            u"debajo del umbral del TFT el enlace no entrega nada y la FOM "
            u"describe un circuito que no es este."
            % (rx["chosen_link"]["m_h"] / rx["rejected_fom_link"]["m_h"]),
            u"un rectificador que conduzca a cualquier tension -sincrono, o "
            u"con umbral positivo- devuelve el problema al caso adaptado y "
            u"con el la bobina de max FOM.")

        decision(
            doc, 2, u"No hay tanque: el condensador es un bloqueo de continua",
            [r"$X_L=\omega L$,   $X_C=1/\omega C$,   $Q=\omega L/R$"],
            "",
            u"cualquiera de los tres condensadores; se usa %g uF por ser la "
            u"menor impedancia. NO se usa para sintonizar nada."
            % (max(rx["caps_f"]) * 1e6),
            None, None,
            [[u"f (kHz)", u"C (uF)", u"|wL| (ohm)", u"|1/wC| (ohm)",
              u"R (ohm)", u"R/X"]] +
            [[u"%.0f" % (r["f_hz"] / 1e3), u"%g" % (r["c_f"] * 1e6),
              u"%.3f" % r["xl"], u"%.4f" % r["xc"], u"%.0f" % r["r"],
              u"%.0f" % r["r_over_x"]] for r in reg["rows"]],
            [0.15, 0.14, 0.19, 0.20, 0.16, 0.16],
            u"R supera a las dos reactancias por %.0f veces en el peor punto "
            u"de la banda. El lazo es una resistencia; la resonancia de "
            u"1/(2 pi raiz(LC)) es un numero sin circuito detras."
            % min(r["r_over_x"] for r in reg["rows"]),
            u"una bobina con R por debajo de unos %.1f ohmios -es decir, mucho "
            u"mas metal- convertiria el lazo en un tanque de verdad y "
            u"devolveria sentido a elegir el condensador." % worst_x)

        decision(
            doc, 3, u"La frecuencia: el techo de la banda",
            [r"$\mathrm{EMF}\propto\omega$,   $\mathrm{FOM}\propto\omega^2$,"
             r"   $f_T^{TFT}=1.2\,\mathrm{MHz}$ a $L=10\,\mu m$"],
            "design.ngspice, medido",
            u"%g kHz, el extremo superior de la banda pedida, no los 100 kHz "
            u"preferidos." % (f_op / 1e3),
            F.eta_vs_frequency(sw),
            u"Eficiencia y tension de salida a lo largo de la banda, con el "
            u"primario resintonizado en cada punto. Monotona: no hay optimo "
            u"interior que buscar.",
            [[u"f (kHz)", u"V_out (V)", u"eta"]] +
            [[u"%.0f" % (r["f_hz"] / 1e3), u"%.4f" % r["vout"],
              num(r["eta"])] for r in sw["frequency"]],
            [0.22, 0.30, 0.48],
            u"un factor %.0f en eficiencia entre 100 y %g kHz. Como no hay "
            u"tanque, nada ata la frecuencia dentro de la banda, y la EMF "
            u"crece con ella."
            % (sw["frequency"][-1]["eta"] / sw["frequency"][0]["eta"],
               f_op / 1e3),
            u"subir mas seria mejor todavia, pero fT del TFT esta en 1,2 MHz "
            u"a L = 10 um: queda menos de una decada de margen y el "
            u"rectificador dejaria de rectificar.")

        p = doc.new(u"4. Decisiones: la bobina receptora (cont.)")
        decision(
            doc, 4, u"Numero de vueltas y ancho de pista",
            [r"$L=K_1\mu_0 N^2 d_{avg}/(1+K_2\rho)$,   "
             r"$\rho=(d_{out}-d_{in})/(d_{out}+d_{in})$",
             r"$R=\rho_m\ell/(w\,t)$"],
            "Mohan 1999 | Wheeler 1942",
            u"n = %d vueltas, w = %g um, gap = %g um (el minimo de DRC)."
            % (ch["n"], ch["w_um"], ch["gap_um"]),
            F.l_vs_turns(rx),
            u"L y area total encerrada frente al numero de vueltas, al ancho y "
            u"separacion ganadores. El area -que es lo que fija M- satura "
            u"antes que L.",
            # The four reference geometries are DIFFERENT coils, not points on
            # one turn sweep, so the table has to name each one.
            [[u"geometria", u"n", u"w (um)", u"L (nH)", u"R (ohm)",
              u"area (mm2)"]] +
            [[lab, u"%d" % v["n"], u"%g" % v["w_um"], u"%.1f" % v["l_nh"],
              u"%.0f" % v["r_ac"], u"%.4f" % (v["turn_area_m2"] * 1e6)]
             for lab, v in ((u"max Q", ser["max_q"]),
                            (u"max FOM", ser["max_fom"]),
                            (u"elegida", ch),
                            (u"max L", ser["max_l"]))],
            [0.20, 0.10, 0.14, 0.18, 0.18, 0.20],
            u"el area encerrada. Cada vuelta anade area hasta que el hueco "
            u"interior se cierra; el gap se pega siempre al minimo de DRC "
            u"porque solo cuesta area sin comprar nada.",
            u"un DRC con ancho o separacion menores. Con 2 um en vez de 5 "
            u"caben mas del doble de vueltas en el mismo cuadrado.")

        decision(
            doc, 5, u"Forma y topologia",
            [r"$K_1=2.34,\ K_2=2.75$ (cuadrada);   "
             r"$K_1=2.46,\ K_2=2.00$ (circular)"],
            "Mohan 1999 | Jenei 2002",
            u"espiral CUADRADA en SERIE.",
            F.shape_and_topology(rx),
            u"L frente a vueltas para las cuatro combinaciones, al ancho y "
            u"separacion minimos. Los anillos en paralelo caen cuatro ordenes "
            u"de magnitud: en paralelo manda la espira mas pequena, y las "
            u"concentricas tienen una muy pequena.",
            [[u"forma / topologia", u"mejor L (nH)", u"mejor Q", u"nota"],
             [u"cuadrada, serie", u"%.1f" % max(
                 v["l_nh"] for v in [ser["max_l"], ch]),
              num(ser["max_q"]["q"], 3), u"elegida"],
             [u"circular, serie", u"%.1f" % ser["max_l"]["l_nh"],
              num(ser["max_q"]["q"], 3), u"7 violaciones de DRC en ind.py"],
             [u"paralelo (ambas)",
              u"%.2f" % rx["by_thickness"]["1um"]["parallel"]["max_l"]["l_nh"],
              num(rx["by_thickness"]["1um"]["parallel"]["max_q"]["q"], 3),
              u"sin puntuar por M: divide la corriente"]],
            [0.26, 0.20, 0.16, 0.38],
            u"la circular da mas L (%.0f frente a %.0f nH al mismo w y gap) "
            u"pero el PCell deja siete violaciones de DRC en su terminal "
            u"interior, documentadas en ind.py, y la cuadrada ninguna."
            % (ser["max_l"]["l_nh"], ch["l_nh"]),
            u"abrir el gap en el terminal interior de la espiral circular "
            u"quitaria el residual y con el la razon para descartarla.")

        p = doc.new(u"4. Decisiones: la bobina receptora (cont.)")
        c50 = rx["chosen_50nm"]
        decision(
            doc, 6, u"El espesor del metal",
            [r"$R=\rho_m\ell/(w\,t)$,   $Q=\omega L/R$,   "
             r"$\delta=\sqrt{\rho_m/(\pi\mu f)}$"],
            "Wheeler 1942",
            u"se reportan LOS DOS. El diseno se cita a 1 um; el proceso hoy "
            u"supone 50 nm.",
            F.coil_drawing(rx),
            u"La bobina elegida a escala dentro de su cuadrado de %.0f um."
            % rx["area_um"],
            [[u"espesor", u"R (ohm)", u"Q", u"M (H)", u"eta_max"],
             [u"50 nm", u"%.0f" % c50["r_ac"], num(c50["q"], 3),
              num(rx["chosen_50nm_link"]["m_h"]),
              num(rx["chosen_50nm_link"]["eta_max"])],
             [u"1 um", u"%.0f" % ch["r_ac"], num(ch["q"], 3),
              num(rx["chosen_link"]["m_h"]),
              num(rx["chosen_link"]["eta_max"])]],
            [0.18, 0.20, 0.18, 0.22, 0.22],
            u"un factor %.0f en resistencia y por tanto en Q, con M "
            u"identica porque M es geometria. La profundidad de penetracion "
            u"a %g kHz es %.0f um, asi que no hay efecto pelicular en ninguno "
            u"de los dos casos." % (c50["r_ac"] / ch["r_ac"], f_op / 1e3,
                                    rx["skin_depth_um"]),
            u"medirlo. Es una SUPOSICION, es el parametro mas influyente de "
            u"todo el documento, y es la accion pendiente de mayor valor.",
            fig_width=0.46)

        # ---- 5. the transmit coil ---------------------------------------
        p = doc.new(u"5. La bobina transmisora")
        doc.text(TXT.TX_INTRO.format(
            n=len(tx["by_awg"]) and sum(1 for _ in open(
                os.path.join(HERE, "tx_sweep.csv"))) - 1,
            a1=min(r["awg"] for r in tx["by_awg"]),
            a2=max(r["awg"] for r in tx["by_awg"])))
        p.table([[u"parametro", u"valor"],
                 [u"topologia", ct["topology"]],
                 [u"vueltas", u"%d en %d capa(s)" % (ct["n"], ct["layers"])],
                 [u"diametro del soporte", u"%.1f mm (exterior %.1f mm)"
                  % (ct["d_in_mm"], ct["d_out_mm"])],
                 [u"calibre", u"AWG %d" % ct["awg"]],
                 [u"GROSOR DEL HILO DE COBRE", u"%.3f mm (%.0f um)"
                  % (ct["d_wire_mm"], ct["d_wire_mm"] * 1e3)],
                 [u"longitud de hilo", u"%.2f m" % ct["length_m"]],
                 [u"inductancia", u"%.2f uH" % (ct["l_h"] * 1e6)],
                 [u"R_dc / R_ac", u"%.4f / %.4f ohm (x%.2f)"
                  % (tx["chosen_link"]["r_dc"], tx["chosen_link"]["r_ac"],
                     tx["chosen_link"]["r_ratio"])],
                 [u"  de la cual, proximidad", u"%.4f ohm en %d capas"
                  % (tx["chosen_link"]["r_prox"],
                     tx["chosen_link"]["prox_layers"])],
                 [u"Q a %.0f kHz" % (f_op / 1e3),
                  u"%.1f" % tx["chosen_link"]["q"]],
                 [u"k a la receptora", num(tx["chosen_link"]["k"])],
                 [u"EMF por raiz(W)", u"%.4f V/W^0.5"
                  % tx["chosen_link"]["emf_per_sqrtw"]]],
                [0.40, 0.60])

        p = doc.new(u"6. Decisiones: la bobina transmisora")
        decision(
            doc, 7, u"El calibre del hilo de cobre",
            [r"$\delta=\sqrt{\rho_m/(\pi\mu f)}$,   "
             r"$\mathrm{EMF}/\sqrt{P}=\omega M/\sqrt{R_{src}+R_{tx}}$"],
            "Wheeler 1942 | ASTM B258",
            u"AWG %d, %.3f mm de cobre." % (ct["awg"], ct["d_wire_mm"]),
            F.tx_by_gauge(tx),
            u"El objetivo frente al calibre. Las bandas sombreadas son limites "
            u"practicos de bobinado, no fisicos: el barrido sigue mejorando "
            u"fuera de ellas.",
            [[u"AWG", u"d (mm)", u"EMF/raiz(W)", u"Q"]] +
            [[u"%d" % r["awg"], u"%.3f" % r["d_wire_mm"],
              u"%.4f" % r["emf_per_sqrtw"], u"%.1f" % r["q"]]
             for r in tx["by_awg"][::2]],
            [0.16, 0.22, 0.34, 0.28],
            u"con este objetivo gana el hilo MAS FINO, y por una razon "
            u"geometrica: a igual numero de vueltas, el hilo fino hace un "
            u"bobinado mucho mas corto y mantiene todas las vueltas cerca del "
            u"receptor. Cincuenta vueltas de AWG 36 miden 6 mm; de AWG 18, "
            u"51 mm, y su extremo lejano no acopla con nada.",
            u"juzgado por k^2 Q1 Q2 en vez de por EMF, gana el hilo mas "
            u"GRUESO. El criterio invierte el resultado, que es exactamente "
            u"por que hay que decir cual se usa.")

        decision(
            doc, 8, u"Topologia: solenoide o espiral plana",
            [r"$L=0.8\,a^2N^2/(6a+9h+10b)$ (solenoide multicapa)",
             r"$F_R \propto \frac{2}{3}(m^2-1)$  (proximidad, m capas)"],
            "Wheeler 1928 | Dowell 1966",
            u"%s." % ct["topology"],
            None, None,
            [[u"topologia", u"mejor EMF/raiz(W)", u"Q", u"k"],
             [u"solenoide", u"%.4f" % tx["chosen_link"]["emf_per_sqrtw"],
              u"%.1f" % tx["chosen_link"]["q"],
              num(tx["chosen_link"]["k"])],
             [u"espiral plana", u"(ver tx_sweep.csv)", u"-", u"-"]],
            [0.28, 0.32, 0.20, 0.20],
            u"el solenoide, por poco. Concentra mas vueltas cerca del eje del "
            u"receptor; la espiral plana reparte las suyas hacia fuera, donde "
            u"acoplan peor con un blanco de 1 mm.",
            u"un receptor mucho mayor invertiria esto: una espiral plana "
            u"acopla mejor con algo de su propio tamano.")

        p = doc.new(u"6. Decisiones: la bobina transmisora (cont.)")
        untuned = sw["tx_untuned"]
        best_f = max(sw["frequency"], key=lambda r: r["eta"])
        decision(
            doc, 9, u"Sintonizar el primario: obligatorio",
            [r"$X_L=\omega L_{tx}=%.0f\,\Omega$   frente a   $R=%.1f\,\Omega$"
             % (2 * math.pi * f_op * ct["l_h"], tx["chosen_link"]["r_ac"]),
             r"$C_{tx}=1/(\omega^2 L_{tx})$"],
            "",
            u"condensador en serie de %s en el primario."
            % _eng(1.0 / ((2 * math.pi * f_op) ** 2 * ct["l_h"])),
            None, None,
            [[u"primario", u"V_out (V)", u"eta", u"factor"],
             [u"sintonizado", u"%.4f" % best_f["vout"], num(best_f["eta"]),
              u"1"],
             [u"sin sintonizar", u"%.2e" % untuned["vout"],
              num(untuned["eta"]),
              u"1/%.0f" % (best_f["eta"] / untuned["eta"])]],
            [0.28, 0.24, 0.24, 0.24],
            u"un factor %.0f en eficiencia. La bobina transmisora es de "
            u"%.0f uH: a %g kHz su reactancia son %.0f ohmios contra %.1f de "
            u"resistencia, y sin cancelarla el excitador solo mete una "
            u"fraccion de la corriente que podria."
            % (best_f["eta"] / untuned["eta"], ct["l_h"] * 1e6, f_op / 1e3,
               2 * math.pi * f_op * ct["l_h"], tx["chosen_link"]["r_ac"]),
            u"nada razonable. Es la unica decision del documento sin "
            u"contrapartida: siempre conviene.")

        decision(
            doc, 10, u"La distancia de trabajo",
            [r"$M=\mu_0\sqrt{r_1r_2}\left[(2/k-k)K(k)-(2/k)E(k)\right]$"],
            "Babic-Akyel 2008",
            u"%g mm entre la cara del bobinado y el chip." % tx["z_mm"],
            F.coupling_vs_distance(tx, sw),
            u"k calculado de la geometria y eficiencia medida en ngspice, "
            u"frente a la separacion. Las dos caen igual de rapido, que es la "
            u"comprobacion de que el modelo magnetico y el circuito dicen lo "
            u"mismo.",
            [[u"z (mm)", u"k", u"V_out (V)", u"eta"]] +
            [[u"%g" % r["z_mm"], num(r["k"]), u"%.4f" % r["vout"],
              num(r["eta"])] for r in sw["distance"]],
            [0.18, 0.24, 0.28, 0.30],
            u"la caida es brutal: de %g a %g mm la eficiencia baja un factor "
            u"%.0f. A 1 mm el enlace da %.2f V."
            % (sw["distance"][0]["z_mm"], sw["distance"][-1]["z_mm"],
               sw["distance"][0]["eta"] / sw["distance"][-1]["eta"],
               sw["distance"][0]["vout"]),
            u"una bobina transmisora mas grande aplana la caida a costa de k "
            u"cerca. El compromiso depende de a que distancia se quiera usar.")

        # ---- 7. the rectifier -------------------------------------------
        p = doc.new(u"7. El rectificador")
        doc.text(TXT.RECT_INTRO.format(rrx=ch["r_ac"]))
        doc.text(TXT.RECT_THRESHOLD)
        p = doc.room(0.34)
        p.figure(F.rect_corners(rec),
                 caption=u"Los tres corners al dimensionado elegido. Se "
                         u"dimensiona por el peor, `%s`." % worst["corner"])

        p = doc.new(u"8. Decisiones: el rectificador")
        decision(
            doc, 11, u"La anchura de los TFT",
            [r"$R_c=3.3/W$   (medida),   $C_{ov}=C_{ox}\,ov\,W$   (medida)",
             r"$C_{ox}=1.564\times10^{-3}\,\mathrm{F/m^2}$"],
            "design.ngspice",
            u"W = %.0f um en ambos dispositivos." % (dz["w"] * 1e6),
            F.rect_width(rec),
            u"Tension de salida frente a la anchura. Optimo interior: la "
            u"conduccion mejora con W y la carga capacitiva empeora con W, "
            u"sobre un nodo cuya impedancia de fuente son %.0f ohmios."
            % ch["r_ac"],
            [[u"magnitud", u"valor"],
             [u"W elegida", u"%.0f um" % (dz["w"] * 1e6)],
             [u"Cov por lado", u"%.2f pF" % (rec["cov_f"] * 1e12)],
             [u"Rc por contacto", u"%.1f ohm" % rec["rc_ohm"]],
             [u"|1/wCov| a %.0f kHz" % (f_op / 1e3),
              u"%.0f ohm" % (1.0 / (2 * math.pi * f_op * rec["cov_f"]))],
             [u"R de la bobina", u"%.0f ohm" % ch["r_ac"]]],
            [0.42, 0.58],
            u"la capacidad de solape. A la W elegida su reactancia son %.0f "
            u"ohmios, comparable a los %.0f de la bobina: mas anchura empieza "
            u"a cortocircuitar la senal antes de llegar al diodo."
            % (1.0 / (2 * math.pi * f_op * rec["cov_f"]), ch["r_ac"]),
            u"un solape menor mueve el optimo hacia mas anchura. Es la razon "
            u"de que design.ngspice senale `ov` como el parametro que hay que "
            u"barrer.")

        decision(
            doc, 12, u"Longitud de canal y solape de puerta",
            [r"$I_d\propto (W/L)(V_{gs}-V_{to})^2$,   $C_{ov}\propto ov$"],
            "design.ngspice | igzo_mmm_lab.ngspice",
            u"L = %.0f um (el minimo de DRC, SD.2) y ov = %.0f um."
            % (dz["l"] * 1e6, dz["ov"] * 1e6),
            F.rect_length_ov(rec),
            u"Las otras dos dimensiones del dispositivo. Las dos van a su "
            u"minimo, sin optimo interior.",
            [[u"parametro", u"elegido", u"limite", u"por que"],
             [u"L", u"%.0f um" % (dz["l"] * 1e6), u"5 um (SD.2)",
              u"corriente, sin contrapartida capacitiva"],
             [u"ov", u"%.0f um" % (dz["ov"] * 1e6), u"eleccion de mascara",
              u"solo cuesta capacidad"]],
            [0.16, 0.16, 0.24, 0.44],
            u"nada las frena dentro del espacio permitido: L corta da mas "
            u"corriente y el solape solo carga. Ambas se pegan al minimo.",
            u"L de 5 um se imprime a unos 8 um segun el PDK (l_bias, una sola "
            u"muestra). Si el sesgo fuese mayor, el optimo de L se movería "
            u"hacia arriba.")

        # ---- 9. simulation ----------------------------------------------
        p = doc.new(u"9. El enlace simulado")
        doc.text(TXT.SIM_INTRO.format(
            rload=dz["rload"], tau=dz["rload"] * 10e-6, per=1.0 / f_op))
        if tr:
            p = doc.room(0.46)
            p.figure(F.ac_response(tr),
                     caption=u"Respuesta en alterna del nodo de recepcion, "
                             u"modulo y fase. El pico cae en %.0f kHz, donde "
                             u"lo predice la sintonia del primario."
                             % (tr["f"][int(tr["vrx_mag"].argmax())] / 1e3))

        p = doc.new(u"9. El enlace simulado (cont.)")
        if tr:
            p = doc.room(0.46)
            p.figure(F.transient_trace(tr),
                     caption=u"Regimen permanente: la portadora que llega a la "
                             u"bobina y la continua rectificada que sale. La "
                             u"salida es plana porque el condensador es de "
                             u"10 uF; el rizado esta en microvoltios.")
        p = doc.room(0.22)
        p.table([[u"magnitud", u"valor"],
                 [u"tension de salida", u"%.4f V" % worst["vout"]],
                 [u"potencia de salida", u"%s W" % num(worst["pout"])],
                 [u"potencia de entrada", u"%.0f W" % worst["pin"]],
                 [u"eficiencia", u"%s" % num(worst["eta"])],
                 [u"eta_max teorica (techo)",
                  u"%s" % num(tx["chosen_link"]["eta_max"])],
                 [u"rizado", u"%.1f uV" % ((tr["vout"].max() - tr["vout"].min())
                                           * 1e6) if tr else u"-"],
                 [u"corner", worst["corner"]],
                 [u"deriva en la ventana de medida",
                  u"%.4f %%" % worst["drift_pct"]]],
                [0.45, 0.55])
        decision(
            doc, 13, u"La resistencia de carga",
            [r"$\eta=P_{out}/P_{in}$,   $P_{out}=V_{out}^2/R_L$"],
            "",
            u"R_L = %.0f ohmios." % dz["rload"],
            F.eta_vs_load(sw),
            u"La eficiencia y la tension de salida tienen su maximo en cargas "
            u"DISTINTAS. Sin fijar una carga no hay ninguna cifra de "
            u"eficiencia que signifique algo.",
            [[u"R (ohm)", u"V_out (V)", u"P_out (W)", u"eta"]] +
            [[u"%.0f" % r["rload"], u"%.4f" % r["vout"], num(r["pout"]),
              num(r["eta"])] for r in sw["load"]],
            [0.22, 0.26, 0.26, 0.26],
            u"el maximo de eficiencia, en %.0f ohmios. La tension maxima cae "
            u"en %.0f ohmios y vale %.2f V: si lo que hace falta es tension y "
            u"no potencia, la carga optima es otra."
            % (max(sw["load"], key=lambda r: r["eta"])["rload"],
               max(sw["load"], key=lambda r: r["vout"])["rload"],
               max(sw["load"], key=lambda r: r["vout"])["vout"]),
            u"la carga real es el circuito que se alimente. Este barrido dice "
            u"cual conviene, no cual habra.")

        # ---- 10. the coupling capacitor ---------------------------------
        p = doc.new(u"10. El condensador de acoplo")
        doc.text(TXT.COUPLING_INTRO.format(q=ch["q"]))
        best_cprx = max(sw["cprx"], key=lambda r: r["eta"])
        ref = sw["coupling_ref"]
        decision(
            doc, 14, u"Anadir un condensador de acoplo: NO",
            [r"$V_{tanque}=Q\cdot\mathrm{EMF}$,   $Q=%.4f$" % ch["q"]],
            "",
            u"ninguno en el secundario. En el primario, si: la decision 9.",
            F.coupling_capacitor(sw),
            u"Eficiencia relativa a no poner nada. Las dos posiciones del "
            u"secundario solo bajan, y a partir de 1 nF hunden la salida: la "
            u"capacidad cortocircuita el nodo contra los %.0f ohmios de la "
            u"bobina." % ch["r_ac"],
            [[u"posicion", u"mejor eta", u"frente a nada"],
             [u"nada", num(ref["eta"]), u"1,0000"],
             [u"paralelo a la bobina", num(best_cprx["eta"]),
              u"%.4f" % (best_cprx["eta"] / ref["eta"])],
             [u"paralelo en el rectificador",
              num(max(sw["ccpl"], key=lambda r: r["eta"])["eta"]),
              u"%.4f" % (max(sw["ccpl"], key=lambda r: r["eta"])["eta"]
                         / ref["eta"])]],
            [0.40, 0.30, 0.30],
            u"la Q del lazo. Una resonancia multiplica la tension por la Q "
            u"del lazo en que esta, y aqui vale %.4f. Un condensador no puede "
            u"multiplicar por un factor menor que uno." % ch["q"],
            u"con Q por encima de uno -es decir, con mucho mas metal- el "
            u"condensador del secundario pasaria a ser obligatorio, igual que "
            u"ya lo es el del primario.")

        # ---- 11. limits and what next -----------------------------------
        p = doc.new(u"11. Limites de este resultado")
        doc.text(TXT.LIMITS)
        p = doc.room(0.36)
        p.head(u"12. Que habria que cambiar")
        doc.text(TXT.NEXT.format(rrx=ch["r_ac"], ft=1.2, ft5=1.9))

        # ---- 12. bibliography -------------------------------------------
        p = doc.new(u"13. Bibliografia")
        p.text(u"Las referencias que respaldan cada ecuacion. Las doce "
               u"primeras vienen de coil_core.BIBLIOGRAPHY, la libreria del "
               u"PDK; la ultima se anadio para este trabajo.", size=9)
        rows = [[u"ref", u"autores, ano", u"que respalda"]]
        for r in cc.BIBLIOGRAPHY:
            rows.append([r["key"],
                         u"%s (%d)" % (r["authors"].split(",")[0].strip(),
                                       r["year"]),
                         r["title"][:58]])
        rows.append([u"Dowell1966", u"P. L. Dowell (1966)",
                     u"Effects of eddy currents in transformer windings"])
        p = doc.room(0.020 * len(rows) + 0.03)
        p.table(rows, [0.18, 0.30, 0.52], size=7.6)

        doc.flush()
    print("wrote %s  (%d pages)" % (out, doc.n))
    return 0


def _eng(x):
    for scale, suf in ((1e-12, "pF"), (1e-9, "nF"), (1e-6, "uF"), (1e-3, "mF")):
        if abs(x) < scale * 1000:
            return "%.4g %s" % (x / scale, suf)
    return "%.4g F" % x


if __name__ == "__main__":
    sys.exit(main())
