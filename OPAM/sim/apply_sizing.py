#!/usr/bin/env python3
"""Write a sizing back into the xschem schematics, and fix the wiring.

Two edits per device, both purely textual:

1.  W, L and m.  The optimiser works with one effective width per device, so
    every instance is written with m=1 and its full width; two devices of
    width W in parallel are exactly one device of width 2W in this wrapper.

2.  Source/drain orientation.  Kept, but no longer load-bearing: the PDK's
    junctions are inert since commit 67779ed and d/s now permute freely.  It
    used to matter, because the wrapper ties the intrinsic bulk to the `s` pin
    and a device drawn with `s` on the high side forward-biased its bulk-drain
    junction.  The mechanism is still worth knowing: swapping D and S in
    xschem does NOT need the wires to move, because the symbol's three pin
    boxes land on the same three coordinates for the flag pairs
    (rot,flip) = (0,0)<->(2,1) and (2,0)<->(0,1), with only D and S exchanged.
    So the swap is a change of the two instance flags and nothing else.
"""

import os
import re
import sys

SWAP = {("0", "0"): ("2", "1"), ("2", "1"): ("0", "0"),
        ("2", "0"): ("0", "1"), ("0", "1"): ("2", "0")}

INST = re.compile(
    r"^(C \{symbols/tft_igzo\.sym\} (-?\d+) (-?\d+) )(\d) (\d)( \{name=(\w+)\n)"
    r"(.*?)(\n\}\n)", re.S | re.M)


def patch(path, sizing, groups, swap_devices, out_path=None):
    """Patch `path`, reading from `path + ".orig"` when that exists.

    The orientation fix toggles two flags, so applying it twice undoes it.
    Deriving every run from the untouched original makes the whole thing
    idempotent: run it as often as you like and the result is the same.
    """
    # .base carries the structural fixes and is preferred; .orig is the
    # untouched original, used only where there is no structural work
    for suffix in (".base", ".orig"):
        if os.path.exists(path + suffix):
            src = path + suffix
            break
    else:
        src = path
    text = open(src).read()
    seen = set()

    def repl(m):
        head, _, _, rot, flip, tail, name, body, close = m.groups()
        seen.add(name)
        if name in swap_devices:
            rot, flip = SWAP[(rot, flip)]
        if name in groups:
            wkey, lkey = groups[name]
            body = re.sub(r"^W=\S+$", "W=%gu" % sizing[wkey], body, flags=re.M)
            body = re.sub(r"^L=\S+$", "L=%gu" % sizing[lkey], body, flags=re.M)
            # widths are absolute, so the multiplier always goes back to 1
            body = re.sub(r"^m=\S+$", "m=1", body, flags=re.M)
        return head + rot + " " + flip + tail + body + close

    new = INST.sub(repl, text)
    missing = set(groups) - seen
    if missing:
        raise SystemExit("devices not found in %s: %s" % (path, sorted(missing)))
    open(out_path or path, "w").write(new)
    return sorted(seen)


# ------------------------------------------------------------------ OPAM2 --
OPAM2_GROUPS = {
    "M4": ("w_in", "l_in"),   "M3": ("w_in", "l_in"),
    "M6": ("w_dl", "l_dl"),   "M7": ("w_dl", "l_dl"),
    "M8": ("w_tail", "l_tail"),
    "M10": ("w_cms", "l_cms"), "M1": ("w_cms", "l_cms"),
    "M2": ("w_cmd", "l_cmd"),
    "M11": ("w_sf", "l_sf"),  "M5": ("w_sf", "l_sf"),
    "M17": ("w_sfl", "l_sfl"),
    "M9": ("w_d2s", "l_d2s"),
    "M12": ("w_od", "l_od"),
    "M13": ("w_ol", "l_ol"),
}
OPAM2_SWAP = {"M4", "M6", "M10", "M2", "M11", "M5", "M9", "M12", "M13"}

# ------------------------------------------------------------------- OPAM --
OPAM_GROUPS = {
    "M2": ("w_in", "l_in"),   "M5": ("w_in", "l_in"),
    "M3": ("w_cc", "l_cc"),   "M4": ("w_cc", "l_cc"),
    "M6": ("w_dl", "l_dl"),   "M7": ("w_dl", "l_dl"),
    "M8": ("w_tail", "l_tail"),
    "M11": ("w_t2", "l_t2"),  "M17": ("w_t2", "l_t2"),
    "M12": ("w_g2", "l_g2"),  "M18": ("w_g2", "l_g2"),
    "M13": ("w_bl", "l_bl"),  "M19": ("w_bl", "l_bl"),
    "M14": ("w_bf", "l_bf"),  "M20": ("w_bf", "l_bf"),
    "M10": ("w_of", "l_of"),  "M16": ("w_of", "l_of"),
    "M9": ("w_od", "l_od"),   "M15": ("w_od", "l_od"),
}
OPAM_SWAP = {"M5", "M4", "M6", "M9", "M10", "M11", "M12", "M13",
             "M14", "M15", "M16", "M17", "M18", "M19", "M20"}
