# PDK-TFT-MMM-LAB — documents

The generated documents about the IGZO TFT PDK. **Only PDFs live here**; the
scripts that produce them, the figures they use and the measured data they read
are all inside the PDK repository, which is self-sufficient:

| | |
|---|---|
| Repository | `git@github.com:Juander28/TFT-MMM-LAB-PDK.git` |
| Working copy | `/foss/designs/TFT-MMM-LAB-PDK` (= `C:\TFT-MMM-LAB-PDK`) |
| Installed as | `$PDK_ROOT/TFT-MMM-LAB-PDK`, with `PDK_ROOT=~/pdks` |
| Activate with | `use-pdk TFT-MMM-LAB-PDK` |
| This folder, from the designs mount | `/foss/designs/Documents/PDK-TFT-MMM-LAB` |

PDFs are deliberately not tracked in git — they are output, and the repository
carries what they are made from.

---

## The five documents

**Cells and tools** — `..._cells_and_tools_en.pdf` / `..._celdas_y_herramientas_es.pdf`
What the PDK contains and how it looks in klayout, xschem, magic and ngspice.
Start here. Ten pages, with how to activate the PDK and how to switch between
it and the other open-source PDKs.

**Cell SOP** — `..._cell_sop_en.pdf` / `..._sop_de_celdas_es.pdf`
Every parameter of every cell: what it does, and a column saying where its
default came from — measured, read off the fabricated chip, assumed, or your
choice. Seven pages. Read it before sizing anything.

**Model vs measurement** — `..._model_vs_measurement_en.pdf` / `..._modelo_vs_medicion_es.pdf`
The evidence behind the model cards: simulated curves over measured ones, the
extraction spread across 86 devices, contact resistance, the C–V that gives
Cox — and a list of what to measure next and what each measurement would
settle. Six pages, every plot generated from the raw data.

**Overview deck** — `..._overview_en.pdf` / `..._presentacion_es.pdf`
Eleven slides, 16:9: what was built, the cells and every parameter with an
arrow pointing at it, the model against the measured curves, and what is
measured versus what is assumed. The parameter panels are drawn from the live
PCell declarations, so they cannot describe a parameter the cells do not have.

**Capabilities and limits** — `..._capabilities_and_limits_en.pdf` / `..._capacidades_y_limites_es.pdf`
What can honestly be designed with this technology and what cannot, sorted into
three boxes: solid, coarse, not supported. Five pages. It has the numbers the
other documents stop short of — fT = 1.2 MHz at L = 10 µm and 1.9 MHz at
L = 5 µm, the 48 % of transconductance the contacts take at W = 100 µm, the
ceiling in a single table — and every one of them is computed by running
ngspice against the PDK's own models while the document is built, so it cannot
drift away from the models it describes. Read it before promising anyone a
bandwidth.

Same content in both languages; each is built from one script with two string
tables, so they cannot drift apart in structure.

---

## Rebuilding them

```bash
use-pdk TFT-MMM-LAB-PDK
cd /foss/designs/TFT-MMM-LAB-PDK/docs/pdf

./make_figures.sh              # real klayout, xschem and magic windows
python3 make_pdf.py            # the guide, both languages
python3 make_sop.py            # the SOP
python3 make_model_report.py   # the model report - runs ngspice as it goes
python3 make_slides.py         # the overview deck - also runs ngspice
python3 make_capabilities.py   # capabilities and limits - runs ngspice too
```

They write here by default; pass a directory to send them somewhere else, and a
language (`en` or `es`) to build just one.

`make_figures.sh` opens a private X server on a free display so nothing appears
on your desktop. Magic paints its window lazily, so a capture can come out
black; the script checks each one, retries three times, and never overwrites a
good figure with a bad one. If a magic figure is blank, run it again.

The model report reads `measurements/` in the repository. That data is not in
git — see `measurements/README.md` there — but it is present on this machine.
