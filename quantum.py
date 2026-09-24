#!/usr/bin/env python3
"""
quantum-cinema — sıfırdan kuantum devre simülatörü (statevector).

Kübit sayısına göre RAM'ı doğrudan besler: 26 kübit = 2^26 = 67M genlik =
1 GB complex128. Kapılar reshape/transpose hilesiyle tüm durumu tek geçişte
değiştirir (BLAS hızında). Yoğun matris referansı ile diferansiyel test edilir.

    from quantum import Devre
    d = Devre(3)
    d.h(0); d.cx(0, 1)
    olasiliklar = d.olasiliklar()
"""

import math

import numpy as np

H = np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
S = np.array([[1, 0], [0, 1j]], dtype=complex)
T = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)
I2 = np.eye(2, dtype=complex)


def rx(teta):
    return np.array([[math.cos(teta / 2), -1j * math.sin(teta / 2)],
                     [-1j * math.sin(teta / 2), math.cos(teta / 2)]], dtype=complex)


def ry(teta):
    return np.array([[math.cos(teta / 2), -math.sin(teta / 2)],
                     [math.sin(teta / 2), math.cos(teta / 2)]], dtype=complex)


def rz(teta):
    return np.array([[np.exp(-1j * teta / 2), 0],
                     [0, np.exp(1j * teta / 2)]], dtype=complex)


class Devre:
    """n kübitli statevector simülatörü. q0 = en anlamlı bit (MSBfirst)."""

    def __init__(self, n, seed=1):
        self.n = n
        self.psi = np.zeros(2 ** n, dtype=complex)
        self.psi[0] = 1.0
        self.rng = np.random.default_rng(seed)
        self.gecmis = []

    # ---- tek kübit kapısı
    def tek(self, m, q):
        psi = self.psi.reshape([2] * self.n)
        psi = np.moveaxis(psi, q, 0)
        s = psi.shape
        psi = psi.reshape(2, -1)
        psi = m @ psi
        psi = psi.reshape(s)
        psi = np.moveaxis(psi, 0, q)
        self.psi = psi.reshape(-1)
        return self

    def h(self, q):
        return self.tek(H, q)

    def x(self, q):
        return self.tek(X, q)

    def y(self, q):
        return self.tek(Y, q)

    def z(self, q):
        return self.tek(Z, q)

    def s(self, q):
        return self.tek(S, q)

    def t(self, q):
        return self.tek(T, q)

    def rx(self, q, teta):
        return self.tek(rx(teta), q)

    def ry(self, q, teta):
        return self.tek(ry(teta), q)

    def rz(self, q, teta):
        return self.tek(rz(teta), q)

    # ---- kontrollü kapılar (maske üzerinden, tam durum geçişi)
    def cx(self, kontrol, hedef):
        psi = self.psi.reshape([2] * self.n)
        psi = np.moveaxis(psi, [kontrol, hedef], [0, 1])
        s = psi.shape
        psi = psi.reshape(2, 2, -1)
        psi[1, [0, 1]] = psi[1, [1, 0]]     # kontrol=1 iken hedefi X'le
        psi = psi.reshape(s)
        psi = np.moveaxis(psi, [0, 1], [kontrol, hedef])
        self.psi = psi.reshape(-1)
        self.gecmis.append(("cx", kontrol, hedef))
        return self

    def cz(self, a, b):
        psi = self.psi.reshape([2] * self.n)
        sl = [slice(None)] * self.n
        sl[a] = 1
        sl[b] = 1
        psi[tuple(sl)] *= -1
        self.gecmis.append(("cz", a, b))
        return self

    def ccx(self, a, b, hedef):
        psi = self.psi.reshape([2] * self.n)
        psi = np.moveaxis(psi, hedef, 0)
        sl = [slice(None)] * self.n
        sl[a + 1 if a < hedef else a] = 1
        sl[b + 1 if b < hedef else b] = 1
        bolge = psi[tuple(sl)]              # eksen0 = hedef
        bolge[[0, 1]] = bolge[[1, 0]]       # X
        psi[tuple(sl)] = bolge
        psi = np.moveaxis(psi, 0, hedef)
        self.psi = psi.reshape(-1)
        self.gecmis.append(("ccx", a, b, hedef))
        return self

    def swap(self, a, b):
        psi = self.psi.reshape([2] * self.n)
        psi = np.swapaxes(psi, a, b)
        self.psi = psi.reshape(-1)
        return self

    # ---- olcum ve olasilik
    def olasiliklar(self):
        return np.abs(self.psi) ** 2

    def olc(self, adet=1):
        p = self.olasiliklar()
        p = p / p.sum()
        return self.rng.choice(len(p), size=adet, p=p)

    def durum(self):
        return self.psi.copy()


# ---------------------------------------------------------------- QFT

def qft(d, qubits=None):
    """Klasik QFT devresi: H + kontrollu fazlar + swap agi."""
    qs = qubits or list(range(d.n))
    n = len(qs)
    for i in range(n):
        d.h(qs[i])
        for j in range(i + 1, n):
            teta = math.pi / (2 ** (j - i))
            _kontrollu_faz(d, qs[j], qs[i], teta)
    for i in range(n // 2):
        d.swap(qs[i], qs[n - 1 - i])
    return d


def _kontrollu_faz(d, kontrol, hedef, teta):
    psi = d.psi.reshape([2] * d.n)
    sl = [slice(None)] * d.n
    sl[kontrol] = 1
    sl[hedef] = 1
    psi[tuple(sl)] *= np.exp(1j * teta)
    return d


# ---------------------------------------------------------------- yoğun referans

def kron_gates(n, islemler):
    """Islem listesini 2^n x 2^n yogun matrise cevirir (yalniz kucuk n icin).
    islem: ("tek", q, M) | ("cx", c, t) | ("cz", a, b)"""
    boyut = 2 ** n
    U = np.eye(boyut, dtype=complex)
    for islem in islemler:
        tur = islem[0]
        if tur == "tek":
            _, q, m = islem
            G = _tek_kron(n, q, m)
        elif tur == "cx":
            _, c, t = islem
            G = np.zeros((boyut, boyut), dtype=complex)
            for i in range(boyut):
                f = i
                if (f >> (n - 1 - c)) & 1:
                    f ^= 1 << (n - 1 - t)
                G[f, i] = 1
        elif tur == "cz":
            _, a, b = islem
            G = np.eye(boyut, dtype=complex)
            for i in range(boyut):
                if ((i >> (n - 1 - a)) & 1) and ((i >> (n - 1 - b)) & 1):
                    G[i, i] = -1
        else:
            raise ValueError(tur)
        U = G @ U
    return U


def _tek_kron(n, q, m):
    sonuc = np.array([[1.0]], dtype=complex)
    for k in range(n):
        sonuc = np.kron(sonuc, m if k == q else I2)
    return sonuc


def yogun_uygula(n, islemler, durum):
    U = kron_gates(n, islemler)
    return U @ durum
