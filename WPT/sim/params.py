#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every knob of the WPT link, in one file.

CHANGE THINGS HERE.  Everything downstream reads this module, so editing a
value below and re-running is the whole workflow - no script carries its own
copy of a number any more.  Run `python3 params.py` to print the configuration
and have it checked for combinations that do not make sense.

Each value carries where it came from, because that matters more than the
number:

    measured   somebody put a probe on silicon and this is what it read
    computed   a sweep in this directory produced it; the file is named
    chosen     a design decision, with the reason next to it
    assumed    nobody has measured it and the result depends on it

The `assumed` ones are the dangerous ones.  There are two, and both are
flagged again by check().
"""

import math

# ==========================================================================
# THE LINK
# ==========================================================================

F_OP = 500e3            # Hz   chosen: the top of the usable band.  The induced
                        #      voltage grows with frequency and nothing inside
                        #      the band constrains the choice - there is no
                        #      tank, see rx_coil.regime().
F_BAND = (100e3, 500e3) # Hz   chosen: the band asked for
F_T_TFT = 1.2e6         # Hz   measured: fT at L = 10 um.  1.9 MHz at L = 5 um.
                        #      Above this the transistors stop rectifying.

Z_MM = 0.5              # mm   chosen: CONTACT.  The chip sits on the transmit
                        #      coil.  Phase 1 assumed 5 mm without asking, and
                        #      that cost a factor 4.6 in efficiency.

K_OVERRIDE = None       #      Set a number to force the coupling and ignore
                        #      the geometry entirely - useful for asking "what
                        #      if k were X".  None means compute it from the
                        #      two coils.  k = 1 is not reachable here; see
                        #      k_study.py.

P_IN_W = 1000.0         # W    chosen: the drive the rectifier needs to reach
                        #      threshold at all.  It is a lot, and that is a
                        #      result rather than a setting.
R_SRC = 1.0             # ohm  assumed: driver output resistance

# ==========================================================================
# THE RECEIVE COIL - on the chip
# ==========================================================================
# computed by rx_coil.py: the maximum-turn-area square spiral inside the
# 1000 x 1000 um budget, which is the right objective for a threshold-limited
# rectifier.  Redrawable in the ind_igzo PCell with the geometry below.

RX_L = 1012.87e-9       # H    computed
RX_R = 497.37           # ohm  computed, at 1 um of gold
RX_Q = 0.00639771       #      computed, at F_OP

RX_SHAPE = "square"     #      computed
RX_N = 49               #      computed
RX_W_UM = 5.0           # um   computed - the DRC floor, GATE.1 / SD.1
RX_GAP_UM = 5.0         # um   computed - the DRC floor, GATE.2 / SD.2
RX_T_UM = 1.0           # um   ASSUMED.  The metal thickness.  Nobody has
                        #      measured it, and it is a factor 20 in Q between
                        #      50 nm and 1 um - the single most influential
                        #      number in this whole study.
RX_AREA_UM = 1000.0     # um   chosen: the area budget

# ==========================================================================
# THE TRANSMIT COIL - copper wire, off-chip
# ==========================================================================
# computed by tx_coil.py at z = 5 mm.  Re-run it after changing Z_MM: the
# optimum at contact is not the optimum at 5 mm.

TX_TOPOLOGY = "solenoid"
TX_D_MM = 1.0           # mm   former diameter
TX_N = 8                #      turns per layer
TX_LAYERS = 4           #      layers
TX_AWG = 36             #      wire gauge, ASTM B258 - 0.127 mm of copper
TX_L = 0.837231e-6      # H    computed by k_study.py at Z_MM
TX_R = 0.80806          # ohm  computed, skin + Dowell proximity
TX_Q = 3.255            #      computed, at F_OP

# WHY THIS COIL AND NOT THE 171 uH ONE PHASE 1 CHOSE.  Phase 1 optimised at a
# 5 mm separation that was never confirmed; the real answer is contact.  At
# 0.5 mm the whole ranking moves, and it moves the way the user remembered:
# a small, low-inductance transmitter couples far better.  Measured in ngspice,
# not argued -
#
#     171 uH, 15 mm former, 50t x 2   k = 0.0077   V(C3) =  2.05 V
#     0.84 uH, 1 mm former, 8t x 4    k = 0.116    V(C3) = 20.23 V
#
# a factor 15 in coupling and 10 in output, from a coil that is also far
# easier to wind: 8 turns in 4 layers on a 1 mm former, 139 mm of AWG 36.
# k = M/sqrt(L1 L2), so dropping L1 raises k even when M does not move.

TX_TUNE = True          #      chosen: series-resonate the transmit loop.  NOT
                        #      optional - it is worth a factor 691 in
                        #      efficiency.  wL_tx is 539 ohms against 10.6 of
                        #      resistance; untuned, the driver delivers almost
                        #      nothing.

# ==========================================================================
# THE RECTIFIER
# ==========================================================================

TFT_W = 6e-3            # m    computed by rectifier.py
TFT_L = 10e-6           # m    CHOSEN BY YOU.  The sweep prefers 5 um, the DRC
                        #      floor; 10 um is your call and the report says
                        #      what it costs.
TFT_OV = 2e-6           # m    computed - the overlap only costs capacitance
CORNER = "tt"           #      chosen: sizing is judged at the worst of the
                        #      three, but a single run defaults to typical
CORNERS = ("best", "tt", "all")
VTO = {"best": 0.09, "tt": -0.26, "all": -0.53}   # measured
                        #      NEGATIVE on two of three: a diode-connected TFT
                        #      with a negative threshold conducts at zero bias
                        #      and does not block.  No width fixes that.

# measured, design.ngspice
COX_AREA = 1.564e-3     # F/m2  50 nm Al2O3
RC_W = 3.3              # ohm*m per contact

# ==========================================================================
# THE PASSIVES - external, not from the PDK
# ==========================================================================

CAPS = (1e-6, 2e-6, 10e-6)   # F  chosen: the parts that exist
C_RES = 10e-6           # F    chosen: the doubler's DC block.  It is NOT
                        #      tuning anything - at 10 uF its reactance here is
                        #      32 milliohms against the coil's 497 ohms.  Any
                        #      of the three works; the largest is the lowest
                        #      impedance.
C_OUT = 10e-6           # F    chosen: the output filter.  Sets the ripple and
                        #      the settling time, not the output voltage.
R_LOAD = 10e3           # ohm  computed: the load that maximises efficiency.
                        #      Maximum VOLTAGE is at 300 k - a different load.

# ==========================================================================
# THE TRANSIENT BODE SWEEP
# ==========================================================================
# The Bode plot is built by running a transient at each frequency and reading
# the SETTLED value on C3, rather than by an AC sweep.  An AC sweep linearises
# the diodes, and the diodes are the circuit.

BODE_F_MIN = 10e3       # Hz
BODE_F_MAX = 5e6        # Hz   past fT on purpose, so the roll-off is visible
BODE_PTS_PER_DECADE = 8
BODE_SETTLE_TOL = 1e-3  #      relative drift between successive windows that
                        #      counts as settled
BODE_WINDOW_CYCLES = 20 #      cycles averaged for one reading
BODE_MAX_CYCLES = 20000 #      give up after this and SAY SO, rather than
                        #      reporting an unsettled point as if it converged
BODE_ABS_V = 1e-6       # V    an ABSOLUTE floor for "settled".  Without it the
                        #      low end of the sweep never converges: with the
                        #      transmitter tuned at F_OP, 10 kHz sees the
                        #      tuning capacitor as a 27 kohm open, the output
                        #      is 5e-10 V of numerical noise, and a RELATIVE
                        #      convergence test applied to noise walks to the
                        #      cycle cap every time.  Below this the answer is
                        #      zero, and saying so is the right answer.
BODE_PTS_PER_PERIOD = 200
BODE_RESONANCE_PTS = 14 #      EXTRA points clustered on the resonance.  A
                        #      logarithmic grid at 8 points per decade steps by
                        #      33 %, which near 500 kHz is 163 kHz - and the
                        #      tuned transmit loop has a Q of 46, so its peak
                        #      is 11 kHz wide.  The plain grid jumped clean
                        #      over it: the nearest point landed two
                        #      bandwidths out and the "peak" it reported was
                        #      0.31 V where the real one is 2.05 V.
BODE_RESONANCE_SPAN = 4.0   #  how many bandwidths either side to cover

# ==========================================================================
# SWEEP GRIDS
# ==========================================================================

K_GRID = [1e-3, 3e-3, 1e-2, 3e-2, 0.1, 0.3, 0.5, 0.8, 1.0]
TX_L_GRID_UH = [0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 200.0]
Z_GRID_MM = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
W_GRID = [100e-6, 300e-6, 1e-3, 3e-3, 6e-3, 10e-3, 20e-3]
RLOAD_GRID = [100, 300, 1e3, 3e3, 1e4, 3e4, 1e5, 3e5, 1e6]

# ==========================================================================
# PATHS AND TOOLS
# ==========================================================================

NGSPICE = "/foss/tools/bin/ngspice"
PDK_NGSPICE = "/foss/designs/TFT-MMM-LAB-PDK/libs.tech/ngspice"
PDK_TOOLS = "/foss/designs/TFT-MMM-LAB-PDK/tools"
PDK_PDF = "/foss/designs/TFT-MMM-LAB-PDK/docs/pdf"
RHO_AU = 2.44e-8        # ohm*m  gold - what the process assumes
RHO_CU = 1.68e-8        # ohm*m  copper - the transmit coil


# ==========================================================================
# Derived, and the checks
# ==========================================================================

def tx_resonant_c(f=None):
    """The series capacitor that cancels the transmit coil's reactance."""
    f = f or F_OP
    return 1.0 / ((2.0 * math.pi * f) ** 2 * TX_L)


