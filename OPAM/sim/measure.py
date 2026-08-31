#!/usr/bin/env python3
"""The measurement block shared by every testbench in this directory.

Five groups, in the order they have to run:

  1. operating point   where every device actually sits
  2. Bode              magnitude AND phase, f-3dB, unity gain, phase margin
  3. input/output      the DC transfer curve and the swing it allows
  4. sine in the band  a real waveform, and the gain it produces
  5. cross-check       the AC gain and the transient gain must agree

Two things are derived rather than guessed, which is what makes the block
survive a re-sizing:

  * the sine FREQUENCY is a decade below the measured f-3dB.  Put it above the
    corner and the transient gain reads low for a reason that has nothing to do
    with the circuit - at 200 Hz on a 66 Hz corner it came out 9.7 dB short.
  * the sine AMPLITUDE is computed from the measured gain to land ~0.6 Vpp at
    the output, so it cannot clip.  If it ever did, group 5 would show it.

The gain reference is the PEAK of the AC response, not its value at 0.1 Hz:
OPAM climbs about 2 dB before it rolls off, so the bottom of the sweep is the
skirt, not the passband.  The cross-check then compares the transient against
the AC gain measured at the sine's own frequency, which is the only comparison
that is true by construction.

Phase margin is taken relative to the DC phase.  OPAM inverts and so sits at
180 degrees already; subtracting that is what makes the number comparable
between the two circuits.

Measured scalars are copied into shell variables as soon as each run ends:
starting another analysis replaces the current plot and its vectors go out of
scope.

No double quotes anywhere in the block - it gets embedded verbatim inside the
quoted `value="..."` attribute of an xschem code block.
"""

BLOCK = """.control
set filetype=ascii
save all

* --- 1. operating point ----------------------------------------------------
op
echo === operating point ===
print {nodes}
print i(VDD)
show m : vgs vds id gm gds

* --- 2. Bode: magnitude and phase ------------------------------------------
ac dec 20 0.1 1e6
let mag_db = vdb(OUT)
let phase  = 180/PI * cph(v(OUT))
* The reference is the PEAK of the response, not the value at 0.1 Hz.  OPAM
* rises about 2 dB from 0.1 Hz to a peak near 2 Hz, so reading the gain at the
* bottom of the sweep understates it and puts f-3dB in the wrong place.
meas ac av_dc  FIND vdb(OUT) AT=0.1
meas ac av_max MAX vdb(OUT)
meas ac f3db   WHEN vdb(OUT)='av_max-3' FALL=1
meas ac funity WHEN vdb(OUT)=0 FALL=1
* Phase margin against the DC phase, not against zero: an inverting amplifier
* already sits at 180 degrees at DC, and subtracting it is what makes the
* number mean the same thing for both circuits.
meas ac ph_dc FIND phase AT=0.1
meas ac ph_u  FIND phase WHEN vdb(OUT)=0 FALL=1
let pm = 180 + (ph_u - ph_dc)
echo === bode: gain, corner, unity gain, phase margin ===
print av_dc av_max f3db funity ph_dc ph_u pm
{stages}* the AC vectors die with the plot, so keep what the later runs need
set avmaxs = $&av_max
set f3s    = $&f3db
plot mag_db
plot phase

* --- 3. input / output relation --------------------------------------------
dc {src} -2 2 0.01
echo === transfer: output against differential input ===
meas dc out_max MAX v(OUT)
meas dc out_min MIN v(OUT)
meas dc vo_0    FIND v(OUT) AT=0
meas dc vo_p    FIND v(OUT) AT=0.01
meas dc vo_m    FIND v(OUT) AT=-0.01
let slope    = (vo_p - vo_m) / 0.02
let slope_db = db(abs(slope))
print out_max out_min vo_0 slope slope_db
plot v(OUT)

* --- 4. sine inside the band -----------------------------------------------
* a decade below the corner, and small enough that the output cannot clip
let fsig = $f3s / 10
let amp  = 0.3 / (10^($avmaxs/20))
set fsigs = $&fsig
set amps  = $&amp
echo === sine: frequency and amplitude derived from the AC run ===
print fsig amp
* the honest reference for the cross-check is the AC gain at THIS frequency,
* not the flat-band figure - one extra single-point AC run buys that
ac lin 1 $fsigs $fsigs
let av_ref = vdb(OUT)
set avrefs = $&av_ref
alter {src} sin = [ 0 $amps $fsigs ]
* Settle for 200 cycles before measuring, and step at 50 points per cycle.
* This is not caution for its own sake: OPAM's bootstrap gate node is held
* only by the off-device leakage (r_off in opam_core.spice), so the signal
* pumps charge into it through C2 and the node drifts for tens of seconds
* before it finds equilibrium.  Measured over 12 cycles the gain reads several
* dB high and is still moving; by 150 cycles it has converged and stays put
* through 1000.  OPAM2 has no such node and settles at once, so the same
* window costs it only simulation time.
let tskip = 200 / $fsigs
let tstop = tskip + 6 / $fsigs
set ts = $&tstop
set tk = $&tskip
let tstep = 1 / (50 * $fsigs)
set tstp = $&tstep
tran $tstp $ts $tk
echo === sine: measured input and output ===
meas tran vi_pp PP {vin}   FROM=$tk TO=$ts
meas tran vo_pp PP v(OUT) FROM=$tk TO=$ts
let av_tran = db(vo_pp / vi_pp)
print vi_pp vo_pp av_tran
plot v(OUT) {vin}

* --- 5. the two gains have to agree ----------------------------------------
* A gap here is a result, not a glitch.  The AC run linearises about the DC
* operating point; the transient is the circuit actually running.  If they
* disagree by more than about 1 dB, either the sine is clipping or the
* operating point moves once the signal is applied - and for a floating
* bootstrap node, it does.
let gain_err = av_tran - $avrefs
print gain_err
echo === done ===
.endc
"""

STAGE = "meas ac {name} MAX vdb({node}) from=0.1 to=1e6\n"


def block(nodes, stages=(), plots=True, src="VD", vin="v(d)"):
    """Render the block.

    `nodes`  printed at the operating point
    `stages` (measurement name, node) pairs for per-stage gains
    `src`    the differential input source: VD in the standalone benches,
             V4 in the schematics, where it sits between INN and INP
    `vin`    how to read the differential input back
    """
    text = BLOCK.format(
        nodes=" ".join("v(%s)" % n for n in nodes),
        stages="".join(STAGE.format(name=n, node=x) for n, x in stages),
        src=src, vin=vin,
    )
    if not plots:
        text = "\n".join(l for l in text.splitlines()
                         if not l.startswith("plot ")) + "\n"
    return text


if __name__ == "__main__":
    print(block(["OUT"], [("av_stage1", "x1.net3")]))
