"""Shared ngspice driver for the OPAM / OPAM2 sizing search.

Renders a flat testbench around one of the parameterised cores, runs
ngspice in batch, and turns the operating point, the AC sweep and the DC
sweep into a single scored result.

The IGZO models are DC-only (SPICE level 1), so the gain reported here is the
DC gain: the AC sweep starts at 0.1 Hz and the value is read in the flat
region.  Nothing above that corner is validated silicon.
"""

import os
import re
import subprocess
import tempfile

NGSPICE = "/foss/tools/bin/ngspice"
PDK = "/foss/designs/TFT-MMM-LAB-PDK/libs.tech/ngspice"
HERE = os.path.dirname(os.path.abspath(__file__))

# Vto per corner.  The wrapper ties bulk to source, so there is no body
# effect and the threshold is exactly Vto.
VTO = {"best": 0.09, "tt": -0.26, "all": -0.53, "short": -1.32}

HEADER = """* auto-generated sizing run - see tb_common.py
.include {pdk}/design.ngspice
.lib {pdk}/igzo_mmm_lab.ngspice {corner}
.include "{here}/{core}"

.param vdd = {vdd}
.param vcm = {vcm}
{extra}
{sizing}

VDD VDD 0 DC 'vdd'
VCM cm  0 DC 'vcm'
VD  d   0 DC 0 AC 1
EIP INP cm d 0 0.5
EIN INN cm d 0 -0.5

{instance}

.control
set filetype=ascii
op
echo "@OP"
print {nodes}
print i(VDD)
echo "@DEV"
show m : vgs vds id gm gds
echo "@AC"
ac dec 20 0.1 1e9
meas ac av_db MAX vdb(OUT) from=0.1 to=1
meas ac av_max MAX vdb(OUT)
meas ac f_at_max WHEN vdb(OUT)=av_max
meas ac f3db WHEN vdb(OUT)='av_max-3' FALL=1
meas ac funity WHEN vdb(OUT)=0 FALL=1
* phase margin, measured against the DC phase so it means the same thing for an
* inverting and a non-inverting amplifier
let phase = 180/PI * cph(v(OUT))
meas ac ph_dc FIND phase AT=0.1
meas ac ph_u  FIND phase WHEN vdb(OUT)=0 FALL=1
let pmv = 180 + (ph_u - ph_dc)
echo PHASEMARGIN $&pmv
echo "@STAGE"
{stages}
echo "@DC"
dc VD -2 2 0.05
meas dc out_max MAX v(OUT)
meas dc out_min MIN v(OUT)
.endc
.end
"""


def build_netlist(core, instance, nodes, sizing, vdd, vcm, corner, extra=None,
                  stages=()):
    """`sizing` is in microns; `extra` holds plain-unit params such as a bias voltage."""
    lines = "\n".join(
        ".param {} = {:.6g}u".format(k, v) for k, v in sorted(sizing.items())
    )
    extra_lines = "\n".join(
        ".param {} = {:.6g}".format(k, v) for k, v in sorted((extra or {}).items())
    )
    stage_lines = "\n".join(
        "meas ac %s MAX vdb(%s) from=0.1 to=1e6" % (name, node)
        for name, node in stages)
    return HEADER.format(
        pdk=PDK, here=HERE, core=core, corner=corner, vdd=vdd, vcm=vcm,
        sizing=lines, extra=extra_lines, instance=instance, stages=stage_lines,
        nodes=" ".join("v(%s)" % n for n in nodes),
    )


DEV_KEYS = ("vgs", "vds", "id", "gm", "gds")


def _parse_devices(text):
    """Parse the `show m` tables into {device: {key: value}}.

    ngspice prints vgs and vds against the terminals as they were DECLARED.
    A device wired with drain and source swapped therefore reports a negative
    vds; the true source is then the terminal called `d`.  Convert to the
    physical orientation here so the saturation check does not depend on how
    the schematic happened to draw the device.
    """
    devices = {}
    block = None
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "device":
            block = parts[1:]
            for name in block:
                devices.setdefault(name, {})
            continue
        if block and parts[0] in DEV_KEYS and len(parts) == len(block) + 1:
            for name, raw in zip(block, parts[1:]):
                try:
                    devices[name][parts[0]] = float(raw)
                except ValueError:
                    devices[name][parts[0]] = float("nan")
    for d in devices.values():
        vgs, vds = d.get("vgs", 0.0), d.get("vds", 0.0)
        if vds < 0:                      # reverse-wired: swap the roles
            d["vgs_t"], d["vds_t"] = vgs - vds, -vds
        else:
            d["vgs_t"], d["vds_t"] = vgs, vds
        d["id_t"] = abs(d.get("id", 0.0))
    return devices


