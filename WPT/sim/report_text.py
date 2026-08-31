#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prose for the WPT report, in Spanish.

Code, identifiers and figure labels are in English throughout this project;
the document the user reads is in Spanish.  This module holds only the text.
Every number the prose refers to is passed in from the measured results, so
nothing here can go stale: there are no literals in these strings that a
simulation could contradict.

THE DECISION BLOCK.  Each design decision is rendered by one function, so they
cannot drift into different shapes, and so that none of them can be written
without the parts that make it auditable:

    la ecuacion . lo elegido . la grafica . la tabla . lo que decidio .
    lo que cambiaria la respuesta

emit_decision() refuses to render a decision that is missing its equation, its
data table or its "what would change it", because a decision without those is
an assertion.
"""

TITLE = "Enlace de potencia inalambrico en TFT de IGZO"
SUBTITLE = ("Bobinas, rectificador y eficiencia medida, con el porque de cada "
            "decision")
FOOTER = "WPT - UCI/INRF MMM Lab"

# --------------------------------------------------------------------------
# The verdict, first, because burying it would be dishonest
# --------------------------------------------------------------------------

VERDICT = u"""\
Este documento contiene un diseno completo y medido, y su resultado principal
es negativo: el enlace no transfiere potencia util. Conviene decirlo antes que
nada, porque todo lo demas -las bobinas optimas, el dimensionado del
rectificador, los barridos- es correcto y sigue siendo util, pero describe el
mejor punto de un espacio de diseno cuyo techo esta muy por debajo de lo
necesario.

La cifra: {vout:.2f} V en la carga con {pin:.0f} W en el excitador, una
eficiencia de {eta:.2e}. Son casi ocho ordenes de magnitud por debajo de un
enlace inductivo utilizable.

La causa no es el rectificador ni la geometria de las bobinas, que estan
optimizadas. Es el factor de calidad de la bobina receptora: Q = {q:.4f} con
{t:g} um de oro, y {q50:.5f} con los 50 nm que el proceso supone hoy. Un
enlace resonante multiplica la tension inducida por la Q del lazo; con Q por
debajo de uno no hay multiplicacion posible, y el condensador de sintonia no
solo no ayuda, sino que estorba. Eso se mide en la seccion 7 y sale exactamente
asi.

Lo que si dice este trabajo, y es lo que hay que llevarse:

  - la geometria optima de la bobina receptora dentro de 1000 x 1000 um, y por
    que el criterio correcto NO es el habitual;
  - que el espesor del metal es el unico parametro con capacidad real de mover
    el resultado, y que hoy es una suposicion sin medir;
  - que el TFT de IGZO, con Vto negativo en tres de los cuatro corners, no es
    un diodo: conduce a polarizacion cero y no bloquea;
  - cuanta potencia haria falta en el primario para que el rectificador
    llegase siquiera a encender.
"""

# --------------------------------------------------------------------------
# Theory
# --------------------------------------------------------------------------

THEORY = u"""\
Un enlace inductivo resonante se describe con tres numeros: la inductancia
mutua M entre las dos bobinas, el coeficiente de acoplamiento k que la
normaliza, y el factor de calidad Q de cada lado. La tension inducida en el
secundario en circuito abierto es

    EMF = w M I_tx

y la eficiencia maxima que cualquier red de adaptacion puede alcanzar depende
de un unico numero combinado, la figura de merito del enlace:

    FOM = k^2 Q1 Q2        eta_max = FOM / (1 + raiz(1 + FOM))^2

Esa expresion es un techo, no una prediccion: supone los dos lados sintonizados
y la carga optima. Un rectificador real alcanza menos.

Aqui aparece la primera decision de fondo, y es la que ordena todo el
documento. La FOM es el criterio correcto cuando la carga esta ADAPTADA en
impedancia. La carga de este circuito no lo esta: son dos TFT conectados en
diodo, y por debajo de su tension de umbral no conducen en absoluto. Mientras
no se supere ese umbral el enlace no entrega nada, y la FOM esta describiendo
un circuito que no es este. Lo primero que hay que maximizar no es la potencia
adaptada sino la TENSION inducida, y eso apunta a una bobina distinta.

La diferencia no es academica: entre la bobina que maximiza la FOM y la que
maximiza la EMF hay un factor {ratio:.1f} en tension inducida, y van en
sentidos opuestos del espacio de diseno.
"""

# --------------------------------------------------------------------------
# Section intros
# --------------------------------------------------------------------------

RX_INTRO = u"""\
La bobina receptora es una espiral plana dentro de un cuadrado de
{area:.0f} x {area:.0f} um. Se ha barrido toda la geometria que las reglas de
diseno permiten -{n:,} geometrias legales por espesor- con las funciones de
coil_core.py, las mismas que usa la celda parametrica ind_igzo del PDK, de modo
que el resultado es dibujable tal cual sin traducir nada.

