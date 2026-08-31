# Sizing search for the OPAM / OPAM2 IGZO amplifiers

Everything here works on flat, parameterised copies of the two schematics, so
a candidate sizing can be simulated without opening xschem.  The schematics
stay the source of truth: `apply_sizing.py` writes the result back into them,
and the netlist xschem then produces is checked device-for-device against the
core netlists in this directory.

## Files

| File | What it is |
|---|---|
| `opam_core.spice`, `opam2_core.spice` | the two amplifiers, one `.param` per function group |
| `tb_common.py` | builds a testbench around a core, runs ngspice, parses the OP / AC / DC results |
| `score.py` | the objective: maximise gain subject to bias, model-range, swing and power constraints |
| `optimize.py` | the search itself - steepest descent over single-dimension moves, scored at the worst corner |
| `search_opam.py` | runs the OPAM starts one at a time, writing `best_opam.json` as each lands |
| `validate.py`, `report.py` | corners, operating point and mismatch margin for a finished sizing |
| `apply_sizing.py` | writes a sizing back into the `.sch` files and fixes the source/drain wiring |
| `search_opam.py`, `refine_opam.py` | OPAM search drivers, writing `best_opam.json` as they go |
| `apply_opam.py` | writes the OPAM result into `OPAM.sch` / `test.sch` and checks the netlist |
| `opam_split_core.spice` | experiment only: OPAM with a second bias pin, used to measure what the shared BIAS costs |
| `measure.py`, `install_measure.py` | the shared measurement block, and its installer |
| `make_testbench.py`, `make_core.py`, `make_biased_schematic.py` | generators: the two testbenches, the parameterised cores, and the self-biased schematic |
| `check_schematics.py` | every device in every schematic against the netlist that was simulated |
| `bias_gen.py`, `search_biased.py` | the on-chip bias reference and its sizing search |
| `bfield.py` | magnetic field: the classical sweep, gain against field per probe tone, and where to put the tone |
| `compensate.py` | the compensation attempts, and why they do not work here |
| `closed_loop.py`, `search_stable.py` | closing the loop, and re-sizing for a phase margin |
| `make_opam_structure.py` | OPAM.sch.base - the structural fixes, kept apart from the sizing |
| `report_data.py`, `figures.py`, `report_text.py`, `make_opam_report.py` | the two PDFs, every number computed live |
| `tb_opam2.spice`, `tb_opam.spice` | standalone testbenches with the final numbers |

## Five things that are easy to get wrong here

**The bulk used to follow the `s` pin - it no longer does.**  `igzo_tft` wires
the intrinsic device as `M1 di g si si`.  A real TFT sits on glass and has no
bulk, so it is symmetric; the model was not.  With live junctions, a device
drawn with `s` on the high side forward-biased its bulk-drain junction,
conducted, and clamped the two nodes about 0.58 V apart - which is exactly why
neither of these amplifiers amplified anything.  Both schematics were drawn
that way in most of their devices.

