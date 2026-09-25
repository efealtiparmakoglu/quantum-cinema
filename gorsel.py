#!/usr/bin/env python3
"""quantum-cinema gorselleri — genlik-alani filmleri ve cok panelli figure."""

import math
import os
import shutil
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quantum import Devre, qft
from viz import Kanvas, genlik_alani, kaydet, metin_yaz, olcekle, png_yaz

FFMPEG = ["ffmpeg", "-y", "-loglevel", "error"]


def gif_yap(tmp, out, fps, desen="f%05d.png", pal_renk=256):
    subprocess = __import__("subprocess")
    subprocess.run(FFMPEG + ["-framerate", str(fps), "-i", f"{tmp}/{desen}",
                             "-vf", f"palettegen=max_colors={pal_renk}:stats_mode=diff",
                             f"{tmp}/pal.png"], check=True)
    subprocess.run(FFMPEG + ["-framerate", str(fps), "-i", f"{tmp}/{desen}",
                             "-i", f"{tmp}/pal.png",
                             "-lavfi", "paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle",
                             "-loop", "0", out], check=True)


# ---------------------------------------------------------------- 1) grover16

def grover16():
    """16 kubut: 65536 genligin her biri 1 piksel — girisim filmi."""
    n, hedef = 16, 42424
    iterasyon = int(math.pi / 4 * math.sqrt(2 ** n))
    d = Devre(n)
    for q in range(n):
        d.h(q)
    tmp = "renders/grover16.frames"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    frameno = 0
    yakala = set(list(range(0, 24)) + list(range(24, iterasyon, 8)) + [iterasyon - 1])
    for it in range(iterasyon):
        d.psi[hedef] *= -1
        for q in range(n):
            d.h(q)
        d.psi[0] *= -1
        for q in range(n):
            d.h(q)
        if it in yakala:
            p = d.olasiliklar()
            img = olcekle(genlik_alani(p, "magma", kontrast=0.55, parlak_us=0.35), 3)
            img = img[24:744, 24:744]
            metin_yaz(img, 12, 10, f"GROVER 16 QUBIT | ITERASYON {it:03d}/{iterasyon} | p(hedef)={p[hedef] * 100:5.2f}%",
                      (255, 220, 150), 2)
            png_yaz(f"{tmp}/f{frameno:05d}.png", img)
            frameno += 1
    gif_yap(tmp, "renders/grover16.gif", 8)
    shutil.rmtree(tmp, ignore_errors=True)
    p = d.olasiliklar()
    print(f"  grover16: {iterasyon} iterasyon, p(hedef)=%{p[hedef] * 100:.2f}, {frameno} kare")
    print("  -> renders/grover16.gif")


# ---------------------------------------------------------------- 2) grover20 (agir)

def grover20():
    """20 kubut: 1,048,576 eleman, ~806 iterasyon — makinenin nefesi kesilir."""
    n, hedef = 20, 777777
    iterasyon = int(math.pi / 4 * math.sqrt(2 ** n))
    d = Devre(n)
    for q in range(n):
        d.h(q)
    tmp = "renders/grover20.frames"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    frameno = 0
    t0 = time.time()
    yakala = set(range(0, 12)) | set(range(12, iterasyon, 24)) | {iterasyon - 1}
    for it in range(iterasyon):
        d.psi[hedef] *= -1
        for q in range(n):
            d.h(q)
        d.psi[0] *= -1
        for q in range(n):
            d.h(q)
        if it in yakala:
            p = d.olasiliklar()
            img = genlik_alani(p, "buz", kontrast=0.65, parlak_us=0.35)
            img = img[::2, ::2].repeat(1, axis=0)                    # 512x512
            img = img.repeat(1, axis=1)
            img = img[16:496, 16:496]
            metin_yaz(img, 12, 10, f"GROVER 20 QUBIT | 1,048,576 ELEMAN | ITERASYON {it:03d}/{iterasyon} | p={p[hedef] * 100:5.2f}%",
                      (180, 230, 255), 2)
            png_yaz(f"{tmp}/f{frameno:05d}.png", img)
            frameno += 1
    gif_yap(tmp, "renders/grover20.gif", 10, pal_renk=200)
    shutil.rmtree(tmp, ignore_errors=True)
    p = d.olasiliklar()
    print(f"  grover20: {iterasyon} iterasyon, p(hedef)=%{p[hedef] * 100:.2f}, "
          f"{frameno} kare, {time.time() - t0:.0f} sn")
    print("  -> renders/grover20.gif")


# ---------------------------------------------------------------- 3) shor15

