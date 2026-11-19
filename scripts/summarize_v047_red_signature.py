"""Summarise sim_results/v047_red_signature/*.json into markdown tables (stdout)."""
import json, math, os, sys
from collections import defaultdict
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sim_results", "v047_red_signature")
ARMS = ["2P_v046", "2P_v047", "2P_v047_D1", "3P_v046", "3P_v047", "4P_v046", "4P_v047"]
R = {a: json.load(open(os.path.join(D, a + ".json"))) for a in ARMS}
def pc(x, n): return 100.0 * x / n
def grp(recs, key):
    d = defaultdict(list)
    for r in recs:
        for s in r["seats"]: d[s[key]].append(s["win"])
    return d
def stats(v):
    n = len(v); m = sum(v) / n; sd = math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1)); return 100 * m, 196 * sd / math.sqrt(n)
S = {}
print("## Pace / endings\n| arm | n | rounds | MC% | PZ% | Sing% | TW% | winner Secrets |\n|---|---|---|---|---|---|---|---|")
for a in ARMS:
    r = R[a]; n = len(r); e = defaultdict(int)
    for x in r:
        e[x["end"]] += 1
    tw = sum(x["tw"] for x in r)
    ws = [x["wsec"] for x in r if x["wsec"] is not None]
    S[a] = dict(rounds=sum(x["rounds"] for x in r) / n, mc=pc(e["market_collapse"], n), pz=pc(e["patient_zero"], n), sing=pc(e["singularity"], n), tw=pc(tw, n), ws=sum(ws) / len(ws))
    s = S[a]; print(f"| {a} | {n} | {s['rounds']:.2f} | {s['mc']:.1f} | {s['pz']:.1f} | {s['sing']:.1f} | {s['tw']:.1f} | {s['ws']:.2f} |")
print("  (end reasons raw:", {a: dict(__import__('collections').Counter(x['end'] for x in R[a])) for a in ARMS}, ")")
print("\n## Archetype win % (95% CI) and spread\n")
for a in ARMS:
    g = grp(R[a], "arch"); m = {k: stats(v) for k, v in sorted(g.items())}
    sp = max(x[0] for x in m.values()) - min(x[0] for x in m.values()); S[a]["spread"] = sp
    cg = grp(R[a], "co"); cm = {k: stats(v)[0] for k, v in cg.items()}; S[a]["cspread"] = max(cm.values()) - min(cm.values())
    print(f"- {a}: " + ", ".join(f"{k} {v[0]:.1f}±{v[1]:.1f}" for k, v in m.items()) + f" | **spread {sp:.1f}** | company spread {S[a]['cspread']:.1f}")
print("\n## SETEC Corp (2P)\n| arm | final MS | MLB 1st/g | MLB 2nd/g | Secrets absorbed/g |\n|---|---|---|---|---|")
for a in ["2P_v046", "2P_v047", "2P_v047_D1"]:
    r = R[a]; n = len(r); f = lambda i: sum(x["setec"][i] for x in r) / n
    print(f"| {a} | {f(0):.2f} | {f(1):.2f} | {f(2):.2f} | {f(3):.2f} |")
print("\n## signature_red telemetry (per 1000 games; fizzle % of events; SETEC share of gifts)\n| arm | events/g | gifts_locked | mutual | fizzles | setec_gifts | setec_ms | capped | zero_rescues | fizzle% | setec share |\n|---|---|---|---|---|---|---|---|---|---|---|")
for a in ARMS:
    r = R[a]; n = len(r); t = {k: sum(x["ctr"][k] for x in r) for k in r[0]["ctr"]}
    gifts = t["events"] - t["fizzles"]
    print(f"| {a} | {t['events']/n:.2f} | {t['gifts_to_locked']} | {t['mutual_cancels']} | {t['fizzles']} | {t['setec_gifts']} | {t['setec_ms_gained']} | {t['capped_gains']} | {t['zero_rescues']} | {pc(t['fizzles'], max(1,t['events'])):.1f} | {pc(t['setec_gifts'], max(1,gifts)):.1f} |")
print("\n## Deltas v047 - v046")
for P in (2, 3, 4):
    a, b = S[f"{P}P_v046"], S[f"{P}P_v047"]
    print(f"- {P}P: rounds {b['rounds']-a['rounds']:+.2f}, MC {b['mc']-a['mc']:+.1f}, Sing {b['sing']-a['sing']:+.1f}, arch spread {b['spread']-a['spread']:+.1f} ({a['spread']:.1f}->{b['spread']:.1f}), company spread {b['cspread']-a['cspread']:+.1f}")
