"""Вибір порогів утримання відступу для К2FH на навчальних і перевірних боях (сітка, як у дереві поведінки)."""
import sys, json
sys.path.insert(0, ".")
import article2_experiments as A
from multiprocessing import Pool
W = (0.183, 0.166, 0.025, 0.271, 0.175, 0.181)   # ваги першого калібрування (за порогів утримання 15; 50), results/article2_calibration_hold15-50.json
holds = [(15, 50), (20, 60), (30, 80), (30, 100), (25, 70)]
def job(args):
    hold, seeds, env = args
    A.HOLD_AMMO, A.HOLD_HP = hold
    return A.run_job(("K2FH|static", W, "naive", env, seeds))
with Pool(2) as p:
    out = {}
    for name, seeds in (("train", A.TRAIN), ("valid", A.VALID)):
        res = p.map(job, [(h, seeds, e) for h in holds for e in A.ENVS], chunksize=1)
        for i, h in enumerate(holds):
            gs = res[i * 5:(i + 1) * 5]
            out[f"{name}{h}"] = A.score(gs)
            print(name, h, round(A.score(gs), 4), flush=True)
json.dump(out, open("results/article2_hold_grid.json", "w"), indent=1)
