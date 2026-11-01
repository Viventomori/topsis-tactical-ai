"""article2_experiments.py — експерименти другої статті: удосконалення методу TOPSIS і вибір ваг критеріїв.

Варіанти методу (сценарій 5 проти 5):
  K1    — метод першої статті (табл. 2);
  K2    — удосконалені функції придатності відступу: Retreat S1 = 10·φ(1 − s1/30), S2 = 10·φ(1 − s2/100);
  K2F   — K2 + некомпенсаторне обмеження допустимості: Attack вилучається за s1 = 0;
  K2FH  — K2F + утримання відступу: розпочатий відступ триває, доки s1 < HOLD_AMMO або s2 < HOLD_HP.
Способи вибору ваг (для будь-якого варіанта):
  expert  — w = (0,20; 0,20; 0,15; 0,20; 0,10; 0,15) (перша стаття);
  entropy — ентропійні ваги, обчислені з матриці рішень на кожному кроці;
  critic  — ваги методом CRITIC, обчислені з матриці рішень на кожному кроці;
  static  — статичний вектор, переданий як w (калібровані ваги).
Ім'я контролера: "<варіант>|<спосіб ваг>", напр. "K2FH|entropy"; "K2FH|static" бере вектор w.
Дерево поведінки з параметрами: "BT|<hp_low>|<threat_def>|<ammo_low>|<hold_ammo>|<hold_hp>" (hold 0|0 — без утримання).

Протокол: калібрування на навчальних боях (seed 10000..), вибір на перевірних (20000..), підсумок на тестових (0..199),
парна схема зі зміною сторін, п'ять середовищ (коефіцієнти влучання за руху стрільця / для цілі в укритті).
"""
import json, math, random, sys, time
from multiprocessing import Pool
import battle_sim as b
import bt_utility_comparison as m
import review_experiments as rx

ENVS = [(0.6, 0.5), (1.0, 0.5), (0.8, 0.8), (0.6, 1.0), (1.0, 1.0)]
W_EXPERT = b.W_BASE
HOLD_AMMO, HOLD_HP = 30, 100   # обрано на навчальних/перевірних боях із сітки HOLD_GRID (results/article2_hold_grid.json)
HOLD_GRID = ((15, 50), (20, 60), (25, 70), (30, 80), (30, 100))
LN = math.log


# ---------------- способи вибору ваг ----------------
def entropy_weights(mat):
    rows, n = len(mat), len(mat[0])
    if rows < 2:
        return [1.0 / n] * n
    d = []
    for j in range(n):
        col = [mat[i][j] for i in range(rows)]
        s = sum(col)
        if s <= 0:
            d.append(0.0); continue
        e = -sum((x / s) * LN(x / s) for x in col if x > 0) / LN(rows)
        d.append(max(0.0, 1.0 - e))
    t = sum(d)
    return [x / t for x in d] if t > 0 else [1.0 / n] * n


def critic_weights(mat):
    rows, n = len(mat), len(mat[0])
    if rows < 2:
        return [1.0 / n] * n
    r = []
    for j in range(n):
        col = [mat[i][j] for i in range(rows)]
        lo, hi = min(col), max(col)
        r.append([(x - lo) / (hi - lo) if hi > lo else 0.0 for x in col])
    mean = [sum(c) / rows for c in r]
    sd = [math.sqrt(sum((x - mu) ** 2 for x in c) / rows) for c, mu in zip(r, mean)]

    def corr(a, bb):
        if sd[a] == 0 or sd[bb] == 0:
            return 0.0
        cov = sum((r[a][i] - mean[a]) * (r[bb][i] - mean[bb]) for i in range(rows)) / rows
        return cov / (sd[a] * sd[bb])
    c = [sd[j] * sum(1 - corr(j, k) for k in range(n)) for j in range(n)]
    t = sum(c)
    return [x / t for x in c] if t > 0 else [1.0 / n] * n


# ---------------- контролери ----------------
def topsis_controller(variant, wmode, agent, agents, w):
    s = m.state(agent, agents)
    if variant == "K2FH" and agent.strat == "Retreat" and (agent.ammo < HOLD_AMMO or agent.hp < HOLD_HP):
        return "Retreat"
    mat = (b.matrix_v1 if variant == "K1" else b.matrix_v2)(*s)
    idx = [1, 2] if (variant in ("K2F", "K2FH") and agent.ammo <= 0) else [0, 1, 2]
    sub = [mat[i] for i in idx]
    if wmode == "expert":
        ww = W_EXPERT
    elif wmode == "entropy":
        ww = entropy_weights(sub)
    elif wmode == "critic":
        ww = critic_weights(sub)
    else:
        ww = w
    c = b.topsis(sub, ww)
    return b.STRATS[idx[max(range(len(idx)), key=lambda k: c[k])]]