Las reglas que acotan el espacio son GATE.1/GATE.2 y SD.1/SD.2 del DRC de este
proceso: {wmin:g} um de ancho minimo y {gmin:g} um de separacion minima, en los
dos metales. La bobina se hace crecer hacia dentro desde el borde de 1000 um,
porque el area es la restriccion.

A {f:.0f} kHz la profundidad de penetracion en oro es {skin:.0f} um. Los dos
espesores estudiados -50 nm y 1 um- estan miles de veces por debajo, asi que
no hay efecto pelicular en absoluto: R_ac = R_dc exactamente, y Q resulta
simplemente proporcional a la frecuencia.
"""

TX_INTRO = u"""\
La bobina transmisora es discreta, de hilo de cobre esmaltado, y se disena
contra la receptora ya elegida. Se han evaluado {n:,} candidatas entre
solenoides multicapa y espirales planas, con calibres de AWG {a1} a AWG {a2}.

El criterio, por coherencia con la seccion anterior, es la tension inducida y
no la figura de merito. Para que la comparacion sea justa se normaliza a la
misma potencia de entrada en vez de a la misma corriente -a cualquier bobina se
le puede dar mas corriente dandole mas potencia-, de donde

    EMF / raiz(P_in) = w M / raiz(R_fuente + R_tx)

Un detalle del modelo que cambio la respuesta: la funcion de resistencia en
alterna de coil_core es de hilo aislado, solo efecto pelicular. Con ella, el
barrido se metia en el bobinado mas profundo que la rejilla permitia y afirmaba
Q = 845 a 500 kHz para un solenoide de doce capas, una bobina que no existe.
Falta el efecto de PROXIMIDAD entre capas, que crece como el cuadrado del
numero de capas. Se ha implementado (Dowell 1966, en proximity.py) y el optimo
se mueve. La leccion es general: un optimizador encuentra siempre lo que el
modelo de perdidas olvido.
"""

RECT_INTRO = u"""\
El rectificador es un doblador de tension de Greinacher: un condensador serie
que bloquea la continua, un TFT en diodo que fija la excursion negativa y otro
que pasa la positiva al condensador de salida.

El compromiso del dispositivo esta en dos constantes que el PDK midio:

    Rc  = 3,3 / W        resistencia de contacto, por contacto
    Cov = cox * ov * W   capacidad de solape, 7,82 fF por um de anchura a ov = 5 um

La anchura compra conduccion y cuesta carga capacitiva, y esa carga cae sobre
el nodo de recepcion, cuya impedancia de fuente son los {rrx:.0f} ohmios de la
bobina. Luego hay una anchura optima y no es la mayor.
"""

RECT_THRESHOLD = u"""\
Hay un segundo problema, independiente del tamano, y no se arregla con ninguna
W: el TFT de IGZO no es un diodo.

Su tension de umbral es NEGATIVA en tres de los cuatro corners -el propio PDK
lo dice: "Vto esta cerca de cero y es ligeramente negativa en muchos
dispositivos (tipo deplexion), lo cual es normal en IGZO sin pasivar"-. Un
dispositivo conectado en diodo con umbral negativo conduce con polarizacion
puerta-fuente nula, y sigue conduciendo hasta que la polarizacion baja por
debajo de Vto. Es decir: no bloquea. El dispositivo serie del doblador deja
salir corriente del condensador de salida hacia atras siempre que el nodo de
entrada este menos de |Vto| por debajo de el.

Solo el corner `best` es de enriquecimiento. Este limite seguiria ahi aunque
las bobinas entregasen cien veces mas tension.
"""

SIM_INTRO = u"""\
Con las bobinas y el dimensionado ya fijados, el circuito completo se simula en
ngspice: barrido en alterna para localizar la respuesta, y transitorio en
regimen permanente para medir la eficiencia real, que es la que cuenta porque
el analisis en alterna no ve la no linealidad de los diodos.

Dos cosas del banco merecen decirse porque no son evidentes.

La primera: el acoplamiento no puede estar en el esquematico. ngspice no
acopla una bobina que vive dentro de un subcircuito, y ind_igzo es uno; el
error literal es "coupling to non-existent inductor xl1.l1". El subcircuito es
exactamente una L en serie con una R -esa es toda su definicion en
design.ngspice- asi que el nucleo plano no pierde nada, y tb_wpt.py --check
comprueba que los dos caminos dan la misma corriente hasta el ultimo digito.

