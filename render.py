#!/usr/bin/env python3
"""quantum-cinema gorsellestirme: olasilik evrimi GIF + spektrum PNG + RAM-max demo."""

import math
import os
import shutil
import struct
import subprocess
import sys
import time
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quantum import Devre, qft

RENK = np.array([[30, 40, 200], [40, 200, 90], [255, 210, 60], [230, 60, 40]], float)


def png_yaz(path, img):
    h, w, _ = img.shape
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += img[y].tobytes()

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b""))


def cubuklar(p_ust, ad):
    """En yuksek olasilikli 8 durumun cubuk grafigi (800x450)."""
    W, H = 800, 450
    img = np.full((H, W, 3), 12, dtype=float)
    k = len(p_ust)
    bw = int(W / (k + 1.5))
    maks = max(p_ust.max(), 1e-12)
    for i, p in enumerate(p_ust):
        h = int((p / maks) * (H - 90))
        x0 = int(bw * 0.75 + i * bw)
        c = RENK[min(int(i / k * 4), 3)]
        img[H - 60 - h:H - 60, x0:x0 + int(bw * 0.72)] = c
        img[H - 56:H - 50, x0:x0 + int(bw * 0.72)] = 40
    img[H - 40:H - 34, :] = 60
    return np.clip(img, 0, 255).astype(np.uint8)


def grover16():
    """Grover 16 kubut: 65536 urun icinde isaretliyi arar; olasilik evrimi GIF."""
    n, hedef = 16, 42424
    d = Devre(n)
    for q in range(n):
        d.h(q)
    iterasyon = int(math.pi / 4 * math.sqrt(2 ** n))       # ~200
    tmp = "renders/grover16.gif.frames"
    os.makedirs(tmp, exist_ok=True)
    frameno = 0
    for it in range(iterasyon):
        d.psi[hedef] *= -1                                  # oracle
        for q in range(n):
            d.h(q)
        d.psi[0] *= -1                                      # difuzyon
        for q in range(n):
            d.h(q)
        if it % max(1, iterasyon // 48) == 0 or it == iterasyon - 1:
            p = d.olasiliklar()
            ust8 = np.argsort(p)[::-1][:8]
            png_yaz(f"{tmp}/f{frameno:03d}.png", cubuklar(p[ust8], frameno))
            frameno += 1
    fps = 6
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
                    "-i", f"{tmp}/f%03d.png",
                    "-vf", "palettegen=max_colors=64", f"{tmp}/pal.png"], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
                    "-i", f"{tmp}/f%03d.png", "-i", f"{tmp}/pal.png",
                    "-lavfi", "paletteuse=dither=none", "-loop", "0",
                    "renders/grover16.gif"], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    p = d.olasiliklar()
    print(f"  grover16: {iterasyon} iterasyon, p(hedef) = {p[hedef]:.4f}")
    print("== BİTTİ -> renders/grover16.gif")


def qft26():
    """RAM-max: 26 kubut QFT — 1 GB statevector, ~350 GB bellegi boydan boyca tarar."""
    n = 26
    t0 = time.time()
    d = Devre(n)
    ram = d.psi.nbytes / 1024 ** 2
    print(f"  statevector: {ram:.0f} MB ({n} kubut)")
    qft(d, list(range(n)))
    sure = time.time() - t0
    print(f"  QFT-26 tamam: {sure:.1f} sn, ~{351 * ram / 1024:.0f} GB bellegi taradi")
    print("== BİTTİ (RAM-max demosu)")


def shor15():
    """Shor N=15: QFT sonrasi olcum olasiliklari — periyot tepeleri."""
    d = Devre(7)
    for q in range(3):
        d.h(q)
    psi = d.psi.reshape([8, 16])
    yeni = np.zeros_like(psi)
    for x in range(8):
        yeni[x, pow(7, x, 15)] = 1.0
    d.psi = yeni.reshape(-1)
    qft(d, qubits=[0, 1, 2])
    p = d.olasiliklar().reshape(8, 16).sum(axis=1)
    p /= p.sum()
    png_yaz("renders/shor15.png", cubuklar(p, 0))
    tepe = [m for m in range(8) if p[m] > 0.15]
    from math import gcd
    rler = [8 // gcd(m, 8) for m in tepe if m]
    print(f"  tepeler: {tepe} -> r adaylari: {rler}")
    print("== BİTTİ -> renders/shor15.png")


if __name__ == "__main__":
    os.makedirs("renders", exist_ok=True)
    hangi = sys.argv[1] if len(sys.argv) > 1 else "hepsi"
    if hangi in ("grover", "hepsi"):
        grover16()
    if hangi in ("qft", "hepsi"):
        qft26()
    if hangi in ("shor", "hepsi"):
        shor15()
