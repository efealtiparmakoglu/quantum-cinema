#!/usr/bin/env python3
"""dalga motoru fizik kapilari: unitarlik, enerji, girişim çizgi araligi (analitik)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from dalga import Dalga, pot_barrier

OK = 0


def kontrol(ad, kosul, detay=""):
    global OK
    if kosul:
        OK += 1
        print(f"  [ok] {ad}")
    else:
        print(f"  [FAIL] {ad} {detay}")
        sys.exit(1)


print("1) unitarlik: serbest paket normu tam korunur")
D = Dalga(256, 20, 0.004)
D.paket(-4, 0, 0.6, 1.2, 8, 0)
n0 = D.norm()
for _ in range(300):
    D.adim()
sapma = abs(D.norm() - n0) / n0
kontrol("norm sapmasi < 1e-10", sapma < 1e-10, f"{sapma:.2e}")

print("2) enerji: serbest paket (V=0) Fourier'da TAM korunur")
k0, p0 = D.enerji()
for _ in range(100):
    D.adim()
k1, p1 = D.enerji()
sapma = abs((k1 + p1) - (k0 + p0)) / (abs(k0) + 1e-12)
kontrol("enerji sapmasi < 1e-9", sapma < 1e-9, f"{sapma:.2e}")

print("3) harmonik tuzak: enerji < %1 sapma")
D2 = Dalga(256, 16, 0.0007)
D2.V = 0.5 * 0.64 * (D2.X ** 2 + D2.Y ** 2)
D2.paket(2.2, 0, 0.9, 0.9, 0, 1.76)
k0, p0 = D2.enerji()
for _ in range(8571):
    D2.adim()
k1, p1 = D2.enerji()
sapma = abs((k1 + p1) - (k0 + p0)) / abs(k0 + p0)
kontrol("enerji sapmasi < %1", sapma < 0.01, f"%{sapma * 100:.3f}")

print("4) cift yarik: girişim çizgi araligi analitik formülle")
# lambda = 2*pi/px ; ekran uzakligi Ls ; yarik ayrimi d -> Delta_y = lambda*Ls/d
px, Ls, d_ = 8.0, 8.0, 1.2
lam = 2 * np.pi / px
Delta_analitik = lam * Ls / d_

D3 = Dalga(512, 20, 0.003)
from dalga import pot_cift_yarik
D3.V = pot_cift_yarik(D3, 0.5, 1.2, 0.5)
D3.paket(-6.5, 0, 0.7, 1.7, px, 0)
for _ in range(1200):
    D3.adim()
# x=+Ls hattindaki olasilik profili (yariklerden Ls uzakta)
ix = int((Ls + 10) / 20 * 512)
profil = np.abs(D3.psi[ix, :]) ** 2
yerel = profil[100:400] - profil[100:400].mean()
yerel *= np.hanning(len(yerel))
F = np.abs(np.fft.rfft(yerel))
frek = np.fft.rfftfreq(len(yerel), d=1)                     # devir/piksel
# fringe bandina bandpass: beklenen 1/2.62 birim = 1/67px = 0.0149 c/px
bant = (frek > 1.0 / 200) & (frek < 1.0 / 60)
baskin = frek[bant][np.argmax(F[bant])] if bant.any() else 0
Delta_olculen = (1.0 / baskin) / 512 * 20                   # piksel -> birim
kontrol(f"çizgi araligi ~ analitik ({Delta_analitik:.2f})",
        abs(Delta_olculen - Delta_analitik) / Delta_analitik < 0.25,
        f"olculen={Delta_olculen:.2f}")

print(f"\nTUM KAPILAR GECTI ({OK} kontrol)")
