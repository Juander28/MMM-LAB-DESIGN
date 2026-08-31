#!/usr/bin/env python3
"""
Project status report: where the project stands, what has been achieved, what
is missing, the problems, and the candidate solutions.

Bilingual - all copy lives in CONTENT[lang], so the English and Spanish editions
cannot drift apart.  Writes PROJECT_STATUS.pdf and ESTADO_DEL_PROYECTO.pdf at
the top level of the project.
"""

import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))

A4 = (8.27, 11.69)
BLUE, RED, GREEN, AMBER, GREY = "#2E5EAA", "#C1425A", "#2A9D8F", "#E0A100", "#6C757D"
INK = "#1A1A1A"
STATE_COLOR = {"done": GREEN, "part": AMBER, "fail": RED, "todo": GREY}

CONTENT = {}

# =============================== ENGLISH ==================================
CONTENT["en"] = dict(
    outfile="PROJECT_STATUS.pdf",
    meta_title="100X Improvement in Bioelectronic Signal Acquisition - Project Status",
    kicker="P R O J E C T   S T A T U S",
    title="100X Improvement in\nBioelectronic Signal Acquisition",
    subtitle="Resonant electrophysiology - coupled LC resonators with Q-enhancement",
    people=("UCLA (Prof. Tyler Clites / Samantha Herman)   -   "
            "UCI (Prof. C. Velez Cuervo / Juan Diego Sanchez)"),
    date="19 August 2026",
    running="100X Improvement in Bioelectronic Signal Acquisition - project status",
    stand_h="Where the project stands",
    stand=[
        "The physics works. A two-channel design point is verified end to end in",
        "simulation: co-tuned notches at 55.89 and 100.00 MHz, both meeting the",
        "bandwidth and loaded-Q specification on a ground-free differential line.",
        "That is the central claim of the project and it holds.",
        "",
        "What does not work yet is everything between that result and a device.",
        "This session put measured IGZO TFT data into the picture for the first",
        "time, and it changed the outlook: the transistors assumed in every",
        "simulation to date are roughly 1400x stronger than the ones actually",
        "fabricated. At 1.5 V the measured devices fall 9x to 64x short of the",
        "transconductance the resonator needs, and no amount of bias current",
        "closes that gap, because the supply caps the gate drive.",
        "",
        "Separately, the channel architecture had a structural flaw that is now",
        "understood and fixed on paper: sharing the return path moved resonances",
        "27-38 % off their design frequencies, and got worse with every channel",
        "added. Giving each channel its own return holds the error under 2.4 %.",
        "",
        "One problem solved, one hard problem newly quantified, and a decision",
        "now on the table about supply voltage and device technology.",
    ],
    tiles=[("2413 / 7217", "loaded Q achieved\n(spec: >= 1667)", GREEN),
           ("9x - 64x", "transconductance\nshortfall at 1.5 V", RED),
           ("2.4% -> 1.2%", "channel placement error\nwith isolated return", GREEN)],
    score_h="Requirements scorecard",
    score_sub="Every system requirement against what has actually been demonstrated",
    score_cols=("REQUIREMENT", "TARGET", "STATUS TODAY", "VERDICT"),
    state_label={"done": "MET", "part": "PARTIAL",
                 "fail": "NOT MET", "todo": "NOT STARTED"},
    reqs=[
        ("Operating band", "50 - 200 MHz", "55.89 and 100.00 MHz verified", "done"),
        ("Notch bandwidth", "<= 30 kHz", "23.2 kHz / 13.9 kHz", "done"),
        ("Loaded Q", ">= 1667 @ 50 MHz", "Q_L 2413 / 7217", "done"),
        ("Ground-free operation", "mandatory", "differential, no ground node", "done"),
        ("Channel count", ">= 1000", "10 placed correctly (isolated ret.)", "part"),
        ("Power per channel", "<= 100 uW", "3.5 mW ideal device; worse with TFT", "fail"),
        ("Real devices (IGZO)", "gm 0.8 - 2.0 mS", "89 uS max at VDD = 1.5 V", "fail"),
        ("Bias stability", "+-0.25 % on Itail", "open loop only, no AGC", "fail"),
        ("Footprint", "150 x 150 um", "not laid out yet", "todo"),
        ("EMG signal path", "+-5 mV, 20 Hz-2 kHz", "not simulated yet", "todo"),
        ("Inductor Q0", "assumed 31", "not measured on film", "todo"),
    ],
    howread_h="How to read this",
    howread=[
        "MET means demonstrated in closed-loop simulation, not calculated. The four",
        "met requirements were re-verified this session against a freshly generated",
        "netlist, reproducing 55.8901 MHz / 35.90 dB / 22.98 kHz / Q_L 2432 and",
        "100.0021 MHz / 39.69 dB / 13.98 kHz / Q_L 7151.",
        "",
        "PARTIAL on channel count: ten channels were placed at their design",
        "frequencies with the isolated return, which is the mechanism that scales.",
        "Nothing above ten has been simulated, and 1000 is still far away.",
        "",
        "NOT MET means measured and found short, with a number attached.",
        "NOT STARTED means no work has been done - not that it is expected to fail.",
    ],
    ach_h="What has been achieved",
    ach_sub="Results that are verified, not assumed",
    achieved=[
        ("A verified two-channel design point", GREEN, [
            "Two co-tuned notches on one ground-free differential line:",
            "    channel A  55.890 MHz   35.9 dB deep   23.2 kHz BW   Q_L 2413",
            "    channel B  100.002 MHz  39.7 dB deep   13.9 kHz BW   Q_L 7217",
            "Both meet the <= 30 kHz bandwidth spec and beat the Q_L >= 1667 target.",
            "Reproduced this session from a newly written netlist generator, so the",
            "result does not depend on any one hand-edited file.",
        ]),
        ("An open, reproducible simulation flow", GREEN, [
            "xschem + ngspice, no proprietary tools, running end to end.",
            "Readers for the lab's raw .xls and .xlsx data written from scratch",
            "(no xlrd/openpyxl available), cross-checked against the pre-existing",
            "analysis: 172 of 172 saturation-current values reproduced exactly.",
        ]),
        ("The first real device model", GREEN, [
            "IGZO TFT parameters extracted from the INRF measurements by two",
            "independent routes that agree to 0.5 % on long-channel devices:",
            "    Kp = 0.72 uA/V^2    Vth ~ 0.1 V    lambda ~ 0.007   (best chip)",
            "Written up as test1/models/tft_igzo_test1.lib with four variants",
            "spanning best case, typical, short-channel and worst-chip.",
        ]),
        ("A structural fix for scaling", GREEN, [
            "The shared-return flaw is identified, quantified and solved on paper.",
            "Isolated return holds channel placement to <= 2.4 % error, improving",
            "to 1.2 % at ten channels, where the shared return degrades to 37.9 %.",
        ]),
        ("Quantified design levers", BLUE, [
            "gm required / tank loss = 854 uS/Ohm, constant to +-4 % over a 16x",
            "range of series resistance. This converts any future inductor-quality",
            "result directly into a transconductance requirement.",
            "Contact-limited length L_c ~ 54 um, so the contact problem is bounded",
            "and its payoff is known: 5.6x in Kp, 2.4x in gm.",
        ]),
    ],
    prob_word="Problem",
    sev_label={"BLOCKING": "BLOCKING", "HIGH": "HIGH",
               "MEDIUM": "MEDIUM", "SOLVED": "SOLVED"},
    found_h="What we found",
    sols_h="Possible solutions",
    problems=[
        dict(rank="1", sev="BLOCKING",
             title="The TFT cannot reach the required gm at 1.5 V",
             what=["The tank needs gm = 0.81 mS (100 MHz) to 2.02 mS (55.9 MHz).",
                   "The best measured device gives 89 uS at VDD = 1.5 V; the realistic",
                   "short-channel device gives 32 uS. Shortfall: 9x to 64x.",
                   "Raising the bias current does not help - VGS is capped by the rail."],
             why="Kp = 0.72 uA/V^2 measured vs 1000 uA/V^2 assumed (factor ~1400).",
             sols=[("Raise the supply",
                    "IGZO TFTs normally run at 5-20 V. Channel B closes at VDD ~ 13 V, "
                    "channel A at ~ 32 V. Cheapest fix technically, but it breaks the "
                    "power budget and the implant safety case - needs a decision."),
                   ("Increase Cox",
                    "Kp = mu*Cox and mu is fixed by the material. A thinner or higher-k "
                    "gate dielectric raises Kp proportionally. Going from a ~100 nm "
                    "SiO2-equivalent to a high-k stack is worth 10-30x."),
                   ("Fix the contacts",
                    "Worth 5.6x in Kp on short-channel devices for free (see problem 4). "
                    "Not sufficient alone, but multiplies with the others."),
                   ("Change the active device",
                    "If the rail must stay at 1.5 V, no TFT technology reaches this gm. "
                    "That is a topology-level decision.")]),
        dict(rank="2", sev="SOLVED",
             title="The shared return destroys the channel frequency plan",
             what=["All channels returned to VDD through the same node, so the N return",
                   "inductors sat in parallel: effective return = (L/2)/N, shrinking with N.",
                   "Modes landed 27-38 % off their design frequencies, and the error grew",
                   "with channel count. Channel 10 landed at 275.8 MHz - out of band."],
             why="Confirmed by simulation at N = 2, 3, 4, 6, 8, 10.",
             sols=[("Isolated return per channel",
                    "Each channel gets its own floating return, coupled to the line at "
                    "both ends so the design stays ground-free. Placement error drops to "
                    "<= 2.4 %, and it improves with N (1.2 % at N=10). Implemented in "
                    "scale/gen_nchan.py --return isolated."),
                   ("Cost",
                    "One extra inductor and one extra coupling capacitor per channel. "
                    "The area cost is real and must be checked against the 150 x 150 um "
                    "cell.")]),
        dict(rank="3", sev="BLOCKING",
             title="Bias sensitivity with no amplitude control",
             what=["Q-enhancement works by cancelling tank loss, so the operating point sits",
                   "just below oscillation. Measured previously: +-0.25 % error on Itail still",
                   "gives >= 17 dB depth, but +1 % on channel B makes it oscillate.",
                   "No feedback loop exists - everything so far is open loop."],
             why="Intrinsic to negative-gm Q-enhancement; consistent with the literature.",
             sols=[("Amplitude control loop (AGC)",
                    "Detect the resonator amplitude and servo the tail current. This is the "
                    "standard answer and the single largest piece of unbuilt work."),
                   ("Isolated return helps",
                    "With channels no longer shifting each other's thresholds, each loop can "
                    "be designed and tuned independently instead of co-tuned as a coupled "
                    "system."),
                   ("Note",
                    "This could not be re-measured this session: AC analysis is linear and "
                    "cannot detect oscillation. Needs pole-zero (.pz) or transient "
                    "analysis.")]),
        dict(rank="4", sev="HIGH",
             title="Contact resistance dominates the short-channel devices",
             what=["Kp is flat at ~0.72 uA/V^2 for L >= 40 um and collapses to 0.13 uA/V^2 at",
                   "L = 8 um. Linear and saturation extractions agree to 0.5 % on long channels",
                   "and diverge to a ratio of 0.64 on short ones - the contact fingerprint.",
                   "2*Rc*W = 6.6e6 Ohm*um (660 Ohm*cm); contact-limited length L_c ~ 54 um."],
             why="~100x worse than good IGZO practice - a process problem, not a material one.",
             sols=[("Contact engineering",
                    "Self-aligned source/drain, an n+ interlayer, or a post-metallisation "
                    "anneal. Standard IGZO practice recovers 1-2 orders."),
                   ("Payoff",
                    "Recovering the intrinsic 0.72 uA/V^2 at L = 8 um is 5.6x in Kp, i.e. "
                    "2.4x in gm, for no extra area and no extra power."),
                   ("Do this before fabricating more",
                    "It changes the device model that every downstream design decision "
                    "depends on.")]),
        dict(rank="5", sev="HIGH",
             title="Power budget is orders of magnitude over",
             what=["Budget is 100 uW/channel (100 mW for 1000 channels). The verified two-channel",
                   "point draws 7.1 mW - 3.5 mW/channel, 35x over, and that is with the",
                   "optimistic device. With the measured TFT the required current is far higher."],
             why="Bias current scales as gm^2/(Kp*(W/L)); a low Kp is paid for in current.",
             sols=[("Duty-cycling",
                    "Channels do not all need to be live at once. EMG bandwidth is 2 kHz "
                    "against a 150 kHz channel allocation - a large duty-cycle margin."),
                   ("Lower the gm requirement",
                    "gm_req / RS = 854 uS/Ohm was measured, constant to +-4 % over a 16x "
                    "range of RS. Lower tank loss lowers the required gm proportionally - "
                    "but thin-film inductors go the wrong way (see 7)."),
                   ("Device sizing",
                    "Larger W/L buys gm at constant current, bounded by area.")]),
        dict(rank="6", sev="MEDIUM",
             title="Measurements that are missing outright",
             what=["VGS/, COX/ and HALL/ are empty for all three chips.",
                   "The CAP test structure area is not recorded, so Cox cannot be normalised.",
                   "W and L are not recorded for the devices in TFT/test/ - which hold the",
                   "best transfer sweeps in the whole set and currently cannot be used",
                   "quantitatively."],
             why="Without Cox we cannot separate mu from Cox, nor predict gate capacitance.",
             sols=[("Measure Cox on a known area",
                    "A single CV sweep on a pad of recorded dimensions closes this. It also "
                    "tells us whether the low Kp is thick dielectric or low mobility - which "
                    "decides whether problem 1 is fixable."),
                   ("Record geometry with the data",
                    "Add W, L and pad spacing to the Clarius test names, so extraction stays "
                    "automatic."),
                   ("Gate capacitance matters here",
                    "At 50-200 MHz the gate capacitance loads the tank directly. It is "
                    "currently a placeholder in the model.")]),
        dict(rank="7", sev="MEDIUM",
             title="Unverified assumptions still carried in the design",
             what=["Inductor Q0 = 31 is assumed, never measured on an actual thin film.",
                   "Realistic film inductors are usually worse, which raises the required gm",
                   "in direct proportion (854 uS/Ohm measured).",
                   "The 150 x 150 um footprint has never been laid out."],
             why="These feed straight into problems 1 and 5 and could make both worse.",
             sols=[("Measure or simulate one film inductor",
                    "Cheap, and it either confirms or invalidates the loss budget the whole "
                    "design rests on."),
                   ("Draw one channel",
                    "A single cell layout answers the footprint question and prices the extra "
                    "inductor the isolated return needs.")]),
    ],
    ev_h="Evidence behind the two hard numbers",
    ev_sub="The transconductance shortfall and the scaling fix",
    ev_t1="Measured device strength - and where the contacts take over",
    ev_x1="channel length L (um)",
    ev_y1="extracted Kp (uA/V$^2$)",
    ev_note1="0.72 uA/V$^2$ intrinsic",
    ev_t2="Ten channels: where they were asked to be, where they land",
    ev_x2="design target frequency (MHz)",
    ev_y2="simulated mode (MHz)",
    ev_leg=("ideal", "shared return (today)", "isolated return (fix)"),
    ev_verif_h="Verification performed this session",
    ev_verif=[
        "Raw .xls reader vs the pre-existing Isat reports: 172 / 172 values exact.",
        "Transfer-curve extraction at VDS = 0.1 / 0.1 / 1 / 2 V gave 26.4 / 27.0 /",
        "27.1 / 28.4 uA/V^2 - 7 % spread across a 20x range of drain voltage - and",
        "the extracted threshold reproduces the instrument's own VT column.",
        "The netlist generator reproduces the verified two-channel design point",
        "before it was used for anything else.",
        "",
        "Not settled: channel-to-channel interaction could not be re-measured,",
        "because AC analysis is linear and cannot detect oscillation. The 9 % figure",
        "carried in the project notes needs re-deriving with .pz or transient.",
    ],
    next_h="What is missing, and in what order",
    next_sub="Sequenced so that the decisions that can invalidate work come first",
    nexts=[("Now", GREEN, [
                "Adopt the isolated return in all further work (scale/gen_nchan.py).",
                "Measure Cox on a pad of known area; record W/L with every device.",
                "Re-derive the channel interaction with .pz or transient, not AC."]),
           ("Next", AMBER, [
                "Decide the supply-voltage question - it is a project-level call, not a tweak.",
                "Contact engineering trial, then re-extract the model.",
                "Measure or simulate one realistic thin-film inductor (Q0)."]),
           ("Then", GREY, [
                "Design the amplitude control loop once the real gm is known.",
                "Lay out one channel and price the isolated-return area cost.",
                "Simulate the EMG signal path end to end (+-5 mV, 20 Hz - 2 kHz)."])],
    dec_h="The decision that gates everything else",
    dec=[
        "The 1.5 V supply was inherited from a silicon-CMOS assumption, not from a",
        "requirement of the application. Every TFT technology - not just this one -",
        "will struggle to deliver milliamp-scale transconductance from that rail.",
        "",
        "Three paths exist and they lead to different projects:",
        "",
        "   1. Raise the supply, and re-open the power and safety budgets.",
        "   2. Raise Cox with a high-k or thinner gate stack, and keep 1.5 V.",
        "   3. Keep 1.5 V and change the active device away from a TFT.",
        "",
        "Nothing downstream - AGC design, power budget, layout - can be settled",
        "before this is. It should be taken deliberately, with UCLA in the room,",
        "rather than defaulted into.",
    ],
    colophon=("Detail behind every number in this report: "
              "report/device_and_scaling_findings.pdf\n"
              "Extraction and simulation code: tools/, tft/, scale/"),
)