def shor15():
    """Shor N=15 cok panelli figuru: fonksiyon, QFT tepeleri, carpanlar."""
    K = Kanvas(1000, 620, bg=(10, 10, 16))
    K.metin(20, 14, "SHOR ALGORITMASI | N=15, a=7 | QUANTUM-CINEMA", (255, 220, 150), 2)

    # panel 1: f(x) = 7^x mod 15
    x0, y0, x1, y1 = 40, 70, 480, 250
    K.panel(x0, y0, x1, y1, "1) f(x) = 7^x mod 15  (klasik degerlendirme)")
    fx = [pow(7, x, 15) for x in range(8)]
    for i, v in enumerate(fx):
        px = x0 + 30 + i * 52
        py = y1 - 20 - v * 22
        K.nokta(px, py, 3, (120, 220, 255))
        K.cizgi(px, y1 - 20, px, py, (60, 80, 120))
    K.metin(x0 + 8, y1 - 14, "x=0..7", (160, 160, 180))

    # panel 2: QFT sonrasi olasilik tepeleri
    x0, y0, x1, y1 = 520, 70, 960, 250
    K.panel(x0, y0, x1, y1, "2) QFT SONRASI OLASILIK  (tepe = periyot bilgisi)")
    from quantum import Devre, qft
    d = Devre(7)
    for q in range(3):
        d.h(q)
    psi = d.psi.reshape([8, 16])
    yeni = np.zeros_like(psi)
    for x in range(8):
        yeni[x, pow(7, x, 15)] = 1.0
    d.psi = yeni.reshape(-1)
    qft(d, qubits=[0, 1, 2])
    p8 = d.olasiliklar().reshape(8, 16).sum(axis=1)
    p8 /= p8.sum()
    for m in range(8):
        px = x0 + 30 + m * 52
        py = y1 - 20 - int(p8[m] * (y1 - y0 - 50))
        renk = (255, 200, 80) if p8[m] > 0.15 else (90, 90, 110)
        K.cizgi(px, y1 - 20, px, py, renk, 3)
        K.metin(px - 3, y1 - 12, str(m), (150, 150, 170))

    # panel 3: periyot -> carpanlar (metin paneli)
    x0, y0 = 40, 300
    K.panel(40, 300, 960, 560, "3) PERIYOTTAN CARPANLARA")
    metinler = [
        "olcum:  m E {0, 2, 4, 6}   (QFT tepeleri)",
        "periyot: r = 8 / gcd(m, 8)  ->  r = 4",
        "",
        "kontrol:  7^4 mod 15 = 2401 mod 15 = 1  (dogru periyot)",
        "",
        "7^(r/2) = 49",
        "gcd(49 - 1, 15) = gcd(48, 15) = 3",
        "gcd(49 + 1, 15) = gcd(50, 15) = 5",
        "",
        "SONUC:  15 = 3 x 5",
    ]
    yy = y0 + 30
    for satir in metinler:
        renk = (255, 230, 120) if "SONUC" in satir else (220, 220, 230)
        K.metin(x0 + 24, yy, satir, renk, 2)
        yy += 24
    K.nokta(700, 430, 26, (80, 200, 120))
    K.metin(688, 408, "15", (10, 12, 10), 2)
    K.metin(676, 444, "= 3 x 5", (120, 255, 160), 2)

    kaydet(K, "renders/shor15.png")
    print("  -> renders/shor15.png")


# ---------------------------------------------------------------- 4) qft spektrum

def qft20():
    """20 kubut periyodik durumun QFT'si: 1M binlik girişim taragi (1D spektrum)."""
    n = 20
    d = Devre(n)
    periyot = 64
    for x in range(0, 2 ** n, periyot):
        d.psi[x] = 1.0
    d.psi /= np.linalg.norm(d.psi)
    t0 = time.time()
    qft(d, list(range(n)))
    p = d.olasiliklar()
    print(f"  qft20: {time.time() - t0:.1f} sn")

    W, H = 1600, 400
    K = Kanvas(W, H, bg=(8, 10, 16))
    K.panel(30, 20, W - 20, H - 50, "QFT SPEKTRUMU | 1,048,576 bin | periyot=64 -> 16 keskin tepe")
    p_log = np.log10(p + 1e-12)
    p_log = np.clip((p_log + 12) / 12, 0, 1)
    for i in range(W):
        b = int(i / W * (2 ** n))
        pencere = p[max(0, b - 256):min(2 ** n, b + 256)]
        deger = p_log[max(0, b - 128):min(2 ** n, b + 128)].max()
        h = int(deger * (H - 110))
        K.cizgi(30 + i, H - 50, 30 + i, H - 50 - h,
                (140, 200, 255) if deger > 0.5 else (70, 110, 170))
    # teoreetik tepeleri isaretle
    for k in range(0, 2 ** n, 2 ** (n - 4)):
        px = 30 + int(k / 2 ** n * W)
        K.cizgi(px, H - 50, px, H - 58, (255, 200, 80))
    K.metin(36, H - 40, "BIN (0 -> 1,048,575)   |   SARI CIZGI = TEORIK TEPE (r=64, 16 adet)", (200, 200, 220), 2)
    png_yaz("renders/qft20.png", np.clip(K.img, 0, 255).astype(np.uint8))
    print("  -> renders/qft20.png")


if __name__ == "__main__":
    hangi = sys.argv[1] if len(sys.argv) > 1 else "hepsi"
    os.makedirs("renders", exist_ok=True)
    if hangi in ("grover", "hepsi"):
        grover16()
    if hangi in ("shor", "hepsi"):
        shor15()
    if hangi in ("qft", "hepsi"):
        qft20()
    if hangi in ("agir", "hepsi"):
        grover20()
