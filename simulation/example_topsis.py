"""Числовий приклад підрозд. 2.3 (табл. 4–8) — детермінований розрахунок."""
import math
import battle_sim as b

W = b.W_BASE
NAMES = b.STRATS


def example(ammo=20, hp=60, allies=2, enemies=3, cover=True):
    s6 = b.threat_level(allies, enemies)
    m = b.matrix_v1(ammo, hp, allies, enemies, cover, s6)
    den = [math.sqrt(sum(m[i][j] ** 2 for i in range(3))) for j in range(6)]
    r = [[m[i][j] / den[j] for j in range(6)] for i in range(3)]
    v = [[r[i][j] * W[j] for j in range(6)] for i in range(3)]
    ap = [max(v[i][j] for i in range(3)) for j in range(6)]
    am = [min(v[i][j] for i in range(3)) for j in range(6)]
    print(f"S6 = {s6:.2f}")
    for name, mat in (("Табл. 4  X", m), ("Табл. 5  r", r), ("Табл. 6  v", v)):
        print(name)
        for n, row in zip(NAMES, mat):
            print(f"  {n:8s}", " ".join(f"{x:7.4f}" for x in row))
    print("A+ =", [round(x, 4) for x in ap]); print("A- =", [round(x, 4) for x in am])
    print("Табл. 7")
    for i, n in enumerate(NAMES):
        dp = math.sqrt(sum((v[i][j] - ap[j]) ** 2 for j in range(6)))
        dm = math.sqrt(sum((v[i][j] - am[j]) ** 2 for j in range(6)))
        print(f"  {n:8s} D+={dp:.4f} D-={dm:.4f} C={dm / (dp + dm):.4f}")


def sensitivity():
    print("Табл. 8 (кількість ворогів 0..7)")
    for e in range(8):
        t = b.threat_level(2, e)
        c = b.topsis(b.matrix_v1(20, 60, 2, e, True, t), W)
        print(f"  {e}  S6={t:.2f}  C=", [round(x, 3) for x in c], "->", NAMES[c.index(max(c))])


if __name__ == "__main__":
    example()
    sensitivity()
