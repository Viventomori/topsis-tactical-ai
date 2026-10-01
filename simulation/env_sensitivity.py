"""Табл. 11 — чутливість до параметрів середовища (парна схема, 400 боїв на рядок)."""
import json
import battle_sim as b
import review_experiments as r

ROWS = [(0.6, 0.5), (1.0, 0.5), (0.8, 0.8), (0.6, 1.0), (1.0, 1.0)]

if __name__ == "__main__":
    out = []
    for mp, cf in ROWS:
        b.MOVE_PENALTY, b.COVER_FACTOR = mp, cf
        row = {"move": mp, "cover": cf}
        for c in ("topsis_v1", "topsis_feas"):
            s = r.summarize(r.paired_series(c))
            row[c] = {"win": s["win_pct"], "loss": s["loss_pct"], "draw": s["draw_pct"], "p": s["binom_p"]}
        print(row, flush=True)
        out.append(row)
    json.dump(out, open("results/env_sensitivity.json", "w"), indent=1, default=float)
