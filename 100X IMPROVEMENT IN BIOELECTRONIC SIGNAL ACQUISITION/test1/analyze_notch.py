#!/usr/bin/env python3
"""Analiza un CSV de ngspice (wrdata) y reporta cada notch:
f0, profundidad, BW(-3dB desde la linea base) y Q_L.

Uso:  python3 analyze_notch.py test1_ac.csv
El archivo debe venir de:  wrdata archivo.csv vector1 [vector2 ...]
(formato: freq re im por cada vector, columnas concatenadas)
"""
import sys
import numpy as np

def notch_report(f, mag_db, label, min_prom=1.0):
    try:
        from scipy.signal import find_peaks
        idx, props = find_peaks(-mag_db, prominence=min_prom)
    except ImportError:                       # fallback sin scipy
        idx = [int(np.argmin(mag_db))]
        props = {"prominences": [99.0]}
    if len(idx) == 0:
        print(f"  {label}: sin notches con prominencia >= {min_prom} dB")
        return
    for k, i in enumerate(idx):
        f0 = f[i]
        # linea base local: mediana lejos del notch
        w = max(10, len(f) // 20)
        far = np.abs(f - f0) > 20 * (f[1] - f[0]) * w / 10
        base = np.median(mag_db[far]) if far.sum() > 10 else np.median(
            np.r_[mag_db[:w], mag_db[-w:]])
        depth = base - mag_db[i]
        thr = base - 3.0
        fL = fR = np.nan
        j = i
        while j > 0 and mag_db[j] < thr:
            j -= 1
        if j < i:
            fL = np.interp(thr, [mag_db[j], mag_db[j + 1]], [f[j], f[j + 1]])
        j = i
        while j < len(f) - 1 and mag_db[j] < thr:
            j += 1
        if j > i:
            fR = np.interp(thr, [mag_db[j], mag_db[j - 1]], [f[j], f[j - 1]])
        bw = fR - fL if np.isfinite(fL) and np.isfinite(fR) else np.nan
        q = f0 / bw if np.isfinite(bw) and bw > 0 else np.nan
        print(f"  {label} notch {k+1}: f0={f0/1e6:10.4f} MHz  "
              f"depth={depth:6.2f} dB  BW={bw/1e3 if np.isfinite(bw) else float('nan'):8.2f} kHz"
              f"  Q_L={q if np.isfinite(q) else float('nan'):9.0f}")

def main(path):
    arr = np.loadtxt(path)
    nvec = arr.shape[1] // 3
    f = arr[:, 0]
    print(f"{path}: {len(f)} puntos, {f[0]/1e6:.2f}-{f[-1]/1e6:.2f} MHz, {nvec} vector(es)")
    for k in range(nvec):
        v = arr[:, 3 * k + 1] + 1j * arr[:, 3 * k + 2]
        m = 20 * np.log10(np.maximum(np.abs(v), 1e-30))
        notch_report(f, m, f"vector{k+1}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "test1_ac.csv")