def vamp_for_power(p_watt=None, r_src=None):
    """Source amplitude that puts p_watt into a resistive transmit loop."""
    p_watt = P_IN_W if p_watt is None else p_watt
    r = (R_SRC if r_src is None else r_src) + TX_R
    return math.sqrt(2.0 * p_watt * r)


def tx_loop_q(f=None):
    """Q of the series-tuned transmit loop - what sets the peak's width."""
    f = f or F_OP
    return 2.0 * math.pi * f * TX_L / (TX_R + R_SRC)


def bode_frequencies():
    """The sweep's frequency points: a log grid, plus the resonance resolved.

    The log grid alone is not enough.  Near F_OP it steps by 163 kHz while the
    tuned peak is 11 kHz wide, so it walks straight past the only interesting
    feature in the response and reports a maximum six times too low.  The extra
    points cover +-BODE_RESONANCE_SPAN bandwidths around F_OP.
    """
    decades = math.log10(BODE_F_MAX / BODE_F_MIN)
    n = max(2, int(round(decades * BODE_PTS_PER_DECADE)) + 1)
    grid = [BODE_F_MIN * (BODE_F_MAX / BODE_F_MIN) ** (i / (n - 1.0))
            for i in range(n)]
    if TX_TUNE and BODE_RESONANCE_PTS > 0:
        bw = F_OP / max(tx_loop_q(), 1e-9)
        half = BODE_RESONANCE_SPAN * bw
        m = BODE_RESONANCE_PTS
        grid += [F_OP - half + 2.0 * half * i / (m - 1.0) for i in range(m)]
        grid.append(F_OP)   # the tuned frequency itself, which an evenly
                            # spaced cluster straddles rather than hits: the
                            # nearest pair read 1.66 V where F_OP reads 2.05
    return sorted(f for f in set(grid) if BODE_F_MIN <= f <= BODE_F_MAX)