_NUM = r"[-+0-9.eE]+"


def run(netlist, cwd=HERE):
    with tempfile.NamedTemporaryFile("w", suffix=".spice", dir="/tmp", delete=False) as fh:
        fh.write(netlist)
        path = fh.name
    try:
        out = subprocess.run(
            [NGSPICE, "-b", path], capture_output=True, text=True,
            timeout=60, cwd=cwd,
        ).stdout
    except subprocess.TimeoutExpired:
        return None
    finally:
        os.unlink(path)

    res = {"raw": out, "nodes": {}, "meas": {}}
    for m in re.finditer(r"^v\((\w+(?:\.\w+)*)\)\s*=\s*(%s)" % _NUM, out, re.M):
        res["nodes"][m.group(1)] = float(m.group(2))
    m = re.search(r"PHASEMARGIN\s+(%s)" % _NUM, out)
    res["pm"] = float(m.group(1)) if m else float("nan")
    m = re.search(r"^i\(vdd\)\s*=\s*(%s)" % _NUM, out, re.M)
    res["idd"] = abs(float(m.group(1))) if m else float("nan")
    for m in re.finditer(
            r"^(av_db|av_max|f_at_max|f3db|funity|out_max|out_min|st_\w+)\s*=\s*(%s)"
            % _NUM, out, re.M):
        res["meas"][m.group(1)] = float(m.group(2))
    res["dev"] = _parse_devices(out)
    return res


TRAN_TB = """* transient swing check - see tb_common.py
.include {pdk}/design.ngspice
.lib {pdk}/igzo_mmm_lab.ngspice {corner}
.include "{here}/{core}"

.param vdd = {vdd}
.param vcm = {vcm}
{extra}
{sizing}

VDD VDD 0 DC 'vdd'
VCM cm  0 DC 'vcm'
VD  d   0 DC 0 SIN(0 {amp} {freq})
EIP INP cm d 0 0.5
EIN INN cm d 0 -0.5

{instance}

.control
tran {step} {stop} {skip}
meas tran vo_max MAX v(OUT) from={skip} to={stop}
meas tran vo_min MIN v(OUT) from={skip} to={stop}
.endc
.end
"""


def transient_swing(core, instance, sizing, vdd, vcm, corner, freq, amp,
                    extra=None, cycles=6, settle=20):
    """Drive a sine in band and report the peak-to-peak output.

    The bootstrap load is a current source only above the corner set by C1/C2,
    so this amplifier's swing cannot be read off a DC sweep: it has to be
    measured with the loop actually running at a frequency where the
    capacitor is doing its job.
    """
    period = 1.0 / freq
    lines = "\n".join(".param {} = {:.6g}u".format(k, v)
                      for k, v in sorted(sizing.items()))
    extra_lines = "\n".join(".param {} = {:.6g}".format(k, v)
                            for k, v in sorted((extra or {}).items()))
    net = TRAN_TB.format(
        pdk=PDK, here=HERE, core=core, corner=corner, vdd=vdd, vcm=vcm,
        sizing=lines, extra=extra_lines, instance=instance,
        amp=amp, freq=freq, step=period / 200, skip=settle * period,
        stop=(settle + cycles) * period,
    )
    res = run(net)
    if not res:
        return None
    for m in re.finditer(r"^(vo_max|vo_min)\s*=\s*(%s)" % _NUM, res["raw"], re.M):
        res["meas"][m.group(1)] = float(m.group(2))
    if "vo_max" in res["meas"] and "vo_min" in res["meas"]:
        return res["meas"]["vo_max"] - res["meas"]["vo_min"]
    return None