# =============================== ESPANOL ==================================
CONTENT["es"] = dict(
    outfile="ESTADO_DEL_PROYECTO.pdf",
    meta_title="100X Improvement in Bioelectronic Signal Acquisition - Estado del proyecto",
    kicker="E S T A D O   D E L   P R O Y E C T O",
    title="Mejora de 100X en la adquisición\nde señales bioelectrónicas",
    subtitle="Electrofisiología resonante - resonadores LC acoplados con realce de Q",
    people=("UCLA (Prof. Tyler Clites / Samantha Herman)   -   "
            "UCI (Prof. C. Vélez Cuervo / Juan Diego Sánchez)"),
    date="19 de agosto de 2026",
    running="100X Improvement in Bioelectronic Signal Acquisition - estado del proyecto",
    stand_h="Dónde estamos",
    stand=[
        "La física funciona. Hay un punto de diseño de dos canales verificado de",
        "extremo a extremo en simulación: notches co-sintonizados en 55.89 y 100.00",
        "MHz, ambos cumpliendo la spec de ancho de banda y Q cargada, sobre una línea",
        "diferencial sin tierra. Esa es la afirmación central del proyecto, y se sostiene.",
        "",
        "Lo que todavía no funciona es todo lo que va de ese resultado a un",
        "dispositivo. En esta sesión entraron por primera vez datos medidos de TFT",
        "de IGZO, y eso cambió el panorama: los transistores asumidos en todas las",
        "simulaciones hasta hoy son unas 1400x más fuertes que los que realmente se",
        "fabricaron. A 1.5 V los dispositivos medidos quedan 9x a 64x cortos de la",
        "transconductancia que pide el resonador, y no hay corriente de polarización",
        "que cierre esa brecha, porque la alimentación limita el ataque de compuerta.",
        "",
        "Aparte, la arquitectura de canales tenía una falla estructural que ya está",
        "entendida y resuelta en papel: compartir el retorno movía las resonancias",
        "27-38 % de sus frecuencias de diseño, y empeoraba con cada canal añadido.",
        "Dar a cada canal su propio retorno mantiene el error por debajo de 2.4 %.",
        "",
        "Un problema resuelto, un problema duro recién cuantificado, y una decisión",
        "ahora sobre la mesa acerca de la tensión de alimentación y la tecnología",
        "del dispositivo.",
    ],
    tiles=[("2413 / 7217", "Q cargada lograda\n(spec: >= 1667)", GREEN),
           ("9x - 64x", "déficit de\ntransconductancia a 1.5 V", RED),
           ("2.4% -> 1.2%", "error de colocación\ncon retorno aislado", GREEN)],
    score_h="Tablero de requisitos",
    score_sub="Cada requisito del sistema contra lo que realmente se ha demostrado",
    score_cols=("REQUISITO", "OBJETIVO", "ESTADO HOY", "VEREDICTO"),
    state_label={"done": "CUMPLE", "part": "PARCIAL",
                 "fail": "NO CUMPLE", "todo": "SIN EMPEZAR"},
    reqs=[
        ("Banda de operación", "50 - 200 MHz", "55.89 y 100.00 MHz verificados", "done"),
        ("Ancho de banda del notch", "<= 30 kHz", "23.2 kHz / 13.9 kHz", "done"),
        ("Q cargada", ">= 1667 @ 50 MHz", "Q_L 2413 / 7217", "done"),
        ("Operación sin tierra", "obligatorio", "diferencial, sin nodo de tierra", "done"),
        ("Número de canales", ">= 1000", "10 bien colocados (retorno aislado)", "part"),
        ("Potencia por canal", "<= 100 uW", "3.5 mW con device ideal; peor con TFT", "fail"),
        ("Dispositivos reales (IGZO)", "gm 0.8 - 2.0 mS", "89 uS máx. a VDD = 1.5 V", "fail"),
        ("Estabilidad de polarización", "+-0.25 % en Itail", "solo lazo abierto, sin AGC", "fail"),
        ("Footprint", "150 x 150 um", "sin layout todavía", "todo"),
        ("Camino de señal EMG", "+-5 mV, 20 Hz-2 kHz", "sin simular todavía", "todo"),
        ("Q0 del inductor", "asumido 31", "sin medir en película", "todo"),
    ],
    howread_h="Cómo leer esto",
    howread=[
        "CUMPLE significa demostrado en simulación de lazo cerrado, no calculado.",
        "Los cuatro requisitos cumplidos se re-verificaron en esta sesión contra un",
        "netlist recién generado, reproduciendo 55.8901 MHz / 35.90 dB / 22.98 kHz /",
        "Q_L 2432 y 100.0021 MHz / 39.69 dB / 13.98 kHz / Q_L 7151.",
        "",
        "PARCIAL en número de canales: diez canales quedaron en sus frecuencias de",
        "diseño con el retorno aislado, que es el mecanismo que escala. Nada por",
        "encima de diez se ha simulado, y 1000 sigue estando lejos.",
        "",
        "NO CUMPLE significa medido y encontrado corto, con un número al lado.",
        "SIN EMPEZAR significa que no se ha trabajado - no que se espere que falle.",
    ],
    ach_h="Lo que se ha conseguido",
    ach_sub="Resultados verificados, no supuestos",
    achieved=[
        ("Un punto de diseño de dos canales verificado", GREEN, [
            "Dos notches co-sintonizados sobre una línea diferencial sin tierra:",
            "    canal A  55.890 MHz   35.9 dB prof.   23.2 kHz BW   Q_L 2413",
            "    canal B  100.002 MHz  39.7 dB prof.   13.9 kHz BW   Q_L 7217",
            "Ambos cumplen la spec de BW <= 30 kHz y superan el objetivo Q_L >= 1667.",
            "Reproducido en esta sesión desde un generador de netlist recién escrito,",
            "así que el resultado no depende de ningún archivo editado a mano.",
        ]),
        ("Un flujo de simulación abierto y reproducible", GREEN, [
            "xschem + ngspice, sin herramientas propietarias, corriendo de punta a punta.",
            "Lectores para los .xls y .xlsx crudos del laboratorio escritos desde cero",
            "(no hay xlrd/openpyxl disponibles), contrastados contra el análisis",
            "preexistente: 172 de 172 corrientes de saturación reproducidas exactamente.",
        ]),
        ("El primer modelo de dispositivo real", GREEN, [
            "Parámetros del TFT de IGZO extraídos de las medidas del INRF por dos vías",
            "independientes que coinciden al 0.5 % en dispositivos de canal largo:",
            "    Kp = 0.72 uA/V^2    Vth ~ 0.1 V    lambda ~ 0.007   (mejor chip)",
            "Escrito como test1/models/tft_igzo_test1.lib con cuatro variantes que",
            "cubren mejor caso, típico, canal corto y peor chip.",
        ]),
        ("Una corrección estructural para el escalado", GREEN, [
            "La falla del retorno compartido está identificada, cuantificada y resuelta.",
            "El retorno aislado mantiene la colocación de canales en <= 2.4 % de error,",
            "mejorando a 1.2 % con diez canales, donde el compartido degrada a 37.9 %.",
        ]),
        ("Palancas de diseño cuantificadas", BLUE, [
            "gm requerido / pérdida del tanque = 854 uS/Ohm, constante a +-4 % sobre un",
            "rango 16x de resistencia serie. Esto convierte cualquier resultado futuro",
            "de calidad de inductor directamente en un requisito de transconductancia.",
            "Longitud limitada por contacto L_c ~ 54 um, así que el problema de",
            "contacto está acotado y su ganancia es conocida: 5.6x en Kp, 2.4x en gm.",
        ]),
    ],
    prob_word="Problema",
    sev_label={"BLOCKING": "BLOQUEANTE", "HIGH": "ALTA",
               "MEDIUM": "MEDIA", "SOLVED": "RESUELTO"},
    found_h="Qué encontramos",
    sols_h="Soluciones posibles",
    problems=[
        dict(rank="1", sev="BLOCKING",
             title="El TFT no alcanza el gm requerido a 1.5 V",
             what=["El tanque pide gm = 0.81 mS (100 MHz) a 2.02 mS (55.9 MHz).",
                   "El mejor dispositivo medido da 89 uS a VDD = 1.5 V; el realista de",
                   "canal corto da 32 uS. Déficit: 9x a 64x.",
                   "Subir la corriente no ayuda - VGS está topado por la alimentación."],
             why="Kp = 0.72 uA/V^2 medido contra 1000 uA/V^2 asumido (factor ~1400).",
             sols=[("Subir la alimentación",
                    "Los TFT de IGZO normalmente operan a 5-20 V. El canal B cierra a "
                    "VDD ~ 13 V y el canal A a ~ 32 V. Es la corrección más barata "
                    "técnicamente, pero rompe el presupuesto de potencia y el caso de "
                    "seguridad del implante - requiere una decisión."),
                   ("Aumentar Cox",
                    "Kp = mu*Cox y mu la fija el material. Un dieléctrico de compuerta más "
                    "delgado o de mayor k sube Kp proporcionalmente. Pasar de un "
                    "equivalente de ~100 nm de SiO2 a un stack high-k vale 10-30x."),
                   ("Arreglar los contactos",
                    "Vale 5.6x en Kp en los dispositivos de canal corto, gratis (ver "
                    "problema 4). No alcanza solo, pero multiplica con las demás."),
                   ("Cambiar el dispositivo activo",
                    "Si el riel debe quedarse en 1.5 V, ninguna tecnología de TFT llega a "
                    "este gm. Esa es una decisión a nivel de topología.")]),
        dict(rank="2", sev="SOLVED",
             title="El retorno compartido destruye el plan de frecuencias",
             what=["Todos los canales retornaban a VDD por el mismo nodo, así que las N",
                   "inductancias de retorno quedaban en paralelo: retorno efectivo = (L/2)/N,",
                   "encogiéndose con N. Los modos caían 27-38 % fuera de sus frecuencias de",
                   "diseño, y el error crecía con el número de canales. El canal 10 aterrizaba",
                   "en 275.8 MHz - fuera de banda."],
             why="Confirmado por simulación en N = 2, 3, 4, 6, 8, 10.",
             sols=[("Retorno aislado por canal",
                    "Cada canal recibe su propio retorno flotante, acoplado a la línea en "
                    "ambos extremos para que el diseño siga sin tierra. El error de "
                    "colocación baja a <= 2.4 %, y mejora con N (1.2 % en N=10). "
                    "Implementado en scale/gen_nchan.py --return isolated."),
                   ("Costo",
                    "Un inductor extra y un capacitor de acople extra por canal. El costo "
                    "de área es real y hay que contrastarlo contra la celda de "
                    "150 x 150 um.")]),
        dict(rank="3", sev="BLOCKING",
             title="Sensibilidad de polarización sin control de amplitud",
             what=["El realce de Q funciona cancelando la pérdida del tanque, así que el punto",
                   "de operación queda justo por debajo de la oscilación. Medido antes:",
                   "+-0.25 % de error en Itail todavía da >= 17 dB de profundidad, pero +1 %",
                   "en el canal B lo hace oscilar.",
                   "No existe ningún lazo de realimentación - todo hasta ahora es lazo abierto."],
             why="Intrínseco al realce de Q por gm negativo; consistente con la literatura.",
             sols=[("Lazo de control de amplitud (AGC)",
                    "Detectar la amplitud del resonador y servocontrolar la corriente de "
                    "cola. Es la respuesta estándar y la pieza más grande de trabajo sin "
                    "construir."),
                   ("El retorno aislado ayuda",
                    "Con los canales ya sin moverse los umbrales entre sí, cada lazo se "
                    "puede diseñar y ajustar de forma independiente en vez de "
                    "co-sintonizado como sistema acoplado."),
                   ("Nota",
                    "Esto no se pudo re-medir en esta sesión: el análisis AC es lineal y no "
                    "puede detectar oscilación. Necesita polo-cero (.pz) o análisis "
                    "transitorio.")]),
        dict(rank="4", sev="HIGH",
             title="La resistencia de contacto domina los dispositivos de canal corto",
             what=["Kp es plano en ~0.72 uA/V^2 para L >= 40 um y se desploma a 0.13 uA/V^2 en",
                   "L = 8 um. Las extracciones lineal y de saturación coinciden al 0.5 % en",
                   "canal largo y divergen a una razón de 0.64 en canal corto - la firma del",
                   "contacto. 2*Rc*W = 6.6e6 Ohm*um (660 Ohm*cm); longitud crítica L_c ~ 54 um."],
             why="~100x peor que buena práctica en IGZO - es un problema de proceso, no de material.",
             sols=[("Ingeniería de contactos",
                    "Fuente/drenaje autoalineados, una intercapa n+, o un recocido "
                    "post-metalización. La práctica estándar en IGZO recupera 1-2 órdenes."),
                   ("Ganancia",
                    "Recuperar los 0.72 uA/V^2 intrínsecos en L = 8 um son 5.6x en Kp, o sea "
                    "2.4x en gm, sin área extra y sin potencia extra."),
                   ("Hacerlo antes de fabricar más",
                    "Cambia el modelo de dispositivo del que dependen todas las decisiones "
                    "de diseño río abajo.")]),
        dict(rank="5", sev="HIGH",
             title="El presupuesto de potencia está órdenes de magnitud arriba",
             what=["El presupuesto es 100 uW/canal (100 mW para 1000 canales). El punto de dos",
                   "canales verificado consume 7.1 mW - 3.5 mW/canal, 35x por encima, y eso es",
                   "con el dispositivo optimista. Con el TFT medido la corriente requerida es",
                   "muchísimo mayor."],
             why="La corriente escala como gm^2/(Kp*(W/L)); un Kp bajo se paga en corriente.",
             sols=[("Duty-cycling",
                    "No todos los canales necesitan estar vivos a la vez. El ancho de banda "
                    "del EMG es 2 kHz contra una asignación de 150 kHz por canal - un margen "
                    "de ciclo de trabajo enorme."),
                   ("Bajar el gm requerido",
                    "Se midió gm_req / RS = 854 uS/Ohm, constante a +-4 % sobre un rango 16x "
                    "de RS. Menos pérdida en el tanque baja el gm requerido "
                    "proporcionalmente - pero los inductores en película van al revés "
                    "(ver 7)."),
                   ("Dimensionamiento del dispositivo",
                    "Un W/L mayor compra gm a corriente constante, acotado por el área.")]),
        dict(rank="6", sev="MEDIUM",
             title="Medidas que faltan del todo",
             what=["VGS/, COX/ y HALL/ están vacías en los tres chips.",
                   "El área de la estructura de CAP no está registrada, así que Cox no se puede",
                   "normalizar. W y L no están registrados para los dispositivos de TFT/test/ -",
                   "que tienen las mejores curvas de transferencia de todo el conjunto y hoy no",
                   "se pueden usar cuantitativamente."],
             why="Sin Cox no separamos mu de Cox, ni predecimos la capacidad de compuerta.",
             sols=[("Medir Cox sobre un área conocida",
                    "Un solo barrido CV sobre un pad de dimensiones registradas cierra esto. "
                    "También dice si el Kp bajo es dieléctrico grueso o movilidad baja - lo "
                    "que decide si el problema 1 tiene arreglo."),
                   ("Registrar la geometría junto con los datos",
                    "Agregar W, L y espaciado de pads a los nombres de test del Clarius, para "
                    "que la extracción siga siendo automática."),
                   ("La capacidad de compuerta importa aquí",
                    "A 50-200 MHz la capacidad de compuerta carga el tanque directamente. Hoy "
                    "es un valor de relleno en el modelo.")]),
        dict(rank="7", sev="MEDIUM",
             title="Supuestos sin verificar que el diseño todavía carga",
             what=["Q0 = 31 del inductor es un supuesto, nunca medido en una película real.",
                   "Los inductores de película realistas suelen ser peores, lo que sube el gm",
                   "requerido en proporción directa (854 uS/Ohm medido).",
                   "El footprint de 150 x 150 um nunca se ha dibujado."],
             why="Estos alimentan directamente los problemas 1 y 5 y podrían empeorar ambos.",
             sols=[("Medir o simular un inductor de película",
                    "Es barato, y confirma o invalida el presupuesto de pérdidas sobre el que "
                    "descansa todo el diseño."),
                   ("Dibujar un canal",
                    "Un layout de una sola celda responde la pregunta del footprint y le pone "
                    "precio al inductor extra que pide el retorno aislado.")]),
    ],
    ev_h="La evidencia detrás de los dos números duros",
    ev_sub="El déficit de transconductancia y la corrección del escalado",
    ev_t1="Fuerza del dispositivo medido - y dónde toman el control los contactos",
    ev_x1="longitud de canal L (um)",
    ev_y1="Kp extraído (uA/V$^2$)",
    ev_note1="0.72 uA/V$^2$ intrínseco",
    ev_t2="Diez canales: dónde se les pidió estar, dónde caen",
    ev_x2="frecuencia objetivo de diseño (MHz)",
    ev_y2="modo simulado (MHz)",
    ev_leg=("ideal", "retorno compartido (hoy)", "retorno aislado (corrección)"),
    ev_verif_h="Verificaciones hechas en esta sesión",
    ev_verif=[
        "Lector de .xls crudo contra los reportes de Isat preexistentes: 172 / 172 exacto.",
        "Extracción de curvas de transferencia a VDS = 0.1 / 0.1 / 1 / 2 V dio 26.4 /",
        "27.0 / 27.1 / 28.4 uA/V^2 - 7 % de dispersión sobre un rango 20x de tensión de",
        "drenaje - y el umbral extraído reproduce la columna VT del propio instrumento.",
        "El generador de netlist reproduce el punto de diseño verificado de dos canales",
        "antes de usarse para cualquier otra cosa.",
        "",
        "Sin resolver: la interacción entre canales no se pudo re-medir, porque el",
        "análisis AC es lineal y no detecta oscilación. El 9 % que llevan las notas del",
        "proyecto hay que rederivarlo con .pz o transitorio.",
    ],
    next_h="Qué falta, y en qué orden",
    next_sub="Secuenciado para que las decisiones que pueden invalidar trabajo vayan primero",
    nexts=[("Ahora", GREEN, [
                "Adoptar el retorno aislado en todo el trabajo posterior (scale/gen_nchan.py).",
                "Medir Cox sobre un pad de área conocida; registrar W/L con cada dispositivo.",
                "Rederivar la interacción entre canales con .pz o transitorio, no con AC."]),
           ("Después", AMBER, [
                "Decidir la pregunta de la alimentación - es una decisión de proyecto, no un ajuste.",
                "Prueba de ingeniería de contactos, y luego re-extraer el modelo.",
                "Medir o simular un inductor de película delgada realista (Q0)."]),
           ("Luego", GREY, [
                "Diseñar el lazo de control de amplitud una vez conocido el gm real.",
                "Hacer el layout de un canal y ponerle precio al área del retorno aislado.",
                "Simular el camino de señal EMG de punta a punta (+-5 mV, 20 Hz - 2 kHz)."])],
    dec_h="La decisión que bloquea todo lo demás",
    dec=[
        "La alimentación de 1.5 V se heredó de un supuesto de CMOS de silicio, no de un",
        "requisito de la aplicación. Cualquier tecnología de TFT - no solo esta - va a",
        "batallar para entregar transconductancia de miliamperios desde ese riel.",
        "",
        "Existen tres caminos y llevan a proyectos distintos:",
        "",
        "   1. Subir la alimentación, y reabrir los presupuestos de potencia y seguridad.",
        "   2. Subir Cox con un stack de compuerta high-k o más delgado, y quedarse en 1.5 V.",
        "   3. Quedarse en 1.5 V y cambiar el dispositivo activo, saliendo del TFT.",
        "",
        "Nada río abajo - diseño del AGC, presupuesto de potencia, layout - se puede",
        "cerrar antes que esto. Conviene tomarla deliberadamente, con UCLA en la sala,",
        "en vez de caer en ella por omisión.",
    ],
    colophon=("Detalle detrás de cada número de este reporte: "
              "report/device_and_scaling_findings.pdf\n"
              "Código de extracción y simulación: tools/, tft/, scale/"),
)


