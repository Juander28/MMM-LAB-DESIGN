v {xschem version=3.4.4 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {CROSS COUPLED X10 - 4 de 10 canales poblados (c1,c6,c8,c10) - plan 50-200 MHz} 0 -160 0 0 0.6 0.6 {layer=8}
C {devices/code_shown.sym} 4040 0 0 0 {name=PARAMS only_toplevel=false value=".param VDD=1.5 L=30n RS=1.5 RT=25
.param Itail=180u cp=0.4p
.param C1=21.108p C2=25.1209p C3=30.396p C4=37.526p C5=47.494p C6=62.033p C7=84.434p C8=121.585p C9=189.977p C10=337.737p
.include models/nmosgen_x10.lib
.ac dec 20000 10Meg 250Meg"}
C {devices/code_shown.sym} 4040 700 0 0 {name=SIMULATION only_toplevel=false value=".control
run
let vact = v(actp)-v(actm)
wrdata x10_ac.csv vact
quit
.endc"}
C {devices/vsource.sym} 0 0 0 0 {name=VV4 value='VDD'}
C {devices/lab_pin.sym} 0 -30 1 0 {name=l1 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 0 30 3 0 {name=l2 sig_type=std_logic lab=0}
C {devices/vsource.sym} 0 220 0 0 {name=VV3 value="0 AC 1"}
C {devices/lab_pin.sym} 0 190 1 0 {name=l3 sig_type=std_logic lab=n01}
C {devices/lab_pin.sym} 0 250 3 0 {name=l4 sig_type=std_logic lab=actm}
C {devices/res.sym} 0 440 0 0 {name=RR5 value=1k}
C {devices/lab_pin.sym} 0 410 1 0 {name=l5 sig_type=std_logic lab=actp}
C {devices/lab_pin.sym} 0 470 3 0 {name=l6 sig_type=std_logic lab=n01}
C {devices/res.sym} 0 660 0 0 {name=RR6 value=1k}
C {devices/lab_pin.sym} 0 630 1 0 {name=l7 sig_type=std_logic lab=actp}
C {devices/lab_pin.sym} 0 690 3 0 {name=l8 sig_type=std_logic lab=actm}
C {devices/nmos4.sym} 0 880 0 0 {name=MM7 model=NMOSGEN w=100u l=100u}
C {devices/lab_pin.sym} 20 850 1 0 {name=l9 sig_type=std_logic lab=n02}
C {devices/lab_pin.sym} -20 880 0 0 {name=l10 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 20 910 3 0 {name=l11 sig_type=std_logic lab=n03}
C {devices/lab_pin.sym} 20 880 2 0 {name=l12 sig_type=std_logic lab=n03}
C {devices/nmos4.sym} 0 1100 0 0 {name=MM8 model=NMOSGEN w=100u l=100u}
C {devices/lab_pin.sym} 20 1070 1 0 {name=l13 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} -20 1100 0 0 {name=l14 sig_type=std_logic lab=n02}
C {devices/lab_pin.sym} 20 1130 3 0 {name=l15 sig_type=std_logic lab=n03}
C {devices/lab_pin.sym} 20 1100 2 0 {name=l16 sig_type=std_logic lab=n03}
C {devices/ind.sym} 480 0 0 0 {name=LL2 value='L/2'}
C {devices/lab_pin.sym} 480 -30 1 0 {name=l17 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 480 30 3 0 {name=l18 sig_type=std_logic lab=xl2}
C {devices/res.sym} 480 220 0 0 {name=RL2ser value='RS/2'}
C {devices/lab_pin.sym} 480 190 1 0 {name=l19 sig_type=std_logic lab=xl2}
C {devices/lab_pin.sym} 480 250 3 0 {name=l20 sig_type=std_logic lab=actm}
C {devices/ind.sym} 480 440 0 0 {name=LL4 value='L/2'}
C {devices/lab_pin.sym} 480 410 1 0 {name=l21 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 480 470 3 0 {name=l22 sig_type=std_logic lab=xl4}
C {devices/res.sym} 480 660 0 0 {name=RL4ser value='RS/2'}
C {devices/lab_pin.sym} 480 630 1 0 {name=l23 sig_type=std_logic lab=xl4}
C {devices/lab_pin.sym} 480 690 3 0 {name=l24 sig_type=std_logic lab=n02}
C {devices/capa.sym} 480 880 0 0 {name=CC1 value='c1'}
C {devices/lab_pin.sym} 480 850 1 0 {name=l25 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 480 910 3 0 {name=l26 sig_type=std_logic lab=n02}
C {devices/capa.sym} 480 1100 0 0 {name=CC6 value='cp'}
C {devices/lab_pin.sym} 480 1070 1 0 {name=l27 sig_type=std_logic lab=actp}
C {devices/lab_pin.sym} 480 1130 3 0 {name=l28 sig_type=std_logic lab=n02}
C {devices/isource.sym} 960 0 0 0 {name=IItail_src3 value='Itail'}
C {devices/lab_pin.sym} 960 -30 1 0 {name=l29 sig_type=std_logic lab=n03}
C {devices/lab_pin.sym} 960 30 3 0 {name=l30 sig_type=std_logic lab=0}
C {devices/nmos4.sym} 960 220 0 0 {name=MM17 model=NMOSGEN w=100u l=100u}
C {devices/lab_pin.sym} 980 190 1 0 {name=l31 sig_type=std_logic lab=n04}
C {devices/lab_pin.sym} 940 220 0 0 {name=l32 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 980 250 3 0 {name=l33 sig_type=std_logic lab=n05}
C {devices/lab_pin.sym} 980 220 2 0 {name=l34 sig_type=std_logic lab=n05}
C {devices/nmos4.sym} 960 440 0 0 {name=MM18 model=NMOSGEN w=100u l=100u}
C {devices/lab_pin.sym} 980 410 1 0 {name=l35 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 940 440 0 0 {name=l36 sig_type=std_logic lab=n04}
C {devices/lab_pin.sym} 980 470 3 0 {name=l37 sig_type=std_logic lab=n05}
C {devices/lab_pin.sym} 980 440 2 0 {name=l38 sig_type=std_logic lab=n05}
C {devices/ind.sym} 960 660 0 0 {name=LL16 value='L/2'}
C {devices/lab_pin.sym} 960 630 1 0 {name=l39 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 960 690 3 0 {name=l40 sig_type=std_logic lab=xl16}
C {devices/res.sym} 960 880 0 0 {name=RL16ser value='RS/2'}
C {devices/lab_pin.sym} 960 850 1 0 {name=l41 sig_type=std_logic lab=xl16}
C {devices/lab_pin.sym} 960 910 3 0 {name=l42 sig_type=std_logic lab=actm}
C {devices/ind.sym} 960 1100 0 0 {name=LL17 value='L/2'}
C {devices/lab_pin.sym} 960 1070 1 0 {name=l43 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 960 1130 3 0 {name=l44 sig_type=std_logic lab=xl17}
C {devices/res.sym} 1440 0 0 0 {name=RL17ser value='RS/2'}
C {devices/lab_pin.sym} 1440 -30 1 0 {name=l45 sig_type=std_logic lab=xl17}
C {devices/lab_pin.sym} 1440 30 3 0 {name=l46 sig_type=std_logic lab=n04}
C {devices/capa.sym} 1440 220 0 0 {name=CC16 value='c6'}
C {devices/lab_pin.sym} 1440 190 1 0 {name=l47 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 1440 250 3 0 {name=l48 sig_type=std_logic lab=n04}
C {devices/capa.sym} 1440 440 0 0 {name=CC17 value='cp'}
C {devices/lab_pin.sym} 1440 410 1 0 {name=l49 sig_type=std_logic lab=actp}
C {devices/lab_pin.sym} 1440 470 3 0 {name=l50 sig_type=std_logic lab=n04}
C {devices/isource.sym} 1440 660 0 0 {name=IItail_src8 value='Itail'}
C {devices/lab_pin.sym} 1440 630 1 0 {name=l51 sig_type=std_logic lab=n05}
C {devices/lab_pin.sym} 1440 690 3 0 {name=l52 sig_type=std_logic lab=0}
C {devices/nmos4.sym} 1440 880 0 0 {name=MM21 model=NMOSGEN w=100u l=100u}
C {devices/lab_pin.sym} 1460 850 1 0 {name=l53 sig_type=std_logic lab=n06}
C {devices/lab_pin.sym} 1420 880 0 0 {name=l54 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 1460 910 3 0 {name=l55 sig_type=std_logic lab=n07}
C {devices/lab_pin.sym} 1460 880 2 0 {name=l56 sig_type=std_logic lab=n07}
C {devices/nmos4.sym} 1440 1100 0 0 {name=MM22 model=NMOSGEN w=100u l=100u}
C {devices/lab_pin.sym} 1460 1070 1 0 {name=l57 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 1420 1100 0 0 {name=l58 sig_type=std_logic lab=n06}
C {devices/lab_pin.sym} 1460 1130 3 0 {name=l59 sig_type=std_logic lab=n07}
C {devices/lab_pin.sym} 1460 1100 2 0 {name=l60 sig_type=std_logic lab=n07}
C {devices/ind.sym} 1920 0 0 0 {name=LL20 value='L/2'}
C {devices/lab_pin.sym} 1920 -30 1 0 {name=l61 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 1920 30 3 0 {name=l62 sig_type=std_logic lab=xl20}
C {devices/res.sym} 1920 220 0 0 {name=RL20ser value='RS/2'}
C {devices/lab_pin.sym} 1920 190 1 0 {name=l63 sig_type=std_logic lab=xl20}
C {devices/lab_pin.sym} 1920 250 3 0 {name=l64 sig_type=std_logic lab=actm}
C {devices/ind.sym} 1920 440 0 0 {name=LL21 value='L/2'}
C {devices/lab_pin.sym} 1920 410 1 0 {name=l65 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 1920 470 3 0 {name=l66 sig_type=std_logic lab=xl21}
C {devices/res.sym} 1920 660 0 0 {name=RL21ser value='RS/2'}
C {devices/lab_pin.sym} 1920 630 1 0 {name=l67 sig_type=std_logic lab=xl21}
C {devices/lab_pin.sym} 1920 690 3 0 {name=l68 sig_type=std_logic lab=n06}
C {devices/capa.sym} 1920 880 0 0 {name=CC20 value='c8'}
C {devices/lab_pin.sym} 1920 850 1 0 {name=l69 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 1920 910 3 0 {name=l70 sig_type=std_logic lab=n06}
C {devices/capa.sym} 1920 1100 0 0 {name=CC21 value='cp'}
C {devices/lab_pin.sym} 1920 1070 1 0 {name=l71 sig_type=std_logic lab=actp}
C {devices/lab_pin.sym} 1920 1130 3 0 {name=l72 sig_type=std_logic lab=n06}
C {devices/isource.sym} 2400 0 0 0 {name=IItail_src10 value='Itail'}
C {devices/lab_pin.sym} 2400 -30 1 0 {name=l73 sig_type=std_logic lab=n07}
C {devices/lab_pin.sym} 2400 30 3 0 {name=l74 sig_type=std_logic lab=0}
C {devices/nmos4.sym} 2400 220 0 0 {name=MM25 model=NMOSGEN w=100u l=100u}
C {devices/lab_pin.sym} 2420 190 1 0 {name=l75 sig_type=std_logic lab=n08}
C {devices/lab_pin.sym} 2380 220 0 0 {name=l76 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 2420 250 3 0 {name=l77 sig_type=std_logic lab=n09}
C {devices/lab_pin.sym} 2420 220 2 0 {name=l78 sig_type=std_logic lab=n09}
C {devices/nmos4.sym} 2400 440 0 0 {name=MM26 model=NMOSGEN w=100u l=100u}
C {devices/lab_pin.sym} 2420 410 1 0 {name=l79 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 2380 440 0 0 {name=l80 sig_type=std_logic lab=n08}
C {devices/lab_pin.sym} 2420 470 3 0 {name=l81 sig_type=std_logic lab=n09}
C {devices/lab_pin.sym} 2420 440 2 0 {name=l82 sig_type=std_logic lab=n09}
C {devices/capa.sym} 2400 660 0 0 {name=CC24 value='c10'}
C {devices/lab_pin.sym} 2400 630 1 0 {name=l83 sig_type=std_logic lab=actm}
C {devices/lab_pin.sym} 2400 690 3 0 {name=l84 sig_type=std_logic lab=n08}
C {devices/capa.sym} 2400 880 0 0 {name=CC25 value='cp'}
C {devices/lab_pin.sym} 2400 850 1 0 {name=l85 sig_type=std_logic lab=actp}
C {devices/lab_pin.sym} 2400 910 3 0 {name=l86 sig_type=std_logic lab=n08}
C {devices/isource.sym} 2400 1100 0 0 {name=IItail_src12 value='Itail'}
C {devices/lab_pin.sym} 2400 1070 1 0 {name=l87 sig_type=std_logic lab=n09}
C {devices/lab_pin.sym} 2400 1130 3 0 {name=l88 sig_type=std_logic lab=0}
C {devices/ind.sym} 2880 0 0 0 {name=LL1 value='L/2'}
C {devices/lab_pin.sym} 2880 -30 1 0 {name=l89 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 2880 30 3 0 {name=l90 sig_type=std_logic lab=xl1}
C {devices/res.sym} 2880 220 0 0 {name=RL1ser value='RS/2'}
C {devices/lab_pin.sym} 2880 190 1 0 {name=l91 sig_type=std_logic lab=xl1}
C {devices/lab_pin.sym} 2880 250 3 0 {name=l92 sig_type=std_logic lab=actm}
C {devices/ind.sym} 2880 440 0 0 {name=LL3 value='L/2'}
C {devices/lab_pin.sym} 2880 410 1 0 {name=l93 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 2880 470 3 0 {name=l94 sig_type=std_logic lab=xl3}
C {devices/res.sym} 2880 660 0 0 {name=RL3ser value='RS/2'}
C {devices/lab_pin.sym} 2880 630 1 0 {name=l95 sig_type=std_logic lab=xl3}
C {devices/lab_pin.sym} 2880 690 3 0 {name=l96 sig_type=std_logic lab=n08}
