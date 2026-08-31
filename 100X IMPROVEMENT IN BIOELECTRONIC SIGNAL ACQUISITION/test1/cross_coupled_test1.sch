v {xschem version=3.4.4 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {CROSS COUPLED TEST1 - designed point (A: 55.89 MHz, B: 100.00 MHz)} 0 -160 0 0 0.6 0.6 {layer=8}
C {devices/code_shown.sym} 5000 0 0 0 {name=PARAMS only_toplevel=false value=".param VDD=1.5 L=100n RS=1
.param Itail=130u c=101p cp=0.4p
.param cpA=280f cpB=155f
.param ItailA=4.07509m ItailB=0.65260m
.param C7val=40.362p
.include models/nmosgen_test1.lib
.ac lin 50000 35Meg 210Meg
* zooms (uncomment ONE to measure BW/Q accurately):
* .ac lin 50000 55.4Meg 56.4Meg
* .ac lin 50000 99.6Meg 100.4Meg"}
C {devices/code_shown.sym} 5000 700 0 0 {name=SIMULATION only_toplevel=false value=".control
run
let vact  = v(actp)-v(actm)
let vmag  = mag(vact)
meas ac vbaseA FIND vmag AT=55.45e6
meas ac vminA  MIN  vmag from=55.7e6  to=56.1e6
meas ac vbaseB FIND vmag AT=99.65e6
meas ac vminB  MIN  vmag from=99.85e6 to=100.15e6
echo depthA_dB (full span underestimates; use zoom .ac for real depth/BW):
print 20*log10(vbaseA/vminA)
echo depthB_dB:
print 20*log10(vbaseB/vminB)
wrdata test1_ac.csv vact v(pasp)
echo Ahora corre:  python3 analyze_notch.py test1_ac.csv
quit
.endc"}
C {devices/vsource.sym} 0 0 0 0 {name=VV4 value='VDD'}
C {devices/lab_pin.sym} 0 -30 1 0 {name=l1 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 0 30 3 0 {name=l2 sig_type=std_logic lab=0}
C {devices/nmos4.sym} 0 220 0 0 {name=MM1 model=NMOSGEN w=100u l=100u}
C {devices/lab_pin.sym} 20 190 1 0 {name=l3 sig_type=std_logic lab=D1}
C {devices/lab_pin.sym} -20 220 0 0 {name=l4 sig_type=std_logic lab=D2}
C {devices/lab_pin.sym} 20 250 3 0 {name=l5 sig_type=std_logic lab=ST}
C {devices/lab_pin.sym} 20 220 2 0 {name=l6 sig_type=std_logic lab=ST}
C {devices/nmos4.sym} 0 440 0 0 {name=MM2 model=NMOSGEN w=100u l=100u}
C {devices/lab_pin.sym} 20 410 1 0 {name=l7 sig_type=std_logic lab=D2}
C {devices/lab_pin.sym} -20 440 0 0 {name=l8 sig_type=std_logic lab=D1}
C {devices/lab_pin.sym} 20 470 3 0 {name=l9 sig_type=std_logic lab=ST}
C {devices/lab_pin.sym} 20 440 2 0 {name=l10 sig_type=std_logic lab=ST}
C {devices/ind.sym} 0 660 0 0 {name=LL1 value='L/2'}
C {devices/lab_pin.sym} 0 630 1 0 {name=l11 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 0 690 3 0 {name=l12 sig_type=std_logic lab=xl1}
C {devices/res.sym} 0 880 0 0 {name=RL1ser value='RS/2'}
C {devices/lab_pin.sym} 0 850 1 0 {name=l13 sig_type=std_logic lab=xl1}
C {devices/lab_pin.sym} 0 910 3 0 {name=l14 sig_type=std_logic lab=D1}
C {devices/ind.sym} 0 1100 0 0 {name=LL3 value='L/2'}
C {devices/lab_pin.sym} 0 1070 1 0 {name=l15 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 0 1130 3 0 {name=l16 sig_type=std_logic lab=xl3}
C {devices/res.sym} 480 0 0 0 {name=RL3ser value='RS/2'}
C {devices/lab_pin.sym} 480 -30 1 0 {name=l17 sig_type=std_logic lab=xl3}
C {devices/lab_pin.sym} 480 30 3 0 {name=l18 sig_type=std_logic lab=D2}
C {devices/capa.sym} 480 220 0 0 {name=CC3 value='c'}
C {devices/lab_pin.sym} 480 190 1 0 {name=l19 sig_type=std_logic lab=D2}
C {devices/lab_pin.sym} 480 250 3 0 {name=l20 sig_type=std_logic lab=D1}
C {devices/isource.sym} 480 440 0 0 {name=IItail_src value='Itail'}
C {devices/lab_pin.sym} 480 410 1 0 {name=l21 sig_type=std_logic lab=ST}
C {devices/lab_pin.sym} 480 470 3 0 {name=l22 sig_type=std_logic lab=0}
C {devices/vsource.sym} 480 660 0 0 {name=VV1 value="0 AC 1"}
C {devices/lab_pin.sym} 480 630 1 0 {name=l23 sig_type=std_logic lab=n01}
C {devices/lab_pin.sym} 480 690 3 0 {name=l24 sig_type=std_logic lab=0}
C {devices/res.sym} 480 880 0 0 {name=RR1 value=1k}
C {devices/lab_pin.sym} 480 850 1 0 {name=l25 sig_type=std_logic lab=pasp}
C {devices/lab_pin.sym} 480 910 3 0 {name=l26 sig_type=std_logic lab=n01}
C {devices/capa.sym} 480 1100 0 0 {name=CC2 value='cp'}
C {devices/lab_pin.sym} 480 1070 1 0 {name=l27 sig_type=std_logic lab=pasp}
C {devices/lab_pin.sym} 480 1130 3 0 {name=l28 sig_type=std_logic lab=n02}
C {devices/capa.sym} 960 0 0 0 {name=CC4 value='c'}
C {devices/lab_pin.sym} 960 -30 1 0 {name=l29 sig_type=std_logic lab=n02}
C {devices/lab_pin.sym} 960 30 3 0 {name=l30 sig_type=std_logic lab=0}
C {devices/ind.sym} 960 220 0 0 {name=LL5 value='L'}
C {devices/lab_pin.sym} 960 190 1 0 {name=l31 sig_type=std_logic lab=n02}
C {devices/lab_pin.sym} 960 250 3 0 {name=l32 sig_type=std_logic lab=xl5}
C {devices/res.sym} 960 440 0 0 {name=RL5ser value=1}
C {devices/lab_pin.sym} 960 410 1 0 {name=l33 sig_type=std_logic lab=xl5}
C {devices/lab_pin.sym} 960 470 3 0 {name=l34 sig_type=std_logic lab=0}
C {devices/capa.sym} 960 660 0 0 {name=CC1 value=70p}
C {devices/lab_pin.sym} 960 630 1 0 {name=l35 sig_type=std_logic lab=pasp}
C {devices/lab_pin.sym} 960 690 3 0 {name=l36 sig_type=std_logic lab=n06}
C {devices/capa.sym} 960 880 0 0 {name=CC6 value='c'}
C {devices/lab_pin.sym} 960 850 1 0 {name=l37 sig_type=std_logic lab=n06}
C {devices/lab_pin.sym} 960 910 3 0 {name=l38 sig_type=std_logic lab=0}
C {devices/ind.sym} 960 1100 0 0 {name=LL2 value='L'}
C {devices/lab_pin.sym} 960 1070 1 0 {name=l39 sig_type=std_logic lab=n06}
C {devices/lab_pin.sym} 960 1130 3 0 {name=l40 sig_type=std_logic lab=xl2}
C {devices/res.sym} 1440 0 0 0 {name=RL2ser value=1}
C {devices/lab_pin.sym} 1440 -30 1 0 {name=l41 sig_type=std_logic lab=xl2}
C {devices/lab_pin.sym} 1440 30 3 0 {name=l42 sig_type=std_logic lab=0}
C {devices/vsource.sym} 1440 220 0 0 {name=VV3 value="0 AC 1"}
C {devices/lab_pin.sym} 1440 190 1 0 {name=l43 sig_type=std_logic lab=n05}
C {devices/lab_pin.sym} 1440 250 3 0 {name=l44 sig_type=std_logic lab=actm}
C {devices/res.sym} 1440 440 0 0 {name=RR5 value=1k}
C {devices/lab_pin.sym} 1440 410 1 0 {name=l45 sig_type=std_logic lab=actp}
C {devices/lab_pin.sym} 1440 470 3 0 {name=l46 sig_type=std_logic lab=n05}
C {devices/capa.sym} 1440 660 0 0 {name=CC9 value='cpA'}
C {devices/lab_pin.sym} 1440 630 1 0 {name=l47 sig_type=std_logic lab=actp}
C {devices/lab_pin.sym} 1440 690 3 0 {name=l48 sig_type=std_logic lab=n03}
C {devices/nmos4.sym} 1440 880 0 0 {name=MM5 model=NMOSGEN w=100u l=100u}
C {devices/lab_pin.sym} 1460 850 1 0 {name=l49 sig_type=std_logic lab=n03}
C {devices/lab_pin.sym} 1420 880 0 0 {name=l50 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 1460 910 3 0 {name=l51 sig_type=std_logic lab=n04}
C {devices/lab_pin.sym} 1460 880 2 0 {name=l52 sig_type=std_logic lab=n04}
C {devices/nmos4.sym} 1440 1100 0 0 {name=MM6 model=NMOSGEN w=100u l=100u}
C {devices/lab_pin.sym} 1460 1070 1 0 {name=l53 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 1420 1100 0 0 {name=l54 sig_type=std_logic lab=n03}
C {devices/lab_pin.sym} 1460 1130 3 0 {name=l55 sig_type=std_logic lab=n04}
C {devices/lab_pin.sym} 1460 1100 2 0 {name=l56 sig_type=std_logic lab=n04}
C {devices/ind.sym} 1920 0 0 0 {name=LL7 value='L/2'}
C {devices/lab_pin.sym} 1920 -30 1 0 {name=l57 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 1920 30 3 0 {name=l58 sig_type=std_logic lab=xl7}
C {devices/res.sym} 1920 220 0 0 {name=RL7ser value='RS/2'}
C {devices/lab_pin.sym} 1920 190 1 0 {name=l59 sig_type=std_logic lab=xl7}
C {devices/lab_pin.sym} 1920 250 3 0 {name=l60 sig_type=std_logic lab=n03}
C {devices/ind.sym} 1920 440 0 0 {name=LL6 value='L/2'}
C {devices/lab_pin.sym} 1920 410 1 0 {name=l61 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 1920 470 3 0 {name=l62 sig_type=std_logic lab=xl6}
C {devices/res.sym} 1920 660 0 0 {name=RL6ser value='RS/2'}
C {devices/lab_pin.sym} 1920 630 1 0 {name=l63 sig_type=std_logic lab=xl6}
C {devices/lab_pin.sym} 1920 690 3 0 {name=l64 sig_type=std_logic lab=actm}
C {devices/capa.sym} 1920 880 0 0 {name=CC5 value='c'}
C {devices/lab_pin.sym} 1920 850 1 0 {name=l65 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 1920 910 3 0 {name=l66 sig_type=std_logic lab=n03}
C {devices/isource.sym} 1920 1100 0 0 {name=IItail_src2 value='ItailA'}
C {devices/lab_pin.sym} 1920 1070 1 0 {name=l67 sig_type=std_logic lab=n04}
C {devices/lab_pin.sym} 1920 1130 3 0 {name=l68 sig_type=std_logic lab=0}
C {devices/capa.sym} 2400 0 0 0 {name=CC8 value='cpB'}
C {devices/lab_pin.sym} 2400 -30 1 0 {name=l69 sig_type=std_logic lab=actp}
C {devices/lab_pin.sym} 2400 30 3 0 {name=l70 sig_type=std_logic lab=n07}
C {devices/nmos4.sym} 2400 220 0 0 {name=MM3 model=NMOSGEN w=100u l=100u}
C {devices/lab_pin.sym} 2420 190 1 0 {name=l71 sig_type=std_logic lab=n07}
C {devices/lab_pin.sym} 2380 220 0 0 {name=l72 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 2420 250 3 0 {name=l73 sig_type=std_logic lab=n08}
C {devices/lab_pin.sym} 2420 220 2 0 {name=l74 sig_type=std_logic lab=n08}
C {devices/nmos4.sym} 2400 440 0 0 {name=MM4 model=NMOSGEN w=100u l=100u}
C {devices/lab_pin.sym} 2420 410 1 0 {name=l75 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 2380 440 0 0 {name=l76 sig_type=std_logic lab=n07}
C {devices/lab_pin.sym} 2420 470 3 0 {name=l77 sig_type=std_logic lab=n08}
C {devices/lab_pin.sym} 2420 440 2 0 {name=l78 sig_type=std_logic lab=n08}
C {devices/ind.sym} 2400 660 0 0 {name=LL8 value='L/2'}
C {devices/lab_pin.sym} 2400 630 1 0 {name=l79 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 2400 690 3 0 {name=l80 sig_type=std_logic lab=xl8}
C {devices/res.sym} 2400 880 0 0 {name=RL8ser value='RS/2'}
C {devices/lab_pin.sym} 2400 850 1 0 {name=l81 sig_type=std_logic lab=xl8}
C {devices/lab_pin.sym} 2400 910 3 0 {name=l82 sig_type=std_logic lab=n07}
C {devices/ind.sym} 2400 1100 0 0 {name=LL4 value='L/2'}
C {devices/lab_pin.sym} 2400 1070 1 0 {name=l83 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 2400 1130 3 0 {name=l84 sig_type=std_logic lab=xl4}
C {devices/res.sym} 2880 0 0 0 {name=RL4ser value='RS/2'}
C {devices/lab_pin.sym} 2880 -30 1 0 {name=l85 sig_type=std_logic lab=xl4}
C {devices/lab_pin.sym} 2880 30 3 0 {name=l86 sig_type=std_logic lab=actm}
C {devices/capa.sym} 2880 220 0 0 {name=CC7 value='C7val'}
C {devices/lab_pin.sym} 2880 190 1 0 {name=l87 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 2880 250 3 0 {name=l88 sig_type=std_logic lab=n07}
C {devices/isource.sym} 2880 440 0 0 {name=IItail_src1 value='ItailB'}
C {devices/lab_pin.sym} 2880 410 1 0 {name=l89 sig_type=std_logic lab=n08}
C {devices/lab_pin.sym} 2880 470 3 0 {name=l90 sig_type=std_logic lab=0}
C {devices/vsource.sym} 2880 660 0 0 {name=VV2 value="0 AC 1"}
C {devices/lab_pin.sym} 2880 630 1 0 {name=l91 sig_type=std_logic lab=n11}
C {devices/lab_pin.sym} 2880 690 3 0 {name=l92 sig_type=std_logic lab=act1m}
C {devices/res.sym} 2880 880 0 0 {name=RR2 value=1k}
C {devices/lab_pin.sym} 2880 850 1 0 {name=l93 sig_type=std_logic lab=act1p}
C {devices/lab_pin.sym} 2880 910 3 0 {name=l94 sig_type=std_logic lab=n11}
C {devices/capa.sym} 2880 1100 0 0 {name=CC11 value='cp'}
C {devices/lab_pin.sym} 2880 1070 1 0 {name=l95 sig_type=std_logic lab=act1p}
C {devices/lab_pin.sym} 2880 1130 3 0 {name=l96 sig_type=std_logic lab=n09}
C {devices/nmos4.sym} 3360 0 0 0 {name=MM7 model=NMOSGEN w=100u l=100u}
C {devices/lab_pin.sym} 3380 -30 1 0 {name=l97 sig_type=std_logic lab=n09}
C {devices/lab_pin.sym} 3340 0 0 0 {name=l98 sig_type=std_logic lab=act1m}
C {devices/lab_pin.sym} 3380 30 3 0 {name=l99 sig_type=std_logic lab=n10}
C {devices/lab_pin.sym} 3380 0 2 0 {name=l100 sig_type=std_logic lab=n10}
C {devices/nmos4.sym} 3360 220 0 0 {name=MM8 model=NMOSGEN w=100u l=100u}
C {devices/lab_pin.sym} 3380 190 1 0 {name=l101 sig_type=std_logic lab=act1m}
C {devices/lab_pin.sym} 3340 220 0 0 {name=l102 sig_type=std_logic lab=n09}
C {devices/lab_pin.sym} 3380 250 3 0 {name=l103 sig_type=std_logic lab=n10}
C {devices/lab_pin.sym} 3380 220 2 0 {name=l104 sig_type=std_logic lab=n10}
C {devices/ind.sym} 3360 440 0 0 {name=LL10 value='L/2'}
C {devices/lab_pin.sym} 3360 410 1 0 {name=l105 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 3360 470 3 0 {name=l106 sig_type=std_logic lab=xl10}
C {devices/res.sym} 3360 660 0 0 {name=RL10ser value='RS/2'}
C {devices/lab_pin.sym} 3360 630 1 0 {name=l107 sig_type=std_logic lab=xl10}
C {devices/lab_pin.sym} 3360 690 3 0 {name=l108 sig_type=std_logic lab=n09}
C {devices/ind.sym} 3360 880 0 0 {name=LL9 value='L/2'}
C {devices/lab_pin.sym} 3360 850 1 0 {name=l109 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 3360 910 3 0 {name=l110 sig_type=std_logic lab=xl9}
C {devices/res.sym} 3360 1100 0 0 {name=RL9ser value='RS/2'}
C {devices/lab_pin.sym} 3360 1070 1 0 {name=l111 sig_type=std_logic lab=xl9}
C {devices/lab_pin.sym} 3360 1130 3 0 {name=l112 sig_type=std_logic lab=act1m}
C {devices/capa.sym} 3840 0 0 0 {name=CC10 value='c'}
C {devices/lab_pin.sym} 3840 -30 1 0 {name=l113 sig_type=std_logic lab=act1m}
C {devices/lab_pin.sym} 3840 30 3 0 {name=l114 sig_type=std_logic lab=n09}
C {devices/isource.sym} 3840 220 0 0 {name=IItail_src3 value='Itail'}
C {devices/lab_pin.sym} 3840 190 1 0 {name=l115 sig_type=std_logic lab=n10}
C {devices/lab_pin.sym} 3840 250 3 0 {name=l116 sig_type=std_logic lab=0}