def check(verbose=True):
    """Complain about combinations that cannot mean what they say."""
    notes, warn, err = [], [], []

    if not (F_BAND[0] <= F_OP <= F_BAND[1]):
        err.append("F_OP (%.0f kHz) is outside F_BAND (%.0f - %.0f kHz)"
                   % (F_OP / 1e3, F_BAND[0] / 1e3, F_BAND[1] / 1e3))
    if F_OP > F_T_TFT:
        err.append("F_OP (%.2f MHz) is ABOVE the TFT's fT (%.2f MHz): the "
                   "diode-connected devices will not rectify there"
                   % (F_OP / 1e6, F_T_TFT / 1e6))
    else:
        notes.append("F_OP is %.1fx below fT - the transistors do rectify"
                     % (F_T_TFT / F_OP))

    if K_OVERRIDE is not None:
        if not (0.0 <= K_OVERRIDE <= 1.0):
            err.append("K_OVERRIDE = %g is not a coupling coefficient; "
                       "k lies in [0, 1]" % K_OVERRIDE)
        else:
            warn.append("K_OVERRIDE = %g is FORCED - the geometry is being "
                        "ignored.  The geometry gives about %.3e."
                        % (K_OVERRIDE, 0.00765))
    if Z_MM <= 0:
        err.append("Z_MM = %g: the coils cannot be at or through each other"
                   % Z_MM)

    if RX_W_UM < 5.0 or RX_GAP_UM < 5.0:
        err.append("RX_W_UM / RX_GAP_UM below 5 um violate GATE.1/.2 and "
                   "SD.1/.2 of this process")
    if TFT_L < 5e-6:
        err.append("TFT_L = %.1f um is below the 5 um DRC floor (SD.2)"
                   % (TFT_L * 1e6))

    if C_RES not in CAPS:
        warn.append("C_RES = %g F is not one of the capacitors that exist %s"
                    % (C_RES, CAPS))
    if C_OUT not in CAPS:
        warn.append("C_OUT = %g F is not one of the capacitors that exist %s"
                    % (C_OUT, CAPS))

    # The two assumptions everything rests on.
    warn.append("RX_T_UM = %g um is ASSUMED, not measured.  It is a factor %.0f "
                "in Q between 50 nm and 1 um and it scales the whole result."
                % (RX_T_UM, RX_T_UM / 0.05))
    warn.append("The TFT models are validated in DC ONLY; everything at %.0f "
                "kHz is extrapolation in frequency." % (F_OP / 1e3))

    # Is there a tank, or is the loop a resistor?
    w = 2.0 * math.pi * F_OP
    xl, xc = w * RX_L, 1.0 / (w * C_RES)
    if RX_R > 10 * max(xl, xc):
        notes.append("Receive loop is RESISTIVE: R = %.0f ohm against |wL| = "
                     "%.2f and |1/wC| = %.3f.  No tank, so the capacitor is a "
                     "DC block and the frequency is free in the band."
                     % (RX_R, xl, xc))
    else:
        warn.append("There is a real tank here now (R = %.0f, X = %.1f) - the "
                    "phase-1 conclusions about the capacitor no longer hold."
                    % (RX_R, max(xl, xc)))

    if verbose:
        print("WPT link configuration")
        print("  frequency      %.0f kHz   (band %.0f - %.0f kHz, fT %.2f MHz)"
              % (F_OP / 1e3, F_BAND[0] / 1e3, F_BAND[1] / 1e3, F_T_TFT / 1e6))
        print("  separation     %g mm" % Z_MM)
        print("  drive          %.0f W  ->  %.1f V amplitude"
              % (P_IN_W, vamp_for_power()))
        print("  RX coil        %.2f nH, %.0f ohm, Q = %.5f   (%s, n=%d, "
              "w=%g um, gap=%g um, %g um Au)"
              % (RX_L * 1e9, RX_R, RX_Q, RX_SHAPE, RX_N, RX_W_UM, RX_GAP_UM,
                 RX_T_UM))
        print("  TX coil        %.2f uH, %.3f ohm, Q = %.1f   (%s, %g mm, "
              "%dt x %d, AWG %d)"
              % (TX_L * 1e6, TX_R, TX_Q, TX_TOPOLOGY, TX_D_MM, TX_N,
                 TX_LAYERS, TX_AWG))
        print("  TX tuning      %s  (C = %.4g pF)"
              % ("series-resonant" if TX_TUNE else "NONE",
                 tx_resonant_c() * 1e12))
        print("  coupling       %s"
              % ("FORCED to %g" % K_OVERRIDE if K_OVERRIDE is not None
                 else "from the geometry"))
        print("  TFTs           W = %.0f um, L = %.0f um, ov = %.0f um"
              % (TFT_W * 1e6, TFT_L * 1e6, TFT_OV * 1e6))
        print("  passives       C_res = %g uF, C_out = %g uF, R_load = %g ohm"
              % (C_RES * 1e6, C_OUT * 1e6, R_LOAD))
        print("  Bode sweep     %.0f kHz - %.1f MHz, %d points, settle to %g"
              % (BODE_F_MIN / 1e3, BODE_F_MAX / 1e6, len(bode_frequencies()),
                 BODE_SETTLE_TOL))
        for label, items in (("note", notes), ("WARNING", warn),
                             ("ERROR", err)):
            for it in items:
                print("\n  %-8s %s" % (label + ":", it))
        print("\n  %s" % ("configuration is consistent" if not err else
                          "%d ERROR(S) - fix them before running anything"
                          % len(err)))
    return err, warn, notes


if __name__ == "__main__":
    import sys
    sys.exit(1 if check()[0] else 0)