# ------------------------------------------------------------- helpers ----
def header(fig, C, text, sub=None):
    fig.text(0.07, 0.955, text, size=15, weight="bold", color=INK)
    if sub:
        fig.text(0.07, 0.933, sub, size=9.5, color=GREY)
    fig.add_artist(plt.Line2D([0.07, 0.93], [0.923, 0.923], color=BLUE, lw=1.6))


def footer(fig, C, n):
    fig.text(0.93, 0.035, str(n), size=8.5, color=GREY, ha="right")
    fig.text(0.07, 0.035, C["running"], size=8, color=GREY)


def wrap(fig, x, y, text, width, size, color, dy):
    words, line = text.split(), ""
    for w in words:
        if len(line) + len(w) + 1 > width:
            fig.text(x, y, line, size=size, color=color)
            y -= dy
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        fig.text(x, y, line, size=size, color=color)
        y -= dy
    return y


# --------------------------------------------------------------- pages ----
def page_cover(pdf, C):
    fig = plt.figure(figsize=A4)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0.62, 1, 0.38]); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, color=BLUE, alpha=0.06))
    fig.text(0.5, 0.855, C["kicker"], ha="center", size=12,
             color=BLUE, weight="bold")
    fig.text(0.5, 0.800, C["title"], ha="center", size=19, weight="bold",
             color=INK, linespacing=1.25, va="center")
    fig.text(0.5, 0.755, C["subtitle"], ha="center", size=12, color=GREY)
    fig.text(0.5, 0.705, C["people"], ha="center", size=9, color=GREY)
    fig.text(0.5, 0.672, C["date"], ha="center", size=9, color=GREY)

    fig.text(0.07, 0.575, C["stand_h"], size=13, weight="bold", color=BLUE)
    y = 0.550
    for line in C["stand"]:
        if line == "":
            y -= 0.010
        else:
            fig.text(0.07, y, line, size=10, color=INK)
            y -= 0.0188

    for i, (big, lab, col) in enumerate(C["tiles"]):
        x = 0.07 + i * 0.293
        ax2 = fig.add_axes([x, 0.075, 0.265, 0.115]); ax2.axis("off")
        ax2.add_patch(FancyBboxPatch((0.02, 0.05), 0.96, 0.9,
                                     boxstyle="round,pad=0.02",
                                     fc=col, ec="none", alpha=0.10))
        ax2.text(0.5, 0.66, big, ha="center", size=15, weight="bold", color=col)
        ax2.text(0.5, 0.26, lab, ha="center", size=8.3, color=GREY, linespacing=1.5)
    pdf.savefig(fig); plt.close(fig)


