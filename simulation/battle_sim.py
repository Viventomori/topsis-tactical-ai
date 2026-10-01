"""
battle_sim.py — імітаційне моделювання бойової взаємодії двох команд агентів ІШІ.

Поле бою: відрізок [0; 100] з двома зонами укриття; команда Red стартує біля x = 0,
команда Blue — біля x = 100. Кожен агент на кожному тіку обирає стратегію
Attack / Defense / Retreat (A1, A2, A3) і виконує відповідну дію.

Контролери:
  * "naive"    — завжди Attack;
  * "topsis_v1" — початковий метод (формули придатності Таблиці 1 початкової версії);
  * "topsis_v2" — удосконалений метод (плавні функції для Retreat, S2 від HP_MAX).

Запуск:  python battle_sim.py            — усі серії та статистика (seed 0..199)
         python battle_sim.py calibrate  — випадковий пошук ваг на train-seed 10000..10059
"""
import math, random, sys, time, json
from statistics import mean, stdev

# ---------------- параметри середовища ----------------
FIELD = 100.0
COVER = [(28.0, 36.0), (64.0, 72.0)]
HP_MAX, AMMO_MAX = 100.0, 30
R_SENSE, R_FIRE = 30.0, 15.0
SPEED = 2.0
P_HIT, DAMAGE = 0.35, 25.0
MOVE_PENALTY, COVER_FACTOR = 0.6, 0.5
BASE_ZONE, REGEN_HP, REGEN_AMMO = 5.0, 2.0, 1
MAX_TICKS = 300
N_PER_TEAM = 5

W_BASE = (0.20, 0.20, 0.15, 0.20, 0.10, 0.15)
W_CAL = (0.30, 0.20, 0.05, 0.35, 0.05, 0.05)   # результат calibrate() + локального пошуку, розділ 7
STRATS = ("Attack", "Defense", "Retreat")


def clamp01(v):
    return 0.0 if v < 0 else 1.0 if v > 1 else v


def in_cover(x):
    return any(a <= x <= b for a, b in COVER)


# ---------------- матриці рішень ----------------
def matrix_v1(ammo, stamina, allies, enemies, cover, threat):
    """Початкові формули (Таблиця 1 початкової версії статті)."""
    return [
        [clamp01(ammo / 30) * 10, clamp01(stamina / 80) * 10, clamp01(allies / 3) * 10,
         clamp01(1 - enemies / 4) * 10, 6 if cover else 4, clamp01(1 - threat / 10) * 10],
        [clamp01(ammo / 50) * 7, clamp01(stamina / 50) * 8, clamp01(allies / 2) * 7,
         clamp01(enemies / 4) * 8, 10 if cover else 3, clamp01(threat / 10) * 7],
        [clamp01(1 - ammo / 15) * 10, clamp01(1 - stamina / 30) * 10, clamp01(1 - allies / 3) * 8,
         clamp01(enemies / 6) * 10, 3 if cover else 7, clamp01(threat / 10) * 10],
    ]


def matrix_v2(ammo, stamina, allies, enemies, cover, threat):
    """Удосконалені формули: для Retreat S1, S2 — плавні спадні функції від максимуму,
    які не обнуляються при середніх значеннях ресурсу."""
    m = matrix_v1(ammo, stamina, allies, enemies, cover, threat)
    m[2][0] = clamp01(1 - ammo / AMMO_MAX) * 10
    m[2][1] = clamp01(1 - stamina / HP_MAX) * 10
    return m


def topsis(matrix, w):
    rows, cols = len(matrix), len(matrix[0])
    s = sum(w)
    w = [x / s for x in w]
    den = [math.sqrt(sum(matrix[i][j] ** 2 for i in range(rows))) or 1.0 for j in range(cols)]
    v = [[matrix[i][j] / den[j] * w[j] for j in range(cols)] for i in range(rows)]
    best = [max(v[i][j] for i in range(rows)) for j in range(cols)]
    worst = [min(v[i][j] for i in range(rows)) for j in range(cols)]
    c = []
    for i in range(rows):
        dp = math.sqrt(sum((v[i][j] - best[j]) ** 2 for j in range(cols)))
        dm = math.sqrt(sum((v[i][j] - worst[j]) ** 2 for j in range(cols)))
        c.append(dm / (dp + dm) if dp + dm > 0 else 0.5)
    return c


# ---------------- агент ----------------
class Agent:
    __slots__ = ("team", "x", "hp", "ammo", "strat", "moved", "shots", "kills")

    def __init__(self, team, x):
        self.team, self.x = team, x
        self.hp, self.ammo = HP_MAX, AMMO_MAX
        self.strat, self.moved, self.shots, self.kills = "Attack", False, 0, 0

    @property
    def home(self):
        return 0.0 if self.team == "Red" else FIELD

    @property
    def fwd(self):
        return 1.0 if self.team == "Red" else -1.0


