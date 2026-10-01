"""Рис. 1 — частка стратегій у рішеннях агентів Red залежно від тіку (200 боїв, метод керує Red)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import battle_sim as b

T = 200
eps = b.series(range(200), "topsis_v1", b.W_BASE)
tot = {s: [0] * T for s in b.STRATS}
for e in eps:
    for t, c in enumerate(e["per_tick"][:T]):
        for s in b.STRATS:
            tot[s][t] += c[s]
share = {s: [] for s in b.STRATS}
for t in range(T):
    n = sum(tot[s][t] for s in b.STRATS)
    for s in b.STRATS:
        share[s].append(100 * tot[s][t] / n if n else float("nan"))
running = [sum(1 for e in eps if len(e["per_tick"]) > t) for t in range(T)]
fig, ax = plt.subplots(figsize=(8, 4), dpi=220)
cols = {"Attack": "#c0392b", "Defense": "#2980b9", "Retreat": "#7f8c8d"}
ax.stackplot(range(1, T + 1), [share[s] for s in b.STRATS], labels=b.STRATS, colors=[cols[s] for s in b.STRATS], alpha=0.9)
ax.set_xlim(1, T); ax.set_ylim(0, 100)
ax.set_xlabel("Тік симуляції"); ax.set_ylabel("Частка рішень агентів Red, %")
ax2 = ax.twinx(); ax2.plot(range(1, T + 1), running, "k--", lw=1.2, label="Боїв, що тривають"); ax2.set_ylim(0, 210)
ax2.set_ylabel("Кількість боїв, що тривають")
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.18), frameon=False, fontsize=9)
plt.tight_layout(); plt.savefig("results/figure1_strategy_dynamics.png", facecolor="white")
print("saved results/figure1_strategy_dynamics.png")