def page_scorecard(pdf, C):
    reqs = C["reqs"]
    fig = plt.figure(figsize=A4)
    header(fig, C, C["score_h"], C["score_sub"])
    ax = fig.add_axes([0.07, 0.30, 0.86, 0.60]); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, len(reqs) + 1.4)

    for xpos, lab in zip((0.005, 0.30, 0.50, 0.875), C["score_cols"]):
        ax.text(xpos, len(reqs) + 0.75, lab, size=8, weight="bold", color=GREY)
    ax.plot([0, 1], [len(reqs) + 0.55] * 2, color=GREY, lw=0.8)

    for i, (req, tgt, got, st) in enumerate(reqs):
        y = len(reqs) - i - 0.35
        col = STATE_COLOR[st]
        if i % 2 == 0:
            ax.add_patch(Rectangle((0, y - 0.30), 1, 0.80, color=GREY, alpha=0.05))
        ax.text(0.005, y, req, size=8.6, color=INK, weight="bold", va="center")
        ax.text(0.30, y, tgt, size=8.2, color=INK, va="center")
        ax.text(0.50, y, got, size=8.2, color=GREY, va="center")
        ax.add_patch(FancyBboxPatch((0.855, y - 0.19), 0.145, 0.38,
                                    boxstyle="round,pad=0.01",
                                    fc=col, ec="none", alpha=0.16))
        ax.text(0.9275, y, C["state_label"][st], size=7.2, color=col,
                weight="bold", ha="center", va="center")

    fig.text(0.07, 0.255, C["howread_h"], size=11, weight="bold", color=BLUE)
    for i, t in enumerate(C["howread"]):
        fig.text(0.07, 0.228 - i * 0.0175, t, size=8.6, color=GREY if i else INK)
    footer(fig, C, 2)
    pdf.savefig(fig); plt.close(fig)


