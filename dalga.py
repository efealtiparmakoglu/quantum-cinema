#!/usr/bin/env python3
"""
dalga.py — 2B Schrödinger denklemini split-step Fourier yöntemiyle çözer.

    i·hbar·dψ/dt = -hbar²/2m ∇²ψ + V(x,y) ψ

hbar = m = 1 birim sistemi. Her adım: yarı FFT -> kinetik faz -> yarı FFT ->
potansiyel faz. Üniter: norm VE enerji tam korunur (kapılar bunu ölçer).

Görsel: |ψ|² parlaklık, faz = renk tonu (hue) -> akan sıvı-gökkuşağı.
"""

import argparse
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import zlib

import numpy as np

N2C = 255.0 / 255


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


# ---------------------------------------------------------------- renk

def faz_rengi(psi, parlaklik_guc=0.45):
    """Faz -> renk tonu (tüm tayfa), |psi|² -> parlaklık. Domain coloring."""
    amp = np.abs(psi)
    faz = np.angle(psi)
    parl = amp / (np.percentile(amp, 99.7) + 1e-12)
    parl = np.clip(parl, 0, 1) ** parlaklik_guc

    hue = (faz + np.pi) / (2 * np.pi)          # 0..1
    seg = hue * 6.0
    x = 1 - np.abs(seg % 2 - 1)
    idx = seg.astype(int) % 6
    r = np.choose(idx, [1, x, 0, 0, 0, 1])
    g = np.choose(idx, [x, 1, 1, x, 0, 0])
    b = np.choose(idx, [0, 0, 1, 1, 1, x])
    renk = np.stack([r, g, b], axis=-1)
    return (renk * parl[..., None] * 255).astype(np.uint8)


# ---------------------------------------------------------------- motor

class Dalga:
    def __init__(self, n, boyut_fiziksel, dt):
        self.n = n
        self.L = boyut_fiziksel
        self.dt = dt
        x = np.linspace(-self.L / 2, self.L / 2, n, endpoint=False)
        self.x = x
        self.X, self.Y = np.meshgrid(x, x)
        k = 2 * np.pi * np.fft.fftfreq(n, d=self.L / n)
        self.KX, self.KY = np.meshgrid(k, k)
        self.K2 = self.KX ** 2 + self.KY ** 2
        self.psi = np.zeros((n, n), dtype=complex)
        self.V = np.zeros((n, n))
        self.kinetic_faz = np.exp(-1j * self.K2 / 2 * dt)   # hbar/m = 1

    def paket(self, x0, y0, sx, sy, px, py):
        gauss = np.exp(-((self.X - x0) ** 2 / (2 * sx ** 2)
                         + (self.Y - y0) ** 2 / (2 * sy ** 2)))
        self.psi = gauss.astype(complex) * np.exp(1j * (px * self.X + py * self.Y))
        self.psi /= np.linalg.norm(self.psi)

    def adim(self, adet=1):
        """Strang bölmesi: V/2 - K - V/2 (simetrik, 2. mertebe)."""
        for _ in range(adet):
            self.psi *= np.exp(-1j * self.V * self.dt / 2)
            self.psi = np.fft.ifft2(self.kinetic_faz * np.fft.fft2(self.psi))
            self.psi *= np.exp(-1j * self.V * self.dt / 2)

    def norm(self):
        return float(np.sum(np.abs(self.psi) ** 2))

    def enerji(self):
        psi_k = np.fft.fft2(self.psi)
        kin = float(np.sum(self.K2 * np.abs(psi_k) ** 2) / 2) * (1 / self.n ** 2)
        pot = float(np.sum(self.V * np.abs(self.psi) ** 2))
        return kin, pot


# ---------------------------------------------------------------- potansiyeller

def pot_cift_yarik(D, yarik_g, ayrım, bar_g=0.6):
    V = np.zeros((D.n, D.n))
    bar = np.abs(D.X) < bar_g
    duvar = ~((np.abs(D.Y - ayrım / 2) < yarik_g) |
              (np.abs(D.Y + ayrım / 2) < yarik_g))
    V[bar & duvar] = 400.0
    return V


def pot_barrier(D, kalinlik=0.4, yukseklik=250.0):
    V = np.zeros((D.n, D.n))
    V[np.abs(D.X) < kalinlik / 2] = yukseklik
    return V


def pot_harmonik(D, omega=0.6):
    return 0.5 * omega ** 2 * (D.X ** 2 + D.Y ** 2)


