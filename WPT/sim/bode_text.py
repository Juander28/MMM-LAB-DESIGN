#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prose for the transient-Bode report, in Spanish.

Code and labels in English throughout the project; the document the user reads
is in Spanish.  No literal number lives in these strings - everything is
substituted from the measured results, so the text cannot drift away from the
data it describes.
"""

TITLE = "Bode por transitorio y acoplamiento"
SUBTITLE = ("Segunda parte del estudio WPT: lo que el analisis AC no puede\n"
            "decir, y un banco que puedes manejar tu")
FOOTER = "WPT fase 2 - UCI/INRF MMM Lab"

ASSUMPTIONS = u"""\
ESTE DOCUMENTO NO USA LOS MISMOS SUPUESTOS QUE EL ANTERIOR. Conviene ponerlo
delante para que los dos no se contradigan sin avisar:

                        este informe            WPT_diseno_es.pdf (fase 1)
  separacion            {z:g} mm                   5 mm
  longitud de canal L   {l:.0f} um                    5 um
  bobina transmisora    {txl:.3f} uH, {txd:g} mm       171,5 uH, 15 mm
  acoplamiento k        {k:.4e}              3,5840e-03
  V(C3) a {f:.0f} kHz      {v:.3f} V                  0,801 V

Los tres cambios, y de donde salen:

  - La SEPARACION. La fase 1 asumio 5 mm sin preguntartelo. Trabajas a
    contacto. Sobre la bobina de la fase 1 eso solo ya valia 2,75 veces en
    tension.
  - LA BOBINA TRANSMISORA. Cambiada a raiz de tu observacion, y es el cambio
    grande: la seccion 5 lo desarrolla.
  - LA LONGITUD DE CANAL. El barrido prefiere 5 um, el minimo del DRC.
    Elegiste 10 um; la seccion 6 dice lo que cuesta.

El factor {vgain:.1f} entre los dos informes es de los tres juntos, no de uno
solo, y no se puede repartir limpiamente porque interactuan.

Y una correccion de un numero que te di al preguntarte por la distancia: dije
que a 1 mm el acoplamiento seria diez veces mejor y la eficiencia unas cien
veces. Era falso. Ese factor diez venia de encoger la bobina - que resulto ser
cierto y es la seccion 5 - no de acercarla. La distancia sola, a igual bobina,
vale 2,2 veces en acoplamiento.
"""

METHOD = u"""\
Un diagrama de Bode se hace normalmente con un barrido en alterna, y aqui no
sirve. El analisis `ac` de ngspice lineariza cada dispositivo alrededor de su
punto de operacion, y los dispositivos de este circuito son dos TFT conectados
en diodo cuyo trabajo entero es ser no lineales. Un barrido AC de este circuito
informa de la respuesta en pequena senal de un rectificador que no esta
rectificando.

Asi que cada punto se obtiene corriendo el TRANSITORIO a esa frecuencia y
leyendo la continua que aparece de verdad sobre C3. Las dos curvas van
superpuestas en la figura, y donde se separan esta justo lo que el AC no puede
decir.
"""

SETTLING = u"""\
EL PROBLEMA DEL ASENTAMIENTO, QUE ES LA PARTE DIFICIL, y tenias razon en
mencionarlo: hace falta mas tiempo, y mucho mas del que parece.

El filtro de salida son {cout:g} uF contra {rload:.0f} ohmios, o sea una
constante de tiempo de {tau:.3g} s. La portadora a {f:.0f} kHz tiene un periodo
de {per:.3g} s. Simular la carga honestamente son unas cinco constantes de
tiempo: **{naive:,.0f} ciclos de portadora** para UN punto de un barrido de
{npts} puntos. Eso no es cuestion de paciencia, es aritmetica, y no hay maquina
que lo haga en un tiempo razonable.

