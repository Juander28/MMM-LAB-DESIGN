v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
N -0 100 -0 120 {lab=#net1}
N -0 120 290 120 {lab=#net1}
N 290 100 290 120 {lab=#net1}
N 290 0 290 40 {lab=INN}
N 170 0 290 0 {lab=INN}
N 0 0 110 0 {lab=#net2}
N -50 -0 -0 0 {lab=#net2}
N -0 0 -0 40 {lab=#net2}
N 150 200 150 220 {lab=xxx}
N 150 120 150 140 {lab=#net1}
N -0 -80 -0 -60 {lab=VDD}
N -0 -80 290 -80 {lab=VDD}
N 290 -80 290 -60 {lab=VDD}
N 290 0 350 -0 {lab=INN}
N 110 70 250 70 {lab=#net2}
N 110 40 110 70 {lab=#net2}
N 70 40 110 40 {lab=#net2}
N 70 0 70 40 {lab=#net2}
N 40 70 90 70 {lab=INN}
N 90 30 90 70 {lab=INN}
N 90 30 290 30 {lab=INN}
N 70 170 110 170 {lab=BIAS}
N -160 0 -110 0 {lab=INP}
C {symbols/cap_mim.sym} 140 0 3 0 {name=C1
W=160.64u
L=160.64u
model=cap_mim
spiceprefix=X
}
C {symbols/ind_igzo.sym} 290 -30 2 0 {name=L1
ls=16.38n
rs=375.8
model=ind_igzo
spiceprefix=X
}
C {symbols/tft_igzo.sym} 270 70 0 0 {name=M1
W=100u
L=10u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/tft_igzo.sym} 20 70 0 1 {name=M2
W=100u
L=10u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {symbols/ind_igzo.sym} 0 -30 0 0 {name=L2
ls=16.38n
rs=375.8
model=ind_igzo
spiceprefix=X
}
C {symbols/cap_mim.sym} -80 0 3 0 {name=C2
W=160.64u
L=160.64u
model=cap_mim
spiceprefix=X
}
C {symbols/tft_igzo.sym} 130 170 0 0 {name=M3
W=100u
L=10u
ov=5u
nf=1
m=1
model=igzo_tft
spiceprefix=X
}
C {iopin.sym} 50 -80 3 0 {name=p1 lab=VDD}
C {iopin.sym} 150 220 1 0 {name=p2 lab=xxx}
C {iopin.sym} -160 0 3 0 {name=p3 lab=INP}
C {iopin.sym} 350 0 3 0 {name=p4 lab=INN}
C {iopin.sym} 70 170 2 0 {name=p5 lab=BIAS}
