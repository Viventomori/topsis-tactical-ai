"""review_experiments.py — експерименти на зауваження рецензента (2, 4, 5).

Парний дизайн: для кожного seed = 0..199 проводиться два бої з однаковими початковими умовами
(контролер X грає за Red проти naive за Blue, потім naive за Red проти X за Blue).
Усі показники обчислюються з погляду команди, якою керує X.
"""
import json, math, random, platform, sys
from statistics import mean, stdev
from scipy import stats
import battle_sim as b

SEEDS = range(200)


def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [100 * (c - h), 100 * (c + h)]


def tci(xs):
    m = mean(xs); h = stats.t.ppf(0.975, len(xs) - 1) * stdev(xs) / math.sqrt(len(xs))
    return [m, m - h, m + h]


def team_view(e, side):
    me, op = (side, "Blue" if side == "Red" else "Red")
    w = 1 if e["winner"] == me else -1 if e["winner"] == op else 0
    eff = lambda t: e[t]["kills"] / e[t]["shots"] if e[t]["shots"] else 0.0
    sh = e["share"][me]; n = sum(sh.values()) or 1
    return {"res": w, "hp": e[me]["hp_total"] / 5, "hp_op": e[op]["hp_total"] / 5,
            "surv": e[me]["survivors"], "surv_op": e[op]["survivors"],
            "eff": eff(me), "eff_op": eff(op), "ticks": e["ticks"],
            "A": 100 * sh["Attack"] / n, "D": 100 * sh["Defense"] / n, "R": 100 * sh["Retreat"] / n,
            "dt": e["t_dec"]["dt"], "nd": e["t_dec"]["n"]}


def paired_series(ctrl, w=b.W_BASE, opp="naive", seeds=SEEDS):
    games = []
    for s in seeds:
        g_red = team_view(b.run_episode(s, ctrl, opp, w, b.W_BASE), "Red")
        g_blue = team_view(b.run_episode(s, opp, ctrl, b.W_BASE, w), "Blue")
        games.append((g_red, g_blue))
    return games


def summarize(games):
    flat = [g for pair in games for g in pair]
    N = len(flat)
    win = sum(g["res"] == 1 for g in flat); loss = sum(g["res"] == -1 for g in flat); draw = N - win - loss
    out = {"N": N, "win": win, "loss": loss, "draw": draw,
           "win_pct": 100 * win / N, "win_ci": wilson(win, N), "loss_pct": 100 * loss / N, "loss_ci": wilson(loss, N),
           "draw_pct": 100 * draw / N, "draw_ci": wilson(draw, N)}
    out["binom_p"] = stats.binomtest(win, win + loss, 0.5).pvalue if win + loss else 1.0
    # показники: середнє за seed (два бої), 95% ДІ за t-розподілом по 200 seed
    for k in ("hp", "hp_op", "surv", "surv_op", "eff", "eff_op", "ticks", "A", "D", "R"):
        out[k] = tci([(a[k] + c[k]) / 2 for a, c in games])
    # парні різниці «X мінус суперник»
    for k in ("hp", "surv", "eff"):
        d = [((a[k] - a[k + "_op"]) + (c[k] - c[k + "_op"])) / 2 for a, c in games]
        out["d_" + k] = tci(d) + [stats.ttest_1samp(d, 0).pvalue]
    # вплив сторони: перемоги X за Red vs за Blue на тих самих seed (точний тест Мак-Немара)
    r_only = sum(1 for a, c in games if a["res"] == 1 and c["res"] != 1)
    b_only = sum(1 for a, c in games if a["res"] != 1 and c["res"] == 1)
    out["side"] = {"win_red": 100 * sum(a["res"] == 1 for a, _ in games) / len(games),
                   "win_blue": 100 * sum(c["res"] == 1 for _, c in games) / len(games),
                   "red_only": r_only, "blue_only": b_only,
                   "p": stats.binomtest(r_only, r_only + b_only, 0.5).pvalue if r_only + b_only else 1.0}
    nd = sum(g["nd"] for g in flat)
    out["us"] = 1e6 * sum(g["dt"] for g in flat) / nd if nd else None
    return out


def compare(g1, g2):
    """Парне порівняння двох контролерів на тих самих 400 боях: Мак-Немар за перемогами, t-тест за HP."""
    f1 = [g for p in g1 for g in p]; f2 = [g for p in g2 for g in p]
    only1 = sum(1 for a, c in zip(f1, f2) if a["res"] == 1 and c["res"] != 1)
    only2 = sum(1 for a, c in zip(f1, f2) if a["res"] != 1 and c["res"] == 1)
    p = stats.binomtest(only1, only1 + only2, 0.5).pvalue if only1 + only2 else 1.0
    dhp = [((a["hp"] + c["hp"]) - (x["hp"] + y["hp"])) / 2 for (a, c), (x, y) in zip(g1, g2)]
    return {"only1": only1, "only2": only2, "p_mcnemar": p, "dhp": tci(dhp) + [stats.ttest_1samp(dhp, 0).pvalue]}


def weights_sensitivity():
    res = {}
    names = ["S1", "S2", "S3", "S4", "S5", "S6"]
    for j in range(6):
        for f in (0.5, 1.5):
            w = list(b.W_BASE); w[j] *= f; s = sum(w); w = [x / s for x in w]
            sm = summarize(paired_series("topsis_v1", tuple(w)))
            res[f"{names[j]}x{f}"] = {"w": [round(x, 3) for x in w], "win": sm["win_pct"], "loss": sm["loss_pct"], "draw": sm["draw_pct"], "hp": sm["hp"][0]}
    sm = summarize(paired_series("topsis_v1", (1 / 6,) * 6))
    res["equal"] = {"w": [round(1 / 6, 3)] * 6, "win": sm["win_pct"], "loss": sm["loss_pct"], "draw": sm["draw_pct"], "hp": sm["hp"][0]}
    rnd = random.Random(2026)
    wins, losses = [], []
    for _ in range(100):
        g = [rnd.gammavariate(1, 1) for _ in range(6)]; s = sum(g); w = tuple(x / s for x in g)
        sm = summarize(paired_series("topsis_v1", w, seeds=range(100)))
        wins.append(sm["win_pct"]); losses.append(sm["loss_pct"])
    q = lambda xs, p: sorted(xs)[int(p * (len(xs) - 1))]
    res["dirichlet100"] = {"win_min": min(wins), "win_q25": q(wins, .25), "win_med": q(wins, .5), "win_q75": q(wins, .75), "win_max": max(wins),
                           "share_win_gt_loss": 100 * sum(1 for a, c in zip(wins, losses) if a > c) / 100,
                           "loss_max": max(losses)}
    return res


if __name__ == "__main__":
    R = {"env": {"python": sys.version.split()[0], "platform": platform.platform(), "cpu": platform.processor() or platform.machine()}}
    G = {}
    for c in ("topsis_v1", "topsis_feas", "saw_v1", "random", "naive"):
        G[c] = paired_series(c)
        R[c] = summarize(G[c])
        print(c, round(R[c]["win_pct"], 1), round(R[c]["loss_pct"], 1), round(R[c]["draw_pct"], 1), "p", R[c]["binom_p"], "side", R[c]["side"], flush=True)
    R["cmp"] = {f"topsis_v1 vs {c}": compare(G["topsis_v1"], G[c]) for c in ("topsis_feas", "saw_v1", "random", "naive")}
    R["weights"] = weights_sensitivity()
    json.dump(R, open("review_results.json", "w"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps(R["cmp"], indent=1, default=float))
    print(json.dumps(R["weights"], indent=1, default=float))
