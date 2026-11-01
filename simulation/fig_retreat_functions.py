"""Рис.: функції придатності стратегії Retreat за критеріями S1 і S2 у варіантах К1 і К2."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import battle_sim as b

out = sys.argv[1] if len(sys.argv) > 1 else "results/retreat_functions.png"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"], "font.size": 12})
fig, ax = plt.subplots(1, 2, figsize=(8.6, 3.3), dpi=300)
xa = [i * 0.1 for i in range(0, 301)]
ax[0].plot(xa, [10 * b.clamp01(1 - x / 15) for x in xa], "k--", lw=1.6, label="К1: 10·φ(1 − s₁/15)")
ax[0].plot(xa, [10 * b.clamp01(1 - x / 30) for x in xa], "k-", lw=1.6, label="К2: 10·φ(1 − s₁/30)")
ax[0].set_xlabel("Запас боєприпасів s₁"); ax[0].set_ylabel("Оцінка придатності Retreat")
ax[0].set_xlim(0, 30); ax[0].set_ylim(0, 10.5); ax[0].set_title("а) критерій S₁", fontsize=12)
xh = list(range(0, 101))
ax[1].plot(xh, [10 * b.clamp01(1 - x / 30) for x in xh], "k--", lw=1.6, label="К1: 10·φ(1 − s₂/30)")
ax[1].plot(xh, [10 * b.clamp01(1 - x / 100) for x in xh], "k-", lw=1.6, label="К2: 10·φ(1 − s₂/100)")
ax[1].set_xlabel("Витривалість s₂ (HP)"); ax[1].set_xlim(0, 100); ax[1].set_ylim(0, 10.5)
ax[1].set_title("б) критерій S₂", fontsize=12)
for a in ax:
    a.legend(frameon=False, fontsize=10.5, loc="upper right"); a.grid(color="0.85", lw=0.6)
plt.tight_layout(); plt.savefig(out, facecolor="white")
print("saved", out)