def page_achieved(pdf, C):
    fig = plt.figure(figsize=A4)
    header(fig, C, C["ach_h"], C["ach_sub"])
    y = 0.885
    for title, col, lines in C["achieved"]:
        fig.add_artist(plt.Line2D([0.07, 0.075], [y - 0.005, y - 0.005],
                                  color=col, lw=6, solid_capstyle="butt"))
        fig.text(0.088, y - 0.009, title, size=11, weight="bold", color=col)
        y -= 0.030
        for ln in lines:
            fig.text(0.088, y, ln, size=8.8, color=INK,
                     family="monospace" if ln.startswith("    ") else "sans-serif")
            y -= 0.0178
        y -= 0.016
    footer(fig, C, 3)
    pdf.savefig(fig); plt.close(fig)


def page_problem(pdf, C, prob, pageno):
    fig = plt.figure(figsize=A4)
    sev_col = {"BLOCKING": RED, "HIGH": AMBER,
               "MEDIUM": GREY, "SOLVED": GREEN}[prob["sev"]]
    header(fig, C, f"{C['prob_word']} {prob['rank']} - {prob['title']}")

    ax = fig.add_axes([0.07, 0.885, 0.16, 0.028]); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.06",
                                fc=sev_col, ec="none", alpha=0.18))
    ax.text(0.5, 0.5, C["sev_label"][prob["sev"]], ha="center", va="center",
            size=8.5, weight="bold", color=sev_col)

    y = 0.845
    fig.text(0.07, y, C["found_h"], size=11, weight="bold", color=BLUE)
    y -= 0.028
    for ln in prob["what"]:
        fig.text(0.07, y, ln, size=9.3, color=INK)
        y -= 0.0195
    y -= 0.012
    fig.text(0.07, y, prob["why"], size=9, color=GREY, style="italic")
    y -= 0.045

    fig.text(0.07, y, C["sols_h"], size=11, weight="bold", color=BLUE)
    y -= 0.032
    for name, text in prob["sols"]:
        fig.text(0.085, y, name, size=9.6, weight="bold", color=INK)
        y -= 0.021
        y = wrap(fig, 0.085, y, text, 84, 8.9, GREY, 0.0172)
        y -= 0.014
    footer(fig, C, pageno)
    pdf.savefig(fig); plt.close(fig)


