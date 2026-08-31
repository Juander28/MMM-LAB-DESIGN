"""Objective and constraint checking for the sizing search.

Maximise DC gain, but only among candidates that are actually usable:
every device in saturation, inside the model's validated range, output
sitting near mid-supply, a real output swing, and a power budget.
"""

import math

MIN_UM, STEP_UM = 10.0, 5.0

# The models are validated for VGS <= 6 V and VDS <= 10 V.  Outside that they
# extrapolate, so a candidate that leaves the box is not a design.
VGS_MAX, VDS_MAX = 6.0, 10.0
# Level 1 has no subthreshold region, so a device biased at a few tens of mV
# of overdrive is not being modelled, it is being extrapolated from a square
# law that stops there.  Anything below this is not a design decision.
VOV_MIN = 0.15
SWING_MIN = 2.0          # V, open-loop output swing we insist on
PM_MIN = 0.0             # deg; per design - 0 means the check is off
FOLLOW_TOL = 0.0         # V; per design - the output must be able to sit where
                         # the input common mode is, or the amplifier cannot be
                         # closed as a unity-gain buffer at all.  0 turns it off.
POWER_MAX = 900e-6       # W, the figure Zysset et al. report for their opamp


def snap(x):
    """Round a dimension onto the 5 um grid, floor at 10 um."""
    return max(MIN_UM, round(x / STEP_UM) * STEP_UM)


def check(res, vdd, vto, diode_devices=(), cutoff_devices=(), gain_key="av_db",
          swing_min=SWING_MIN, pm_min=PM_MIN, vcm=None,
          follow_tol=FOLLOW_TOL):
    """Return (violations, info).

    Every violation carries a normalised magnitude in `info["penalty"]` as
    well as a message.  A plain count is a staircase and the search stalls on
    it: with three or four constraints coupled through one bias point, no
    single-parameter move ever removes a whole violation, so nothing ever
    looks like progress.  A graded penalty gives the search something to walk
    down.
    """
    bad, info, pen = [], {}, 0.0

    def fail(msg, amount):
        bad.append(msg)
        return amount
    if res is None:
        info["penalty"] = 100.0
        return ["no result"], info

    dev = res["dev"]
    if not dev:
        info["penalty"] = 100.0
        return ["no operating point"], info

    for name, d in dev.items():
        short = name.split(".")[-2] if "." in name else name
        # A device the solver left inconsistent (current with no
        # transconductance) means the operating point did not converge.
        if d["id_t"] > 1e-9 and d.get("gm", 0.0) == 0.0:
            pen += fail("%s: inconsistent OP" % short, 1.0)
            continue
        if short in cutoff_devices:
            # held in cut-off on purpose (the bootstrap load's parallel device)
            continue
        vov = d["vgs_t"] - vto
        if vov < VOV_MIN:
            pen += fail("%s: vov=%.3f < %.2f" % (short, vov, VOV_MIN),
                        (VOV_MIN - vov) / VOV_MIN)
            continue
        if short not in diode_devices and d["vds_t"] < vov - 1e-3:
            pen += fail("%s: triode (vds=%.2f vov=%.2f)" % (short, d["vds_t"], vov),
                        (vov - d["vds_t"]) / vov)
        if d["vgs_t"] > VGS_MAX:
            pen += fail("%s: vgs=%.2f > %.1f" % (short, d["vgs_t"], VGS_MAX),
                        (d["vgs_t"] - VGS_MAX) / VGS_MAX)
        if d["vds_t"] > VDS_MAX:
            pen += fail("%s: vds=%.2f > %.1f" % (short, d["vds_t"], VDS_MAX),
                        (d["vds_t"] - VDS_MAX) / VDS_MAX)

    vout = res["nodes"].get("out", float("nan"))
    info["vout"] = vout
    if not (0.2 * vdd <= vout <= 0.8 * vdd):
        off = max(0.2 * vdd - vout, vout - 0.8 * vdd)
        pen += fail("vout=%.2f outside 20-80%% of VDD" % vout, off / vdd)

    if follow_tol and vcm is not None:
        # A buffer has to be able to output the voltage it is fed.  With the
        # output sitting at 4.7 V and the common mode at 1.8 V the two ranges
        # never meet, and the loop latches whatever the phase margin says.
        off = abs(vout - vcm)
        if off > follow_tol:
            pen += fail("output %.2f V cannot reach Vcm %.2f V" % (vout, vcm),
                        (off - follow_tol) / max(vcm, 1.0))

    swing = res["meas"].get("out_max", 0.0) - res["meas"].get("out_min", 0.0)
    info["swing"] = swing
    if swing_min and swing < swing_min:
        pen += fail("swing=%.2f V < %.1f V" % (swing, swing_min),
                    (swing_min - swing) / swing_min)

    power = res["idd"] * vdd
    info["power"] = power
    if not math.isfinite(power) or power > POWER_MAX:
        pen += fail("power=%.0f uW > %.0f uW" % (power * 1e6, POWER_MAX * 1e6),
                    10.0 if not math.isfinite(power)
                    else (power - POWER_MAX) / POWER_MAX)

    pm = res.get("pm", float("nan"))
    info["pm"] = pm
    if pm_min:
        # An amplifier that cannot be closed in a loop is a gain block, not an
        # opamp.  Both papers characterise the open loop, but Zysset's is used
        # as a unity-gain buffer, so the margin has to be a constraint and not
        # an afterthought.
        if not math.isfinite(pm):
            pen += fail("no phase margin measurement", 5.0)
        elif pm < pm_min:
            pen += fail("phase margin %.1f deg < %.0f" % (pm, pm_min),
                        (pm_min - pm) / 90.0)

    av = res["meas"].get(gain_key, float("-inf"))
    info["av_db"] = av
    if not math.isfinite(av):
        pen += fail("no gain measurement", 10.0)
    info["penalty"] = pen
    return bad, info


def objective(res, vdd, vto, diode_devices=(), cutoff_devices=(), gain_key="av_db",
              swing_min=SWING_MIN, pm_min=PM_MIN, vcm=None,
          follow_tol=FOLLOW_TOL):
    """Higher is better.  Infeasible candidates score below every feasible one."""
    bad, info = check(res, vdd, vto, diode_devices, cutoff_devices, gain_key,
                      swing_min, pm_min, vcm, follow_tol)
    av = info.get("av_db", float("-inf"))
    if not math.isfinite(av):
        av = -300.0
    if bad:
        return -1000.0 - info["penalty"] + av / 1000.0, bad, info
    return av, bad, info
