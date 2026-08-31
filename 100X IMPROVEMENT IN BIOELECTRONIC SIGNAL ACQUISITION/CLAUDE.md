# CLAUDE.md — Contexto del proyecto (leelo antes de tocar nada)

**Proyecto: 100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION**

> Este archivo lo lee Claude Code automaticamente al arrancar en esta carpeta.
> Contiene TODO lo necesario para continuar el trabajo sin repetir errores ya cometidos.

## 1. Que es este proyecto

**100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION** — electrofisiologia resonante.
Colaboracion UCLA (Prof. Tyler Clites / Samantha Herman) — UCI (Prof. C. Velez Cuervo /
Juan Diego Sanchez).

Se trata de resonadores LC acoplados con **pares cross-coupled NMOS** que hacen
**Q-enhancement** (resistencia negativa). Cada canal produce un **notch** (muesca) en la
respuesta AC de una linea diferencial **sin tierra**. La profundidad y el ancho del notch
son lo que se lee para recuperar la senal EMG.

### Requisitos del sistema (no negociables)

| Parametro | Valor | Origen |
|---|---|---|
| Banda de operacion | 50–200 MHz | acoplamiento capacitivo WPT por piel |
| Canales objetivo | >= 1000 | Samantha |
| Ancho de banda por canal | 150 kHz | 150 MHz / 1000 canales |
| **BW del notch (-3 dB)** | **<= 30 kHz** | 5x menor que el BW asignado, evita crosstalk |
| **Q_L requerida** | **>= 1667 @ 50 MHz** (>= 6667 @ 200 MHz) | derivada: Q = f0 / BW |
| Sin tierra dentro del cuerpo | obligatorio | notch entre dos nodos arbitrarios |
| Potencia por canal | <= 100 uW | 100 mW / 1000 canales |
| Senal EMG | +-5 mV diferencial, 20 Hz – 2 kHz | Samantha |

## 2. Estado actual: punto de diseno VERIFICADO

Dos canales co-sintonizados simultaneamente (ambos activos a la vez):

| Canal | f0 | Profundidad | BW-3dB | Q_L | cp (acople) | Itail | Margen a oscilacion |
|---|---|---|---|---|---|---|---|
| A | 55.890 MHz | 35.9 dB | 23.2 kHz OK | 2413 OK | cpA = 280 fF | ItailA = 4.07509 mA | 1.55 % |
| B | **100.002 MHz** | 39.7 dB | 13.9 kHz OK | 7217 OK | cpB = 155 fF | ItailB = 0.65260 mA | 0.90 % |

Ambos canales **CUMPLEN** la spec de BW <= 30 kHz y Q_L >= 1667.
Tanque del canal B retoceado: **C7 = 40.362 pF** (era 60 pF) para caer exacto en 100 MHz.

Verificado en lazo cerrado: el `.sch` de esta carpeta se netlistea con xschem y se simula
con ngspice reproduciendo estos numeros.

## 3. Cinco cosas que YA se descubrieron (no las vuelvas a descubrir)

1. **Corrimiento por retorno compartido.** Los dos canales comparten el retorno `actm`
   hacia VDD a traves de L6 || L4 = 25 nH. Eso **sube y separa** los modos respecto al
   calculo ingenuo: 50.0 / 64.8 MHz calculados -> 54.2 / 83.9 MHz reales (con los valores
   originales). El canal aislado `act1` (que NO comparte retorno) si cae en 49.94 MHz,
   lo que confirma el mecanismo. **Nunca confies en f0 = 1/(2*pi*sqrt(L*C)) a secas:
   siempre verifica con un barrido AC.**

2. **Un solo Itail compartido NO sirve.** Los umbrales de oscilacion dependen fuertisimo
   de la frecuencia (canal A: 4.14 mA, canal B: 0.659 mA). Con una sola corriente es
   imposible realzar ambos canales. Por eso el diseno usa `{ItailA}` e `{ItailB}`
   separados (las fuentes de corriente ya eran independientes en el esquematico).

3. **Los canales interactuan.** Polarizar A a 4.08 mA **baja el umbral de B un ~9 %**
   (0.723 -> 0.659 mA). Hay que co-sintonizar con iteracion de punto fijo sobre ambos
   umbrales, nunca canal por canal aislado.