def sense(agent, agents):
    allies = [a for a in agents if a is not agent and a.team == agent.team and a.hp > 0 and abs(a.x - agent.x) <= R_SENSE]
    enemies = [a for a in agents if a.team != agent.team and a.hp > 0 and abs(a.x - agent.x) <= R_SENSE]
    return allies, enemies


def threat_level(n_allies, n_enemies):
    """S6 — потенційна загроза: локальне співвідношення сил у радіусі R_sense, шкала 0..10."""
    return 10.0 * n_enemies / (n_enemies + n_allies + 1)


def saw(matrix, w):
    """Зважена сума (SAW) на тій самій нормалізованій матриці (5), (6) — для абляції агрегації."""
    rows, cols = len(matrix), len(matrix[0])
    s = sum(w)
    den = [math.sqrt(sum(matrix[i][j] ** 2 for i in range(rows))) or 1.0 for j in range(cols)]
    return [sum(matrix[i][j] / den[j] * w[j] / s for j in range(cols)) for i in range(rows)]


# Контролери:
#   naive        — завжди Attack;
#   random       — рівноймовірний вибір стратегії на кожному тіку (ті самі правила руху/укриття);
#   topsis_v1    — запропонований метод (Табл. 2, TOPSIS);
#   topsis_feas  — те саме + некомпенсаторне обмеження: Attack недопустима при ammo = 0
#                  (альтернатива вилучається з матриці до застосування TOPSIS);
#   saw_v1       — та сама матриця придатності, агрегація зваженою сумою замість TOPSIS;
#   topsis_v2    — удосконалені функції Retreat (для наступних досліджень).
def decide(agent, agents, ctrl, w, stats, crnd=None):
    if ctrl == "naive":
        return "Attack"
    if ctrl == "random":
        return crnd.choice(STRATS)
    allies, enemies = sense(agent, agents)
    s = (agent.ammo, agent.hp, len(allies), len(enemies), in_cover(agent.x),
         threat_level(len(allies), len(enemies)))
    t0 = time.perf_counter()
    m = (matrix_v2 if ctrl == "topsis_v2" else matrix_v1)(*s)
    idx = [0, 1, 2]
    if ctrl == "topsis_feas" and agent.ammo <= 0:
        idx = [1, 2]
    sub = [m[i] for i in idx]
    c = saw(sub, w) if ctrl == "saw_v1" else topsis(sub, w)
    best = idx[max(range(len(idx)), key=lambda k: c[k])]   # за рівності — перша за порядком A1, A2, A3
    stats["dt"] += time.perf_counter() - t0
    stats["n"] += 1
    return STRATS[best]


def step_move(a, target):
    d = target - a.x
    if abs(d) < 1e-9:
        return
    a.x += max(-SPEED, min(SPEED, d))
    a.x = max(0.0, min(FIELD, a.x))
    a.moved = True


def nearest(a, pool):
    return min(pool, key=lambda e: abs(e.x - a.x)) if pool else None


def run_episode(seed, ctrl_red, ctrl_blue, w_red=W_BASE, w_blue=W_BASE):
    rnd = random.Random(seed)                 # генератор середовища (позиції, влучання)
    crnd = random.Random(seed + 1_000_003)    # окремий генератор для контролера random
    agents = [Agent("Red", rnd.uniform(0, 10)) for _ in range(N_PER_TEAM)] + \
             [Agent("Blue", rnd.uniform(90, 100)) for _ in range(N_PER_TEAM)]
    ctrl = {"Red": (ctrl_red, w_red), "Blue": (ctrl_blue, w_blue)}
    share = {t: {s: 0 for s in STRATS} for t in ("Red", "Blue")}
    per_tick = []   # розподіл стратегій агентів Red на кожному тіку
    tstats = {"dt": 0.0, "n": 0}
    tick = 0
    while tick < MAX_TICKS:
        tick += 1
        alive = [a for a in agents if a.hp > 0]
        if not any(a.team == "Red" for a in alive) or not any(a.team == "Blue" for a in alive):
            tick -= 1
            break
        for a in alive:
            c, w = ctrl[a.team]
            a.strat = decide(a, agents, c, w, tstats, crnd)
            share[a.team][a.strat] += 1
            a.moved = False
        per_tick.append({st: sum(1 for q in alive if q.team == "Red" and q.strat == st) for st in STRATS})
        # рух
        for a in alive:
            enemies_all = [e for e in alive if e.team != a.team]
            _, enemies = sense(a, agents)
            tgt = nearest(a, enemies)
            if a.strat == "Attack":
                if tgt is None:
                    step_move(a, a.x + a.fwd * SPEED)          # просування до противника
                elif abs(tgt.x - a.x) > R_FIRE:
                    step_move(a, tgt.x)
            elif a.strat == "Defense":
                if not in_cover(a.x):
                    cz = min(COVER, key=lambda z: min(abs(z[0] - a.x), abs(z[1] - a.x)))
                    step_move(a, (cz[0] + cz[1]) / 2)
            else:  # Retreat
                if abs(a.x - a.home) > BASE_ZONE:
                    step_move(a, a.home)
                else:
                    a.hp = min(HP_MAX, a.hp + REGEN_HP)
                    a.ammo = min(AMMO_MAX, a.ammo + REGEN_AMMO)
        # стрільба (одночасна)
        dmg = {}
        for a in alive:
            if a.strat == "Retreat" or a.ammo <= 0:
                continue
            targets = [e for e in alive if e.team != a.team and abs(e.x - a.x) <= R_FIRE]
            if not targets:
                continue
            e = nearest(a, targets)
            a.ammo -= 1
            a.shots += 1
            d = abs(e.x - a.x)
            p = P_HIT * (1 - 0.5 * d / R_FIRE)
            if a.moved:
                p *= MOVE_PENALTY
            if in_cover(e.x):
                p *= COVER_FACTOR
            if rnd.random() < p:
                dmg[id(e)] = dmg.get(id(e), 0.0) + DAMAGE
                if e.hp - dmg[id(e)] <= 0 < e.hp - (dmg[id(e)] - DAMAGE):
                    a.kills += 1
        for e in alive:
            if id(e) in dmg:
                e.hp -= dmg[id(e)]
    red_alive = [a for a in agents if a.team == "Red" and a.hp > 0]
    blue_alive = [a for a in agents if a.team == "Blue" and a.hp > 0]
    winner = "Red" if red_alive and not blue_alive else "Blue" if blue_alive and not red_alive else "Draw"
    res = {"winner": winner, "ticks": tick, "share": share, "t_dec": tstats, "per_tick": per_tick}
    for t, al in (("Red", red_alive), ("Blue", blue_alive)):
        team = [a for a in agents if a.team == t]
        res[t] = {"hp_total": sum(max(0.0, a.hp) for a in team),        # загиблі = 0
                  "survivors": len(al),
                  "shots": sum(a.shots for a in team),
                  "kills": sum(a.kills for a in team),
                  "ammo_alive": [a.ammo for a in al],
                  "last_strat": [a.strat for a in al]}
    return res