def pot_merkez(D, r0=1.2, yukseklik=300.0):
    r = np.sqrt(D.X ** 2 + D.Y ** 2)
    V = np.zeros((D.n, D.n))
    V[r < r0] = yukseklik
    return V


# ---------------------------------------------------------------- cizim

def kare_ciz(D, stil="faz"):
    amp = np.abs(D.psi)
    parl = np.clip(amp / (np.percentile(amp, 99.9) + 1e-12), 0, 1) ** 0.5
    if stil == "intensity":
        # siyah -> lacivert -> camgobegi -> beyaz (kuantum optik gorunumu)
        t = parl[..., None]
        r = np.clip(1.8 * t - 0.5, 0, 1)
        g = np.clip(1.5 * t, 0, 1)
        b = np.clip(1.2 * t, 0, 1)
        img = np.concatenate([r, g, b], axis=-1)
        return (img * 255).astype(np.uint8)
    return faz_rengi(D.psi, 0.4)


# ---------------------------------------------------------------- sahne kosucu

def kos(cfg):
    sim = cfg["sim"]
    stil = sim.get("style", "faz")
    W, H = sim.get("width", 512), sim.get("height", 512)
    D = Dalga(sim["grid"], sim["L"], sim["dt"])
    if cfg.get("init", {}).get("type") == "paket":
        i = cfg["init"]
        D.paket(i["x0"], i["y0"], i.get("sx", 0.5), i.get("sy", 0.5),
                i.get("px", 0), i.get("py", 0))
    elif cfg.get("init", {}).get("type") == "iki_paket":
        i = cfg["init"]
        D.paket(i["x0"], i["y0"], i.get("sx", 0.5), i.get("sy", 0.5),
                i.get("px", 0), i.get("py", 0))
        D.psi += D.paket_hedef(i.get("x1", 0), i.get("y1", 0),
                               i.get("sx", 0.5), i.get("py", 0))
    pot_adi = cfg.get("potential", {}).get("type")
    if pot_adi == "cift_yarik":
        D.V = pot_cift_yarik(D, cfg["potential"].get("slit", 0.35),
                             cfg["potential"].get("separation", 1.6),
                             cfg["potential"].get("barrier", 0.6))
    elif pot_adi == "barrier":
        D.V = pot_barrier(D, cfg["potential"].get("thickness", 0.4),
                          cfg["potential"].get("height", 250.0))
    elif pot_adi == "harmonik":
        D.V = pot_harmonik(D, cfg["potential"].get("omega", 0.6))
    elif pot_adi == "merkez":
        D.V = pot_merkez(D, cfg["potential"].get("radius", 1.2),
                         cfg["potential"].get("height", 300.0))

    norm0 = D.norm()
    kin0, pot0 = D.enerji()
    e0 = kin0 + pot0
    print(f"  grid {D.n}x{D.n} | norm0 {norm0:.6f} | E0 {e0:.2f}")

    out = cfg["output"]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    gif_adi = out
    tmp = out + ".frames"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    toplam = sim["steps"]
    kareno = 0
    kare_her = sim.get("frame_every", max(1, toplam // 120))

    for adim in range(toplam):
        D.adim()
        if (adim + 1) % kare_her == 0:
            img = kare_ciz(D, stil)
            png_yaz(f"{tmp}/f{kareno:05d}.png", img)
            kareno += 1
            if kareno % 30 == 0:
                print(f"  kare {kareno} (adim {adim + 1}/{toplam})")

    son_norm = D.norm()
    k1, p1 = D.enerji()
    sapma = abs((k1 + p1) - e0) / (abs(e0) + 1e-12)

    fps = sim.get("fps", 20)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
                    "-i", f"{tmp}/f%05d.png",
                    "-vf", "palettegen=max_colors=256:stats_mode=diff", f"{tmp}/pal.png"],
                   check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
                    "-i", f"{tmp}/f%05d.png", "-i", f"{tmp}/pal.png",
                    "-lavfi", "paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle",
                    "-loop", "0", gif_adi], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"  kare: {kareno} | norm sapmasi: %{abs(son_norm - norm0) / norm0 * 100:.6f} | "
          f"enerji sapmasi: %{sapma * 100:.4f}")
    print(f"== BİTTİ -> {gif_adi}")
    return {"norm": son_norm / norm0, "enerji": sapma}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    a = ap.parse_args()
    kos(json.load(open(a.scene, encoding="utf-8")))