def bt_param_controller(params, agent, agents):
    hp_low, thr, ammo_low, h_ammo, h_hp = params
    ammo, hp, na, ne, cover, threat = m.state(agent, agents)
    if h_ammo and agent.strat == "Retreat" and (ammo < h_ammo or hp < h_hp):
        return "Retreat"
    if ammo <= ammo_low or hp < hp_low:
        return "Retreat"
    if ne > 0 and threat >= thr:
        return "Defense"
    return "Attack"


_base_decide = m.decide


def decide(agent, agents, ctrl, w, stats, crnd=None):
    if "|" not in ctrl:
        return _base_decide(agent, agents, ctrl, w, stats, crnd)
    t0 = time.perf_counter()
    parts = ctrl.split("|")
    if parts[0] == "BT":
        st = bt_param_controller(tuple(float(x) for x in parts[1:]), agent, agents)
    else:
        st = topsis_controller(parts[0], parts[1], agent, agents, w)
    stats["dt"] += time.perf_counter() - t0
    stats["n"] += 1
    return st


b.decide = decide

BT_DEFAULT = "BT|30|5|0|0|0"
BT_HOLD_DEFAULT = "BT|30|5|0|15|50"


# ---------------- запуск серій ----------------
def run_job(job):
    ctrl, w, opp, env, seeds = job
    b.MOVE_PENALTY, b.COVER_FACTOR = env
    g = rx.paired_series(ctrl, tuple(w), opp=opp, seeds=seeds)
    b.MOVE_PENALTY, b.COVER_FACTOR = ENVS[0]
    return g


def objective(games):
    flat = [x for p in games for x in p]
    n = len(flat)
    wl = sum(x["res"] for x in flat) / n
    dhp = sum(x["hp"] - x["hp_op"] for x in flat) / n
    return wl + 0.5 * dhp / b.HP_MAX


def evaluate(pool, ctrls, seeds, opp="naive"):
    """ctrls: list of (ctrl, w). Повертає {(ctrl, w): [games по ENVS]}."""
    jobs = [(c, w, opp, env, seeds) for c, w in ctrls for env in ENVS]
    res = pool.map(run_job, jobs, chunksize=1)
    out = {}
    k = 0
    for c, w in ctrls:
        out[(c, tuple(w))] = res[k:k + len(ENVS)]
        k += len(ENVS)
    return out


def score(gs):
    return sum(objective(g) for g in gs) / len(gs)


def dirichlet(rnd, k=6):
    g = [rnd.gammavariate(1.0, 1.0) for _ in range(k)]
    s = sum(g)
    return [round(x / s, 3) for x in g]


TRAIN = range(10000, 10050)   # 50 seed × 2 сторони = 100 боїв на середовище
VALID = range(20000, 20100)   # 200 боїв на середовище
TEST = range(0, 200)          # 400 боїв на середовище


def calibrate(pool, n_cand=200, top=10):
    rnd = random.Random(2026)
    cands = [list(W_EXPERT), list(b.W_CAL)] + [dirichlet(rnd) for _ in range(n_cand)]
    tr = evaluate(pool, [("K2FH|static", w) for w in cands], TRAIN)
    ranked = sorted(cands, key=lambda w: -score(tr[("K2FH|static", tuple(w))]))
    best = ranked[:top]
    va = evaluate(pool, [("K2FH|static", w) for w in best], VALID)
    vbest = max(best, key=lambda w: score(va[("K2FH|static", tuple(w))]))
    return {"train_scores": {str(w): score(tr[("K2FH|static", tuple(w))]) for w in ranked[:top]},
            "valid_scores": {str(w): score(va[("K2FH|static", tuple(w))]) for w in best},
            "expert_train": score(tr[("K2FH|static", tuple(W_EXPERT))]),
            "best": vbest}


def bt_grid():
    out = []
    for hp in (20, 30, 40, 50):
        for thr in (3.34, 5.0, 6.0):
            for al in (0, 5):
                for hold in ((0, 0),) + HOLD_GRID:
                    out.append(f"BT|{hp}|{thr:g}|{al}|{hold[0]}|{hold[1]}")
    return out