Lo que lo salva es que el valor asentado NO depende del condensador de salida.
Lo fija el balance de carga: lo que los diodos entregan por ciclo es igual a lo
que la carga consume. El condensador fija el rizado y el tiempo de
establecimiento, y nada mas. De ahi las tres etapas:

  1. SEMBRAR - hallar la respuesta sobre un condensador deliberadamente
     pequeno, elegido para que su constante de tiempo sean unos veinte periodos
     de portadora. Asienta en unos cientos de ciclos y converge a la misma
     tension.
  2. CONFIRMAR - correr el condensador real de {cout:g} uF arrancando en
     caliente desde esa respuesta, con `.ic v(out)=`. Si la semilla era buena
     la salida no se mueve; la deriva a lo largo de la ventana de medida es la
     prueba, y se MIDE, no se supone.
  3. ALARGAR - si se mueve, volver a arrancar donde acabo y doblar la
     duracion. Parar cuando este estable, o al llegar al tope - y un punto que
     llego al tope se reporta como NO ASENTADO, con marcador hueco, nunca
     colado como si hubiera convergido.

Resultado: cada punto converge en {typ:,.0f} ciclos en vez de {naive:,.0f}, un
factor {saving:.0f}. La tabla da los ciclos que hizo falta en cada frecuencia.
"""

RESONANCE_TRAP = u"""\
UNA TRAMPA QUE COSTO UN BARRIDO ENTERO, y merece contarse porque no dio ninguna
senal de que algo iba mal.

La primera version de este barrido se hizo con la bobina transmisora de la fase
1, la de 171,5 uH. Sintonizada, su lazo tenia una Q de {q_old:.0f}, de modo que
el pico media unos {bw_old:.0f} kHz de ancho. La rejilla era solo logaritmica,
{ppd} puntos por decada, que cerca de {f:.0f} kHz avanza a saltos de
{step:.0f} kHz.

La rejilla salto por encima del pico entero. El punto mas cercano cayo a dos
anchos de banda de la resonancia, el maximo que reporto fue {wrong:.3f} V
cuando el verdadero era {right_old:.2f} V - un factor {ratio:.0f} - y la curva
salia suave y creible. No hay aviso posible: una rejilla logaritmica es la
eleccion correcta para mirar decadas y la equivocada para resolver un pico
estrecho, y el resultado de usarla mal se parece exactamente a un resultado
bueno.

El barrido lleva ahora {extra} puntos extra repartidos sobre la resonancia, y
la frecuencia de trabajo esta metida explicitamente en la rejilla porque un
grupo de puntos equiespaciados la rodea sin tocarla.

Con la bobina de {txl:.3f} uH que este informe adopta el problema ya no
aparece: la Q del lazo baja a {q_new:.1f} y el pico se ensancha hasta
{bw_new:.0f} kHz, de sobra para cualquier rejilla. Pero eso es suerte del
diseno nuevo, no del metodo, y por eso los puntos extra se quedan.
"""

K_INTRO = u"""\
Preguntaste dos cosas sobre el acoplamiento y las dos tienen respuesta con
numeros.

"ESTO FUE ASUMIENDO 1 DE k, MIRA SI ES LO MEJOR." k = 1 significa enlace de
flujo perfecto: cada linea de campo que crea el primario atraviesa el
secundario y vuelve. Entre una bobina de milimetros y un milimetro cuadrado de
espiral sobre vidrio eso no puede pasar a ninguna distancia. Asi que la
pregunta no es si k = 1 es mejor -claro que mas acoplamiento es mejor- sino
cuanto por debajo esta la realidad. La geometria da k = {k:.4e} a {z:g} mm. La
tabla dice lo que k = 1 daria, y es un techo, no una opcion.

"CUANDO BOBINAS MAS PEQUENAS HABIA MEJOR ACOPLE, POR EJEMPLO DE 1 uH." Tenias
razon, y la razon esta en la definicion: k = M / raiz(L1 L2), asi que bajar L1
sube k aunque M no se mueva. El barrido completo lo confirma y anade algo mejor
todavia, que esta en la seccion siguiente.
"""

TX_L_FINDING = u"""\
Y sale algo que no esperaba. La bobina de {near_l:.3g} uH no solo acopla
{kratio:.0f} veces mejor que la de {best_l:.4g} uH: entrega {vratio:.0f} % de
su tension de salida. Es decir, **empata en lo que importa con doce veces mejor
acoplamiento y una construccion mucho mas simple**.

