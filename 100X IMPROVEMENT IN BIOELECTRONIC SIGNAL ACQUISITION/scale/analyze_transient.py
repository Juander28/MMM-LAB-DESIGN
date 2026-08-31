#!/usr/bin/env python3
"""
Recover the frequency response from the noise-driven time record.

Two independent estimators, because agreeing is the point:
  H1 = FFT(out)/FFT(in)          full resolution, lightly smoothed
  H2 = Pxy/Pxx  (Welch)          least-squares estimate, averaged

If the notches, depths and bandwidths from the time record land on the ones the
AC sweep predicted, the AC result is confirmed by a method that never used .ac.
"""

import argparse
import os

import numpy as np
from scipy.signal import csd, welch, find_peaks
from scipy.ndimage import median_filter


def load(path, skip_us=35.0):
    d = np.loadtxt(path)
    # wrdata writes (t, vin, t, vout) - drop the repeated time column
    t = d[:, 0]
    vin = d[:, 1]
    vout = d[:, 3] if d.shape[1] > 3 else d[:, 2]
    m = t >= skip_us * 1e-6
    return t[m], vin[m], vout[m]


def h_direct(t, x, y, smooth=9):
    n = len(t)
    dt = float(np.median(np.diff(t)))
    win = np.hanning(n)
    X = np.fft.rfft(x * win)
    Y = np.fft.rfft(y * win)
    f = np.fft.rfftfreq(n, dt)
    H = np.abs(Y) / np.maximum(np.abs(X), np.abs(X).max() * 1e-6)
    db = 20 * np.log10(np.maximum(H, 1e-12))
    if smooth > 1:
        db = median_filter(db, size=smooth)
    return f, db


def h_welch(t, x, y, nperseg):
    dt = float(np.median(np.diff(t)))
    fs = 1.0 / dt
    f, Pxx = welch(x, fs, nperseg=nperseg)
    _, Pxy = csd(x, y, fs, nperseg=nperseg)
    H = np.abs(Pxy) / np.maximum(Pxx, Pxx.max() * 1e-12)
    return f, 20 * np.log10(np.maximum(H, 1e-12))


def notches(f, db, fmin=40e6, fmax=210e6, prom=1.0):
    m = (f >= fmin) & (f <= fmax)
    fw, dw = f[m], db[m]
    idx, _ = find_peaks(-dw, prominence=prom)
    out = []
    w = max(20, len(fw) // 60)
    for i in idx:
        lo, hi = max(0, i - w), min(len(fw), i + w + 1)
        ring = np.r_[dw[lo:max(lo, i - w // 5)], dw[min(hi, i + w // 5):hi]]
        if ring.size < 8:
            continue
        base = float(np.median(ring))
        depth = base - dw[i]
        thr = base - 3.0
        j = i
        while j > 0 and dw[j] < thr:
            j -= 1
        k = i
        while k < len(fw) - 1 and dw[k] < thr:
            k += 1
        bw = (fw[k] - fw[j]) if k > j else np.nan
        out.append((fw[i], depth, bw))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("txt")
    ap.add_argument("--skip", type=float, default=35.0, help="us to discard")
    ap.add_argument("--nperseg", type=int, default=262144)
    a = ap.parse_args()

    t, x, y = load(a.txt, a.skip)
    dt = float(np.median(np.diff(t)))
    print(f"record: {len(t)} samples, dt = {dt*1e12:.1f} ps, "
          f"fs = {1/dt/1e9:.2f} GHz, T = {(t[-1]-t[0])*1e6:.1f} us "
          f"(after discarding {a.skip:g} us)")
    print(f"frequency resolution: direct {1/(t[-1]-t[0])/1e3:.2f} kHz, "
          f"Welch {1/dt/a.nperseg/1e3:.2f} kHz")
    print(f"input RMS {np.std(x):.4g} V, output RMS {np.std(y):.4g} V")

    f1, db1 = h_direct(t, x, y)
    f2, db2 = h_welch(t, x, y, min(a.nperseg, len(t) // 2))

    for name, f, db, prom in (("DIRECT  FFT(out)/FFT(in)", f1, db1, 1.5),
                              ("WELCH   Pxy/Pxx", f2, db2, 1.0)):
        ns = notches(f, db, prom=prom)
        print(f"\n{name}: {len(ns)} notches in 40-210 MHz")
        print(f"{'#':>3} {'f0[MHz]':>10} {'depth[dB]':>10} {'BW[kHz]':>10} {'Q_L':>8}")
        for i, (f0, dep, bw) in enumerate(sorted(ns), 1):
            q = f0 / bw if bw == bw and bw > 0 else float("nan")
            print(f"{i:3d} {f0/1e6:10.3f} {dep:10.2f} "
                  f"{bw/1e3 if bw == bw else float('nan'):10.2f} {q:8.0f}")

    np.save(os.path.splitext(a.txt)[0] + "_psd.npy",
            np.array([f1, db1], dtype=object), allow_pickle=True)


if __name__ == "__main__":
    main()