def calibrate_bt(pool, top=10):
    grid = bt_grid()
    tr = evaluate(pool, [(c, W_EXPERT) for c in grid], TRAIN)
    ranked = sorted(grid, key=lambda c: -score(tr[(c, tuple(W_EXPERT))]))
    best = ranked[:top]
    va = evaluate(pool, [(c, W_EXPERT) for c in best], VALID)
    vbest = max(best, key=lambda c: score(va[(c, tuple(W_EXPERT))]))
    return {"train_scores": {c: score(tr[(c, tuple(W_EXPERT))]) for c in ranked[:top]},
            "valid_scores": {c: score(va[(c, tuple(W_EXPERT))]) for c in best},
            "default_train": score(tr[(BT_DEFAULT, tuple(W_EXPERT))]),
            "best": vbest}


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "calibrate"
    with Pool(2) as pool:
        if step == "calibrate":
            t = time.time()
            R = {"topsis": calibrate(pool)}
            print("TOPSIS best", R["topsis"]["best"], round(time.time() - t), "s", flush=True)
            json.dump(R, open("results/article2_calibration.json", "w"), ensure_ascii=False, indent=1, default=float)
            R["bt"] = calibrate_bt(pool)
            print("BT best", R["bt"]["best"], round(time.time() - t), "s", flush=True)
            json.dump(R, open("results/article2_calibration.json", "w"), ensure_ascii=False, indent=1, default=float)


# ---------------- підсумкова оцінка на тестових боях ----------------
def brief(games):
    s = rx.summarize(games)
    keep = ("N", "win", "loss", "draw", "win_pct", "win_ci", "loss_pct", "loss_ci", "draw_pct", "draw_ci", "binom_p",
            "hp", "hp_op", "surv", "eff", "ticks", "A", "D", "R", "us", "side")
    out = {k: s[k] for k in keep}
    flat = [x for p in games for x in p]
    out["points_win"] = sum(1 for x in flat if x["res"] == 0 and x["hp"] > x["hp_op"] + 1e-9)
    out["points_loss"] = sum(1 for x in flat if x["res"] == 0 and x["hp"] < x["hp_op"] - 1e-9)
    return out


def final(pool):
    cal = json.load(open("results/article2_calibration.json"))
    w_cal = tuple(cal["topsis"]["best"])
    bt_cal = cal["bt"]["best"]
    main = [("K1|expert", W_EXPERT), ("K2|expert", W_EXPERT), ("K2F|expert", W_EXPERT), ("K2FH|expert", W_EXPERT),
            ("K2FH|entropy", W_EXPERT), ("K2FH|critic", W_EXPERT), ("K2FH|static", w_cal),
            (BT_DEFAULT, W_EXPERT), (BT_HOLD_DEFAULT, W_EXPERT), (bt_cal, W_EXPERT), ("utility", W_EXPERT)]
    ev = evaluate(pool, main, TEST)
    R = {"w_cal": w_cal, "bt_cal": bt_cal, "envs": ENVS, "vs_naive": {}, "mcnemar": {}, "h2h": {}}
    for (c, w), gs in ev.items():
        name = c if c != "K2FH|static" else "K2FH|cal"
        R["vs_naive"][name] = [brief(g) for g in gs]
        R["vs_naive"][name + "#mean_win"] = sum(brief(g)["win_pct"] for g in gs) / len(gs)
    fin = ev[("K2FH|static", w_cal)]
    for c, w in [(BT_DEFAULT, W_EXPERT), (bt_cal, W_EXPERT), ("K2FH|expert", W_EXPERT), ("utility", W_EXPERT)]:
        R["mcnemar"][c] = [rx.compare(f, o) for f, o in zip(fin, ev[(c, tuple(w))])]
    # очні серії: остаточний метод проти еталонів
    for opp in (BT_DEFAULT, bt_cal, "utility"):
        jobs = [("K2FH|static", w_cal, opp, env, TEST) for env in ENVS]
        R["h2h"][opp] = [brief(g) for g in pool.map(run_job, jobs, chunksize=1)]
    jobs = [(bt_cal, W_EXPERT, "utility", env, TEST) for env in ENVS]
    R["h2h"]["bt_cal_vs_utility"] = [brief(g) for g in pool.map(run_job, jobs, chunksize=1)]
    return R


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "final":
    with Pool(2) as pool:
        t = time.time()
        R = final(pool)
        json.dump(R, open("results/article2_final.json", "w"), ensure_ascii=False, indent=1, default=float)
        print("final done", round(time.time() - t), "s")
