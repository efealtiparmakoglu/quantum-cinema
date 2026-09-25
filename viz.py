"""quantum-cinema gorsellestirme motoru.

Genlik-alani: n kubutun 2^n olasiligi dogrudan bir goruntunun pikselleridir
(n = 16 -> 256x256). Kuantum girisimi boylece "cizilmez", GORUNUR.

Eksen/panel: matplotlib yok — cizgiler, tiklar ve 3x5 font elle cizilir.
"""

import math
import os
import struct
import zlib

import numpy as np

W_ = None  # aktif kanvas genisligi (cizim yardimcilari icin)


# ---------------------------------------------------------------- png

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


# ---------------------------------------------------------------- font (3x5)

FONT = {
    "0": "111101101101111", "1": "010110010010111", "2": "111001111100111",
    "3": "111001111001111", "4": "101101111001001", "5": "111100111001111",
    "6": "111100111101111", "7": "111001001001001", "8": "111101111101111",
    "9": "111101111001111", "A": "111101111101101", "B": "110101110101110",
    "C": "011100100100011", "D": "110101101101110", "E": "111100110100111",
    "F": "111100110100100", "G": "011100101101011", "H": "101101111101101",
    "I": "111010010010111", "K": "101101110101101", "L": "100100100100111",
    "M": "101111111101101", "N": "110101101101101", "O": "010101101101010",
    "P": "110101110100100", "Q": "010101101110011", "R": "110101110110101",
    "S": "011100010100110", "T": "111010010010010", "U": "101101101101111",
    "V": "101101101101010", "X": "101101010101101", "Y": "101101010010010",
    " ": "000000000000000", ":": "000010000010000", ".": "000000000000010",
    "=": "000111000111000", "-": "000000111000000", "r": "000000111110100",
    "(": "001010010010001", ")": "100010010100000", "%": "101001010100101",
}


def metin_yaz(img, x, y, metin, renk=(235, 235, 235), olcek=1):
    H, W = img.shape[:2]
    for ci, ch in enumerate(metin.upper()):
        bits = FONT.get(ch)
        if bits is None:
            continue
        for r in range(5):
            for c in range(3):
                if bits[r * 3 + c] == "1":
                    yy, xx = y + r * olcek, x + ci * 4 * olcek
                    img[yy:yy + olcek, xx:xx + olcek] = renk


# ---------------------------------------------------------------- genlik alani

def genlik_alani(p, palet="magma", kontrast=0.25, parlak_us=0.5):
    """2^n olasilik -> kare goruntu. parlaklik = log-olasilik (girisim gorunsun)."""
    n = int(math.log2(p.size))
    yan = 2 ** (n // 2)
    alan = p.reshape(yan, yan)
    logd = np.log10(alan + 10 ** (-kontrast * 10))
    logd = np.clip((logd + kontrast * 10) / (kontrast * 10), 0, 1)
    parlak = logd ** parlak_us

    t = parlak
    if palet == "magma":          # siyah -> mor -> kirmizi -> sari -> beyaz
        r = np.clip(3.2 * t - 0.1, 0, 1)
        g = np.clip(2.2 * t - 1.05, 0, 1) + np.clip((t - 0.55) * 0.6, 0, 0.25)
        b = np.clip(1.6 * t, 0, 0.85) * (1 - np.clip((t - 0.75) * 4, 0, 1)) + \
            np.clip((t - 0.85) * 6.6, 0, 1)
    elif palet == "buz":          # siyah -> lacivert -> camgobegi -> beyaz
        r = np.clip(2.4 * t - 1.0, 0, 1)
        g = np.clip(1.6 * t, 0, 0.95)
        b = np.clip(1.1 * t + 0.12, 0, 1)
    else:                          # ates: siyah -> kirmizi -> sari
        r = np.clip(2.6 * t, 0, 1)
        g = np.clip(2.0 * t - 1.0, 0, 1)
        b = np.clip(1.4 * t - 1.35, 0, 1)
    return (np.stack([r, g, b], axis=-1) * 255).astype(np.uint8)


def olcekle(img, faktor):
    return img.repeat(faktor, axis=0).repeat(faktor, axis=1)


# ---------------------------------------------------------------- eksen araci

class Kanvas:
    def __init__(self, W, H, bg=(10, 10, 14)):
        self.W, self.H = W, H
        self.img = np.full((H, W, 3), bg, dtype=float)

    def cizgi(self, x0, y0, x1, y1, renk=(200, 200, 200), kalinlik=1):
        adim = int(max(abs(x1 - x0), abs(y1 - y0))) * 2 + 1
        for i in range(adim + 1):
            t = i / adim
            x, y = int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t)
            if 0 <= y < self.H and 0 <= x < self.W:
                self.img[y, x] = renk
                if kalinlik > 1:
                    self.img[min(y + 1, self.H - 1), x] = renk

    def nokta(self, x, y, r, renk):
        self.img[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1] = renk

    def metin(self, x, y, metin, renk=(235, 235, 235), olcek=1):
        metin_yaz(self.img, x, y, metin, renk, olcek)

    def panel(self, x0, y0, x1, y1, baslik=None):
        self.cizgi(x0, y0, x1, y0, (90, 90, 110))
        self.cizgi(x0, y0, x0, y1, (90, 90, 110))
        self.cizgi(x0, y1, x1, y1, (90, 90, 110))
        self.cizgi(x1, y0, x1, y1, (90, 90, 110))
        if baslik:
            self.metin(x0 + 6, y0 - 9, baslik)


def kaydet(kanvas, path):
    png_yaz(path, np.clip(kanvas.img, 0, 255).astype(np.uint8))
