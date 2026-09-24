#!/usr/bin/env python3
"""quantum-cinema dogrulama kapsulu: analitik kuantum sonuclari + yogun referans."""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from quantum import Devre, H, kron_gates

OK = 0


def kontrol(ad, kosul, detay=""):
    global OK
    if kosul:
        OK += 1
        print(f"  [ok] {ad}")
    else:
        print(f"  [FAIL] {ad} {detay}")
        sys.exit(1)


print("1) Bell durumu")
d = Devre(2)
d.h(0).cx(0, 1)
p = d.olasiliklar()
kontrol("00 ve 11 %%50/%%50", abs(p[0] - 0.5) < 1e-12 and abs(p[3] - 0.5) < 1e-12 and
        abs(p[1]) < 1e-12 and abs(p[2]) < 1e-12)

print("2) CNOT dogruluk tablosu — yogun matris referansiyla")
U = kron_gates(2, [("cx", 0, 1)])
uyum = True
for giris in range(4):
    durum = np.zeros(4, dtype=complex)
    durum[giris] = 1
    ref = U @ durum
    d = Devre(2)
    if giris & 2: d.x(0)
    if giris & 1: d.x(1)
    d.cx(0, 1)
    uyum &= np.allclose(d.psi, ref)
kontrol("4 giris birebir", uyum)

print("3) Toffoli 24 kombinasyon")
hata = 0
def idx(g):
    return ((g & 1) << 2) | (g & 2) | ((g >> 2) & 1)
for a, b, h in ((0, 1, 2), (0, 2, 1), (1, 2, 0)):
    for g in range(8):
        d = Devre(3)
        if g & 1: d.x(0)
        if g & 2: d.x(1)
        if g & 4: d.x(2)
        d.ccx(a, b, h)
        p = d.olasiliklar()
        kontroller = [(g >> c) & 1 for c in (a, b)]
        flip = (1 << (2 - h)) if all(kontroller) else 0
        if abs(p[idx(g) ^ flip] - 1.0) >= 1e-12:
            hata += 1
kontrol("24 kombinasyon", hata == 0)

print("4) Kuantum teleportasyon — indirgenmiş yogunluk matrisi")
rng = np.random.default_rng(3)
teta, phi = rng.random() * np.pi, rng.random() * 2 * np.pi
hazir = np.array([math.cos(teta / 2), np.exp(1j * phi) * math.sin(teta / 2)])
d = Devre(3)
psi = d.psi.reshape([2] * 3)
psi[(0, 0, 0)], psi[(0, 0, 1)] = hazir[0], hazir[1]
d.psi = psi.reshape(-1)
d.cx(0, 1).h(0).cx(1, 2).cz(0, 2)
psi = d.psi.reshape([2] * 3)
# her klasik dal (a,b) icin: proje + X^b Z^a duzeltmesi -> q2 = hazir olmali
dal_hata = 0
for a in range(2):
    for b in range(2):
        dal = psi[(a, b, slice(None))]
        norm = np.linalg.norm(dal)
        if norm < 1e-12:
            continue
        dal = dal / norm
        if b:
            dal = dal[::-1]                     # X
        if a:
            dal = dal * [1, -1]                 # Z
        dal_hata += int(not np.allclose(dal, hazir, atol=1e-10))
kontrol("4 dalin herisinde q2 = gonderilen durum", dal_hata == 0, f"{dal_hata} dal hatali")

print("5) Grover 6 kubut: |42> isaretli arama")
N = 64
hedef = 42
d = Devre(6)
for q in range(6):
    d.h(q)
adim = int(math.pi / 4 * math.sqrt(N))
for _ in range(adim):
    d.psi[hedef] *= -1                       # oracle
    for q in range(6):
        d.h(q)
    d.psi[0] *= -1                           # |0> faz cevirme
    for q in range(6):
        d.h(q)
p = d.olasiliklar()
kontrol(f"{adim} iterasyonda p(|{hedef}>) > 0.9", p[hedef] > 0.9, f"p={p[hedef]:.3f}")

print("6) QFT 6 kubut — yogun QFT matrisiyle diferansiyel")
d = Devre(6)
rng6 = np.random.default_rng(9)
for q in range(6):
    d.ry(q, rng6.random() * math.pi)
girdi = d.durum()
n = 6
boyut = 2 ** n
omega = np.exp(2j * np.pi / boyut)
F = np.array([[omega ** (j * k) / math.sqrt(boyut) for k in range(boyut)]
              for j in range(boyut)])
beklenen = F @ girdi
from quantum import qft as qft_uygula
qft_uygula(d)
fark = np.abs(d.psi - beklenen).max()
kontrol("statevector birebir (max fark < 1e-9)", fark < 1e-9, f"fark={fark:.2e}")

print("7) Shor N=15, a=7 — periyot bulma + carpanlar")
# sayac 3 kubut (x=0..7), is registri 4 kubut: f(x) = 7^x mod 15
d = Devre(7)
for q in range(3):
    d.h(q)
psi = d.psi.reshape([8, 16])
yeni = np.zeros_like(psi)
for x in range(8):
    fx = pow(7, x, 15)
    yeni[x, fx] = 1.0
d.psi = yeni.reshape(-1)
# sayac kaydina QFT (3 kubut)
from quantum import qft
qft(d, qubits=[0, 1, 2])
p = d.olasiliklar().reshape(8, 16).sum(axis=1)
tepe = [m for m in range(8) if p[m] > 0.2]
r_aday = set()
for m in tepe[1:]:
    if m:
        from math import gcd
        r_aday.add(8 // gcd(m, 8))
basarili = False
for r in r_aday:
    if r % 2 == 0:
        x = pow(7, r // 2, 15)
        f1, f2 = math.gcd(x - 1, 15), math.gcd(x + 1, 15)
        if f1 * f2 == 15:
            basarili = (f1, f2)
kontrol(f"periyot r={sorted(r_aday)} -> 15 = {basarili}", bool(basarili))

print("8) determinizm")
def kur():
    d = Devre(4, seed=5)
    for q in range(4):
        d.h(q).ry(q, 0.7)
    return d
o1 = kur().olc(8)
o2 = kur().olc(8)
kontrol("ayni seed -> ayni olcum", bool(np.array_equal(o1, o2)))

print(f"\nTUM KAPILAR GECTI ({OK} kontrol)")


def idx3(a, b, c):
    return (a << 2) | (b << 1) | c