def page_evidence(pdf, C):
    rows = list(np.load(os.path.join(ROOT, "tft", "params.npy"), allow_pickle=True))
    fig = plt.figure(figsize=A4)
    header(fig, C, C["ev_h"], C["ev_sub"])

    ax = fig.add_axes([0.10, 0.60, 0.80, 0.27])
    for chip, col, mk in (("TFT1", BLUE, "o"), ("TFT2", RED, "^"), ("TFT3", GREEN, "s")):
        r = [x for x in rows if x["chip"] == chip]
        if r:
            ax.semilogx([x["L"] for x in r], [x["kp_lin"] * 1e6 for x in r],
                        mk, color=col, ms=4.5, alpha=0.75, label=chip)
    ax.axhline(0.717, ls="--", color=GREY, lw=1)
    ax.text(8.6, 0.76, C["ev_note1"], size=7.8, color=GREY)
    ax.set_xlabel(C["ev_x1"], size=9)
    ax.set_ylabel(C["ev_y1"], size=9)
    ax.set_title(C["ev_t1"], size=10, color=INK)
    ax.legend(frameon=False, fontsize=8)
    ax.grid(alpha=0.25, which="both")
    ax.tick_params(labelsize=8)

    ax = fig.add_axes([0.10, 0.235, 0.80, 0.27])
    ladder = [50.0, 66.6667, 83.3333, 100.0, 116.6667, 133.3333,
              150.0, 166.6667, 183.3333, 200.0]
    shared = [65.9, 88.7, 111.7, 134.7, 158.0, 181.3, 204.7, 228.2, 251.9, 275.8]
    iso = [49.4, 65.9, 82.3, 98.8, 115.3, 131.8, 148.3, 164.7, 181.2, 197.6]
    ax.plot([40, 210], [40, 210], "--", color=GREY, lw=1, label=C["ev_leg"][0])
    ax.plot(ladder, shared, "o", color=RED, ms=6, label=C["ev_leg"][1])
    ax.plot(ladder, iso, "s", color=GREEN, ms=6, label=C["ev_leg"][2])
    ax.set_xlabel(C["ev_x2"], size=9)
    ax.set_ylabel(C["ev_y2"], size=9)
    ax.set_title(C["ev_t2"], size=10, color=INK)
    ax.legend(frameon=False, fontsize=8)
    ax.grid(alpha=0.25)
    ax.tick_params(labelsize=8)
    ax.set_xlim(40, 210)

    fig.text(0.07, 0.175, C["ev_verif_h"], size=11, weight="bold", color=BLUE)
    warn = C["ev_verif"].index("")
    for i, t in enumerate(C["ev_verif"]):
        fig.text(0.07, 0.148 - i * 0.0172, t, size=8.6,
                 color=RED if i > warn else GREY)
    footer(fig, C, 11)
    pdf.savefig(fig); plt.close(fig)


