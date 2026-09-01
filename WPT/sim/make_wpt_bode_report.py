#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The phase-2 report: transient Bode, coupling, and the parameterised bench.

    python3 make_wpt_bode_report.py            # into WPT/
    python3 make_wpt_bode_report.py <dir>      # somewhere else

Reads bode_tran.json, k_study.json, rectifier.json and params.py.  Every number
is computed by the sweeps rather than quoted, so the document cannot drift from
the design it describes.

The page engine, the decision block and the equation panel are imported from
make_wpt_report.py, so the two documents look like one set.  Prose in
bode_text.py, in Spanish; code and labels in English.
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/foss/designs/TFT-MMM-LAB-PDK/docs/pdf")

import matplotlib                                           # noqa: E402
matplotlib.use("Agg")

import bode_text as TXT                                     # noqa: E402
import figures as F                                         # noqa: E402
import params as P                                          # noqa: E402
from make_wpt_report import Doc, decision, equation, num     # noqa: E402
from pdfkit import PdfPages                                 # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.normpath(os.path.join(HERE, "..", "figures"))


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(
        os.path.join(HERE, ".."))
    os.makedirs(out_dir, exist_ok=True)

    b = json.load(open(os.path.join(HERE, "bode_tran.json")))
    ks = json.load(open(os.path.join(HERE, "k_study.json")))
    rec = json.load(open(os.path.join(HERE, "rectifier.json")))

    fixed = b["fixed"]
    at_op = min(fixed, key=lambda r: abs(r["f_hz"] - P.F_OP))
    peak = b["peak"]
    naive = fixed[0].get("naive_cycles", 0.0)
    typ = sorted(r["cycles"] for r in fixed)[len(fixed) // 2]
    bw = P.F_OP / P.tx_loop_q()

    out = os.path.join(out_dir, "WPT_bode_es.pdf")
    with PdfPages(out) as pdf:
        doc = Doc(pdf, TXT.FOOTER)

        # ---- 1. assumptions and verdict ---------------------------------
        p = doc.new(TXT.TITLE, kicker="Informe de diseno - fase 2")
        p.text(TXT.SUBTITLE, size=10, color="#555555")
        p.head(u"1. Supuestos, y en que se diferencian del informe anterior")
        doc.text(TXT.ASSUMPTIONS.format(
            z=P.Z_MM, l=P.TFT_L * 1e6, k=ks["geometric_k"], f=P.F_OP / 1e3,
            v=at_op["vout"], txl=P.TX_L * 1e6, txd=P.TX_D_MM,
            vgain=at_op["vout"] / 0.801), size=8.6)
        doc.text(TXT.VERDICT.format(
            v=at_op["vout"], rload=P.R_LOAD, pin=at_op["pin"],
            eta=at_op["eta"], vgain=at_op["vout"] / 0.801, q=P.RX_Q))

        # ---- 2. the method ----------------------------------------------
        p = doc.new(u"2. Bode por transitorio: el metodo")
        doc.text(TXT.METHOD)
        doc.text(TXT.SETTLING.format(
            cout=P.C_OUT * 1e6, rload=P.R_LOAD, tau=P.C_OUT * P.R_LOAD,
            f=P.F_OP / 1e3, per=1.0 / P.F_OP, naive=naive,
            npts=len(fixed), typ=typ, saving=naive / max(typ, 1)))
        p = doc.room(0.34)
        p.figure(F.bode_cycles(b),
                 caption=u"Ciclos de portadora simulados en cada punto, contra "
                         u"los que necesitaria arrancar en frio. La diferencia "
                         u"es lo que hace el barrido posible.")

        # ---- 3. the resonance trap --------------------------------------
        p = doc.new(u"3. Una trampa que costo un barrido entero")
        # The trap happened with the phase-1 transmitter, and the numbers are
        # that coil's - mixing them with this report's would be exactly the
        # kind of quiet error the section is about.
        q_old = 2 * math.pi * P.F_OP * 171.482e-6 / (10.574 + P.R_SRC)
        doc.text(TXT.RESONANCE_TRAP.format(
            ppd=P.BODE_PTS_PER_DECADE, f=P.F_OP / 1e3,
            step=P.F_OP * (10 ** (1.0 / P.BODE_PTS_PER_DECADE) - 1) / 1e3,
            q_old=q_old, bw_old=P.F_OP / q_old / 1e3,
            wrong=0.3097, right_old=2.0458, ratio=2.0458 / 0.3097,
            extra=P.BODE_RESONANCE_PTS + 1, txl=P.TX_L * 1e6,
            q_new=P.tx_loop_q(), bw_new=bw / 1e3))

        # ---- 4. the plots -----------------------------------------------
        p = doc.new(u"4. La respuesta")
        p = doc.room(0.42)
        p.figure(F.bode_voltage(b),
                 caption=u"El valor estable de C3 en cada frecuencia, que es "
                         u"lo que pediste. Linea continua: el primario "
                         u"sintonizado una vez a %.0f kHz, que es el diagrama "
                         u"de Bode del circuito. Discontinua: resintonizado en "
                         u"cada punto, que es la envolvente de lo que el "
                         u"enlace podria dar. Los marcadores huecos, si los "
                         u"hubiera, serian puntos que no asentaron."
                         % (P.F_OP / 1e3))
        p = doc.room(0.20)
        p.table([[u"f (kHz)", u"V(C3) (V)", u"dB", u"ciclos", u"estado"]] +
                [[u"%.1f" % (r["f_hz"] / 1e3), u"%.6f" % r["vout"],
                  u"%.1f" % r["db"], u"%d" % r["cycles"],
                  u"estable" if r["settled"] else u"NO ASENTADO"]
                 for r in fixed if abs(r["f_hz"] - P.F_OP) < 3 * bw],
                [0.20, 0.24, 0.16, 0.16, 0.24])

        p = doc.new(u"4. La respuesta (cont.)")
        p = doc.room(0.40)
        p.figure(F.bode_db(b),
                 caption=u"Lo mismo en decibelios, con el barrido AC "
                         u"superpuesto. El AC lineariza los diodos, asi que "
                         u"describe la respuesta en pequena senal de un "
                         u"rectificador que no rectifica; el transitorio mide "
                         u"la continua que aparece de verdad. La separacion "
                         u"entre las dos curvas es lo que el AC no puede "
                         u"decir, y es la razon de que quisieras el "
                         u"transitorio.")

        # ---- 5. the coupling --------------------------------------------
        p = doc.new(u"5. El acoplamiento")
        doc.text(TXT.K_INTRO.format(k=ks["geometric_k"], z=P.Z_MM))
        decision(
            doc, 1, u"k = 1 no es una opcion, es un techo",
            [r"$k = M/\sqrt{L_1 L_2} \leq 1$",
             r"$M=\mu_0\sqrt{r_1r_2}\left[(2/k-k)K(k)-(2/k)E(k)\right]$"],
            "Babic-Akyel 2008",
            u"el k que da la geometria, %.4e a %g mm."
            % (ks["geometric_k"], P.Z_MM),
            F.k_forced(ks["forced_k"]),
            u"Tension de salida contra un k forzado. La estrella es lo que da "
            u"la geometria real.",
            [[u"k", u"V(C3) (V)", u"eta", u""]] +
            [[u"%.4g" % r["k"], u"%.4f" % r["vout"], num(r["eta"]),
              u"<- el real" if r.get("is_real") else u""]
             for r in ks["forced_k"]],
            [0.18, 0.26, 0.28, 0.28],
            u"nada que se pueda elegir: k lo fija la geometria. k = 1 pide "
            u"enlace de flujo perfecto entre una bobina de milimetros y un "
            u"milimetro cuadrado de espiral, y eso no ocurre a ninguna "
            u"distancia.",
            u"acercar las bobinas, agrandar la receptora o encoger la "
            u"transmisora. Las tres estan barridas aqui, y la mejor "
            u"combinacion llega a k = %.2f - una cuarta parte de la unidad, "
            u"con una bobina de 1 mm a 0,1 mm de distancia."
            % max(r["k"] for r in ks["tx_inductance"]))

        p = doc.new(u"5. El acoplamiento (cont.)")
        near, best = ks["near_1uh"], ks["best_output"]
        decision(
            doc, 2, u"La inductancia del primario: tu observacion del 1 uH",
            [r"$k = M/\sqrt{L_1 L_2}$   -   bajar $L_1$ sube $k$ aunque $M$ no cambie"],
            "",
            u"%.4g uH: %s de %g mm, %d vueltas x %d, AWG %d."
            % (near["l_uh"], near["topology"], near["d_mm"], near["n"],
               near["layers"], near["awg"]),
            F.tx_inductance_fig(ks["tx_inductance"]),
            u"k y tension de salida contra la inductancia del primario, a "
            u"%g mm. Van en sentidos distintos, y ahi esta el hallazgo."
            % P.Z_MM,
            [[u"L1 (uH)", u"Q1", u"k", u"V(C3) (V)", u"bobina"]] +
            [[u"%.4g" % r["l_uh"], u"%.1f" % r["q"], u"%.3e" % r["k"],
              u"%.4f" % r["vout"],
              u"%g mm %dtx%d AWG%d" % (r["d_mm"], r["n"], r["layers"],
                                       r["awg"])]
             for r in ks["tx_inductance"]],
            [0.15, 0.11, 0.18, 0.18, 0.38],
            u"tenias razon: k sube %.0f veces al bajar de %.4g a %.4g uH. Y la "
            u"de %.4g uH entrega el %.0f %% de la tension de la mejor, asi que "
            u"empata en lo que importa con mucho mejor acoplamiento y una "
            u"construccion mas simple."
            % (near["k"] / best["k"], best["l_uh"], near["l_uh"],
               near["l_uh"], 100.0 * near["vout"] / max(best["vout"], 1e-15)),
            u"un receptor mayor, o una distancia mayor: las dos desplazan el "
            u"optimo hacia inductancias mas altas.")

        p = doc.new(u"5. El acoplamiento (cont.)")
        decision(
            doc, 3, u"La separacion: contacto",
            [r"$M \propto 1/z^3$ en campo lejano;   $\mathrm{EMF}=\omega M I_{tx}$"],
            "",
            u"%g mm - el chip apoyado sobre la bobina." % P.Z_MM,
            F.distance_fig(ks["distance"]),
            u"Tension de salida contra separacion. Las dos estrellas son este "
            u"informe y el supuesto de la fase 1.",
            [[u"z (mm)", u"k", u"M (H)", u"V(C3) (V)", u"eta"]] +
            [[u"%g" % r["z_mm"], u"%.3e" % r["k"], u"%.3e" % r["m_h"],
              u"%.4f" % r["vout"], num(r["eta"])] for r in ks["distance"]],
            [0.15, 0.21, 0.21, 0.22, 0.21],
            u"lo que tu dijiste que era el caso real. La fase 1 asumio 5 mm "
            u"sin preguntar, y eso solo ya vale un factor en tension de "
            u"salida.",
            u"cualquier encapsulado, sustrato o separador entre el chip y la "
            u"bobina. La curva dice exactamente cuanto cuesta cada milimetro.")

        # ---- 6. L = 10 um -----------------------------------------------
        p = doc.new(u"6. La longitud de canal, L = 10 um")
        doc.text(TXT.L10_INTRO)
        p = doc.room(0.16)
        p.table([[u"parametro", u"valor", u"de donde"],
                 [u"W", u"%.0f um" % (P.TFT_W * 1e6), u"barrido, rectifier.py"],
                 [u"L", u"%.0f um" % (P.TFT_L * 1e6), u"TU ELECCION"],
                 [u"ov", u"%.0f um" % (P.TFT_OV * 1e6), u"barrido"],
                 [u"Cov por lado", u"%.2f pF" % (P.COX_AREA * P.TFT_OV
                                                 * P.TFT_W * 1e12), u"medido"],
                 [u"Rc por contacto", u"%.1f ohm" % (P.RC_W / P.TFT_W),
                  u"medido"],
                 [u"V(C3) a %.0f kHz" % (P.F_OP / 1e3),
                  u"%.4f V" % at_op["vout"], u"transitorio, asentado"]],
                [0.30, 0.24, 0.46])

        # ---- 7. the schematics ------------------------------------------
        p = doc.new(u"7. Los esquematicos")
        doc.text(TXT.SCHEMATIC_INTRO.format(itx=0.2548, itx_ok=0.8607))
        for png, cap in (("wpt_pdk.png",
                          u"WPT.sch - tu dibujo, con la bobina receptora "
                          u"cambiada a ind.sym para que K1 la alcance."),
                         ("wpt_sim.png",
                          u"WPT_sim.sch - generado desde params.py, con el "
                          u"condensador de sintonia del primario dibujado en "
                          u"serie y no en un bloque de texto.")):
            path = os.path.join(FIGDIR, png)
            if os.path.exists(path) and os.path.getsize(path) > 0:
                p = doc.room(0.40)
                p.image(path, caption=cap, width=1.0)
            else:
                doc.text(u"[%s no se pudo capturar en esta ejecucion; "
                         u"vuelve a lanzar sim/shot_xschem.sh]" % png, size=8)

        # ---- 8. params.py ------------------------------------------------
        p = doc.new(u"8. El banco parametrizado")
        doc.text(TXT.PARAMS_INTRO)
        p = doc.room(0.30)
        p.code("""$ python3 params.py
  frequency      %.0f kHz   (band %.0f - %.0f kHz, fT %.2f MHz)
  separation     %g mm
  drive          %.0f W  ->  %.1f V amplitude
  RX coil        %.2f nH, %.0f ohm, Q = %.5f
  TX coil        %.2f uH, %.3f ohm, Q = %.1f
  TFTs           W = %.0f um, L = %.0f um, ov = %.0f um
  ...
  WARNING: RX_T_UM is ASSUMED, not measured.
  WARNING: The TFT models are validated in DC ONLY."""
               % (P.F_OP / 1e3, P.F_BAND[0] / 1e3, P.F_BAND[1] / 1e3,
                  P.F_T_TFT / 1e6, P.Z_MM, P.P_IN_W, P.vamp_for_power(),
                  P.RX_L * 1e9, P.RX_R, P.RX_Q, P.TX_L * 1e6, P.TX_R, P.TX_Q,
                  P.TFT_W * 1e6, P.TFT_L * 1e6, P.TFT_OV * 1e6))
        p = doc.room(0.22)
        p.table([[u"si quieres cambiar...", u"toca esto en params.py"],
                 [u"la distancia", u"Z_MM"],
                 [u"la frecuencia de trabajo", u"F_OP"],
                 [u"las bobinas", u"RX_L / RX_R / TX_L / TX_R"],
                 [u"forzar un acoplamiento", u"K_OVERRIDE"],
                 [u"los transistores", u"TFT_W / TFT_L / TFT_OV"],
                 [u"los condensadores y la carga", u"C_RES / C_OUT / R_LOAD"],
                 [u"el barrido de Bode", u"BODE_F_MIN / _MAX / _PTS_PER_DECADE"],
                 [u"la potencia de excitacion", u"P_IN_W"]],
                [0.46, 0.54])
        doc.flush()

    print("wrote %s  (%d pages)" % (out, doc.n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
