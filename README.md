# ⚛️ quantum-cinema

**EN:** A **quantum computer simulator** built from scratch — statevector engine in NumPy that maxes out your RAM: a 26-qubit register is a **1 GB** complex array, and a single QFT pass scans **~350 GB** of memory. Verified against analytic quantum results and a dense-matrix reference. Grover search, QFT, quantum teleportation and Shor's factoring of 15 — all running, all proven.

**TR:** Sıfırdan yazılmış **kuantum bilgisayar simülatörü** — NumPy statevector motoru RAM'ı doğrudan besler: 26 kübit = **1 GB**'lık genlik dizisi; tek QFT geçişi **~350 GB** belleği boydan boyca tarar. Analitik kuantum sonuçları ve yoğun-matris referansıyla doğrulanır. Grover araması, QFT, kuantum teleportasyon ve Shor'un 15'i çarpanlarına ayırışı — hepsi çalışır, hepsi kanıtlı.

![grover](renders/grover16.gif)

## 🖼️ Gallery / Galeri

### 🔍 Grover 16-qubit — 65,536 items
![grover](renders/grover16.gif)
201 amplitude-amplification iterations: the marked item's probability ramps from 1/65536 to **100.00%**. Watch the spike grow. — *201 genlik büyütme iterasyonu: işaretli elemanın olasılığı 1/65536'dan %100'e tırmanır.*

### ⚛️ Shor N=15 — [`render.py`](render.py)
![shor](renders/shor15.png)
QFT period-finding: four sharp peaks → r = 4 → **15 = 3 × 5**. Factoring, quantum style. — *QFT periyot bulma: dört keskin tepe → 15 = 3 × 5.*

## 🧱 The engine / Motor

| Piece | Detail |
|---|---|
| ⚛️ Statevector | complex128, 2ⁿ genlik — 26 kübite kadar (1 GB+ RAM) |
| 🚪 Gates | H X Y Z S T · RX RY RZ · CX CZ CCX · SWAP — reshape/moveaxis tek geçiş, döngü yok |
| 🌊 QFT | N-logN kapı ile kuantum Fourier dönüşümü |
| 🎲 Measurement | olasılık dağılımından tohumlu örnekleme |
| 🔎 Reference | ≤8 kübit için yoğun 2ⁿ×2ⁿ matris simülatörü — diferansiyel test referansı |

## ✅ Verification / Doğrulama — kuantumda göz güvenilmez

**EN:** Quantum states can't be eyeballed — so every algorithm is checked against an independent truth: CNOT truth table vs **dense matrix reference**, teleportation verified branch-by-branch via **reduced density matrices**, Grover's success probability against the analytic π/4 formula, QFT against the textbook DFT matrix, and Shor actually **factoring 15**. During development these gates caught a broken Toffoli axis-shift and a mask shape bug.

**TR:** Kuantum durumları gözle denetlenemez — her algoritma bağımsız bir hakikate karşı sınanır: CNOT doğruluk tablosu **yoğun matris referansıyla**, teleportasyon **indirgenmiş yoğunluk matrisleriyle** dal dal, Grover başarısı π/4 formülüyle, QFT ders kitabı DFT matrisiyle — ve Shor gerçekten 15'i çarpar. Geliştirme sırasında bozuk Toffoli eksen kayması ve maske şekil bugı bu kapılar sayesinde yakalandı.

```bash
python3 tests/verify.py    # 8 kapı
python3 render.py hepsi    # grover16 GIF + 26 kübit RAM-max + shor15
```

## 🚀 Usage / Kullanım

```python
from quantum import Devre, qft

d = Devre(26)            # 1 GB statevector — RAM'in nefesini keser
for q in range(26):
    d.h(q)
qft(d, list(range(26)))  # ~350 GB bellek trafigi, ~30 sn
```

## 🧪 Why / Neden

**TR:** Kuantum simülatörleri "bu domain çok karmaşık" denerek profesyonel araçlara bırakılır. Bu proje tersini kanıtlıyor: kapı mekanığını reshape/moveaxis ile kurgulayan, RAM bütçesini hesaplayıp 26 kübitte 1 GB'ı yöneten ve her sonucu iki bağımsız gerçeklemeyle doğrulayan bir motor ~400 satırda yazılabilir. Silicon-cinema klasik bilgisayarın beynini döktü; bu repo kuantum mekaniğinin matematikini çalıştırıyor.

## 📄 License

MIT