4. **Existe una cresta de profundidad.** Para cada cp hay un margen de polarizacion optimo
   (compensacion critica). Demasiado cerca del umbral: el notch se angosta y se hace
   somero. Demasiado lejos: no hay realce. Ademas hay un limite estructural: para el canal
   B a 100 MHz, cp mayor a ~200 fF **no puede** cumplir BW <= 30 kHz con ninguna
   polarizacion.

5. **La metrica Q solo vale si el notch es profundo.** Q = f0/BW medido a (linea base
   - 3 dB) es un artefacto cuando la profundidad es <= 3 dB. Las corridas viejas (max
   3.6 dB) daban Q basura. **Exige profundidad >> 3 dB antes de reportar cualquier Q.**

### Sensibilidad — el problema duro pendiente

| Error en Itail | Profundidad resultante |
|---|---|
| +-0.25 % | >= 17 dB |
| +-0.50 % | >= 9 dB |
| +1.00 % en canal B | **OSCILA** |

Una implementacion real necesita **control de amplitud / realimentacion de polarizacion
(AGC)**. Esto es consistente con la literatura de Q-enhancement por gm negativo.

### Potencia — pendiente

7.1 mW para 2 canales (VDD = 1.5 V). Muy por encima del presupuesto de 100 uW/canal.
Es esperable con el NMOS generico (Kp = 1m, W/L = 1); hay que redimensionar dispositivos
y/o hacer duty-cycling.

## 4. Estructura de esta carpeta

```
100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION/
├── CLAUDE.md                    <- este archivo
├── README.md                    <- como correr todo
├── test1/
│   ├── cross_coupled_test1.sch      esquematico xschem (punto de diseno)
│   ├── cross_coupled_test1.spice    netlist YA generado y verificado
│   ├── run_test1.sh                 netlist + simula + analiza
│   ├── analyze_notch.py             f0 / profundidad / BW / Q_L de cada notch
│   └── models/
│       ├── nmosgen_test1.lib        NMOS generico nivel-1 (el de LTspice)
│       └── tft_igzo_template.lib    PLANTILLA para los TFT IGZO de Juan (aun sin datos)
└── x10/
    ├── cross_coupled_x10.sch        el X10 (4 de 10 canales poblados)
    ├── cross_coupled_x10.spice
    ├── run_x10.sh
    ├── analyze_notch.py
    └── models/nmosgen_x10.lib
```

Origen: los esquematicos se generaron desde los `.asc` de LTspice que estan en
`SIMULATION/TEST1/` y `SIMULATION/X10/` del Drive de Juan. El netlist de xschem para X10
es **bit-exacto** contra la traduccion directa del `.asc` (0.0000 dB de diferencia en
28k puntos).

## 5. Como correr (comandos exactos)

Entorno: **un solo contenedor**, `iic-osic-tools_chipathon_xvnc` (imagen
chipathon26). Esta carpeta es `"C:\Users\juand\Documents\GitHub\sscs-2026-zotnetic\designs\100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION"` en el
Windows del usuario, montada como `/foss/designs/100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION` adentro. Lo que
edites aqui se ve del otro lado al instante: **no uses `docker cp`**.

```bash
cd "/foss/designs/100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION/test1"
./run_test1.sh                      # netlistea + simula + analiza
# si xschem falla por config de librerias:
ngspice -b cross_coupled_test1.spice && python3 analyze_notch.py test1_ac.csv
```

> **Contexto del repo.** `/foss/designs` es el repo de tapeout **sscs-2026-zotnetic**
> (GF180MCU, con su propio `xschemrc` en `designs/.config/.xschem/`). Esta carpeta
> `simulaciones/` es un anexo independiente: sus esquematicos usan los simbolos
> genericos de xschem (`devices/*.sym`), NO los del PDK, asi que no dependen de esa
> configuracion ni la afectan. Si el paso de xschem falla por rutas de libreria, usa
> el netlist `.spice` pre-generado (ya esta verificado) — no pierdas tiempo peleando
> con el xschemrc del PDK.
>
> **No toques nada fuera de la carpeta del proyecto** sin que Juan lo pida: ahi vive el
> tapeout real (`DESIGN/`, `libs/`, `zotnetic_layout/`, `a_zonetic2026/`).
> Y ojo: es un repo de git, asi que lo que crees aparecera en `git status`.

**Salida esperada del span completo** (35–210 MHz, paso 3.5 kHz):