The PDK fixed it at the source (commit `67779ed`, "Make the device symmetric,
and give it a magnetic field"): all four corners now carry
`Is=0 Js=0 Cbd=0 Cbs=0 Cj=0 Cjsw=0`, so the junctions are inert and `d` and `s`
are genuinely interchangeable.  The re-orientation applied here is therefore a
no-op today, and it is kept only because it is correct and matches the
schematics.  It is recorded because the failure it fixed cost a lot of
debugging, and because the trick it used is still useful: swapping D and S in
xschem needs no rewiring, since the symbol's three pin boxes land on the same
three coordinates for the flag pairs `(rot,flip) = (0,0)<->(2,1)` and
`(2,0)<->(0,1)`, with only D and S exchanged.

**Score at the worst corner, not the best one.**  Scoring on `best` alone
finds knife edges.  An early run reached 73 dB on OPAM2 and fell to -109 dB at
`tt`, with the input pair biased at 17 mV of overdrive - below anything a
level-1 model can claim, since it has no subthreshold region at all.  Hence
`VOV_MIN` in `score.py`, and hence the worst-corner objective.

**A device in the source of a common-source stage must not be a current
source.**  OPAM's XM11/XM17 sit between the second stage's amplifying device
and VSS.  Held in saturation - which is what a blanket "everything in
saturation" rule asks for - they are a current source in the source, they
degenerate gm by gm/gds (about 1600x here), and the whole second stage gives
-0.5 dB.  They belong in triode, as degeneration resistors.  Fixing that one
constraint took OPAM from 22 dB to 33 dB at the worst corner, and the second
stage from -0.5 dB to +33 dB.  Getting there also needs the stage current
raised at the same time, because a low `net10` forces a large overdrive on
XM18 and collapses its gm: three groups have to move together, which is why
the coupled moves and the hand-built seeds exist.

**Watch what the search buys with area.**  Left free it grew C1/C2 to 2000 um
a side - a 4 mm2 plate - for 0.35 dB, and stretched the cut-off device XM14/
XM20 to 5000 x 2000 um for another 0.6 dB.  A device held in cut-off
contributes only its overlap capacitance, which goes as W alone, so all that
length bought nothing at all: `l_bf` is pinned at the minimum and the
capacitors at the drawn 160.64 um.  That is 10 mm2 of area for 0.63 dB.

**The two amplifiers need different figures of merit.**  OPAM2's gain is flat
from DC.  OPAM's bootstrap load is diode-connected at DC and only becomes a
current source above the corner set by C1/C2, so it has almost no DC gain by
design: its figure of merit is the mid-band gain, and its output swing has to
be measured in transient rather than from a DC sweep.

## The measurement block

`measure.py` renders one `.control` block and `install_measure.py` puts it in
every testbench, so the schematic benches and the standalone ones cannot report
different numbers for the same circuit - which they did, by 3.9 dB, until the
stimulus was made identical.  Five groups: operating point, Bode magnitude and
phase, the DC transfer curve, a sine inside the band, and a cross-check that the
AC gain and the transient gain agree.

Two things in it are derived rather than chosen, and both had to be:

  * the sine FREQUENCY comes from the measured f-3dB.  Parked at 200 Hz on a
    66 Hz corner the transient gain read 9.7 dB low, for a reason that has
    nothing to do with the circuit.
  * PHASE MARGIN is measured against the DC phase, not against zero.  OPAM
    inverts and already sits at 180 degrees, and without subtracting it the
    margin came out as -178 degrees.

The transient settles for 200 cycles before it is measured.  OPAM's bootstrap
gate node is held only by the off-device leakage, so the signal pumps charge into
it and the node drifts for tens of seconds; measured over 12 cycles the gain
reads several dB high and is still moving.

## Phase margin, and what it costs

The gain-optimal OPAM has -36 degrees of phase margin.  Compensation does not
rescue it and the reason is worth keeping:

  * a Miller capacitor puts its right-half-plane zero at gm/C, and with gm in
    microsiemens and mim plates in picofarads that zero lands on the unity-gain
    frequency instead of far above it.  Measured: the margin goes from -36 to
    -117 degrees.  A nulling device in triode gets it back to about -29, no
    better than doing nothing.
  * loading the dominant node creates no zero, but needs a 2000 x 2000 um plate -
    4 mm2, 6.3 nF - to buy 2.4 degrees.

So the margin has to come out of the sizing, and it does: `pm_min` in the
Design.  A second constraint has to come with it, `follow_tol`.  The first
stable sizing had 45 degrees of margin and still latched as a unity-gain buffer,
because its output range was 2.7-6.6 V while its input common mode was 1.8 V -
the two never met, so the loop had nowhere to settle.  Requiring the output to
be able to sit at the common mode fixes that and costs another 12 dB.

`closed_loop.py` is the check that matters: wire OUT back to INP - the inverting
input, since OPAM's DC transfer has a negative slope - step it, and look.  All
three corners settle with under 4 % overshoot.  Note the closed-loop gain error:
with only 12.6 dB of open-loop gain at the worst corner there is not enough loop
gain for an accurate buffer, only a stable one.

The gain-optimal sizing is kept in `best_opam_maxgain.json`.  It is still the
right answer for an open-loop gain block, which is what both papers characterise.

## Nothing is written by hand twice

Every file that could hold the same number in two places is generated:

    make_opam_structure.py   OPAM.sch.base   structural fixes, no sizing
    apply_opam.py            OPAM.sch        sizing, from best_opam.json
    make_testbench.py        test*.sch       the benches
    make_core.py             *_core.spice    cores, from the schematics
    install_measure.py       tb_*.spice      measurement block AND .param sizing
    check_schematics.py      -               every device, both directions

That list exists because each entry was a bug first: an input pair left at
L = 10 um, capacitors at 100x50 instead of 160.64, r_off resistors that lived
only in the core, and a standalone bench still holding the gain-optimal sizing
after the design had been re-sized - which put a stale 10.9 dB into the report.

## Reproducing

    python3 check_schematics.py    # run this first, and after any edit
    python3 optimize.py opam2      # full search, writes results_opam2.csv
    python3 search_opam.py         # OPAM search, writes best_opam.json
    python3 report.py opam2        # corners, operating point, mismatch margin
    python3 report.py opam
    python3 apply_sizing.py        # (via apply_opam.py) back into the schematics
    python3 search_biased.py       # the self-biased variant
    python3 bfield.py              # magnetic field
    python3 make_opam_report.py    # both PDFs, into ~/Documents
    ngspice -b tb_opam2.spice      # the final sizings, standalone
    ngspice -b tb_opam.spice

`apply_sizing.patch` always reads from `<name>.sch.orig`, so re-running it is
safe: the orientation fix toggles two flags and would otherwise undo itself.