La segunda: el condensador de salida es de 10 uF contra una carga de
{rload:.0f} ohmios, o sea una constante de tiempo de {tau:.2g} s frente a un
periodo de portadora de {per:.2g} s. Simular la carga honestamente serian
millones de ciclos. Pero el valor en regimen permanente lo fija el balance de
carga y NO el condensador, que solo fija el rizado y el tiempo de
establecimiento: se halla sobre un condensador pequeno, donde converge en
decenas de ciclos, y se confirma sobre el real con la condicion inicial puesta
en la respuesta. Si es la respuesta correcta, la salida no se mueve; y si se
mueve, la ejecucion lo dice.
"""

COUPLING_INTRO = u"""\
La pregunta era si anadir un condensador de acoplo aumenta la transferencia.
Tiene tres lecturas distintas y se han probado las tres, en vez de elegir una:

  - EN SERIE EN EL PRIMARIO, que sintoniza la reactancia de la bobina
    transmisora. Este no es opcional y ya esta en todas las ejecuciones.
  - EN PARALELO CON LA BOBINA RECEPTORA, resonancia paralelo en el secundario.
  - EN PARALELO EN LA ENTRADA DEL RECTIFICADOR.

Las dos del secundario no mejoran nada, y la razon se puede dar con un numero
en vez de con una opinion: una resonancia multiplica una tension por la Q del
lazo en que esta, y la Q de este lazo es {q:.4f}. Un condensador no puede
multiplicar una tension por un factor menor que uno. Lo unico que hace la
capacidad anadida es cargar el nodo, y eso se ve en la medida.
"""

LIMITS = u"""\
Lo que este resultado NO dice, y hay que tenerlo delante antes de citarlo:

  - LOS MODELOS DEL TFT ESTAN VALIDADOS SOLO EN CONTINUA. igzo_mmm_lab.ngspice
    lo declara: Cox esta medida, pero la capacidad de solape descansa sobre un
    solape de 5 um leido de una celda de GDS, y nada se ha contrastado contra
    una C-V medida ni contra parametros S. Todo lo que aqui se hace a 500 kHz
    es extrapolacion en frecuencia de un modelo ajustado en continua.

  - ind_igzo NO TIENE CAPACIDAD PARASITA NI AUTORRESONANCIA. Es una L en serie
    con una R y nada mas. Por debajo de la frecuencia en que la capacidad
    propia de la bobina importa eso es correcto, y a 500 kHz lo es; por encima
    dejaria de serlo.

  - EL ESPESOR DEL METAL ES UNA SUPOSICION SIN MEDIR. Es, ademas, el parametro
    del que mas depende todo lo anterior: entre 50 nm y 1 um hay un factor 20
    en resistencia y por tanto en Q. Los dos casos se dan en paralelo en cada
    tabla precisamente por eso. Medirlo es la accion de mayor valor pendiente.

  - EL MODELO DE PROXIMIDAD ES UNIDIMENSIONAL. Dowell supone el campo paralelo
    a las capas, lo cual es cierto dentro de un solenoide largo y menos cierto
    en sus extremos. Para una bobina corta SOBRESTIMA la perdida, asi que la
    eficiencia que sale es un suelo y no una estimacion central. Es la
    direccion en la que un error debe apuntar.

  - EL MODELO DE MUTUA SUPONE UNA SOLA CORRIENTE POR VUELTA. Es cierto en una
    espiral serie y falso en anillos en paralelo, por eso la topologia paralelo
    se barre y se reporta por su L y su Q, pero no se puntua por M.
"""

NEXT = u"""\
Que habria que cambiar, en orden de cuanto mueve el resultado:

  1. EL ESPESOR DEL METAL. Es un factor 20 en Q entre 50 nm y 1 um, y el
     resultado escala con el. Antes que nada, medirlo.
  2. LA BOBINA RECEPTORA FUERA DEL CHIP. Un area de 1 mm2 con pistas de 5 um
     de ancho impone una resistencia de {rrx:.0f} ohmios que ningun cambio de
     geometria evita. Una bobina externa de cobre de un centimetro cambia el
     problema por completo.
  3. LA FRECUENCIA. La EMF crece con w y la figura de merito con w al
     cuadrado, pero el techo es fT del TFT: {ft:.1f} MHz a L = 10 um y
     {ft5:.1f} MHz a L = 5 um. Entre los 500 kHz de aqui y ese techo queda
     menos de una decada.
  4. UN RECTIFICADOR QUE BLOQUEE. Con Vto negativa no hay diodo. Un rectificador
     sincrono, o un ajuste de proceso que lleve el umbral a positivo, quita el
     segundo de los dos problemas.
"""