```
vector1 notch 1: f0=   55.8884 MHz  depth= 16.33 dB
vector1 notch 2: f0=  100.0033 MHz  depth= 14.07 dB
vector2 notch 1: f0=   38.4406 MHz              <- linea pasiva de referencia
```

> **OJO — trampa de resolucion.** Esos 16/14 dB son **aparentes**. El paso del span
> completo (3.5 kHz) es mas grueso que el BW real del notch (14–23 kHz), asi que
> **subestima** la profundidad. La profundidad real (35.9 / 39.7 dB) solo aparece con
> los zooms. Para medirla: edita el bloque `PARAMS` del `.sch` (o del `.spice`), comenta
> la linea `.ac lin 50000 35Meg 210Meg` y descomenta UNA de estas:
>
> ```
> .ac lin 50000 55.4Meg 56.4Meg    # canal A
> .ac lin 50000 99.6Meg 100.4Meg   # canal B
> ```
>
> Nunca reportes profundidad ni Q desde un barrido de span completo.

## 6. Reglas de diseno (ajustadas a los dos puntos verificados)

- Resonancia serie a traves del capacitor de acople:
  `f0 = 1 / (2*pi*sqrt(L_loop * (C_tanque + cp)))`
- Factor de calidad del tanque: `Q0 = 2*pi*f*L_loop / RS_loop`
- Spec: `Q_L = f0 / BW >= f0 / 30 kHz`
- **Regla de acople:** `cp(f) = 1 / (2*pi*f*Zcp)` con `Zcp ~ 10.2 kOhm`
  (comprobacion: 280 fF @ 55.89 MHz y 155 fF @ 100.00 MHz — ambos verificados)
- **Estimacion de polarizacion:** `Itail(f) ~ 0.6526 mA * (100 MHz / f)^3.15`
  (ajuste empirico de 2 puntos — **verificalo co-sintonizando en simulacion**)
- Realce: `Q_enh = Q0 / (1 - gm*Rp/2)`, oscila en `gm*Rp/2 = 1`,
  con `gm = sqrt(2*Kp*(W/L)*Itail/2)`

### Metodo que funciono (siguelo en este orden)

1. Barrido AC de span completo para **localizar los modos reales** (no los calculados).
2. Re-medir el **umbral de oscilacion PARA CADA cp** (la perdida por acople lo sube);
   estacionarse 0.5–3 % por debajo.
3. Mapa 2D (cp x margen) -> escoger **maxima profundidad sujeta a BW <= 30 kHz**.
4. **Co-sintonizar todos los canales juntos** (punto fijo sobre los umbrales).
5. Retocar la C del tanque para la frecuencia exacta.
6. Auditar sensibilidad al error de polarizacion.

## 7. El X10 — advertencia importante

Tal como esta parametrizado (L = 30 nH, RS = 1.5 Ohm, Kp = 200 uA/V^2, Itail 170–190 uA)
**no produce notches medibles** (< 0.03 dB). Razon: `Q0 = w*L/RS` es solo 6–25 y los pares
cross-coupled a esa corriente casi no compensan.

Ademas **las etiquetas de comentario del `.asc` original estan equivocadas**: el bloque
rotulado "50MHZ" en realidad lleva `c1 = 21.108 pF`, que resuena en **200 MHz**, no en 50.
No te guies por esos rotulos.

Su escalera `C1...C10` es exactamente un plan de 50 a 200 MHz en pasos de 16.67 MHz.
Los valores rediseniados (con L = 100 nH) estan en `LC_design_values.xlsx` / `.pdf`
en la raiz de la carpeta del proyecto en el Drive.

## 8. Los transistores (pendiente clave)

Ahora mismo todo usa `NMOSGEN`, un NMOS generico nivel-1 (el modelo por defecto tipo
LTspice). Juan va a fabricar **TFT de IGZO** en el INRF de UCI y aun **no tiene el modelo
extraido**.

Cuando lo tenga:
1. Llenar `models/tft_igzo_template.lib` con los parametros extraidos.
2. En `models/nmosgen_test1.lib`: comentar la linea `.model NMOSGEN ...` y descomentar
   el `.include tft_igzo_template.lib`.
3. En el esquematico/netlist: cambiar `NMOSGEN` por el nombre del modelo TFT y ajustar
   `w=` / `l=` a la geometria real.

