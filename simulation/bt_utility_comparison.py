"""bt_utility_comparison.py — дерево поведінки (BT) та Utility AI як еталонні контролери.

Контролери (усі отримують ті самі шість показників стану агента, що й TOPSIS):
  bt            — дерево поведінки без пам'яті: Selector(Retreat-послідовність, Defense-послідовність, Attack);
  bt_hold       — те саме дерево, але розпочатий відступ триває (стан Running), доки агент не відновить
                  половину запасів: боєприпаси >= 15 і HP >= 50;
  utility       — Utility AI за схемою Infinite Axis Utility System [Mark 2009]: корисність дії = добуток
                  кривих відгуку з компенсаційним множником; криві відгуку — функції придатності табл. 2, нормовані до [0; 1];
  utility_floor — те саме, крива відгуку має нижню межу 0,1 (u' = 0,1 + 0,9·u), без «вето».
Модуль підміняє battle_sim.decide, тому його достатньо імпортувати перед запуском серій.
"""
import time
import battle_sim as b

BT_AMMO_EMPTY = 0        # Retreat: боєприпасів немає
BT_HP_LOW = 30           # Retreat: HP нижче 30 (поріг функції придатності відступу, табл. 2)
BT_THREAT_DEF = 5.0      # Defense: s6 >= 5  <=>  ворогів поруч не менше, ніж союзників + 1
HOLD_AMMO, HOLD_HP = 15, 50


def bt_decide(ammo, hp, n_allies, n_enemies, cover, threat, prev, hold):
    if hold and prev == "Retreat" and (ammo < HOLD_AMMO or hp < HOLD_HP):
        return "Retreat"
    if ammo <= BT_AMMO_EMPTY or hp < BT_HP_LOW:
        return "Retreat"
    if n_enemies > 0 and threat >= BT_THREAT_DEF:
        return "Defense"
    return "Attack"


UMAX = [[10, 10, 10, 10, 6, 10],
        [4.2, 8, 7, 8, 10, 7],
        [10, 10, 8, 10, 7, 10]]


def utility_scores(m, floor=0.0):
    n = len(m[0])
    mod = 1.0 - 1.0 / n
    out = []
    for i, row in enumerate(m):
        s = 1.0
        for j, x in enumerate(row):
            u = b.clamp01(x / UMAX[i][j])
            u = floor + (1.0 - floor) * u
            u = u + (1.0 - u) * mod * u
            s *= u
        out.append(s)
    return out


EXTRA = {}          # ім'я контролера -> функція(agent, agents, w) -> стратегія (розширення в інших модулях)
_orig_decide = b.decide


def state(agent, agents):
    allies, enemies = b.sense(agent, agents)
    return (agent.ammo, agent.hp, len(allies), len(enemies), b.in_cover(agent.x),
            b.threat_level(len(allies), len(enemies)))


def decide(agent, agents, ctrl, w, stats, crnd=None):
    if ctrl in EXTRA:
        t0 = time.perf_counter()
        st = EXTRA[ctrl](agent, agents, w)
        stats["dt"] += time.perf_counter() - t0; stats["n"] += 1
        return st
    if ctrl not in ("bt", "bt_hold", "utility", "utility_floor"):
        return _orig_decide(agent, agents, ctrl, w, stats, crnd)
    s = state(agent, agents)
    t0 = time.perf_counter()
    if ctrl in ("utility", "utility_floor"):
        u = utility_scores(b.matrix_v1(*s), 0.1 if ctrl == "utility_floor" else 0.0)
        st = b.STRATS[max(range(3), key=lambda k: u[k])]
    else:
        st = bt_decide(*s, prev=agent.strat, hold=(ctrl == "bt_hold"))
    stats["dt"] += time.perf_counter() - t0
    stats["n"] += 1
    return st


b.decide = decide
