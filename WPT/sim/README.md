# WPT link: coil design, rectifier sizing, and what the link actually does

Everything here works on flat, parameterised copies of `WPT.sch`, so a
candidate can be simulated without opening xschem. The schematic stays the
source of truth for layout and LVS; `make_wpt_schematic.py` writes the chosen
values back into it, and nothing that holds a number is written by hand twice.

**The headline, so it is not buried:** the link does not work. 0.80 V into a
10 k load for 858 W at the driver, an efficiency of 7.5e-8. The geometry is
optimal and the rectifier is sized; the ceiling is the receive coil's Q of
0.0064. See `WPT_diseno_es.pdf` for the whole argument.

## Files

| File | What it is |
|---|---|
| `link.py` | mutual inductance, coupling, the k²Q₁Q₂ figure of merit and η_max; `--selftest` checks it against the dipole limit |
| `proximity.py` | Dowell's proximity-effect resistance for multi-layer windings, which `coil_core` does not model |
| `rx_coil.py` | the receive coil: every legal spiral in 1000 × 1000 µm, four objectives, the regime test |
| `tx_coil.py` | the transmit coil: copper wire, both topologies, every gauge |
| `tb_wpt.py` | the ngspice driver — netlist, AC, transient, steady state, raw traces |
| `wpt_core_gen.py` | writes `wpt_core.spice`, the same link as a standalone netlist |
| `rectifier.py` | sizing the two diode-connected TFTs, at every corner |
| `sweep.py` | frequency, distance, load, and the coupling-capacitor experiment |
| `make_wpt_schematic.py` | the values back into `WPT.sch`, plus what the drawing was missing |
| `figures.py`, `report_text.py`, `make_wpt_report.py` | the PDF, every number computed live |

## Reproducing

```bash
python3 link.py --selftest        # the magnetics, against closed-form limits
python3 proximity.py              # Dowell, against its own asymptotes
python3 rx_coil.py                # rx_coil.json, rx_sweep.csv     (~30 s)
python3 rx_coil.py --check-tx     # the ranking does not depend on the TX
python3 tx_coil.py                # tx_coil.json, tx_sweep.csv     (~20 s)
python3 tx_coil.py --selftest     # winding placement and coupling
python3 tb_wpt.py --check         # the flat coils against the PDK subcircuit
python3 rectifier.py              # rectifier.json, rect_sweep.csv (~2 min)
python3 sweep.py                  # sweeps.json, sweeps.csv        (~4 min)
python3 make_wpt_schematic.py     # ../WPT.sch
python3 wpt_core_gen.py           # wpt_core.spice
ngspice -b wpt_core.spice         # the link by hand, no Python
python3 make_wpt_report.py        # ../WPT_diseno_es.pdf
```

Run them in that order: each reads the JSON the previous one wrote.

## Seven things that were wrong first, and are easy to get wrong again

**The objective is the induced voltage, not the figure of merit.** k²Q₁Q₂ is
the right criterion for a load matched in impedance. This load is two
diode-connected TFTs, and below threshold they conduct nothing at all, so what
has to be maximised first is the open-circuit EMF — which means turn AREA, not
the best ratio of area to resistance. The two criteria pick coils a factor 6.5
apart in M, and they sit at opposite corners of the space.

**There is no tank.** The first version of `rx_coil.py` treated the three
external capacitors as tuning elements and only allowed geometries resonating
inside the band. At 1 µH and 1 µF both reactances are about 1 Ω and the coil's
resistance is 500: R beats them by three orders of magnitude everywhere in the
band, so the loop is a resistor and the resonance is a number with no circuit
behind it. `rx_coil.regime()` is that check, and it now runs every time.

**`5.0 * 1e-6` is one ulp below `5e-6`.** The DRC floor is 5 µm, the grid was
held in metres, and the minimum-width corner — where maximum inductance lives —
was silently rejected as a violation. Lengths are carried in microns now and
converted only where the physics is called.

**An optimiser finds whatever the loss model forgot.** `coil_core`'s AC
resistance is an isolated-wire model. Scored with it, the transmit sweep walked
into the deepest multi-layer winding the grid allowed and claimed Q = 845 at
500 kHz. The missing term was proximity loss between layers, which grows as m².
`proximity.py` supplies it and the optimum moves.

**A separation is measured from the near face of a winding, not its middle.**
`link.solenoid_axial` centres the turns on zero, so a 16 mm solenoid placed at
a 5 mm gap had the receiver *inside* it, and reported a coupling to match.
`tx_coil.py --selftest` asserts the closest turn sits at the nominal gap, and
cross-checks the elliptic sum against the dipole approximation.

**The seed capacitor has two inequalities and they are easy to invert.** The
output filter is 10 µF against a 10 k load: a 0.1 s time constant against a
2 µs carrier. `steady_state()` finds the answer on a small capacitor and
confirms it on the real one. That capacitor's time constant must be *much
larger* than the carrier period and much smaller than the simulated span —
sized the other way round it does not smooth at all, and the "DC output" swung
between −1.6 and +1.7 V while every number downstream looked plausible.

**ngspice will not couple into a subcircuit.** `K1 L2 XL1.L1 k` gives
`Fatal error: k1: coupling to non-existent inductor xl1.l1`. `ind_igzo` is an
L in series with an R and nothing else, so the flat core loses nothing;
`tb_wpt.py --check` proves the two are electrically identical to the last
digit. This is why the coupling is not in `WPT.sch`.

## Two more that cost less but still cost

`meas ... FIND ... AT=` refuses the last time point of a run ("out of
interval"), so the transient runs one period past the window it measures. And
`meas` takes a vector, not an expression: `meas ac x FIND mag(i(V1))` produces
nothing at all, silently — it needs a `let` first.

## What the schematic was missing

No ground anywhere, so there was no node 0 and nothing could be simulated. C3's
lower plate one segment short of the ground rail. No load, so no efficiency to
measure. No coupling between the two coils. And no series tuning on the
transmit side, which alone is a factor of 691 in efficiency.
