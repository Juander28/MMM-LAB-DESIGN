"""Second, finer pass for OPAM2 starting from the coarse optimum."""
import os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import optimize as O

BEST = dict(l_cmd=200, l_cms=200, l_d2s=200, l_dl=200, l_in=25, l_od=140,
            l_ol=200, l_sf=800, l_sfl=100, l_tail=200, w_cmd=140, w_cms=200,
            w_d2s=200, w_dl=50, w_in=3200, w_od=1100, w_ol=140, w_sf=50,
            w_sfl=200, w_tail=200)

log, pool = [], ThreadPoolExecutor(O.WORKERS)
sz = dict(BEST)
for factors in (O.FACTORS, O.FINE, O.FINE):
    sz, val, bad, info = O.coordinate_descent(O.OPAM2, sz, 8, log, pool, factors=factors)
    print("pass -> Av=%.2f dB (worst corner)  viol=%s" % (info["av_db"], bad or "none"))
    sys.stdout.flush()
print("\nfinal sizing (um):")
for k in sorted(sz):
    print("  %-8s %6.0f" % (k, sz[k]))
print("vout=%.2f swing=%.2f power=%.0f uW" % (info["vout"], info["swing"], info["power"] * 1e6))