Nada mas cambia: mismos bancos de prueba, mismas metricas. **Ojo:** con la movilidad tipica
de IGZO (5–15 cm2/Vs, mucho menor que silicio) el `gm` disponible sera bastante menor,
asi que **habra que re-hacer todo el paso 2–4 del metodo** (los umbrales y las corrientes
cambiaran mucho). Es de esperar que se necesiten W/L grandes o mas corriente.

## 9. Convenciones al trabajar aqui

- **Idioma:** Juan escribe en espanol; los entregables tecnicos (figuras, tablas, papers)
  van **en ingles**, formato publicacion.
- **Nunca sobreescribas** los `.asc` originales de LTspice: crea archivos nuevos.
- **Verifica siempre en lazo cerrado**: si generas un esquematico, vuelve a netlistearlo
  y simularlo antes de afirmar que funciona.
- Al reportar un notch, da SIEMPRE los cuatro numeros: **f0, profundidad, BW-3dB y Q_L**,
  e indica si el barrido fue span completo (aparente) o zoom (real).
- Si una profundidad sale <= 3 dB, di explicitamente que la Q no es confiable.

## 10. Ruta de trabajo

Hecho: punto de diseno de 2 canales verificado (A 55.89 / B 100.00 MHz), flujo abierto
xschem+ngspice funcionando, tablas L/C para los 10 canales. Se demostro que la topologia
PUEDE dar Q_L > 1667. Falta demostrar que puede hacerlo de forma robusta, escalable,
dentro del presupuesto de potencia y con dispositivos reales.

| # | Fase | Pregunta que responde | Esfuerzo | Importancia |
|---|---|---|---|---|
| 1 | **Escalado a N canales** | Hasta cuantos canales aguanta el retorno compartido | bajo | alta |
| 2 | **Retorno separado por canal** | Elimina la interaccion? A que costo de area? | medio | alta |
| 3 | **Lazo de AGC** | Se puede mantener el punto de operacion sin lazo abierto? | alto | **critica** |
| 4 | **Presupuesto de potencia** | Se puede llegar a 100 uW/canal? (hoy: 3.5 mW/canal) | medio-alto | alta |
| 5 | **Modelo TFT IGZO** | Puede un TFT dar el gm necesario en 150x150 um? | alto | **critica** |
| 6 | **Inductores en pelicula** | Que Q0 real se logra a 50-200 MHz? (se asumio 31) | medio | alta |
| 7 | **Footprint / layout** | Cabe un canal en 150x150 um? | medio | alta |
| 8 | **Validacion experimental** | PCB discreto primero, microfabricado despues | alto | — |

### Orden recomendado

**Ahora:** fases 1 y 2 — son baratas (la infraestructura ya existe) y la 2 puede
simplificar todo lo demas.

**En paralelo y pronto:** dos estimaciones baratas que **pueden invalidar supuestos**:
- *Peor caso de la fase 5:* barrer `Kp` hacia abajo (de 1m a 10u) y ver donde deja de
  cumplirse la spec. Eso da un **requisito de movilidad minima** que orienta la
  fabricacion, antes de fabricar nada.
- *Fase 6:* estimar Q0 de un inductor en pelicula delgada realista (probablemente < 10,
  contra 31 asumido) y ver que le hace al margen de estabilidad.

**Despues:** fase 3 (AGC), que es el mayor riesgo de viabilidad y la que mas trabajo lleva.

**Principio:** las fases que pueden matar el proyecto (3, 5, 6) deben atacarse con
estimaciones baratas lo antes posible, aunque su version completa venga despues.
No dejar los riesgos existenciales para el final.

### Riesgos principales

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| El AGC no alcanza la precision necesaria (+-0.25 %) | bloqueante | fase 3 temprano; revisar literatura |
| El IGZO no da suficiente gm (movilidad 5-15 cm2/Vs) | bloqueante | estimacion de peor caso antes de fabricar |
| Q0 de inductores en pelicula muy bajo | alto | fase 6 antes de comprometer topologia |
| El canal no cabe en 150x150 um | alto | fase 7 en paralelo, no al final |
| Potencia 35x sobre presupuesto | medio | duty-cycling + redimensionado |

> La version completa de esta ruta, con criterios de "listo" por fase, esta en el
> proyecto de claude.ai: `claude/Ruta_de_trabajo.md`.