def series(seeds, ctrl_red, w_red=W_BASE):
    return [run_episode(s, ctrl_red, "naive", w_red) for s in seeds]


def summarize(eps):
    N = len(eps)
    wr = sum(e["winner"] == "Red" for e in eps)
    wb = sum(e["winner"] == "Blue" for e in eps)
    out = {"N": N, "red_wins": wr, "blue_wins": wb, "draws": N - wr - wb,
           "avg_ticks": mean(e["ticks"] for e in eps)}
    for t in ("Red", "Blue"):
        hp = [e[t]["hp_total"] / N_PER_TEAM for e in eps]            # середнє HP на агента, загиблі = 0
        out[t] = {"hp": mean(hp), "hp_sd": stdev(hp),
                  "surv": mean(e[t]["survivors"] for e in eps),
                  "ammo_eff": mean(e[t]["kills"] / e[t]["shots"] if e[t]["shots"] else 0 for e in eps)}
        tot = {s: sum(e["share"][t][s] for e in eps) for s in STRATS}
        n = sum(tot.values())
        out[t]["share"] = {s: 100 * tot[s] / n for s in STRATS}
    n = sum(e["t_dec"]["n"] for e in eps)
    out["us_per_decision"] = 1e6 * sum(e["t_dec"]["dt"] for e in eps) / n if n else 0
    return out


def objective(eps):
    s = summarize(eps)
    return (s["red_wins"] - s["blue_wins"]) / s["N"] + 0.5 * (s["Red"]["hp"] - s["Blue"]["hp"]) / HP_MAX


def calibrate(n_cand=250, train=range(10000, 10060), rng_seed=7):
    rnd = random.Random(rng_seed)
    cands = [W_BASE] + [tuple(round(x, 3) for x in _dirichlet(rnd, 6)) for _ in range(n_cand)]
    best = None
    for k, w in enumerate(cands):
        val = objective(series(train, "topsis_v2", w))
        if best is None or val > best[0]:
            best = (val, w)
            print(f"[{k}] obj={val:.3f} w={w}", flush=True)
    # округлення до кроку 0.05 і нормування
    w = [round(x / 0.05) * 0.05 for x in best[1]]
    s = sum(w); w = tuple(round(x / s, 2) for x in w)
    print("best:", best, "rounded:", w)
    return w


def _dirichlet(rnd, k):
    g = [rnd.gammavariate(1.0, 1.0) for _ in range(k)]
    s = sum(g)
    return [x / s for x in g]


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "calibrate":
        calibrate()
    else:
        test = range(0, 200)
        for name, ctrl, w in (("К1: TOPSIS v1 (початковий), w_base", "topsis_v1", W_BASE),
                              ("К2: TOPSIS v2 (удосконалений), w_base", "topsis_v2", W_BASE),
                              ("К3: TOPSIS v2 (удосконалений), w_cal", "topsis_v2", W_CAL)):
            print(name, json.dumps(summarize(series(test, ctrl, w)), ensure_ascii=False))
