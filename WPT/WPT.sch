v {xschem version=3.4.8RC file_version=1.3

* WPT link - IGZO TFT voltage doubler on a planar receive coil.
*
* HAND-EDITED by Juander28 on 2026-08-31: the receive coil was swapped from
* the ind_igzo subcircuit to a plain ind.sym so that K1 can reach it, labels
* were added (tran, IN, rec, med, OUT), and the K1 line was uncommented.
* That is the right move and it is why this file simulates at all.
*
* Do NOT regenerate over it: sim/make_wpt_schematic.py now refuses unless
* given --force.  The generated drawing lives in WPT_sim.sch instead.
}
G {}
K {}
V {}
S {}
E {}
N -180 160 -180 180 {lab=0}
N -180 180 -30 180 {lab=0}
N -30 180 120 180 {lab=0}
N 60 70 120 70 {lab=OUT}
N 120 70 120 110 {lab=OUT}
N -60 70 0 70 {lab=med}
N -30 70 -30 120 {lab=med}
N -10 110 30 110 {lab=med}
N -30 110 -10 110 {lab=med}
N -180 70 -120 70 {lab=rec}
N -180 70 -180 100 {lab=rec}
N 120 170 120 180 {lab=0}
N 120 70 210 70 {lab=OUT}
N 210 70 210 110 {lab=OUT}
N 210 170 210 180 {lab=0}
N 120 180 210 180 {lab=0}
N -370 80 -340 80 {lab=#net1}
N -370 80 -370 110 {lab=#net1}
N -370 160 -370 190 {lab=0}
N -370 190 -250 190 {lab=0}
N -250 160 -250 190 {lab=0}
N -280 80 -250 80 {lab=IN}
N -250 80 -250 100 {lab=IN}
N -70 110 -70 150 {lab=med}
N -70 110 -30 110 {lab=med}
C {capa.sym} -90 70 1 0 {name=C1
m=1
value=10u
footprint=1206
device="ceramic capacitor"
}
C {symbols/tft_igzo.sym} -50 150 0 0 {name=M1
W=6000u
L=5u
ov=2u
nf=1
m=1
B=0
b_scale=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 30 90 3 0 {name=M2
W=6000u
L=5u
ov=2u
nf=1
m=1
B=0
b_scale=1
model=igzo_tft
spiceprefix=X
}
C {capa.sym} 120 140 2 0 {name=C3
m=1
value=10u
footprint=1206
device="ceramic capacitor"
}
C {res.sym} 210 140 0 0 {name=RL
value=10k
footprint=1206
device=resistor
m=1
}
C {vsource.sym} -370 130 0 0 {name=V1 value="DC 0 AC 1 SIN(0 152.145 500k)" savecurrent=true
}
C {res.sym} -310 80 1 0 {name=R1
value=1
footprint=1206
device=resistor
m=1
}
C {ind.sym} -250 130 0 0 {name=L2
m=1
value=171.482u
footprint=1206
device=inductor
}
C {devices/gnd.sym} -70 180 0 0 {name=g1 lab=0}
C {devices/gnd.sym} -370 190 0 0 {name=g2 lab=0}
C {devices/code_shown.sym} -370 270 0 0 {name=MODELS only_toplevel=true
format="tcleval( @value )"
value="
.include $::IGZO_MODELS/design.ngspice
.lib $::IGZO_MODELS/igzo_mmm_lab.ngspice tt
"}
C {devices/code_shown.sym} 240 0 0 0 {name=NGSPICE only_toplevel=true
value="
* The transmit loop MUST be series-tuned: L2 is 171.482uH and its reactance at
* 500 kHz is 539 ohms against 10.57 ohms of resistance.  Untuned, the drive
* current - and with it everything downstream - falls by a factor of about 51.
CTX  n_txa n_tx1 590.855p
*
* THE COUPLING BELONGS HERE AND CANNOT GO HERE.  ngspice will not couple an
* inductor inside a subcircuit, and L1 above is the ind_igzo subcircuit:
*     Fatal error: k1: coupling to non-existent inductor xl1.l1
* The coupled netlist is sim/wpt_core.spice, generated from the same numbers.
 K1 L1 L2 0.00358402
*
.control
set filetype=ascii
ac dec 40 1e3 1e7
plot v(out)
tran 1e-08 0.00012
plot v(out)
.endc
"}
C {devices/title.sym} -220 390 0 0 {name=l5 author="UCI/INRF - MMM Lab"}
C {lab_pin.sym} 210 70 1 0 {name=p1 sig_type=std_logic lab=OUT}
C {lab_pin.sym} -250 80 1 0 {name=p2 sig_type=std_logic lab=IN}
C {ind.sym} -180 130 0 0 {name=L1
m=1
value=171.482u
footprint=1206
device=inductor
}
C {lab_pin.sym} -180 70 1 0 {name=p3 sig_type=std_logic lab=rec}
C {lab_pin.sym} -30 70 1 0 {name=p4 sig_type=std_logic lab=med}
C {lab_pin.sym} -370 80 1 0 {name=p5 sig_type=std_logic lab=tran}
