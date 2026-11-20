"""Prints compact tables from scripts/probe_gray_vuln.py summaries (sim_results/gray_vuln/*.json)."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "sim_results", "gray_vuln")
V = sys.argv[1].split(",") if len(sys.argv) > 1 else ["G1", "A13", "B23", "C35", "C36", "D123", "E356", "E345"]
P = (2, 3, 4)


def load(v, pol, pl):
    p = os.path.join(D, f"{v}_{pol}_{pl}P.json")
    return json.load(open(p)) if os.path.exists(p) else None


def table(title, f, pol="S"):
    print(f"\n== {title}")
    print(f"{'var':6s}" + "".join(f"{str(pl) + 'P':>22s}" for pl in P))
    for v in V:
        cells = []
        for pl in P:
            s, b = load(v, pol, pl), load("G1", pol, pl)
            cells.append(f(s, b) if s and b else "n/a")
        print(f"{v:6s}" + "".join(f"{c:>22s}" for c in cells))


table("rounds | PZ% | MC% | SING%", lambda s, b: f"{s['rounds']:.2f}|{s['PZ']:.0f}|{s['MC']:.0f}|{s['SING']:.0f}")
table("PZ+MC d vs G1 (pp) | TW%", lambda s, b: f"{s['PZ'] + s['MC'] - b['PZ'] - b['MC']:+.1f}|{s['TW']:.1f}")
table("Green lost/seat | hits/seat", lambda s, b: f"{s['green_lost']:.2f}|{s['hits']:.2f}")
table("income/seat-rd (x G1) | dead%", lambda s, b: f"{s['inc']:.2f} ({s['inc'] / b['inc']:.3f})|{s['dead_pct']:.1f}")
table("Gray ⚠/die | Gray ⚠/rd | col ⚠/rd", lambda s, b: f"{s['gray_vuln_per_die']:.2f}|{s['gray_vuln_pr']:.2f}|{s['col_vuln_pr']:.2f}")
table("Gray rolled/rd | col rolled/rd", lambda s, b: f"{s['gray_rolled_pr']:.2f}|{s['col_rolled_pr']:.2f}")
table("winner Secrets | all Secrets", lambda s, b: f"{s['win_secrets']:.1f}|{s['secrets']:.1f}")
table("company spread | WH spread", lambda s, b: f"{s['co_spread']:.1f}|{s['wh_spread']:.1f}")
table("first thin rd | thins/seat | never%", lambda s, b: f"{s['first_thin_mean']:.2f}|{s['thins_per_seat']:.2f}|{s['never_thin_pct']:.0f}")
table("Rel L2 rd(%) | Rel L3 rd(%)", lambda s, b: f"{s['rel2_round']:.1f}({s['rel2_pct']:.0f})|{s['rel3_round']:.1f}({s['rel3_pct']:.0f})")
table("Pen L3 rd(%) | Tri L4 rd(%)", lambda s, b: f"{s['pen3_round']:.1f}({s['pen3_pct']:.0f})|{s['tri4_round']:.1f}({s['tri4_pct']:.0f})")
table("win% thin<=R3 | >R3 | never", lambda s, b: f"{s['win_early_thin']:.0f}|{s['win_late_thin']:.0f}|{s['win_never_thin']:.0f}")
print("\n== thin sources / seat (S, 3P)")
for v in V:
    s = load(v, "S", 3)
    if s:
        print(f"{v:6s} {s['thin_src']}")
print("\n== Gray owned by round R1..R8 (S)")
for pl in P:
    for v in V:
        s = load(v, "S", pl)
        if s:
            print(f"{pl}P {v:6s} " + " ".join(f"{s['owned_by_round'].get(str(r), float('nan')):.2f}" for r in range(1, 9)))
print("\n== Gray ⚠ per game-round summed over seats R1..R6 (S, 3P)")
for v in V:
    s = load(v, "S", 3)
    if s:
        print(f"{v:6s} " + " ".join(f"{s['vuln_by_round'].get(str(r), [0, 0])[0]:.2f}/{s['vuln_by_round'].get(str(r), [0, 0])[1]:.2f}" for r in range(1, 7)))
print("\n== win% by Gray owned entering R5 (S): {gray: (win%, n)}")
for pl in P:
    for v in V:
        s = load(v, "S", pl)
        if s:
            print(f"{pl}P {v:6s} {s['win_by_gray_r5']}")
print("\n== seat-0 forced policy: win% S | R (rush) | L (legacy); R-S, S-L in pp; seat-0 Green lost S|R|L")
for pl in P:
    for v in V:
        s, r, l = load(v, "S", pl), load(v, "R", pl), load(v, "L", pl)
        if s and r and l:
            print(f"{pl}P {v:6s} {s['seat0_win']:5.1f} {r['seat0_win']:5.1f} {l['seat0_win']:5.1f}  R-S {r['seat0_win'] - s['seat0_win']:+5.1f}"
                  f"  S-L {s['seat0_win'] - l['seat0_win']:+5.1f}  R-L {r['seat0_win'] - l['seat0_win']:+5.1f}"
                  f"  GL {s['seat0_green_lost']:.2f}|{r['seat0_green_lost']:.2f}|{l['seat0_green_lost']:.2f}"
                  f"  thins/seat-all S {s['thins_per_seat']:.2f} L {l['thins_per_seat']:.2f}")
