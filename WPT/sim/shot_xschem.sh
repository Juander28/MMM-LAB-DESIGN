#!/usr/bin/env bash
#
# Photograph the two WPT schematics.
#
#     ./shot_xschem.sh
#
# The windows open on a private X server of our own, on a display number
# nobody else is using, and it is torn down at the end.  Two reasons, both
# learned in the PDK's make_figures.sh, which this follows: your VNC desktop
# stays untouched, and the screen is guaranteed empty - a stale window left
# over from an earlier run would otherwise sit on top of the one we mean to
# photograph.
set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WPT="$(cd "${HERE}/.." && pwd)"
FIG="${WPT}/figures"
mkdir -p "${FIG}"

export PDK_ROOT="${PDK_ROOT:-$HOME/pdks}"
export PDK="${PDK:-TFT-MMM-LAB-PDK}"
PDKPATH="${PDK_ROOT}/${PDK}"
[ -d "${PDKPATH}" ] || PDKPATH="/foss/designs/TFT-MMM-LAB-PDK"
[ -d "${PDKPATH}" ] || { echo "no PDK found" >&2; exit 1; }

DISP=""
for n in $(seq 90 99); do
    if [ ! -e "/tmp/.X11-unix/X${n}" ]; then DISP=":${n}"; break; fi
done
[ -n "${DISP}" ] || { echo "no free X display between :90 and :99" >&2; exit 1; }

echo "== private X server on ${DISP} =="
Xvfb "${DISP}" -screen 0 1900x1400x24 >/dev/null 2>&1 &
XVFB_PID=$!
sleep 3
export DISPLAY="${DISP}"

# The paths are BRACED for Tcl.  This directory is under "MMM-LAB DESIGN",
# and an unbraced `set netlist_dir /foss/designs/MMM-LAB DESIGN/WPT/sim` is a
# Tcl syntax error - too many arguments - which makes xschem abort the rcfile
# and then quietly fail to paint anything.  Third variant of the same trap in
# this project, after ngspice's wrdata and xschem's own `print png`.
cat > "${HERE}/.xschemrc_shot" <<XRC
source {${PDKPATH}/libs.tech/xschem/xschemrc}
set netlist_dir {${HERE}}
XRC

# The PNG is written to a path with NO SPACES and moved afterwards.  xschem's
# `print png` takes its filename from a Tcl command string and splits it on
# whitespace, and this project lives under "MMM-LAB DESIGN" - so the path lost
# everything after the space and the file was never written, silently.  Same
# trap as ngspice's wrdata.
TMPD="$(mktemp -d)"
trap 'kill ${XVFB_PID} 2>/dev/null || true; rm -f "${HERE}/.xschemrc_shot"; rm -rf "${TMPD}"' EXIT

for pair in "WPT.sch:wpt_pdk.png" "WPT_sim.sch:wpt_sim.png"; do
    src="${pair%%:*}"; png="${pair##*:}"
    [ -f "${WPT}/${src}" ] || { echo "  ! ${src} not there - generate it first"; continue; }
    # xschem exits non-zero after a successful batch export, hence the || true
    timeout 90 xschem --rcfile "${HERE}/.xschemrc_shot" \
        --tcl "after 2500 {xschem zoom_full; xschem print png ${TMPD}/${png}; exit}" \
        "${WPT}/${src}" >/dev/null 2>&1 || true
    [ -s "${TMPD}/${png}" ] && mv "${TMPD}/${png}" "${FIG}/${png}"
    if [ -s "${FIG}/${png}" ]; then
        echo "  wrote ${FIG}/${png}  ($(stat -c%s "${FIG}/${png}") bytes)"
    else
        echo "  ! ${png} came out empty - the window never painted.  Re-run."
    fi
done