def page_next(pdf, C):
    fig = plt.figure(figsize=A4)
    header(fig, C, C["next_h"], C["next_sub"])
    y = 0.87
    for phase, col, items in C["nexts"]:
        ax = fig.add_axes([0.07, y - 0.005, 0.10, 0.030]); ax.axis("off")
        ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.06",
                                    fc=col, ec="none", alpha=0.18))
        ax.text(0.5, 0.5, phase, ha="center", va="center", size=10,
                weight="bold", color=col)
        y -= 0.055
        for it in items:
            fig.add_artist(plt.Line2D([0.085, 0.092], [y + 0.004, y + 0.004],
                                      color=col, lw=2.5))
            y = wrap(fig, 0.10, y, it, 82, 9.3, INK, 0.0185)
            y -= 0.008
        y -= 0.028

    fig.text(0.07, y, C["dec_h"], size=12, weight="bold", color=RED)
    y -= 0.032
    for t in C["dec"]:
        fig.text(0.07, y, t, size=9.3,
                 color=BLUE if t.startswith("   ") else INK,
                 weight="bold" if t.startswith("   ") else "normal")
        y -= 0.0195

    fig.text(0.07, 0.052, C["colophon"], size=8.2, color=GREY, style="italic")
    footer(fig, C, 12)
    pdf.savefig(fig); plt.close(fig)


def build(lang):
    C = CONTENT[lang]
    out = os.path.join(ROOT, C["outfile"])
    with PdfPages(out) as pdf:
        page_cover(pdf, C)
        page_scorecard(pdf, C)
        page_achieved(pdf, C)
        for i, p in enumerate(C["problems"]):
            page_problem(pdf, C, p, 4 + i)
        page_evidence(pdf, C)
        page_next(pdf, C)
        pdf.infodict()["Title"] = C["meta_title"]
        pdf.infodict()["Author"] = "UCLA-UCI collaboration"
    print("wrote", out)


if __name__ == "__main__":
    langs = sys.argv[1:] or ["en", "es"]
    for lg in langs:
        build(lg)
