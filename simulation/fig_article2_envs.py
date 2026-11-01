"""Рис.: частка перемог проти наївного ІШІ в п'яти середовищах (тестові бої, N = 400 на точку)."""
import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
R = json.load(open("results/article2_final.json"))
out = sys.argv[1] if len(sys.argv) > 1 else "results/article2_envs.png"
bt_cal = R["bt_cal"]
series = [("К1, експертні ваги", "K1|expert", "k", ":", "o"),
          ("К2FH, експертні ваги", "K2FH|expert", "0.45", "--", "s"),
          ("К2FH, калібровані ваги", "K2FH|cal", "k", "-", "D"),
          ("Дерево поведінки (стандартне)", "BT|30|5|0|0|0", "0.45", "-", "^"),
          ("Дерево поведінки (каліброване)", bt_cal, "0.45", "-.", "v"),
          ("Utility AI", "utility", "k", (0, (1, 3)), "x")]
plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"], "font.size": 12})
fig, ax = plt.subplots(figsize=(8.6, 4.2), dpi=300)
xs = list(range(1, 6))
for label, key, col, ls, mk in series:
    ys = [e["win_pct"] for e in R["vs_naive"][key]]
    ax.plot(xs, ys, color=col, ls=ls, marker=mk, lw=1.5, ms=6, label=label)
ax.set_xticks(xs)
ax.set_xticklabels([f"Е{i}\n({e[0]:.1f}; {e[1]:.1f})".replace(".", ",") for i, e in enumerate(R["envs"], 1)])
ax.set_xlabel("Середовище (множник імовірності влучання: за руху стрільця; для цілі в укритті)")
ax.set_ylabel("Частка перемог, %")
ax.set_ylim(0, 105); ax.grid(color="0.85", lw=0.6)
ax.legend(frameon=False, fontsize=10, ncol=2, loc="lower left")
plt.tight_layout(); plt.savefig(out, facecolor="white"); print("saved", out)
