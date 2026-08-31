v {xschem version=3.4.8RC file_version=1.3
* IGZO TFT output characteristics - UCI/INRF process (igzo_mmm_lab)
*
* Sweeps Id against Vds at several Vgs on the device the model was validated
* against: W = 1000 um, L = 8 um.  At Vgs = 6 V, Vds = 10 V the measurement
* gives 670-701 uA and this netlist gives ~654 uA.
*
* Both limits of the model are visible here: it is DC-only, and it is valid
* for Vgs <= 6 V and Vds <= 10 V.  The sweep deliberately stops there.
}
G {}
K {}
V {}
S {}
F {}
E {}
N 410 -580 410 -560 {lab=#net1}
N 410 -560 530 -560 {lab=#net1}
N 530 -590 530 -560 {lab=#net1}
N 410 -680 410 -640 {lab=#net2}
N 410 -680 530 -680 {lab=#net2}
N 530 -680 530 -650 {lab=#net2}
N 680 -590 680 -570 {lab=#net1}
N 680 -560 800 -560 {lab=#net1}
N 800 -600 800 -570 {lab=#net1}
N 680 -690 680 -650 {lab=#net3}
N 680 -690 800 -690 {lab=#net3}
N 800 -690 800 -660 {lab=#net3}
N 570 -620 590 -620 {lab=#net3}
N 530 -670 580 -670 {lab=#net2}
N 640 -670 640 -620 {lab=#net2}
N 580 -670 640 -670 {lab=#net2}
N 590 -660 680 -660 {lab=#net3}
N 590 -660 590 -620 {lab=#net3}
N 530 -560 680 -560 {lab=#net1}
N 680 -570 680 -560 {lab=#net1}
N 800 -570 800 -560 {lab=#net1}
N 380 -800 410 -800 {lab=#net4}
N 410 -810 410 -800 {lab=#net4}
N 410 -800 410 -790 {lab=#net4}
N 450 -840 450 -730 {lab=#net5}
N 410 -730 450 -730 {lab=#net5}
N 340 -730 410 -730 {lab=#net5}
N 340 -770 340 -730 {lab=#net5}
N 340 -730 340 -720 {lab=#net5}
N 300 -760 340 -760 {lab=#net5}
N 260 -730 260 -510 {lab=#net6}
N 260 -870 260 -790 {lab=VDD}
N 260 -870 410 -870 {lab=VDD}
N 340 -870 340 -830 {lab=VDD}
N 410 -870 570 -870 {lab=VDD}
N 300 -530 300 -480 {lab=#net6}
N 260 -530 300 -530 {lab=#net6}
N 380 -530 550 -530 {lab=BIAS}
N 340 -660 340 -560 {lab=#net7}
N 380 -690 410 -690 {lab=#net2}
N 410 -690 410 -680 {lab=#net2}
N 820 -800 850 -800 {lab=#net8}
N 820 -810 820 -800 {lab=#net8}
N 820 -800 820 -790 {lab=#net8}
N 780 -840 780 -730 {lab=#net9}
N 780 -730 820 -730 {lab=#net9}
N 820 -730 890 -730 {lab=#net9}
N 890 -770 890 -730 {lab=#net9}
N 890 -730 890 -720 {lab=#net9}
N 890 -760 930 -760 {lab=#net9}
N 970 -730 970 -510 {lab=OUT}
N 970 -870 970 -790 {lab=VDD}
N 820 -870 970 -870 {lab=VDD}
N 890 -870 890 -830 {lab=VDD}
N 660 -870 820 -870 {lab=VDD}
N 930 -530 930 -480 {lab=OUT}
N 930 -530 970 -530 {lab=OUT}
N 890 -660 890 -560 {lab=#net10}
N 820 -690 850 -690 {lab=#net3}
N 800 -690 820 -690 {lab=#net3}
N 570 -870 660 -870 {lab=VDD}
N 260 -450 970 -450 {lab=VSS}
N 550 -530 850 -530 {lab=BIAS}
N 640 -870 640 -840 {lab=VDD}
N 570 -870 570 -840 {lab=VDD}
N 530 -810 530 -680 {lab=#net2}
N 680 -810 680 -690 {lab=#net3}
N 530 -800 550 -800 {lab=#net2}
N 640 -760 680 -760 {lab=#net3}
N 340 -500 340 -450 {lab=VSS}
N 590 -500 590 -450 {lab=VSS}
N 890 -500 890 -450 {lab=VSS}
C {devices/title.sym} 160 -30 0 0 {name=l5 author="UCI/INRF - MMM Lab"}
C {symbols/tft_igzo.sym} 390 -610 0 0 {name=M2
W=385u
L=10u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 550 -620 0 1 {name=M4
W=400u
L=1505u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 660 -620 0 0 {name=M3
W=400u
L=1505u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 820 -630 0 1 {name=M5
W=385u
L=10u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 550 -840 0 1 {name=M6
W=140u
L=200u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 660 -840 0 0 {name=M7
W=140u
L=200u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 570 -530 0 0 {name=M8
W=2950u
L=200u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 280 -480 0 1 {name=M9
W=10u
L=15u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 280 -760 0 1 {name=M10
W=2720u
L=530u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 360 -530 0 1 {name=M11
W=2510u
L=45u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 360 -690 0 1 {name=M12
W=200u
L=195u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 360 -800 0 1 {name=M13
W=100u
L=35u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 430 -840 0 1 {name=M14
W=5000u
L=10u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/cap_mim.sym} 410 -760 0 0 {name=C1
W=160.64u
L=160.64u
model=cap_mim
spiceprefix=X
}
C {ipin.sym} 370 -610 0 0 {name=p1 lab=INP}
C {iopin.sym} 970 -870 0 0 {name=p2 lab=VDD}
C {ipin.sym} 840 -630 2 0 {name=p3 lab=INN}
C {symbols/tft_igzo.sym} 950 -480 0 0 {name=M15
W=10u
L=15u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 950 -760 0 0 {name=M16
W=2720u
L=530u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 870 -530 0 0 {name=M17
W=2510u
L=45u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 870 -690 0 0 {name=M18
W=200u
L=195u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 870 -800 0 0 {name=M19
W=100u
L=35u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 800 -840 0 0 {name=M20
W=5000u
L=10u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/cap_mim.sym} 820 -760 0 1 {name=C2
W=160.64u
L=160.64u
model=cap_mim
spiceprefix=X
}
C {iopin.sym} 790 -450 0 0 {name=p4 lab=VSS}
C {symbols/cap_mim.sym} 550 -770 2 1 {name=C3
W=160.64u
L=160.64u
model=cap_mim
spiceprefix=X
}
C {symbols/cap_mim.sym} 640 -730 0 1 {name=C4
W=160.64u
L=160.64u
model=cap_mim
spiceprefix=X
}
C {lab_pin.sym} 550 -740 3 0 {name=p5 sig_type=std_logic lab=INN}
C {lab_pin.sym} 640 -700 0 0 {name=p6 sig_type=std_logic lab=INP}
C {iopin.sym} 730 -530 0 0 {name=p7 lab=BIAS}
C {opin.sym} 970 -640 0 0 {name=p8 lab=OUT}
C {devices/lab_pin.sym} 380 -800 0 0 {name=l_boot_l lab=BOOT_L}
C {devices/lab_pin.sym} 850 -800 0 0 {name=l_boot_r lab=BOOT_R}
C {devices/res.sym} 1100 -800 0 0 {name=Rb1 value=1T m=1}
C {devices/lab_pin.sym} 1100 -830 0 0 {name=lrb1p lab=BOOT_L}
C {devices/lab_pin.sym} 1100 -770 0 0 {name=lrb1m lab=VDD}
C {devices/res.sym} 1250 -800 0 0 {name=Rb2 value=1T m=1}
C {devices/lab_pin.sym} 1250 -830 0 0 {name=lrb2p lab=BOOT_R}
C {devices/lab_pin.sym} 1250 -770 0 0 {name=lrb2m lab=VDD}