Es la que recomiendo. La diferencia practica no es pequena: {near_desc} frente
a {best_desc}.
"""

L10_INTRO = u"""\
Pediste L = 10 um en los transistores. El barrido prefiere 5 um, que es el
minimo que permite el DRC de este proceso (regla SD.2), porque la corriente de
un TFT va como W/L y nada dentro del espacio permitido frena a L hacia abajo.

Es tu decision y se documenta con el numero, no se discute. Lo que cuesta esta
en la tabla. Vale la pena saber que hay un argumento a favor de tu eleccion que
el barrido no puede ver: el PDK dice que una L dibujada de 5 um se imprime a
unos 8 um -su parametro `l_bias`, medido sobre UNA muestra- asi que a 5 um
dibujados el sesgo del proceso es del 60 % y a 10 um es del 30 %. Un
dispositivo mas largo es un dispositivo cuyo tamano real se conoce mejor.
"""

SCHEMATIC_INTRO = u"""\
Hay dos esquematicos y no son redundantes.

WPT.sch es tu dibujo, con el que ngspice acopla porque cambiaste la bobina
receptora de la celda `ind_igzo` a un `ind.sym` normal. Esa fue la decision
correcta y es la razon de que el fichero simule: `ind.sym` genera una L
desnuda, y `K1 L1 L2` puede alcanzarla. Un subcircuito no.

WPT_sim.sch es la version generada desde `params.py`, con las dos bobinas como
inductor mas resistencia en serie, el condensador de sintonia del primario
DIBUJADO -no en un bloque de texto- y los bloques de control listos. Se abre,
se netlista y se simula.

UN ERROR MIO QUE HAY QUE CORREGIR EN TU DIBUJO. El bloque de codigo de WPT.sch
lleva esta linea:

    CTX  n_txa n_tx1 590.855p

`n_txa` y `n_tx1` son nombres de nodo del netlist plano de `sim/tb_wpt.py`, y
en tu esquematico NO EXISTEN: alli los nodos del primario se llaman `tran` e
`IN`. Ese condensador cuelga entre dos nodos nuevos que no tocan nada, o sea
que no hace nada, y el lazo primario se queda sin sintonizar. Medido sobre tu
netlist: {itx:.3f} A de corriente de excitacion donde deberia haber {itx_ok:.3f}.

No se puede arreglar desde el bloque de codigo, porque es un elemento en SERIE:
hay que dibujarlo entre R1 y L2, partiendo la red `IN`. En WPT_sim.sch esta
asi.
"""

PARAMS_INTRO = u"""\
Todo lo que este estudio puede variar vive ahora en un solo fichero,
`sim/params.py`. Cambiar un valor ahi y volver a lanzar es el flujo entero:
ningun script guarda ya su propia copia de un numero.

`python3 params.py` imprime la configuracion y AVISA de las combinaciones que
no pueden significar lo que dicen: frecuencia por encima de fT, k fuera de
[0,1], anchos por debajo del DRC, condensadores que no existen. Y senala las
dos suposiciones de las que depende todo: el espesor del metal, que nadie ha
medido, y que los modelos del TFT estan validados solo en continua.
"""

VERDICT = u"""\
Con la separacion de contacto y L = 10 um el enlace entrega {v:.3f} V sobre
{rload:.0f} ohmios con {pin:.0f} W en el excitador: una eficiencia de {eta:.3e}.

Es {vgain:.1f} veces la tension del informe anterior, y sigue sin ser un enlace
util. Lo que ha cambiado son los supuestos, no el techo: ese lo pone la Q de la
bobina receptora, {q:.4f}, y ninguna de las decisiones de este documento la
toca. Para moverla hay que cambiar el metal o sacar la bobina del chip, que es
lo que decia el informe anterior y sigue diciendo este.
"""
