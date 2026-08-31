#!/usr/bin/env python3
"""The prose of the report, in both languages.

Code and figure labels are in English throughout; only this file is
translated, because only this file is read by a person choosing a language.
"""

EN = {
    "kicker": "UCI/INRF - MMM Lab - IGZO TFT amplifiers",
    "footer": "TFT-MMM-LAB-PDK - igzo_mmm_lab - every number computed from the models",
    "t1": "Two IGZO TFT amplifiers,\nsized against the measured process",
    "intro_h": "What this is",
    "intro": """Two operational amplifiers drawn in the UCI/INRF IGZO TFT process, each
reproducing a published circuit, and sized here for the largest open-loop gain the
process will actually hold across its corners.

  OPAM2   after Zysset et al., IEEE EDL 34(11), 2013 - an all-enhancement opamp,
          16 TFTs, published at 18.7 dB and 900 uW on flexible polyimide.
  OPAM    after Zhao et al., IEEE TBCAS 18(6), 2024 - a cross-coupled pair with a
          capacitor bootstrap load, published at 43.5 dB.

A third variant, OPAM with the bias generated on chip, removes the external bias
pin entirely.  That matters more than it sounds: the threshold moves 0.62 V from
the best corner to the worst, so a fixed external bias has to be re-trimmed for
every corner, and a chain of diode-connected devices does that tracking by itself.""",
    "proc_h": "What the process gives you, and what it does not",
    "proc": """Everything below follows from four facts about the models, and it is worth
reading them before any number in this report.

  1. The models are DC-only, SPICE level 1, validated for VGS <= 6 V and
     VDS <= 10 V.  Every sweep here stays inside that box.
  2. gm/gds = 2/(lambda*Vov) does not depend on L.  Long channels do not buy
     gain in this process; a small overdrive and a high load impedance do.
  3. Contact resistance is Rd = Rs = 3.3/W ohms with W in metres - 3.3 kohm on a
     1000 um device.  It degenerates the source, so wide input devices are gain.
  4. Vto moves from +0.09 V (best) through -0.26 V (tt) to -0.53 V (all).  That
     0.62 V spread is the single hardest constraint in the whole design.""",
    "size_h": "Sizing",
    "size": """Widths and lengths are drawn dimensions in micrometres, grouped by function;
devices that must match share a size.  Multiplier m is 1 everywhere: two devices of
width W in parallel are exactly one device of width 2W in this wrapper, since the
contact resistance goes as 1/W and the overlap capacitance as W.""",
    "gain_h": "How to estimate the gain before simulating",
    "gain": """Three expressions cover every stage in both circuits.  They are worth
evaluating by hand, because they say which term is setting the gain - which a
simulator result does not.

  transconductance      gm  = Kp * (W/L) * Vov
  output conductance    gds = lambda * Id
  intrinsic gain        gm/gds = 2 / (lambda * Vov)

  diode-loaded stage    Av = gm_drv / (gm_load + gds)
                           = sqrt( (W/L)_drv / (W/L)_load )  = Vov_load / Vov_drv
  cross-coupled pair    Av = gm_in / (gm_load - gm_cc + gds)
  contact degeneration  gm_eff = gm / (1 + gm*Rs),  Rs = 3.3/W

The cross-coupled expression is the one to respect.  It buys gain by subtracting
from the load conductance, and as gm_cc approaches gm_load the gain runs away -
and then latches.  A design that lives close to that cancellation is a design that
depends on matching, so it has to be checked at every corner and against mismatch,
not just at the nominal point.""",
    "bw_h": "How to estimate the bandwidth, and why it is the weakest number here",
    "bw": """The dominant pole is 1/(2*pi*R*C) at whichever internal node has the largest
product.  R is one over the shunt conductance at that node; C is the sum of the gate
overlap capacitances of every terminal on it, Cov = Cox * ov * W per side, plus any
MIM plate.  Picking the node by eye does not work: for OPAM2 the output sits on a
diode load and its pole is a kilohertz away, while the real corner is set at the
first stage's drain.  Sweeping every node finds it.

This is the least trustworthy figure in the report, and for a stated reason.  Cox
is measured - 1.564 fF/um2, from the 400 x 400 um plate.  The 5 um gate overlap it
multiplies was read off one GDS cell, and nothing in this PDK has ever been checked
against a measured C-V or an S-parameter.  Treat the bandwidth as an order of
magnitude, not a specification.""",
    "res_h": "Results",
    "res": """Open-loop differential gain, measured with a 1 V differential AC source and
read at the peak of the response.  Every corner satisfies the same constraints:
every device in saturation, every VGS and VDS inside the validated box, the output
within 20-80 % of the supply, and the power under the 900 uW the Zysset paper
reports.""",
    "exp_h": "Are the results what was expected?",
    "exp": """The hand estimates and the simulator agree where the topology is simple and
part company where it leans on a cancellation - which is exactly where one should
expect them to.

Against the papers: OPAM2 reaches 32 dB at its worst corner where the paper reports
18.7 dB, at 67 uW against 900 uW.  That is not a better circuit, it is a bigger one -
the devices here are hundreds of micrometres wide because the process is slow.  OPAM
reaches 63 dB at the best corner against a published 43.5 dB, but the honest figure
is the one measured with a real waveform, and that is 52.5 dB.  Two effects account
for the difference, and both are worth stating plainly.""",
    "gap_h": "Two things the AC analysis does not see",
    "gap": """First, the bootstrap gate node is pumped above the supply.  In the DC operating
point it sits at exactly VDD; in a settled transient it sits 175 mV higher, because
the signal injects charge through C2 and the only way out is the off-device leakage.
The stage's own output moves 167 mV with it, and that costs 11 dB.  An AC analysis
linearises about the DC point and never sees any of it.  This is not a simulation
artefact: a floating bootstrap node in silicon is pumped the same way, and where it
settles depends on a leakage current this model gives as exactly zero.

Second, the phase margin is negative.  As an open-loop gain block - which is what
both papers characterise - that is fine.  Closed at unity gain it would oscillate.
The Zhao paper puts a phase compensation loop in its title; the sizing here has no
such loop, and the search never had phase margin as a constraint, because optimising
against an AC number this PDK cannot validate would be optimising against a guess.""",
    "bias_h": "Generating the bias on chip",
    "bias": """The external bias pin needed a different voltage at every corner - 1.25 V,
0.90 V, 0.63 V - because what the tail device needs is a fixed overdrive, and the
threshold moves underneath it.  Three diode-connected devices from VDD to VSS fix
that without a pin: the tap sits one gate-source drop above VSS, and a gate-source
drop is Vth + Vov, so it follows the threshold on its own.  The top of the chain is
split in two so that no device sits at more than about half the supply across its
gate; one device there would be at VGS = 6.7 V, outside the validated box.

It tracks 39 % of the threshold shift, not 100 %: a two-branch divider cannot do
better, because the overdrive it produces is a fixed fraction of (VDD - 2*Vth), and
that grows as Vth falls.  Perfect tracking would need a reference current
proportional to Kp.  What matters is that the amplifier meets its constraints at all
three corners with nothing adjusted between them, and it does - the sizing absorbs
the residual.  The chain costs 0.81 uA, under 5 % of the total.""",
    "field_h": "Magnetic field",
    "field": """The wrapper divides the intrinsic width by 1 + (mu*b_scale*B)^2.  Because
level 1 only ever uses the product Kp*W/L, that is the same as dividing Kp, which is
the same as dividing the mobility - so this models classical magnetoresistance, and
Kn and channel resistance are one fact, not two.  Contact resistance and overlap
capacitance use the outer W and do not move with the field, which is where the
physics leaves them.

What is NOT modelled: the Hall effect - a transverse voltage, and the effect an
actual magnetometer is built from - and any shift of the threshold with field.  If
what the laboratory measures under field is one of those, fitting b_scale would be
forcing the wrong mechanism.

At b_scale = 1 the effect is (mu*B)^2 = 2.1e-7 per tesla at the best corner: two
parts in ten million, below the resolution of any measurement in this report.  It
also goes as mu squared, so the sensitivity changes by 31x between the best and the
short corners.  Classical magnetoresistance in this material is not a sensor.""",
    "sense_h": "The gain is blind to the field; the bandwidth is not",
    "sense": """A uniform mobility change barely moves the gain.  That is not luck, it is
the topology: the gain is set by ratios of identical devices, and a change that
scales all of them together leaves the ratios alone.  Reduce the effective width by
95 % and the gain falls 0.6 dB - while the supply current falls 95 % and the
bandwidth falls 82 %.

That points at the measurement to make.  Park a probe tone where the response is
steep, and a bandwidth shift becomes an amplitude change.  On the corner it is worth
about 2.5x the flat band; a decade past the corner, where the full roll-off is, OPAM
gives 10.3 dB of output per unit of relative mobility change against 0.94 dB in the
flat band - eleven times better.

Turned around, that is the number to hand the laboratory: for a tenth of a decibel
of output change at one tesla, the measured effect would have to sit about 216 times
above the classical one.  If it does not, this amplifier is not the sensor - and the
place to look is a topology where only one branch sees the field, so the ratios stop
cancelling.""",
    "lim_h": "What to trust, and what not to",
    "lim": """  Gain, DC operating point, swing, power     trustworthy.  The models reproduce
      measured output curves with a median simulated/measured of 1.01 over 18
      devices, and every number here sits inside the validated box.
  Bandwidth, phase margin, anything AC       an order of magnitude.  Cox is
      measured; the overlap that sets every capacitance was read off one GDS cell
      and never checked against a C-V.
  The transient gain of OPAM                 more trustworthy than its AC gain,
      because the bootstrap node's DC level is set by a leakage the model puts at
      zero.
  Magnetic field                             the classical term is right and
      negligible.  Anything larger is a measurement this PDK has not made.
  Level 1 runs about 20 % pessimistic on gm, because the measured saturation
      exponent is 2.31 rather than the square law's 2.""",
    "col_corner": "corner", "col_gain": "gain", "col_stage1": "stage 1",
    "col_stage2": "stage 2", "col_f3db": "f-3dB", "col_pm": "swing",
    "col_pow": "power", "col_vout": "output", "col_bias": "BIAS",
    "col_fn": "function", "col_dev": "devices", "col_w": "W (um)",
    "col_l": "L (um)", "col_wl": "W/L",
    "col_est": "estimated", "col_sim": "simulated", "col_err": "difference",
    "col_stage": "stage", "col_tone": "probe tone", "col_freq": "f (Hz)",
    "col_sens": "dB per unit dmu/mu",
    "gvf_h": "Gain against field, one curve per probe tone",
    "gvf": """Each curve is a tone held at a fixed frequency while the field moves the
circuit underneath it.  The lowest curve sits a decade below the corner, in the flat
band, and barely moves - a mobility change scales every device together and the ratios
that set the gain do not notice.  The higher the tone sits on the roll-off, the more of
the same change it reads: over the full sweep the flat-band tone loses
{gvf_flat:.1f} dB and the one at thirty times the corner loses {gvf_edge:.1f} dB.

That is the measurement to build a sensor on, if the effect is ever large enough to
measure: not the gain, which is blind to the field, but the gain read at a frequency
where the response is steep.""",
    "tran_h": "The signals in time",
    "tran": """Input and output against time, at a tone a decade below the corner, with the
amplitude chosen from the measured gain so the output lands near 0.6 V peak-to-peak and
cannot clip.  Input and output are drawn on two panels sharing the time axis rather than
one pair of scales: the input is under ten millivolts and the output is hundreds, and on
one scale the input would be a flat line.

This is also the check that the AC gain is not lying.  The gain read off these waveforms
and the gain read off the AC sweep at the same frequency agree to {err2:.2f} dB on OPAM2.
On OPAM they differ by {err1:.1f} dB, and that difference is the subject of the page on
what the AC analysis does not see.""",
    "cap_gvf": "Gain against relative mobility change, one line per probe tone",
    "cap_io": "Input and output against time, best corner",
    "cap_bode": "Gain and phase against frequency, three corners",
    "cap_tf": "Output against differential input",
    "cap_sine": "A sine inside the band, best corner",
    "cap_bw": "The -3 dB corner against relative mobility change",
    "cap_probe": "Sensitivity against where the probe tone sits",
}

