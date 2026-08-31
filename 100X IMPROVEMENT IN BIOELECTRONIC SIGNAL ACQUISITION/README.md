# 100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION

Xschem + ngspice (flujo abierto, listo para tu Docker)

Paquete generado y **verificado en lazo cerrado** el 2026-08-18: cada esquemático
fue netlistado con Xschem (headless) y simulado con ngspice-42; los resultados
reproducen el punto de diseño validado en LTspice/ngspice de TEST1.

```
100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION/
├── README.md                      ← este archivo
├── CLAUDE.md                      ← contexto completo del proyecto (lo lee Claude Code solo)
├── USAR_CLAUDE_CODE.md            ← guía para correr Claude Code DENTRO del contenedor
├── instalar_claude_code.sh        ← instalador (córrelo dentro del contenedor)
├── test1/
│   ├── cross_coupled_test1.sch    ← esquemático Xschem (punto de diseño A/B)
│   ├── cross_coupled_test1.spice  ← netlist YA generado (por si no quieres abrir xschem)
│   ├── run_test1.sh               ← netlist + simula + analiza en un paso
│   ├── analyze_notch.py           ← f0, profundidad, BW(−3dB), Q_L de cada notch
│   └── models/
│       ├── nmosgen_test1.lib      ← modelo genérico nivel-1 (el de LTspice, Kp=1m)
│       └── tft_igzo_template.lib  ← PLANTILLA para el modelo de tus TFT IGZO
└── x10/
    ├── cross_coupled_x10.sch      ← tu X10: 4 de 10 canales poblados (plan 50–200 MHz)
    ├── cross_coupled_x10.spice
    ├── run_x10.sh
    ├── analyze_notch.py
    └── models/nmosgen_x10.lib     ← modelo del X10 original (Kp=200µ)
```

## Dónde vive esto y cómo se corre

**Un solo contenedor para todo:** `iic-osic-tools_chipathon_xvnc` (imagen
chipathon26), el que ya está corriendo. No hace falta cambiar puertos ni crear
contenedores nuevos.

Esta carpeta vive en **`"C:\Users\juand\Documents\GitHub\sscs-2026-zotnetic\designs\100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION"`** en Windows, y
el contenedor la monta como **`/foss/designs/100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION`**. Editas en Windows,
se ve adentro al instante y al revés — nada de `docker cp`.

    docker exec -it iic-osic-tools_chipathon_xvnc bash
    cd "/foss/designs/100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION/test1"
    ./run_test1.sh

Requisitos dentro del contenedor: xschem, ngspice y python3 con numpy
(scipy opcional) — todos vienen en las imágenes IIC-OSIC-TOOLS/Chipathon.

Copia de respaldo de todo esto: también está en el Drive del proyecto, en
`SIMULATION/..` de este proyecto.

### Dos avisos sobre este repo

**1. Es un repo de git (tapeout zotnetic 2026).** Estos archivos van a aparecer en
`git status`. Decide tú si los commiteas o los añades a `.gitignore` — no toqué
nada de tu configuración.

**2. Tienes tu propio `xschemrc`** en `designs/.config/.xschem/`, configurado para
tu PDK (GF180). Si al correr `run_test1.sh` el paso de xschem falla por rutas de
librerías, **no es problema**: el netlist `.spice` ya viene generado y verificado.
El script cae solo a ese respaldo, o córrelo a mano:

    ngspice -b cross_coupled_test1.spice && python3 analyze_notch.py test1_ac.csv

Estos esquemáticos usan los símbolos genéricos de xschem (`devices/*.sym`), no los
del PDK, así que son independientes de tu configuración de GF180.

## Flujo de trabajo

1. **GUI:** `xschem cross_coupled_test1.sch` — el esquemático está en estilo
   "etiquetas": cada pin lleva su nombre de red (actp, actm, VDD, 0…). Es
   eléctricamente exacto; puedes reacomodar componentes a gusto sin romper nada
   mientras conserves las etiquetas. Netlist: menú *Netlist* o `run_test1.sh`.
2. **Span completo:** el bloque PARAMS trae `.ac lin 50000 35Meg 210Meg`. El
   span completo **subestima la profundidad** del notch (paso 3.5 kHz vs BW de
   14–23 kHz); para métricas reales comenta esa línea y descomenta uno de los
   zooms (canal A o canal B).
3. **Métricas:** `python3 analyze_notch.py test1_ac.csv` → f0, profundidad,
   BW₋₃dB y Q_L de cada notch (mismo criterio que tu notch_quality_analyzer).

## Punto de diseño verificado (test1)

| Canal | f0 | Profundidad | BW₋₃dB | Q_L | cp | Itail |
|---|---|---|---|---|---|---|
| A | 55.890 MHz | 35.9 dB | 23.2 kHz | 2413 | cpA=280 fF | ItailA=4.07509 mA (margen 1.55%) |
| B | 100.002 MHz | 39.7 dB | 13.9 kHz | 7217 | cpB=155 fF | ItailB=0.65260 mA (margen 0.90%) |

Sensibilidad: ±0.25% en Itail conserva ≥17 dB; +1% en ItailB → oscila.

## X10 — advertencia

Tal como está (L=30 nH, RS=1.5 Ω, Kp=200 µ, Itail 170–190 µA) **no produce
notches medibles** (< 0.03 dB): Q₀ = ωL/RS ≈ 6–25 y el par cross-coupled a esa
corriente casi no compensa. Los valores corregidos por canal (C, cp, Itail para
L=100n/RS=1) están en `LC_design_values.xlsx` / `.pdf` en la carpeta raíz del
proyecto.

## Claude Code dentro del contenedor

En vez de dar acceso remoto a tu Docker, puedes correr un agente **adentro**, donde
tiene acceso directo a xschem y ngspice:

```bash
cd "/foss/designs/100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION"
bash instalar_claude_code.sh     # una sola vez
claude                            # lee CLAUDE.md automáticamente
```

`CLAUDE.md` lleva todo el contexto (punto de diseño verificado, los hallazgos clave,
las reglas de diseño, las trampas conocidas), así que no hay que explicarle nada.
Detalles en `USAR_CLAUDE_CODE.md`.

## Tus TFT (cuando tengas el modelo)

1. Edita `models/tft_igzo_template.lib` con los parámetros extraídos de tus
   dispositivos IGZO (plantilla comentada adentro).
2. En `models/nmosgen_test1.lib` comenta el `.model NMOSGEN…` y descomenta el
   `.include tft_igzo_template.lib`.
3. En el esquemático (o netlist) cambia `NMOSGEN` por el nombre de tu modelo y
   ajusta `w=`/`l=` a tu geometría real. Nada más cambia: mismos bancos de
   prueba, mismas métricas.