ES = dict(EN)
ES.update({
    "kicker": "UCI/INRF - MMM Lab - amplificadores IGZO TFT",
    "footer": "TFT-MMM-LAB-PDK - igzo_mmm_lab - cada numero calculado desde los modelos",
    "t1": "Dos amplificadores IGZO TFT,\ndimensionados contra el proceso medido",
    "intro_h": "Que es esto",
    "intro": """Dos amplificadores operacionales dibujados en el proceso IGZO TFT de UCI/INRF,
cada uno reproduciendo un circuito publicado, y dimensionados aqui para la mayor
ganancia en lazo abierto que el proceso aguanta de verdad en todos sus corners.

  OPAM2   segun Zysset et al., IEEE EDL 34(11), 2013 - un opamp all-enhancement de
          16 TFT, publicado con 18.7 dB y 900 uW sobre poliimida flexible.
  OPAM    segun Zhao et al., IEEE TBCAS 18(6), 2024 - un par cross-coupled con carga
          bootstrap por condensador, publicado con 43.5 dB.

Una tercera variante, OPAM con el bias generado en el chip, elimina por completo el
pin de polarizacion externo. Importa mas de lo que parece: el umbral se mueve 0.62 V
del mejor corner al peor, asi que un bias externo fijo hay que reajustarlo en cada
corner, y una cadena de dispositivos en diodo hace ese seguimiento sola.""",
    "proc_h": "Que da el proceso, y que no",
    "proc": """Todo lo que sigue sale de cuatro hechos sobre los modelos, y conviene leerlos
antes que cualquier numero de este informe.

  1. Los modelos son solo de continua, SPICE nivel 1, validados para VGS <= 6 V y
     VDS <= 10 V. Todos los barridos de aqui se quedan dentro de esa caja.
  2. gm/gds = 2/(lambda*Vov) no depende de L. Los canales largos no compran ganancia
     en este proceso; un sobreimpulso pequeno y una impedancia de carga alta, si.
  3. La resistencia de contacto es Rd = Rs = 3.3/W ohmios con W en metros - 3.3 kohm
     en un dispositivo de 1000 um. Degenera el surtidor, asi que una entrada ancha es
     ganancia directa.
  4. Vto va de +0.09 V (best) a -0.26 V (tt) y a -0.53 V (all). Esos 0.62 V de
     dispersion son la restriccion mas dura de todo el diseno.""",
    "size_h": "Dimensionamiento",
    "size": """Anchuras y longitudes son dimensiones dibujadas en micrometros, agrupadas por
funcion; los dispositivos que deben aparearse comparten tamano. El multiplicador m es
1 en todas partes: dos dispositivos de anchura W en paralelo son exactamente uno de
anchura 2W en este wrapper, porque la resistencia de contacto va como 1/W y la
capacidad de solape como W.""",
    "gain_h": "Como estimar la ganancia antes de simular",
    "gain": """Tres expresiones cubren todas las etapas de los dos circuitos. Vale la pena
evaluarlas a mano, porque dicen que termino esta fijando la ganancia - cosa que el
resultado del simulador no dice.

  transconductancia     gm  = Kp * (W/L) * Vov
  conductancia salida   gds = lambda * Id
  ganancia intrinseca   gm/gds = 2 / (lambda * Vov)

  etapa con carga diodo Av = gm_drv / (gm_load + gds)
                           = raiz( (W/L)_drv / (W/L)_load )  = Vov_load / Vov_drv
  par cross-coupled     Av = gm_in / (gm_load - gm_cc + gds)
  degeneracion contacto gm_ef = gm / (1 + gm*Rs),  Rs = 3.3/W

La del par cross-coupled es la que hay que respetar. Compra ganancia restando de la
conductancia de carga, y cuando gm_cc se acerca a gm_load la ganancia se dispara - y
despues engancha. Un diseno que vive cerca de esa cancelacion es un diseno que depende
del apareamiento, asi que hay que comprobarlo en todos los corners y frente a
desapareo, no solo en el punto nominal.""",
    "bw_h": "Como estimar el ancho de banda, y por que es el numero mas debil de aqui",
    "bw": """El polo dominante es 1/(2*pi*R*C) en el nodo interno con el producto mayor. R es
uno partido por la conductancia de derivacion en ese nodo; C es la suma de las
capacidades de solape de puerta de cada terminal que llega, Cov = Cox * ov * W por
lado, mas cualquier placa MIM. Elegir el nodo a ojo no funciona: en OPAM2 la salida
esta sobre una carga diodo y su polo queda a un kilohercio, mientras que el codo real
lo fija el drenador de la primera etapa. Barrer todos los nodos lo encuentra.

Es la cifra menos fiable del informe, y por un motivo declarado. Cox esta medido -
1.564 fF/um2, de la placa de 400 x 400 um. El solape de puerta de 5 um por el que se
multiplica se leyo de una celda del GDS, y nada en este PDK se ha comprobado nunca
contra una C-V medida ni contra un parametro S. Trata el ancho de banda como un orden
de magnitud, no como una especificacion.""",
    "res_h": "Resultados",
    "res": """Ganancia diferencial en lazo abierto, medida con una fuente AC diferencial de
1 V y leida en el pico de la respuesta. Todos los corners cumplen las mismas
restricciones: cada dispositivo en saturacion, cada VGS y VDS dentro de la caja
validada, la salida entre el 20 y el 80 % de la alimentacion, y el consumo por debajo
de los 900 uW que reporta el paper de Zysset.""",
    "exp_h": "Son los resultados los esperados?",
    "exp": """Las estimaciones a mano y el simulador coinciden donde la topologia es simple y
se separan donde se apoya en una cancelacion - que es exactamente donde cabe esperarlo.

Frente a los papers: OPAM2 llega a 32 dB en su peor corner donde el paper reporta
18.7 dB, con 67 uW frente a 900 uW. No es un circuito mejor, es uno mas grande - los
dispositivos aqui miden cientos de micrometros porque el proceso es lento. OPAM llega
a 63 dB en el mejor corner frente a los 43.5 dB publicados, pero la cifra honesta es la
medida con una forma de onda real, y esa es 52.5 dB. Dos efectos explican la
diferencia, y los dos merecen decirse claramente.""",
    "gap_h": "Dos cosas que el analisis AC no ve",
    "gap": """La primera: el nodo de puerta del bootstrap se bombea por encima de la
alimentacion. En el punto de operacion de continua esta exactamente en VDD; en un
transitorio asentado esta 175 mV mas arriba, porque la senal le inyecta carga por C2 y
la unica salida es la fuga del dispositivo en corte. La salida de esa etapa se mueve
167 mV con el, y eso cuesta 11 dB. Un analisis AC linealiza en el punto de continua y
no ve nada de esto. No es un artefacto de simulacion: un nodo de bootstrap flotante en
silicio se bombea igual, y donde se asiente depende de una corriente de fuga que este
modelo da como exactamente cero.

La segunda: el margen de fase es negativo. Como bloque de ganancia en lazo abierto -
que es lo que caracterizan los dos papers - esta bien. Cerrado a ganancia unidad
oscilaria. El paper de Zhao lleva un lazo de compensacion de fase en el titulo; el
dimensionamiento de aqui no lo tiene, y la busqueda nunca tuvo el margen de fase como
restriccion, porque optimizar contra un numero AC que este PDK no puede validar seria
optimizar contra una suposicion.""",
    "bias_h": "Generar el bias en el chip",
    "bias": """El pin de bias externo necesitaba una tension distinta en cada corner - 1.25 V,
0.90 V, 0.63 V - porque lo que el dispositivo de cola necesita es un sobreimpulso fijo,
y el umbral se le mueve por debajo. Tres dispositivos en diodo de VDD a VSS lo
resuelven sin pin: el tap queda a un salto puerta-surtidor sobre VSS, y un salto
puerta-surtidor es Vth + Vov, asi que sigue al umbral solo. La parte alta de la cadena
se parte en dos para que ningun dispositivo tenga mas de media alimentacion sobre su
puerta; uno solo ahi estaria a VGS = 6.7 V, fuera de la caja validada.

Sigue el 39 % del desplazamiento de umbral, no el 100 %: un divisor de dos ramas no
puede hacer mas, porque el sobreimpulso que produce es una fraccion fija de
(VDD - 2*Vth), y eso crece cuando Vth baja. Un seguimiento perfecto necesitaria una
corriente de referencia proporcional a Kp. Lo que importa es que el amplificador cumple
sus restricciones en los tres corners sin ajustar nada entre ellos, y lo hace - el
dimensionamiento absorbe el residuo. La cadena cuesta 0.81 uA, menos del 5 % del total.""",
    "field_h": "Campo magnetico",
    "field": """El wrapper divide la anchura intrinseca entre 1 + (mu*b_scale*B)^2. Como el
nivel 1 solo usa el producto Kp*W/L, eso es lo mismo que dividir Kp, que es lo mismo
que dividir la movilidad - o sea que esto modela magnetorresistencia clasica, y Kn y
resistencia de canal son un solo hecho, no dos. La resistencia de contacto y la
capacidad de solape usan la W exterior y no se mueven con el campo, que es donde la
fisica las deja.

Lo que NO esta modelado: el efecto Hall - una tension transversal, y el efecto con el
que de verdad se construye un magnetometro - y cualquier corrimiento del umbral con el
campo. Si lo que el laboratorio mide bajo campo es alguno de esos, ajustar b_scale
seria forzar el mecanismo equivocado.

Con b_scale = 1 el efecto es (mu*B)^2 = 2.1e-7 por tesla en el mejor corner: dos partes
en diez millones, por debajo de la resolucion de cualquier medida de este informe.
Ademas va con mu al cuadrado, asi que la sensibilidad cambia 31 veces entre el corner
best y el short. La magnetorresistencia clasica en este material no es un sensor.""",
    "sense_h": "La ganancia es ciega al campo; el ancho de banda no",
    "sense": """Un cambio uniforme de movilidad casi no mueve la ganancia. No es suerte, es la
topologia: la ganancia esta fijada por cocientes de dispositivos identicos, y un cambio
que los escala a todos juntos deja los cocientes intactos. Reduce la anchura efectiva
un 95 % y la ganancia cae 0.6 dB - mientras la corriente de alimentacion cae un 95 % y
el ancho de banda un 82 %.

Eso senala cual es la medida que hay que hacer. Coloca un tono de sonda donde la
respuesta tiene pendiente, y un desplazamiento de ancho de banda se convierte en un
cambio de amplitud. En el codo vale unas 2.5 veces la banda plana; una decada mas alla
del codo, donde esta toda la caida, OPAM da 10.3 dB de salida por unidad de cambio
relativo de movilidad frente a 0.94 dB en la banda plana - once veces mejor.

Dado la vuelta, ese es el numero que hay que darle al laboratorio: para una decima de
decibelio de cambio de salida a un tesla, el efecto medido tendria que estar unas 216
veces por encima del clasico. Si no lo esta, este amplificador no es el sensor - y donde
hay que mirar es en una topologia en la que solo una rama vea el campo, para que los
cocientes dejen de cancelarse.""",
    "lim_h": "De que fiarse y de que no",
    "lim": """  Ganancia, punto de operacion, swing, consumo    fiables. Los modelos reproducen
      curvas de salida medidas con una mediana simulado/medido de 1.01 sobre 18
      dispositivos, y todos los numeros de aqui caen dentro de la caja validada.
  Ancho de banda, margen de fase, todo lo AC     un orden de magnitud. Cox esta
      medido; el solape que fija todas las capacidades se leyo de una celda del GDS
      y nunca se comprobo contra una C-V.
  La ganancia en transitorio de OPAM             mas fiable que su ganancia AC,
      porque el nivel de continua del nodo de bootstrap lo fija una fuga que el
      modelo pone a cero.
  Campo magnetico                                el termino clasico es correcto y
      despreciable. Cualquier cosa mayor es una medida que este PDK no ha hecho.
  El nivel 1 va un 20 % pesimista en gm, porque el exponente de saturacion medido es
      2.31 y no el 2 de la ley cuadratica.""",
    "col_corner": "corner", "col_gain": "ganancia", "col_stage1": "etapa 1",
    "col_stage2": "etapa 2", "col_f3db": "f-3dB", "col_pm": "swing",
    "col_pow": "consumo", "col_vout": "salida", "col_bias": "BIAS",
    "col_fn": "funcion", "col_dev": "dispositivos", "col_w": "W (um)",
    "col_l": "L (um)", "col_wl": "W/L",
    "col_est": "estimado", "col_sim": "simulado", "col_err": "diferencia",
    "col_stage": "etapa", "col_tone": "tono de sonda", "col_freq": "f (Hz)",
    "col_sens": "dB por unidad de dmu/mu",
    "gvf_h": "Ganancia frente al campo, una curva por tono de sonda",
    "gvf": """Cada curva es un tono mantenido a frecuencia fija mientras el campo mueve el
circuito por debajo. La curva mas baja esta una decada por debajo del codo, en la banda
plana, y casi no se mueve - un cambio de movilidad escala todos los dispositivos juntos y
los cocientes que fijan la ganancia no se enteran. Cuanto mas arriba esta el tono en la
caida, mas lee del mismo cambio: en todo el barrido el tono de banda plana
pierde {gvf_flat:.1f} dB y el que esta a treinta veces el codo pierde {gvf_edge:.1f} dB.

Esa es la medida sobre la que construir un sensor, si el efecto llega alguna vez a ser
medible: no la ganancia, que es ciega al campo, sino la ganancia leida a una frecuencia
donde la respuesta tiene pendiente.""",
    "tran_h": "Las senales en el tiempo",
    "tran": """Entrada y salida frente al tiempo, con un tono una decada por debajo del codo y
la amplitud elegida a partir de la ganancia medida para que la salida quede cerca de
0.6 V pico-pico y no pueda recortar. Entrada y salida van en dos paneles que comparten el
eje de tiempo, no en un par de escalas: la entrada esta por debajo de diez milivoltios y
la salida en cientos, y en una sola escala la entrada seria una linea plana.

Es tambien la comprobacion de que la ganancia AC no miente. La ganancia leida de estas
formas de onda y la del barrido AC a la misma frecuencia coinciden en {err2:.2f} dB en
OPAM2. En OPAM difieren en {err1:.1f} dB, y esa diferencia es el tema de la pagina sobre
lo que el analisis AC no ve.""",
    "cap_gvf": "Ganancia frente al cambio relativo de movilidad, una linea por tono",
    "cap_io": "Entrada y salida frente al tiempo, corner best",
    "cap_bode": "Ganancia y fase frente a la frecuencia, tres corners",
    "cap_tf": "Salida frente a entrada diferencial",
    "cap_sine": "Un seno dentro de la banda, corner best",
    "cap_bw": "El codo de -3 dB frente al cambio relativo de movilidad",
    "cap_probe": "Sensibilidad segun donde se coloque el tono de sonda",
})

STRINGS = {"en": EN, "es": ES}
